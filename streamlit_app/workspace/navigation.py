"""
Navigation component for ExoQ
Provides a permanent navigation menu accessible from any page.
"""

import streamlit as st


def render_navigation():
    """Render a navigation menu that can be added to any page."""
    
    # Make the expander more prominent with CSS
    st.markdown("""
    <style>
    div[data-testid="stExpander"] {
        border: 2px solid #1b5e20 !important;
        border-radius: 10px !important;
        background-color: #f8f9fa !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    with st.expander("📱 ☰ MENU - Click to Open", expanded=False):
        st.markdown("### 📚 Modules")
        if st.button("🏠 Home", key="nav_home", use_container_width=True):
            st.session_state.pipeline_step = 0
            st.rerun()
        if st.button("📘 Module 1: Introduction", key="nav_mod1", use_container_width=True):
            st.session_state.pipeline_step = 1
            st.rerun()
        if st.button("📗 Module 2: Star Selection", key="nav_mod2", use_container_width=True):
            st.session_state.pipeline_step = 2
            st.rerun()
        if st.button("📙 Module 3: Light Curve Analysis", key="nav_mod3", use_container_width=True):
            st.session_state.pipeline_step = 3
            st.rerun()
        if st.button("📕 Module 4: Planet Detection", key="nav_mod4", use_container_width=True):
            st.session_state.pipeline_step = 4
            st.rerun()
        if st.button("📓 Module 5: Planet Characterization", key="nav_mod5", use_container_width=True):
            st.session_state.pipeline_step = 5
            st.rerun()
        if st.button("📒 Module 6: Habitability", key="nav_mod6", use_container_width=True):
            st.session_state.pipeline_step = 6
            st.rerun()
        if st.button("📔 Module 7: Discovery", key="nav_mod7", use_container_width=True):
            st.session_state.pipeline_step = 7
            st.rerun()
        
        st.markdown("---")
        
        # Resume Game button - only show if there are unanalyzed stars
        if st.session_state.get("analyzed_stars") and st.session_state.get("stars"):
            unanalyzed_count = len(st.session_state.stars) - len(st.session_state.analyzed_stars)
            if unanalyzed_count > 0:
                st.markdown("### 🎮 Quick Resume")
                if st.button(f"Resume Game ({unanalyzed_count} stars left)", key="nav_resume_game", use_container_width=True, type="primary"):
                    # Find next unanalyzed star
                    for star in st.session_state.stars:
                        if star["source_id"] not in st.session_state.analyzed_stars:
                            st.session_state.selected_source_id = star["source_id"]
                            st.session_state.selected_star = star
                            st.session_state.pipeline_step = 3  # Go to Module 3 (Light Curve)
                            st.rerun()
                            break
