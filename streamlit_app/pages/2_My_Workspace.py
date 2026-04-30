"""My Workspace — list and re-load saved Module 1 runs.

Per the project rule "no sidebar", this is a regular Streamlit page (the
Streamlit ``pages/`` mechanism still surfaces these in the in-page page
selector at the very top, *not* in a sidebar) and the sign-in widget is
mirrored in the same ``☰ Main Menu`` popover used on Home.
"""

from __future__ import annotations

import io
import sys
import os
from pathlib import Path

import pandas as pd
import streamlit as st

# Make the workspace package importable regardless of how Streamlit launches.
HERE = Path(__file__).resolve()
APP_ROOT = HERE.parents[1]  # streamlit_app/
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from workspace import current_user, sign_in_widget, get_store  # noqa: E402
from workspace.identity import current_display_name  # noqa: E402

st.set_page_config(page_title="My Workspace · ExoQ", page_icon="👤", layout="wide")

# --- Header + sign-in popover -----------------------------------------------
st.markdown("# 👤 My Workspace")
st.caption(
    "Every successful Module 1 run is saved to your workspace. "
    "Open one to re-load its survivors back into the pipeline, or download the CSV."
)

with st.popover("☰ Main Menu", use_container_width=False):
    sign_in_widget()

uid = current_user()
if not uid:
    st.info(
        "You are not signed in. Open **☰ Main Menu** above and pick a display name "
        "to start saving your runs."
    )
    st.stop()

st.caption(
    f"Signed in as **{current_display_name() or uid}** "
    f"(`{uid}`). Runs below are private to your workspace folder."
)

store = get_store()
runs = store.list_runs(uid)

# --- Empty state ------------------------------------------------------------
if not runs:
    st.warning(
        "No saved runs yet. Head back to **Home**, paste your IDs (or upload a CSV), "
        "and click **Run Module 1 — Begin GAIA Survival Test**. "
        "We'll auto-save the survivors here."
    )
    st.stop()

# --- Summary table ----------------------------------------------------------
def _fmt_run(r):
    return {
        "run_id":       r.run_id,
        "saved (UTC)":  r.created_at.split(".")[0].replace("T", " "),
        "module":       r.module,
        "source":       r.source,
        "inputs":       r.inputs_count,
        "survivors":    r.survivors_count,
        "🥇 Certified": r.gold,
        "🥈 Need Follow Up": r.silver,
        "🥉 Failed":    r.failed,
        "label":        r.label or "",
    }


df_runs = pd.DataFrame([_fmt_run(r) for r in runs])
st.markdown(
    "<p style='font-size:1rem;font-weight:600;margin:0.6rem 0 0.1rem 0;'>"
    f"Saved runs ({len(runs)})</p>",
    unsafe_allow_html=True,
)
st.dataframe(df_runs, use_container_width=True, hide_index=True)

st.markdown("---")

# --- Per-run actions --------------------------------------------------------
labels = [f"{r.created_at.split('.')[0].replace('T', ' ')}  ·  {r.module}  ·  "
          f"{r.survivors_count}/{r.inputs_count} survivors  ·  {r.run_id}"
          for r in runs]
choice = st.selectbox("Open a run", options=range(len(runs)), format_func=lambda i: labels[i])

selected = runs[choice]
record = store.load_run(uid, selected.run_id)

st.markdown(
    "<p style='font-size:1rem;font-weight:600;margin:0.6rem 0 0.1rem 0;'>"
    f"Run details — <code>{selected.run_id}</code></p>",
    unsafe_allow_html=True,
)
meta_cols = st.columns(4)
meta_cols[0].metric("Inputs",      selected.inputs_count)
meta_cols[1].metric("Survivors",   selected.survivors_count)
meta_cols[2].metric("🥇 Certified", selected.gold)
meta_cols[3].metric("🥉 Failed",    selected.failed)

# Show survivors frame if present.
survivors = record.frames.get("survivors")
if survivors is not None and not survivors.empty:
    preview_cols = [c for c in [
        "source_id", "gaia_dr3_name", "ra", "dec",
        "teff_gspphot", "logg_gspphot", "ruwe", "bp_rp", "tier",
    ] if c in survivors.columns]
    if not preview_cols:
        preview_cols = list(survivors.columns[:8])
    st.dataframe(survivors[preview_cols].head(50), use_container_width=True, hide_index=True)

    csv_buf = io.StringIO()
    survivors.to_csv(csv_buf, index=False)
    st.download_button(
        "⬇️ Download survivors.csv",
        data=csv_buf.getvalue(),
        file_name=f"survivors_{selected.run_id}.csv",
        mime="text/csv",
        type="primary",
    )

# --- Reload action ----------------------------------------------------------
st.markdown("")
reload_col, delete_col = st.columns([1, 1])
with reload_col:
    if st.button("⤴️ Reload this run into Home (Module 1)", type="primary"):
        st.session_state["pipeline_data"] = survivors.copy() if survivors is not None else None
        st.session_state["pipeline_step"] = 1
        st.session_state["pipeline_started"] = True
        st.session_state["m1_only"] = True
        st.session_state["m1_celebrated"] = True   # don't replay balloons
        st.session_state["m1_input_count"] = selected.inputs_count
        st.session_state["m1_survivor_count"] = selected.survivors_count
        st.session_state["m1_loaded_run_id"] = selected.run_id
        st.success(
            f"Run `{selected.run_id}` reloaded into Module 1. "
            f"Switch back to **Home** to continue."
        )

with delete_col:
    if st.button("🗑️ Delete this run", help="Permanently removes the run folder from disk."):
        store.delete_run(uid, selected.run_id)
        st.warning(f"Deleted `{selected.run_id}`. Refresh the page to update the list.")
