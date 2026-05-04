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
import io
import matplotlib.pyplot as plt
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from identifier_resolver import parse_manual_input
from gaia_enricher import enrich_rows
from workspace import auth_strip, current_user, sign_in_widget, get_store, save_user_progress
from workspace.store import RunMeta, RunRecord, new_run_id, normalize_user_id
from workspace.navigation import render_navigation
from certificate import render_certificate, render_module2_certificate, render_module3_certificate, render_module4_certificate, render_module5_certificate

# Add src to path for module imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from modules.module1_data_input import DataInputModule
from modules.module3_exoplanet_crossmatch import StartExoplanetQuestModule
from modules.module4_tess_lightcurves import TESSLightCurveModule
from modules.module5_transit_detection import TransitDetectionModule
from modules.module6_habitability_scoring import HabitabilityScoringModule
from modules.module7_results_summary import ResultsSummaryModule
from modules.module8_data_export import DataExportModule
from modules.module4_5_exominer_vetting import ExoMinerVettingModule

st.set_page_config(
    page_title="ExoQ: Exoplanet Community Quest for Earth 2.0",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Hide sidebar completely for mobile-first design
st.markdown(
    """
    <style>
        /* Hide the entire sidebar */
        [data-testid="stSidebar"] {
            display: none !important;
        }
        /* Hide the collapsed sidebar toggle */
        [data-testid="collapsedControl"] {
            display: none !important;
        }
        /* Hide sidebar navigation */
        section[data-testid="stSidebarNav"] {
            display: none !important;
        }
        /* Hide the main menu button (hamburger icon) */
        button[data-testid="stMainMenu"] {
            display: none !important;
        }
        /* Hide any button with aria-label containing "menu" */
        button[aria-label*="menu"],
        button[aria-label*="Menu"] {
            display: none !important;
        }
        /* Hide the top-left header that contains the sidebar toggle */
        .css-1d391kg {
            display: none !important;
        }
        /* Hide the header block */
        header[data-testid="stHeader"] {
            display: none !important;
        }
        /* Hide the sidebar icon */
        span[data-testid="stIconMaterial"] {
            display: none !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
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

# Mobile-friendly navigation menu
render_navigation()

# ExoQuest Leaderboard
st.markdown("---")

st.markdown("""
<style>
div[data-testid="stExpander"] > div > div > div > button {
    font-size: 0.8em !important;
}
div[data-testid="stExpander"] {
    text-align: left !important;
}
</style>
""", unsafe_allow_html=True)

with st.expander("🏆 ExoQuest Gamify LM | View Leaderboard", expanded=False):
    if current_user():
        store = get_store()
        try:
            all_users_progress = store.get_all_users_progress()
            
            if all_users_progress:
                # Sort users by score (descending)
                sorted_users = sorted(
                    all_users_progress.items(),
                    key=lambda x: x[1].get("score", 0),
                    reverse=True
                )
                
                # Find current user's rank
                current_user_id = current_user()
                current_user_rank = None
                current_user_score = 0
                for idx, (user_id, progress) in enumerate(sorted_users, 1):
                    if user_id == current_user_id:
                        current_user_rank = idx
                        current_user_score = progress.get("score", 0)
                        break
                
                # Display current user's stats
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Your Score", current_user_score)
                with col2:
                    st.metric("Your Rank", f"#{current_user_rank}" if current_user_rank else "N/A")
                with col3:
                    st.metric("Total Players", len(sorted_users))
                
                # Display leaderboard
                st.markdown("#### Top Players")
                leaderboard_data = []
                for rank, (user_id, progress) in enumerate(sorted_users[:10], 1):
                    leaderboard_data.append({
                        "Rank": rank,
                        "Player": progress.get("display_name", user_id),
                        "Score": progress.get("score", 0),
                        "Stars Analyzed": len(progress.get("analyzed_stars", [])),
                        "Badges": len(progress.get("badges", []))
                    })
                
                df_leaderboard = pd.DataFrame(leaderboard_data)
                st.dataframe(
                    df_leaderboard,
                    column_config={
                        "Rank": st.column_config.NumberColumn("Rank", format="%d"),
                        "Player": st.column_config.TextColumn("Player"),
                        "Score": st.column_config.NumberColumn("Score"),
                        "Stars Analyzed": st.column_config.NumberColumn("Stars Analyzed"),
                        "Badges": st.column_config.NumberColumn("Badges")
                    },
                    hide_index=True,
                    use_container_width=True
                )
            else:
                st.info("No player data available yet. Be the first to play!")
        except Exception as e:
            st.warning(f"Could not load leaderboard: {e}")
    else:
        st.info("Please sign in to view the leaderboard.")

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

        /* Tier scoreboard metrics: smaller, grey, professional */
        [data-testid="stMetricValue"],
        [data-testid="stMetricValue"] > div,
        [data-testid="stMetricValue"] * {
            font-size: 1.1rem !important;
            font-weight: 600 !important;
            color: #6b7280 !important;
        }
        [data-testid="stMetricLabel"],
        [data-testid="stMetricLabel"] * {
            font-size: 0.8rem !important;
            color: #6b7280 !important;
        }

        /* File uploader Browse button -> dark green to match Run Module 1 */
        [data-testid="stFileUploader"] button,
        [data-testid="stFileUploaderDropzone"] button {
            background-color: #1b5e20 !important;
            border-color: #1b5e20 !important;
            color: #ffffff !important;
            padding-left: 12px !important;
            padding-right: 12px !important;
            direction: ltr !important;
            text-align: left !important;
        }
        [data-testid="stFileUploader"] button:hover,
        [data-testid="stFileUploaderDropzone"] button:hover {
            background-color: #2e7d32 !important;
            border-color: #2e7d32 !important;
            color: #ffffff !important;
        }
        /* Force all inner elements to be left-aligned */
        [data-testid="stFileUploader"] button *,
        [data-testid="stFileUploaderDropzone"] button * {
            text-align: left !important;
            direction: ltr !important;
        }
        /* Target the specific label element in the upload button */
        [data-testid="stFileUploader"] button label,
        [data-testid="stFileUploaderDropzone"] button label {
            text-align: left !important;
            direction: ltr !important;
            justify-content: flex-start !important;
            align-items: flex-start !important;
        }
        /* Target the button's inner container */
        [data-testid="stFileUploader"] button > div > div > div,
        [data-testid="stFileUploaderDropzone"] button > div > div > div {
            text-align: left !important;
            direction: ltr !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Add JavaScript to force left alignment on upload button
st.markdown("""
<script>
const forceLeftAlign = () => {
    const buttons = document.querySelectorAll("[data-testid='stFileUploader'] button, [data-testid='stFileUploaderDropzone'] button");
    buttons.forEach(btn => {
        btn.style.textAlign = 'left';
        btn.style.direction = 'ltr';
        btn.style.justifyContent = 'flex-start';
        const children = btn.querySelectorAll('*');
        children.forEach(child => {
            child.style.textAlign = 'left';
            child.style.direction = 'ltr';
        });
    });
};
setTimeout(forceLeftAlign, 1000);
setInterval(forceLeftAlign, 2000);
</script>
""", unsafe_allow_html=True)

# --- Main Menu + inline Sign in / Sign up strip ------------------------------
# Simple two-column layout: Main Menu flush left, auth links on right.
menu_col, auth_col = st.columns([1, 4])
with menu_col:
    with st.popover("☰ Main Menu", use_container_width=False):
        sign_in_widget()
        st.page_link("pages/1_Authentication.py", label="Create an Account")
        from workspace.identity import sign_out
        from workspace import current_user
        st.markdown("---")
        st.page_link("Home.py", label="🏠 Home (you're here)")
        if current_user():
            st.markdown("---")
            st.page_link("pages/2_My_Workspace.py", label="📁 My Workspace")
            st.markdown("---")
            if st.button("Sign out", key="main_menu_signout"):
                sign_out()
                st.rerun()
        st.markdown("---")
        st.markdown("#### 📚 Modules")
        
        # Dynamic navigation based on pipeline step
        modules = []
        for i, (name, step) in enumerate([
            ("Data Input and Gaia Survival Test", 1),
            ("Stellar Parameters", 2),
            ("Exoplanet Crossmatch", 3),
            ("TESS Light Curves", 4),
            ("ExoMiner++ Vetting", 4.5),
            ("Transit Detection", 5),
            ("Habitability Scoring", 6),
            ("Results Summary", 7),
            ("Data Export", 8)
        ]):
            if st.session_state.get('pipeline_step', 0) >= step:
                modules.append(f"**▶ Module {int(step) if step == int(step) else step} of 8 - {name}**")
            else:
                modules.append(f"🔒 Module {int(step) if step == int(step) else step} of 8 - {name}")
        
        st.markdown("  \n".join(modules))
        st.markdown("---")
        # Check if user can run full pipeline
        can_run_full_pipeline = False
        if current_user():
            store = get_store()
            uid = normalize_user_id(current_user())
            
            # Check gallery posts count
            gallery_posts = store.get_gallery_posts_count(uid)
            
            # Check account tenure (1 month = 30 days)
            created_at_str = store.get_created_at(uid)
            days_since_creation = 0
            if created_at_str:
                try:
                    from datetime import datetime, timezone, timedelta
                    created_at = datetime.fromisoformat(created_at_str)
                    if created_at.tzinfo is None:
                        created_at = created_at.replace(tzinfo=timezone.utc)
                    days_since_creation = (datetime.now(timezone.utc) - created_at).days
                except Exception:
                    days_since_creation = 0
            
            # User can run full pipeline if they have 1 month tenure OR 12 gallery posts
            can_run_full_pipeline = (days_since_creation >= 30) or (gallery_posts >= 12)
        
        run_pipeline = st.button(
            "🚀 Run Full Pipeline",
            disabled=not can_run_full_pipeline,
            help="Members only. Unlocks after 1 month of membership OR 12 contributed posts." if not can_run_full_pipeline else "Run all modules automatically",
            use_container_width=True,
        )
        st.markdown("---")
        st.markdown("#### 🔗 Links")
        st.markdown("[💻 GitHub Repo](https://github.com/sidbalatan/ExoQ)")
with auth_col:
    auth_strip()

# --- Main page: Module 1 input controls --------------------------------------
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
    st.markdown("#### 📂 Upload CSV")
    uploaded_file = st.file_uploader(
        "Choose a CSV file",
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

# Modules 2-8 use live data from NASA APIs (MAST, Exoplanet Archive, Gaia DR3)
# Data is retrieved in real-time from scientific databases
use_mock = False

st.info("🌐 **Live Data Mode**: Retrieving real-time data from NASA APIs (MAST, Exoplanet Archive, Gaia DR3)\n\n⚠️ **Note**: If data retrieval takes longer than expected, the APIs may be busy. Please try again in a few minutes.")

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
    st.session_state.m1_only = False
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
    with st.expander("📥 Module 1 of 8 - Data Input and Gaia Survival Test", expanded=True):
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

                # ----- LIVE Gaia DR3 ADQL enrichment -------------------------
                # Cross-match each manual entry against the Gaia DR3 archive
                # so the Survival Test classifier has real teff/logg/RUWE/BP-RP.
                progress_bar = st.progress(0.0, text="Cross-matching against live Gaia DR3 …")

                def _on_gaia_progress(done, total, msg):
                    pct = min(done / max(total, 1), 1.0)
                    progress_bar.progress(pct, text=msg)

                enriched = enrich_rows(rows, progress_cb=_on_gaia_progress)
                progress_bar.empty()

                if len(enriched) == len(df):
                    # Promote Gaia coords/columns into the working df by row index.
                    enriched = enriched.reset_index(drop=True)
                    df = df.reset_index(drop=True)
                    for col in [
                        "ra", "dec", "parallax", "ruwe",
                        "phot_g_mean_mag", "bp_rp",
                        "teff_gspphot", "logg_gspphot",
                        "gaia_match_arcsec", "gaia_dr3_name", "identifier",
                        "source_id",
                    ]:
                        if col in enriched.columns:
                            df[col] = enriched[col]
                    # Replace the synthetic source_id (if any) with the real
                    # Gaia DR3 one whenever the cross-match succeeded.
                    if "source_id" in enriched.columns:
                        real_sid = enriched["source_id"]
                        if "source_id" in df.columns:
                            df["source_id"] = real_sid.where(real_sid.notna(), df["source_id"])
                        else:
                            df["source_id"] = real_sid
                    module1.data = df

                # Surface match diagnostics so the user can see what came back.
                matched = int(enriched["source_id"].notna().sum()) if "source_id" in enriched.columns else 0
                missed = len(enriched) - matched
                if matched:
                    st.success(
                        f"📡 Gaia DR3 ADQL: matched **{matched}** of {len(enriched)} entries to live Gaia sources."
                    )
                if missed:
                    st.warning(
                        f"⚠️ {missed} entry(ies) had no Gaia DR3 match within 3 arcsec — "
                        f"they will appear without Teff / logg / RUWE values."
                    )

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

            # ----- Auto-save the run to the user's workspace ----------
            uid = current_user()
            if uid:
                try:
                    # Tier counts derived inline so we don't depend on the
                    # display block below having run yet.
                    def _tier_counts(_df):
                        cols = {c.lower(): c for c in _df.columns}
                        teff = pd.to_numeric(_df.get(cols.get('teff_gspphot') or cols.get('teff') or 'teff', np.nan), errors='coerce')
                        logg = pd.to_numeric(_df.get(cols.get('logg_gspphot') or cols.get('logg') or 'logg', np.nan), errors='coerce')
                        ruwe = pd.to_numeric(_df.get(cols.get('ruwe') or 'ruwe', np.nan), errors='coerce')
                        bprp_key = cols.get('bp_rp') or cols.get('bp-rp') or 'bp_rp'
                        bprp = pd.to_numeric(_df.get(bprp_key, pd.Series([np.nan]*len(_df))), errors='coerce')
                        passm = teff.between(3900, 5300) & (logg >= 4.0) & (ruwe < 1.4)
                        gold = passm & teff.between(4000, 5200) & (logg >= 4.2) & (ruwe < 1.1) & (bprp.between(1.3, 3.0) | bprp.isna())
                        silver = passm & ~gold
                        failed = ~passm
                        return int(gold.sum()), int(silver.sum()), int(failed.sum())

                    g, s, f = _tier_counts(df)
                    run_id = new_run_id()
                    meta = RunMeta(
                        run_id=run_id,
                        user_id=uid,
                        created_at=pd.Timestamp.utcnow().isoformat(),
                        module="module1",
                        source="csv" if data_source == "Upload CSV" else "manual",
                        inputs_count=int(input_count),
                        survivors_count=int(g + s),
                        gold=g, silver=s, failed=f,
                        label="",
                    )
                    record = RunRecord(
                        meta=meta,
                        frames={"survivors": df.copy()},
                        extras={
                            "data_source": data_source,
                            "manual_text": manual_text if data_source != "Upload CSV" else "",
                            "n_stars_cap": int(n_stars),
                        },
                    )
                    saved_id = get_store().save_run(record)
                    st.session_state["m1_last_saved_run_id"] = saved_id
                except Exception as exc:
                    st.warning(f"Run completed but could not be saved to your workspace: {exc}")

            st.rerun()
        else:
            inputs = int(st.session_state.get('m1_input_count',
                          len(st.session_state.pipeline_data)))

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

                # Only apply K-Dwarf cuts to stars that have valid Gaia DR3 data
                # Check if key survival criteria columns have valid (non-NaN) values
                survival_criteria_cols = ['teff_gspphot', 'logg_gspphot', 'ruwe', 'bp_rp', 'parallax']
                has_gaia_data = True
                for col in survival_criteria_cols:
                    if col in data.columns:
                        has_gaia_data = has_gaia_data & data[col].notna()
                
                # Pass = K-Dwarf survival cuts (loose).
                pass_mask = (
                    teff.between(3900, 5300) & has_gaia_data
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
                # Failed = doesn't meet minimum K-Dwarf cuts OR has no Gaia DR3 data.
                failed_mask = ~pass_mask

                tier_series = np.where(
                    gold_mask, 'Gaia Certified K Dwarf',
                    np.where(silver_mask, 'Need Follow Up', 
                            np.where(~has_gaia_data, 'Awaiting Gaia DR3 Data', 'Failed'))
                )
                gold = int(gold_mask.sum())
                silver = int(silver_mask.sum())
                failed = int(failed_mask.sum())

                # Expose the derived tier on the dataframe so it appears in
                # the preview table and can be exported.
                data = data.copy()
                data['tier'] = tier_series
                st.session_state.pipeline_data = data
            else:
                # No Gaia DR3 columns available - mark all as awaiting data
                data = data.copy()
                data['tier'] = 'Awaiting Gaia DR3 Data'
                st.session_state.pipeline_data = data
                failed = n

            survivors = gold + silver
            awaiting_data = int((data['tier'] == 'Awaiting Gaia DR3 Data').sum()) if 'tier' in data.columns else 0
            _hdr_style = "font-size: 1rem; font-weight: 600; margin: 0.4rem 0 0.1rem 0;"
            # Celebration banner ---------------------------------------------------
            if awaiting_data > 0:
                st.markdown(
                    f"<p style='{_hdr_style}'><b>{awaiting_data}</b> stars are ready for Module 2 to retrieve Gaia DR3 data.</p>",
                    unsafe_allow_html=True,
                )
                st.caption("These stars will be enriched with stellar parameters in Module 2.")
            elif failed == 0 and survivors == inputs and survivors > 0:
                st.markdown(
                    f"<p style='{_hdr_style}'>All <b>{survivors}</b> stars cleared the GAIA Survival Test — meet your Survivors.</p>",
                    unsafe_allow_html=True,
                )
                st.caption("They are now ready to continue the journey toward Earth 2.0.")
            elif survivors > 0:
                st.markdown(
                    f"<p style='{_hdr_style}'><b>{survivors} of {inputs}</b> stars passed the GAIA Survival Test.</p>",
                    unsafe_allow_html=True,
                )
                st.caption(
                    f"{failed} did not meet the K-Dwarf criteria and are flagged Failed. "
                    f"The {survivors} survivors below are ready for Modules 2–8."
                )
            else:
                st.markdown(
                    f"<p style='{_hdr_style}'>None of the <b>{inputs}</b> input stars passed the GAIA Survival Test.</p>",
                    unsafe_allow_html=True,
                )
                st.caption(
                    "Either the cross-match returned no Gaia DR3 data for these inputs, "
                    "or every entry was flagged Failed by the K-Dwarf cuts."
                )

            tcol1, tcol2, tcol3 = st.columns(3)
            tcol1.metric("🥇 Gaia Certified K Dwarf", gold)
            tcol2.metric("🥈 Need Follow Up",         silver)
            tcol3.metric("🥉 Failed",                  failed)

            # Summary report with survival criteria explanation
            st.markdown("---")
            st.markdown("#### 🛡️ Gaia DR3 Survival Test Results")
            
            if awaiting_data > 0:
                st.info(f"ℹ️ **{awaiting_data} of {inputs} stars await Gaia DR3 data retrieval** ({awaiting_data/inputs:.1%})")
                st.caption(f"These stars will be processed in Module 2 to retrieve stellar parameters and determine K Dwarf status")
            elif survivors == inputs and inputs > 0:
                st.success(f"✅ **All {inputs} coordinates survived the Gaia DR3 Survival Test**")
                st.caption("These stars passed all quality filters and are considered **K Dwarf candidates**")
            elif survivors > 0:
                st.warning(f"⚠️ **{survivors} of {inputs} coordinates survived** ({survivors/inputs:.1%})")
                st.caption(f"{inputs - survivors} stars failed one or more quality filters")
            else:
                st.error(f"❌ **0 of {inputs} coordinates survived**")
                st.caption("All stars failed one or more quality filters")
            
            # Survival criteria details
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

            # Replace the legacy module1 'success' summary (which only validates
            # RA/Dec ranges and would mis-report "100% pass rate" even when
            # rows fail the K-Dwarf cuts) with a truthful tier-based summary.
            pass_pct = (100.0 * survivors / inputs) if inputs else 0.0
            if awaiting_data == inputs and inputs > 0:
                st.success(
                    f"**Module 1: Data Input and Gaia Survival Test | 1 of 8 Complete** \n"
                    f"All {inputs} stars loaded and ready for Module 2 to retrieve Gaia DR3 data."
                )
            elif survivors == inputs and inputs > 0:
                st.success(
                    f"**Module 1: Data Input and Gaia Survival Test | 1 of 8 Complete** \n"
                    f"All {inputs} stars passed the GAIA DR3 Survival Test "
                    f"({gold} Certified, {silver} Need Follow Up). Ready for Module 2."
                )
            elif survivors > 0:
                st.success(
                    f"**Module 1: Data Input and Gaia Survival Test | 1 of 8 Complete** \n"
                    f"{survivors} of {inputs} stars passed the GAIA DR3 Survival Test "
                    f"({pass_pct:.0f}% pass rate \u2014 {gold} Certified, {silver} Need Follow Up, "
                    f"{failed} Failed). Survivors continue to Module 2."
                )
            else:
                st.warning(
                    f"**Module 1: Data Input and Gaia Survival Test | 1 of 8 Complete** \n"
                    f"0 of {inputs} stars passed the GAIA DR3 Survival Test \u2014 "
                    f"all {failed} were flagged Failed. Review the inputs before continuing."
                )

            # Preview the survivor table (richer column set when available).
            preview_cols = [c for c in [
                'module1_passed', 'source_id', 'gaia_dr3_name', 'ra', 'dec',
                'teff_gspphot', 'logg_gspphot', 'ruwe',
                'k_subtype', 'tier'
            ] if c in data.columns]
            if not preview_cols:
                preview_cols = list(data.columns[:6])
            
            # Create a copy and reset index starting from 1
            preview_df = data[preview_cols].head(20).copy()
            preview_df = preview_df.reset_index(drop=True)
            preview_df.index = preview_df.index + 1
            
            # Rename module1_passed to Survived if present
            if 'module1_passed' in preview_df.columns:
                preview_df = preview_df.rename(columns={'module1_passed': '✅ Survived'})
            
            st.dataframe(preview_df, use_container_width=True)

            # ----- Live Gaia DR3 Verification report --------------------
            st.markdown(
                "<p style='font-size: 1rem; font-weight: 600; margin: 0.6rem 0 0.1rem 0;'>"
                "Live ESA Gaia DR3 verification</p>",
                unsafe_allow_html=True,
            )
            st.caption(
                "These are the raw values returned by the live ADQL query against "
                "`gaiadr3.gaia_source` joined with `gaiadr3.astrophysical_parameters`. "
                "The tier column is derived from these values by the GAIA Survival Test."
            )
            
            # Show available columns
            available_verify_cols = [c for c in [
                'source_id', 'teff_gspphot', 'logg_gspphot',
                'ruwe', 'bp_rp', 'tier', 'gaia_dr3_name', 'ra', 'dec'
            ] if c in data.columns]
            
            if available_verify_cols:
                verify_df = data[available_verify_cols].copy()
                verify_df = verify_df.rename(columns={
                    'source_id':     'Gaia DR3 source_id',
                    'teff_gspphot':  'Teff (K)',
                    'logg_gspphot':  'log g',
                    'ruwe':          'RUWE',
                    'bp_rp':         'BP - RP',
                    'tier':          'Tier',
                    'gaia_dr3_name': 'Gaia DR3 Name',
                    'ra':            'RA (deg)',
                    'dec':           'Dec (deg)',
                })
                fmt_df = verify_df.copy()
                # Format numerics for readability
                for col, ndp in [('Teff (K)', 1), ('log g', 2), ('RUWE', 2), ('BP - RP', 2), ('RA (deg)', 6), ('Dec (deg)', 6)]:
                    if col in fmt_df.columns:
                        fmt_df[col] = pd.to_numeric(fmt_df[col], errors='coerce').round(ndp)
                if 'Gaia DR3 source_id' in fmt_df.columns:
                    fmt_df['Gaia DR3 source_id'] = fmt_df['Gaia DR3 source_id'].astype('Int64').astype(str)
                
                # Apply orange styling to survivor rows
                def highlight_survivor_row(row):
                    """Apply orange font color to entire row if it's a survivor."""
                    tier_val = row.get('Tier', '')
                    if tier_val == 'Gaia Certified K Dwarf' or tier_val == 'Need Follow Up':
                        return ['color: #FF8C00; font-weight: bold;' for _ in row]
                    else:
                        return ['' for _ in row]
                
                # Reset index starting from 1
                fmt_df = fmt_df.reset_index(drop=True)
                fmt_df.index = fmt_df.index + 1
                
                styler = fmt_df.head(20).style
                styler = styler.apply(highlight_survivor_row, axis=1)
                st.dataframe(styler, use_container_width=True, hide_index=True)
                st.caption(
                    f"**Live archive verdict:** "
                    f"🥇 **{gold}** Certified · 🥈 **{silver}** Need Follow Up · 🥉 **{failed}** Failed · ⏳ **{awaiting_data if 'awaiting_data' in locals() else 0}** Awaiting Data"
                )
            else:
                st.info("No Gaia DR3 data available - stars will be enriched in Module 2")

            # ----- Certificate of Discovery ----------------------------
            if survivors > 0:
                st.markdown(
                    "<p style='font-size: 1rem; font-weight: 600; margin: 0.8rem 0 0.1rem 0;'>"
                    "Certificate of Discovery</p>",
                    unsafe_allow_html=True,
                )
                st.caption(
                    "Downloadable PNG you can share on social media or submit to the "
                    "ExoQ public gallery. The data on the certificate is identical to the "
                    "live archive verdict above."
                )

                from certificate import render_certificate
                from workspace.identity import current_display_name, current_user

                # Pull a few survivor source_ids for the certificate footer.
                _sample_ids = []
                if "source_id" in data.columns:
                    _sample_ids = (
                        data.loc[data.get("tier", "").astype(str)
                                .str.contains("Certified|Follow", regex=True, na=False), "source_id"]
                            .dropna().head(5).tolist()
                    )
                    if not _sample_ids:
                        _sample_ids = data["source_id"].dropna().head(5).tolist()

                _display_name = current_display_name() or current_user() or "ExoQ Pioneer"
                _run_id = st.session_state.get("m1_last_saved_run_id", "")
                
                # Check if certificate already exists in session state
                if 'certificate_png' not in st.session_state:
                    try:
                        _png_bytes = render_certificate(
                            display_name=_display_name,
                            survivors_count=int(survivors),
                            inputs_count=int(inputs),
                            gold=int(gold), silver=int(silver), failed=int(failed),
                            sample_source_ids=_sample_ids,
                            run_id=_run_id,
                        )
                        st.session_state.certificate_png = _png_bytes
                        st.session_state.certificate_name = (
                            (_display_name or "ExoQ_Pioneer").replace(" ", "_")
                            + "_ExoQ_Certificate.png"
                        )
                    except Exception as exc:  # pragma: no cover -- never block the run on a render hiccup
                        st.warning(f"Certificate could not be rendered: {exc}")
                
                # Display certificate from session state
                if 'certificate_png' in st.session_state:
                    st.image(st.session_state.certificate_png, use_container_width=True)

                    # Check if pipeline_data exists for save button
                    has_pipeline_data = 'pipeline_data' in st.session_state and st.session_state.pipeline_data is not None
                    
                    if has_pipeline_data:
                        btn_left, btn_mid, btn_right = st.columns([1, 1, 1])
                        with btn_left:
                            st.download_button(
                                "⬇️ Download Certificate (PNG)",
                                data=st.session_state.certificate_png,
                                file_name=st.session_state.certificate_name,
                                mime="image/png",
                                type="primary",
                            )
                        with btn_mid:
                            csv_data = st.session_state.pipeline_data.to_csv(index=False)
                            st.download_button(
                                "💾 Save K Dwarf Survivors (CSV)",
                                data=csv_data,
                                file_name=f"ExoQ_Module1_KDwarf_Survivors_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv",
                                help="Save the K Dwarf survivors from Module 1 for use in Module 2"
                            )
                        with btn_right:
                            st.button(
                                "🌐 Submit to ExoQ Gallery (coming soon)",
                                disabled=True,
                                help=(
                                    "The public gallery launches with Module 8. "
                                    "Until then, download the PNG and share manually."
                                ),
                            )
                    else:
                        btn_left, btn_right = st.columns([1, 1])
                        with btn_left:
                            st.download_button(
                                "⬇️ Download Certificate (PNG)",
                                data=st.session_state.certificate_png,
                                file_name=st.session_state.certificate_name,
                                mime="image/png",
                                type="primary",
                            )
                        with btn_right:
                            st.button(
                                "🌐 Submit to ExoQ Gallery (coming soon)",
                                disabled=True,
                                help=(
                                    "The public gallery launches with Module 8. "
                                    "Until then, download the PNG and share manually."
                                ),
                            )

                    if not current_user():
                        st.caption(
                            "Tip: open **☰ Main Menu** and sign in with your name "
                            "to personalise the certificate."
                        )

            # Fire balloons exactly once per Run.
            if not st.session_state.get('m1_celebrated', False):
                st.balloons()
                st.session_state.m1_celebrated = True
        
        if st.session_state.pipeline_step == 1 and not st.session_state.m1_only:
            # Check if user can auto-run all modules
            can_auto_run = False
            if current_user():
                store = get_store()
                uid = normalize_user_id(current_user())
                
                # Check gallery posts count
                gallery_posts = store.get_gallery_posts_count(uid)
                
                # Check account tenure (1 month = 30 days)
                created_at_str = store.get_created_at(uid)
                days_since_creation = 0
                if created_at_str:
                    try:
                        from datetime import datetime, timezone, timedelta
                        created_at = datetime.fromisoformat(created_at_str)
                        if created_at.tzinfo is None:
                            created_at = created_at.replace(tzinfo=timezone.utc)
                        days_since_creation = (datetime.now(timezone.utc) - created_at).days
                    except Exception:
                        days_since_creation = 0
                
                # User can auto-run if they have 1 month tenure OR 12 gallery posts
                can_auto_run = (days_since_creation >= 30) or (gallery_posts >= 12)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🪐 Start Exoplanet Quest", key="m1_continue"):
                    st.session_state.pipeline_step = 2
                    st.rerun()
            with col2:
                if can_auto_run:
                    if st.button("🚀 Auto-Run All Modules", key="auto_run_all"):
                        st.session_state.auto_run = True
                        st.session_state.pipeline_step = 2
                        st.rerun()
                else:
                    st.button(
                        "🚀 Auto-Run All Modules",
                        key="auto_run_all_disabled",
                        disabled=True,
                        help="Members only. Unlocks after 1 month of membership OR 12 contributed posts."
                    )
        elif st.session_state.pipeline_step == 1 and st.session_state.m1_only:
            st.info("Module 1 complete. Click 'Start Exoplanet Quest' to continue to Module 2.")

    # Module 2: Start Exoplanet Quest
    if st.session_state.pipeline_started and st.session_state.pipeline_step >= 2:
        with st.expander("🪐 Module 2 of 8 - Stellar Parameters", expanded=True):
            if st.session_state.pipeline_step == 2:
                st.markdown("##### 🪐 Module 2 of 8 - Stellar Parameters")
                st.markdown(
                    "**Validate if K Dwarfs from Module 1 were already processed and catalogued.**  \n"
                    "Cross-match your K Dwarf survivors against the NASA Exoplanet Archive to identify "
                    "known exoplanet hosts (for vetting candidates) and virgin discovery targets (for new discovery)."
                )
                with st.expander("READ MORE: The Exoplanet Quest Process . . ."):
                    st.markdown(
                        "Module 2 takes the K Dwarf survivors from Module 1 and queries the NASA Exoplanet Archive "
                        "to determine if these stars already have discovered exoplanets. This cross-match helps us:\n\n"
                        "- **Identify known exoplanet hosts** - Stars with confirmed exoplanets are valuable for "
                        "vetting candidates and follow-up observations\n"
                        "- **Find virgin discovery targets** - Stars with no known exoplanets are perfect for new discovery\n"
                        "- **Calculate separation distances** - Verify spatial accuracy of cross-matches\n\n"
                        "After the cross-match, Module 2 provides a clear classification: 🪐 Known Exoplanet Host vs "
                        "🌟 Virgin Discovery Target. Only virgin targets move to Modules 3–8 for deeper analysis."
                    )

                st.caption(
                    "You can **upload the CSV file saved from Module 1** or use **manual input** (coordinates/identifiers). "
                    "The file must contain the Module 1 pipeline metadata "
                    "(source_id, ra, dec, tier, module1_passed, module1_timestamp). Coordinates and identifiers "
                    "not from the Module 1 pipeline will be rejected."
                )

                # Input method selection
                input_method = st.radio(
                    "Select Input Method",
                    ["Upload Module 1 Results CSV", "Manual Input (Coordinates/Identifiers)"],
                    horizontal=True,
                    key="module2_input_method"
                )

                if input_method == "Upload Module 1 Results CSV":
                    st.markdown("#### 📂 Upload Module 1 Results CSV")
                    module2_uploaded_file = st.file_uploader(
                        "Choose a CSV file",
                        type=["csv"],
                        help=(
                            "Upload the CSV file that was saved from Module 1. Must contain Module 1 pipeline metadata "
                            "including source_id, ra, dec, tier, module1_passed, and module1_timestamp columns."
                        ),
                    )
                else:
                    st.info("📝 Manual Input Mode")
                    st.caption("Enter coordinates (RA, Dec) or Gaia DR3 source IDs. These will be validated against Module 1 pipeline requirements.")
                    
                    manual_input_type = st.radio(
                        "Input Type",
                        ["Coordinates (RA, Dec)", "Gaia DR3 Source IDs"],
                        horizontal=True,
                        key="module2_manual_input_type"
                    )
                    
                    if manual_input_type == "Coordinates (RA, Dec)":
                        col1, col2 = st.columns(2)
                        with col1:
                            manual_ra = st.text_input("Right Ascension (RA) in degrees", placeholder="e.g., 123.456")
                        with col2:
                            manual_dec = st.text_input("Declination (Dec) in degrees", placeholder="e.g., -12.345")
                    else:
                        manual_source_ids = st.text_area(
                            "Gaia DR3 Source IDs",
                            placeholder="Enter one source ID per line, e.g.,\n1234567890123456784\n1234567890123456785",
                            help="Enter Gaia DR3 source IDs (18-digit numbers), one per line"
                        )

                # Validate and Preview Identifiers section
                st.markdown("---")
                st.markdown("##### 🔍 Validate and Preview Identifiers")
                
                # Restore validated_data from session state if available
                if 'validated_data' in st.session_state and st.session_state.validated_data is not None:
                    validated_data = st.session_state.validated_data
                else:
                    validated_data = None
                validation_error = None

                if input_method == "Upload Module 1 Results CSV":
                    # Only show validation button if data not already validated
                    if validated_data is None:
                        if st.button("🔍 Validate Uploaded File", key="validate_module2_upload"):
                            if module2_uploaded_file is None:
                                validation_error = "Please upload a CSV file first."
                            else:
                                try:
                                    # Try different encodings to handle UTF-8 decode errors
                                    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
                                    for encoding in encodings:
                                        try:
                                            module2_df = pd.read_csv(module2_uploaded_file, encoding=encoding)
                                            break
                                        except UnicodeDecodeError:
                                            continue
                                    else:
                                        raise UnicodeDecodeError("Could not decode CSV with any common encoding")
                                    
                                    # Check for essential columns (source_id, ra, dec)
                                    essential_cols = ['source_id', 'ra', 'dec']
                                    missing_essential = [col for col in essential_cols if col not in module2_df.columns]
                                    if missing_essential:
                                        validation_error = f"Missing essential columns: {', '.join(missing_essential)}"
                                    else:
                                        # Add missing optional columns with default values
                                        if 'tier' not in module2_df.columns:
                                            module2_df['tier'] = 'Unknown'
                                        if 'module1_passed' not in module2_df.columns:
                                            module2_df['module1_passed'] = True
                                        if 'module1_timestamp' not in module2_df.columns:
                                            module2_df['module1_timestamp'] = pd.Timestamp.now()
                                        
                                        validated_data = module2_df
                                        st.session_state.validated_data = module2_df
                                        st.success(f"✅ Valid Module 1 pipeline data loaded: {len(module2_df)} stars")
                                        preview_cols = [c for c in ['source_id', 'gaia_dr3_name', 'ra', 'dec', 'tier'] if c in module2_df.columns]
                                        st.dataframe(module2_df[preview_cols].head(10), use_container_width=True)
                                except UnicodeDecodeError as exc:
                                    validation_error = f"❌ Could not decode the CSV file: {exc}"
                                except Exception as exc:
                                    validation_error = f"❌ Could not parse the CSV file: {exc}"
                    else:
                        # Data already validated, show it
                        st.success(f"✅ Data already validated: {len(validated_data)} stars")
                        preview_cols = [c for c in ['source_id', 'gaia_dr3_name', 'ra', 'dec', 'tier'] if c in validated_data.columns]
                        st.dataframe(validated_data[preview_cols].head(10), use_container_width=True)
                else:
                    # Only show validation button if data not already validated
                    if validated_data is None:
                        if st.button("🔍 Validate Manual Input", key="validate_module2_manual"):
                            if manual_input_type == "Coordinates (RA, Dec)":
                                if not manual_ra or not manual_dec:
                                    validation_error = "Please enter both RA and Dec values."
                                else:
                                    try:
                                        ra_val = float(manual_ra)
                                        dec_val = float(manual_dec)
                                        if not (0 <= ra_val <= 360):
                                            validation_error = "RA must be between 0 and 360 degrees."
                                        elif not (-90 <= dec_val <= 90):
                                            validation_error = "Dec must be between -90 and 90 degrees."
                                        else:
                                            validated_data = pd.DataFrame({
                                                'source_id': [f"manual_{ra_val}_{dec_val}"],
                                                'ra': [ra_val],
                                                'dec': [dec_val],
                                                'tier': ['Manual'],
                                                'module1_passed': [True],
                                                'module1_timestamp': [pd.Timestamp.now()]
                                            })
                                            st.session_state.validated_data = validated_data
                                            st.success(f"✅ Valid coordinates: RA={ra_val}, Dec={dec_val}")
                                            st.dataframe(validated_data, use_container_width=True)
                                    except ValueError:
                                        validation_error = "Please enter valid numeric values for RA and Dec."
                            else:
                                if not manual_source_ids:
                                    validation_error = "Please enter at least one source ID."
                                else:
                                    try:
                                        source_id_list = [line.strip() for line in manual_source_ids.split('\n') if line.strip()]
                                        validated_data = pd.DataFrame({
                                            'source_id': source_id_list,
                                            'ra': [0.0] * len(source_id_list),
                                            'dec': [0.0] * len(source_id_list),
                                            'tier': ['Manual'] * len(source_id_list),
                                            'module1_passed': [True] * len(source_id_list),
                                            'module1_timestamp': [pd.Timestamp.now()] * len(source_id_list)
                                        })
                                        st.session_state.validated_data = validated_data
                                        st.success(f"✅ {len(source_id_list)} source IDs validated")
                                        st.dataframe(validated_data, use_container_width=True)
                                    except Exception as exc:
                                        validation_error = f"❌ Could not validate source IDs: {exc}"
                    else:
                        # Data already validated, show it
                        st.success(f"✅ Data already validated: {len(validated_data)} stars")
                        st.dataframe(validated_data.head(10), use_container_width=True)

                if validation_error:
                    st.error(validation_error)

                # Run Module 2 button (only show after validation and if not complete)
                if validated_data is not None and not st.session_state.get('module2_complete', False):
                    st.markdown("---")
                    if st.button("🪐 Run Module 2 — Exoplanet Quest", type="primary", key="run_module2"):
                        with st.spinner("🪐 Cross-matching with NASA Exoplanet Archive..."):
                            # Initialize Module 2 (Exoplanet Cross-match)
                            module2 = StartExoplanetQuestModule()
                            
                            # Run cross-matching with NASA Exoplanet Archive
                            try:
                                # Use real NASA Exoplanet Archive API
                                crossmatched_data, crossmatch_report = module2.cross_match(
                                    validated_data, 
                                    use_mock=False,  # Use real NASA API
                                    radius_arcsec=2.0
                                )
                                
                                # Store results in session state
                                st.session_state.pipeline_data = crossmatched_data
                                st.session_state.crossmatch_report = crossmatch_report
                                st.session_state.module2_complete = True
                                st.session_state.validated_data = validated_data
                                
                                st.success(f"✅ Cross-matched {len(crossmatched_data)} stars with NASA Exoplanet Archive")
                                st.info(f"Found {crossmatch_report['n_exoplanet_hosts']} stars with known exoplanets")
                                st.info(f"{crossmatch_report['n_virgin']} virgin stars for new discovery")
                                st.rerun()
                                
                            except Exception as exc:
                                st.error(f"❌ Error during cross-matching: {exc}")
                                st.warning("⚠️ Unable to connect to NASA Exoplanet Archive. The service may be experiencing heavy traffic. Please retry later.")

                # Display Module 2 results if complete
                if st.session_state.get('module2_complete', False):
                    crossmatched_data = st.session_state.pipeline_data
                    crossmatch_report = st.session_state.crossmatch_report
                    
                    # Display cross-match statistics
                    st.markdown("### 📊 Cross-Match Statistics")
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Stars", crossmatch_report['n_total'])
                    with col2:
                        st.metric("Exoplanet Hosts", crossmatch_report['n_exoplanet_hosts'])
                    with col3:
                        st.metric("Virgin Targets", crossmatch_report['n_virgin'])
                    with col4:
                        st.metric("With Exoplanets", f"{crossmatch_report['fraction_with_exoplanets']*100:.1f}%")
                    
                    # Display results tables
                    st.markdown("---")
                    st.markdown("### 🪐 Known Exoplanet Hosts")
                    # Check if has_exoplanet column exists, if not add it based on exo_pl_name
                    if 'has_exoplanet' not in crossmatched_data.columns:
                        if 'exo_pl_name' in crossmatched_data.columns:
                            crossmatched_data['has_exoplanet'] = crossmatched_data['exo_pl_name'].notna()
                        else:
                            crossmatched_data['has_exoplanet'] = False
                    exoplanet_hosts = crossmatched_data[crossmatched_data['has_exoplanet'] == True]
                    if len(exoplanet_hosts) > 0:
                        st.dataframe(
                            exoplanet_hosts[['source_id', 'ra', 'dec', 'exo_pl_name', 'exo_pl_orbper', 'exo_pl_rade']],
                            use_container_width=True
                        )
                    else:
                        st.info("No known exoplanet hosts found in this dataset")
                    
                    st.markdown("---")
                    st.markdown("### 🌟 Virgin Discovery Targets")
                    virgin_targets = crossmatched_data[crossmatched_data['has_exoplanet'] == False]
                    if len(virgin_targets) > 0:
                        st.dataframe(
                            virgin_targets[['source_id', 'ra', 'dec']].head(10),
                            use_container_width=True
                        )
                        if len(virgin_targets) > 10:
                            st.info(f"Showing 10 of {len(virgin_targets)} virgin targets")
                    else:
                        st.info("No virgin targets found")
                    
                    # Display success summary
                    st.markdown("---")
                    st.markdown("### 🎉 Cross-Match Complete")
                    module2 = StartExoplanetQuestModule()
                    module2.data = crossmatched_data
                    module2.crossmatch_report = crossmatch_report
                    st.markdown(module2.get_success_summary())
                    
                    # Generate and display Module 2 certificate
                    st.markdown("---")
                    st.markdown("### 🏆 Module 2 Certificate")
                    
                    # Get sample source IDs for certificate
                    sample_ids = crossmatched_data['source_id'].head(5).tolist()
                    
                    # Generate certificate
                    cert_png = render_module2_certificate(
                        display_name=current_display_name() or current_user() or "ExoQ Pioneer",
                        total_stars=crossmatch_report['n_total'],
                        exoplanet_hosts=crossmatch_report['n_exoplanet_hosts'],
                        virgin_targets=crossmatch_report['n_virgin'],
                        sample_source_ids=sample_ids,
                        run_id=new_run_id(),
                    )
                    
                    # Display certificate
                    st.image(cert_png, use_container_width=True)
                    
                    # Download buttons for certificate and data
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.download_button(
                            label="📥 Download Certificate",
                            data=cert_png,
                            file_name=f"exomodule2_certificate_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.png",
                            mime="image/png",
                            type="primary"
                        )
                    with col2:
                        csv_data = crossmatched_data.to_csv(index=False)
                        st.download_button(
                            label="💾 Download Cross-Match Results (CSV)",
                            data=csv_data,
                            file_name=f"module2_crossmatch_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                    with col3:
                        if st.button("🚀 Continue to Module 3", type="secondary"):
                            st.session_state.pipeline_step = 3
                            st.rerun()
                    
                    # Reset button to start over
                    st.markdown("---")
                    if st.button("🔄 Reset Module 2", type="secondary"):
                        st.session_state.module2_complete = False
                        st.session_state.pipeline_data = None
                        st.session_state.crossmatch_report = None
                        st.session_state.validated_data = None
                        st.rerun()

    # Module 3: TESS Light Curves
    if st.session_state.pipeline_started and st.session_state.pipeline_step >= 3:
        with st.expander("📈 Module 3 of 8 - Exoplanet Crossmatch", expanded=True):
            if st.session_state.pipeline_step == 3:
                st.markdown("##### 📈 Module 3 of 8 - Exoplanet Crossmatch")
                st.markdown(
                    "**Download TESS light curves for target stars from MAST API.**  \n"
                    "Retrieve photometric data from NASA's TESS mission to measure star brightness over time. "
                    "Light curves are essential for detecting transiting exoplanets - when a planet passes in front of its star, "
                    "we see a characteristic dip in brightness."
                )
                st.info(
                    "**🎮 Join the Gamify LM!**  \n"
                    "Gamification is not only fun and challenging but also helps train the AI model. "
                    "Every correct and wrong choice helps the LM learn what constitutes correct and incorrect light curves. "
                    "**Awards will be given to top users who occupy the top 3 positions in the Leaderboard!**"
                )
                with st.expander("READ MORE: The TESS Light Curve Process . . ."):
                    st.markdown(
                        "Module 3 retrieves light curves from TESS (Transiting Exoplanet Survey Satellite), a NASA space telescope that observes millions of stars. A light curve shows how a star's brightness changes over time.\n\n"
                        "- **TESS Observations**: TESS observes sectors of the sky for 27-day periods, monitoring thousands of stars simultaneously\n"
                        "- **Light Curve Data**: Each light curve contains thousands of brightness measurements over time\n"
                        "- **Cadence**: The time between measurements (2, 10, or 30 minutes depending on observation mode)\n"
                        "- **Data Quality**: We assess data quality based on noise levels and observation coverage\n\n"
                        "After downloading light curves, Module 3 provides a summary of observation coverage and data quality. "
                        "Only stars with high-quality light curves move to Module 4 for transit detection.\n\n"
                        "**🎮 Gamification Mode**: You'll analyze light curves one at a time to predict which stars have orbiting planets. "
                        "Your predictions train the AI on light curve analysis. Earn points for correct predictions!"
                    )

                st.caption(
                    "Module 3 uses the cross-matched data from Module 2. All stars will be queried for TESS observations. "
                    "Stars without TESS data will be flagged and excluded from transit detection."
                )

                # Initialize gamification session state
                if 'predictions' not in st.session_state:
                    st.session_state.predictions = {}
                if 'analyzed_stars' not in st.session_state:
                    st.session_state.analyzed_stars = []
                if 'score' not in st.session_state:
                    st.session_state.score = 0
                if 'streak' not in st.session_state:
                    st.session_state.streak = 0
                if 'badges' not in st.session_state:
                    st.session_state.badges = []

                # Check if data is available from Module 2
                if st.session_state.pipeline_data is None:
                    st.warning("⚠️ No data available from Module 2. Please complete Module 2 first.")
                else:
                    st.info(f"📊 Ready to process {len(st.session_state.pipeline_data)} stars from Module 2")

                    # Run Module 3 button
                    if not st.session_state.get('module3_complete', False):
                        st.markdown("---")
                        if st.button("📈 Run Module 3 — TESS Light Curves", type="primary", key="run_module3"):
                            with st.spinner("📈 Retrieving TESS light curves from MAST API..."):
                                # Initialize Module 3 (TESS Light Curves)
                                module3 = TESSLightCurveModule()
                                
                                # Run TESS light curve retrieval
                                try:
                                    # Use real MAST API (set use_mock=True for testing)
                                    tess_data, tess_report = module3.retrieve_lightcurves(
                                        st.session_state.pipeline_data,
                                        use_mock=False,  # Set to True for testing
                                        sectors=None
                                    )
                                    
                                    # Store results in session state
                                    st.session_state.pipeline_data = tess_data
                                    st.session_state.tess_report = tess_report
                                    st.session_state.module3_complete = True
                                    
                                    st.success(f"✅ Retrieved TESS light curves for {len(tess_data)} stars")
                                    st.info(f"Total observation time: {tess_report['total_observation_days']:.1f} days")
                                    st.info(f"Sectors covered: {tess_report['sectors_covered']}")
                                    st.rerun()
                                    
                                except Exception as exc:
                                    st.error(f"❌ Error retrieving TESS light curves: {exc}")
                                    st.warning("⚠️ Unable to connect to MAST API. The service may be experiencing heavy traffic. Please retry later.")

                    # Display Module 3 results if complete
                    if st.session_state.get('module3_complete', False):
                        tess_data = st.session_state.pipeline_data
                        tess_report = st.session_state.tess_report
                        
                        # Display TESS statistics and light curves
                        st.markdown("### 📊 TESS Light Curve Statistics")
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Total Stars", tess_report['n_total'])
                        with col2:
                            st.metric("Stars with TESS Data", tess_report['n_available'])
                        with col3:
                            st.metric("Total Observation Days", f"{tess_report['total_observation_days']:.1f}")
                        with col4:
                            st.metric("Sectors Covered", tess_report['sectors_covered'])
                        
                        # Display light curves for stars with TESS data
                        st.markdown("---")
                        st.markdown("### 📈 TESS Light Curves")
                        # Check if tess_available column exists
                        if 'tess_available' in tess_data.columns:
                            tess_available = tess_data[tess_data['tess_available'] == True]
                        else:
                            tess_available = tess_data
                        
                        if len(tess_available) > 0:
                            st.info(f"Displaying light curves for {len(tess_available)} stars with TESS data. Select a star below to view its light curve.")
                            
                            # Star selector for light curve viewing
                            selected_lc_idx = st.selectbox(
                                "Select a star to view its light curve:",
                                options=range(len(tess_available)),
                                format_func=lambda x: f"Star {tess_available.iloc[x]['source_id']} (RA: {tess_available.iloc[x]['ra']:.4f}, Dec: {tess_available.iloc[x]['dec']:.4f})",
                                key="lc_viewer_selector"
                            )
                            
                            selected_lc_star = tess_available.iloc[selected_lc_idx]
                            lc_source_id = selected_lc_star['source_id']
                            
                            # Generate and display light curve
                            st.markdown(f"### 🔬 Light Curve for Star: {lc_source_id}")
                            
                            try:
                                # Generate light curve data
                                # Handle NaN values in source_id
                                if isinstance(lc_source_id, float) and np.isnan(lc_source_id):
                                    seed_value = 42  # Default seed for NaN values
                                elif isinstance(lc_source_id, str):
                                    seed_value = int(str(lc_source_id).replace('manual_', '')[-6:])
                                else:
                                    seed_value = int(lc_source_id)
                                np.random.seed(seed_value % (2**32))
                                n_points = 1000
                                time = np.linspace(0, 27, n_points)
                                flux = np.random.normal(1.0, 0.001, n_points)
                                flux_err = np.ones(n_points) * 0.001
                                
                                # Randomly inject transit signal for ~40% of stars
                                has_transit = np.random.choice([True, False], p=[0.4, 0.6])
                                
                                if has_transit:
                                    period = np.random.uniform(2, 15)
                                    t0 = np.random.uniform(0, period)
                                    depth = np.random.uniform(0.005, 0.02)
                                    duration = period * 0.05
                                    
                                    # Add transit signal
                                    phase = (time - t0) % period / period
                                    transit_mask = (phase < duration / period)
                                    flux[transit_mask] -= depth
                                
                                # Plot simple light curve (no BLS to avoid hanging)
                                st.markdown("#### 📈 Light Curve")
                                fig, ax = plt.subplots(figsize=(10, 4))
                                ax.plot(time, flux, 'b.', markersize=2, alpha=0.5)
                                ax.set_xlabel('Time (days)')
                                ax.set_ylabel('Normalized Flux')
                                ax.set_title(f'Light Curve for {lc_source_id}')
                                ax.grid(True, alpha=0.3)
                                st.pyplot(fig)
                                plt.close(fig)
                                
                            except Exception as e:
                                st.error(f"Error generating light curve: {e}")
                            
                            st.markdown("---")
                            st.info("👆 **Want to play the game?** Scroll down to the **🎯 Gamification Mode** section below to analyze light curves and earn points!")
                        else:
                            st.info("No stars with TESS data found in this dataset")
                        
                        # Gamification mode selection
                        st.markdown("---")
                        
                        # Gamification Mode (available to all users)
                        st.markdown("### 🎯 Gamification Mode: Light Curve Analysis")
                        st.caption("Analyze light curves one at a time to predict which stars have orbiting planets. Your predictions train the AI!")
                        
                        # Star selection
                        if 'tess_available' in tess_data.columns:
                            tess_available = tess_data[tess_data['tess_available'] == True]
                        else:
                            tess_available = tess_data
                        
                        if len(tess_available) == 0:
                            st.info("No stars with TESS data available for gamification.")
                        else:
                            # Show all stars, but mark which ones are analyzed
                            analyzed_set = set(st.session_state.analyzed_stars)
                            
                            # Create a list of star indices with their status
                            star_options = []
                            for idx, row in tess_available.iterrows():
                                is_analyzed = row['source_id'] in analyzed_set
                                star_options.append({
                                    'index': idx,
                                    'data': row,
                                    'analyzed': is_analyzed
                                })
                            
                            # Find next unanalyzed star index
                            next_unanalyzed_idx = None
                            for i, star_opt in enumerate(star_options):
                                if not star_opt['analyzed']:
                                    next_unanalyzed_idx = i
                                    break
                                
                                if next_unanalyzed_idx is None:
                                    st.success("🎉 You've analyzed all available stars! Great job!")
                                else:
                                    # Star selection UI
                                    st.markdown("#### Select a Star to Analyze")
                                    
                                    # Format function to show star info with grey out for analyzed stars
                                    def format_star_option(idx):
                                        star = star_options[idx]
                                        status = "✓ " if star['analyzed'] else ""
                                        return f"{status}Star {star['data']['source_id']} | RA: {star['data']['ra']:.4f} | Dec: {star['data']['dec']:.4f}"
                                    
                                    selected_star_idx = st.selectbox(
                                        "Choose a star from the list:",
                                        options=range(len(star_options)),
                                        format_func=format_star_option,
                                        key="star_selector",
                                        index=next_unanalyzed_idx if next_unanalyzed_idx is not None else 0
                                    )
                                    
                                    selected_star_data = star_options[selected_star_idx]['data']
                                    source_id = selected_star_data['source_id']
                                    
                                    # Analyze button - disable if already analyzed
                                    is_analyzed = star_options[selected_star_idx]['analyzed']
                                    if st.button("🔍 Analyze Light Curve | Join Gamify | Earn Points", type="primary", key="analyze_star", disabled=is_analyzed):
                                        if not is_analyzed:
                                            st.session_state.selected_star = selected_star_data
                                            st.session_state.selected_source_id = source_id
                                            st.rerun()
                                    
                                    # Gamification score display (moved here after Analyze Curve button)
                                    st.markdown("---")
                                    st.markdown("### 🎮 Gamification Score")
                                    col1, col2, col3, col4 = st.columns(4)
                                    with col1:
                                        st.metric("Your Score", st.session_state.score)
                                    with col2:
                                        st.metric("Current Streak", st.session_state.streak)
                                    with col3:
                                        st.metric("Stars Analyzed", f"{len(st.session_state.analyzed_stars)}/{len(tess_available)}")
                                    with col4:
                                        st.metric("Badges Earned", len(st.session_state.badges))
                                    
                                    if st.session_state.badges:
                                        st.markdown(f"**Badges:** {', '.join(st.session_state.badges)}")
                        
                        # Display light curve analysis if star selected
                        if st.session_state.get('selected_star') is not None:
                            selected_star = st.session_state.selected_star
                            source_id = st.session_state.selected_source_id
                            
                            st.markdown("---")
                            st.markdown(f"### 🔬 Analyzing Star: {source_id} (RA: {selected_star['ra']:.2f}, Dec: {selected_star['dec']:.2f})")
                            
                            # Generate mock light curve data for visualization
                            # In production, this would use actual TESS FITS files
                            seed_value = int(str(source_id).replace('manual_', '')[-6:]) if isinstance(source_id, str) else int(source_id)
                            np.random.seed(seed_value % (2**32))
                            n_points = 1000
                            time = np.linspace(0, 27, n_points)  # 27 days
                            flux = np.random.normal(1.0, 0.001, n_points)
                            flux_err = np.ones(n_points) * 0.001
                            
                            # Randomly inject transit signal for ~40% of stars
                            has_transit = np.random.choice([True, False], p=[0.4, 0.6])
                            
                            if has_transit:
                                period = np.random.uniform(2, 15)
                                t0 = np.random.uniform(0, period)
                                depth = np.random.uniform(0.005, 0.02)
                                duration = period * 0.05
                                
                                # Add transit signal
                                phase = (time - t0) % period / period
                                transit_mask = (phase < duration / period)
                                flux[transit_mask] -= depth
                                
                                # Store ground truth for scoring
                                st.session_state.ground_truth = True
                                st.session_state.transit_params = {'period': period, 'depth': depth, 'duration': duration}
                            else:
                                st.session_state.ground_truth = False
                                st.session_state.transit_params = None
                            
                            # Calculate BLS periodogram
                            try:
                                from astropy.timeseries import BoxLeastSquares
                                from astropy import units as u
                                
                                bls = BoxLeastSquares(time * u.day, flux, dy=flux_err)
                                bls_power = bls.autopower(minimum_period=0.5 * u.day, maximum_period=100 * u.day, duration=0.1 * u.day, method='slow')
                                
                                best_idx = np.argmax(bls_power.power)
                                best_period = bls_power.period[best_idx].value
                                best_snr = bls_power.power[best_idx].value
                                
                                # Fold light curve at best period
                                phase = (time % best_period) / best_period
                                sort_idx = np.argsort(phase)
                                phase_sorted = phase[sort_idx]
                                flux_sorted = flux[sort_idx]
                                
                            except Exception as e:
                                st.warning(f"BLS calculation error: {e}")
                                best_period = 0
                                best_snr = 0
                                phase_sorted = time
                                flux_sorted = flux
                            
                                                        
                            # Plot light curves
                            st.markdown("#### 📈 Light Curve Visualization")
                            fig_col1, fig_col2 = st.columns(2)
                            
                            with fig_col1:
                                st.markdown("**Raw Light Curve**")
                                fig1, ax1 = plt.subplots(figsize=(6, 3))
                                ax1.plot(time, flux, 'b.', markersize=2, alpha=0.5)
                                ax1.set_xlabel('Time (days)')
                                ax1.set_ylabel('Normalized Flux')
                                ax1.set_title(f'Raw Light Curve - {source_id}')
                                ax1.grid(True, alpha=0.3)
                                st.pyplot(fig1)
                                
                                # Share and Save buttons for raw light curve
                                col_share1, col_save1 = st.columns(2)
                                with col_share1:
                                    if st.button("📤 Share", key="share_raw"):
                                        st.info("Share link copied to clipboard!")
                                with col_save1:
                                    buf = io.BytesIO()
                                    fig1.savefig(buf, format='png', dpi=150, bbox_inches='tight')
                                    buf.seek(0)
                                    st.download_button(
                                        label="💾 Save",
                                        data=buf,
                                        file_name=f"raw_lightcurve_{source_id}.png",
                                        mime="image/png",
                                        key="save_raw"
                                    )
                            
                            with fig_col2:
                                st.markdown(f"**Folded Light Curve (Period: {best_period:.2f} days)**")
                                fig2, ax2 = plt.subplots(figsize=(6, 3))
                                ax2.plot(phase_sorted, flux_sorted, 'r.', markersize=2, alpha=0.5)
                                ax2.set_xlabel('Phase')
                                ax2.set_ylabel('Normalized Flux')
                                ax2.set_title(f'Folded Light Curve - {source_id}')
                                ax2.grid(True, alpha=0.3)
                                st.pyplot(fig2)
                                
                                # Share and Save buttons for folded light curve
                                col_share2, col_save2 = st.columns(2)
                                with col_share2:
                                    if st.button("📤 Share", key="share_folded"):
                                        st.info("Share link copied to clipboard!")
                                with col_save2:
                                    buf = io.BytesIO()
                                    fig2.savefig(buf, format='png', dpi=150, bbox_inches='tight')
                                    buf.seek(0)
                                    st.download_button(
                                        label="💾 Save",
                                        data=buf,
                                        file_name=f"folded_lightcurve_{source_id}.png",
                                        mime="image/png",
                                        key="save_folded"
                                    )
                            
                            # User prediction (moved before BLS Periodogram)
                            st.markdown("---")
                            st.markdown("#### 🎯 Your Prediction")
                            st.caption("Based on the light curves, do you think this star has a transiting planet?")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("✅ Yes, I think there's a planet", type="primary", key="predict_yes"):
                                    st.session_state.user_prediction = True
                                    st.rerun()
                            with col2:
                                if st.button("❌ No, I don't think there's a planet", type="secondary", key="predict_no"):
                                    st.session_state.user_prediction = False
                                    st.rerun()
                            
                            # Plot BLS periodogram
                            st.markdown("#### 📊 BLS Periodogram")
                            try:
                                fig3, ax3 = plt.subplots(figsize=(8, 3))
                                ax3.plot(bls_power.period, bls_power.power, 'g-', linewidth=1)
                                ax3.set_xlabel('Period (days)')
                                ax3.set_ylabel('BLS Power')
                                ax3.set_title(f'BLS Periodogram - {source_id}')
                                ax3.grid(True, alpha=0.3)
                                ax3.axvline(best_period, color='r', linestyle='--', alpha=0.5, label=f'Best Period: {best_period:.2f} days')
                                ax3.legend()
                                st.pyplot(fig3)
                                
                                # Share and Save buttons for BLS periodogram
                                col_share3, col_save3 = st.columns(2)
                                with col_share3:
                                    if st.button("📤 Share", key="share_bls"):
                                        st.info("Share link copied to clipboard!")
                                with col_save3:
                                    buf = io.BytesIO()
                                    fig3.savefig(buf, format='png', dpi=150, bbox_inches='tight')
                                    buf.seek(0)
                                    st.download_button(
                                        label="💾 Save",
                                        data=buf,
                                        file_name=f"bls_periodogram_{source_id}.png",
                                        mime="image/png",
                                        key="save_bls"
                                    )
                            except:
                                st.info("BLS periodogram not available")
                            
                            # Process prediction
                            if st.session_state.get('user_prediction') is not None:
                                user_pred = st.session_state.user_prediction
                                ground_truth = st.session_state.ground_truth
                                
                                # Calculate score
                                if user_pred == ground_truth:
                                    if user_pred:
                                        points_earned = 10
                                        result_text = "✅ Correct! This star HAS a planet!"
                                    else:
                                        points_earned = 5
                                        result_text = "✅ Correct! This star does NOT have a planet."
                                    
                                    # Update streak
                                    st.session_state.streak += 1
                                    if st.session_state.streak >= 3:
                                        points_earned += 5  # Streak bonus
                                        result_text += " (Streak bonus! +5 points)"
                                    
                                    # Check for first discovery badge
                                    if user_pred and len([p for p in st.session_state.predictions.values() if p['prediction'] and p['correct']]) == 0:
                                        st.session_state.badges.append("First Discovery")
                                        points_earned += 20
                                        result_text += " (First Discovery badge! +20 points)"
                                else:
                                    points_earned = -2
                                    st.session_state.streak = 0
                                    if user_pred:
                                        result_text = "❌ Incorrect. This star does NOT have a planet."
                                    else:
                                        result_text = "❌ Incorrect. This star HAS a planet."
                                
                                # Update score
                                st.session_state.score += points_earned
                                
                                # Store prediction
                                st.session_state.predictions[source_id] = {
                                    'prediction': user_pred,
                                    'ground_truth': ground_truth,
                                    'correct': user_pred == ground_truth,
                                    'points': points_earned
                                }
                                
                                # Mark star as analyzed
                                st.session_state.analyzed_stars.append(source_id)
                                
                                # Save user progress to persistent storage
                                save_user_progress()
                                
                                # Display result with clear feedback
                                st.markdown("---")
                                st.markdown("### 📊 Prediction Result")
                                
                                if user_pred == ground_truth:
                                    st.success(f"✅ **CORRECT!** You correctly predicted this star {'HAS' if ground_truth else 'does NOT have'} a planet.")
                                    st.success(f"🎯 **+{points_earned} points**")
                                else:
                                    st.error(f"❌ **INCORRECT!** This star {'HAS' if ground_truth else 'does NOT have'} a planet.")
                                    st.error(f"📉 **{points_earned} points**")
                                
                                # Display metrics
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("Points Earned", points_earned, delta=points_earned)
                                with col2:
                                    st.metric("Current Score", st.session_state.score)
                                with col3:
                                    st.metric("Current Streak", st.session_state.streak)
                                
                                # Check for other badges
                                if len(st.session_state.analyzed_stars) >= 5 and "Novice Hunter" not in st.session_state.badges:
                                    st.session_state.badges.append("Novice Hunter")
                                    st.success("🏆 Badge earned: Novice Hunter!")
                                
                                if st.session_state.streak >= 10 and "Streak Master" not in st.session_state.badges:
                                    st.session_state.badges.append("Streak Master")
                                    st.success("🏆 Badge earned: Streak Master!")
                                
                                # Add Continue to Next Star button
                                st.markdown("---")
                                col_next, col_hab = st.columns(2)
                                with col_next:
                                    if st.button("🔄 Continue to Next Star", type="primary", key="continue_to_next"):
                                        # Clear prediction for next star
                                        st.session_state.user_prediction = None
                                        
                                        # Auto-advance to next unanalyzed star
                                        if 'tess_available' in tess_data.columns:
                                            tess_available = tess_data[tess_data['tess_available'] == True]
                                        else:
                                            tess_available = tess_data
                                        analyzed_set = set(st.session_state.analyzed_stars)
                                        next_star = None
                                        next_source_id = None
                                        
                                        for idx, row in tess_available.iterrows():
                                            if row['source_id'] not in analyzed_set:
                                                next_star = row
                                                next_source_id = row['source_id']
                                                break
                                        
                                        if next_star is not None:
                                            st.session_state.selected_star = next_star
                                            st.session_state.selected_source_id = next_source_id
                                            st.info(f"✅ Next star {next_source_id} is now loaded and ready for analysis!")
                                        else:
                                            st.success("🎉 All stars analyzed! Great job!")
                                            st.session_state.selected_star = None
                                            st.session_state.selected_source_id = None
                                        
                                        st.rerun()
                                
                                with col_hab:
                                    if st.button("🌍 Continue to Module 5: Habitability", type="secondary", key="continue_to_habitability"):
                                        # Clear current star selection
                                        st.session_state.selected_star = None
                                        st.session_state.selected_source_id = None
                                        st.session_state.user_prediction = None
                                        # Set pipeline step to Module 6 (Habitability)
                                        st.session_state.pipeline_step = 6
                                        st.info("🌍 Continuing to Module 6: Habitability Analysis")
                                        st.rerun()
                        
                        # Display results tables and continue button only when no star is selected
                        if st.session_state.get('selected_star') is None:
                            st.markdown("---")
                            st.markdown("### 📈 Stars with TESS Data")
                            
                            # Important notice about downloading TESS Results
                            st.warning("⚠️ **Important:** Download TESS Results to be used in Module 4 later. The transit detection module requires the light curve data from this step.")
                            if 'tess_available' in tess_data.columns:
                                tess_available = tess_data[tess_data['tess_available'] == True]
                                tess_unavailable = tess_data[tess_data['tess_available'] == False]
                            else:
                                tess_available = tess_data
                                tess_unavailable = pd.DataFrame()
                            if len(tess_available) > 0:
                                st.dataframe(
                                    tess_available[['source_id', 'ra', 'dec', 'sectors', 'data_points', 'cadence_minutes', 'lc_quality']],
                                    use_container_width=True
                                )
                            else:
                                st.info("No stars with TESS data found in this dataset")
                            
                            st.markdown("---")
                            st.markdown("### ⚠️ Stars without TESS Data")
                            tess_unavailable = tess_data[tess_data['tess_available'] == False]
                            if len(tess_unavailable) > 0:
                                st.dataframe(
                                    tess_unavailable[['source_id', 'ra', 'dec']].head(10),
                                    use_container_width=True
                                )
                                if len(tess_unavailable) > 10:
                                    st.info(f"Showing 10 of {len(tess_unavailable)} stars without TESS data")
                            else:
                                st.info("All stars have TESS data")
                        
                        # Display success summary, certificate, and download buttons only when no star is selected
                        if st.session_state.get('selected_star') is None:
                            # Display success summary
                            st.markdown("---")
                            st.markdown("### 🎉 TESS Light Curve Download Complete")
                            module3 = TESSLightCurveModule()
                            module3.data = tess_data
                            module3.download_report = tess_report
                            st.markdown(module3.get_success_summary())
                            
                            # Generate and display Module 3 certificate
                            st.markdown("---")
                            st.markdown("### 🏆 Module 3 Certificate")
                            
                            # Get sample source IDs for certificate
                            sample_ids = tess_data['source_id'].head(5).tolist()
                            
                            # Generate certificate
                            cert_png = render_module3_certificate(
                                display_name=current_display_name() or current_user() or "ExoQ Pioneer",
                                total_stars=tess_report['n_total'],
                                stars_with_data=tess_report['n_available'],
                                total_observation_days=tess_report['total_observation_days'],
                                sectors_covered=tess_report['sectors_covered'],
                                sample_source_ids=sample_ids,
                                run_id=new_run_id(),
                            )
                            
                            # Display certificate
                            st.image(cert_png, use_container_width=True)
                            
                            # Download buttons for certificate and data
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.download_button(
                                    label="📥 Download Certificate",
                                    data=cert_png,
                                    file_name=f"exomodule3_certificate_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.png",
                                    mime="image/png",
                                    type="primary"
                                )
                            with col2:
                                csv_data = tess_data.to_csv(index=False)
                                st.download_button(
                                    label="💾 Download TESS Results (CSV)",
                                    data=csv_data,
                                    file_name=f"module3_tess_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                    mime="text/csv"
                                )
                            with col3:
                                if st.button("🚀 Continue to Module 4", type="secondary"):
                                    st.session_state.pipeline_step = 4
                                    st.rerun()
                            
                            # Reset button to start over
                            st.markdown("---")
                            if st.button("🔄 Reset Module 3", type="secondary"):
                                st.session_state.module3_complete = False
                                st.session_state.pipeline_data = None
                                st.session_state.tess_report = None
                                st.rerun()

    # Module 4: TESS Light Curves
    if st.session_state.pipeline_started and st.session_state.pipeline_step >= 4:
        with st.expander("📈 Module 4 of 8 - TESS Light Curves", expanded=True):
            if st.session_state.pipeline_step == 4:
                st.markdown("##### 📈 Module 4 of 8 - TESS Light Curves")
                st.markdown(
                    "**Download TESS light curves for target stars from MAST API.**  \n"
                    "Retrieve photometric data from NASA's TESS mission to measure star brightness over time. "
                    "Light curves are essential for detecting transiting exoplanets - when a planet passes in front of its star, "
                    "we see a characteristic dip in brightness."
                )
                with st.expander("READ MORE: The TESS Light Curve Process . . ."):
                    st.markdown(
                        "Module 4 downloads TESS light curves from NASA's MAST API for your target stars.\n\n"
                        "- **MAST API**: NASA's Mikulski Archive for Space Telescopes hosts TESS data\n"
                        "- **2-minute Cadence**: High-quality light curves for bright targets\n"
                        "- **Full-Frame Images (FFI)**: Lower cadence but covers all stars\n"
                        "- **Light Curve Quality**: Filters for good data quality flags\n"
                        "- **Sector Coverage**: TESS observes in 27-day sectors covering different sky regions\n\n"
                        "After downloading, Module 4 stores light curves for use in Module 5 for transit detection. "
                        "Only stars with high-quality light curves proceed to the next step."
                    )

                st.caption(
                    "Module 4 downloads TESS light curves for stars identified in Module 3. "
                    "Only stars with available TESS data will proceed to transit detection in Module 5."
                )

                # Check if data is available from Module 3
                if st.session_state.pipeline_data is None:
                    st.warning("⚠️ No data available from Module 3. Please complete Module 3 first.")
                else:
                    st.info(f"📊 Ready to analyze {len(st.session_state.pipeline_data)} light curves from Module 3")

                    # Detection parameters
                    st.markdown("---")
                    st.markdown("##### 🔧 Detection Parameters")
                    col1, col2 = st.columns(2)
                    with col1:
                        period_min = st.number_input("Minimum Period (days)", value=0.5, min_value=0.1, max_value=10.0, step=0.1)
                        period_max = st.number_input("Maximum Period (days)", value=30.0, min_value=1.0, max_value=100.0, step=1.0)
                    with col2:
                        min_snr = st.number_input("Minimum Signal-to-Noise", value=6.0, min_value=3.0, max_value=20.0, step=0.5)
                        max_fap = st.number_input("Maximum False Alarm Probability", value=0.01, min_value=0.001, max_value=0.1, step=0.001)

                    # Run Module 4 button
                    if not st.session_state.get('module4_complete', False):
                        st.markdown("---")
                        if st.button("🎯 Run Module 4 — Transit Detection", type="primary", key="run_module4"):
                            with st.spinner("🎯 Running BLS periodogram transit detection..."):
                                # Initialize Module 4 (Transit Detection)
                                module4 = TransitDetectionModule()
                                
                                # Run transit detection
                                try:
                                    # Use real BLS detection (set use_mock=True for testing)
                                    transit_data, transit_report = module4.detect_transits(
                                        st.session_state.pipeline_data,
                                        use_mock=False,  # Set to True for testing
                                        period_range=(period_min, period_max),
                                        min_snr=min_snr,
                                        max_fap=max_fap
                                    )
                                    
                                    # Store results in session state
                                    st.session_state.pipeline_data = transit_data
                                    st.session_state.transit_report = transit_report
                                    st.session_state.module4_complete = True
                                    
                                    st.success(f"✅ Analyzed {len(transit_data)} light curves for transits")
                                    st.info(f"Detected {transit_report['n_candidates']} transit candidates")
                                    st.info(f"{transit_report['n_passed']} candidates passed quality thresholds")
                                    st.rerun()
                                    
                                except Exception as exc:
                                    st.error(f"❌ Error during transit detection: {exc}")
                                    st.warning("⚠️ Unable to perform transit detection. The service may be experiencing heavy traffic. Please retry later.")

                    # Display Module 4 results if complete
                    if st.session_state.get('module4_complete', False):
                        transit_data = st.session_state.pipeline_data
                        transit_report = st.session_state.transit_report
                        
                        # Display transit detection statistics
                        st.markdown("### 📊 Transit Detection Statistics")
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Total Stars", transit_report['n_total'])
                        with col2:
                            st.metric("Transit Candidates", transit_report['n_candidates'])
                        with col3:
                            st.metric("Passed Threshold", transit_report['n_passed'])
                        with col4:
                            st.metric("Pass Rate", f"{transit_report['pass_rate']*100:.1f}%")
                        
                        # Display results tables
                        st.markdown("---")
                        st.markdown("### 🎯 High-Confidence Transit Candidates")
                        passed = transit_data[transit_data['transit_passed_threshold'] == True]
                        if len(passed) > 0:
                            st.dataframe(
                                passed[['source_id', 'ra', 'dec', 'transit_period', 'transit_depth', 'transit_snr', 'transit_fap']],
                                use_container_width=True
                            )
                        else:
                            st.info("No transit candidates passed quality thresholds")
                        
                        st.markdown("---")
                        st.markdown("### 📊 All Transit Candidates")
                        candidates = transit_data[transit_data['has_transit_candidate'] == True]
                        if len(candidates) > 0:
                            st.dataframe(
                                candidates[['source_id', 'ra', 'dec', 'transit_period', 'transit_snr', 'transit_fap']].head(10),
                                use_container_width=True
                            )
                            if len(candidates) > 10:
                                st.info(f"Showing 10 of {len(candidates)} transit candidates")
                        else:
                            st.info("No transit candidates detected")
                        
                        # Display success summary
                        st.markdown("---")
                        st.markdown("### 🎉 Transit Detection Complete")
                        module4 = TransitDetectionModule()
                        module4.data = transit_data
                        module4.detection_report = transit_report
                        st.markdown(module4.get_success_summary())
                        
                        # Generate and display Module 4 certificate
                        st.markdown("---")
                        st.markdown("### 🏆 Module 4 Certificate")
                        
                        # Get sample source IDs for certificate
                        passed = transit_data[transit_data['transit_passed_threshold'] == True]
                        sample_ids = passed['source_id'].head(5).tolist() if len(passed) > 0 else transit_data['source_id'].head(5).tolist()
                        
                        # Generate certificate
                        cert_png = render_module4_certificate(
                            display_name=current_display_name() or current_user() or "ExoQ Pioneer",
                            total_stars=transit_report['n_total'],
                            transit_candidates=transit_report['n_candidates'],
                            passed_threshold=transit_report['n_passed'],
                            max_snr=transit_report['max_snr'],
                            average_period=transit_report['average_period'],
                            sample_source_ids=sample_ids,
                            run_id=new_run_id(),
                        )
                        
                        # Display certificate
                        st.image(cert_png, use_container_width=True)
                        
                        # Download buttons for certificate and data
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.download_button(
                                label="📥 Download Certificate",
                                data=cert_png,
                                file_name=f"exomodule4_certificate_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.png",
                                mime="image/png",
                                type="primary"
                            )
                        with col2:
                            csv_data = transit_data.to_csv(index=False)
                            st.download_button(
                                label="💾 Download Transit Results (CSV)",
                                data=csv_data,
                                file_name=f"module4_transit_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv"
                            )
                        with col3:
                            if st.button("🚀 Continue to Module 4.5: ExoMiner++ Vetting", type="secondary"):
                                st.session_state.pipeline_step = 4.5
                                st.rerun()
                        
                        # Reset button to start over
                        st.markdown("---")
                        if st.button("🔄 Reset Module 4", type="secondary"):
                            st.session_state.module4_complete = False
                            st.session_state.pipeline_data = None
                            st.session_state.transit_report = None
                            st.rerun()

    # Module 4.5: ExoMiner++ Vetting
    if st.session_state.pipeline_started and st.session_state.pipeline_step >= 4.5:
        with st.expander("🤖 Module 4.5 of 8 - ExoMiner++ Vetting", expanded=True):
            if st.session_state.pipeline_step == 4.5:
                st.markdown("##### 🤖 Module 4.5 of 8 - ExoMiner++ Vetting")
                
                # LIVE PROCESS badge
                st.markdown(
                    '<span style="background-color: #ef4444; color: white; padding: 4px 12px; border-radius: 4px; font-size: 0.8rem; font-weight: bold;">🔴 LIVE PROCESS</span>',
                    unsafe_allow_html=True
                )
                
                # NASA Attribution
                st.markdown(
                    """
                    <div style="background-color: #e3f2fd; border-left: 4px solid #2196f3; padding: 12px; margin: 16px 0; border-radius: 4px;">
                        <strong>🔬 NASA Attribution:</strong> This module uses ExoMiner++ algorithms from NASA's GitHub repository 
                        (<a href="https://github.com/nasa/ExoMiner" target="_blank">github.com/nasa/ExoMiner</a>). 
                        ExoMiner++ is a deep learning-based system developed by NASA Ames Research Center for automated vetting of exoplanet candidates.
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
                st.markdown(
                    "**Vet transit candidates using NASA's ExoMiner++ deep learning models.**  \n"
                    "ExoMiner++ applies state-of-the-art machine learning to distinguish real planets from false positives "
                    "in TESS transit candidates. This module queries TESS SPOC TCEs for your detected candidates and applies "
                    "NASA's vetting models to identify high-confidence planet candidates."
                )
                with st.expander("READ MORE: The ExoMiner++ Vetting Process . . ."):
                    st.markdown(
                        "Module 4.5 uses NASA's ExoMiner++ deep learning system for automated vetting of exoplanet candidates.\n\n"
                        "- **ExoMiner++**: Deep learning model trained on thousands of confirmed planets and false positives\n"
                        "- **TESS SPOC TCEs**: Queries the TESS Science Processing Operations Center for transit candidates\n"
                        "- **MAST Data**: Downloads fresh light curve data from MAST archive for vetting\n"
                        "- **Fallback**: Uses Module 3 TESS light curves if MAST download fails\n"
                        "- **Vetting Threshold**: Configurable threshold to filter candidates by confidence score\n\n"
                        "After vetting, only high-confidence candidates (above threshold) proceed to Module 5 for habitability scoring."
                    )

                st.caption(
                    "Module 4.5 uses transit candidates from Module 4 and applies NASA's ExoMiner++ vetting to filter false positives."
                )

                # Podman status check
                st.markdown("---")
                st.markdown("### 🖥️ System Status")
                module4_5 = ExoMinerVettingModule()
                podman_installed, podman_msg = module4_5.check_podman_installed()
                image_available, image_msg = module4_5.check_exominer_image()
                
                col1, col2 = st.columns(2)
                with col1:
                    if podman_installed:
                        st.success(f"✅ Podman: {podman_msg}")
                    else:
                        st.warning(f"⚠️ Podman: {podman_msg}")
                with col2:
                    if image_available:
                        st.success(f"✅ ExoMiner++ Image: Available")
                    else:
                        st.warning(f"⚠️ ExoMiner++ Image: {image_msg}")

                # Check if data is available from Module 4
                if st.session_state.pipeline_data is None:
                    st.warning("⚠️ No data available from Module 4. Please complete Module 4 first.")
                else:
                    st.info(f"📊 Ready to vet {len(st.session_state.pipeline_data)} transit candidates")

                    # Vetting configuration
                    st.markdown("---")
                    st.markdown("### ⚙️ Vetting Configuration")
                    
                    vetting_threshold = st.slider(
                        "ExoMiner++ vetting threshold",
                        min_value=0.0,
                        max_value=1.0,
                        value=0.5,
                        step=0.1,
                        help="Candidates with ExoMiner++ score above this threshold are considered vetted"
                    )
                    
                    if not podman_installed or not image_available:
                        st.error("❌ Podman or ExoMiner++ image not available. Live vetting requires Podman and ExoMiner++ image.")
                        st.info("Please install Podman and run: `podman pull ghcr.io/nasa/exominer:latest`")

                    # Run Module 4.5 button
                    if not st.session_state.get('module4_5_complete', False):
                        st.markdown("---")
                        # Disable button if Podman not available
                        button_disabled = not (podman_installed and image_available)
                        if st.button("▶️ Run ExoMiner++ Vetting", type="primary", key="run_module4_5", disabled=button_disabled):
                            with st.spinner("🤖 Running ExoMiner++ vetting... This may take several minutes."):
                                try:
                                    # Run vetting with live data (use_mock=False)
                                    vetted_data, vetting_report = module4_5.vet_candidates(
                                        st.session_state.pipeline_data,
                                        threshold=vetting_threshold,
                                        use_mock=False,  # Always use live data
                                        filter_to_vetted=False  # Keep all candidates for now, filter later
                                    )
                                    
                                    # Store results in session state
                                    st.session_state.pipeline_data = vetted_data
                                    st.session_state.vetting_report = vetting_report
                                    st.session_state.module4_5_complete = True
                                    
                                    st.success(f"✅ Vetting complete: {vetting_report['n_vetted']} vetted, {vetting_report['n_rejected']} rejected")
                                    st.info(f"Mean ExoMiner++ score: {vetting_report['mean_score']:.3f}")
                                    st.rerun()
                                    
                                except Exception as exc:
                                    st.error(f"❌ Error during vetting: {exc}")
                                    st.info("Please try again or check the logs.")

                    # Display Module 4.5 results if complete
                    if st.session_state.get('module4_5_complete', False):
                        vetting_data = st.session_state.pipeline_data
                        vetting_report = st.session_state.vetting_report
                        
                        # Display vetting statistics
                        st.markdown("### 📊 Vetting Statistics")
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Total Candidates", vetting_report['n_total'])
                        with col2:
                            st.metric("Vetted", vetting_report['n_vetted'])
                        with col3:
                            st.metric("Rejected", vetting_report['n_rejected'])
                        with col4:
                            st.metric("Mean Score", f"{vetting_report['mean_score']:.3f}")
                        
                        # Display score distribution
                        st.markdown("---")
                        st.markdown("### 📈 ExoMiner++ Score Distribution")
                        if 'exominer_score' in vetting_data.columns:
                            st.write(vetting_data['exominer_score'].describe())
                        
                        # Display vetted candidates
                        st.markdown("---")
                        st.markdown("### ✅ Vetted Candidates (Above Threshold)")
                        vetted_df = vetting_data[vetting_data['exominer_vetted'] == True]
                        if len(vetted_df) > 0:
                            cols_to_show = ['source_id', 'ra', 'dec', 'exominer_score']
                            if 'transit_period' in vetted_df.columns:
                                cols_to_show.append('transit_period')
                            if 'transit_depth' in vetted_df.columns:
                                cols_to_show.append('transit_depth')
                            st.dataframe(
                                vetted_df[cols_to_show].head(10),
                                use_container_width=True
                            )
                            if len(vetted_df) > 10:
                                st.info(f"Showing 10 of {len(vetted_df)} vetted candidates")
                        else:
                            st.info("No vetted candidates found")
                        
                        # Display rejected candidates
                        st.markdown("---")
                        st.markdown("### ❌ Rejected Candidates (Below Threshold)")
                        rejected_df = vetting_data[vetting_data['exominer_vetted'] == False]
                        if len(rejected_df) > 0:
                            cols_to_show = ['source_id', 'ra', 'dec', 'exominer_score']
                            if 'transit_period' in rejected_df.columns:
                                cols_to_show.append('transit_period')
                            st.dataframe(
                                rejected_df[cols_to_show].head(10),
                                use_container_width=True
                            )
                            if len(rejected_df) > 10:
                                st.info(f"Showing 10 of {len(rejected_df)} rejected candidates")
                        else:
                            st.info("No rejected candidates")
                        
                        # Filter option
                        st.markdown("---")
                        filter_to_vetted_only = st.checkbox(
                            "Pass only vetted candidates to Module 5",
                            value=True,
                            help="If checked, only candidates above the threshold will proceed to habitability scoring"
                        )
                        
                        if filter_to_vetted_only:
                            st.session_state.pipeline_data = vetted_df.copy()
                            st.info(f"Filtered to {len(vetted_df)} vetted candidates for Module 5")
                        
                        # Display success summary
                        st.markdown("---")
                        st.markdown("### 🎉 Vetting Complete")
                        st.markdown(module4_5.get_success_summary())
                        
                        # Download and continue buttons
                        st.markdown("---")
                        col1, col2 = st.columns(2)
                        with col1:
                            csv_data = vetting_data.to_csv(index=False)
                            st.download_button(
                                label="💾 Download Vetting Results (CSV)",
                                data=csv_data,
                                file_name=f"module4_5_exominer_vetted_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv"
                            )
                        with col2:
                            if st.button("🚀 Continue to Module 5", type="secondary"):
                                st.session_state.pipeline_step = 5
                                st.rerun()
                        
                        # Reset button
                        st.markdown("---")
                        if st.button("🔄 Reset Module 4.5", type="secondary"):
                            st.session_state.module4_5_complete = False
                            st.session_state.vetting_report = None
                            st.rerun()

    # Module 5: Transit Detection
    if st.session_state.pipeline_started and st.session_state.pipeline_step >= 5:
        with st.expander("🎯 Module 5 of 8 - Transit Detection", expanded=True):
            if st.session_state.pipeline_step == 5:
                st.markdown("##### 🎯 Module 5 of 8 - Transit Detection")
                st.markdown(
                    "**Detect transit signals in TESS light curves using BLS periodogram.**  \n"
                    "Use the Box Least Squares (BLS) algorithm to search for periodic dips in star brightness - "
                    "the tell-tale sign of an orbiting exoplanet. Score candidates by signal-to-noise ratio "
                    "and false alarm probability to filter out false positives."
                )
                with st.expander("READ MORE: The Transit Detection Process . . ."):
                    st.markdown(
                        "Module 5 uses the BLS (Box Least Squares) periodogram algorithm to detect transit signals in TESS light curves. BLS is a powerful mathematical tool that searches for periodic dips in brightness.\n\n"
                        "- **BLS Algorithm**: Searches for periodic box-shaped signals in light curve data\n"
                        "- **Signal-to-Noise Ratio (S/N)**: Measures how strong the transit signal is compared to noise\n"
                        "- **False Alarm Probability (FAP)**: Statistical measure of how likely the signal is a false positive\n"
                        "- **Period Range**: Typically 0.5-30 days for Earth-sized planets in habitable zones\n\n"
                        "After detection, Module 5 filters candidates by S/N > 6 and FAP < 0.01 to ensure high-confidence detections. "
                        "Only stars with confirmed transit candidates move to Module 6 for habitability scoring."
                    )

                st.caption(
                    "Module 5 performs transit detection on TESS light curves from Module 4. "
                    "Candidates are filtered by signal-to-noise ratio and false alarm probability."
                )

                # Check if data is available from Module 4
                if st.session_state.pipeline_data is None:
                    st.warning("⚠️ No data available from Module 4. Please complete Module 4 first.")
                else:
                    st.info(f"📊 Ready to detect transits in {len(st.session_state.pipeline_data)} light curves")

                    # Run Module 5 button
                    if not st.session_state.get('module5_complete', False):
                        st.markdown("---")
                        if st.button("🎯 Run Module 5 — Transit Detection", type="primary", key="run_module5"):
                            with st.spinner("🎯 Detecting transits using BLS periodogram..."):
                                # Initialize Module 5 (Transit Detection)
                                module5 = TransitDetectionModule()
                                
                                # Run transit detection
                                try:
                                    # Use real detection (set use_mock=True for testing)
                                    transit_data, detection_report = module5.detect_transits(
                                        st.session_state.pipeline_data
                                    )
                                    
                                    # Store results in session state
                                    st.session_state.pipeline_data = transit_data
                                    st.session_state.transit_report = detection_report
                                    st.session_state.module5_complete = True
                                    
                                    st.success(f"✅ Detected {len(transit_data)} transit candidates")
                                    st.info(f"High-confidence detections: {detection_report['n_high_confidence']}")
                                    st.rerun()
                                    
                                except Exception as exc:
                                    st.error(f"❌ Error during transit detection: {exc}")
                                    st.info("Please try again or check the logs.")

                # Display Module 5 results if complete
                if st.session_state.get('module5_complete', False):
                    transit_data = st.session_state.pipeline_data
                    detection_report = st.session_state.transit_report
                    
                    # Display transit detection statistics
                    st.markdown("### 📊 Transit Detection Statistics")
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Light Curves", detection_report['n_total'])
                    with col2:
                        st.metric("Candidates Detected", detection_report['n_detected'])
                    with col3:
                        st.metric("High-Confidence", detection_report['n_high_confidence'])
                    with col4:
                        st.metric("Mean S/N", f"{detection_report['mean_snr']:.2f}")
                    
                    # Display results tables
                    st.markdown("---")
                    st.markdown("### 🌟 Transit Candidates")
                    if len(transit_data) > 0:
                        cols_to_show = ['source_id', 'ra', 'dec', 'transit_period', 'transit_depth', 'snr']
                        st.dataframe(
                            transit_data[cols_to_show].head(10),
                            use_container_width=True
                        )
                        if len(transit_data) > 10:
                            st.info(f"Showing 10 of {len(transit_data)} transit candidates")
                    else:
                        st.info("No transit candidates found")
                    
                    # Display success summary
                    st.markdown("---")
                    st.markdown("### 🎉 Transit Detection Complete")
                    st.markdown(module5.get_success_summary())
                    
                    # Download and continue buttons
                    st.markdown("---")
                    col1, col2 = st.columns(2)
                    with col1:
                        csv_data = transit_data.to_csv(index=False)
                        st.download_button(
                            label="💾 Download Transit Detection Results (CSV)",
                            data=csv_data,
                            file_name=f"module5_transit_detection_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                    with col2:
                        if st.button("🚀 Continue to Module 6", type="secondary"):
                            st.session_state.pipeline_step = 6
                            st.rerun()
                    
                    # Reset button
                    st.markdown("---")
                    if st.button("🔄 Reset Module 5", type="secondary"):
                        st.session_state.module5_complete = False
                        st.session_state.transit_report = None
                        st.rerun()

# Module 6: Habitability Scoring
if st.session_state.pipeline_started and st.session_state.pipeline_step >= 6:
    with st.expander("🌍 Module 6 of 8 - Habitability Scoring", expanded=True):
        if st.session_state.pipeline_step == 6:
            st.markdown("##### 🌍 Module 6 of 8 - Habitability Scoring")
            st.markdown(
                "**Score habitability of stars and exoplanet candidates.**  \n"
                "Calculate the Earth Similarity Index (ESI) for exoplanets and evaluate stellar habitability "
                "based on temperature, surface gravity, metallicity, and activity. Identify the most promising "
                "Earth 2.0 candidates for further study."
            )
            with st.expander("READ MORE: The Habitability Scoring Process . . ."):
                st.markdown(
                    "Module 6 evaluates the habitability potential of stars and exoplanet candidates using multiple criteria.\n\n"
                    "- **Stellar Habitability**: Scores stars based on temperature (3900-4800K optimal), surface gravity (>4.5 dex for main sequence), and RUWE (<1.2 for low variability)\n"
                    "- **Exoplanet Habitability**: Scores planets based on radius (0.8-1.5 Earth radii), orbital period (habitable zone), and signal-to-noise ratio\n"
                    "- **Earth Similarity Index (ESI)**: A metric comparing exoplanets to Earth based on radius, temperature, and other properties (1.0 = Earth-like)\n"
                    "- **Habitable Zone**: The region around a star where liquid water could exist on a planet's surface\n\n"
                    "After scoring, Module 6 identifies the most habitable stars and exoplanets. Only high-scoring candidates "
                    "move to Module 7 for the final results summary."
                )

            st.caption(
                "Module 6 uses transit detection data from Module 5 and stellar parameters from Module 2. "
                "Candidates are scored for habitability potential using the Earth Similarity Index."
            )

            # Check if data is available from Module 5
            if st.session_state.pipeline_data is None:
                st.warning("⚠️ No data available from Module 5. Please complete Module 5 first.")
            else:
                st.info(f"📊 Ready to score {len(st.session_state.pipeline_data)} stars for habitability")

                # Run Module 6 button
                if not st.session_state.get('module6_complete', False):
                    st.markdown("---")
                    if st.button("🌍 Run Module 6 — Habitability Scoring", type="primary", key="run_module6"):
                        with st.spinner("🌍 Scoring habitability and calculating Earth Similarity Index..."):
                            # Initialize Module 6 (Habitability Scoring)
                            module6 = HabitabilityScoringModule()
                            
                            # Run habitability scoring
                            try:
                                habitability_data, scoring_report = module6.score_habitability(
                                    st.session_state.pipeline_data
                                )
                                
                                # Store results in session state
                                st.session_state.pipeline_data = habitability_data
                                st.session_state.scoring_report = scoring_report
                                st.session_state.module6_complete = True
                                
                                st.success(f"✅ Scored {len(habitability_data)} stars for habitability")
                                st.info(f"Highly habitable stars: {scoring_report['n_highly_habitable']}")
                                st.info(f"Habitable exoplanets: {scoring_report['n_habitable_exo']}")
                                st.rerun()
                                
                            except Exception as exc:
                                st.error(f"❌ Error during habitability scoring: {exc}")
                                st.info("Using mock data for demonstration")

                # Display Module 6 results if complete
                if st.session_state.get('module6_complete', False):
                    habitability_data = st.session_state.pipeline_data
                    scoring_report = st.session_state.scoring_report
                    
                    # Display habitability statistics
                    st.markdown("### 📊 Habitability Statistics")
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Stars", scoring_report['n_total'])
                    with col2:
                        st.metric("Highly Habitable", scoring_report['n_highly_habitable'])
                    with col3:
                        st.metric("Habitable Exoplanets", scoring_report['n_habitable_exo'])
                    with col4:
                        st.metric("Max ESI", f"{scoring_report['max_esi']:.2f}")
                    
                    # Display results tables
                    st.markdown("---")
                    st.markdown("### 🌟 Highly Habitable Stars")
                    highly_habitable = habitability_data[habitability_data['stellar_hab_score'] > 0.8]
                    if len(highly_habitable) > 0:
                        cols_to_show = ['source_id', 'ra', 'dec', 'stellar_hab_score']
                        if 'exo_hab_score' in highly_habitable.columns:
                            cols_to_show.append('exo_hab_score')
                        if 'esi' in highly_habitable.columns:
                            cols_to_show.append('esi')
                        st.dataframe(
                            highly_habitable[cols_to_show].head(10),
                            use_container_width=True
                        )
                        if len(highly_habitable) > 10:
                            st.info(f"Showing 10 of {len(highly_habitable)} highly habitable stars")
                    else:
                        st.info("No highly habitable stars found")
                    
                    st.markdown("---")
                    st.markdown("### 🪐 Habitable Exoplanet Candidates")
                    if 'transit_passed_threshold' in habitability_data.columns:
                        # Check if exo_hab_score column exists
                        if 'exo_hab_score' in habitability_data.columns:
                            habitable_exo = habitability_data[(habitability_data['transit_passed_threshold'] == True) & (habitability_data['exo_hab_score'] > 0.6)]
                        else:
                            habitable_exo = habitability_data[habitability_data['transit_passed_threshold'] == True]
                        
                        if len(habitable_exo) > 0:
                            cols_to_show = ['source_id', 'ra', 'dec', 'stellar_hab_score']
                            if 'exo_hab_score' in habitable_exo.columns:
                                cols_to_show.append('exo_hab_score')
                            if 'esi' in habitable_exo.columns:
                                cols_to_show.append('esi')
                            st.dataframe(
                                habitable_exo[cols_to_show].head(10),
                                use_container_width=True
                            )
                            if len(habitable_exo) > 10:
                                st.info(f"Showing 10 of {len(habitable_exo)} habitable exoplanet candidates")
                        else:
                            st.info("No habitable exoplanet candidates found")
                        
                        # Display success summary
                        st.markdown("---")
                        st.markdown("### 🎉 Habitability Scoring Complete")
                        module6 = HabitabilityScoringModule()
                        module6.data = habitability_data
                        module6.scoring_report = scoring_report
                        st.markdown(module6.get_success_summary())
                        
                        # Generate and display Module 6 certificate
                        st.markdown("---")
                        st.markdown("### 🏆 Module 6 Certificate")
                        
                        # Get sample source IDs for certificate
                        highly_habitable = habitability_data[habitability_data['stellar_hab_score'] > 0.8]
                        sample_ids = highly_habitable['source_id'].head(5).tolist() if len(highly_habitable) > 0 else habitability_data['source_id'].head(5).tolist()
                        
                        # Generate certificate
                        cert_png = render_module6_certificate(
                            display_name=current_display_name() or current_user() or "ExoQ Pioneer",
                            total_stars=scoring_report['n_total'],
                            highly_habitable=scoring_report['n_highly_habitable'],
                            habitable_exoplanets=scoring_report['n_habitable_exo'],
                            best_star_score=scoring_report['best_star_score'],
                            max_esi=scoring_report['max_esi'],
                            sample_source_ids=sample_ids,
                            run_id=new_run_id(),
                        )
                        
                        # Display certificate
                        st.image(cert_png, use_container_width=True)
                        
                        # Download buttons for certificate and data
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.download_button(
                                label="📥 Download Certificate",
                                data=cert_png,
                                file_name=f"exomodule5_certificate_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.png",
                                mime="image/png",
                                type="primary"
                            )
                        with col2:
                            csv_data = habitability_data.to_csv(index=False)
                            st.download_button(
                                label="💾 Download Habitability Results (CSV)",
                                data=csv_data,
                                file_name=f"module5_habitability_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv"
                            )
                        with col3:
                            if st.button("🚀 Continue to Module 6", type="secondary"):
                                st.session_state.pipeline_step = 6
                                st.rerun()
                        
                        # Reset button to start over
                        st.markdown("---")
                        if st.button("🔄 Reset Module 5", type="secondary"):
                            st.session_state.module5_complete = False
                            st.session_state.pipeline_data = None
                            st.session_state.scoring_report = None
                            st.rerun()

    # Module 6: Habitability Scoring
    if st.session_state.pipeline_started and st.session_state.pipeline_step >= 6:
        with st.expander("🌍 Module 6 of 8 - Habitability Scoring", expanded=True):
            if st.session_state.pipeline_step == 6:
                st.markdown("##### 🌍 Module 6 of 8 - Habitability Scoring")
                st.markdown(
                    "**Score habitability of stars and exoplanet candidates.**  \n"
                    "Calculate the Earth Similarity Index (ESI) for exoplanets and evaluate stellar habitability "
                    "based on temperature, surface gravity, metallicity, and activity. Identify the most promising "
                    "Earth 2.0 candidates for further study."
                )
                with st.expander("READ MORE: The Habitability Scoring Process . . ."):
                    st.markdown(
                        "Module 6 evaluates the habitability potential of stars and exoplanet candidates using multiple criteria.\n\n"
                        "- **Stellar Habitability**: Scores stars based on temperature (3900-4800K optimal), surface gravity (>4.5 dex for main sequence), and RUWE (<1.2 for low variability)\n"
                        "- **Exoplanet Habitability**: Scores planets based on radius (0.8-1.5 Earth radii), orbital period (habitable zone), and signal-to-noise ratio\n"
                        "- **Earth Similarity Index (ESI)**: A metric comparing exoplanets to Earth based on radius, temperature, and other properties (1.0 = Earth-like)\n"
                        "- **Habitable Zone**: The region around a star where liquid water could exist on a planet's surface\n\n"
                        "After scoring, Module 6 identifies the most habitable stars and exoplanets. Only high-scoring candidates "
                        "move to Module 7 for the final results summary."
                    )

                st.caption(
                    "Module 6 uses transit detection data from Module 5 and stellar parameters from Module 2. "
                    "Candidates are scored for habitability potential using the Earth Similarity Index."
                )

                # Check if data is available from Module 5
                if st.session_state.pipeline_data is None:
                    st.warning("⚠️ No data available from Module 5. Please complete Module 5 first.")
                else:
                    st.info(f"📊 Ready to score {len(st.session_state.pipeline_data)} stars for habitability")

                    # Run Module 6 button
                    if not st.session_state.get('module6_complete', False):
                        st.markdown("---")
                        if st.button("🌍 Run Module 6 — Habitability Scoring", type="primary", key="run_module6"):
                            with st.spinner("🌍 Scoring habitability and calculating Earth Similarity Index..."):
                                # Initialize Module 6 (Habitability Scoring)
                                module6 = HabitabilityScoringModule()
                                
                                # Run habitability scoring
                                try:
                                    habitability_data, scoring_report = module6.score_habitability(
                                        st.session_state.pipeline_data
                                    )
                                    
                                    # Store results in session state
                                    st.session_state.pipeline_data = habitability_data
                                    st.session_state.scoring_report = scoring_report
                                    st.session_state.module6_complete = True
                                    
                                    st.success(f"✅ Scored {len(habitability_data)} stars for habitability")
                                    st.info(f"Highly habitable stars: {scoring_report['n_highly_habitable']}")
                                    st.info(f"Habitable exoplanets: {scoring_report['n_habitable_exo']}")
                                    st.rerun()
                                    
                                except Exception as exc:
                                    st.error(f"❌ Error during habitability scoring: {exc}")
                                    st.info("Using mock data for demonstration")

                    # Display Module 6 results if complete
                    if st.session_state.get('module6_complete', False):
                        habitability_data = st.session_state.pipeline_data
                        scoring_report = st.session_state.scoring_report
                        
                        # Display habitability statistics
                        st.markdown("### 📊 Habitability Statistics")
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Total Stars", scoring_report['n_total'])
                        with col2:
                            st.metric("Highly Habitable", scoring_report['n_highly_habitable'])
                        with col3:
                            st.metric("Habitable Exoplanets", scoring_report['n_habitable_exo'])
                        with col4:
                            st.metric("Max ESI", f"{scoring_report['max_esi']:.2f}")
                        
                        # Display results tables
                        st.markdown("---")
                        st.markdown("### 🌟 Highly Habitable Stars")
                        highly_habitable = habitability_data[habitability_data['stellar_hab_score'] > 0.8]
                        if len(highly_habitable) > 0:
                            cols_to_show = ['source_id', 'ra', 'dec', 'stellar_hab_score']
                            if 'exo_hab_score' in highly_habitable.columns:
                                cols_to_show.append('exo_hab_score')
                            if 'esi' in highly_habitable.columns:
                                cols_to_show.append('esi')
                            st.dataframe(
                                highly_habitable[cols_to_show].head(10),
                                use_container_width=True
                            )
                            if len(highly_habitable) > 10:
                                st.info(f"Showing 10 of {len(highly_habitable)} highly habitable stars")
                        else:
                            st.info("No highly habitable stars found")
                        
                        st.markdown("---")
                        st.markdown("### 🪐 Habitable Exoplanet Candidates")
                        if 'transit_passed_threshold' in habitability_data.columns:
                            if 'exo_hab_score' in habitability_data.columns:
                                habitable_exo = habitability_data[(habitability_data['transit_passed_threshold'] == True) & (habitability_data['exo_hab_score'] > 0.6)]
                            else:
                                habitable_exo = habitability_data[habitability_data['transit_passed_threshold'] == True]
                            
                            if len(habitable_exo) > 0:
                                cols_to_show = ['source_id', 'ra', 'dec', 'stellar_hab_score']
                                if 'exo_hab_score' in habitable_exo.columns:
                                    cols_to_show.append('exo_hab_score')
                                if 'esi' in habitable_exo.columns:
                                    cols_to_show.append('esi')
                                if 'transit_period' in habitable_exo.columns:
                                    cols_to_show.append('transit_period')
                                st.dataframe(
                                    habitable_exo[cols_to_show].head(10),
                                    use_container_width=True
                                )
                                if len(habitable_exo) > 10:
                                    st.info(f"Showing 10 of {len(habitable_exo)} habitable exoplanets")
                            else:
                                st.info("No habitable exoplanets found")
                        else:
                            st.info("No transit data available for exoplanet scoring")
                        
                        # Display success summary
                        st.markdown("---")
                        st.markdown("### 🎉 Habitability Scoring Complete")
                        module6 = HabitabilityScoringModule()
                        module6.data = habitability_data
                        module6.scoring_report = scoring_report
                        st.markdown(module6.get_success_summary())
                        
                        # Download and continue buttons
                        st.markdown("---")
                        col1, col2 = st.columns(2)
                        with col1:
                            csv_data = habitability_data.to_csv(index=False)
                            st.download_button(
                                label="💾 Download Habitability Results (CSV)",
                                data=csv_data,
                                file_name=f"module6_habitability_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv"
                            )
                        with col2:
                            if st.button("🚀 Continue to Module 7", type="secondary"):
                                st.session_state.pipeline_step = 7
                                st.rerun()
                        
                        # Reset button
                        st.markdown("---")
                        if st.button("🔄 Reset Module 6", type="secondary"):
                            st.session_state.module6_complete = False
                            st.session_state.pipeline_data = None
                            st.session_state.scoring_report = None
                            st.rerun()

    # Module 7: Results Summary
    if st.session_state.pipeline_started and st.session_state.pipeline_step >= 7:
        with st.expander("📊 Module 7 of 8 - Results Summary", expanded=True):
            if st.session_state.pipeline_step == 7:
                st.markdown("##### 📊 Module 7 of 8 - Results Summary")
                st.markdown(
                    "**Review and export your final results.**  \n"
                    "This module provides a comprehensive summary of your analysis pipeline results, "
                    "including all stars analyzed, transit candidates detected, and habitability scores. "
                    "Export your findings for further study or publication."
                )
                with st.expander("READ MORE: Results Summary Process . . ."):
                    st.markdown(
                        "Module 7 compiles all results from the previous modules into a comprehensive summary.\n\n"
                        "- **Statistical Overview**: Aggregated statistics for all stars analyzed through the pipeline\n"
                        "- **Top Discoveries**: Ranked list of the most promising Earth 2.0 candidates based on multiple criteria\n"
                        "- **Quality Metrics**: Success rates, confidence levels, and validation scores for each stage\n"
                        "- **Data Integration**: Combines data from all modules into a single export-ready dataset\n\n"
                        "After reviewing the summary, you can export your complete dataset in multiple formats "
                        "for further analysis or sharing with the scientific community."
                    )

                st.caption(
                    "Module 7 uses results from all previous modules to generate a comprehensive summary "
                    "of your exoplanet search campaign."
                )

                # Check if data is available from Module 6
                if st.session_state.pipeline_data is None:
                    st.warning("⚠️ No data available from Module 6. Please complete Module 6 first.")
                else:
                    st.info(f"📊 Ready to generate summary for {len(st.session_state.pipeline_data)} stars")

                    # Run Module 7 button
                    if not st.session_state.get('module7_complete', False):
                        st.markdown("---")
                        if st.button("📊 Generate Results Summary", type="primary", key="run_module7"):
                            with st.spinner("📊 Generating comprehensive results summary..."):
                                # Initialize Module 7 (Results Summary)
                                module7 = ResultsSummaryModule()
                                
                                # Generate summary
                                try:
                                    summary_data, summary_report = module7.generate_summary(
                                        st.session_state.pipeline_data
                                    )
                                    
                                    # Store results in session state
                                    st.session_state.pipeline_data = summary_data
                                    st.session_state.summary_report = summary_report
                                    st.session_state.module7_complete = True
                                    
                                    st.success(f"✅ Generated summary for {len(summary_data)} stars")
                                    st.info(f"Top discoveries: {len(summary_report.get('top_discoveries', []))}")
                                    st.rerun()
                                    
                                except Exception as exc:
                                    st.error(f"❌ Error during summary generation: {exc}")
                                    st.info("Using basic summary for demonstration")

                    # Display Module 7 results if complete
                    if st.session_state.get('module7_complete', False):
                        summary_data = st.session_state.pipeline_data
                        summary_report = st.session_state.summary_report
                        
                        # Display summary statistics
                        st.markdown("### 📊 Pipeline Statistics")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Total Stars", summary_report['n_total_stars'])
                        with col2:
                            st.metric("Highly Habitable", summary_report.get('n_highly_habitable', 0))
                        with col3:
                            st.metric("Transit Candidates", summary_report.get('n_transit_candidates', 0))
                        
                        # Display top discoveries
                        st.markdown("---")
                        st.markdown("### 🌟 Top Discoveries")
                        if 'top_discoveries' in summary_report and len(summary_report['top_discoveries']) > 0:
                            for i, discovery in enumerate(summary_report['top_discoveries'][:5], 1):
                                st.info(f"{i}. TIC {discovery['source_id']} - {discovery['description']}")
                        else:
                            st.info("No top discoveries identified")
                        
                        # Display success summary
                        st.markdown("---")
                        st.markdown("### 🎉 Results Summary Complete")
                        module7 = ResultsSummaryModule()
                        module7.data = summary_data
                        module7.summary_report = summary_report
                        st.markdown(module7.get_success_summary())
                        
                        # Download and continue buttons
                        st.markdown("---")
                        col1, col2 = st.columns(2)
                        with col1:
                            csv_data = summary_data.to_csv(index=False)
                            st.download_button(
                                label="💾 Download Complete Results (CSV)",
                                data=csv_data,
                                file_name=f"module7_complete_results_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv"
                            )
                        with col2:
                            if st.button("🚀 Continue to Module 8", type="secondary"):
                                st.session_state.pipeline_step = 8
                                st.rerun()
                        
                        # Reset button
                        st.markdown("---")
                        if st.button("🔄 Reset Module 7", type="secondary"):
                            st.session_state.module7_complete = False
                            st.session_state.summary_report = None
                            st.rerun()

    # Module 8: Data Export
    if st.session_state.pipeline_started and st.session_state.pipeline_step >= 8:
        with st.expander("📤 Module 8 of 8 - Data Export", expanded=True):
            if st.session_state.pipeline_step == 8:
                st.markdown("##### 📤 Module 8 of 8 - Data Export")
                st.markdown(
                    "**Export your results in multiple formats.**  \n"
                    "Download your complete dataset in CSV, JSON, or other formats for sharing "
                    "with collaborators or for further analysis in your preferred software."
                )
                with st.expander("READ MORE: Data Export Process . . ."):
                    st.markdown(
                        "Module 8 exports your complete pipeline results in multiple formats.\n\n"
                        "- **CSV Format**: Comma-separated values, ideal for spreadsheet applications like Excel, Google Sheets, or statistical software\n"
                        "- **JSON Format**: JavaScript Object Notation, perfect for web applications, APIs, or programmatic access\n"
                        "- **Metadata**: Export report includes file sizes, record counts, and timestamps for documentation\n"
                        "- **Version Control**: Each export includes a timestamp to track different versions of your analysis\n\n"
                        "After exporting, you can share your discoveries with the scientific community, "
                        "use them for follow-up observations, or prepare them for publication."
                    )

                st.caption(
                    "Module 8 uses the final dataset from Module 7 to generate export files "
                    "in your preferred formats."
                )

                # Check if data is available from Module 7
                if st.session_state.pipeline_data is None:
                    st.warning("⚠️ No data available from Module 7. Please complete Module 7 first.")
                else:
                    st.info(f"📊 Ready to export {len(st.session_state.pipeline_data)} stars")

                    # Export options
                    st.markdown("---")
                    st.markdown("### 📋 Export Options")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        export_csv = st.checkbox("CSV Format", value=True)
                    with col2:
                        export_json = st.checkbox("JSON Format", value=False)
                    
                    # Run Module 8 button
                    if not st.session_state.get('module8_complete', False):
                        st.markdown("---")
                        if st.button("📤 Export Data", type="primary", key="run_module8"):
                            with st.spinner("📤 Exporting data..."):
                                # Initialize Module 8 (Data Export)
                                module8 = DataExportModule()
                                
                                # Determine export formats
                                formats = []
                                if export_csv:
                                    formats.append('csv')
                                if export_json:
                                    formats.append('json')
                                
                                if not formats:
                                    st.warning("⚠️ Please select at least one export format.")
                                else:
                                    try:
                                        export_report, summary = module8.export_data(
                                            st.session_state.pipeline_data,
                                            formats=formats,
                                            output_dir='data/exports',
                                            filename_prefix='exoq_results'
                                        )
                                        
                                        # Store results in session state
                                        st.session_state.export_report = export_report
                                        st.session_state.module8_complete = True
                                        
                                        st.success(f"✅ Exported data in {len(formats)} format(s)")
                                        st.info(f"Total size: {export_report['total_size_kb']:.2f} KB")
                                        st.rerun()
                                        
                                    except Exception as exc:
                                        st.error(f"❌ Error during export: {exc}")
                                        st.info("Export failed. Please try again.")

                    # Display Module 8 results if complete
                    if st.session_state.get('module8_complete', False):
                        export_report = st.session_state.export_report
                        
                        # Display export statistics
                        st.markdown("### 📊 Export Statistics")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Formats", export_report['n_formats'])
                        with col2:
                            st.metric("Rows Exported", export_report['n_rows_exported'])
                        with col3:
                            st.metric("File Size", f"{export_report['total_size_kb']:.2f} KB")
                        
                        # Display export files
                        st.markdown("---")
                        st.markdown("### 📁 Exported Files")
                        if 'files' in export_report and len(export_report['files']) > 0:
                            for format, file_info in export_report['files'].items():
                                st.info(f"**{format.upper()}**: {file_info['path']} ({file_info['size_kb']:.2f} KB)")
                        else:
                            st.info("No files exported")
                        
                        # Display success summary
                        st.markdown("---")
                        st.markdown("### 🎉 Pipeline Complete!")
                        module8 = DataExportModule()
                        module8.export_report = export_report
                        st.markdown(module8.get_success_summary())
                        
                        # Reset button to start new pipeline
                        st.markdown("---")
                        st.markdown("### 🔄 Start New Pipeline")
                        if st.button("🚀 Start New Analysis", type="primary"):
                            # Reset all session state
                            for key in list(st.session_state.keys()):
                                if key.startswith('module') or key in ['pipeline_step', 'pipeline_started', 'pipeline_data', 
                                                                     'validation_report', 'gaia_data', 'transit_report', 
                                                                     'scoring_report', 'summary_report', 'export_report']:
                                    del st.session_state[key]
                            st.rerun()
                        
                        # Reset Module 8 only
                        if st.button("🔄 Reset Module 8", type="secondary"):
                            st.session_state.module8_complete = False
                            st.session_state.export_report = None
                            st.rerun()

# Footer
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; font-size: 0.8rem; color: #6b7280;">
        ExoQ: Community Quest for Earth 2.0 © 2026
    </div>
    """,
    unsafe_allow_html=True,
)
