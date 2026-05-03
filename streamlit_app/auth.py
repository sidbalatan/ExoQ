"""
ExoQ Authentication Page

Standalone authentication page for user sign-in/sign-up.
"""

import streamlit as st
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from workspace import sign_in_widget, current_user

st.set_page_config(
    page_title="ExoQ Authentication",
    page_icon="🔐",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Hide sidebar completely
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
        .css-1d391kg {
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

# Page header
st.markdown("""
<div style="text-align: center; margin-top: 2rem; margin-bottom: 2rem;">
    <div style="font-size: 5rem; line-height: 1;">🌍</div>
    <h1 style="margin: 0.5rem 0 0 0; font-weight: 700; font-size: 2rem;">
        ExoQ Authentication
    </h1>
    <p style="color: #666; margin-top: 1rem;">
        Sign in to access your workspace and run the full pipeline
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# Sign in widget
sign_in_widget()

# After sign-in, show redirect options
if current_user():
    st.markdown("---")
    st.markdown("### Continue to:")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🏠 Go to Home Page", use_container_width=True):
            st.switch_page("Home.py")
    
    with col2:
        if st.button("📁 Go to Workspace", use_container_width=True):
            st.switch_page("pages/2_My_Workspace.py")
