from __future__ import annotations

import time
import threading
from abc import ABC, abstractmethod
from typing import Any


class ThreadContextStore(ABC):
    """Abstract store for per-thread context data."""

    @abstractmethod
    def get(self, thread_id: str) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def put(self, thread_id: str, context: dict[str, Any]) -> None:
        raise NotImplementedError

    @abstractmethod
    def clear(self, thread_id: str) -> None:
        raise NotImplementedError


class LRUContextStore(ThreadContextStore):
    """In-memory LRU context store with TTL, safe for single-process use."""

    def __init__(self, max_size: int = 512, ttl_seconds: int = 3600) -> None:
        self._store: dict[str, dict[str, Any]] = {}
        self._access_times: dict[str, float] = {}
        self._ttl = ttl_seconds
        self._max_size = max_size
        self._lock = threading.Lock()

    def get(self, thread_id: str) -> dict[str, Any]:
        with self._lock:
            self._evict_expired()
            if thread_id in self._store:
                self._access_times[thread_id] = time.monotonic()
                return dict(self._store[thread_id])
            return {}

    def put(self, thread_id: str, context: dict[str, Any]) -> None:
        with self._lock:
            self._evict_expired()
            if len(self._store) >= self._max_size and thread_id not in self._store:
                self._evict_lru()
            self._store[thread_id] = dict(context)
            self._access_times[thread_id] = time.monotonic()

    def clear(self, thread_id: str) -> None:
        with self._lock:
            self._store.pop(thread_id, None)
            self._access_times.pop(thread_id, None)

    def _evict_expired(self) -> None:
        if self._ttl <= 0:
            return
        cutoff = time.monotonic() - self._ttl
        expired = [
            tid for tid, ts in self._access_times.items() if ts < cutoff
        ]
        for tid in expired:
            self._store.pop(tid, None)
            self._access_times.pop(tid, None)

    def _evict_lru(self) -> None:
        if not self._access_times:
            return
        lru_key = min(self._access_times, key=lambda k: self._access_times[k])
        self._store.pop(lru_key, None)
        self._access_times.pop(lru_key, None)
