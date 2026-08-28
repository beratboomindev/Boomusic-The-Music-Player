"""Dinleme istatistikleri: bir şarkının kaç kere çalındığını sayar.

Veriler ``~/.local/share/boomusic/stats.json`` içinde, dosya yolu -> sayaç
şeklinde saklanır. Bir şarkı çalmaya BAŞLADIĞINDA sayaç bir artırılır
(şarkının tamamı dinlenmese de). Bu, en basit ve öngörülebilir kural olduğu
için seçildi; farklı bir davranış istenirse (örn. sayaç sadece şarkının
en az %50'si dinlendiğinde artsın) bu mantığı değiştirmek yalnızca
``record_play`` çağrısının ne zaman yapıldığını (bkz. app.py) değiştirmeyi
gerektirir.

Yazma optimizasyonu: her ``record_play`` çağrısı hemen diske yazmaz.
2 saniyelik bir gecikme (debounce) ile toplu yazma yapılır; sürekli
çalma durumunda yazma sayısı büyük ölçüde azalır.
"""
from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .config import default_data_dir


_SAVE_DELAY = 2.0
_SAVE_POLL = 0.25


class Stats:
    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = Path(data_dir) if data_dir else default_data_dir()
        self.stats_file = self.data_dir / "stats.json"
        self._lock = threading.Lock()
        self._data: Dict[str, int] = self._load()
        self._dirty = threading.Event()
        self._stop = threading.Event()
        self._last_save = 0.0
        self._save_thread = threading.Thread(
            target=self._save_loop, name="boomusic-stats", daemon=True
        )
        self._save_thread.start()

    def _load(self) -> Dict[str, int]:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        if self.stats_file.exists():
            try:
                with open(self.stats_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    return {str(k): int(v) for k, v in data.items()}
            except (json.JSONDecodeError, OSError, ValueError):
                pass
        return {}

    def _save(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        tmp = self.stats_file.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)
        tmp.replace(self.stats_file)

    def _save_loop(self) -> None:
        while not self._stop.is_set():
            self._dirty.wait(timeout=_SAVE_POLL)
            if self._stop.is_set():
                break
            if self._dirty.is_set() and time.monotonic() - self._last_save >= _SAVE_DELAY:
                self._dirty.clear()
                with self._lock:
                    self._save()
                self._last_save = time.monotonic()

    def record_play(self, track_path: str) -> int:
        with self._lock:
            new_count = self._data.get(track_path, 0) + 1
            self._data[track_path] = new_count
        self._dirty.set()
        return new_count

    def get_count(self, track_path: str) -> int:
        return self._data.get(track_path, 0)

    def total_plays(self) -> int:
        return sum(self._data.values())

    def top(self, n: int = 5) -> List[Tuple[str, int]]:
        return sorted(self._data.items(), key=lambda kv: kv[1], reverse=True)[:n]

    def forget(self, track_path: str) -> None:
        with self._lock:
            if track_path in self._data:
                del self._data[track_path]
        self._dirty.set()

    def flush(self) -> None:
        self._dirty.set()
        with self._lock:
            self._save()
            self._dirty.clear()
