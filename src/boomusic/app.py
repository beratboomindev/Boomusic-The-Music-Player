"""Boomusic uygulama mantığı (controller).

Bu sınıf; ayarlar (Config), kütüphane (Library), istatistikler (Stats),
akıllı karıştırma (SmartShuffle) ve ses motorunu (AudioEngine) birbirine
bağlar. Kasıtlı olarak ``pystray`` veya herhangi bir arayüz kütüphanesi
İÇERMEZ; böylece görüntü sunucusu (X/Wayland) olmayan bir ortamda bile
(örn. otomatik testlerde) sorunsuz import edilip test edilebilir.
Tepsi (tray) menüsü sadece bu sınıfın metodlarını çağırır.

== Thread güvenliği: TEK YAZAR kuralı ==
``self.shuffle`` (SmartShuffle) ve ``self._sequential_index`` kendi
başlarına thread-safe DEĞİLDİR. Bu bilinçli bir tasarım: performans için
kilit eklemek yerine, bu durumu MUTLAK OLARAK SADECE TEK BİR THREAD'İN
(``_worker_loop``) değiştirmesini garanti ediyoruz. Bu yüzden next(),
previous(), play_track_path(), toggle_shuffle() ve rescan() gibi
durum-DEĞİŞTİREN her şey ``_submit`` ile aynı kuyruğa girer ve sırayla
işlenir -- asla doğrudan/senkron çalışmazlar. Böylece örneğin "kullanıcı
tam shuffle'ı kapatırken otomatik şarkı geçişi de tetiklenirse torba
tutarsız kalır mı?" türünden yarış durumları (race condition) yapısal
olarak imkânsız hale gelir. Sadece OKUMA yapan getter'lar (shuffle_enabled,
now_playing_display, track_entries, vb.) kilitsiz, doğrudan çağrılabilir;
en kötü ihtimalle worker bir komutu işlerken bir an için bir adım eski
bilgi gösterirler, bu zararsızdır.
"""
from __future__ import annotations

import base64
import logging
import os
import queue
import shutil
import subprocess
import threading
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional

from . import notifier
from .config import Config
from .library import Library
from .player import AudioEngine
from .shuffle import SmartShuffle
from .stats import Stats
from .youtube import (
    YoutubeResult,
    check_yt_dlp,
    youtube_search,
    youtube_get_stream_url,
    youtube_download,
    youtube_download_url,
    DOWNLOAD_DIR_NAME,
)

logger = logging.getLogger("boomusic.app")

VOLUME_PRESETS = (0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100)


class TrackEntry(NamedTuple):
    """Tray menüsündeki 'Şarkı Seç' listesi için basit, salt-okunur görünüm."""
    path: str
    display_name: str
    is_current: bool
    played_this_round: bool
    play_count: int


class App:
    def __init__(
        self,
        config: Optional[Config] = None,
        library: Optional[Library] = None,
        stats: Optional[Stats] = None,
        shuffle: Optional[SmartShuffle] = None,
        engine: Optional[AudioEngine] = None,
        engine_kwargs: Optional[dict] = None,
    ):
        self.config = config or Config()
        self.library = library or Library(str(self.config.music_folder_path))
        self.stats = stats or Stats()
        self.shuffle = shuffle or SmartShuffle(t.path for t in self.library.tracks)
        # engine_kwargs: normalde BOŞTUR; sadece testte (örn. gerçek ses
        # kartı olmadan '--aout=dummy' vermek için) kullanılır -- bkz.
        # AudioEngine(extra_vlc_args=...). engine= zaten verilmişse yok sayılır.
        self.engine = engine or AudioEngine(
            on_track_finished=self._on_track_finished, **(engine_kwargs or {})
        )

        self._sequential_index: int = -1
        self._track_state_gen: int = 0
        self._current_playlist: Optional[str] = None
        self._current_playlist_tracks: List[str] = []

        # YouTube durumu (dict keyed by video_id for O(1) lookup)
        self._youtube_results: Dict[str, YoutubeResult] = {}
        self._youtube_mix_queue: List[str] = []
        self._yt_now_playing: Optional[dict] = None

        self._download_progress: Dict[str, dict] = {}
        self._download_lock = threading.Lock()

        self.engine.set_volume(0.0 if self.config.settings.muted else self.config.settings.volume)

        # TEK YAZAR kuyruğu -- yukarıdaki modül docstring'ine bakın.
        self._cmd_queue: "queue.Queue" = queue.Queue()
        self._worker_stop = threading.Event()
        # Worker şu an bir komut işliyor mu? (testler ve ileride "işleniyor"
        # göstergesi gibi ihtiyaçlar için faydalı, dışarıya salt-okunur bir sinyal.)
        self._worker_busy = threading.Event()
        self._worker = threading.Thread(
            target=self._worker_loop, name="boomusic-app-worker", daemon=True
        )
        self._worker.start()

    # -- Arka plan işlem kuyruğu ----------------------------------------------------
    def _worker_loop(self) -> None:
        while not self._worker_stop.is_set():
            try:
                cmd = self._cmd_queue.get(timeout=0.2)
            except queue.Empty:
                continue
            self._worker_busy.set()
            try:
                cmd()
            except Exception:
                logger.exception("Arka plan komutu çalıştırılırken hata oluştu")
            finally:
                self._worker_busy.clear()

    def is_busy(self) -> bool:
        """Worker şu an next/previous/vb. işliyor mu (fade nedeniyle birkaç
        saniye sürebilir). Kuyrukta bekleyen komutları da hesaba katar."""
        return self._worker_busy.is_set() or not self._cmd_queue.empty()

    def _submit(self, fn) -> None:
        self._cmd_queue.put(fn)

    # -- AudioEngine'den gelen geri çağırma -------------------------------------
    def _on_track_finished(self) -> None:
        """Bir parça kendiliğinden bittiğinde izleme thread'i tarafından çağrılır."""
        self._submit(self._do_next)

    # ============================================================================
    # DIŞA AÇIK API -- hepsi kuyruğa yazıp HEMEN döner (playback/shuffle durumunu
    # değiştiren TEK bir şey bile doğrudan/senkron çalışmaz; bkz. sınıf docstring'i).
    # ============================================================================
    def play_pause(self) -> None:
        self._submit(self._do_play_pause)

    def next(self) -> None:
        self._submit(self._do_next)

    def previous(self) -> None:
        self._submit(self._do_previous)

    def play_track_path(self, path: str) -> None:
        """Kullanıcının 'Şarkı Seç' listesinden ELLE seçtiği belirli bir parça."""
        self._submit(lambda: self._do_play_specific(path))

    def seek(self, seconds: float) -> None:
        self._submit(lambda: self.engine.seek_to(seconds))

    def toggle_shuffle(self) -> None:
        self._submit(self._do_toggle_shuffle)

    def rescan(self) -> None:
        self._submit(self._do_rescan)

    def set_volume_percent(self, percent: int) -> None:
        self._submit(lambda: self._do_set_volume_percent(percent))

    def toggle_mute(self) -> None:
        self._submit(self._do_toggle_mute)

    def open_volume_slider(self) -> None:
        """Varsa 'zenity' ile gerçek bir sürüklemeli ses kaydırıcısı açar.

        Bu, kuyruğa DEĞİL, kendi ayrı thread'ine gönderilir çünkü dakikalarca
        açık kalabilecek bloklayıcı bir dialog'dur; kuyrukta beklerse diğer
        tüm next/previous/vb. işlemleri o pencere kapanana kadar donardı.
        İçeride sesi değiştirirken yine de tek-yazar kuralına uymak için
        set_volume_percent() (kuyruklu) kullanılır.
        """
        threading.Thread(
            target=self._run_volume_slider, daemon=True, name="boomusic-volume-slider"
        ).start()

    # ============================================================================
    # GERÇEK İŞLER -- SADECE worker thread'inde çalışır (kuyruktan). Bunları
    # asla doğrudan çağırma; her zaman yukarıdaki _submit sarmalayıcılarından geç.
    # ============================================================================
    def _do_play_pause(self) -> None:
        if self.engine.current_path() is None:
            self._do_next()
            return
        self.engine.toggle_pause()

    def _do_next(self) -> None:
        self._track_state_gen += 1
        self._do_transition(self._next_path_getter())

    def _do_previous(self) -> None:
        self._track_state_gen += 1
        self._do_transition(self._previous_path_getter())

    def _do_play_specific(self, path: str) -> None:
        self._track_state_gen += 1

        playlist = self.library.playlist_name_for(path)
        self._current_playlist = playlist
        self._current_playlist_tracks = [t.path for t in self.library.get_tracks_for_playlist(playlist)]
        self.shuffle.set_tracks(self._current_playlist_tracks)

        def getter():
            result = self.shuffle.play_specific(path)
            if result is not None:
                try:
                    idx = self._current_playlist_tracks.index(path)
                    self._sequential_index = idx
                except ValueError:
                    pass
            return result

        self._do_transition(getter)

    def _next_path_getter(self):
        if self.config.settings.shuffle_enabled:
            return self.shuffle.next_track
        return self._sequential_next_path

    def _previous_path_getter(self):
        if self.config.settings.shuffle_enabled:
            return self.shuffle.previous_track
        return self._sequential_previous_path

    def _sequential_next_path(self) -> Optional[str]:
        tracks = self._current_playlist_tracks if self._current_playlist_tracks else [t.path for t in self.library.tracks]
        n = len(tracks)
        if n == 0:
            return None
        self._sequential_index = (self._sequential_index + 1) % n
        path = tracks[self._sequential_index]
        self.shuffle.play_specific(path)
        return path

    def _sequential_previous_path(self) -> Optional[str]:
        tracks = self._current_playlist_tracks if self._current_playlist_tracks else [t.path for t in self.library.tracks]
        n = len(tracks)
        if n == 0:
            return None
        if self._sequential_index < 0:
            self._sequential_index = n - 1
        else:
            self._sequential_index = (self._sequential_index - 1) % n
        path = tracks[self._sequential_index]
        self.shuffle.play_specific(path)
        return path

    def _do_transition(self, get_path) -> None:
        if not self.shuffle.has_tracks():
            return
        if self.engine.is_active() and not self.engine.is_paused():
            self.engine.stop(fade_out=True)
        path = get_path()
        self._load_and_play(path)

    def _load_and_play(self, path: Optional[str]) -> bool:
        if path is None:
            return False
        self._yt_now_playing = None
        track = self.library.find(path)
        duration = track.duration if track else None
        ok = self.engine.play(path, duration_seconds=duration)
        if not ok:
            return False
        self.stats.record_play(path)
        return True

    # -- Ses seviyesi (gerçek işler) ------------------------------------------------
    def _do_set_volume_percent(self, percent: int) -> None:
        new_vol = self.engine.set_volume(max(0, min(100, percent)) / 100.0)
        self.config.update(volume=new_vol, muted=False)

    def _do_toggle_mute(self) -> None:
        settings = self.config.settings
        if settings.muted:
            restore_to = settings.volume_before_mute if settings.volume_before_mute > 0 else 0.5
            self.engine.set_volume(restore_to)
            self.config.update(muted=False, volume=restore_to)
        else:
            current = self.engine.get_volume()
            remember = current if current > 0 else (settings.volume_before_mute or 0.5)
            self.engine.set_volume(0.0)
            self.config.update(muted=True, volume=0.0, volume_before_mute=remember)

    def _run_volume_slider(self) -> None:
        tool = shutil.which("zenity")
        if not tool:
            logger.warning("zenity kurulu değil, ses kaydırıcısı kullanılamaz")
            return
        original = self.volume_percent()
        try:
            proc = subprocess.Popen(
                [
                    tool, "--scale", "--title=Boomusic",
                    "--text=Ses seviyesi",
                    f"--value={original}",
                    "--min-value=0", "--max-value=100", "--step=1",
                    "--print-partial",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
            )
        except Exception:
            logger.exception("zenity başlatılamadı")
            return

        assert proc.stdout is not None
        for line in proc.stdout:
            line = line.strip()
            if line.isdigit():
                self.set_volume_percent(int(line))  # kuyruğa girer, tek-yazar korunur
        proc.wait()
        if proc.returncode != 0:
            self.set_volume_percent(original)

    # -- Shuffle (gerçek iş) --------------------------------------------------------
    def _do_toggle_shuffle(self) -> None:
        self._track_state_gen += 1
        new_value = not self.config.settings.shuffle_enabled
        if not new_value:
            current = self.engine.current_path()
            tracks = self._current_playlist_tracks if self._current_playlist_tracks else [t.path for t in self.library.tracks]
            try:
                idx = tracks.index(current) if current else -1
            except ValueError:
                idx = -1
            self._sequential_index = idx if idx >= 0 else -1
        self.config.update(shuffle_enabled=new_value)

    def shuffle_enabled(self) -> bool:
        return self.config.settings.shuffle_enabled

    # -- Kütüphane (gerçek iş) --------------------------------------------------------
    def _do_rescan(self) -> None:
        self._track_state_gen += 1
        current = self.engine.current_path()
        tracks = self.library.rescan()
        if self._current_playlist:
            self._current_playlist_tracks = [t.path for t in self.library.get_tracks_for_playlist(self._current_playlist)]
            self.shuffle.set_tracks(self._current_playlist_tracks)
        else:
            self.shuffle.set_tracks(t.path for t in tracks)
        if current:
            pool = self._current_playlist_tracks if self._current_playlist_tracks else [t.path for t in tracks]
            try:
                self._sequential_index = pool.index(current)
            except ValueError:
                self._sequential_index = -1

    def open_music_folder(self) -> None:
        subprocess.Popen(["xdg-open", str(self.config.music_folder_path)])

    # -- YouTube ---------------------------------------------------------------
    def _store_yt_results(self, results: List[YoutubeResult]) -> None:
        self._youtube_results = {r.video_id: r for r in results}

    def _build_yt_result_dict(self, r: YoutubeResult) -> dict:
        return {
            "type": "youtube",
            "video_id": r.video_id,
            "title": r.title,
            "subtitle": r.channel,
            "duration": r.duration,
            "thumbnail_url": r.thumbnail_url,
            "source": "youtube",
        }

    def search_local(self, query: str) -> List[dict]:
        query = query.strip().lower()
        if not query:
            return []
        results = []
        for t in self.library.tracks:
            if query in t.title.lower() or query in t.artist.lower():
                results.append({
                    "type": "local",
                    "path": t.path,
                    "title": t.display_name,
                    "subtitle": t.artist,
                    "duration": t.duration,
                    "source": "local",
                })
        return results

    def search_youtube(self, query: str) -> List[dict]:
        if not check_yt_dlp():
            logger.warning("yt-dlp kurulu değil, YouTube araması kullanılamaz")
            return []
        limit = self.config.settings.youtube_search_limit
        results = youtube_search(query, limit=limit)
        self._store_yt_results(results)
        return [r.to_dict() for r in results]

    def search_all(self, query: str) -> dict:
        query = query.strip().lower()
        if not query:
            return {"local": [], "youtube": []}

        local_results = []
        for t in self.library.tracks:
            if query in t.title.lower() or query in t.artist.lower():
                local_results.append({
                    "type": "local",
                    "path": t.path,
                    "title": t.display_name,
                    "subtitle": t.artist,
                    "duration": t.duration,
                    "source": "local",
                })

        youtube_results = []
        if not self.youtube_mix_enabled():
            return {"local": local_results, "youtube": youtube_results, "error": ""}
        if not check_yt_dlp():
            return {"local": local_results, "youtube": youtube_results, "error": "yt-dlp kurulu değil. YouTube araması için paket yöneticinizle yt-dlp kurun"}
        limit = self.config.settings.youtube_search_limit
        yt_results = youtube_search(query, limit=limit)
        if not yt_results:
            return {"local": local_results, "youtube": youtube_results, "error": "YouTube araması sonuç vermedi. yt-dlp güncel mi kontrol edin."}
        self._store_yt_results(yt_results)
        for r in yt_results:
            youtube_results.append(self._build_yt_result_dict(r))

        return {"local": local_results, "youtube": youtube_results}

    def get_youtube_results(self) -> List[dict]:
        return [r.to_dict() for r in self._youtube_results.values()]

    def clear_youtube_results(self) -> None:
        self._youtube_results.clear()

    def play_youtube(self, video_id: str) -> None:
        """YouTube şarkısını doğrudan çalar."""
        self._submit(lambda: self._do_play_youtube(video_id))

    def play_youtube_in_mix(self, video_id: str) -> None:
        """YouTube şarkısını yerel şarkılarla karışık moda ekler."""
        self._submit(lambda: self._do_play_youtube_in_mix(video_id))

    def toggle_youtube_mix(self) -> None:
        """YouTube + yerel karışık modu açar/kapatır."""
        self._submit(self._do_toggle_youtube_mix)

    def youtube_mix_enabled(self) -> bool:
        """YouTube + yerel karışık mod açık mı."""
        return self.config.settings.youtube_mix_with_local

    def _do_play_youtube(self, video_id: str) -> None:
        stream_url = youtube_get_stream_url(video_id)
        if not stream_url:
            return

        yt_result = self._youtube_results.get(video_id)
        path = f"youtube:{video_id}"
        title = yt_result.title if yt_result else "Bilinmeyen YouTube Şarkısı"
        channel = yt_result.channel if yt_result else ""
        duration = yt_result.duration if yt_result else None

        self._track_state_gen += 1
        self._yt_now_playing = {"title": title, "artist": channel}

        ok = self.engine.play(stream_url, duration_seconds=duration)
        if not ok:
            self._yt_now_playing = None
            return

        self.engine.set_current_path(path)
        self.stats.record_play(path)

    def _do_play_youtube_in_mix(self, video_id: str) -> None:
        """YouTube şarkısını karışık sıraya ekler ve çalar."""
        path = f"youtube:{video_id}"
        if path not in self._youtube_mix_queue:
            self._youtube_mix_queue.append(path)
        self._do_play_youtube(video_id)

    def _do_toggle_youtube_mix(self) -> None:
        """YouTube erişimini açar/kapatır."""
        new_value = not self.config.settings.youtube_mix_with_local
        self.config.update(youtube_mix_with_local=new_value)

    # -- YouTube İndirme -------------------------------------------------------
    def get_download_progress(self, key: str) -> Optional[dict]:
        with self._download_lock:
            return self._download_progress.get(key)

    def get_active_downloads(self) -> list:
        with self._download_lock:
            return [
                {"key": k, **v}
                for k, v in self._download_progress.items()
                if v.get("status") in ("downloading", "processing")
            ]

    def download_youtube(self, video_id: str) -> None:
        threading.Thread(
            target=self._do_download_youtube,
            args=(video_id,),
            daemon=True,
            name="boomusic-yt-download",
        ).start()

    def download_youtube_url(self, url: str) -> None:
        threading.Thread(
            target=self._do_download_youtube_url,
            args=(url,),
            daemon=True,
            name="boomusic-yt-url-download",
        ).start()

    def _update_dl_progress(self, key: str, percent: int, status: str, title: str) -> None:
        with self._download_lock:
            self._download_progress[key] = {"percent": percent, "status": status, "title": title}

    def _do_download_youtube(self, video_id: str) -> None:
        key = f"yt:{video_id}"
        yt_result = self._youtube_results.get(video_id)
        title = yt_result.title if yt_result else video_id
        output_dir = str(self.config.music_folder_path / DOWNLOAD_DIR_NAME)
        self._update_dl_progress(key, 0, "downloading", title)
        filepath = youtube_download(video_id, output_dir,
                                    progress_callback=lambda p: self._update_dl_progress(key, int(p), "downloading", title))
        if filepath:
            self._update_dl_progress(key, 100, "done", title)
            self._submit(self._do_rescan)
        else:
            self._update_dl_progress(key, 0, "error", title)

    def _do_download_youtube_url(self, url: str) -> None:
        key = f"url:{hash(url)}"
        title = "URL indirme"
        output_dir = str(self.config.music_folder_path / DOWNLOAD_DIR_NAME)
        self._update_dl_progress(key, 0, "downloading", title)
        filepath = youtube_download_url(url, output_dir,
                                        progress_callback=lambda p: self._update_dl_progress(key, int(p), "downloading", title))
        if filepath:
            self._update_dl_progress(key, 100, "done", os.path.basename(filepath))
            self._submit(self._do_rescan)
        else:
            self._update_dl_progress(key, 0, "error", title)

    def _do_create_playlist(self, name: str, description: str, cover_path: str) -> None:
        self.library.create_playlist(name)
        if description:
            self.library.set_playlist_meta(name, description=description)
        if cover_path:
            self.library.set_cover_from_file(name, cover_path)
        self._submit(self._do_rescan)

    def _do_edit_playlist(self, old_name: str, new_name: str, description: str, cover_path: str) -> None:
        if new_name != old_name:
            self.library.rename_playlist(old_name, new_name)
        target = new_name
        if description:
            self.library.set_playlist_meta(target, description=description)
        if cover_path:
            self.library.set_cover_from_file(target, cover_path)
        self._submit(self._do_rescan)

    def track_entries(self) -> List[TrackEntry]:
        """'Şarkı Seç' alt menüsü için: kütüphanedeki her parçanın küçük, SALT
        OKUNUR bir görünümü. Worker aynı anda bir şey değiştiriyorsa en kötü
        ihtimalle bir adım eski bilgi döner (zararsız, bkz. sınıf docstring'i).
        """
        return self._entries_for(self.library.tracks)

    MOST_PLAYED_NAME = "En Çok Dinlenenler"

    def playlists(self) -> List[dict]:
        """[{name, track_count, description, special?}] -- özel + alt klasör tabanlı."""
        result = []
        top = self.stats.top(9999)
        library_paths = {t.path for t in self.library.tracks}
        existing_top = [(p, c) for p, c in top if p in library_paths]
        result.append({
            "name": self.MOST_PLAYED_NAME,
            "track_count": len(existing_top),
            "description": "En çok dinlediğin şarkılar",
            "special": True,
        })
        for name, tracks in self.library.playlists():
            meta = self.library.playlist_meta(name)
            result.append({"name": name, "track_count": len(tracks), "description": meta.get("description", "")})
        return result

    def get_playlist_info(self, name: str) -> dict:
        meta = self.library.playlist_meta(name)
        cover = self.library.get_cover_data_uri(name)
        return {"name": name, "description": meta.get("description", ""), "cover": cover or ""}

    def create_playlist(self, name: str, description: str = "", cover_path: str = "") -> None:
        self._submit(lambda: self._do_create_playlist(name, description, cover_path))

    def edit_playlist(self, old_name: str, new_name: str, description: str = "", cover_path: str = "") -> None:
        self._submit(lambda: self._do_edit_playlist(old_name, new_name, description, cover_path))

    def get_playlist_cover(self, name: str) -> Optional[str]:
        return self.library.get_cover_data_uri(name)

    def set_playlist_cover(self, name: str, source_path: str) -> Optional[str]:
        return self.library.set_cover_from_file(name, source_path)

    def add_file_to_playlist(self, playlist_name: str, source_path: str, display_name: str, artist: str) -> None:
        self._submit(lambda: self._do_add_file_to_playlist(playlist_name, source_path, display_name, artist))

    def remove_track(self, path: str) -> bool:
        """Bir şarkıyı diskten siler. Worker'da çalışır: eğer o an
        çalıyorsa önce engine durdurulur, böylece VLC dosyayı tutmaz.
        True: silindi, False: silinemedi (dosya yok, izin yok, vs.)."""
        result_box = {"ok": False}
        def _worker():
            # Eğer bu şarkı o an çalıyorsa durdur (dosya silinmeden önce
            # VLC tutuyor olabilir; OS dosya silmeye izin verse de
            # "playing removed file" durumu oluşur).
            if self.engine.current_path() == path:
                self.engine.stop()
            result_box["ok"] = self.library.remove_track(path)
            self._submit(self._do_rescan)
        self._submit(_worker)
        return result_box["ok"]  # best-effort sync answer; gerçek sonuç rescan'de

    def delete_playlist(self, name: str) -> None:
        """Playlist'in klasörünü tamamen siler (tüm şarkılar + meta).
        Eğer silinen playlist o an seçiliyse 'Genel'e geçilir; silinen
        playlist'te çalan şarkı varsa engine durdurulur.

        JS köprüsü `.then(refresh)` ile hemen ardından state çektiği
        için (silinen playlist menüde gözükmesin diye) BURADA işin
        bitmesini bekliyoruz. Normalde _submit fire-and-forget; ama
        bu çağrı kısa (rmtree + rescan) ve pywebview köprüsü ana
        thread'de DEĞİL, ayrı bir thread'de — bu yüzden beklemek
        GUI'yi bloklamaz, sadece bridge thread'ini (max 10s)."""
        done = threading.Event()
        ok_box = {"ok": True}
        def _worker():
            try:
                if self._current_playlist == name:
                    self._current_playlist = None
                    self._current_playlist_tracks = []
                # Silinen playlist'te çalan şarkı varsa durdur
                cur = self.engine.current_path()
                if cur:
                    try:
                        cur_pl = self.library.playlist_name_for(cur)
                        if cur_pl == name:
                            self.engine.stop()
                    except Exception:
                        pass
                try:
                    self.library.delete_playlist(name)
                except ValueError as e:
                    logger.warning("delete_playlist başarısız: %s", e)
                    ok_box["ok"] = False
                    return
                # Rescan'ı KENDİMİZ çağırıp bitmesini bekle; bu sayede
                # JS'in hemen ardından get_state() çekmesi fresh data görür.
                self._do_rescan()
            finally:
                done.set()
        self._submit(_worker)
        # pywebview köprüsü ayrı thread'de çalışır; beklemek GUI'yi
        # bloklamaz. 10s üst limit: sonsuz bekleme koruması.
        done.wait(timeout=10.0)

    def get_all_playlists(self) -> list:
        """Tüm playlist'lerin adlarını düz liste olarak döner (context menu
        'Şu playliste ekle' alt menüsü için)."""
        return [p["name"] for p in self.playlists() if p["name"] != self._current_playlist]

    MIME_EXT_MAP = {
        "mpeg": "mp3", "mp3": "mp3", "mp4": "m4a", "x-m4a": "m4a",
        "flac": "flac", "ogg": "ogg", "vorbis": "ogg", "opus": "opus",
        "wav": "wav", "wma": "wma", "aac": "aac", "x-aac": "aac",
    }

    def _do_add_file_to_playlist(self, playlist_name: str, source_path: str, display_name: str, artist: str) -> None:
        folder = self.library._folder_for_playlist(playlist_name)
        folder.mkdir(parents=True, exist_ok=True)
        if source_path.startswith("data:"):
            header, _, b64data = source_path.partition(",")
            raw = base64.b64decode(b64data)
            raw_mime = header.split(";")[0].split("/")[-1] if "/" in header else "mpeg"
            ext = "." + self.MIME_EXT_MAP.get(raw_mime, raw_mime)
        else:
            source = Path(source_path)
            if not source.exists():
                logger.warning("Kaynak dosya mevcut değil: %s", source_path)
                return
            raw = source.read_bytes()
            ext = source.suffix
        safe_name = "".join(c for c in display_name if c.isalnum() or c in " ._-()[]'\"!,").strip() or "dosya"
        dest = folder / f"{safe_name}{ext}"
        counter = 1
        while dest.exists():
            dest = folder / f"{safe_name}_{counter}{ext}"
            counter += 1
        dest.write_bytes(raw)
        if artist:
            self.library.set_track_meta(playlist_name, dest.name, display_name, artist)
        self._submit(self._do_rescan)

    def tracks_in_playlist(self, name: Optional[str]) -> List[TrackEntry]:
        """Belirli bir 'çalma listesi'ndeki şarkılar. name=None
        ya da bulunamazsa TÜM kütüphaneyi döner (güvenli varsayılan)."""
        if name == self.MOST_PLAYED_NAME:
            entries = self._entries_for(self.library.tracks)
            entries.sort(key=lambda e: e.play_count, reverse=True)
            return [e for e in entries if e.play_count > 0]
        for pl_name, tracks in self.library.playlists():
            if pl_name == name:
                return self._entries_for(tracks, pl_name)
        return self.track_entries()

    def _entries_for(self, tracks, playlist_name=None) -> List[TrackEntry]:
        current = self.engine.current_path()
        meta = {}
        if playlist_name:
            meta = self.library.get_track_meta(playlist_name)
        entries = []
        for t in tracks:
            fname = Path(t.path).name
            custom = meta.get(fname, {})
            title = custom.get("title") or t.title
            artist = custom.get("artist") or t.artist
            display = f"{artist} - {title}" if artist else title
            entries.append(
                TrackEntry(
                    path=t.path,
                    display_name=display,
                    is_current=(t.path == current),
                    played_this_round=self.shuffle.is_played_this_round(t.path),
                    play_count=self.stats.get_count(t.path),
                )
            )
        return entries

    # -- İstatistikler --------------------------------------------------------------
    def show_top_stats(self, n: int = 5) -> None:
        pass

    def notifications_enabled(self) -> bool:
        return self.config.settings.notifications_enabled

    # -- Tray menüsü için durum bilgisi (salt okunur getter'lar) ----------------------
    def now_playing_display(self) -> str:
        path = self.engine.current_path()
        if not path:
            return "Şu an bir şey çalmıyor"
        if self._yt_now_playing:
            return f"{self._yt_now_playing['title']} - {self._yt_now_playing['artist']}"
        return self.library.display_name_for(path)

    def is_paused(self) -> bool:
        return self.engine.is_paused()

    def is_playing(self) -> bool:
        return self.engine.is_active() and not self.engine.is_paused()

    def volume_percent(self) -> int:
        return round(self.engine.get_volume() * 100)

    def is_muted(self) -> bool:
        return self.config.settings.muted

    def track_count(self) -> int:
        return len(self.library)

    def current_play_count(self) -> int:
        path = self.engine.current_path()
        if not path:
            return 0
        return self.stats.get_count(path)

    def position_seconds(self) -> float:
        return self.engine.get_position_seconds()

    def duration_seconds(self) -> float:
        path = self.engine.current_path()
        track = self.library.find(path) if path else None
        engine_dur = self.engine.get_duration_seconds()
        if engine_dur > 0:
            return engine_dur
        return track.duration if (track and track.duration) else 0.0

    def playback_state(self) -> dict:
        """GUI'nin periyodik olarak (örn. her 500ms) sorgulayacağı, tüm
        çalma durumunu tek seferde veren TOPLU bir anlık görüntü."""
        path = self.engine.current_path()
        if self._yt_now_playing:
            title = self._yt_now_playing["title"]
            artist = self._yt_now_playing["artist"]
            track = None
        elif path:
            track = self.library.find(path) if path else None
            title = track.title if track else None
            artist = track.artist if track else ""
        else:
            track = None
            title = None
            artist = ""
        return {
            "path": path,
            "title": title,
            "artist": artist,
            "playlist": None if self._yt_now_playing else (self.library.playlist_name_for(path) if path else None),
            "is_playing": self.is_playing(),
            "is_paused": self.is_paused(),
            "position": self.position_seconds(),
            "duration": self.duration_seconds(),
            "play_count": self.current_play_count(),
            "volume_percent": self.volume_percent(),
            "is_muted": self.is_muted(),
            "shuffle_enabled": self.shuffle_enabled(),
            "nowplaying_visible": self.config.settings.nowplaying_visible,
            "track_count": self.track_count(),
            "track_state_gen": self._track_state_gen,
            "youtube_mix_enabled": self.youtube_mix_enabled(),
        }

    # -- Kapatma ------------------------------------------------------------------------
    def shutdown(self) -> None:
        logger.info("Boomusic kapatılıyor...")
        self._worker_stop.set()
        self.stats.flush()
        try:
            self.engine.shutdown()
        finally:
            self.config.save()
