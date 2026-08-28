"""Boomusic giriş noktası.

Çalıştırma:
    python3 -m boomusic

Bu dosya günlükleme (logging), tek-örnek (single instance) kilidi, sinyal
yönetimi ve App + Tray + GUI penceresini birbirine bağlamaktan sorumludur.
İş mantığının tamamı ``app.py``'dedir; bu dosya sadece programı ayağa
kaldırır ve HER AŞAMAYI ayrıntılı günlükler (böylece bir şey takılırsa/
çökerse ``boomusic.log`` dosyasında TAM OLARAK nerede olduğu görülür).

== Mimari: neden tray'i pywebview ile AYNI (paylaşılan) döngüde çalıştırıyoruz ==
pystray'in Linux'taki AppIndicator arka ucu VE pywebview'in Linux'taki GTK
arka ucu, İKİSİ DE GTK/GLib tabanlıdır. Aynı süreç içinde, biri bir arka
plan thread'inde diğeri ana thread'de olmak üzere İKİ AYRI GTK ana döngüsü
(mainloop) çalıştırmak GTK'nın thread modeliyle güvenli değildir ve
kilitlenmeye (sessizce takılıp kalmaya) yol açabilir -- yaşanan "uygulama
açılmıyor, hata da yok" belirtisi tam olarak buna işaret ediyordu.

Çözüm: GUI kullanılabiliyorsa, tepsi simgesi KENDİ mainloop'unu BAŞLATMAZ
(``icon.run()`` değil); bunun yerine ``icon.run_detached()`` ile sadece
KAYDEDİLİR, ve gerçek/tek ortak GTK döngüsünü ``webview.start()``
(``gui.start()``) başlatır -- bu döngü hem pencerenin hem de tepsi
simgesinin olaylarını birlikte işler. GUI hiç kullanılamıyorsa (örn.
webkit2gtk kurulu değilse), tepsi eskisi gibi kendi (tek başına, güvenli)
arka plan thread'inde ``icon.run()`` ile çalışır.
"""
from __future__ import annotations

import fcntl
import logging
import logging.handlers
import os
import signal
import sys
import threading
from pathlib import Path
from typing import Optional

from . import notifier
from .app import App
from .config import default_data_dir

LOCK_FILE_NAME = "boomusic.lock"
LOG_FILE_NAME = "boomusic.log"


def _setup_logging(data_dir: Path) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    log_file = data_dir / LOG_FILE_NAME
    handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=1_000_000, backupCount=2, encoding="utf-8"
    )
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    handler.setFormatter(formatter)

    root = logging.getLogger("boomusic")
    root.setLevel(logging.INFO)
    root.addHandler(handler)

    if sys.stderr is not None and sys.stderr.isatty():
        console = logging.StreamHandler()
        console.setFormatter(formatter)
        root.addHandler(console)


def _acquire_single_instance_lock(data_dir: Path):
    data_dir.mkdir(parents=True, exist_ok=True)
    lock_path = data_dir / LOCK_FILE_NAME
    lock_file = open(lock_path, "w")
    try:
        fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        lock_file.close()
        return None
    lock_file.write(str(os.getpid()))
    lock_file.flush()
    return lock_file


def _start_tray_thread(tray, tray_crashed: threading.Event, logger: logging.Logger) -> threading.Thread:
    """Tray'i KENDİ (tek başına) arka plan thread'inde, klasik pystray
    kalıbıyla çalıştırır. Sadece GUI hiç yoksa/kullanılamıyorsa kullanılır
    (bkz. modül docstring'i -- GUI varken bunun yerine run_detached() kullanılır)."""

    def _run_tray() -> None:
        logger.info("[tray] icon.run() (kendi thread'inde) çağrılıyor...")
        try:
            tray.run()
            logger.info("[tray] icon.run() normal şekilde döndü (durduruldu).")
        except Exception:
            logger.exception("[tray] icon.run() thread'inde beklenmeyen hata oluştu.")
            tray_crashed.set()

    t = threading.Thread(target=_run_tray, name="boomusic-tray", daemon=False)
    t.start()
    return t


def main() -> int:
    # PulseAudio / PipeWire'da bu uygulamanın ses akışının "Boomusic"
    # olarak görünmesini sağlar (VLC ve pywebview/python3 yerine).
    os.environ.setdefault("PULSE_PROP_application.name", "Boomusic")
    os.environ.setdefault("PULSE_PROP_application.icon_name", "boomusic")

    data_dir = default_data_dir()
    _setup_logging(data_dir)
    logger = logging.getLogger("boomusic.main")
    logger.info("=== Boomusic başlangıç dizisi başladı (pid=%s) ===", os.getpid())

    lock_file = _acquire_single_instance_lock(data_dir)
    if lock_file is None:
        logger.warning("Boomusic zaten çalışıyor; yeni örnek başlatılmadı.")
        notifier.notify("Boomusic", "Boomusic zaten çalışıyor (tepsiye bakın).")
        return 0
    logger.info("[1/5] Tek-örnek kilidi alındı.")

    try:
        app: Optional[App] = App()
        logger.info("[2/5] App() oluşturuldu (%d şarkı, ses hazır: %s).", app.track_count(), app.engine.audio_ready)
    except Exception:
        logger.exception("[2/5] App() oluşturulurken hata oluştu -- uygulama başlatılamıyor.")
        lock_file.close()
        return 1

    # Just Icon Mode: config'de True ise uygulama PENCERESİZ başlar; tüm
    # kontrol tepsi simgesindeki menüden yapılır. Ana thread bir Event'te
    # bloklanır; kullanıcı 'Pencere Moduna Dön' seçince Event set edilir,
    # tray durdurulur, ana thread uyanır, pencere oluşturulup gösterilir.
    just_icon_mode = bool(app.config.settings.just_icon_mode)
    if just_icon_mode:
        logger.info("[2.5/5] just_icon_mode=AKTİF: pencere oluşturulmayacak.")

    # -- GUI penceresi nesnesini oluştur (henüz BAŞLATMIYORUZ) -----------------------
    gui = None
    if not just_icon_mode:
        try:
            from .gui import GuiWindow

            gui = GuiWindow(app)
            logger.info("[3/5] GuiWindow() oluşturuldu (pencere HENÜZ görünmüyor, bu normal).")
        except Exception:
            logger.exception(
                "[3/5] GuiWindow() oluşturulamadı (webkit2gtk-4.1/GTK kurulu değil olabilir). "
                "Uygulama sadece tepsi simgesiyle devam edecek."
            )
    else:
        logger.info("[3/5] just_icon_mode açık; GuiWindow atlanıyor.")

    # -- Tray nesnesini oluştur (henüz BAŞLATMIYORUZ) --------------------------------
    tray = None
    try:
        from .tray import Tray

        tray = Tray(app, gui=gui)
        logger.info("[4/5] Tray() oluşturuldu (simge HENÜZ görünmüyor, bu normal).")
    except Exception:
        logger.exception(
            "[4/5] Tray() oluşturulamadı. Masaüstü ortamınızda AppIndicator/"
            "StatusNotifierItem desteği olduğundan emin olun (bkz. README.md)."
        )

    if tray is None and gui is None:
        logger.error("Ne tray ne de GUI oluşturulabildi; çıkılıyor.")
        app.shutdown()
        lock_file.close()
        return 1

    tray_crashed = threading.Event()
    tray_thread: Optional[threading.Thread] = None
    tray_detached = False
    # just_icon_mode'dan pencere moduna geçmek için ana thread bu event'i bekler.
    enter_window_mode_event = threading.Event()
    if tray is not None and not just_icon_mode:
        tray.set_enter_window_mode_callback(enter_window_mode_event.set)

    if tray is not None and gui is not None:
        # GUI VE tray birlikte: GTK mainloop çakışmasını önlemek için tray'i
        # KENDİ loop'unu başlatmadan sadece kaydediyoruz (bkz. modül docstring'i).
        try:
            logger.info("[5/5] Tray, run_detached() ile paylaşılan GTK döngüsüne kaydediliyor...")
            tray.icon.run_detached()
            tray_detached = True
            logger.info("[5/5] Tray başarıyla kaydedildi (run_detached).")
        except Exception:
            logger.exception(
                "[5/5] run_detached() başarısız oldu; tray klasik (kendi thread'i) "
                "moduna düşüyor. Bu, GUI ile aynı anda küçük bir çakışma riski taşır."
            )
            tray_thread = _start_tray_thread(tray, tray_crashed, logger)
    elif tray is not None:
        # GUI yok: tray'in kendi başına, kendi thread'inde çalışması güvenlidir.
        # Bu dal hem just_icon_mode=True durumunu, hem de webkit kurulu değilken
        # otomatik düşülen durumu kapsar.
        tray_thread = _start_tray_thread(tray, tray_crashed, logger)

    def _handle_signal(signum, _frame):
        logger.info("Sinyal alındı (%s), kapatılıyor...", signum)
        if tray is not None:
            try:
                tray.stop()
            except Exception:
                logger.exception("tray.stop() sırasında hata")
        if gui is not None:
            try:
                gui.quit()
            except Exception:
                logger.exception("gui.quit() sırasında hata")
        # Just Icon Mode'daysa Event'i de set et ki ana thread uyansın ve çıkış yapsın.
        enter_window_mode_event.set()
        # Güvenlik ağı: normal kapanış birkaç saniyede tamamlanmazsa
        # (beklenmeyen bir GTK/pywebview tuhaflığı vb.) süreci KOŞULSUZ
        # sonlandır -- kullanıcı asla elle 'kill' yapmak zorunda kalmamalı.
        threading.Timer(4.0, lambda: os._exit(0)).start()

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    logger.info(
        "Boomusic başlatıldı (%d şarkı bulundu, ses hazır: %s, tray: %s, gui: %s, "
        "tray_modu: %s, just_icon_mode: %s).",
        app.track_count(), app.engine.audio_ready, tray is not None, gui is not None,
        "paylaşılan-döngü (run_detached)" if tray_detached else ("kendi-thread'i" if tray_thread else "yok"),
        just_icon_mode,
    )

    exit_code = 0
    gui_start_failed = False
    try:
        if just_icon_mode and gui is None and tray is not None:
            # --- SADECE İKON MODU: ana thread pencere açılmasını bekler ---
            # Kullanıcı tray'de 'Pencere Moduna Dön' seçtiğinde tray callback'i
            # bu event'i set eder; aşağıda uyanıp pencereyi oluştururuz. Çıkış
            # (tray menüsündeki 'Çık' veya SIGTERM) yine event'i set eder;
            # o zaman pencere moduna geçmeden uygulama kapanır.
            logger.info("Just Icon Mode: ana thread pencere moduna geçiş bekliyor...")
            entered = enter_window_mode_event.wait()
            if not entered:
                logger.info("Event iptal edildi, çıkılıyor.")
            else:
                if app.config.settings.just_icon_mode:
                    # Event, çıkış için de set edilmiş olabilir (signal handler);
                    # eğer hâlâ just_icon_mode=True ise kullanıcı ÇIKIŞ yolunu seçti.
                    logger.info("Event set edildi ama just_icon_mode hâlâ açık -- çıkış yolu.")
                else:
                    # Kullanıcı pencere moduna dönmeyi seçti. Önce tray'i
                    # durdur (run_detached olmadığı için stop() güvenli), sonra
                    # pencere oluştur ve başlat.
                    logger.info("Pencere moduna geçiliyor -- tray durduruluyor...")
                    try:
                        tray.stop()
                    except Exception:
                        logger.exception("tray.stop() sırasında hata")
                    if tray_thread is not None:
                        tray_thread.join(timeout=3)
                    try:
                        from .gui import GuiWindow
                        gui = GuiWindow(app)
                        logger.info("GuiWindow() oluşturuldu (just_icon_mode'dan dönüş).")
                    except Exception:
                        logger.exception(
                            "Pencere moduna dönüş başarısız: GuiWindow oluşturulamadı. "
                            "Uygulama kapanıyor."
                        )
                        exit_code = 1
                    if gui is not None:
                        try:
                            logger.info("GUI mainloop'u başlatılıyor...")
                            gui.start()
                            logger.info("GUI mainloop'u normal şekilde sona erdi.")
                        except Exception:
                            logger.exception("GUI başlatılamadı (just_icon_mode'dan dönüş).")
                            exit_code = 1
        elif gui is not None:
            try:
                logger.info("GUI mainloop'u başlatılıyor (webview.start) -- ana thread burada bloke olacak...")
                gui.start()
                logger.info("GUI mainloop'u normal şekilde sona erdi (pencere/uygulama kapatıldı).")
            except Exception:
                logger.exception(
                    "GUI penceresi başlatılamadı (webview.start hata verdi; "
                    "webkit2gtk-4.1/GTK kurulu değil ya da bozuk olabilir)."
                )
                gui_start_failed = True
            if tray is not None:
                try:
                    tray.stop()
                except Exception:
                    logger.exception("gui sonrası tray.stop() sırasında hata")

        if gui is None or gui_start_failed:
            if gui_start_failed:
                if tray is not None and tray_thread is None:
                    # run_detached denenmiş olabilir ama GUI çöktüğü için
                    # gerçek bir döngü hiç çalışmamış olabilir; tray'i şimdi
                    # klasik (kendi thread'i) modda TEKRAR başlatıyoruz.
                    logger.info("Tray, klasik (kendi thread'i) modda yeniden başlatılıyor...")
                    try:
                        tray.stop()
                    except Exception:
                        pass
                    tray_thread = _start_tray_thread(tray, tray_crashed, logger)
            if tray_thread is not None:
                while tray_thread.is_alive():
                    tray_thread.join(timeout=0.5)
            elif gui_start_failed and tray is None:
                exit_code = 1

        if tray_crashed.is_set():
            exit_code = 1
    except Exception:
        logger.exception("Ana döngüde beklenmeyen bir hata oluştu, uygulama sonlandırılıyor.")
        exit_code = 1
        if tray is not None:
            try:
                tray.stop()
            except Exception:
                pass
    finally:
        if tray_thread is not None:
            tray_thread.join(timeout=3)
        app.shutdown()
        try:
            lock_file.close()
        except OSError:
            pass
        logger.info("=== Boomusic kapandı (exit_code=%s) ===", exit_code)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
