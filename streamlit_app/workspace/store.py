"""Workspace persistence layer.

This module defines:

* :class:`RunRecord` / :class:`RunMeta` -- value types describing a saved run.
* :class:`WorkspaceStore` -- a structural :class:`Protocol` describing how
  the rest of ExoQ talks to a backend.
* :class:`LocalFileStore` -- the only concrete implementation today. Writes
  every run to ``<repo>/data/users/<user_id>/runs/<run_id>/``.
* :func:`get_store` -- factory used by the rest of the app. Inspects the
  ``EXOQ_WORKSPACE_BACKEND`` env var (default ``"local"``) and returns the
  appropriate store. When you add a Supabase or S3 store later, register it
  here -- nowhere else.

Design choices that keep us forward-compatible
----------------------------------------------
* **Run IDs are timestamped + nonce** (``2026-04-30_021530_a1b2c3``). They
  sort lexicographically and are globally unique without needing a database
  sequence -- so a future cloud migration is a straight ``aws s3 sync``.
* **Each run is self-contained** -- a folder of CSV + JSON only. Migration
  to cloud storage is a copy. No relational dependencies between rows.
* **Schema versioning** -- ``metadata.json`` stores ``"schema_version": 1``
  so future format changes can be migrated tractably.
* **Identity is a string** -- today derived from a chosen username, later
  from an OAuth ``sub`` claim. Same string everywhere.
"""

from __future__ import annotations

import json
import os
import re
import secrets
import shutil
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

import pandas as pd

SCHEMA_VERSION = 1


# ---------------------------------------------------------------------------
# Value types
# ---------------------------------------------------------------------------
@dataclass
class RunMeta:
    """Compact metadata describing a saved run (used by list views)."""

    run_id: str
    user_id: str
    created_at: str            # ISO-8601 UTC
    module: str                # e.g. "module1"
    source: str                # "csv" | "manual"
    inputs_count: int
    survivors_count: int
    gold: int
    silver: int
    failed: int
    label: str = ""            # optional user-supplied note
    schema_version: int = SCHEMA_VERSION


@dataclass
class RunRecord:
    """A run that's ready to be saved.

    Files are stored as DataFrames keyed by filename (without extension); the
    store is responsible for serialising them to disk.
    """

    meta: RunMeta
    frames: Dict[str, pd.DataFrame] = field(default_factory=dict)
    extras: Dict[str, Any] = field(default_factory=dict)  # arbitrary JSON-able blobs


# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------
@runtime_checkable
class WorkspaceStore(Protocol):
    """Pluggable storage protocol. Today: local files. Later: cloud."""

    def save_run(self, record: RunRecord) -> str: ...
    def list_runs(self, user_id: str) -> List[RunMeta]: ...
    def load_run(self, user_id: str, run_id: str) -> RunRecord: ...
    def delete_run(self, user_id: str, run_id: str) -> None: ...
    def user_exists(self, user_id: str) -> bool: ...
    def create_user(self, user_id: str, display_name: str = "") -> None: ...


# ---------------------------------------------------------------------------
# ID helpers
# ---------------------------------------------------------------------------
_USER_ID_RE = re.compile(r"[^a-z0-9_-]+")


def normalize_user_id(raw: str) -> str:
    """Sanitise a free-text username into a filesystem-safe identifier.

    >>> normalize_user_id('Sid Balatan!')
    'sid_balatan'
    """
    if not raw:
        return ""
    s = raw.strip().lower().replace(" ", "_")
    s = _USER_ID_RE.sub("", s)
    return s[:64] or ""


def new_run_id() -> str:
    """Sortable + unique run id without external deps.

    Format: ``YYYY-MM-DD_HHMMSS_<6 hex chars>``. Lexicographic sort matches
    chronological order; the nonce avoids collisions when two runs land in
    the same second.
    """
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M%S")
    return f"{ts}_{secrets.token_hex(3)}"


# ---------------------------------------------------------------------------
# Local file backend
# ---------------------------------------------------------------------------
def _repo_data_root() -> Path:
    """Return the repo's ``data/users`` directory, creating it if absent."""
    here = Path(__file__).resolve()
    repo_root = here.parents[2]  # streamlit_app/workspace/store.py -> repo root
    base = repo_root / "data" / "users"
    base.mkdir(parents=True, exist_ok=True)
    return base


class LocalFileStore:
    """File-backed implementation of :class:`WorkspaceStore`.

    Layout::

        data/users/<user_id>/runs/<run_id>/metadata.json
                                          /<frame_name>.csv ...
                                          /extras.json
    """

    def __init__(self, root: Optional[Path] = None) -> None:
        self.root: Path = Path(root) if root is not None else _repo_data_root()
        self.root.mkdir(parents=True, exist_ok=True)

    # -- internal helpers --------------------------------------------------
    def _user_dir(self, user_id: str) -> Path:
        uid = normalize_user_id(user_id)
        if not uid:
            raise ValueError("user_id must be non-empty after normalization")
        d = self.root / uid
        d.mkdir(parents=True, exist_ok=True)
        (d / "runs").mkdir(parents=True, exist_ok=True)
        return d

    def _run_dir(self, user_id: str, run_id: str) -> Path:
        return self._user_dir(user_id) / "runs" / run_id

    # -- protocol ----------------------------------------------------------
    def save_run(self, record: RunRecord) -> str:
        run_dir = self._run_dir(record.meta.user_id, record.meta.run_id)
        run_dir.mkdir(parents=True, exist_ok=True)

        # Frames as CSV (small, portable, diff-friendly).
        for name, df in record.frames.items():
            safe = re.sub(r"[^a-zA-Z0-9_-]+", "_", name)
            df.to_csv(run_dir / f"{safe}.csv", index=False)

        if record.extras:
            (run_dir / "extras.json").write_text(
                json.dumps(record.extras, indent=2, default=str), encoding="utf-8"
            )

        (run_dir / "metadata.json").write_text(
            json.dumps(asdict(record.meta), indent=2), encoding="utf-8"
        )
        return record.meta.run_id

    def list_runs(self, user_id: str) -> List[RunMeta]:
        runs_dir = self._user_dir(user_id) / "runs"
        out: List[RunMeta] = []
        if not runs_dir.exists():
            return out
        for child in sorted(runs_dir.iterdir(), reverse=True):
            meta_path = child / "metadata.json"
            if not meta_path.exists():
                continue
            try:
                raw = json.loads(meta_path.read_text(encoding="utf-8"))
                out.append(RunMeta(**raw))
            except Exception:
                # Malformed metadata -- skip rather than crash the page.
                continue
        return out

    def load_run(self, user_id: str, run_id: str) -> RunRecord:
        run_dir = self._run_dir(user_id, run_id)
        meta_path = run_dir / "metadata.json"
        if not meta_path.exists():
            raise FileNotFoundError(f"No such run: {run_id}")

        meta = RunMeta(**json.loads(meta_path.read_text(encoding="utf-8")))

        frames: Dict[str, pd.DataFrame] = {}
        for csv_path in run_dir.glob("*.csv"):
            try:
                frames[csv_path.stem] = pd.read_csv(csv_path)
            except Exception:
                continue

        extras: Dict[str, Any] = {}
        extras_path = run_dir / "extras.json"
        if extras_path.exists():
            try:
                extras = json.loads(extras_path.read_text(encoding="utf-8"))
            except Exception:
                extras = {}

        return RunRecord(meta=meta, frames=frames, extras=extras)

    def delete_run(self, user_id: str, run_id: str) -> None:
        run_dir = self._run_dir(user_id, run_id)
        if run_dir.exists():
            shutil.rmtree(run_dir)

    # -- account helpers ---------------------------------------------------
    def _profile_path(self, user_id: str) -> Path:
        uid = normalize_user_id(user_id)
        return self.root / uid / "profile.json"

    def user_exists(self, user_id: str) -> bool:
        """A user 'exists' once we've written a profile marker for them."""
        uid = normalize_user_id(user_id)
        if not uid:
            return False
        return (self.root / uid / "profile.json").exists()

    def create_user(self, user_id: str, display_name: str = "") -> None:
        """Create the profile marker for a new account.

        Idempotent: writing twice keeps the original ``created_at`` so the
        caller can guard with :meth:`user_exists` to decide whether the
        account is fresh.
        """
        uid = normalize_user_id(user_id)
        if not uid:
            raise ValueError("user_id must be non-empty after normalization")
        d = self._user_dir(uid)
        prof = d / "profile.json"
        if prof.exists():
            try:
                existing = json.loads(prof.read_text(encoding="utf-8"))
            except Exception:
                existing = {}
        else:
            existing = {
                "user_id": uid,
                "display_name": display_name or uid,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "schema_version": SCHEMA_VERSION,
            }
        # Allow display_name updates without resetting created_at.
        if display_name:
            existing["display_name"] = display_name
        prof.write_text(json.dumps(existing, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------
_STORE_SINGLETON: Optional[WorkspaceStore] = None


def get_store() -> WorkspaceStore:
    """Return the configured workspace store (cached as a module singleton).

    Today we always return :class:`LocalFileStore`. To swap backends later,
    register the new implementation here keyed off ``EXOQ_WORKSPACE_BACKEND``.
    """
    global _STORE_SINGLETON
    if _STORE_SINGLETON is not None:
        return _STORE_SINGLETON

    backend = os.environ.get("EXOQ_WORKSPACE_BACKEND", "local").lower()

    if backend == "local":
        _STORE_SINGLETON = LocalFileStore()
    else:
        # Future: "supabase", "s3", ...
        raise ValueError(
            f"Unknown EXOQ_WORKSPACE_BACKEND={backend!r}. "
            f"Currently supported: 'local'."
        )

    return _STORE_SINGLETON
