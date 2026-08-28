"""In-memory async job tracking for video inference.

A single-process in-memory store is sufficient for the local demo and for
tests. For a horizontally scaled deployment, replace this with a Redis- or
database-backed store behind the same JobStore interface -- see
docs/architecture.md for the scaling note.
"""

from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field

from .schemas import JobStatusEnum, VideoInferenceResult


@dataclass
class Job:
    job_id: str
    status: JobStatusEnum = JobStatusEnum.queued
    result: VideoInferenceResult | None = None
    error: str | None = None
    created_at: float = field(default_factory=time.time)


class JobStore:
    def __init__(self, ttl_s: int = 3600) -> None:
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()
        self._ttl_s = ttl_s

    def create(self) -> Job:
        job = Job(job_id=str(uuid.uuid4()))
        with self._lock:
            self._jobs[job.job_id] = job
        return job

    def get(self, job_id: str) -> Job | None:
        self._evict_expired()
        with self._lock:
            return self._jobs.get(job_id)

    def mark_processing(self, job_id: str) -> None:
        with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id].status = JobStatusEnum.processing

    def mark_completed(self, job_id: str, result: VideoInferenceResult) -> None:
        with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id].status = JobStatusEnum.completed
                self._jobs[job_id].result = result

    def mark_failed(self, job_id: str, error: str) -> None:
        with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id].status = JobStatusEnum.failed
                self._jobs[job_id].error = error

    def _evict_expired(self) -> None:
        cutoff = time.time() - self._ttl_s
        with self._lock:
            expired = [jid for jid, job in self._jobs.items() if job.created_at < cutoff]
            for jid in expired:
                del self._jobs[jid]
