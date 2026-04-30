"""Workspace package: persistent per-user storage for ExoQ runs.

The :mod:`workspace.store` module defines a small protocol that abstracts
*where* user data lives. Today we ship :class:`LocalFileStore` which writes
to ``data/users/<user_id>/runs/<run_id>/``. Tomorrow we add a
``SupabaseStore`` that satisfies the same protocol. Modules never touch
the filesystem directly; they go through this protocol so swapping
backends is a one-line config change.
"""

from .identity import auth_strip, current_user, sign_in_widget
from .store import (
    LocalFileStore,
    RunMeta,
    RunRecord,
    WorkspaceStore,
    get_store,
)

__all__ = [
    "LocalFileStore",
    "RunMeta",
    "RunRecord",
    "WorkspaceStore",
    "get_store",
    "current_user",
    "sign_in_widget",
    "auth_strip",
]
