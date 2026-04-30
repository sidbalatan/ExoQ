"""
ExoQ Pipeline Test Page

Full pipeline integration test for all 8 modules
"""

import streamlit as st
import pandas as pd
import numpy as np
import sys
import os

# Add src to path for module imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from modules.module1_data_input import DataInputModule
from modules.module2_stellar_parameters import StellarParameterModule
from modules.module3_exoplanet_crossmatch import ExoplanetCrossMatchModule
from modules.module4_tess_lightcurves import TESSLightCurveModule
from modules.module5_transit_detection import TransitDetectionModule
from modules.module6_habitability_scoring import HabitabilityScoringModule
from modules.module7_results_summary import ResultsSummaryModule
from modules.module8_data_export import DataExportModule

st.set_page_config(
    page_title="Pipeline Test - ExoQ",
    page_icon="🔬",
    layout="wide"
)

st.title("🔬 ExoQ Pipeline Test")
st.markdown("---")

st.markdown("""
### Test the full ExoQ data pipeline

This page runs all 8 modules sequentially to demonstrate the complete pipeline:
1. **Data Input** - Load coordinates
2. **Stellar Parameters** - Get Gaia DR3 data
3. **Exoplanet Cross-Match** - Check NASA Exoplanet Archive
4. **TESS Light Curves** - Retrieve observation data
5. **Transit Detection** - Detect transits with BLS
6. **Habitability Scoring** - Score habitability
7. **Results Summary** - Generate summary
8. **Data Export** - Export results
""")

# Sidebar controls
st.sidebar.header("Pipeline Controls")

n_stars = st.sidebar.slider("Number of stars", min_value=5, max_value=100, value=10, step=5)
data_source = st.sidebar.selectbox("Data source", ["Virgin List", "Vetted List", "Manual Entry"])
use_mock = st.sidebar.checkbox("Use mock data", value=True, help="Use mock data for testing (no API calls)")

run_pipeline = st.sidebar.button("🚀 Run Full Pipeline", type="primary")

# Initialize session state
if 'pipeline_data' not in st.session_state:
    st.session_state.pipeline_data = None
if 'pipeline_step' not in st.session_state:
    st.session_state.pipeline_step = 0
if 'pipeline_started' not in st.session_state:
    st.session_state.pipeline_started = False

if run_pipeline:
    st.session_state.pipeline_step = 0
    st.session_state.pipeline_started = True
    st.session_state.pipeline_data = None
    st.rerun()

# Show instruction if pipeline hasn't started
if not st.session_state.pipeline_started:
    st.info("👆 Click 'Run Full Pipeline' in the sidebar to begin the ExoQ pipeline analysis.")

# Only run modules if pipeline has been started
if st.session_state.pipeline_started and st.session_state.pipeline_step >= 0:
    # Module 1: Data Input
    with st.expander("📥 Module 1: Data Input", expanded=st.session_state.pipeline_step == 0):
        if st.session_state.pipeline_step == 0:
            st.info("Loading coordinates...")
            
            module1 = DataInputModule()
            
            if data_source == "Virgin List":
                df, validation = module1.load_from_virgin_list(n_stars=n_stars)
            elif data_source == "Vetted List":
                df, validation = module1.load_from_vetted_list(n_stars=n_stars)
            else:
                coordinates = [
                    {'ra': 150.0, 'dec': 10.0},
                    {'ra': 200.0, 'dec': -20.0},
                    {'ra': 250.0, 'dec': 30.0}
                ]
                df, validation = module1.load_manual_entry(coordinates)
            
            st.success(module1.get_success_summary())
            st.dataframe(df[['source_id', 'ra', 'dec']].head())
            
            st.session_state.pipeline_data = df
            st.session_state.pipeline_step = 1
            st.rerun()
        else:
            st.success("Data input complete!")
            st.dataframe(st.session_state.pipeline_data[['source_id', 'ra', 'dec']].head())
        
        if st.session_state.pipeline_step == 1:
            if st.button("Continue to Module 2", key="m1_continue"):
                st.session_state.pipeline_step = 2
                st.rerun()

if st.session_state.pipeline_started and st.session_state.pipeline_step >= 1:
    # Module 2: Stellar Parameters
    with st.expander("🌟 Module 2: Stellar Parameters", expanded=st.session_state.pipeline_step == 1):
        if st.session_state.pipeline_step == 1:
            st.info("Retrieving stellar parameters from Gaia DR3...")
            
            module2 = StellarParameterModule()
            df, quality = module2.get_parameters(st.session_state.pipeline_data, use_mock=use_mock)
            
            st.success(module2.get_success_summary())
            st.dataframe(df[['source_id', 'ra', 'dec', 'teff_gspphot', 'logg_gspphot', 'ruwe']].head())
            
            st.session_state.pipeline_data = df
            st.session_state.pipeline_step = 2
            st.rerun()
        else:
            st.success("Stellar parameters retrieved!")
            st.dataframe(st.session_state.pipeline_data[['source_id', 'ra', 'dec', 'teff_gspphot', 'logg_gspphot', 'ruwe']].head())
        
        if st.session_state.pipeline_step == 2:
            if st.button("Continue to Module 3", key="m2_continue"):
                st.session_state.pipeline_step = 3
                st.rerun()

if st.session_state.pipeline_started and st.session_state.pipeline_step >= 2:
    # Module 3: Exoplanet Cross-Match
    with st.expander("🪐 Module 3: Exoplanet Cross-Match", expanded=st.session_state.pipeline_step == 2):
        if st.session_state.pipeline_step == 2:
            st.info("Cross-matching with NASA Exoplanet Archive...")
            
            module3 = ExoplanetCrossMatchModule()
            df, report = module3.cross_match(st.session_state.pipeline_data, use_mock=use_mock)
            
            st.success(module3.get_success_summary())
            st.dataframe(df[['source_id', 'has_exoplanet', 'exo_pl_name', 'exo_pl_orbper']].head())
            
            st.session_state.pipeline_data = df
            st.session_state.pipeline_step = 3
            st.rerun()
        else:
            st.success("Exoplanet cross-match complete!")
            st.dataframe(st.session_state.pipeline_data[['source_id', 'has_exoplanet', 'exo_pl_name', 'exo_pl_orbper']].head())
        
        if st.session_state.pipeline_step == 3:
            if st.button("Continue to Module 4", key="m3_continue"):
                st.session_state.pipeline_step = 4
                st.rerun()

if st.session_state.pipeline_started and st.session_state.pipeline_step >= 3:
    # Module 4: TESS Light Curves
    with st.expander("📈 Module 4: TESS Light Curves", expanded=st.session_state.pipeline_step == 3):
        if st.session_state.pipeline_step == 3:
            st.info("Retrieving TESS light curves from MAST API...")
            
            module4 = TESSLightCurveModule()
            df, report = module4.retrieve_lightcurves(st.session_state.pipeline_data, use_mock=use_mock)
            
            st.success(module4.get_success_summary())
            st.dataframe(df[['source_id', 'tess_available', 'sectors', 'data_points', 'cadence_minutes']].head())
            
            st.session_state.pipeline_data = df
            st.session_state.pipeline_step = 4
            st.rerun()
        else:
            st.success("TESS light curves retrieved!")
            st.dataframe(st.session_state.pipeline_data[['source_id', 'tess_available', 'sectors', 'data_points', 'cadence_minutes']].head())
        
        if st.session_state.pipeline_step == 4:
            if st.button("Continue to Module 5", key="m4_continue"):
                st.session_state.pipeline_step = 5
                st.rerun()

if st.session_state.pipeline_started and st.session_state.pipeline_step >= 4:
    # Module 5: Transit Detection
    with st.expander("🎯 Module 5: Transit Detection", expanded=st.session_state.pipeline_step == 4):
        if st.session_state.pipeline_step == 4:
            st.info("Detecting transits using BLS periodogram...")
            
            module5 = TransitDetectionModule()
            df, report = module5.detect_transits(st.session_state.pipeline_data, use_mock=use_mock)
            
            st.success(module5.get_success_summary())
            st.dataframe(df[['source_id', 'has_transit_candidate', 'transit_period', 'transit_snr']].head())
            
            st.session_state.pipeline_data = df
            st.session_state.pipeline_step = 5
            st.rerun()
        else:
            st.success("Transit detection complete!")
            st.dataframe(st.session_state.pipeline_data[['source_id', 'has_transit_candidate', 'transit_period', 'transit_snr']].head())
        
        if st.session_state.pipeline_step == 5:
            if st.button("Continue to Module 6", key="m5_continue"):
                st.session_state.pipeline_step = 6
                st.rerun()

if st.session_state.pipeline_started and st.session_state.pipeline_step >= 5:
    # Module 6: Habitability Scoring
    with st.expander("💧 Module 6: Habitability Scoring", expanded=st.session_state.pipeline_step == 5):
        if st.session_state.pipeline_step == 5:
            st.info("Scoring habitability of stars and exoplanets...")
            
            module6 = HabitabilityScoringModule()
            df, report = module6.score_habitability(st.session_state.pipeline_data, st.session_state.pipeline_data)
            
            st.success(module6.get_success_summary())
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
            st.success("Habitability scoring complete!")
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

if st.session_state.pipeline_started and st.session_state.pipeline_step >= 6:
    # Module 7: Results Summary
    with st.expander("🏆 Module 7: Results Summary", expanded=st.session_state.pipeline_step == 6):
        if st.session_state.pipeline_step == 6:
            st.info("Generating comprehensive results summary...")
            
            module7 = ResultsSummaryModule()
            df, report = module7.generate_summary(st.session_state.pipeline_data)
            
            st.success(module7.get_success_summary())
            
            # Display top discoveries
            st.subheader("Top Discoveries")
            for i, discovery in enumerate(report['top_discoveries'][:5], 1):
                st.write(f"{i}. TIC {discovery['source_id']} - {discovery['description']}")
            
            st.session_state.pipeline_data = df
            st.session_state.pipeline_step = 7
            st.rerun()
        else:
            st.success("Results summary complete!")
            
            # Display top discoveries
            st.subheader("Top Discoveries")
            for i, discovery in enumerate(st.session_state.pipeline_data.get('top_discoveries', [] )[:5], 1):
                st.write(f"{i}. TIC {discovery['source_id']} - {discovery['description']}")
        
        if st.session_state.pipeline_step == 7:
            if st.button("Continue to Module 8", key="m7_continue"):
                st.session_state.pipeline_step = 8
                st.rerun()

if st.session_state.pipeline_started and st.session_state.pipeline_step >= 7:
    # Module 8: Data Export
    with st.expander("💾 Module 8: Data Export", expanded=st.session_state.pipeline_step == 7):
        if st.session_state.pipeline_step == 7:
            st.info("Exporting results in multiple formats...")
            
            module8 = DataExportModule()
            report, summary = module8.export_data(st.session_state.pipeline_data, formats=['csv', 'json'])
            
            st.success(summary)
            
            # Display export report
            st.subheader("Export Report")
            st.json(report)
            
            st.session_state.pipeline_step = 8
            st.rerun()
        else:
            st.success("Data export complete!")
            
            # Display export report
            st.subheader("Export Report")
            st.json(st.session_state.pipeline_data.get('export_report', {}))
        
        if st.session_state.pipeline_step == 8:
            st.balloons()
            st.markdown("---")
            st.success("🎉 Pipeline Complete! All modules executed successfully!")

# Reset button
if st.session_state.pipeline_step > 0 or st.session_state.pipeline_started:
    st.sidebar.markdown("---")
    if st.sidebar.button("🔄 Reset Pipeline"):
        st.session_state.pipeline_step = 0
        st.session_state.pipeline_data = None
        st.session_state.pipeline_started = False
        st.rerun()
