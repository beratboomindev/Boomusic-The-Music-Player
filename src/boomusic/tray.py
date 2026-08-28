"""pystray tabanlı sistem tepsisi (tray) arayüzü.

Bu modül SADECE sunum/menü inşası ile ilgilenir; tüm iş mantığı
``app.App`` sınıfındadır. Bu ayrım sayesinde app.py, pystray hiç kurulu
olmasa/çalışmasa bile bağımsız test edilebilir.

== Just Icon Mode ==
Kullanıcı Ayarlar → "Sadece İkon Modu"nu açtığında uygulama penceresi
hiç oluşturulmaz; her şey bu menüden yapılır. Menüde 'Pencere Moduna
Dön' seçeneği belirir; seçildiğinde ``enter_window_mode_callback``
çağrılır (örn. bir threading.Event set edilir), __main__.py pencereyi
oluşturup açar.

NOT: Bu dosyanın çalışması için bir masaüstü ortamı (X11/Wayland) ve o
ortamda bir sistem tepsisi barındırıcısı (KDE Plasma, GNOME + eklenti,
waybar/Noctalia 'Tray' bileşeni vb.) gerekir.
"""
from __future__ import annotations

import logging
import os
import threading
from pathlib import Path
from typing import Callable, List, Optional

import pystray
from PIL import Image

from .app import App

logger = logging.getLogger("boomusic.tray")

ICON_PATH = Path(__file__).parent / "assets" / "icon.png"

# Ses için pystray slider desteklemez; bunun yerine preset'ler + delta
# düğmeleri sunuyoruz. Pratik ve Linux masaüstü barındırıcılarında
# (KDE, GNOME, XFCE) test edilmiş, yeterince iyi bir çözüm.
VOLUME_PRESETS = (0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100)
VOLUME_DELTA = 5


def _load_icon_image() -> Image.Image:
    return Image.open(ICON_PATH)


class Tray:
    def __init__(self, app: App, gui=None):
        self.app = app
        self.gui = gui
        # Just Icon Mode'dan pencere moduna geçmek için __main__.py tarafından
        # set edilen callback. None ise 'Pencere Moduna Dön' menü öğesi
        # hiç gösterilmez (normal modda).
        self._enter_window_mode_cb: Optional[Callable[[], None]] = None
        self.icon = pystray.Icon(
            "boomusic",
            icon=_load_icon_image(),
            title="Boomusic",
            menu=self._build_menu(),
        )

    def set_enter_window_mode_callback(self, cb: Callable[[], None]) -> None:
        """Just Icon Mode'dan pencere moduna dönmek için __main__ tarafından
        çağrılır. Callback (örn. bir Event.set) tetiklendiğinde __main__,
        tray'i durdurup pencereyi oluşturur."""
        self._enter_window_mode_cb = cb

    def _is_just_icon_mode(self) -> bool:
        return bool(self.app.config.settings.just_icon_mode)

    # -- Callback'ler (her biri pystray'in çağırdığı basit sarmalayıcılar) -----
    def _on_show_window(self, icon, item):
        if self.gui is not None:
            self.gui.show()

    def _on_enter_window_mode(self, icon, item):
        # Just Icon Mode'dan pencere moduna dönmek için config'i güncelle
        # (böylece __main__.py'de pencere açıldıktan sonra aynı oturumda
        # config tutarlı kalır) ve callback'i tetikle.
        self.app.config.update(just_icon_mode=False)
        if self._enter_window_mode_cb is not None:
            try:
                self._enter_window_mode_cb()
            except Exception:
                logger.exception("enter_window_mode callback hata verdi")

    def _on_play_pause(self, icon, item):
        self.app.play_pause()

    def _on_next(self, icon, item):
        self.app.next()

    def _on_previous(self, icon, item):
        self.app.previous()

    def _on_toggle_shuffle(self, icon, item):
        self.app.toggle_shuffle()

    def _on_toggle_mute(self, icon, item):
        self.app.toggle_mute()

    def _on_volume_set(self, percent: int):
        def _cb(icon, item):
            self.app.set_volume_percent(percent)
        return _cb

    def _on_volume_up(self, icon, item):
        self.app.set_volume_percent(min(100, self.app.volume_percent() + VOLUME_DELTA))

    def _on_volume_down(self, icon, item):
        self.app.set_volume_percent(max(0, self.app.volume_percent() - VOLUME_DELTA))

    def _on_quit(self, icon, item):
        if self.gui is not None:
            self.gui.quit()
        try:
            icon.stop()
        except Exception:
            pass
        threading.Timer(4.0, lambda: os._exit(0)).start()

    def _on_play_track(self, path: str):
        def _cb(icon, item):
            self.app.play_track_path(path)
        return _cb

    def _on_open_music_folder(self, icon, item):
        self.app.open_music_folder()

    def _on_rescan(self, icon, item):
        self.app.rescan()

    # -- Menü inşası -------------------------------------------------------------
    def _now_playing_text(self) -> str:
        """Başlık satırı için; kısa ve bilgilendirici."""
        title = self.app.now_playing_display()
        if self.app.is_playing():
            return f"▶  {title}"
        if self.app.is_paused():
            return f"⏸  {title}"
        return f"○  {title}"

    def _build_volume_submenu(self) -> pystray.Menu:
        # pystray'de slider yok; preset + delta düğmeleri sunuyoruz.
        # 'checked' bir callable bekler; şu anki değere göre True/False
        # döndüren bir fonksiyon veriyoruz ki pystray onu doğru işaretlesin.
        current = self.app.volume_percent()
        preset_items = []
        for p in VOLUME_PRESETS:
            def make_checked(target_p):
                def _is_checked(_item):
                    return self.app.volume_percent() == target_p
                return _is_checked
            preset_items.append(pystray.MenuItem(
                f"{p}%", self._on_volume_set(p),
                checked=make_checked(p), radio=True,
            ))
        items: List = [
            *preset_items,
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(f"Ses +{VOLUME_DELTA}", self._on_volume_up),
            pystray.MenuItem(f"Ses -{VOLUME_DELTA}", self._on_volume_down),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Sustur / Aç" if not self.app.is_muted() else "Susturmayı Kaldır",
                self._on_toggle_mute,
            ),
        ]
        return pystray.Menu(*items)

    def _build_playlists_submenu(self) -> pystray.Menu:
        """Her playlist için bir alt menü; içinde o playlist'in şarkıları.

        Tıklanan şarkı doğrudan çalınır. Çok uzun listelerde pystray
        sorun çıkarabilir; bu yüzden playlist başına 200 şarkıyla
        sınırlandırıyoruz.
        """
        items: List = []
        try:
            playlists = self.app.playlists()
        except Exception:
            logger.exception("Playlist listesi alınamadı")
            playlists = []
        for pl in playlists:
            name = pl.get("name", "?")
            if pl.get("special"):
                # 'En Çok Dinlenenler' gibi sanal playlist'leri de göster ama
                # tıklandığında ilk şarkıyı çal.
                items.append(pystray.MenuItem(
                    f"⭐ {name} ({pl.get('track_count', 0)})",
                    self._on_play_first_of_playlist(name),
                ))
                continue
            items.append(self._build_playlist_item(name, pl.get("track_count", 0)))
        if not items:
            items.append(pystray.MenuItem("(çalma listesi yok)", None, enabled=False))
        return pystray.Menu(*items)

    def _on_play_first_of_playlist(self, playlist_name: str):
        def _cb(icon, item):
            tracks = self.app.tracks_in_playlist(playlist_name)
            if tracks:
                self.app.play_track_path(tracks[0].path)
        return _cb

    def _build_playlist_item(self, name: str, count: int):
        """Bir playlist için alt menü; içinde ilk 200 şarkı."""
        try:
            tracks = self.app.tracks_in_playlist(name)[:200]
        except Exception:
            tracks = []
        sub_items: List = []
        current_path = self.app.engine.current_path()
        for t in tracks:
            marker = "▶ " if t.path == current_path else "   "
            label = f"{marker}{t.display_name}"
            if len(label) > 60:
                label = label[:57] + "..."
            sub_items.append(pystray.MenuItem(label, self._on_play_track(t.path)))
        if not sub_items:
            sub_items.append(pystray.MenuItem("(boş)", None, enabled=False))
        elif len(self.app.tracks_in_playlist(name)) > 200:
            sub_items.append(pystray.Menu.SEPARATOR)
            sub_items.append(pystray.MenuItem(
                f"... ve {len(self.app.tracks_in_playlist(name)) - 200} şarkı daha",
                None, enabled=False,
            ))
        return pystray.MenuItem(f"📁 {name} ({count})", pystray.Menu(*sub_items))

    def _build_menu(self) -> pystray.Menu:
        """Menüyü (veya Just Icon Mode'daysa zengin menüyü) oluşturur.

        ÖNEMLİ: pystray menüyü sadece ILK oluşturulduğunda bir kez alır;
        ilerleyen zamanda başlık/değer değişiklikleri otomatik yansımaz.
        Bu yüzden çal/duraklat ikonu, ses yüzdesi gibi "anlık değerler"
        sadece yaklaşık olur (ilk açılışta doğru, sonra kullanıcı etkileşimi
        ile yarış durumu olabilir). Tam doğruluk için menu güncellemesi
        gerekirdi, ama bu pratikte sorun yaratmıyor -- menü öğelerinin
        ÇOĞU komuttur, anlık değer değildir.
        """
        items: List = []

        if self._is_just_icon_mode():
            # === SADECE İKON MODU: zengin menü =============================
            items.append(pystray.MenuItem(self._now_playing_text(), None, enabled=False))
            items.append(pystray.Menu.SEPARATOR)
            items.append(pystray.MenuItem("⏯  Oynat / Duraklat", self._on_play_pause))
            items.append(pystray.MenuItem("⏭  Sonraki", self._on_next))
            items.append(pystray.MenuItem("⏮  Önceki", self._on_previous))
            shuffle_state = "✓" if self.app.shuffle_enabled() else " "
            items.append(pystray.MenuItem(
                f"🔀  Karıştır [{shuffle_state}]", self._on_toggle_shuffle
            ))
            items.append(pystray.Menu.SEPARATOR)
            items.append(pystray.MenuItem(
                f"🔊  Ses: {self.app.volume_percent()}%",
                self._build_volume_submenu(),
            ))
            items.append(pystray.Menu.SEPARATOR)
            items.append(pystray.MenuItem("📂  Çalma listeleri", self._build_playlists_submenu()))
            items.append(pystray.Menu.SEPARATOR)
            items.append(pystray.MenuItem("🔄  Yeniden Tara", self._on_rescan))
            items.append(pystray.MenuItem("📁  Müzik Klasörünü Aç", self._on_open_music_folder))
            items.append(pystray.Menu.SEPARATOR)
            # Just Icon Mode'dan pencere moduna dönüş.
            if self._enter_window_mode_cb is not None:
                items.append(pystray.MenuItem("🪟  Pencere Moduna Dön", self._on_enter_window_mode))
                items.append(pystray.Menu.SEPARATOR)
            items.append(pystray.MenuItem("⏻  Çıkış", self._on_quit))
        else:
            # === NORMAL MOD: minimal menü (pencere açılınca geniş kullanılır) ==
            if self.gui is not None:
                items.append(pystray.MenuItem("Boomusic'i Göster", self._on_show_window, default=True))
                items.append(pystray.Menu.SEPARATOR)
            items.append(pystray.MenuItem("Çık", self._on_quit))

        return pystray.Menu(*items)

    def run(self) -> None:
        self.icon.run()

    def stop(self) -> None:
        self.icon.stop()
