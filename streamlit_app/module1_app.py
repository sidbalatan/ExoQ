#!/usr/bin/env python
# coding: utf-8

import streamlit as st
import pandas as pd
import numpy as np
import sys
import os
import tempfile
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

st.set_page_config(
    page_title="Module 1: Data Input and Gaia Survival Test",
    page_icon="📥",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Load CSS
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

local_css("streamlit_app/static/style.css")

# Import module logic
from modules.module1_data_input import DataInputModule
from modules.integrity_tracker import IntegrityTracker

from workspace import current_user, get_store
from workspace.store import normalize_user_id, RunMeta, RunRecord, new_run_id
from identifier_resolver import parse_manual_input
from gaia_enricher import enrich_rows
from certificate import render_certificate

# Page header - matching Home.py layout
st.markdown("##### 📥 Module 1 of 8 - Data Input and Gaia Survival Test")
st.markdown(
    "**The starting line of your quest for Earth 2.0.**  \n"
    "Hand the pipeline a list of sky coordinates — upload a CSV or type "
    "RA/Dec pairs by hand."
)

with st.expander("READ MORE: The Input Process . . ."):
    st.markdown(
        "Module 1 accepts any CSV with `ra` and `dec` columns. Validated K Dwarf "
        "catalogs (those with `DR3Name`, `Teff`, `logg`, `RUWE`, etc.) are "
        "auto-recognized and routed through the rich loader. Manual Entry lets "
        "you type RA/Dec pairs by hand for quick spot checks.\n\n"
        "After ingest, Module 1 sanity-checks coordinate ranges, deduplicates "
        "by source ID where available, standardizes column names, and prepares "
        "the batch for the **Gaia DR3 Survival Test** below. "
        "Only the stars that survive move on to Modules 2–8."
    )

st.caption(
    "Type RA/Dec pairs or catalog IDs below — or use the **📂 Upload CSV** widget on the right. "
    "Accepts: **RA / Dec** *(required)*, **Gaia DR3 IDs**, **TIC IDs**, "
    "**KIC / EPIC IDs**, **2MASS / Spitzer IDs**. Extra columns "
    "(Teff, logg, RUWE, photometry, …) are auto-recognized."
)

# Two-column layout matching Home.py
input_left, input_right = st.columns([3, 2])
with input_left:
    manual_text = st.text_area(
        "Coordinates or Identifiers",
        value=(
            "150.0, 10.0\n"
            "Gaia DR3 4271989156548409344\n"
            "TIC 261136679\n"
            "HD 209458\n"
            "2MASS J05551028+2351124"
        ),
        height=170,
        help=(
            "One entry per line. Each line can be:\n"
            "• 'RA, Dec' in decimal degrees (e.g. 150.0, 10.0)\n"
            "• Gaia DR3 source_id (e.g. 'Gaia DR3 4271989156548409344' or just the number)\n"
            "• TIC, KIC, EPIC, 2MASS, HD, HIP, TYC ID, or a common name\n"
            "Identifiers are resolved to RA/Dec via Simbad (with a MAST TIC fallback).\n"
            "Lines starting with # are ignored."
        ),
    )
    if st.button(
        "📋 Validate & Preview Identifiers",
        key="m1_validate_btn",
        type="primary",
    ):
        st.session_state["m1_show_manual_preview"] = True
    st.caption(
        "ℹ️ The lines above are samples. **Delete them and paste in your own** "
        "RA/Dec pairs *or* catalog IDs (Gaia DR3 / TIC / KIC / EPIC / 2MASS / HD / HIP / TYC) "
        "before clicking *Run Module 1*."
    )
    if st.session_state.get("m1_show_manual_preview"):
        with st.spinner("Resolving identifiers via Simbad / MAST …"):
            preview_rows, preview_unresolved = parse_manual_input(manual_text)
        if preview_rows:
            n_resolved = sum(1 for r in preview_rows if r.get("identifier"))
            n_numeric = len(preview_rows) - n_resolved
            st.info(
                f"📋 {len(preview_rows)} entries ready — "
                f"{n_resolved} resolved from identifiers, {n_numeric} numeric RA/Dec."
            )
            st.dataframe(
                pd.DataFrame(preview_rows)[["identifier", "resolved_label", "ra", "dec"]]
                  .rename(columns={"resolved_label": "resolved as"}),
                use_container_width=True,
                height=min(35 + 35 * len(preview_rows), 250),
            )
            st.markdown(
                "<p style='font-size: 0.85rem; font-weight: 600; margin: 0.25rem 0;'>"
                "👇 CLICK THE RUN GAIA SURVIVAL TEST BUTTON LOCATED BELOW"
                "</p>",
                unsafe_allow_html=True,
            )
        if preview_unresolved:
            st.warning(
                "Could not resolve **" + str(len(preview_unresolved)) + "** line(s): "
                + ", ".join(f"`{u}`" for u in preview_unresolved[:6])
                + (" …" if len(preview_unresolved) > 6 else "")
            )
        if not preview_rows and not preview_unresolved:
            st.info("Nothing to preview yet — paste some entries into the textarea above.")
with input_right:
    uploaded_file = st.file_uploader(
        "📂 Upload CSV (overrides manual entry)",
        type=["csv"],
        help=(
            "Upload a CSV instead of typing. Must contain at least 'ra' and 'dec' "
            "columns. Validated K Dwarf catalogs (with Teff, logg, RUWE, DR3Name, etc.) "
            "are auto-recognized. When a file is uploaded it overrides the manual entry."
        ),
    )

n_stars = st.slider(
    "Max stars to load (CSV only)",
    min_value=5, max_value=500, value=10, step=5,
    help="Caps the number of rows loaded from the uploaded CSV. Ignored for manual entry.",
)

# Default catalog sampling to random; user-facing toggle removed.
random_sample = True

# Auto-pick the active data source: a non-empty file uploader wins over manual text.
data_source = "Upload CSV" if uploaded_file is not None else "Manual Entry"
if uploaded_file is not None:
    # Peek at the upload so the user sees the table before pressing Run.
    try:
        uploaded_file.seek(0)
        preview_df = pd.read_csv(uploaded_file)
        uploaded_file.seek(0)  # rewind so the run handler can re-read it later
    except Exception as exc:
        preview_df = None
        st.error(f"❌ Could not parse `{uploaded_file.name}` as a CSV: {exc}")

    if preview_df is not None:
        rows, cols = preview_df.shape
        has_ra = any(c.lower() == "ra" for c in preview_df.columns)
        has_dec = any(c.lower() == "dec" for c in preview_df.columns)
        validated_markers = [
            c for c in preview_df.columns
            if c in ("DR3Name", "Teff", "logg", "RUWE", "validation_tier", "k_subtype")
        ]

        if has_ra and has_dec:
            st.success(
                f"✅ Loaded **{uploaded_file.name}** — **{rows:,}** rows × **{cols}** columns. "
                f"Required `ra` and `dec` columns detected. **Ready to run.**"
            )
        else:
            st.error(
                f"⚠️ Loaded **{uploaded_file.name}** ({rows:,}×{cols}) but the required "
                f"`ra` and/or `dec` columns are missing. Module 1 will fail until those are present."
            )

        if validated_markers:
            st.caption(
                "🔬 Validated K Dwarf catalog detected — extra columns recognized: "
                + ", ".join(f"`{c}`" for c in validated_markers)
            )

        with st.expander(f"📋 Preview — first {min(20, rows)} rows", expanded=True):
            st.dataframe(preview_df.head(20), use_container_width=True)

        st.caption(
            f"Manual text above is ignored while a CSV is loaded. "
            f"At most **{n_stars}** of the **{rows:,}** rows will feed the pipeline "
            f"(adjust with the slider above)."
        )

# Modules 2-8 default to mock data while they remain gated behind the
# members-only Run Full Pipeline. No user-facing toggle is needed.
use_mock = True

st.markdown(
    "**🧬 The Gaia DR3 Survival Test.**  \n"
    "Your coordinates are pushed against **ESA Gaia DR3** and forced through a gauntlet of "
    "quality filters. Only the fittest stars — the **🌱 Survivors** — move on to Modules 2–8."
)
with st.expander("About the GAIA DR3 Filters in Isolating K Dwarfs . . ."):
    st.markdown(
        "ESA Gaia DR3 is the most precise stellar census ever made — *1.8 billion stars*. "
        "Just like life on Earth 1.0, only the fittest survive. The K Dwarfs that pass every "
        "cut become **Survivors**, the ones worth pursuing in our quest for **Earth 2.0**."
    )

    st.markdown("##### 🛡️ Survival criteria")
    crit_left, crit_right = st.columns(2)
    with crit_left:
        st.markdown(
            "- **Effective temperature** — *Teff*  \n"
            "  &nbsp;&nbsp;`3,900 K ≤ Teff ≤ 5,300 K`  \n"
            "  *Goldilocks zone for K-type stars: not too hot (G), not too cold (M).*\n"
            "\n"
            "- **Surface gravity** — *log g*  \n"
            "  &nbsp;&nbsp;`log g ≥ 4.0`  \n"
            "  *Compact dwarfs only — bloated red giants are ejected.*\n"
            "\n"
            "- **Astrometric quality** — *RUWE*  \n"
            "  &nbsp;&nbsp;`RUWE < 1.4`  \n"
            "  *Clean single-star solution; suspected unresolved binaries fail.*"
        )
    with crit_right:
        st.markdown(
            "- **Color index** — *BP − RP*  \n"
            "  &nbsp;&nbsp;`1.1 ≤ BP − RP ≤ 2.6`  \n"
            "  *The orange-red glow of a true K Dwarf.*\n"
            "\n"
            "- **Distance** — *parallax-based*  \n"
            "  &nbsp;&nbsp;`Plx > 0`, finite  \n"
            "  *Must have a real, measurable distance.*\n"
            "\n"
            "- **Cleanliness flags** — *contaminants out*  \n"
            "  &nbsp;&nbsp;`flag_giant = False`  \n"
            "  &nbsp;&nbsp;`flag_mdwarf = False`  \n"
            "  *Known giants and M dwarfs are filtered out.*"
        )

st.markdown("---")

# Run Module 1 button
col1, col2 = st.columns([1, 3])
with col1:
    run_module = st.button("▶️ Run Gaia DR3 Survival Test", type="primary", key="run_module_1")
with col2:
    st.caption("Load and validate input data through Gaia DR3 Survival Test")

# Module execution
if run_module:
    module1 = DataInputModule()
    tracker = IntegrityTracker()
    
    if data_source == "Upload CSV":
        if uploaded_file is None:
            st.error("Please upload a CSV file before running Module 1.")
            st.stop()
        
        # Persist upload to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = tmp.name
        
        # Load CSV
        head = pd.read_csv(tmp_path, nrows=1)
        if "DR3Name" in head.columns or "validation_tier" in head.columns:
            df, validation = module1.load_real_kdwarf_catalog(
                file_path=tmp_path,
                n_stars=n_stars,
                random_sample=random_sample,
            )
        else:
            df, validation = module1.load_csv(tmp_path)
            if n_stars and len(df) > n_stars:
                df = df.head(n_stars).reset_index(drop=True)
                module1.data = df
    else:
        # Manual entry
        with st.spinner("Resolving identifiers via Simbad / MAST …"):
            rows, unresolved = parse_manual_input(manual_text)
        
        if unresolved:
            st.warning(
                f"Could not resolve {len(unresolved)} line(s): "
                + ", ".join(f"`{u}`" for u in unresolved[:6])
                + (" …" if len(unresolved) > 6 else "")
            )
        
        if not rows:
            st.error(
                "No valid coordinates or identifiers found. "
                "Each line must be 'RA, Dec' in decimal degrees "
                "or a catalog ID (Gaia DR3 / TIC / KIC / EPIC / 2MASS / HD / HIP / TYC)."
            )
            st.stop()
        
        coordinates = [{"ra": r["ra"], "dec": r["dec"]} for r in rows]
        df, validation = module1.load_manual_entry(coordinates)
        
        # Gaia DR3 enrichment
        progress_bar = st.progress(0.0, text="Cross-matching against live Gaia DR3 …")
        
        def _on_gaia_progress(done, total, msg):
            pct = min(done / max(total, 1), 1.0)
            progress_bar.progress(pct, text=msg)
        
        enriched = enrich_rows(rows, progress_cb=_on_gaia_progress)
        progress_bar.empty()
        
        if len(enriched) == len(df):
            enriched = enriched.reset_index(drop=True)
            df = df.reset_index(drop=True)
            for col in [
                "ra", "dec", "parallax", "ruwe",
                "phot_g_mean_mag", "bp_rp",
                "teff_gspphot", "logg_gspphot",
                "gaia_match_arcsec", "gaia_dr3_name", "identifier",
            ]:
                if col in enriched.columns:
                    df[col] = enriched[col]
            if "source_id" in enriched.columns:
                real_sid = enriched["source_id"]
                if "source_id" in df.columns:
                    df["source_id"] = real_sid.where(real_sid.notna(), df["source_id"])
                else:
                    df["source_id"] = real_sid
            module1.data = df
    
    # Initialize integrity tracking
    df = tracker.initialize_integrity_columns(df)
    
    # Mark as Module 1 complete ONLY for rows with valid Gaia DR3 data
    # Check if key survival criteria columns have valid (non-NaN) values
    survival_criteria_cols = ['teff_gspphot', 'logg_gspphot', 'ruwe', 'bp_rp', 'parallax']
    has_gaia_data = df[survival_criteria_cols].notna().all(axis=1)
    
    # Only mark rows with Gaia data as survived
    df['module1_passed'] = has_gaia_data
    df.loc[has_gaia_data, 'module1_timestamp'] = pd.Timestamp.now().isoformat()
    
    # Display results
    st.markdown("---")
    st.markdown("### 🎯 Results")
    
    # Data source indicator
    if data_source == "Upload CSV" and preview_df is not None:
        if validated_markers:
            st.info("📊 **Data Source:** Validated K Dwarf catalog (CSV upload)")
            st.caption("✅ Stars already classified as K Dwarfs with Teff, logg, RUWE data from catalog")
        else:
            st.info("📊 **Data Source:** CSV upload with RA/Dec coordinates")
            st.caption("🔬 **Live Gaia DR3 data:** Cross-matched against ESA Gaia DR3 for stellar parameters")
    else:
        st.info("📊 **Data Source:** Manual entry")
        st.caption("🔬 **Live Gaia DR3 data:** Cross-matched against ESA Gaia DR3 for stellar parameters")
    
    # Survival status
    st.markdown("---")
    st.markdown("#### 🛡️ Gaia DR3 Survival Test Results")
    
    survivors = len(df[df['module1_passed'] == True])
    total = len(df)
    
    if survivors == total:
        st.success(f"✅ **All {total} coordinates survived the Gaia DR3 Survival Test**")
        st.caption("These stars passed all quality filters and are considered **K Dwarf candidates**")
    else:
        st.warning(f"⚠️ **{survivors} of {total} coordinates survived** ({survivors/total:.1%})")
        st.caption(f"{total - survivors} stars failed one or more quality filters")
    
    # Filter details - shown in table instead of expander
    st.markdown("""
    **Survival criteria applied to the table below:**
    - Effective temperature (Teff): 3,900 K ≤ Teff ≤ 5,300 K
    - Surface gravity (log g): log g ≥ 4.0
    - Astrometric quality (RUWE): RUWE < 1.4
    - Color index (BP − RP): 1.1 ≤ BP − RP ≤ 2.6
    - Distance: Parallax > 0 (real, measurable distance)
    - Cleanliness flags: Not flagged as giant or M dwarf
    
    **Note:** Surviving stars are **K Dwarf candidates** - they passed the initial quality filters
    but will undergo further refinement in subsequent modules.
    """)
    
    st.markdown("---")
    st.subheader("📋 Surviving Stars Data Table")
    st.caption("🔬 **Live Data:** Stellar parameters from ESA Gaia DR3 | Survival criteria columns highlighted")
    
    # Reorder columns to show survival criteria prominently
    # Define column order: Survived status first -> gaia_dr3_name -> identifiers -> survival criteria -> other columns
    survival_criteria_cols = ['teff_gspphot', 'logg_gspphot', 'ruwe', 'bp_rp', 'parallax', 'flag_giant', 'flag_mdwarf']
    identifier_cols = ['module1_passed', 'gaia_dr3_name', 'ra', 'dec', 'source_id']
    status_cols = ['module1_timestamp']
    
    # Get all columns
    all_cols = list(df.columns)
    
    # Build ordered column list
    ordered_cols = []
    for col in identifier_cols:
        if col in all_cols:
            ordered_cols.append(col)
    for col in survival_criteria_cols:
        if col in all_cols:
            ordered_cols.append(col)
    for col in status_cols:
        if col in all_cols:
            ordered_cols.append(col)
    
    # Add remaining columns not in the above lists
    for col in all_cols:
        if col not in ordered_cols:
            ordered_cols.append(col)
    
    # Reorder dataframe
    df_display = df[ordered_cols]
    
    # Reset index to start at 1 instead of 0 for user-friendly counting
    df_display = df_display.reset_index(drop=True)
    df_display.index = df_display.index + 1
    
    # Rename columns to show survival criteria ranges
    column_rename_map = {
        'teff_gspphot': 'Teff [3,900-5,300 K]',
        'logg_gspphot': 'log g [≥ 4.0]',
        'ruwe': 'RUWE [< 1.4]',
        'bp_rp': 'BP-RP [1.1-2.6]',
        'parallax': 'Parallax [> 0 mas]',
        'flag_giant': 'Giant flag',
        'flag_mdwarf': 'M dwarf flag',
        'module1_passed': '✅ Survived',
        'module1_timestamp': 'Timestamp'
    }
    df_display = df_display.rename(columns=column_rename_map)
    
    # Apply styling using pandas Styler
    def highlight_survived_row(row):
        """Apply orange font color to entire row if survived."""
        # Check if this row survived
        survived = row.get('✅ Survived', False)
        if pd.isna(survived):
            survived = False
        if survived == True or survived == 'True':
            return ['color: #FF8C00; font-weight: bold;' for _ in row]
        else:
            return ['' for _ in row]
    
    def highlight_survived_status(val):
        """Highlight survived status: orange for True, red for False."""
        if pd.isna(val):
            return ''
        if val == True or val == 'True':
            return 'color: #FF8C00; font-weight: bold;'
        else:
            return 'color: #AA0000; font-weight: bold;'
    
    # Create styler
    survival_criteria_display_names = [
        'Teff [3,900-5,300 K]',
        'log g [≥ 4.0]',
        'RUWE [< 1.4]',
        'BP-RP [1.1-2.6]',
        'Parallax [> 0 mas]',
        'Giant flag',
        'M dwarf flag'
    ]
    
    identifier_display_names = [
        'gaia_dr3_name',
        'ra',
        'dec'
    ]
    
    styler = df_display.head(20).style
    
    # Apply orange font color to entire row if survived
    styler = styler.apply(highlight_survived_row, axis=1)
    
    # Apply green/red to Survived column (overrides orange for True/False)
    if '✅ Survived' in df_display.columns:
        styler = styler.map(highlight_survived_status, subset=['✅ Survived'])
    
    st.dataframe(styler, width='stretch')

# Generate and display K Dwarf Certificate
if run_module and survivors > 0:
    st.markdown("---")
    st.markdown("### 🏆 K Dwarf Certificate")
    
    # Calculate tier breakdown
    gold = survivors  # All survivors are gold tier for now
    silver = 0  # Silver tier not implemented yet
    failed = total - survivors
    
    # Get sample source IDs from survivors
    survivor_df = df[df['module1_passed'] == True]
    sample_ids = survivor_df['source_id'].dropna().head(5).tolist() if 'source_id' in survivor_df.columns else []
    
    # Get user display name
    user = current_user()
    display_name = user if user else "ExoQ Pioneer"
    
    # Generate run ID
    run_id = new_run_id()[:8]  # Short version for display
    
    # Render certificate
    cert_png = render_certificate(
        display_name=display_name,
        survivors_count=survivors,
        inputs_count=total,
        gold=gold,
        silver=silver,
        failed=failed,
        sample_source_ids=sample_ids,
        run_id=run_id,
    )
    
    # Display certificate
    st.image(cert_png, width=800)
    
    # Download button
    st.download_button(
        label="📥 Download Certificate",
        data=cert_png,
        file_name=f"exoq_certificate_{run_id}.png",
        mime="image/png",
        type="primary",
    )

# Save to workspace
if run_module:
    st.markdown("---")
    st.markdown("### Save to Workspace")
    
    user = current_user()
    if user:
        dataset_name = st.text_input(
            "Dataset name",
            value=f"module1_results_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}"
        )
        
        if st.button("💾 Save to Workspace"):
            try:
                # Save to workspace
                store = get_store()
                uid = normalize_user_id(user)
                
                # Create workspace directory if needed
                workspace_dir = os.path.join("data", "users", uid)
                os.makedirs(workspace_dir, exist_ok=True)
                
                # Save CSV
                file_path = os.path.join(workspace_dir, f"{dataset_name}.csv")
                df.to_csv(file_path, index=False)
                
                st.success(f"Saved {len(df)} coordinates to workspace as '{dataset_name}.csv'")
            except Exception as exc:
                st.error(f"Failed to save: {exc}")
    else:
        st.caption("Sign in to save your results to workspace.")

# Navigation
st.markdown("---")
st.markdown("### Next Steps")

col1, col2 = st.columns(2)
with col1:
    if st.button("🪐 Go to Module 2", key="go_to_module_2"):
        st.info("Opening Module 2: Start Exoplanet Quest...")
        # TODO: Link to module2_exoplanet_crossmatch.ipynb
with col2:
    if st.button("🏠 Return to Navigation Hub", key="return_to_hub"):
        st.info("Returning to Navigation Hub...")
        # TODO: Link to Home.ipynb
