"""pystray tabanlı sistem tepsisi (tray) arayüzü.

Bu modül SADECE sunum/menü inşası ile ilgilenir; tüm iş mantığı
``app.App`` sınıfındadır (bu dosyada iş mantığı YOKTUR, sadece pystray'e
bağlama/etiketleme var). Bu ayrım sayesinde app.py, pystray hiç kurulu
olmasa/çalışmasa bile bağımsız test edilebilir.

NOT: Bu dosyanın çalışması için bir masaüstü ortamı (X11/Wayland) ve o
ortamda bir sistem tepsisi barındırıcısı (KDE Plasma, GNOME + eklenti,
waybar/Noctalia 'Tray' bileşeni vb.) gerekir. Görüntü sunucusu olmayan
bir ortamda (örn. sunucu/CI) sadece import edilebilir, çalıştırılamaz.
"""
from __future__ import annotations

import logging
import os
import threading
from pathlib import Path

import pystray
from PIL import Image

from .app import App

logger = logging.getLogger("boomusic.tray")

ICON_PATH = Path(__file__).parent / "assets" / "icon.png"


def _load_icon_image() -> Image.Image:
    return Image.open(ICON_PATH)


class Tray:
    def __init__(self, app: App, gui=None):
        self.app = app
        self.gui = gui
        self.icon = pystray.Icon(
            "boomusic",
            icon=_load_icon_image(),
            title="Boomusic",
            menu=self._build_menu(),
        )

    def _on_show_window(self, icon, item):
        if self.gui is not None:
            self.gui.show()

    def _on_quit(self, icon, item):
        if self.gui is not None:
            self.gui.quit()
        try:
            icon.stop()
        except Exception:
            pass
        threading.Timer(4.0, lambda: os._exit(0)).start()

    def _build_menu(self) -> pystray.Menu:
        items = []
        if self.gui is not None:
            items.append(pystray.MenuItem("Boomusic'i Göster", self._on_show_window, default=True))
            items.append(pystray.Menu.SEPARATOR)
        items.append(pystray.MenuItem("Çık", self._on_quit))
        return pystray.Menu(*items)

    def run(self) -> None:
        self.icon.run()

    def stop(self) -> None:
        self.icon.stop()
