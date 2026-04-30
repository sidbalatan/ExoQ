"""
ExoQ - Community Quest for Earth 2.0
Landing Page
"""

import streamlit as st

st.set_page_config(
    page_title="ExoQ - Community Quest for Earth 2.0",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.title("🌍 ExoQ")
st.subheader("Community Quest for Earth 2.0")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(label="Community Members", value="1,245")
with col2:
    st.metric(label="Stars Analyzed", value="15,678")
with col3:
    st.metric(label="Exoplanet Candidates", value="342")
with col4:
    st.metric(label="Confirmed Discoveries", value="12")

st.markdown("---")

st.markdown("## Quick Demo: Experience the Quest")
st.markdown("""
Want to see the complete platform in action? Click below to run a simulated demo 
with dummy data through all stages. No login required.
""")

col_demo1, col_demo2, col_demo3 = st.columns([1, 1, 1])
with col_demo2:
    if st.button("Run Simulated Demo", type="primary", use_container_width=True):
        st.switch_page("pages/00_Simulated_Demo.py")

st.markdown("---")
st.header("What is ExoQ?")

st.markdown("""
ExoQ is a mobile-friendly web application designed for the astronomy community.
It helps researchers search for K-dwarf stars, filter candidates, generate 
TESS light curves, grade habitability, and share discoveries in our quest for Earth 2.0.
""")

st.markdown("---")
st.header("Why K Dwarfs?")

st.markdown("""
K-type dwarf stars are the most promising targets for finding Earth 2.0:

- **Long-lived** (15-30 billion years) — stable for life evolution
- **Lower luminosity** — habitable zone closer, easier to detect transits
- **Numerous** — ~75% of nearby stars are M/K dwarfs
- **Lower activity** — less harmful radiation than M dwarfs
""")

st.markdown("---")
st.header("How It Works")

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.markdown("#### 1. Register")
with col2:
    st.markdown("#### 2. Choose")
with col3:
    st.markdown("#### 3. Run")
with col4:
    st.markdown("#### 4. Save")
with col5:
    st.markdown("#### 5. Share")

st.markdown("---")

col_left, col_right = st.columns(2)
with col_left:
    st.markdown("### Ready to Start Your Quest?")
    if st.button("Register", type="primary", use_container_width=True):
        st.switch_page("pages/01_Register.py")
with col_right:
    st.markdown("### Already Have an Account?")
    if st.button("Login", use_container_width=True):
        st.switch_page("pages/01_Register.py")

st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: #888;'>"
    "ExoQ v0.1 | Built for the Astronomy Community | "
    "<a href='https://github.com/sidbalatan/ExoQ'>GitHub</a>"
    "</p>",
    unsafe_allow_html=True
)
