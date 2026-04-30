"""
ExoQ - Exoplanet Community Quest for Earth 2.0

Main app entry point. Currently hosts Module 1 (Data Input). Modules
2-8 are gated behind a members-only "Run Full Pipeline" flow.
"""

import os
import sys
import tempfile

import pandas as pd
import streamlit as st

# Make the src/ package importable.
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from modules.module1_data_input import DataInputModule  # noqa: E402

# -----------------------------------------------------------------------------
# Page config + global styling
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="ExoQ: Exoplanet Community Quest for Earth 2.0",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Fully hide the Streamlit sidebar (mobile-first design).
st.markdown(
    """
    <style>
        [data-testid="stSidebar"] { display: none !important; }
        [data-testid="stSidebarCollapsedControl"] { display: none !important; }
        [data-testid="collapsedControl"] { display: none !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🌍 ExoQ: Exoplanet Community Quest for Earth 2.0")
st.markdown("---")

# -----------------------------------------------------------------------------
# Main Menu (replaces the sidebar)
# -----------------------------------------------------------------------------
with st.popover("☰ Main Menu", use_container_width=False):
    st.markdown("#### 📚 Modules")
    st.markdown(
        "**▶ Module 1 — Data Input**  \n"
        "🔒 Module 2 — Stellar Parameters  \n"
        "🔒 Module 3 — Exoplanet Cross-Match  \n"
        "🔒 Module 4 — TESS Light Curves  \n"
        "🔒 Module 5 — Transit Detection  \n"
        "🔒 Module 6 — Habitability Scoring  \n"
        "🔒 Module 7 — Results Summary  \n"
        "🔒 Module 8 — Data Export"
    )
    st.markdown("---")
    st.button(
        "🚀 Run Full Pipeline",
        disabled=True,
        help="Members only. Unlocks after 6 months of membership OR 12 contributed posts.",
        use_container_width=True,
    )
    st.markdown("---")
    st.markdown("#### 🔗 Links")
    st.markdown("[💻 GitHub Repo](https://github.com/sidbalatan/ExoQ)")

# -----------------------------------------------------------------------------
# Module 1 — Data Input
# -----------------------------------------------------------------------------
st.subheader("📥 Module 1 — Data Input")
st.caption("Load and validate stellar coordinates for the ExoQ pipeline.")

col_left, col_right = st.columns([2, 1])
with col_left:
    data_source = st.selectbox(
        "Data source",
        ["Upload CSV", "Manual Entry"],
        help="'Upload CSV' loads coordinates from your file. 'Manual Entry' lets you type RA/Dec pairs directly.",
    )
with col_right:
    n_stars = st.slider(
        "Max stars to load",
        min_value=5, max_value=500, value=10, step=5,
        help="Caps the number of rows loaded from the uploaded CSV. Ignored for Manual Entry.",
    )

uploaded_file = None
manual_text = ""
if data_source == "Upload CSV":
    uploaded_file = st.file_uploader(
        "Upload CSV file",
        type=["csv"],
        help=(
            "CSV must contain at least 'ra' and 'dec' columns. Validated K Dwarf "
            "catalogs (with Teff, logg, RUWE, DR3Name, etc.) are auto-recognized."
        ),
    )
elif data_source == "Manual Entry":
    manual_text = st.text_area(
        "Coordinates (one per line, RA, Dec)",
        value="150.0, 10.0\n200.0, -20.0\n250.0, 30.0",
        height=150,
        help="Enter one coordinate pair per line as 'RA, Dec' in decimal degrees. Lines starting with # are ignored.",
    )

run_module1 = st.button("▶️ Run Module 1", type="primary")
st.markdown("---")

# -----------------------------------------------------------------------------
# Session state + execution
# -----------------------------------------------------------------------------
if "m1_data" not in st.session_state:
    st.session_state.m1_data = None
if "m1_summary" not in st.session_state:
    st.session_state.m1_summary = None
if "m1_validation" not in st.session_state:
    st.session_state.m1_validation = None


def _parse_manual_coordinates(text: str) -> list:
    """Parse a multi-line 'RA, Dec' text blob into a list of dicts."""
    coords = []
    for line in (text or "").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p for p in line.replace(",", " ").split() if p]
        if len(parts) < 2:
            continue
        try:
            coords.append({"ra": float(parts[0]), "dec": float(parts[1])})
        except ValueError:
            continue
    return coords


if run_module1:
    module1 = DataInputModule()
    try:
        if data_source == "Upload CSV":
            if uploaded_file is None:
                st.error("Please upload a CSV file above before running Module 1.")
                st.stop()
            # Persist upload to a temp file so the loader can read it by path.
            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name
            # Auto-detect validated K Dwarf catalogs and route to the rich loader.
            head = pd.read_csv(tmp_path, nrows=1)
            if "DR3Name" in head.columns or "validation_tier" in head.columns:
                df, validation = module1.load_real_kdwarf_catalog(
                    file_path=tmp_path,
                    n_stars=n_stars,
                    random_sample=True,
                )
            else:
                df, validation = module1.load_csv(tmp_path)
                if n_stars and len(df) > n_stars:
                    df = df.head(n_stars).reset_index(drop=True)
                    module1.data = df
        else:  # Manual Entry
            coordinates = _parse_manual_coordinates(manual_text)
            if not coordinates:
                st.error("No valid 'RA, Dec' pairs found in the manual entry box.")
                st.stop()
            df, validation = module1.load_manual_entry(coordinates)

        st.session_state.m1_data = df
        st.session_state.m1_summary = module1.get_success_summary()
        st.session_state.m1_validation = validation
    except Exception as exc:  # surface loader errors to the user
        st.error(f"Module 1 failed: {exc}")
        st.session_state.m1_data = None

# -----------------------------------------------------------------------------
# Display results
# -----------------------------------------------------------------------------
if st.session_state.m1_data is not None:
    st.success(st.session_state.m1_summary)
    df = st.session_state.m1_data
    preview_cols = [
        c for c in [
            "source_id", "gaia_dr3_name", "ra", "dec",
            "teff_gspphot", "logg_gspphot", "ruwe",
            "k_subtype", "validation_tier", "confidence",
        ] if c in df.columns
    ]
    st.dataframe(df[preview_cols].head(20), use_container_width=True)
    with st.expander("Loaded dataset details", expanded=False):
        st.write(f"**Rows:** {len(df)}")
        st.write(f"**Columns:** {len(df.columns)}")
        st.write(f"**Source:** `{st.session_state.m1_validation.get('catalog_path', 'user input')}`")
        if "filter_cuts" in (st.session_state.m1_validation or {}):
            st.write(f"**Filter cuts:** {st.session_state.m1_validation['filter_cuts']}")
    st.info("✅ Module 1 complete. Modules 2–8 unlock with membership.")
else:
    st.info(
        "👆 Configure the data source above and click **▶️ Run Module 1** "
        "to load and validate input data."
    )
