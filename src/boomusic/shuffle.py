"""'Smart Shuffle' algoritması.

Kural: Playlist'teki bir şarkı, diğer TÜM şarkılar en az bir kez çalınmadan
tekrar çalınamaz. Örnek: 3 şarkı var (A, B, C). Önce A çalındı. B ve C
çalınana kadar A bir daha seçilmez. B ve C de çalındığında "tur"
tamamlanmış olur ve algoritma sıfırlanır: A, B, C tekrar seçilebilir hale
gelir (yeni, rastgele bir sırayla).

Bu, oyunlarda sık kullanılan "torba karıştırma" (bag shuffle) yöntemidir:
Elimizde henüz bu turda çalınmamış şarkıların olduğu bir "torba" vardır.
Bir şarkı seçilince torbadan çıkar. Torba boşaldığında bütün şarkılarla
yeniden doldurulur ve karıştırılır (bir öncekiyle art arda aynı şarkının
gelmemesi için, mümkünse son çalınan şarkı yeni torbanın ilk turundan
hariç tutulur).

Ayrıca "önceki / sonraki" gezinmesi için basit bir geçmiş (history) tutulur;
böylece "önceki şarkı" tuşu gerçekten az önce çalan şarkıya geri gider,
torbadan yeni bir rastgele seçim yapmaz. "Sonraki" tuşuna, geri gidilmiş
bir noktadan basılırsa da önce bu geçmişte ileri gidilir (redo), torba
sadece geçmişin en ucundayken tüketilir.
"""
from __future__ import annotations

import random
from typing import Iterable, List, Optional, Set


class SmartShuffle:
    MAX_HISTORY = 500

    def __init__(self, track_paths: Optional[Iterable[str]] = None):
        self._all_paths: List[str] = []
        self._bag_set: Set[str] = set()
        self._bag_list: List[str] = []
        self._history: List[str] = []
        self._position: int = -1
        if track_paths is not None:
            self.set_tracks(track_paths)

    def set_tracks(self, track_paths: Iterable[str]) -> None:
        new_paths = list(track_paths)
        new_set = set(new_paths)
        old_set = set(self._all_paths)

        self._all_paths = new_paths

        self._history = [p for p in self._history if p in new_set]
        if self._position >= len(self._history):
            self._position = len(self._history) - 1

        self._bag_list = [p for p in self._bag_list if p in new_set]
        added = [p for p in new_paths if p not in old_set]
        if added:
            self._bag_list.extend(added)
            random.shuffle(self._bag_list)
        self._bag_set = set(self._bag_list)

    def has_tracks(self) -> bool:
        return len(self._all_paths) > 0

    def track_count(self) -> int:
        return len(self._all_paths)

    def current_track(self) -> Optional[str]:
        if 0 <= self._position < len(self._history):
            return self._history[self._position]
        return None

    def has_previous(self) -> bool:
        return self._position > 0

    def remaining_in_round(self) -> int:
        return len(self._bag_list)

    def add_track(self, path: str) -> None:
        if path not in self._all_paths:
            self._all_paths.append(path)
        if path not in self._bag_set:
            self._bag_list.append(path)
            self._bag_set.add(path)

    def next_track(self) -> Optional[str]:
        if not self._all_paths:
            return None

        if self._position < len(self._history) - 1:
            self._position += 1
            return self._history[self._position]

        if not self._bag_list:
            self._refill_bag(exclude=self.current_track())

        if self._bag_list:
            pick = self._bag_list.pop()
            self._bag_set.discard(pick)
        else:
            pick = self._all_paths[0]

        self._append_history(pick)
        return pick

    def previous_track(self) -> Optional[str]:
        if self._position > 0:
            self._position -= 1
            return self._history[self._position]
        return self.current_track()

    def play_specific(self, path: str) -> Optional[str]:
        if path not in self._all_paths:
            return None
        if path in self._bag_set:
            self._bag_list.remove(path)
            self._bag_set.discard(path)
        self._append_history(path)
        return path

    def is_played_this_round(self, path: str) -> bool:
        return path in self._all_paths and path not in self._bag_set

    def _refill_bag(self, exclude: Optional[str]) -> None:
        pool = list(self._all_paths)
        random.shuffle(pool)
        if exclude is not None and len(pool) > 1 and pool[-1] == exclude:
            swap_with = random.randrange(len(pool) - 1)
            pool[-1], pool[swap_with] = pool[swap_with], pool[-1]
        self._bag_list = pool
        self._bag_set = set(pool)

    def _append_history(self, path: str) -> None:
        self._history.append(path)
        self._position = len(self._history) - 1
        if len(self._history) > self.MAX_HISTORY:
            trim = len(self._history) - self.MAX_HISTORY
            self._history = self._history[trim:]
            self._position -= trim
