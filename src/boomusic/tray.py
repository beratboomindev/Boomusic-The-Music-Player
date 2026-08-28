"""pystray tabanlı sistem tepsisi (tray) arayüzü.

Bu modül SADECE sunum/menü inşası ile ilgilenir; tüm iş mantığı
``app.App`` sınıfındadır. Bu ayrım sayesinde app.py, pystray hiç kurulu
olmasa/çalışmasa bile bağımsız test edilebilir.

== İki başlatma modu ==
Uygulama iki şekilde başlatılabilir; her birinin tray menüsü farklıdır:
1) ``boomusic``          → GUI pencere + SADE tray menüsü ("Göster"+"Çık").
                           Kullanıcı her şeyi pencereden kontrol eder; tray
                           sadece "görünür olsun ve kapatılabilsin" işi yapar.
2) ``boomusic-tray``     → sadece tray simgesi, ZENGİN menü (oynat/duraklat,
                           ses, playlist'ler, vs.). Pencere hiç açılmaz; menü
                           TÜM kontrol arayüzüdür (CLI: ``--tray-only``).

İki mod AYNI anda çalışabilir (farklı lock dosyaları). Her birinin kendi
tray simgesi olur; bu kasıtlıdır — kullanıcı bilinçli olarak ikisini de
başlatmış demektir. Sadece birini kullanmak istiyorsanız diğerini
başlatmayın.

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
    def __init__(self, app: App, gui=None, rich_menu: bool = False):
        """Tepsi simgesi ve menüsünü oluşturur.

        rich_menu=False (varsayılan, GUI modu):
            SADE menü: sadece 'Boomusic'i Göster' (gui varsa) + 'Çıkış'.
            Mantık: GUI açıkken kullanıcı her şeyi pencereden kontrol eder;
            tray menüsünü zengin tutmak tekrardır (pencere zaten orada).

        rich_menu=True (Just Icon modu, --tray-only):
            ZENGİN menü: oynat/duraklat, ses, playlist'ler, karıştır,
            yeniden tara, vs. Pencere yok; menü TÜM kontrol arayüzüdür.
        """
        self.app = app
        self.gui = gui
        self._rich_menu = rich_menu
        # Normal modda "Boomusic'i Göster" menü öğesi bu callback'i çağırır.
        # Just Icon Mode'da (gui=None) bu callback tanımsız kalır ve menüde
        # "Göster" öğesi gösterilmez.
        self._show_window_cb: Optional[Callable[[], None]] = None
        self.icon = pystray.Icon(
            "boomusic",
            icon=_load_icon_image(),
            title="Boomusic",
            menu=self._build_menu(),
        )

    def set_show_window_callback(self, cb: Callable[[], None]) -> None:
        """GUI modunda pencereyi göstermek için __main__.py tarafından atanır."""
        self._show_window_cb = cb

    # -- Callback'ler (pystray'in çağırdığı basit sarmalayıcılar) ---------------
    def _on_show_window(self, icon, item):
        if self._show_window_cb is not None:
            try:
                self._show_window_cb()
            except Exception:
                logger.exception("show_window callback hata verdi")
        elif self.gui is not None:
            # set_show_window_callback çağrılmadıysa fallback olarak gui.show() dene.
            try:
                self.gui.show()
            except Exception:
                logger.exception("gui.show() başarısız")
        else:
            # Just Icon modunda pencere YOK -- bu menü öğesi tıklandığında
            # yeni bir GUI örneği başlat (kullanıcı pencereye geri dönmek
            # istiyor). Mevcut Just Icon süreci çalışmaya devam eder; yeni
            # GUI ayrı bir lock dosyası kullandığı için çakışma olmaz.
            # (İsterse kullanıcı daha sonra Just Icon simgesinden 'Çıkış'
            # seçebilir.)
            import subprocess
            launcher = os.path.expanduser("~/.local/bin/boomusic")
            if os.path.isfile(launcher):
                try:
                    subprocess.Popen(
                        [launcher],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        stdin=subprocess.DEVNULL,
                        start_new_session=True,
                    )
                except Exception:
                    logger.exception("boomusic (GUI) başlatılamadı")
            else:
                logger.error("GUI launcher bulunamadı: %s", launcher)

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
        # 1 saniye içinde süreç kapanmazsa SIGKILL ile zorla öldür. Normalde
        # webview.start() veya tray.run() döndüğünde süreç zaten kapanmış
        # olur; bu timer sadece 'sıkıştı' senaryosu için garanti.
        import signal as _sig
        def _kill():
            try:
                os.kill(os.getpid(), _sig.SIGKILL)
            except Exception:
                os._exit(0)
        threading.Timer(1.0, _kill).start()

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
        title = self.app.now_playing_display()
        if self.app.is_playing():
            return f"▶  {title}"
        if self.app.is_paused():
            return f"⏸  {title}"
        return f"○  {title}"

    def _build_volume_submenu(self) -> pystray.Menu:
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
        items: List = []
        try:
            playlists = self.app.playlists()
        except Exception:
            logger.exception("Playlist listesi alınamadı")
            playlists = []
        for pl in playlists:
            name = pl.get("name", "?")
            count = pl.get("track_count", 0)
            if pl.get("special"):
                # Sanal playlist'ler (En Çok Dinlenenler gibi): ilk şarkıyı çal.
                items.append(pystray.MenuItem(
                    f"⭐ {name} ({count})",
                    self._on_play_first_of_playlist(name),
                ))
                continue
            items.append(self._build_playlist_item(name, count))
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
        try:
            tracks = self.app.tracks_in_playlist(name)
        except Exception:
            tracks = []
        sub_items: List = []
        current_path = self.app.engine.current_path()
        # Çok uzun listelerde pystray sorun çıkarabilir; 200 şarkı sınırı.
        for t in tracks[:200]:
            marker = "▶ " if t.path == current_path else "   "
            label = f"{marker}{t.display_name}"
            if len(label) > 60:
                label = label[:57] + "..."
            sub_items.append(pystray.MenuItem(label, self._on_play_track(t.path)))
        if not sub_items:
            sub_items.append(pystray.MenuItem("(boş)", None, enabled=False))
        elif len(tracks) > 200:
            sub_items.append(pystray.Menu.SEPARATOR)
            sub_items.append(pystray.MenuItem(
                f"... ve {len(tracks) - 200} şarkı daha", None, enabled=False,
            ))
        return pystray.MenuItem(f"📁 {name} ({count})", pystray.Menu(*sub_items))

    def _build_menu(self) -> pystray.Menu:
        """Menü moduna göre iki farklı şekilde oluşturulur.

        rich_menu=False (GUI modu, varsayılan): SADE menü — sadece
            (GUI varsa) 'Boomusic'i Göster' + 'Çıkış'. Mantık: GUI açıkken
            kullanıcı her şeyi pencereden kontrol eder; tray menüsünü
            zengin tutmak tekrardır.

        rich_menu=True (Just Icon modu): ZENGİN menü — oynat/duraklat,
            ses, playlist'ler, karıştır, yeniden tara, vs. Pencere yok;
            menü TÜM kontrol arayüzüdür. (GUI aynı anda çalışıyorsa
            'Boomusic'i Göster' öğesi de burada görünür.)
        """
        items: List = []
        if not self._rich_menu:
            # === SADE MENÜ (GUI modu) ===
            if self._show_window_cb is not None or self.gui is not None:
                items.append(pystray.MenuItem(
                    "Boomusic'i Göster", self._on_show_window, default=True
                ))
            items.append(pystray.MenuItem("Çıkış", self._on_quit))
            return pystray.Menu(*items)

        # === ZENGİN MENÜ (Just Icon modu) ===
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
        # Just Icon modunda HER ZAMAN 'Göster' öğesi göster: tıklandığında
        # yeni bir GUI örneği subprocess olarak başlatılır (mevcut Just Icon
        # süreci çalışmaya devam eder; farklı lock dosyaları sayesinde
        # çakışma olmaz). GUI modunda gösteriyorsa sadece mevcut pencereyi
        # öne getirir; o davranış zaten _on_show_window içinde.
        items.append(pystray.Menu.SEPARATOR)
        items.append(pystray.MenuItem("🪟  Boomusic'i Göster", self._on_show_window, default=True))
        items.append(pystray.Menu.SEPARATOR)
        items.append(pystray.MenuItem("⏻  Çıkış", self._on_quit))
        return pystray.Menu(*items)

    def run(self) -> None:
        self.icon.run()

    def stop(self) -> None:
        self.icon.stop()
