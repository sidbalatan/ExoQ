"""
Enrich a list of resolved manual-input rows with **live Gaia DR3** astrophysical
parameters via ADQL.

For each row from :func:`identifier_resolver.parse_manual_input` we need to
attach the columns the Gaia DR3 Survival Test classifier expects:

    teff_gspphot, logg_gspphot, ruwe, bp_rp, parallax

Strategy
--------
* Tokens that are Gaia DR3 source_ids -> one batched ADQL query against
  ``gaiadr3.gaia_source`` joined with ``gaiadr3.astrophysical_parameters``
  using ``WHERE source_id IN (...)``.
* All other tokens (TIC, HD, 2MASS, plain RA/Dec, …) -> per-row cone search
  at 3 arcsec radius; we take the closest Gaia DR3 source.

A 1-second courtesy sleep between cone-search calls keeps us friendly to the
Gaia archive even though ten queries per Run is well below any rate limit.

Notes
-----
* The Gaia archive sometimes warns about DR4 evolution; that's informational.
* ``astroquery.gaia.Gaia.launch_job`` is synchronous; for batches > ~100 rows
  switch to ``launch_job_async``.
"""

from __future__ import annotations

import re
import time
from functools import lru_cache
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# Lazy import so importing this module is cheap.
_gaia = None


def _get_gaia():
    """Return the singleton :class:`astroquery.gaia.GaiaClass` instance."""
    global _gaia
    if _gaia is None:
        from astroquery.gaia import Gaia  # noqa: WPS433 (deliberate lazy import)

        Gaia.MAIN_GAIA_TABLE = "gaiadr3.gaia_source"
        Gaia.ROW_LIMIT = -1  # unlimited
        _gaia = Gaia
    return _gaia


# ------------------------------------------------------------------
# Source-ID extraction
# ------------------------------------------------------------------
_GAIA_DR3_RE = re.compile(r"^\s*gaia\s*dr\s*3\s+(\d+)\s*$", re.I)
_BARE_INT_RE = re.compile(r"^\d{10,}$")  # bare large integer == Gaia DR3 id


def extract_gaia_source_id(token: str) -> Optional[int]:
    """Return the Gaia DR3 ``source_id`` encoded in *token*, or ``None``."""
    if not token:
        return None
    s = token.strip()
    m = _GAIA_DR3_RE.match(s)
    if m:
        return int(m.group(1))
    if _BARE_INT_RE.match(s):
        return int(s)
    return None


# ------------------------------------------------------------------
# Column set we always want returned per row
# ------------------------------------------------------------------
_ENRICHED_COLS = [
    "source_id",
    "ra",
    "dec",
    "parallax",
    "ruwe",
    "phot_g_mean_mag",
    "bp_rp",
    "teff_gspphot",
    "logg_gspphot",
]


# ------------------------------------------------------------------
# Batched ID lookup
# ------------------------------------------------------------------
@lru_cache(maxsize=4096)
def _cached_source_id_lookup(source_ids: Tuple[int, ...]) -> pd.DataFrame:
    """Fetch Gaia DR3 + astrophysical params for a tuple of ``source_id``.

    The tuple makes the result hashable so ``lru_cache`` can short-circuit
    duplicate queries within a Streamlit session.
    """
    if not source_ids:
        return pd.DataFrame(columns=_ENRICHED_COLS)
    Gaia = _get_gaia()
    id_list = ", ".join(str(int(s)) for s in source_ids)
    query = f"""
        SELECT
            g.source_id,
            g.ra, g.dec,
            g.parallax, g.parallax_error,
            g.ruwe,
            g.phot_g_mean_mag,
            g.bp_rp,
            ap.teff_gspphot,
            ap.logg_gspphot,
            ap.mh_gspphot
        FROM gaiadr3.gaia_source AS g
        LEFT JOIN gaiadr3.astrophysical_parameters AS ap
               ON g.source_id = ap.source_id
        WHERE g.source_id IN ({id_list})
    """
    job = Gaia.launch_job(query)
    table = job.get_results()
    return table.to_pandas()


# ------------------------------------------------------------------
# Per-row cone search
# ------------------------------------------------------------------
@lru_cache(maxsize=4096)
def _cached_cone_match(ra: float, dec: float, radius_arcsec: float = 3.0) -> Optional[dict]:
    """Return the closest Gaia DR3 row within *radius_arcsec* of (ra, dec).

    Returns a dict of the enriched columns or ``None`` if no Gaia DR3 source
    is found within the radius.
    """
    Gaia = _get_gaia()
    radius_deg = radius_arcsec / 3600.0
    query = f"""
        SELECT TOP 1
            g.source_id,
            g.ra, g.dec,
            g.parallax, g.parallax_error,
            g.ruwe,
            g.phot_g_mean_mag,
            g.bp_rp,
            ap.teff_gspphot,
            ap.logg_gspphot,
            ap.mh_gspphot,
            DISTANCE(POINT('ICRS', g.ra, g.dec),
                     POINT('ICRS', {ra}, {dec})) AS dist_deg
        FROM gaiadr3.gaia_source AS g
        LEFT JOIN gaiadr3.astrophysical_parameters AS ap
               ON g.source_id = ap.source_id
        WHERE 1 = CONTAINS(
            POINT('ICRS', g.ra, g.dec),
            CIRCLE('ICRS', {ra}, {dec}, {radius_deg})
        )
        ORDER BY dist_deg ASC
    """
    try:
        job = Gaia.launch_job(query)
        df = job.get_results().to_pandas()
    except Exception:
        return None
    if df.empty:
        return None
    return df.iloc[0].to_dict()


# ------------------------------------------------------------------
# Public entry point
# ------------------------------------------------------------------
def enrich_rows(
    rows: List[Dict],
    progress_cb=None,
) -> pd.DataFrame:
    """Enrich rows produced by ``parse_manual_input`` with Gaia DR3 columns.

    Parameters
    ----------
    rows
        List of dicts with at minimum ``ra``, ``dec``; optionally
        ``identifier`` and ``resolved_label``.
    progress_cb
        Optional callable ``(done, total, message)`` used for Streamlit
        progress reporting.

    Returns
    -------
    pandas.DataFrame
        One row per input row (some columns may be ``NaN`` if the live Gaia
        query had no match). Always includes ``ra``, ``dec``, ``source_id``,
        ``teff_gspphot``, ``logg_gspphot``, ``ruwe``, ``bp_rp``, ``parallax``,
        plus ``identifier``, ``resolved_label``, and ``gaia_match_arcsec``.
    """
    total = len(rows)

    # --- Phase 1: split rows into "have Gaia ID" vs "RA/Dec only" -----
    by_id_indices: Dict[int, List[int]] = {}
    cone_indices: List[int] = []
    for i, r in enumerate(rows):
        sid = extract_gaia_source_id(r.get("identifier") or r.get("resolved_label") or "")
        if sid is not None:
            by_id_indices.setdefault(sid, []).append(i)
        else:
            cone_indices.append(i)

    # --- Phase 2: batched source_id lookup ----------------------------
    id_lookup_df: Optional[pd.DataFrame] = None
    if by_id_indices:
        if progress_cb:
            progress_cb(0, total, f"Querying Gaia DR3 for {len(by_id_indices)} source_ids…")
        try:
            id_lookup_df = _cached_source_id_lookup(tuple(sorted(by_id_indices.keys())))
        except Exception as exc:
            id_lookup_df = pd.DataFrame()
            if progress_cb:
                progress_cb(0, total, f"Gaia source_id query failed: {exc}")

    by_sid: Dict[int, dict] = {}
    if id_lookup_df is not None and not id_lookup_df.empty:
        for _, row in id_lookup_df.iterrows():
            try:
                by_sid[int(row["source_id"])] = row.to_dict()
            except Exception:
                continue

    # --- Phase 3: per-row cone search for non-Gaia tokens -------------
    cone_results: Dict[int, Optional[dict]] = {}
    for offset, i in enumerate(cone_indices, start=1):
        if progress_cb:
            progress_cb(
                offset,
                len(cone_indices),
                f"Cone-matching against Gaia DR3 ({offset} / {len(cone_indices)})…",
            )
        ra = float(rows[i]["ra"])
        dec = float(rows[i]["dec"])
        try:
            cone_results[i] = _cached_cone_match(ra, dec, 3.0)
        except Exception:
            cone_results[i] = None
        time.sleep(0.5)  # courtesy spacing for the Gaia archive

    # --- Phase 4: assemble the output dataframe -----------------------
    enriched: List[dict] = []
    for i, r in enumerate(rows):
        out: Dict[str, object] = {
            "ra": float(r["ra"]),
            "dec": float(r["dec"]),
            "identifier": r.get("identifier", ""),
            "resolved_label": r.get("resolved_label", ""),
            "source_id": pd.NA,
            "parallax": np.nan,
            "ruwe": np.nan,
            "phot_g_mean_mag": np.nan,
            "bp_rp": np.nan,
            "teff_gspphot": np.nan,
            "logg_gspphot": np.nan,
            "gaia_match_arcsec": np.nan,
        }

        # Direct source_id hit
        sid = extract_gaia_source_id(r.get("identifier") or r.get("resolved_label") or "")
        if sid is not None and sid in by_sid:
            hit = by_sid[sid]
            for c in (
                "source_id", "ra", "dec", "parallax", "ruwe",
                "phot_g_mean_mag", "bp_rp", "teff_gspphot", "logg_gspphot",
            ):
                if c in hit and pd.notna(hit[c]):
                    out[c] = hit[c]
            out["gaia_match_arcsec"] = 0.0  # exact id match
        else:
            # Cone-match fallback
            hit = cone_results.get(i)
            if hit is not None:
                for c in (
                    "source_id", "parallax", "ruwe",
                    "phot_g_mean_mag", "bp_rp", "teff_gspphot", "logg_gspphot",
                ):
                    if c in hit and pd.notna(hit[c]):
                        out[c] = hit[c]
                # Distance back to the *requested* coords for transparency
                if "dist_deg" in hit and pd.notna(hit["dist_deg"]):
                    out["gaia_match_arcsec"] = float(hit["dist_deg"]) * 3600.0
                # Prefer the Gaia coordinates over the requested ones so the
                # downstream pipeline uses the precise position.
                for c in ("ra", "dec"):
                    if c in hit and pd.notna(hit[c]):
                        out[c] = float(hit[c])

        # Convenient label
        if pd.notna(out.get("source_id", pd.NA)) and out["source_id"] is not pd.NA:
            out["gaia_dr3_name"] = f"Gaia DR3 {int(out['source_id'])}"
        else:
            out["gaia_dr3_name"] = ""

        enriched.append(out)

    return pd.DataFrame(enriched)
