"""Lightweight identity layer for ExoQ.

Today we ship a username-only sign-in / sign-up (no password). It exists
purely to give every user a stable ``user_id`` so
:class:`workspace.store.LocalFileStore` can carve out a per-user folder.
This module is intentionally thin so we can later replace it with
``streamlit-authenticator`` or an OAuth flow without touching Module 1-8.

**No sidebar.** All widgets render inline in the page.
"""

from __future__ import annotations

from typing import Optional

import streamlit as st

from .store import get_store, normalize_user_id


SESSION_KEY = "exoq_user_id"
SESSION_DISPLAY_KEY = "exoq_user_display_name"


# ---------------------------------------------------------------------------
# Session helpers
# ---------------------------------------------------------------------------
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


def _set_session(uid: str, display_name: str) -> None:
    st.session_state[SESSION_KEY] = uid
    st.session_state[SESSION_DISPLAY_KEY] = display_name


# ---------------------------------------------------------------------------
# Forms
# ---------------------------------------------------------------------------
def _sign_in_form(form_key: str = "exoq_signin_form") -> None:
    """Form: existing-account login. Refuses unknown user_ids."""
    with st.form(form_key, clear_on_submit=False, border=False):
        name = st.text_input(
            "Display name",
            placeholder="e.g. Sid Balatan",
            key=f"{form_key}_input",
            help="The name you used when you signed up.",
        )
        submitted = st.form_submit_button("Sign in", type="primary")

    if not submitted:
        return

    uid = normalize_user_id(name)
    if not uid:
        st.warning("Pick a name with at least one letter or digit.")
        return

    store = get_store()
    if not store.user_exists(uid):
        st.error(
            f"No account found for `{uid}`. "
            f"Use **Sign up** to create one (it takes one click)."
        )
        return

    _set_session(uid, name.strip())
    st.success(f"Welcome back, {name.strip() or uid}.")
    st.rerun()


def _sign_up_form(form_key: str = "exoq_signup_form") -> None:
    """Form: brand-new account. Refuses if the user_id already exists."""
    with st.form(form_key, clear_on_submit=False, border=False):
        name = st.text_input(
            "Display name",
            placeholder="e.g. Sid Balatan",
            key=f"{form_key}_input",
            help=(
                "We turn this into a filesystem-safe user_id "
                "(lowercase, underscores, hyphens). Pick something "
                "you'll remember -- you'll use the same name to sign in."
            ),
        )
        submitted = st.form_submit_button("Create account", type="primary")

    if not submitted:
        return

    uid = normalize_user_id(name)
    if not uid:
        st.warning("Pick a name with at least one letter or digit.")
        return

    store = get_store()
    if store.user_exists(uid):
        st.error(
            f"An account already exists for `{uid}`. "
            f"Use **Sign in** instead."
        )
        return

    store.create_user(uid, display_name=name.strip())
    _set_session(uid, name.strip())
    st.success(
        f"Account created for `{uid}`. Your runs will save to your private workspace."
    )
    st.rerun()


# ---------------------------------------------------------------------------
# Public widgets
# ---------------------------------------------------------------------------
def auth_strip() -> None:
    """Compact inline auth strip designed to sit just under the page title.

    * When signed out -> tiny grey line ``Not signed in`` plus two
      popovers (**Sign in** / **Sign up**) at ~0.8rem.
    * When signed in -> ``Signed in as <name>`` plus a compact **Sign out**.
    """
    # Scoped CSS so we don't bleed into other buttons.
    st.markdown(
        """
        <style>
            .exoq-auth-strip {
                font-size: 0.6rem;
                color: #6b7280;
                margin: -0.25rem 0 0.1rem 0;
            }
            .exoq-auth-strip b { color: #374151; font-weight: 600; }
            div[data-testid="stPopover"] button[aria-haspopup="true"] {
                font-size: 0.6rem !important;
                padding: 0.05rem 0.5rem !important;
                min-height: 0 !important;
                line-height: 1.1 !important;
            }
            /* Tighten the columns so the two popovers sit shoulder-to-shoulder */
            .exoq-auth-row [data-testid="column"] { padding: 0 0.1rem !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    uid = current_user()
    if uid:
        c1, c2 = st.columns([6, 1])
        with c1:
            display = current_display_name() or uid
            st.markdown(
                f"<div class='exoq-auth-strip' style='text-align:right;padding-top:0.4rem;'>"
                f"Signed in as <b>{display}</b> &nbsp;·&nbsp;"
                f"<code style='font-size:0.55rem'>{uid}</code></div>",
                unsafe_allow_html=True,
            )
        with c2:
            if st.button("Sign out", key="exoq_signout_btn"):
                sign_out()
                st.rerun()
        return

    # Signed out: two compact popovers, side by side, centered.
    st.markdown('<div class="exoq-auth-row">', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns([5, 1, 1, 5])
    with c2:
        with st.popover("Sign in", use_container_width=True):
            st.markdown("**Sign in to ExoQ**")
            _sign_in_form("exoq_signin_strip")
    with c3:
        with st.popover("Sign up", use_container_width=True):
            st.markdown("**Create your ExoQ account**")
            _sign_up_form("exoq_signup_strip")
    st.markdown("</div>", unsafe_allow_html=True)


def sign_in_widget(*, location_label: str = "👤 Sign in") -> None:
    """Stacked Sign in / Sign up tabs. Used by the My Workspace page."""
    uid = current_user()
    if uid:
        st.markdown(
            f"**{location_label}** &nbsp;·&nbsp; "
            f"signed in as `{current_display_name() or uid}` (`{uid}`)"
        )
        if st.button("Sign out", key="exoq_signout_btn_legacy"):
            sign_out()
            st.rerun()
        return

    st.markdown(f"**{location_label}**")
    tab_in, tab_up = st.tabs(["Sign in", "Sign up"])
    with tab_in:
        _sign_in_form("exoq_signin_legacy")
    with tab_up:
        _sign_up_form("exoq_signup_legacy")


def require_user(blocking_message: str = "Please sign in or sign up before running.") -> Optional[str]:
    uid = current_user()
    if not uid:
        st.info(blocking_message)
    return uid
