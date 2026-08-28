"""Müzik klasörünü tarayıp çalınabilir parçaların (Track) listesini çıkarır."""
from __future__ import annotations

import base64
import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("boomusic.library")

SUPPORTED_EXTENSIONS = {".mp3", ".ogg", ".oga", ".wav", ".flac"}
COVER_FILENAME = "cover.jpg"
MAX_COVER_DIMENSION = 600  # kapak için gereksiz büyük dosyaları küçültüyoruz

try:
    from mutagen import File as _MutagenFile
    _HAS_MUTAGEN = True
except Exception:  # mutagen kurulu değilse dosya adını kullanmaya devam ederiz
    _HAS_MUTAGEN = False

try:
    from PIL import Image
    _HAS_PIL = True
except Exception:
    _HAS_PIL = False


@dataclass(frozen=True)
class Track:
    path: str
    title: str
    artist: str = ""
    duration: Optional[float] = None  # saniye; okunamazsa None
    source: str = "local"  # "local" veya "youtube"
    thumbnail_url: str = ""
    youtube_video_id: str = ""

    @property
    def display_name(self) -> str:
        if self.artist:
            return f"{self.artist} - {self.title}"
        return self.title

    @property
    def is_youtube(self) -> bool:
        return self.source == "youtube"


def _read_metadata(file_path: Path) -> Tuple[str, str, Optional[float]]:
    title = file_path.stem
    artist = ""
    duration: Optional[float] = None
    if not _HAS_MUTAGEN:
        return title, artist, duration
    try:
        audio = _MutagenFile(file_path, easy=True)
        if audio is not None:
            if audio.tags:
                title_tag = audio.tags.get("title")
                artist_tag = audio.tags.get("artist")
                if title_tag:
                    title = str(title_tag[0]).strip() or title
                if artist_tag:
                    artist = str(artist_tag[0]).strip()
            if getattr(audio, "info", None) is not None:
                length = getattr(audio.info, "length", None)
                if isinstance(length, (int, float)) and length > 0:
                    duration = float(length)
    except Exception:
        # Etiket/süre okunamazsa dosya adıyla ve süresiz devam ederiz;
        # müzik çalmayı bu yüzden durdurmaya değmez.
        pass
    return title, artist, duration


def scan_folder(folder: str) -> List[Track]:
    """Klasörü (ve alt klasörlerini) tarar, desteklenen ses dosyalarını döner.

    Sonuç dosya yoluna göre alfabetik sıralanır; böylece art arda taramalar
    tutarlı bir sıra üretir (shuffle kendi rastgeleliğini, sıralı mod ise
    bu sırayı kullanır).
    """
    root = Path(folder).expanduser()
    tracks: List[Track] = []
    if not root.exists():
        return tracks
    for entry in sorted(root.rglob("*")):
        if entry.is_file() and entry.suffix.lower() in SUPPORTED_EXTENSIONS:
            title, artist, duration = _read_metadata(entry)
            tracks.append(Track(path=str(entry), title=title, artist=artist, duration=duration))
    return tracks


class Library:
    DEFAULT_PLAYLIST_NAME = "Genel"

    def __init__(self, folder: str):
        self.folder = folder
        self.tracks: List[Track] = []
        self._by_path: Dict[str, Track] = {}
        self._by_index: Dict[str, int] = {}
        self._playlist_cache: Optional[List[Tuple[str, List[Track]]]] = None
        self._meta_cache: Dict[str, tuple] = {}  # name -> (timestamp, dict)
        self.rescan()

    def _invalidate_cache(self) -> None:
        self._playlist_cache = None
        self._meta_cache.clear()

    def rescan(self) -> List[Track]:
        self.tracks = scan_folder(self.folder)
        self._by_path = {t.path: t for t in self.tracks}
        self._by_index = {t.path: i for i, t in enumerate(self.tracks)}
        self._invalidate_cache()
        return self.tracks

    def set_folder(self, folder: str) -> List[Track]:
        self.folder = folder
        return self.rescan()

    def find(self, path: str) -> "Track | None":
        return self._by_path.get(path)

    def display_name_for(self, path: str) -> str:
        track = self.find(path)
        if track:
            return track.display_name
        return Path(path).stem

    def index_of(self, path: str) -> Optional[int]:
        return self._by_index.get(path)

    def playlists(self):
        """Diskteki tüm alt klasörleri çalma listesi olarak listeler.

        Üç kaynaktan üretilir:
        1) Track'lerin bulunduğu klasörler (mevcut tasarım).
        2) İçinde şarkı olmasa bile diskte VAR olan alt klasörler ("yeni
           çalma listesi" ile oluşturulmuş ama henüz şarkı atılmamış
           olanlar dahil).
        3) "Genel" (müzik kökünün kendisi) -- eğer kök-dizinde şarkı
           varsa zaten 1. maddeden gelir; ama kullanıcı tüm müziğini
           alt klasörlere koymuşsa bile "Genel" listenin VAR olduğu
           gösterilir (içine sürükle-bırak ile şarkı atabilsin diye).

        "Genel" her zaman ilk sırada, sonra diskteki alt klasörler
        alfabetik sırayla. Boş playlist'ler 0 şarkı gösterir.
        """
        if self._playlist_cache is not None:
            return self._playlist_cache
        root = Path(self.folder).expanduser()

        # Önce track'lerden grupları çıkar.
        groups: Dict[str, list] = {}
        for t in self.tracks:
            group_name = self.playlist_name_for(t.path)
            groups.setdefault(group_name, []).append(t)

        # Sonra diskteki tüm alt klasörleri gez; içinde şarkı OLMAYAN ama
        # klasör olarak VAR olan playlist'leri de ekle (yeni oluşturulmuş
        # boş playlist'ler dahil).
        if root.exists():
            for entry in sorted(root.iterdir(), key=lambda p: p.name.lower()):
                if not entry.is_dir():
                    continue
                if entry.name not in groups:
                    groups[entry.name] = []

        # "Genel" her zaman listede olsun; kullanıcı tüm şarkılarını alt
        # klasörlere koymuş olsa bile buraya sürükle-bırak yapabilsin.
        groups.setdefault(self.DEFAULT_PLAYLIST_NAME, [])

        ordered: List[Tuple[str, list]] = []
        if self.DEFAULT_PLAYLIST_NAME in groups:
            ordered.append((self.DEFAULT_PLAYLIST_NAME, groups.pop(self.DEFAULT_PLAYLIST_NAME)))
        for name in sorted(groups.keys(), key=str.lower):
            ordered.append((name, groups[name]))
        self._playlist_cache = ordered
        return ordered

    def playlist_name_for(self, track_path: str) -> str:
        root = Path(self.folder).expanduser()
        try:
            rel_parts = Path(track_path).relative_to(root).parts
        except ValueError:
            rel_parts = (Path(track_path).name,)
        return rel_parts[0] if len(rel_parts) > 1 else self.DEFAULT_PLAYLIST_NAME

    def get_tracks_for_playlist(self, name: str) -> list:
        for pl_name, tracks in self.playlists():
            if pl_name == name:
                return list(tracks)
        return list(self.tracks)

    def __len__(self) -> int:
        return len(self.tracks)

    # -- Çalma listesi kapak resimleri -------------------------------------------
    # Kapaklar, ayrı bir veritabanı yerine DOĞRUDAN müzik klasörünün kendi
    # içinde (her çalma listesinin/alt klasörün kendi "cover.jpg" dosyası
    # olarak) saklanır. Böylece uygulama silinip yeniden kurulsa bile, ya da
    # klasör başka bir bilgisayara taşınsa bile kapaklar hep şarkılarla
    # birlikte kalır -- ayrı bir "uygulama verisi" senkronizasyonu gerekmez.
    def _folder_for_playlist(self, playlist_name: str) -> Path:
        root = Path(self.folder).expanduser()
        if playlist_name == self.DEFAULT_PLAYLIST_NAME:
            return root
        return root / playlist_name

    def cover_path(self, playlist_name: str) -> Optional[Path]:
        candidate = self._folder_for_playlist(playlist_name) / COVER_FILENAME
        return candidate if candidate.exists() else None

    def get_cover_data_uri(self, playlist_name: str) -> Optional[str]:
        path = self.cover_path(playlist_name)
        if not path:
            return None
        try:
            data = path.read_bytes()
            return "data:image/jpeg;base64," + base64.b64encode(data).decode("ascii")
        except OSError:
            logger.exception("Kapak resmi okunamadı: %s", path)
            return None

    def set_cover_from_file(self, playlist_name: str, source_path: str) -> Optional[str]:
        """Kullanıcının seçtiği bir resmi, bu çalma listesinin kapak resmi
        olarak (JPEG'e çevirip küçülterek) kaydeder. Başarılıysa yeni
        kapağın data URI'sini, başarısızsa None döner."""
        if not _HAS_PIL:
            logger.error("Pillow kurulu değil, kapak resmi kaydedilemiyor.")
            return None
        folder = self._folder_for_playlist(playlist_name)
        try:
            folder.mkdir(parents=True, exist_ok=True)
            dest = folder / COVER_FILENAME
            img = Image.open(source_path)
            img = img.convert("RGB")
            img.thumbnail((MAX_COVER_DIMENSION, MAX_COVER_DIMENSION))
            img.save(dest, "JPEG", quality=87)
        except Exception:
            logger.exception("Kapak resmi kaydedilemedi (kaynak: %s)", source_path)
            return None
        return self.get_cover_data_uri(playlist_name)

    PLAYLIST_META_FILENAME = "playlist.json"
    TRACK_META_FILENAME = "track_meta.json"

    def create_playlist(self, name: str) -> None:
        if name == self.DEFAULT_PLAYLIST_NAME:
            raise ValueError("Varsayılan çalma listesi oluşturulamaz")
        folder = self._folder_for_playlist(name)
        folder.mkdir(parents=True, exist_ok=True)
        self._invalidate_cache()

    def delete_playlist(self, name: str) -> None:
        """Playlist'in klasörünü tamamen siler. Default playlist (Genel)
        SİLİNEMEZ (zaten disk üzerinde ayrı bir klasörü yok, müzik kökünün
        kendisi). Başarılıysa cache invalidate edilir; rescan gerekir."""
        if name == self.DEFAULT_PLAYLIST_NAME:
            raise ValueError("Varsayılan çalma listesi silinemez")
        folder = self._folder_for_playlist(name)
        if not folder.exists():
            # Zaten yok; başarılı sayılır.
            self._invalidate_cache()
            return
        if not folder.is_dir():
            raise ValueError(f"Beklenmeyen yol türü: {folder}")
        # Müzik kökünün altında mı kontrolü (path traversal koruması)
        root = Path(self.folder).expanduser().resolve()
        target = folder.resolve()
        try:
            target.relative_to(root)
        except ValueError:
            raise ValueError(f"Güvenlik: playlist klasörü müzik kökünün dışında: {folder}")
        import shutil
        shutil.rmtree(folder)
        self._invalidate_cache()

    def remove_track(self, track_path: str) -> bool:
        """Tek bir şarkıyı diskten SİLER. Track playlist'ten (alt klasörden)
        veya Genel'den (kök dizin) olabilir. Başarıyla silindiyse True.

        Sadece gerçek ses dosyalarını siler; yanlışlıkla başka bir dosya
        yolunun silinmesini engellemek için uzantı kontrolü yapar. Eğer
        bu şarkı Genel (kök dizin) playlist'indeyse, dosya tamamen
        silinir; alt klasördeyse sadece dosya silinir (diğer şarkılar
        etkilenmez)."""
        path = Path(track_path).expanduser()
        if not path.exists() or not path.is_file():
            return False
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            # Güvenlik: desteklenmeyen uzantılı dosyaları silmeyi reddet.
            logger.warning("remove_track: desteklenmeyen uzantı, silinmedi: %s", path)
            return False
        try:
            path.unlink()
        except OSError:
            logger.exception("Şarkı silinemedi: %s", path)
            return False
        # meta dosyalarındaki bu track'e ait girdiyi de temizle (en iyi
        # çaba; meta'da orphan anahtar kalırsa zarar yok, sadece yer kaplar).
        self._cleanup_track_meta(track_path)
        self._invalidate_cache()
        return True

    def _cleanup_track_meta(self, track_path: str) -> None:
        """Track silindikten sonra ilgili playlist'in track_meta.json
        dosyasından da bu dosya adına ait girdiyi kaldırır (varsa)."""
        fname = Path(track_path).name
        # Hangi playlist'te olduğunu bul
        try:
            rel = Path(track_path).resolve().relative_to(Path(self.folder).expanduser().resolve())
        except ValueError:
            return
        if len(rel.parts) < 2:
            playlist_name = self.DEFAULT_PLAYLIST_NAME
        else:
            playlist_name = rel.parts[0]
        if playlist_name == self.DEFAULT_PLAYLIST_NAME:
            # Kök dizindeki track'lerin metası Genel için tutulmaz (mevcut
            # _entries_for mantığına göre; meta sadece alt klasörler için).
            return
        meta_path = self._folder_for_playlist(playlist_name) / self.TRACK_META_FILENAME
        if not meta_path.exists():
            return
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            return
        if fname in meta:
            del meta[fname]
            try:
                meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
            except OSError:
                logger.exception("track_meta.json güncellenemedi: %s", meta_path)

    def rename_playlist(self, old_name: str, new_name: str) -> None:
        if old_name == self.DEFAULT_PLAYLIST_NAME:
            raise ValueError("Varsayılan çalma listesi yeniden adlandırılamaz")
        if new_name == old_name:
            return
        if not new_name or new_name in (".", "..") or "/" in new_name or "\\" in new_name:
            raise ValueError(f"Geçersiz çalma listesi adı: {new_name!r}")
        old_folder = self._folder_for_playlist(old_name)
        new_folder = self._folder_for_playlist(new_name)
        old_folder.rename(new_folder)
        self._invalidate_cache()

    def playlist_meta(self, name: str) -> dict:
        now = time.time()
        cached = self._meta_cache.get(name)
        if cached and now - cached[0] < 10:
            return cached[1]
        folder = self._folder_for_playlist(name)
        meta_path = folder / self.PLAYLIST_META_FILENAME
        meta = {}
        if meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
            except Exception:
                pass
        self._meta_cache[name] = (now, meta)
        return meta

    def set_playlist_meta(self, name: str, **kwargs) -> None:
        folder = self._folder_for_playlist(name)
        meta = self.playlist_meta(name)
        meta.update(kwargs)
        meta_path = folder / self.PLAYLIST_META_FILENAME
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    def get_track_meta(self, name: str) -> dict:
        folder = self._folder_for_playlist(name)
        meta_path = folder / self.TRACK_META_FILENAME
        if meta_path.exists():
            try:
                return json.loads(meta_path.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}

    def set_track_meta(self, name: str, filename: str, title: str, artist: str) -> None:
        folder = self._folder_for_playlist(name)
        meta_path = folder / self.TRACK_META_FILENAME
        meta = {}
        if meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
            except Exception:
                pass
        meta[filename] = {"title": title, "artist": artist}
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
