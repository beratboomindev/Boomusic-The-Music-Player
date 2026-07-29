"""Masaüstü bildirimleri (notify-send üzerinden).

`notify-send`, çoğu Linux masaüstü ortamında (GNOME, KDE, XFCE, vb.)
libnotify ile birlikte gelir. Kurulu değilse ya da bir bildirim sunucusu
çalışmıyorsa, burada sessizce (uygulamayı çökertmeden) günlüğe (log) not
düşülür -- bildirim, uygulamanın çalışması için gerekli değildir.
"""
from __future__ import annotations

import logging
import shutil
import subprocess

logger = logging.getLogger("boomusic.notifier")

_notify_send_path = shutil.which("notify-send")


def notify(title: str, message: str = "", app_name: str = "Boomusic") -> None:
    if not _notify_send_path:
        logger.debug("notify-send bulunamadı, bildirim atlanıyor: %s - %s", title, message)
        return
    try:
        subprocess.run(
            [_notify_send_path, "-a", app_name, title, message],
            check=False,
            timeout=5,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        logger.exception("Bildirim gönderilemedi")


def open_path(path: str) -> bool:
    """Bir klasörü/dosyayı sistemin varsayılan dosya yöneticisinde açar."""
    xdg_open = shutil.which("xdg-open")
    if not xdg_open:
        logger.debug("xdg-open bulunamadı, klasör açılamıyor: %s", path)
        return False
    try:
        subprocess.Popen(
            [xdg_open, path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        return True
    except Exception:
        logger.exception("Klasör açılamadı: %s", path)
        return False
