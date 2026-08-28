"""libVLC (python-vlc) üzerinde ince bir ses çalma katmanı (AudioEngine).

NEDEN pygame DEĞİL VLC: Arayüzdeki "istediğin saniyeye sar" (seek) özelliği
için MP3'lerde GÜVENİLİR mutlak konumlandırma gerekiyordu. pygame/SDL_mixer
bunu MP3'te sadece GÖRECELİ (mevcut konumdan itibaren) ve VBR kodlamada
hatalı yapabiliyor. libVLC, formattan bağımsız, doğru ve mutlak seek
sağlıyor -- bu yüzden ses motorunu buna taşıdık.

Bu modül playlist, shuffle ya da istatistik gibi kavramları BİLMEZ; sadece
"bir dosyayı çal / duraklat / durdur / sar / sesini ayarla" işini yapar ve
bir parça kendiliğinden bittiğinde ``on_track_finished`` callback'ini
tetikler. Playlist / shuffle mantığı üst seviyede (``app.py``) yönetilir.

Fade in/out: libVLC'de pygame'deki gibi hazır bir "fade_ms" yoktur; bu
yüzden burada FADE_SECONDS boyunca sesi küçük adımlarla değiştiren tek bir
arka plan thread'i ile MANUEL olarak uygulanır (her fade için yeni thread
oluşturmak yerine kuyruklu tek thread).
"""
from __future__ import annotations

import logging
import queue
import threading
import time
from typing import Callable, NamedTuple, Optional

import vlc

logger = logging.getLogger("boomusic.player")

POLL_INTERVAL_SECONDS = 0.2
FADE_SECONDS = 2.0
FADE_STEPS = 30
FADE_STEP_SECONDS = FADE_SECONDS / FADE_STEPS
MIN_DURATION_FOR_NATURAL_FADE = FADE_SECONDS + 1.0


class _FadeCommand(NamedTuple):
    generation: int
    from_percent: int
    to_percent: int


class AudioEngine:
    def __init__(
        self,
        on_track_finished: Optional[Callable[[], None]] = None,
        extra_vlc_args: tuple = (),
    ):
        self.on_track_finished = on_track_finished

        self._current_path: Optional[str] = None
        self._current_duration: Optional[float] = None
        self._active = False
        self._paused = False
        self._natural_fade_started = False
        self._volume = 0.8
        self._fade_generation = 0
        self._lock = threading.Lock()
        self._stop_events = threading.Event()

        self._audio_ready = False
        self._instance: Optional[vlc.Instance] = None
        self._vlc_player: Optional[vlc.MediaPlayer] = None
        try:
            vlc_args = ["--no-video", "--quiet"]
            if extra_vlc_args:
                vlc_args.extend(extra_vlc_args)
            self._instance = vlc.Instance(*vlc_args)
            if self._instance is None:
                raise RuntimeError("vlc.Instance() None döndü (geçersiz argümanlar?)")
            self._vlc_player = self._instance.media_player_new()
            self._audio_ready = True
        except Exception as exc:
            logger.error("Ses cihazı (libVLC) başlatılamadı: %s", exc)

        # Single shared fade thread with a command queue
        self._fade_queue: "queue.Queue[_FadeCommand]" = queue.Queue()
        self._fade_thread = threading.Thread(
            target=self._fade_loop, name="boomusic-fade", daemon=True
        )
        self._fade_thread.start()

        self._watch_thread = threading.Thread(
            target=self._watch_loop, name="boomusic-audio-watch", daemon=True
        )
        self._watch_thread.start()

    @property
    def audio_ready(self) -> bool:
        return self._audio_ready

    def set_volume(self, volume: float) -> float:
        self._volume = max(0.0, min(1.0, volume))
        with self._lock:
            self._fade_generation += 1
        if self._audio_ready:
            self._vlc_player.audio_set_volume(round(self._volume * 100))
        return self._volume

    def get_volume(self) -> float:
        return self._volume

    def play(self, path: str, duration_seconds: Optional[float] = None) -> bool:
        if not self._audio_ready:
            return False
        with self._lock:
            try:
                media = self._instance.media_new(path)
                self._vlc_player.set_media(media)
                self._vlc_player.audio_set_volume(0)
                ok = self._vlc_player.play()
                if ok != 0:
                    raise RuntimeError("libvlc play() sıfırdan farklı döndü")
            except Exception as exc:
                logger.error("Çalınamadı (%s): %s", path, exc)
                self._active = False
                self._current_path = None
                self._current_duration = None
                return False
            self._current_path = path
            self._current_duration = (
                duration_seconds
                if duration_seconds and duration_seconds >= MIN_DURATION_FOR_NATURAL_FADE
                else None
            )
            self._active = True
            self._paused = False
            self._natural_fade_started = False
            self._fade_generation += 1
            gen = self._fade_generation

        self._fade_queue.put(_FadeCommand(gen, 0, round(self._volume * 100)))
        return True

    def toggle_pause(self) -> bool:
        with self._lock:
            if not self._audio_ready or self._current_path is None:
                return self._paused
            if self._paused:
                self._vlc_player.play()
                self._paused = False
            else:
                self._vlc_player.pause()
                self._paused = True
            return self._paused

    def stop(self, fade_out: bool = False) -> None:
        with self._lock:
            if not self._audio_ready:
                self._active = False
                self._paused = False
                return
            should_fade = fade_out and self._active and not self._paused
            self._fade_generation += 1
            gen = self._fade_generation
            vol = round(self._volume * 100)
            self._active = False
            self._paused = False

        if should_fade:
            self._fade_queue.put(_FadeCommand(gen, vol, 0))
            self._fade_queue.join()
            with self._lock:
                if self._fade_generation == gen:
                    self._vlc_player.stop()
        else:
            self._vlc_player.stop()

    def is_paused(self) -> bool:
        return self._paused

    def is_active(self) -> bool:
        return self._active

    def current_path(self) -> Optional[str]:
        return self._current_path

    def set_current_path(self, path: Optional[str]) -> None:
        with self._lock:
            self._current_path = path

    def get_position_seconds(self) -> float:
        if not self._audio_ready or not self._active:
            return 0.0
        ms = self._vlc_player.get_time()
        return max(0.0, ms / 1000.0) if ms and ms > 0 else 0.0

    def get_duration_seconds(self) -> float:
        if not self._audio_ready:
            return 0.0
        ms = self._vlc_player.get_length()
        if ms and ms > 0:
            return ms / 1000.0
        return self._current_duration or 0.0

    def seek_to(self, seconds: float) -> None:
        if not self._audio_ready or not self._active:
            return
        duration = self.get_duration_seconds()
        seconds = max(0.0, min(seconds, duration if duration > 0 else seconds))
        with self._lock:
            self._vlc_player.set_time(int(seconds * 1000))
            self._natural_fade_started = False

    def shutdown(self) -> None:
        self._stop_events.set()
        self.stop(fade_out=False)

    # -- Single reusable fade thread ------------------------------------------------
    def _fade_loop(self) -> None:
        while not self._stop_events.is_set():
            try:
                cmd = self._fade_queue.get(timeout=0.5)
            except queue.Empty:
                continue
            self._execute_fade(cmd)
            self._fade_queue.task_done()

    def _execute_fade(self, cmd: _FadeCommand) -> None:
        if not self._audio_ready:
            return
        for step in range(FADE_STEPS + 1):
            with self._lock:
                if self._fade_generation != cmd.generation:
                    return
                frac = step / FADE_STEPS
                level = round(cmd.from_percent + (cmd.to_percent - cmd.from_percent) * frac)
            self._vlc_player.audio_set_volume(max(0, min(100, level)))
            if step < FADE_STEPS:
                time.sleep(FADE_STEP_SECONDS)

    # -- İzleme döngüsü --------------------------------------------------------------
    def _watch_loop(self) -> None:
        while not self._stop_events.is_set():
            time.sleep(POLL_INTERVAL_SECONDS)
            if not self._audio_ready:
                continue

            trigger_finished = False
            with self._lock:
                if self._active and not self._paused:
                    if not self._natural_fade_started and self._current_duration is not None:
                        remaining = self._current_duration - self.get_position_seconds()
                        if 0 <= remaining <= FADE_SECONDS:
                            self._natural_fade_started = True
                            self._fade_generation += 1
                            gen = self._fade_generation
                            self._fade_queue.put(
                                _FadeCommand(gen, round(self._volume * 100), 0)
                            )

                    if not self._vlc_player.is_playing() and self._vlc_player.get_state() in (
                        vlc.State.Ended, vlc.State.Stopped, vlc.State.Error,
                    ):
                        self._active = False
                        trigger_finished = True

            if trigger_finished and self.on_track_finished:
                try:
                    self.on_track_finished()
                except Exception:
                    logger.exception("on_track_finished callback hata verdi")
