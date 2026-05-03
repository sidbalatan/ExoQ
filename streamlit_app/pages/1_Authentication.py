"""ExoQ Authentication page.

Hosts the Sign in / Sign up forms in a dedicated route so the home page
can stay free of auth popovers. Linked from the topnav `Sign in` and
`Create an Account` text links via `st.page_link`.
"""

import streamlit as st

from workspace import sign_in_widget, current_user, current_email
from workspace.identity import sign_out
from workspace.navigation import render_navigation

st.set_page_config(
    page_title="ExoQ - Sign in or Create an Account",
    page_icon="🔑",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Hide sidebar completely for mobile-first design
st.markdown(
    """
    <style>
        [data-testid="stSidebar"] {
            display: none !important;
        }
        [data-testid="collapsedControl"] {
            display: none !important;
        }
        section[data-testid="stSidebarNav"] {
            display: none !important;
        }
        button[data-testid="stMainMenu"] {
            display: none !important;
        }
        button[aria-label*="menu"],
        button[aria-label*="Menu"] {
            display: none !important;
        }
        header[data-testid="stHeader"] {
            display: none !important;
        }
        span[data-testid="stIconMaterial"] {
            display: none !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Navigation menu
render_navigation()

st.markdown("# 🔑 Sign in to ExoQ")
st.caption(
    "Enter your email and password to create your private workspace, or sign back "
    "in to an existing account. ExoQ uses email-based identity with optional PIN "
    "verification so each user gets a secure folder for their saved runs."
)

st.markdown("---")

uid = current_user()
if uid:
    email = current_email() or uid
    st.success(
        f"You are signed in as **{email}** "
        f"(`{uid}`). Your runs save to your private workspace."
    )
    col_a, col_b = st.columns([1, 3])
    with col_a:
        if st.button("Sign out", type="primary"):
            sign_out()
            st.rerun()
    with col_b:
        st.page_link("Home.py", label="← Back to Home", icon="🏠")
else:
    sign_in_widget(location_label="Sign in or Create an Account")
    st.markdown("---")
    st.page_link("Home.py", label="← Back to Home", icon="🏠")
