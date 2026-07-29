"""YouTube entegrasyonu (yt-dlp tabanlı).

yt-dlp kullanarak YouTube Music'ten şarkı arar ve çalar. API anahtarı
gerektirmez, sınırsız erişim sağlar.

Özellikler:
- ymsearch: Sadece müzik/podcast içeriği (videolar, klipler hariç)
- Süre filtresi: 30 saniyeden kısa videolar elenir
- Stream URL cache: 30 dakika süreli cache ile tekrar istek gönderilmez
- Reklamsız: yt-dlp zaten reklam göstermez
"""
from __future__ import annotations

import json
import logging
import os
import re
import shutil
import subprocess
import threading
import time
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional

logger = logging.getLogger("boomusic.youtube")

SEARCH_TIMEOUT = 15  # saniye
STREAM_URL_TIMEOUT = 20  # saniye
CACHE_TTL = 1800  # 30 dakika
MIN_DURATION = 60    # 60 saniyeden kısa videoları (shorts) hariç tut
MAX_DURATION = 1200  # 20 dakikadan uzun videoları (podcast/vlog) hariç tut


@dataclass(frozen=True)
class YoutubeResult:
    """YouTube arama sonucu."""
    video_id: str
    title: str
    channel: str
    duration: float  # saniye
    thumbnail_url: str
    view_count: int = 0

    @property
    def display_name(self) -> str:
        return f"{self.title} - {self.channel}"

    @property
    def duration_str(self) -> str:
        """GG:SS formatında süre."""
        mins = int(self.duration) // 60
        secs = int(self.duration) % 60
        return f"{mins}:{secs:02d}"

    def to_dict(self) -> dict:
        d = asdict(self)
        d["type"] = "youtube"
        d["subtitle"] = self.channel
        return d


class _StreamUrlCache:
    """Stream URL'leri için basit TTL cache."""

    def __init__(self, ttl: int = CACHE_TTL):
        self._cache: Dict[str, tuple] = {}  # video_id -> (url, timestamp)
        self._lock = threading.Lock()
        self._ttl = ttl

    def get(self, video_id: str) -> Optional[str]:
        with self._lock:
            if video_id in self._cache:
                url, ts = self._cache[video_id]
                if time.time() - ts < self._ttl:
                    return url
                del self._cache[video_id]
        return None

    def set(self, video_id: str, url: str) -> None:
        with self._lock:
            self._cache[video_id] = (url, time.time())

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()


def check_yt_dlp() -> bool:
    """yt-dlp'nin kurulu olup olmadığını kontrol eder."""
    return shutil.which("yt-dlp") is not None


def _prewarm_stream_cache(results: List[YoutubeResult]) -> None:
    """Arama sonuçlarındaki ilk 2 videonun stream URL'ini önceden cache'ler."""
    def warm():
        warmed = 0
        for r in results:
            if warmed >= 2:
                break
            if r.video_id not in _stream_cache:
                try:
                    youtube_get_stream_url(r.video_id)
                    warmed += 1
                except Exception:
                    pass
    threading.Thread(target=warm, daemon=True).start()


def _pick_thumbnail(thumbnails: list) -> str:
    if not thumbnails:
        return ""
    for t in reversed(thumbnails):
        if t.get("id") in ("maxresdefault", "sddefault", "hqdefault", "mqdefault"):
            return t.get("url", "")
    return thumbnails[-1].get("url", "")


def _parse_yt_result(data: dict) -> Optional[YoutubeResult]:
    video_id = data.get("id", "")
    if not video_id:
        return None
    try:
        duration = float(data.get("duration") or 0)
    except (TypeError, ValueError):
        duration = 0.0
    if duration and (duration < MIN_DURATION or duration > MAX_DURATION):
        return None
    return YoutubeResult(
        video_id=video_id,
        title=data.get("title", "Bilinmeyen"),
        channel=data.get("channel", data.get("uploader", "Bilinmeyen")),
        duration=float(duration) if duration else 0.0,
        thumbnail_url=_pick_thumbnail(data.get("thumbnails") or []),
        view_count=int(data.get("view_count", 0) or 0),
    )


def _run_yt_dlp(cmd: list, timeout: int):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        logger.warning("yt-dlp zaman aşımı")
    except Exception:
        logger.exception("yt-dlp hatası")
    return None


def _parse_json_lines(output: str) -> List[YoutubeResult]:
    results: List[YoutubeResult] = []
    for line in output.strip().split("\n"):
        if not line.strip():
            continue
        try:
            r = _parse_yt_result(json.loads(line))
            if r:
                results.append(r)
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            continue
    return results


def youtube_search(query: str, limit: int = 10) -> List[YoutubeResult]:
    yt_dlp = shutil.which("yt-dlp")
    if not yt_dlp or not query or not query.strip():
        return []

    # Önce ymsearch (YouTube Music) dene — genelde müzik sonuçları döner
    # Olmazsa ytsearch'e düş (süre filtresi sayesinde çoğu video elenir)
    for extractor in ("ymsearch", "ytsearch"):
        cmd = [
            yt_dlp,
            f"{extractor}{limit}:{query.strip()}",
            "--flat-playlist", "--dump-json", "--no-download",
            "--no-warnings", "--no-check-formats",
        ]
        result = _run_yt_dlp(cmd, SEARCH_TIMEOUT)
        if result is None or result.returncode != 0:
            if result is not None:
                logger.warning("yt-dlp %s hatası (returncode=%d): %s",
                               extractor, result.returncode, result.stderr[:200])
            continue
        results = _parse_json_lines(result.stdout)
        if results:
            logger.info("YouTube araması (%s): '%s' -> %d sonuç", extractor, query, len(results))
            _prewarm_stream_cache(results)
            return results

    return []


def youtube_get_stream_url(video_id: str) -> Optional[str]:
    """YouTube videosu için çalınabilir ses URL'ini döner.

    Stream URL'leri cache'lenir (30 dk TTL). URL'lerin süresi dolabilir,
    bu yüzden cache'den alınamazsa yeniden istenir.

    Args:
        video_id: YouTube video ID'si

    Returns:
        Çalınabilir URL veya None
    """
    yt_dlp = shutil.which("yt-dlp")
    if not yt_dlp:
        logger.error("yt-dlp bulunamadı")
        return None

    # Cache kontrolü
    cached = _stream_cache.get(video_id)
    if cached:
        return cached

    url = f"https://www.youtube.com/watch?v={video_id}"
    format_tries = [
        ["-f", "bestaudio[ext=m4a]/bestaudio"],
        ["-f", "bestaudio/best"],
        ["-f", "worstaudio/worst"],
    ]
    base_cmd = [
        yt_dlp, url, "--get-url", "--no-warnings",
        "--extractor-retries", "3",
        "--allow-unplayable-formats",
    ]
    # Önce player_client ile dene, olmazsa sade halini dene
    client_tries = [
        ["--extractor-args", "youtube:player_client=android,web"],
        [],
    ]

    for client_args in client_tries:
        for fmt_args in format_tries:
            cmd = base_cmd + client_args + fmt_args
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=STREAM_URL_TIMEOUT,
                )
            except subprocess.TimeoutExpired:
                logger.warning("Stream URL alma zaman aşımı: %s", video_id)
                continue
            except Exception:
                logger.exception("Stream URL alma hatası: %s", video_id)
                continue

            if result.returncode != 0:
                logger.debug("yt-dlp stream denemesi başarısız (returncode=%d): %s",
                             result.returncode, result.stderr[:120])
                continue

            stream_url = result.stdout.strip().split("\n")[0] if result.stdout.strip() else None
            if stream_url:
                _stream_cache.set(video_id, stream_url)
                logger.info("Stream URL alındı: %s", video_id)
                return stream_url

    logger.warning("Tüm stream URL denemeleri başarısız: %s", video_id)
    return None


def youtube_get_video_info(video_id: str) -> Optional[YoutubeResult]:
    yt_dlp = shutil.which("yt-dlp")
    if not yt_dlp:
        return None

    url = f"https://www.youtube.com/watch?v={video_id}"
    cmd_base = [
        yt_dlp, url, "--dump-json", "--no-download", "--no-warnings",
        "--extractor-retries", "3",
        "--allow-unplayable-formats",
    ]
    client_tries = [
        ["--extractor-args", "youtube:player_client=android,web"],
        [],
    ]
    for client_args in client_tries:
        cmd = cmd_base + client_args
        result = _run_yt_dlp(cmd, STREAM_URL_TIMEOUT)
        if result is None or result.returncode != 0:
            continue
        try:
            return _parse_yt_result(json.loads(result.stdout))
        except Exception:
            logger.exception("Video bilgisi parse hatası: %s", video_id)
            continue

    return None


DOWNLOAD_TIMEOUT = 300
DOWNLOAD_DIR_NAME = "YouTube İndirilenler"


def _parse_progress(line: str) -> Optional[float]:
    match = re.search(r'(\d+\.?\d*)%', line)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None


def _youtube_download_impl(cmd: list, progress_callback) -> Optional[str]:
    yt_dlp = shutil.which("yt-dlp")
    if not yt_dlp:
        return None
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
    except Exception:
        logger.exception("yt-dlp indirme başlatılamadı")
        return None

    for line in iter(process.stderr.readline, ''):
        if not line:
            break
        if progress_callback:
            pct = _parse_progress(line)
            if pct is not None:
                progress_callback(pct)

    process.wait()
    if process.returncode != 0:
        remaining = process.stderr.read() if not process.stderr.closed else ''
        logger.warning("yt-dlp indirme hatası (returncode=%d): %s",
                       process.returncode, (remaining or '')[:300])
        return None

    filepath = ''
    if process.stdout and not process.stdout.closed:
        filepath = process.stdout.read().strip()
    if filepath and os.path.isfile(filepath):
        return filepath
    return None


def youtube_download(video_id: str, output_dir: str,
                     progress_callback=None) -> Optional[str]:
    yt_dlp = shutil.which("yt-dlp")
    if not yt_dlp:
        return None

    url = f"https://www.youtube.com/watch?v={video_id}"
    output_template = os.path.join(output_dir, "%(title)s.%(ext)s")
    cmd = [
        yt_dlp, url,
        "-x", "--audio-format", "mp3", "--audio-quality", "0",
        "-f", "bestaudio[ext=m4a]/bestaudio",
        "-o", output_template,
        "--embed-thumbnail", "--add-metadata",
        "--no-warnings", "--no-playlist", "--newline",
        "--print", "after_move:filepath",
        "--extractor-retries", "3",
    ]

    try:
        os.makedirs(output_dir, exist_ok=True)
    except Exception:
        logger.exception("İndirme klasörü oluşturulamadı: %s", output_dir)
        return None

    return _youtube_download_impl(cmd, progress_callback)


def youtube_download_url(url: str, output_dir: str,
                         progress_callback=None) -> Optional[str]:
    yt_dlp = shutil.which("yt-dlp")
    if not yt_dlp:
        return None

    output_template = os.path.join(output_dir, "%(title)s.%(ext)s")
    cmd = [
        yt_dlp, url,
        "-x", "--audio-format", "mp3", "--audio-quality", "0",
        "-f", "bestaudio[ext=m4a]/bestaudio",
        "-o", output_template,
        "--embed-thumbnail", "--add-metadata",
        "--no-warnings", "--no-playlist", "--newline",
        "--print", "after_move:filepath",
        "--extractor-retries", "3",
    ]

    try:
        os.makedirs(output_dir, exist_ok=True)
    except Exception:
        logger.exception("İndirme klasörü oluşturulamadı: %s", output_dir)
        return None

    return _youtube_download_impl(cmd, progress_callback)


# Global cache instance'ı
_stream_cache = _StreamUrlCache()
