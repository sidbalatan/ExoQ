"""
ExoQ - Exoplanet Community Quest for Earth 2.0

Main app entry point. Hosts the full 8-module pipeline. Module 1 is
free; Modules 2-8 are gated behind the members-only Run Full Pipeline.
"""

import streamlit as st
import pandas as pd
import numpy as np
import sys
import os
from identifier_resolver import parse_manual_input

# Add src to path for module imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from modules.module1_data_input import DataInputModule
from modules.module2_stellar_parameters import StellarParameterModule
from modules.module3_exoplanet_crossmatch import ExoplanetCrossMatchModule
from modules.module4_tess_lightcurves import TESSLightCurveModule
from modules.module5_transit_detection import TransitDetectionModule
from modules.module6_habitability_scoring import HabitabilityScoringModule
from modules.module7_results_summary import ResultsSummaryModule
from modules.module8_data_export import DataExportModule

st.set_page_config(
    page_title="ExoQ: Exoplanet Community Quest for Earth 2.0",
    page_icon="🌍",
    layout="wide",
)

st.markdown(
    """
    <div style="text-align: center; margin-top: 0.5rem; margin-bottom: 1rem;">
        <div style="font-size: 4rem; line-height: 1;">🌍</div>
        <h1 style="margin: 0.25rem 0 0 0; font-weight: 700; font-size: 1.5rem;">
            ExoQ: Exoplanet Community<br>Quest for Earth 2.0
        </h1>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown("---")

# Style primary buttons (Run Module 1) in dark green.
st.markdown(
    """
    <style>
        button[kind="primary"],
        [data-testid="baseButton-primary"],
        [data-testid="stBaseButton-primary"] {
            background-color: #1b5e20 !important;
            border-color: #1b5e20 !important;
            color: #ffffff !important;
        }
        button[kind="primary"]:hover,
        [data-testid="baseButton-primary"]:hover,
        [data-testid="stBaseButton-primary"]:hover {
            background-color: #2e7d32 !important;
            border-color: #2e7d32 !important;
            color: #ffffff !important;
        }
        button[kind="primary"]:focus:not(:active),
        [data-testid="baseButton-primary"]:focus:not(:active),
        [data-testid="stBaseButton-primary"]:focus:not(:active) {
            background-color: #1b5e20 !important;
            border-color: #1b5e20 !important;
            color: #ffffff !important;
            box-shadow: 0 0 0 0.2rem rgba(46, 125, 50, 0.35) !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Main Menu (mobile-first dropdown navigation) ----------------------------
with st.popover("☰ Main Menu", use_container_width=False):
    st.markdown("#### 📚 Modules")
    st.markdown(
        "**▶ Module 1 of 8 - Data Input**  \n"
        "🔒 Module 2 of 8 - Stellar Parameters  \n"
        "🔒 Module 3 of 8 - Exoplanet Cross-Match  \n"
        "🔒 Module 4 of 8 - TESS Light Curves  \n"
        "🔒 Module 5 of 8 - Transit Detection  \n"
        "🔒 Module 6 of 8 - Habitability Scoring  \n"
        "🔒 Module 7 of 8 - Results Summary  \n"
        "🔒 Module 8 of 8 - Data Export"
    )
    st.markdown("---")
    run_pipeline = st.button(
        "🚀 Run Full Pipeline",
        disabled=True,
        help="Members only. Unlocks after 6 months of membership OR 12 contributed posts.",
        use_container_width=True,
    )
    st.markdown("---")
    st.markdown("#### 🔗 Links")
    st.markdown("[💻 GitHub Repo](https://github.com/sidbalatan/ExoQ)")

# --- Main page: Module 1 input controls --------------------------------------
st.markdown("##### 📥 Module 1 of 8 - Data Input")
st.markdown(
    "**The starting line of your quest for Earth 2.0.**  \n"
    "Hand the pipeline a list of sky coordinates — upload a CSV or type "
    "RA/Dec pairs by hand."
)
with st.expander("Read more"):
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
    "Type RA/Dec pairs below — or click the 📂 icon on the right to upload a CSV. "
    "Accepts: **RA / Dec** *(required)*, **Gaia DR3 IDs**, **TIC IDs**, "
    "**KIC / EPIC IDs**, **2MASS / Spitzer IDs**. Extra columns "
    "(Teff, logg, RUWE, photometry, …) are auto-recognized."
)

input_left, input_right = st.columns([5, 1])
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
    st.caption(
        "ℹ️ The lines above are samples. **Delete them and paste in your own** "
        "RA/Dec pairs *or* catalog IDs (Gaia DR3 / TIC / KIC / EPIC / 2MASS / HD / HIP / TYC) "
        "before clicking *Run Module 1*."
    )
with input_right:
    st.markdown("<div style='height: 1.85rem'></div>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "📂 Upload CSV",
        type=["csv"],
        label_visibility="visible",
        help=(
            "Upload a CSV instead of typing. Must contain at least 'ra' and 'dec' "
            "columns. Validated K Dwarf catalogs (with Teff, logg, RUWE, DR3Name, etc.) "
            "are auto-recognized. When a file is uploaded it overrides the manual entry above."
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
with st.expander("Read more"):
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
            "  &nbsp;&nbsp;`contaminant = False`"
        )

    st.markdown(
        "##### 🏷️ Validation tiers\n"
        "Each star is stamped with a confidence tier based on how cleanly it cleared the gauntlet:\n"
        "- 🥇 **Gaia Certified K Dwarf** — passed every cut with margin to spare\n"
        "- 🥈 **Need Follow Up** — passed with minor borderline values; worth a second look\n"
        "- 🥉 **Failed** — did not meet the K-Dwarf criteria"
    )
    st.caption(
        "When this run finishes, you'll see how many of your input stars made it through the gauntlet — "
        "the **Survivors** — along with their Gaia DR3 IDs, K subtype, and validation tier. "
        "Only Survivors continue to Modules 2–8."
    )

run_module1 = st.button("▶️ Run Module 1 — Begin GAIA Survival Test", type="primary")
st.markdown("---")

# Initialize session state
if 'pipeline_data' not in st.session_state:
    st.session_state.pipeline_data = None
if 'pipeline_step' not in st.session_state:
    st.session_state.pipeline_step = 0
if 'pipeline_started' not in st.session_state:
    st.session_state.pipeline_started = False
if 'm1_only' not in st.session_state:
    st.session_state.m1_only = False
if 'summaries' not in st.session_state:
    st.session_state.summaries = {}

if run_module1:
    st.session_state.pipeline_step = 0
    st.session_state.pipeline_started = True
    st.session_state.m1_only = True
    st.session_state.pipeline_data = None
    st.session_state.summaries = {}
    st.rerun()

if run_pipeline:
    st.session_state.pipeline_step = 0
    st.session_state.pipeline_started = True
    st.session_state.m1_only = False
    st.session_state.pipeline_data = None
    st.session_state.summaries = {}
    st.rerun()

# Show instruction if pipeline hasn't started
if not st.session_state.pipeline_started:
    st.info("👆 Configure the data source above and click **▶️ Run Module 1** to load and validate input data.")

# Only run modules if pipeline has been started
if st.session_state.pipeline_started and st.session_state.pipeline_step >= 0:
    # Module 1: Data Input
    with st.expander("📥 Module 1 of 8 - Data Input", expanded=True):
        if st.session_state.pipeline_step == 0:
            st.info("Loading coordinates...")
            
            module1 = DataInputModule()
            
            if data_source == "Upload CSV":
                if uploaded_file is None:
                    st.error("Please upload a CSV file above before running Module 1.")
                    st.stop()
                # Persist the upload to a temp file so the loader can read it by path.
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
                    tmp.write(uploaded_file.getvalue())
                    tmp_path = tmp.name
                # If the uploaded file looks like a validated K Dwarf catalog, use
                # the rich catalog loader; otherwise fall back to generic load_csv.
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
            else:  # Manual Entry
                with st.spinner("Resolving identifiers via Simbad / MAST …"):
                    rows, unresolved = parse_manual_input(manual_text)
                if unresolved:
                    st.warning(
                        "Could not resolve **" + str(len(unresolved)) + "** line(s): "
                        + ", ".join(f"`{u}`" for u in unresolved[:6])
                        + (" …" if len(unresolved) > 6 else "")
                    )
                if not rows:
                    st.error(
                        "No valid coordinates or recognizable identifiers found in the "
                        "manual entry box. Each line must be 'RA, Dec' in decimal degrees "
                        "or a catalog ID (Gaia DR3 / TIC / KIC / EPIC / 2MASS / HD / HIP / TYC)."
                    )
                    st.stop()
                resolved_count = sum(1 for r in rows if r.get("identifier"))
                st.info(
                    f"Parsed **{len(rows)}** entries — "
                    f"{resolved_count} resolved from identifiers, "
                    f"{len(rows) - resolved_count} numeric RA/Dec."
                )
                coordinates = [{"ra": r["ra"], "dec": r["dec"]} for r in rows]
                input_count = len(coordinates)
                df, validation = module1.load_manual_entry(coordinates)

            # Capture the survivor headline numbers for the celebration block.
            survivor_count = int(len(df))
            if data_source == "Upload CSV" and 'preview_df' in dir() and preview_df is not None:
                # For CSV the effective input is the slider-capped row count.
                input_count = min(int(preview_df.shape[0]), int(n_stars))
            elif data_source != "Upload CSV":
                # Manual entry: input_count was set just above.
                pass
            else:
                input_count = survivor_count
            st.session_state.m1_input_count = input_count
            st.session_state.m1_survivor_count = survivor_count
            st.session_state.m1_celebrated = False  # trigger balloons on next render

            summary = module1.get_success_summary()
            st.session_state.summaries['module1'] = summary
            st.session_state.pipeline_data = df
            st.session_state.pipeline_step = 1
            st.rerun()
        else:
            survivors = int(st.session_state.get('m1_survivor_count', len(st.session_state.pipeline_data)))
            inputs = int(st.session_state.get('m1_input_count', survivors))
            ejected = max(inputs - survivors, 0)

            # 🎉 Celebration banner -------------------------------------------------
            if ejected > 0:
                st.markdown(
                    f"### 🎉 Congratulations! **{survivors} of {inputs}** stars survived the Gaia DR3 Survival Test."
                )
                st.caption(
                    f"🔬 {ejected} did not meet the K-Dwarf criteria and were ejected. "
                    f"The {survivors} **🌱 Survivors** below are ready for Modules 2–8."
                )
            else:
                st.markdown(
                    f"### 🎉 Congratulations! All **{survivors}** stars cleared the gauntlet — meet your **🌱 Survivors**!"
                )
                st.caption("They are now ready to continue the journey toward Earth 2.0.")

            # Re-derive the tier on the fly from the actual Gaia DR3 quality
            # columns. We deliberately ignore the CSV's `validation_tier`
            # column because in some catalogs every survivor is stamped
            # "Bronze" by an upstream pipeline, which would mis-bucket every
            # star into "Failed" under our renamed UI labels.
            data = st.session_state.pipeline_data

            def _col(*names):
                """Return the first column name present in `data`, else None."""
                for n in names:
                    if n in data.columns:
                        return n
                return None

            teff_col = _col('teff_gspphot', 'Teff', 'teff')
            logg_col = _col('logg_gspphot', 'logg')
            ruwe_col = _col('ruwe', 'RUWE')
            bprp_col = _col('bp_rp', 'BP_RP', 'BP-RP')

            n = len(data)
            gold = silver = failed = 0
            tier_series = None
            if teff_col and logg_col and ruwe_col:
                teff = pd.to_numeric(data[teff_col], errors='coerce')
                logg = pd.to_numeric(data[logg_col], errors='coerce')
                ruwe = pd.to_numeric(data[ruwe_col], errors='coerce')
                bprp = (
                    pd.to_numeric(data[bprp_col], errors='coerce')
                    if bprp_col else pd.Series([np.nan] * n, index=data.index)
                )

                # Pass = K-Dwarf survival cuts (loose).
                pass_mask = (
                    teff.between(3900, 5300)
                    & (logg >= 4.0)
                    & (ruwe < 1.4)
                )
                # Gold = Gaia Certified K Dwarf -> all clean with margin.
                gold_mask = pass_mask & (
                    teff.between(4000, 5200)
                    & (logg >= 4.2)
                    & (ruwe < 1.1)
                    & (bprp.between(1.3, 3.0) | bprp.isna())
                )
                # Silver = passes thresholds but borderline.
                silver_mask = pass_mask & ~gold_mask
                # Failed = doesn't meet minimum K-Dwarf cuts.
                failed_mask = ~pass_mask

                tier_series = np.where(
                    gold_mask, 'Gaia Certified K Dwarf',
                    np.where(silver_mask, 'Need Follow Up', 'Failed')
                )
                gold = int(gold_mask.sum())
                silver = int(silver_mask.sum())
                failed = int(failed_mask.sum())

                # Expose the derived tier on the dataframe so it appears in
                # the preview table and can be exported.
                data = data.copy()
                data['tier'] = tier_series
                st.session_state.pipeline_data = data

            tcol1, tcol2, tcol3 = st.columns(3)
            tcol1.metric("� Gaia Certified K Dwarf", gold)
            tcol2.metric("🥈 Need Follow Up",         silver)
            tcol3.metric("🥉 Failed",                  failed)

            st.success(st.session_state.summaries.get('module1', 'Module 1: Data Input | 1 of 8 Complete!'))

            # Preview the survivor table (richer column set when available).
            preview_cols = [c for c in [
                'source_id', 'gaia_dr3_name', 'ra', 'dec',
                'teff_gspphot', 'logg_gspphot', 'ruwe',
                'k_subtype', 'tier'
            ] if c in data.columns]
            if not preview_cols:
                preview_cols = list(data.columns[:6])
            st.dataframe(data[preview_cols].head(20), use_container_width=True)

            # Fire balloons exactly once per Run.
            if not st.session_state.get('m1_celebrated', False):
                st.balloons()
                st.session_state.m1_celebrated = True
        
        if st.session_state.pipeline_step == 1 and not st.session_state.m1_only:
            if st.button("Continue to Module 2", key="m1_continue"):
                st.session_state.pipeline_step = 2
                st.rerun()
        elif st.session_state.pipeline_step == 1 and st.session_state.m1_only:
            st.info("✅ Module 1 complete. Modules 2-8 are disabled while we focus on Module 1.")

if st.session_state.pipeline_started and not st.session_state.m1_only and st.session_state.pipeline_step >= 1:
    # Module 2: Stellar Parameters
    with st.expander("🌟 Module 2 of 8 - Stellar Parameters", expanded=st.session_state.pipeline_step == 1):
        if st.session_state.pipeline_step == 1:
            st.info("Retrieving stellar parameters from Gaia DR3...")
            
            module2 = StellarParameterModule()
            df, quality = module2.get_parameters(st.session_state.pipeline_data, use_mock=use_mock)
            
            summary = module2.get_success_summary()
            st.session_state.summaries['module2'] = summary
            st.success(summary)
            st.dataframe(df[['source_id', 'ra', 'dec', 'teff_gspphot', 'logg_gspphot', 'ruwe']].head())
            
            st.session_state.pipeline_data = df
            st.session_state.pipeline_step = 2
            st.rerun()
        else:
            st.success(st.session_state.summaries.get('module2', 'Module 2: Stellar Parameters | 2 of 8 Complete!'))
            # Only display columns that exist
            cols_to_show = ['source_id']
            for col in ['ra', 'dec', 'teff_gspphot', 'logg_gspphot', 'ruwe']:
                if col in st.session_state.pipeline_data.columns:
                    cols_to_show.append(col)
            st.dataframe(st.session_state.pipeline_data[cols_to_show].head())
        
        if st.session_state.pipeline_step == 2:
            if st.button("Continue to Module 3", key="m2_continue"):
                st.session_state.pipeline_step = 3
                st.rerun()

if st.session_state.pipeline_started and not st.session_state.m1_only and st.session_state.pipeline_step >= 2:
    # Module 3: Exoplanet Cross-Match
    with st.expander("🪐 Module 3 of 8 - Exoplanet Cross-Match", expanded=st.session_state.pipeline_step == 2):
        if st.session_state.pipeline_step == 2:
            st.info("Cross-matching with NASA Exoplanet Archive...")
            
            module3 = ExoplanetCrossMatchModule()
            df, report = module3.cross_match(st.session_state.pipeline_data, use_mock=use_mock)
            
            summary = module3.get_success_summary()
            st.session_state.summaries['module3'] = summary
            st.success(summary)
            st.dataframe(df[['source_id', 'has_exoplanet', 'exo_pl_name', 'exo_pl_orbper']].head())
            
            st.session_state.pipeline_data = df
            st.session_state.pipeline_step = 3
            st.rerun()
        else:
            st.success(st.session_state.summaries.get('module3', 'Module 3: Exoplanet Cross-Match | 3 of 8 Complete!'))
            # Only display columns that exist
            cols_to_show = ['source_id']
            for col in ['has_exoplanet', 'exo_pl_name', 'exo_pl_orbper']:
                if col in st.session_state.pipeline_data.columns:
                    cols_to_show.append(col)
            st.dataframe(st.session_state.pipeline_data[cols_to_show].head())
        
        if st.session_state.pipeline_step == 3:
            if st.button("Continue to Module 4", key="m3_continue"):
                st.session_state.pipeline_step = 4
                st.rerun()

if st.session_state.pipeline_started and not st.session_state.m1_only and st.session_state.pipeline_step >= 3:
    # Module 4: TESS Light Curves
    with st.expander("📈 Module 4 of 8 - TESS Light Curves", expanded=st.session_state.pipeline_step == 3):
        if st.session_state.pipeline_step == 3:
            st.info("Retrieving TESS light curves from MAST API...")
            
            module4 = TESSLightCurveModule()
            df, report = module4.retrieve_lightcurves(st.session_state.pipeline_data, use_mock=use_mock)
            
            summary = module4.get_success_summary()
            st.session_state.summaries['module4'] = summary
            st.success(summary)
            st.dataframe(df[['source_id', 'tess_available', 'sectors', 'data_points', 'cadence_minutes']].head())
            
            st.session_state.pipeline_data = df
            st.session_state.pipeline_step = 4
            st.rerun()
        else:
            st.success(st.session_state.summaries.get('module4', 'Module 4: TESS Light Curves | 4 of 8 Complete!'))
            # Only display columns that exist
            cols_to_show = ['source_id']
            for col in ['tess_available', 'sectors', 'data_points', 'cadence_minutes']:
                if col in st.session_state.pipeline_data.columns:
                    cols_to_show.append(col)
            st.dataframe(st.session_state.pipeline_data[cols_to_show].head())
        
        if st.session_state.pipeline_step == 4:
            if st.button("Continue to Module 5", key="m4_continue"):
                st.session_state.pipeline_step = 5
                st.rerun()

if st.session_state.pipeline_started and not st.session_state.m1_only and st.session_state.pipeline_step >= 4:
    # Module 5: Transit Detection
    with st.expander("🎯 Module 5 of 8 - Transit Detection", expanded=st.session_state.pipeline_step == 4):
        if st.session_state.pipeline_step == 4:
            st.info("Detecting transits using BLS periodogram...")
            
            module5 = TransitDetectionModule()
            df, report = module5.detect_transits(st.session_state.pipeline_data, use_mock=use_mock)
            
            summary = module5.get_success_summary()
            st.session_state.summaries['module5'] = summary
            st.success(summary)
            st.dataframe(df[['source_id', 'has_transit_candidate', 'transit_period', 'transit_snr']].head())
            
            st.session_state.pipeline_data = df
            st.session_state.pipeline_step = 5
            st.rerun()
        else:
            st.success(st.session_state.summaries.get('module5', 'Module 5: Transit Detection | 5 of 8 Complete!'))
            # Only display columns that exist
            cols_to_show = ['source_id']
            for col in ['has_transit_candidate', 'transit_period', 'transit_snr']:
                if col in st.session_state.pipeline_data.columns:
                    cols_to_show.append(col)
            st.dataframe(st.session_state.pipeline_data[cols_to_show].head())
        
        if st.session_state.pipeline_step == 5:
            if st.button("Continue to Module 6", key="m5_continue"):
                st.session_state.pipeline_step = 6
                st.rerun()

if st.session_state.pipeline_started and not st.session_state.m1_only and st.session_state.pipeline_step >= 5:
    # Module 6: Habitability Scoring
    with st.expander("💧 Module 6 of 8 - Habitability Scoring", expanded=st.session_state.pipeline_step == 5):
        if st.session_state.pipeline_step == 5:
            st.info("Scoring habitability of stars and exoplanets...")
            
            module6 = HabitabilityScoringModule()
            df, report = module6.score_habitability(st.session_state.pipeline_data, st.session_state.pipeline_data)
            
            summary = module6.get_success_summary()
            st.session_state.summaries['module6'] = summary
            st.success(summary)
            # Only display columns that exist
            cols_to_show = ['source_id', 'stellar_hab_score']
            if 'exo_hab_score' in df.columns:
                cols_to_show.append('exo_hab_score')
            if 'esi' in df.columns:
                cols_to_show.append('esi')
            st.dataframe(df[cols_to_show].head())
            
            st.session_state.pipeline_data = df
            st.session_state.pipeline_step = 6
            st.rerun()
        else:
            st.success(st.session_state.summaries.get('module6', 'Module 6: Habitability Scoring | 6 of 8 Complete!'))
            # Only display columns that exist
            cols_to_show = ['source_id', 'stellar_hab_score']
            if 'exo_hab_score' in st.session_state.pipeline_data.columns:
                cols_to_show.append('exo_hab_score')
            if 'esi' in st.session_state.pipeline_data.columns:
                cols_to_show.append('esi')
            st.dataframe(st.session_state.pipeline_data[cols_to_show].head())
        
        if st.session_state.pipeline_step == 6:
            if st.button("Continue to Module 7", key="m6_continue"):
                st.session_state.pipeline_step = 7
                st.rerun()

if st.session_state.pipeline_started and not st.session_state.m1_only and st.session_state.pipeline_step >= 6:
    # Module 7: Results Summary
    with st.expander("🏆 Module 7 of 8 - Results Summary", expanded=st.session_state.pipeline_step == 6):
        if st.session_state.pipeline_step == 6:
            st.info("Generating comprehensive results summary...")
            
            module7 = ResultsSummaryModule()
            df, report = module7.generate_summary(st.session_state.pipeline_data)
            
            summary = module7.get_success_summary()
            st.session_state.summaries['module7'] = summary
            st.success(summary)
            
            # Display top discoveries
            st.subheader("Top Discoveries")
            for i, discovery in enumerate(report['top_discoveries'][:5], 1):
                st.write(f"{i}. TIC {discovery['source_id']} - {discovery['description']}")
            
            st.session_state.pipeline_data = df
            st.session_state.pipeline_step = 7
            st.rerun()
        else:
            st.success(st.session_state.summaries.get('module7', 'Module 7: Results Summary | 7 of 8 Complete!'))
            
            # Display top discoveries
            st.subheader("Top Discoveries")
            for i, discovery in enumerate(st.session_state.pipeline_data.get('top_discoveries', [] )[:5], 1):
                st.write(f"{i}. TIC {discovery['source_id']} - {discovery['description']}")
        
        if st.session_state.pipeline_step == 7:
            if st.button("Continue to Module 8", key="m7_continue"):
                st.session_state.pipeline_step = 8
                st.rerun()

if st.session_state.pipeline_started and not st.session_state.m1_only and st.session_state.pipeline_step >= 7:
    # Module 8: Data Export
    with st.expander("💾 Module 8 of 8 - Data Export", expanded=st.session_state.pipeline_step == 7):
        if st.session_state.pipeline_step == 7:
            st.info("Exporting results in multiple formats...")
            
            module8 = DataExportModule()
            report, summary = module8.export_data(st.session_state.pipeline_data, formats=['csv', 'json'])
            
            st.session_state.summaries['module8'] = summary
            st.success(summary)
            
            # Display export report
            st.subheader("Export Report")
            st.json(report)
            
            st.session_state.pipeline_step = 8
            st.rerun()
        else:
            st.success(st.session_state.summaries.get('module8', 'Module 8: Data Export | 8 of 8 Complete!'))
            
            # Display export report
            st.subheader("Export Report")
            st.json(st.session_state.pipeline_data.get('export_report', {}))
        
        if st.session_state.pipeline_step == 8:
            st.balloons()
            st.markdown("---")
            st.success("🎉 Pipeline Complete! All modules executed successfully!")

# Reset button
if st.session_state.pipeline_step > 0 or st.session_state.pipeline_started:
    st.markdown("---")
    if st.button("🔄 Reset Pipeline"):
        st.session_state.pipeline_step = 0
        st.session_state.pipeline_data = None
        st.session_state.pipeline_started = False
        st.session_state.summaries = {}
        st.rerun()
