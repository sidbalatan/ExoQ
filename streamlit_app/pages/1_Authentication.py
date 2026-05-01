"""ExoQ Authentication page.

Hosts the Sign in / Sign up forms in a dedicated route so the home page
can stay free of auth popovers. Linked from the topnav `Sign in` and
`Create an Account` text links via `st.page_link`.
"""

import streamlit as st

from workspace import sign_in_widget, current_user, current_display_name
from workspace.identity import sign_out

st.set_page_config(
    page_title="ExoQ - Sign in or Create an Account",
    page_icon="🔑",
    layout="centered",
)

st.markdown("# 🔑 Sign in to ExoQ")
st.caption(
    "Pick a display name to create your private workspace, or sign back "
    "in to an existing account. ExoQ uses a lightweight username-only "
    "identity so each user gets a stable folder for their saved runs."
)

st.markdown("---")

uid = current_user()
if uid:
    st.success(
        f"You are signed in as **{current_display_name() or uid}** "
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
