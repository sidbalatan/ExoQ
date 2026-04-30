"""
Resolve astronomical identifiers (Gaia DR3, TIC, KIC, EPIC, 2MASS, HD, HIP,
TYC, common names, …) to (RA, Dec) in decimal degrees.

Strategy:
  1. Simbad (`astroquery.simbad.Simbad.query_object`) — primary resolver.
  2. MAST TIC catalog query — fallback for TIC IDs that Simbad doesn't know.

Resolved tokens are cached in-process via `functools.lru_cache` so reruns of
the Streamlit script don't repeat network calls.
"""

from __future__ import annotations

import re
from functools import lru_cache
from typing import List, Optional, Tuple

# Lazy-loaded astroquery handles so importing this module is cheap.
_simbad = None
_mast_catalogs = None


def _get_simbad():
    global _simbad
    if _simbad is None:
        from astroquery.simbad import Simbad

        _simbad = Simbad()
        _simbad.TIMEOUT = 15
    return _simbad


def _get_mast_catalogs():
    global _mast_catalogs
    if _mast_catalogs is None:
        from astroquery.mast import Catalogs

        _mast_catalogs = Catalogs
    return _mast_catalogs


# ------------------------------------------------------------------
# Identifier classification + normalization
# ------------------------------------------------------------------
_PATTERNS = [
    (re.compile(r"^gaia\s*dr\s*[123]\s+\d+$", re.I), "gaia"),
    (re.compile(r"^tic\s+\d+$", re.I), "tic"),
    (re.compile(r"^kic\s+\d+$", re.I), "kic"),
    (re.compile(r"^epic\s+\d+$", re.I), "epic"),
    (re.compile(r"^2mass\s+j[0-9+\-.]+$", re.I), "2mass"),
    (re.compile(r"^hd\s+\d+$", re.I), "hd"),
    (re.compile(r"^hip\s+\d+$", re.I), "hip"),
    (re.compile(r"^tyc\s+[0-9\-]+$", re.I), "tyc"),
]


def classify(token: str) -> Optional[str]:
    """Return the identifier type for a token, or None if unrecognized."""
    s = (token or "").strip()
    for pat, kind in _PATTERNS:
        if pat.match(s):
            return kind
    # Bare large integer -> probably a Gaia DR3 source_id.
    if s.isdigit() and len(s) >= 10:
        return "gaia"
    return None


def normalize(token: str) -> str:
    """Normalize a token to a Simbad-friendly form."""
    s = (token or "").strip()
    if s.isdigit() and len(s) >= 10:
        return f"Gaia DR3 {s}"
    return re.sub(r"\s+", " ", s)


# ------------------------------------------------------------------
# Resolver
# ------------------------------------------------------------------
@lru_cache(maxsize=10000)
def resolve(token: str) -> Tuple[float, float, str]:
    """Resolve ``token`` to ``(ra_deg, dec_deg, resolved_label)``.

    Raises :class:`ValueError` if the identifier cannot be resolved.
    """
    name = normalize(token)
    kind = classify(name)

    # ---- Primary: Simbad -----------------------------------------
    try:
        Simbad = _get_simbad()
        result = Simbad.query_object(name)
    except Exception:
        result = None

    if result is not None and len(result) > 0:
        row = result[0]
        ra = _extract_ra(row)
        dec = _extract_dec(row)
        if ra is not None and dec is not None:
            return float(ra), float(dec), name

    # ---- Fallback: MAST TIC catalog ------------------------------
    if kind == "tic":
        m = re.match(r"^tic\s+(\d+)$", name, re.I)
        if m:
            tic_id = m.group(1)
            try:
                Catalogs = _get_mast_catalogs()
                rows = Catalogs.query_criteria(catalog="TIC", ID=tic_id)
                if rows is not None and len(rows) > 0:
                    return float(rows[0]["ra"]), float(rows[0]["dec"]), name
            except Exception:
                pass

    raise ValueError(f"Could not resolve identifier '{token}'")


def _extract_ra(row) -> Optional[float]:
    for col in ("ra", "RA"):
        if col in row.colnames:
            val = row[col]
            try:
                return float(val)
            except (ValueError, TypeError):
                try:
                    from astropy.coordinates import Angle
                    import astropy.units as u

                    return float(Angle(str(val), unit=u.hourangle).degree)
                except Exception:
                    continue
    return None


def _extract_dec(row) -> Optional[float]:
    for col in ("dec", "DEC"):
        if col in row.colnames:
            val = row[col]
            try:
                return float(val)
            except (ValueError, TypeError):
                try:
                    from astropy.coordinates import Angle
                    import astropy.units as u

                    return float(Angle(str(val), unit=u.deg).degree)
                except Exception:
                    continue
    return None


# ------------------------------------------------------------------
# High-level multi-line parser
# ------------------------------------------------------------------
def parse_manual_input(text: str) -> Tuple[List[dict], List[str]]:
    """Parse the manual-entry textarea.

    Each non-empty / non-comment line can be one of:
      * ``RA, Dec`` numeric pair in decimal degrees.
      * An astronomical identifier (Gaia DR3 / TIC / KIC / EPIC / 2MASS / HD /
        HIP / TYC / common name).
      * A bare large integer (assumed to be a Gaia DR3 ``source_id``).

    Returns ``(rows, unresolved)`` where ``rows`` is a list of dicts
    ``{ra, dec, identifier, resolved_label}`` and ``unresolved`` is a list of
    raw lines that could not be parsed or resolved.
    """
    rows: List[dict] = []
    unresolved: List[str] = []

    for line in (text or "").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue

        # Try numeric RA, Dec first -----------------------------------
        parts = [p for p in s.replace(",", " ").split() if p]
        if len(parts) >= 2:
            try:
                ra = float(parts[0])
                dec = float(parts[1])
                rows.append(
                    {"ra": ra, "dec": dec, "identifier": "", "resolved_label": ""}
                )
                continue
            except ValueError:
                pass  # fall through to identifier resolution

        # Try identifier resolution -----------------------------------
        try:
            ra, dec, label = resolve(s)
            rows.append(
                {"ra": ra, "dec": dec, "identifier": s, "resolved_label": label}
            )
        except Exception:
            unresolved.append(s)

    return rows, unresolved
