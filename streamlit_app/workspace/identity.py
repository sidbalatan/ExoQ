"""Lightweight identity layer for ExoQ.

Today we ship a username-only sign-in (no password). It exists purely to
give every user a stable ``user_id`` so :class:`workspace.store.LocalFileStore`
can carve out a per-user folder. This module is intentionally thin so we can
later replace it with ``streamlit-authenticator`` or an OAuth flow without
touching Module 1-8.

**No sidebar.** Per project rule, the sign-in widget renders inside the
existing ``☰ Main Menu`` popover at the top of Home.py.
"""

from __future__ import annotations

from typing import Optional

import streamlit as st

from .store import normalize_user_id


SESSION_KEY = "exoq_user_id"
SESSION_DISPLAY_KEY = "exoq_user_display_name"


def current_user() -> Optional[str]:
    """Return the signed-in user_id (filesystem-safe), or ``None``."""
    return st.session_state.get(SESSION_KEY)


def current_display_name() -> str:
    """Return the user's chosen display name (free text)."""
    return st.session_state.get(SESSION_DISPLAY_KEY, "")


def sign_out() -> None:
    """Clear the in-session identity. Per-user files are left intact on disk."""
    st.session_state.pop(SESSION_KEY, None)
    st.session_state.pop(SESSION_DISPLAY_KEY, None)


def sign_in_widget(*, location_label: str = "👤 Sign in") -> None:
    """Render a self-contained sign-in / sign-out widget.

    Designed to be placed inside any container (e.g. the ``☰ Main Menu``
    popover). Renders:

    * If signed in -> a one-line summary plus a "Sign out" button.
    * If signed out -> a username text input plus a "Sign in" button.

    The widget never touches global layout (no sidebar, no top bar).
    """
    uid = current_user()
    if uid:
        st.markdown(
            f"**{location_label}** &nbsp;·&nbsp; signed in as `{current_display_name() or uid}` "
            f"(`{uid}`)"
        )
        if st.button("Sign out", key="exoq_signout_btn"):
            sign_out()
            st.rerun()
        return

    st.markdown(f"**{location_label}**")
    with st.form("exoq_signin_form", clear_on_submit=False, border=False):
        name = st.text_input(
            "Display name",
            placeholder="e.g. Sid Balatan",
            help=(
                "Used to label your saved runs. We turn this into a "
                "filesystem-safe user_id (lowercase, underscores)."
            ),
            key="exoq_signin_input",
        )
        submitted = st.form_submit_button("Sign in", type="primary")

    if submitted:
        uid = normalize_user_id(name)
        if not uid:
            st.warning(
                "Pick a display name with at least one letter or digit "
                "(letters, digits, underscores and hyphens are kept)."
            )
            return
        st.session_state[SESSION_KEY] = uid
        st.session_state[SESSION_DISPLAY_KEY] = name.strip()
        st.success(f"Signed in as `{uid}`. Your runs will be saved to your workspace.")
        st.rerun()


def require_user(blocking_message: str = "Please sign in via ☰ Main Menu before running.") -> Optional[str]:
    """Helper for callers that need a user_id and want to early-out otherwise.

    Returns the user_id or ``None``. If ``None``, also renders an info
    message so the caller can simply ``st.stop()`` afterwards.
    """
    uid = current_user()
    if not uid:
        st.info(blocking_message)
    return uid
