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
    """Minimal inline auth strip: text links to the Authentication page.

    * When signed out -> plain text links: "Sign in | Create an Account"
    * When signed in -> "Signed in as <name>" + Sign out button
    """
    # Keep the row horizontal and right-aligned.
    st.markdown(
        """
        <style>
            .st-key-exoq_auth div[data-testid="stHorizontalBlock"] {
                flex-direction: row !important;
                flex-wrap: nowrap !important;
                justify-content: flex-end !important;
                align-items: center !important;
                gap: 0.4rem !important;
            }
            .st-key-exoq_auth div[data-testid="stHorizontalBlock"]
                > div[data-testid="column"] {
                width: auto !important;
                flex: 0 0 auto !important;
                min-width: 0 !important;
                padding: 0 !important;
            }
            /* Make the page_link widgets look like plain text. */
            .st-key-exoq_auth a[data-testid="stPageLink-NavLink"] {
                background: transparent !important;
                border: none !important;
                box-shadow: none !important;
                padding: 0 !important;
                margin: 0 !important;
                color: #6b7280 !important;
                font-weight: 500 !important;
                font-size: 0.75rem !important;
                text-decoration: none !important;
                white-space: nowrap !important;
            }
            .st-key-exoq_auth a[data-testid="stPageLink-NavLink"]:hover {
                color: #1b5e20 !important;
                text-decoration: underline !important;
            }
            /* Pipe separator style. */
            .st-key-exoq_auth .exoq-auth-pipe {
                color: #d1d5db;
                font-size: 0.75rem;
                user-select: none;
            }
            /* Signed-in label. */
            .st-key-exoq_auth .exoq-auth-strip {
                font-size: 0.72rem;
                color: #6b7280;
                white-space: nowrap;
            }
            .st-key-exoq_auth .exoq-auth-strip b { color: #374151; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.container(key="exoq_auth"):
        uid = current_user()
        if uid:
            c_spacer, c_label, c_btn = st.columns([6, 3, 1])
            with c_label:
                display = current_display_name() or uid
                st.markdown(
                    f"<span class='exoq-auth-strip'>Signed in as <b>{display}</b></span>",
                    unsafe_allow_html=True,
                )
            with c_btn:
                if st.button("Sign out", key="exoq_signout_btn"):
                    sign_out()
                    st.rerun()
            return

        # Signed out: simple text links to the Authentication page.
        c_in, c_pipe, c_up = st.columns([1, 1, 1])
        with c_in:
            st.page_link("pages/1_Authentication.py", label="Sign in")
        with c_pipe:
            st.markdown("<span class='exoq-auth-pipe'>|</span>", unsafe_allow_html=True)
        with c_up:
            st.page_link("pages/1_Authentication.py", label="Create an Account")


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
