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
from email_validator import validate_email, EmailNotValidError

from .store import get_store, normalize_user_id, hash_password, verify_password_hash
from .email_service import generate_verification_code, send_verification_email


SESSION_KEY = "exoq_user_id"
SESSION_EMAIL_KEY = "exoq_user_email"


# ---------------------------------------------------------------------------
# Session helpers
# ---------------------------------------------------------------------------
def current_user() -> Optional[str]:
    """Return the signed-in user_id (filesystem-safe), or ``None``."""
    return st.session_state.get(SESSION_KEY)


def current_email() -> str:
    """Return the user's email address."""
    return st.session_state.get(SESSION_EMAIL_KEY, "")


def sign_out() -> None:
    """Clear the in-session identity. Per-user files are left intact on disk."""
    st.session_state.pop(SESSION_KEY, None)
    st.session_state.pop(SESSION_EMAIL_KEY, None)


def _set_session(uid: str, email: str) -> None:
    st.session_state[SESSION_KEY] = uid
    st.session_state[SESSION_EMAIL_KEY] = email


# ---------------------------------------------------------------------------
# Forms
# ---------------------------------------------------------------------------
def _sign_in_form(form_key: str = "exoq_signin_form") -> None:
    """Form: existing-account login using email and password."""
    with st.form(form_key, clear_on_submit=False, border=False):
        email = st.text_input(
            "Email",
            placeholder="you@example.com",
            key=f"{form_key}_email",
            help="The email you used when you signed up.",
        )
        password = st.text_input(
            "Password",
            type="password",
            key=f"{form_key}_password",
            help="Your account password.",
        )
        submitted = st.form_submit_button("Sign in", type="primary")

    if not submitted:
        return

    # Validate email format
    try:
        validate_email(email)
    except EmailNotValidError:
        st.error("Please enter a valid email address.")
        return

    uid = normalize_user_id(email)
    if not uid:
        st.warning("Invalid email address.")
        return

    store = get_store()
    if not store.user_exists(uid):
        st.error(
            f"No account found for `{email}`. "
            f"Use **Sign up** to create one."
        )
        return

    if not store.verify_password(uid, password):
        st.error("Incorrect password.")
        return

    # Check if email is verified
    if not store.is_email_verified(uid):
        st.error(
            f"Your email address is not verified. Please check your email for the verification code, "
            f"or sign up again to receive a new code."
        )
        return

    _set_session(uid, email)
    st.success(f"Welcome back, {email}.")
    st.rerun()


def _sign_up_form(form_key: str = "exoq_signup_form") -> None:
    """Form: brand-new account with email, password, and optional PIN."""
    # Check if we're in verification step
    if f"{form_key}_pending_email" in st.session_state:
        pending_data = st.session_state[f"{form_key}_pending_data"]
        pending_email = pending_data["email"]
        pending_uid = pending_data["uid"]
        pending_password_hash = pending_data["password_hash"]
        pending_pin = pending_data.get("pin")
        
        st.info(f"A verification code has been sent to **{pending_email}**. Please enter it below to complete your registration.")
        
        # Show error if email failed previously
        if st.session_state.get(f"{form_key}_email_failed"):
            st.error("Failed to send verification email. You can try resending below.")
        
        verification_code = st.text_input(
            "Verification Code",
            max_chars=6,
            key=f"{form_key}_verification_code",
            help="Enter the 6-digit code sent to your email.",
        )
        
        col_verify, col_cancel = st.columns([1, 1])
        with col_verify:
            if st.button("Verify", key=f"{form_key}_verify", type="primary"):
                store = get_store()
                # Check code without requiring existing user
                if store.verify_code(pending_uid, verification_code):
                    # Now create the user after verification
                    store.create_user(pending_uid, pending_email, pending_password_hash, pending_pin)
                    store.set_email_verified(pending_uid, True)
                    # Clean up pending verification file
                    store.cleanup_pending_verification(pending_uid)
                    _set_session(pending_uid, pending_email)
                    # Clear pending state
                    st.session_state.pop(f"{form_key}_pending_email", None)
                    st.session_state.pop(f"{form_key}_pending_uid", None)
                    st.session_state.pop(f"{form_key}_pending_data", None)
                    st.session_state.pop(f"{form_key}_email_failed", None)
                    st.success(
                        f"Account created for `{pending_email}`. Your runs will save to your private workspace."
                    )
                    st.rerun()
                else:
                    st.error("Invalid or expired verification code.")
        
        with col_cancel:
            if st.button("Cancel", key=f"{form_key}_cancel"):
                st.session_state.pop(f"{form_key}_pending_email", None)
                st.session_state.pop(f"{form_key}_pending_uid", None)
                st.session_state.pop(f"{form_key}_pending_data", None)
                st.session_state.pop(f"{form_key}_email_failed", None)
                st.rerun()
        
        # Resend option - always show this
        st.markdown("---")
        if st.button("Resend verification code", key=f"{form_key}_resend"):
            new_code = generate_verification_code()
            store = get_store()
            store.store_verification_code(pending_uid, new_code)
            if send_verification_email(pending_email, new_code):
                st.session_state.pop(f"{form_key}_email_failed", None)
                st.success("New verification code sent! Check your email.")
            else:
                st.session_state[f"{form_key}_email_failed"] = True
                st.error("Failed to send email. Please check your Gmail configuration.")
        
        return
    
    # Initial sign-up form
    with st.form(form_key, clear_on_submit=False, border=False):
        email = st.text_input(
            "Email",
            placeholder="you@example.com",
            key=f"{form_key}_email",
            help="Your email will be your login identifier.",
        )
        password = st.text_input(
            "Password",
            type="password",
            key=f"{form_key}_password",
            help="Choose a strong password (min 8 characters).",
        )
        confirm_password = st.text_input(
            "Confirm Password",
            type="password",
            key=f"{form_key}_confirm_password",
        )
        pin = st.text_input(
            "PIN (optional)",
            type="password",
            max_chars=6,
            key=f"{form_key}_pin",
            help="Optional 6-digit PIN for extra security.",
        )
        submitted = st.form_submit_button("Create account", type="primary")

    if not submitted:
        return

    # Validate email format
    try:
        validate_email(email)
    except EmailNotValidError:
        st.error("Please enter a valid email address.")
        return

    uid = normalize_user_id(email)
    if not uid:
        st.warning("Invalid email address.")
        return

    # Validate password
    if len(password) < 8:
        st.error("Password must be at least 8 characters.")
        return

    if password != confirm_password:
        st.error("Passwords do not match.")
        return

    # Validate PIN if provided
    if pin and (not pin.isdigit() or len(pin) != 6):
        st.error("PIN must be exactly 6 digits.")
        return

    store = get_store()
    if store.user_exists(uid):
        st.error(
            f"An account already exists for `{email}`. "
            f"Use **Sign in** instead."
        )
        return

    password_hash = hash_password(password)
    
    # Generate and store verification code (before creating user)
    verification_code = generate_verification_code()
    store = get_store()
    store.store_verification_code(uid, verification_code)
    
    # Store all pending registration data in session state
    st.session_state[f"{form_key}_pending_email"] = email
    st.session_state[f"{form_key}_pending_uid"] = uid
    st.session_state[f"{form_key}_pending_data"] = {
        "uid": uid,
        "email": email,
        "password_hash": password_hash,
        "pin": pin if pin else None
    }
    
    # Try to send verification email
    if send_verification_email(email, verification_code):
        st.success(f"Verification code sent to {email}. Please check your email.")
    else:
        st.session_state[f"{form_key}_email_failed"] = True
        st.error("Failed to send verification email. Check your Gmail configuration below, then click Resend.")
    
    st.rerun()


# ---------------------------------------------------------------------------
# Public widgets
# ---------------------------------------------------------------------------
def auth_strip() -> None:
    """Minimal inline auth strip: text links to the Authentication page.

    * When signed out -> plain text links: "Sign in | Create an Account"
    * When signed in -> "Signed in as <email>" + Sign out button
    """
    # Keep the row horizontal and right-aligned.
    st.markdown(
        """
        <style>
            .st-key-exoq_auth div[data-testid="stHorizontalBlock"] {
                flex-direction: row !important;
                flex-wrap: nowrap !important;
                justify-content: flex-start !important;
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
            email = current_email() or uid
            st.markdown(
                f"<span style='font-size: 0.75rem; color: #6b7280;'>Signed in as <b style='color: #374151;'>{email}</b></span>",
                unsafe_allow_html=True,
            )
            return

        # Signed out: single compact link.
        st.page_link("pages/1_Authentication.py", label="Sign in | Create an Account")


def sign_in_widget(*, location_label: str = "👤 Sign in") -> None:
    """Stacked Sign in / Sign up tabs. Used by the My Workspace page."""
    uid = current_user()
    if uid:
        email = current_email() or uid
        st.markdown(
            f"**{location_label}** &nbsp;·&nbsp; "
            f"signed in as `{email}` (`{uid}`)"
        )
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
