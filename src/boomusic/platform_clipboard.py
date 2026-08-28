"""Platform-özel pano (clipboard) işlemleri.

GUI'da context menu 'Şarkı bağlantısını kopyala' gibi işlemler için
metni sistem panosuna kopyalamamız gerekiyor. webview'in JavaScript
tarafında navigator.clipboard.writeText() bazen çalışmaz (özellikle
webkit2gtk'da focus ve güvenlik kısıtlamaları); bu yüzden işi Python
tarafına alıyoruz.

Linux öncelik sırası:
  1. xclip          (X11, en yaygın)
  2. xsel           (X11, alternatif)
  3. wl-copy        (Wayland)
  4. pbcopy         (mac benzeri, bazen Linux'ta da var)
  5. pyperclip      (pip; tercih etmiyoruz ama fallback)
  6. GTK 3          (son çare: pip python paketi 'gi' zaten kurulu)
"""
from __future__ import annotations

import logging
import shutil
import subprocess

logger = logging.getLogger("boomusic.clipboard")


def copy_text(text: str) -> bool:
    """Metni sistem panosuna kopyalar. Başarılıysa True.

    Sıralı olarak şu araçları dener; hangisi varsa onu kullanır:
    xclip → xsel → wl-copy → pbcopy → pyperclip → GTK 3.
    Hiçbiri yoksa False döner (GUI tarafı kullanıcıya 'kopyalanamadı'
    mesajı gösterir).
    """
    if not text:
        return False
    # 1-4. Harici komutlar
    for cmd in (["xclip", "-selection", "clipboard"],
                ["xsel", "--clipboard", "--input"],
                ["wl-copy"],
                ["pbcopy"]):
        if shutil.which(cmd[0]):
            try:
                p = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                p.communicate(text.encode("utf-8"), timeout=2)
                if p.returncode == 0:
                    return True
            except Exception:
                logger.exception("Pano aracı başarısız: %s", cmd[0])
                continue
    # 5. pyperclip (pip paketi; her yerde kurulu olmayabilir)
    try:
        import pyperclip
        pyperclip.copy(text)
        return True
    except Exception:
        pass
    # 6. GTK 3 (son çare)
    try:
        import gi
        gi.require_version("Gtk", "3.0")
        from gi.repository import Gtk, Gdk
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        clipboard.set_text(text, -1)
        clipboard.store()
        return True
    except Exception:
        logger.exception("GTK clipboard da başarısız")
    return False
