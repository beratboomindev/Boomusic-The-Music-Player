"""pywebview tabanlı masaüstü penceresi.

Bu modül SUNUM ile ilgilenir; iş mantığının tamamı yine ``app.py``'dedir
(tıpkı ``tray.py`` gibi). ``JsApi`` sınıfı, pencere içindeki HTML/JS'in
``window.pywebview.api.<method>()`` üzerinden çağırabileceği metotları
tanımlar; pywebview bu çağrıları otomatik olarak Python <-> JS köprüsünden
geçirir (JS tarafında bir Promise döner).

NOT: Bu dosyanın çalışması için bir masaüstü ortamı VE bir webview arka
ucu (GTK+WebKit2GTK ya da Qt+QtWebEngine) gerekir. Görüntü sunucusu
olmayan bir ortamda (örn. otomatik testlerde) sadece import edilip
``JsApi`` sınıfı bağımsız test edilebilir; ``GuiWindow.start()`` çalıştırılamaz.
"""
from __future__ import annotations

import base64
import logging
import os
import shutil
import subprocess
import threading
from pathlib import Path
from typing import Optional

import webview

from .app import App

logger = logging.getLogger("boomusic.gui")

HTML_PATH = Path(__file__).parent / "assets" / "gui.html"
ICON_PATH = Path(__file__).parent / "assets" / "icon.png"

# Pencere WM_CLASS'ını ayarlamak için GTK kütüphanesini tembel yükle
# (pywebview GTK backend'i kullanıyorsa çalışır; yoksa sessizce yoksayılır).
try:
    import gi
    gi.require_version("Gtk", "3.0")
    from gi.repository import Gtk, GLib, Gdk
    _HAS_GTK = True
except Exception:
    _HAS_GTK = False


def _screen_size() -> tuple:
    """Ekran çözünürlüğünü döner (width, height). GTK yoksa varsayılan 1920x1080."""
    if _HAS_GTK:
        try:
            display = Gdk.Display.get_default()
            if display:
                monitor = display.get_monitor(0)
                if monitor:
                    geo = monitor.get_geometry()
                    return (geo.width, geo.height)
        except Exception:
            pass
    return (1920, 1080)


def _window_size() -> tuple:
    """Pencere boyutunu ekran çözünürlüğüne göre hesaplar.

    Hem büyük monitörlerde aşırı küçük kalmaması için oransal büyütme YAPAR,
    hem de küçük ekranlarda (örn. 1280x720 netbook) pencerenin ekranı
    taşırmaması için şu güvenli sınırları uygular:
      - minimum: 480x380  (HTML'in min_size'ı)
      - maksimum: ekran boyutunun %95'i (kenarlarda biraz pay bırakır;
        WM'in başlık çubuğu / kenar boşlukları için gerekli, yoksa pencere
        ekranın altını taşırır ve ulaşılamaz hale gelir)
      - ayrıca en az 360px yükseklik farkı bırakırız (ekran-yükseklik
        eşiği 380'in altına düşerse otomatik küçültürüz, böylece 1366x768
        bir dizüstünde bile içerik görünür kalır).
    """
    sw, sh = _screen_size()
    min_w, min_h = 480, 380

    # Oransal hedef boyut (yüksek DPI / büyük monitör için)
    target_w = max(min_w, int(sw * 0.70))
    target_h = max(min_h, int(sh * 0.78))

    # Küçük ekranlarda ekrana sığması için clamp et
    cap_w = max(min_w, int(sw * 0.95))
    cap_h = max(min_h, int(sh * 0.90))  # 0.90: WM kenarlıkları için pay

    w = min(target_w, cap_w)
    h = min(target_h, cap_h)

    return (w, h)


def _inject_brand_icon(html: str) -> str:
    icon_path = Path(__file__).parent / "assets" / "icon.png"
    try:
        with open(icon_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        uri = f"data:image/png;base64,{b64}"
        return html.replace("__BOOMUSIC_ICON__", uri)
    except Exception:
        return html.replace("__BOOMUSIC_ICON__", "")


class JsApi:
    """Pencere içindeki JS'in çağırdığı köprü sınıfı.

    Tüm gerçek iş mantığı ``self.app`` (App) üzerinden yürür; burada
    sadece App'in metotlarına ince bir sarmalayıcı ve GUI'ye özgü "hangi
    çalma listesi şu an görüntüleniyor" gibi SUNUMA özgü, geçici durum var.
    """

    def __init__(self, app: App):
        self.app = app
        self.window: Optional["webview.Window"] = None  # GuiWindow tarafından sonradan atanır
        self._selected_playlist: Optional[str] = None
        self._cached_track_gen: int = -1
        self._cached_tracks: list = []
        self._cached_playlist_name: Optional[str] = None

    # -- Durum ------------------------------------------------------------------
    def get_state(self) -> dict:
        state = self.app.playback_state()
        playlists = self.app.playlists()
        if self._selected_playlist is None and playlists:
            self._selected_playlist = playlists[0]["name"]
        state["playlists"] = playlists
        state["selected_playlist"] = self._selected_playlist
        gen = state["track_state_gen"]
        if gen != self._cached_track_gen or self._selected_playlist != self._cached_playlist_name:
            self._cached_track_gen = gen
            self._cached_playlist_name = self._selected_playlist
            tracks = self.app.tracks_in_playlist(self._selected_playlist)
            self._cached_tracks = [
                {
                    "path": t.path,
                    "name": t.display_name,
                    "is_current": t.is_current,
                    "played_this_round": t.played_this_round,
                    "play_count": t.play_count,
                }
                for t in tracks
            ]
        state["tracks"] = self._cached_tracks
        state["youtube_mix_enabled"] = self.app.youtube_mix_enabled()
        return state

    def select_playlist(self, name: str) -> dict:
        self._selected_playlist = name
        return self.get_state()

    def get_settings(self) -> dict:
        return {
            "music_folder": str(self.app.config.music_folder_path),
            "nowplaying_visible": self.app.config.settings.nowplaying_visible,
            "youtube_mix_enabled": self.app.youtube_mix_enabled(),
            "internet_enabled": self.app.youtube_mix_enabled(),
            "font_family": self.app.config.settings.font_family,
            "language": self.app.config.settings.language,
            "sidebar_width": int(self.app.config.settings.sidebar_width),
        }

    def set_font(self, family: str) -> None:
        self.app.config.update(font_family=family)

    def set_language(self, lang: str) -> None:
        self.app.config.update(language=lang)

    def set_sidebar_width(self, width: int) -> None:
        """Kullanıcının sürükleyerek ayarladığı sidebar genişliğini kaydeder.

        JS tarafı 140..400 aralığında clamp'leyip gönderir; biz yine de
        burada savunma amaçlı tekrar clamp'liyoruz. Ayar, pencere kapatıldıktan
        veya monitör değiştirildikten sonra bile korunur (config.json'a yazılır).
        """
        try:
            w = int(width)
        except (TypeError, ValueError):
            return
        w = max(140, min(400, w))
        self.app.config.update(sidebar_width=w)

    def get_cover(self, playlist_name: str) -> Optional[str]:
        return self.app.get_playlist_cover(playlist_name)

    def pick_playlist_cover(self, playlist_name: str) -> Optional[str]:
        """Native dosya seçiciyi açar; seçilen resmi bu çalma listesinin
        kapağı olarak kaydeder ve yeni kapağın data URI'sini döner."""
        if self.window is None:
            return None
        try:
            result = self.window.create_file_dialog(
                webview.OPEN_DIALOG,
                file_types=("Resim Dosyaları (*.jpg;*.jpeg;*.png;*.webp;*.bmp)", "Tüm Dosyalar (*.*)"),
            )
        except Exception:
            logger.exception("Kapak resmi seçme penceresi açılamadı")
            return None
        if not result:
            return None
        return self.app.set_playlist_cover(playlist_name, result[0])

    def get_playlist_info(self, name: str) -> dict:
        return self.app.get_playlist_info(name)

    def create_playlist(self, name: str, description: str = "", cover_path: str = "") -> None:
        self.app.create_playlist(name, description, cover_path)

    def edit_playlist(self, old_name: str, new_name: str, description: str = "", cover_path: str = "") -> None:
        self.app.edit_playlist(old_name, new_name, description, cover_path)

    def delete_playlist(self, name: str) -> None:
        """Playlist'i (klasör + tüm şarkılar + meta) siler."""
        self.app.delete_playlist(name)

    def add_file_to_playlist(self, playlist_name: str, source_path: str, display_name: str, artist: str = "") -> None:
        self.app.add_file_to_playlist(playlist_name, source_path, display_name, artist)

    def remove_track(self, path: str) -> bool:
        """Bir şarkıyı diskten siler. O an çalıyorsa önce durdurur."""
        return self.app.remove_track(path)

    def get_all_playlists(self) -> list:
        """Tüm playlist adlarını döner (context menu 'Şu playliste ekle' için)."""
        return self.app.get_all_playlists()

    def copy_to_clipboard(self, text: str) -> bool:
        """Metni sistem panosuna kopyalar (webkit2gtk clipboard API'si
        üzerinden). Webview'da 'document.execCommand(\"copy\")' modern
        webview'lerde güvenlik nedeniyle çalışmaz; bu yüzden native
        API'yi kullanıyoruz.

        Eğer ileride webkit clipboard API'si değişirse, burası tek güncelleme
        noktası olur."""
        try:
            from .platform_clipboard import copy_text
            return copy_text(text)
        except Exception:
            logger.exception("Pano kopyalama başarısız")
            return False

    def open_file_in_default_app(self, path: str) -> None:
        """Dosyayı sistemdeki varsayılan uygulamayla açar (dosya yöneticisi,
        müzik çalar, video oynatıcı vs. — kullanıcının seçtiği uzantıya
        göre değişir). 'Cihazdan kaldır' alternatif olarak 'şarkıyı göster'
        için kullanışlı."""
        try:
            import subprocess
            subprocess.Popen(["xdg-open", path])
        except Exception:
            logger.exception("Dosya açılamadı: %s", path)

    def pick_image_file(self) -> Optional[str]:
        """Native dosya seçici açar, seçilen resim dosyasının yolunu döner."""
        if self.window is None:
            return None
        try:
            result = self.window.create_file_dialog(
                webview.OPEN_DIALOG,
                file_types=("Resim Dosyaları (*.jpg;*.jpeg;*.png;*.webp;*.bmp)", "Tüm Dosyalar (*.*)"),
            )
        except Exception:
            logger.exception("Dosya seçme penceresi açılamadı")
            return None
        if not result:
            return None
        return result[0]

    # -- YouTube ---------------------------------------------------------------
    def search_local(self, query: str) -> list:
        """Yerel kütüphanede şarkı arar."""
        return self.app.search_local(query)

    def search_youtube(self, query: str) -> list:
        """YouTube Music'te şarkı/podcast arar."""
        return self.app.search_youtube(query)

    def search_all(self, query: str) -> dict:
        """Yerel ve YouTube'da birlikte arar."""
        return self.app.search_all(query)

    def get_youtube_results(self) -> list:
        """Mevcut YouTube arama sonuçlarını döner."""
        return self.app.get_youtube_results()

    def play_youtube(self, video_id: str) -> None:
        """YouTube şarkısını doğrudan çalar."""
        if not self.app.youtube_mix_enabled():
            return
        self.app.play_youtube(video_id)

    def play_youtube_in_mix(self, video_id: str) -> None:
        """YouTube şarkısını yerel şarkılarla karışık moda ekler."""
        if not self.app.youtube_mix_enabled():
            return
        self.app.play_youtube_in_mix(video_id)

    def toggle_youtube_mix(self) -> None:
        """YouTube + yerel karışık modu açar/kapatır."""
        self.app.toggle_youtube_mix()

    def clear_youtube_search(self) -> None:
        """YouTube arama sonuçlarını temizler."""
        self.app.clear_youtube_results()

    def download_youtube(self, video_id: str) -> None:
        """YouTube şarkısını MP3 olarak indirir."""
        if not self.app.youtube_mix_enabled():
            return
        self.app.download_youtube(video_id)

    def download_youtube_url(self, url: str) -> None:
        """YouTube linkiyle MP3 indirir."""
        if not self.app.youtube_mix_enabled():
            return
        self.app.download_youtube_url(url)

    def get_download_progress(self, key: str) -> Optional[dict]:
        """İndirme progress'ini döner."""
        return self.app.get_download_progress(key)

    def get_active_downloads(self) -> list:
        """Devam eden indirmeleri döner."""
        return self.app.get_active_downloads()

    # -- Aksiyonlar (hepsi App'in zaten kuyruklu/thread-safe metotlarını çağırır) --
    def play_pause(self) -> None:
        self.app.play_pause()

    def next(self) -> None:
        self.app.next()

    def previous(self) -> None:
        self.app.previous()

    def play_track(self, path: str) -> None:
        self.app.play_track_path(path)

    def seek(self, seconds) -> None:
        self.app.seek(float(seconds))

    def set_volume(self, percent) -> None:
        self.app.set_volume_percent(int(percent))

    def toggle_mute(self) -> None:
        self.app.toggle_mute()

    def toggle_shuffle(self) -> None:
        self.app.toggle_shuffle()

    def rescan(self) -> None:
        self.app.rescan()

    def open_music_folder(self) -> None:
        self.app.open_music_folder()

    def toggle_nowplaying_panel(self) -> None:
        self.app.config.update(nowplaying_visible=not self.app.config.settings.nowplaying_visible)

    def quit_app(self) -> None:
        """Ayarlar panelindeki 'Çıkış' -- garantili kapanış.

        pywebview'in `window.destroy()` çağrısı bazı durumlarda (webkit
        çakışması, webview zaten kapanmışsa, vs.) sessizce takılıp
        kalabiliyor. Bu yüzden 'normal yol' denenir; olmazsa 1 saniye
        sonra süreç SIGKILL ile zorla öldürülür (tüm thread'ler dahil,
        Python yorumlayıcısı durdurulur). SIGKILL'ın geri dönüşü yoktur
        ama bu KAPANIŞ çağrısı; audio engine zaten shutdown edildi, log
        dosyaları zaten yazıldı, geriye yazılacak bir şey kalmadı.
        """
        import signal as _sig
        if self.window is not None:
            try:
                self.window.destroy()
            except Exception:
                logger.exception("Pencere kapatılamadı (quit_app)")
        # SIGKILL = 9; Linux'ta thread'ler dahil süreç garantili ölür.
        # 1 saniye, 'normal kapanış' için tanınan süre; pywebview/GI bunu
        # kullanmazsa zorla öldür.
        def _kill():
            try:
                os.kill(os.getpid(), _sig.SIGKILL)
            except Exception:
                os._exit(0)
        threading.Timer(1.0, _kill).start()

    def enter_just_icon_mode(self) -> bool:
        """Ayarlar panelindeki 'Sadece İkon Moduna Geç' butonu için.

        Davranış (eski tasarımdan farklı):
          1) 'boomusic-tray' launcher'ını arka planda başlatır.
          2) ~0.7 sn sonra GUI SÜRECİNİ tamamen kapatır (SIGKILL ile).
             Bu, artık iki ayrı tray simgesinin aynı anda durmaması
             içindir; önceki tasarımda GUI sadece gizleniyordu, simgesi
             arka planda kalmaya devam ediyordu.

        Geri dönüş: kullanıcı yeni Just Icon simgesinin menüsündeki
        'Boomusic'i Göster' öğesine tıkladığında tray subprocess olarak
        yeni bir GUI başlatır (kendi lock dosyası var, çakışma olmaz).
        """
        launcher = os.path.expanduser("~/.local/bin/boomusic-tray")
        if not os.path.isfile(launcher):
            logger.error("boomusic-tray launcher bulunamadı: %s", launcher)
            return False
        try:
            subprocess.Popen(
                [launcher],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                start_new_session=True,
            )
        except Exception:
            logger.exception("boomusic-tray başlatılamadı")
            return False
        # Just Icon lock dosyasını oluşturması ve kullanıcının yeni simgeyi
        # görmesi için yarım saniye bekle; sonra GUI'yi öldür.
        threading.Timer(0.7, self._kill_after_just_icon_launch).start()
        return True

    def _kill_after_just_icon_launch(self) -> None:
        """enter_just_icon_mode'tan ~0.7 sn sonra GUI SÜRECİNİ tamamen
        sonlandırır. quit_app'tekiyle aynı SIGKILL mekanizması; sadece
        pencere destroy ATLANIR çünkü zaten yeni bir GUI başlatılacak,
        mevcut pencereyi gizlemeye/destroy etmeye gerek yok."""
        import signal as _sig
        try:
            os.kill(os.getpid(), _sig.SIGKILL)
        except Exception:
            os._exit(0)

    def pick_music_folder(self) -> Optional[str]:
        if self.window is None:
            return None
        try:
            result = self.window.create_file_dialog(webview.FOLDER_DIALOG)
        except Exception:
            logger.exception("Klasör seçme penceresi açılamadı")
            return None
        if not result:
            return None
        folder = result[0]
        self.app.config.update(music_folder=folder)
        self.app.library.set_folder(folder)
        self.app.rescan()
        self._selected_playlist = None  # yeni klasörle birlikte sıfırla
        return folder


class GuiWindow:
    def __init__(self, app: App):
        self.app = app
        self.api = JsApi(app)
        html = _inject_brand_icon(HTML_PATH.read_text(encoding="utf-8"))
        win_w, win_h = _window_size()
        self.window = webview.create_window(
            "Boomusic - The Music Player",
            html=html,
            js_api=self.api,
            width=win_w,
            height=win_h,
            min_size=(480, 380),
            background_color="#121218",
        )
        self.api.window = self.window
        self.window.events.closing += self._on_closing

        # Görev çubuğunda "python3" yerine "Boomusic" görünmesi için
        # GTK penceresinin WM_CLASS'ını ayarla (başlangıçta bir kere).
        if _HAS_GTK:
            def _set_wmclass():
                try:
                    native = self.window.gui.window
                    if hasattr(native, "set_wmclass"):
                        native.set_wmclass("boomusic", "Boomusic")
                    icon_path = str(ICON_PATH)
                    if hasattr(native, "set_icon_from_file"):
                        native.set_icon_from_file(icon_path)
                    elif hasattr(native, "set_icon"):
                        from gi.repository import GdkPixbuf
                        pixbuf = GdkPixbuf.Pixbuf.new_from_file(icon_path)
                        native.set_icon(pixbuf)
                except Exception:
                    pass
                return False
            GLib.idle_add(_set_wmclass)

    def _on_closing(self):
        # Pencerenin kapat (X) düğmesi uygulamayı SONLANDIRMAZ, sadece
        # pencereyi gizler -- tepsi simgesi zaten arka planda çalışmaya
        # devam eder. Gerçek çıkış tepsi menüsündeki "Çıkış"tandır.
        self.window.hide()
        return False  # varsayılan kapatma davranışını iptal et

    def show(self) -> None:
        try:
            self.window.show()
        except Exception:
            logger.exception("Pencere gösterilemedi")

    def hide(self) -> None:
        try:
            self.window.hide()
        except Exception:
            logger.exception("Pencere gizlenemedi")

    def quit(self) -> None:
        """Pencereyi GERÇEKTEN kapatır (gizlemez). Paylaşılan GTK döngüsü
        (webview.start()) tüm pencereler kapanınca sona erer; bu yüzden
        "Çıkış" burayı çağırmalı, sadece tray.stop()'u değil -- aksi halde
        ana thread webview döngüsünde bloke kalmaya devam eder."""
        try:
            self.window.destroy()
        except Exception:
            logger.exception("Pencere kapatılamadı (destroy)")

    def start(self) -> None:
        """pywebview'in kendi mainloop'unu başlatır. BLOKE OLUR; ana
        thread'den çağrılmalıdır (bkz. __main__.py)."""
        webview.start()
