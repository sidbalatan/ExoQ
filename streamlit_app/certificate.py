"""Render a downloadable Certificate of Discovery as a PNG.

The certificate is rendered with matplotlib (already a project dependency)
so we don't add any new packages. Output is returned as raw PNG bytes,
ready for ``st.download_button`` and ``st.image``.

Design notes
------------
* Landscape 1600x1000 for high-DPI social-share use (Twitter card 1200x675
  is the smallest target; this scales down cleanly).
* Muted slate / navy palette -- nothing loud. The audience is the science
  community.
* Every datum on the certificate is derived from the same DataFrame the
  GAIA Survival Test scored, so what users share matches what they ran.
* No marketing fluff: explicit attribution to ESA Gaia DR3.
"""

from __future__ import annotations

import io
from datetime import datetime, timezone
from typing import Iterable, Optional

import matplotlib
matplotlib.use("Agg")  # safe for non-GUI backends (Streamlit / headless)

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches


# Brand palette (kept conservative on purpose).
_BG_OUTER     = "#0b1220"   # near-black navy
_BG_INNER     = "#101a30"   # inner panel
_INK_PRIMARY  = "#e6edf3"   # near-white
_INK_MUTED    = "#9aa4b2"   # cool grey
_ACCENT_GOLD  = "#d4af37"
_ACCENT_LINE  = "#3b4a66"


def _short_id(sid) -> str:
    """Format a Gaia DR3 source_id for display (full digits, not exp)."""
    try:
        return f"Gaia DR3 {int(sid)}"
    except Exception:
        return str(sid)


def render_module3_certificate(
    *,
    display_name: str,
    total_stars: int,
    stars_with_data: int,
    total_observation_days: float,
    sectors_covered: int,
    sample_source_ids: Optional[Iterable] = None,
    run_id: str = "",
    issued_at: Optional[datetime] = None,
) -> bytes:
    """Return PNG bytes of a Module 3 TESS Light Curves Certificate."""
    
    issued_at = issued_at or datetime.now(timezone.utc)
    name = (display_name or "ExoQ Pioneer").strip() or "ExoQ Pioneer"
    
    fig = plt.figure(figsize=(16, 10), dpi=120, facecolor=_BG_OUTER)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 10)
    ax.axis("off")
    
    # Inner panel
    panel = mpatches.FancyBboxPatch(
        (0.5, 0.5), 15, 9,
        boxstyle="round,pad=0.02,rounding_size=0.25",
        linewidth=2,
        edgecolor=_ACCENT_LINE,
        facecolor=_BG_INNER,
    )
    ax.add_patch(panel)
    
    # Decorative thin gold accent rule under the title
    ax.plot([4.5, 11.5], [8.05, 8.05], color=_ACCENT_GOLD, linewidth=1.2, alpha=0.9)
    
    # Branding
    ax.text(8, 9.05, "ExoQ", color=_INK_PRIMARY,
            ha="center", va="center", fontsize=42, fontweight="bold",
            family="DejaVu Sans")
    ax.text(8, 8.45, "Module 3: TESS Light Curves Certificate",
            color=_INK_MUTED, ha="center", va="center",
            fontsize=18, fontstyle="italic", family="DejaVu Sans")
    
    # Recipient line
    ax.text(8, 7.4, "This certifies that",
            color=_INK_MUTED, ha="center", va="center", fontsize=14)
    ax.text(8, 6.55, name,
            color=_INK_PRIMARY, ha="center", va="center",
            fontsize=42, fontweight="bold")
    
    # Underline under name
    ax.plot([4.5, 11.5], [6.05, 6.05], color=_ACCENT_LINE, linewidth=0.8)
    
    # Achievement statement
    statement = (
        f"📈 has successfully retrieved TESS light curves for  {total_stars}  K Dwarf stars  "
        f"from NASA's TESS mission,\n"
        f"accumulating {total_observation_days:.1f} days of photometric data across {sectors_covered} sectors."
    )
    ax.text(8, 5.35, statement,
            color=_INK_PRIMARY, ha="center", va="center",
            fontsize=18, linespacing=1.5)
    
    # Light curve breakdown row
    tier_y = 4.0
    tier_x = [4.6, 8.0, 11.4]
    tier_labels = ["Stars with TESS Data", "Total Observation Days", "Sectors Covered"]
    tier_emojis = ["📈", "🔭", "🌍"]
    tier_values = [stars_with_data, f"{total_observation_days:.1f}", sectors_covered]
    for x, lbl, em, val in zip(tier_x, tier_labels, tier_emojis, tier_values):
        ax.text(x, tier_y + 0.55, em,
                color=_ACCENT_GOLD, ha="center", va="center",
                fontsize=22, fontweight="bold")
        ax.text(x, tier_y, str(val),
                color=_INK_PRIMARY, ha="center", va="center",
                fontsize=32, fontweight="bold")
        ax.text(x, tier_y - 0.55, lbl,
                color=_INK_MUTED, ha="center", va="center",
                fontsize=12)
    
    # Sample star IDs
    if sample_source_ids:
        ids = list(sample_source_ids)[:5]
        if ids:
            sample_text = "TESS-observed stars include: " + " · ".join(_short_id(s) for s in ids)
            if total_stars > len(ids):
                sample_text += f"  (+{total_stars - len(ids)} more)"
            ax.text(8, 2.55, sample_text,
                    color=_INK_MUTED, ha="center", va="center",
                    fontsize=10, family="DejaVu Sans Mono")
    
    # Footer: TESS attribution (left), date + run id (right)
    ax.plot([1.0, 15.0], [1.5, 1.5], color=_ACCENT_LINE, linewidth=0.6)
    
    ax.text(1.2, 1.05, "Verified by NASA TESS",
            color=_INK_PRIMARY, ha="left", va="center",
            fontsize=12, fontweight="bold")
    ax.text(1.2, 0.7, "tess.mit.edu · MAST API · light curve data",
            color=_INK_MUTED, ha="left", va="center", fontsize=9)
    
    issued_str = issued_at.strftime("Issued %Y-%m-%d %H:%M UTC")
    ax.text(14.8, 1.05, issued_str,
            color=_INK_PRIMARY, ha="right", va="center", fontsize=11)
    if run_id:
        ax.text(14.8, 0.7, f"Run ID: {run_id}",
                color=_INK_MUTED, ha="right", va="center",
                fontsize=8, family="DejaVu Sans Mono")
    
    # Tag line
    ax.text(8, 0.25, "ExoQ — Community Quest for Earth 2.0",
            color=_INK_MUTED, ha="center", va="center",
            fontsize=9, fontstyle="italic")
    
    buf = io.BytesIO()
    fig.savefig(buf, format="png", facecolor=_BG_OUTER, dpi=120)
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


def render_module5_certificate(
    *,
    display_name: str,
    total_stars: int,
    highly_habitable: int,
    habitable_exoplanets: int,
    best_star_score: float,
    max_esi: float,
    sample_source_ids: Optional[Iterable] = None,
    run_id: str = "",
    issued_at: Optional[datetime] = None,
) -> bytes:
    """Return PNG bytes of a Module 5 Habitability Scoring Certificate."""
    
    issued_at = issued_at or datetime.now(timezone.utc)
    name = (display_name or "ExoQ Pioneer").strip() or "ExoQ Pioneer"
    
    fig = plt.figure(figsize=(16, 10), dpi=120, facecolor=_BG_OUTER)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 10)
    ax.axis("off")
    
    # Inner panel
    panel = mpatches.FancyBboxPatch(
        (0.5, 0.5), 15, 9,
        boxstyle="round,pad=0.02,rounding_size=0.25",
        linewidth=2,
        edgecolor=_ACCENT_LINE,
        facecolor=_BG_INNER,
    )
    ax.add_patch(panel)
    
    # Decorative thin gold accent rule under the title
    ax.plot([4.5, 11.5], [8.05, 8.05], color=_ACCENT_GOLD, linewidth=1.2, alpha=0.9)
    
    # Branding
    ax.text(8, 9.05, "ExoQ", color=_INK_PRIMARY,
            ha="center", va="center", fontsize=42, fontweight="bold",
            family="DejaVu Sans")
    ax.text(8, 8.45, "Module 5: Habitability Scoring Certificate",
            color=_INK_MUTED, ha="center", va="center",
            fontsize=18, fontstyle="italic", family="DejaVu Sans")
    
    # Recipient line
    ax.text(8, 7.4, "This certifies that",
            color=_INK_MUTED, ha="center", va="center", fontsize=14)
    ax.text(8, 6.55, name,
            color=_INK_PRIMARY, ha="center", va="center",
            fontsize=42, fontweight="bold")
    
    # Underline under name
    ax.plot([4.5, 11.5], [6.05, 6.05], color=_ACCENT_LINE, linewidth=0.8)
    
    # Achievement statement
    statement = (
        f"🌍 has successfully evaluated  {total_stars}  stars  "
        f"for habitability potential,\n"
        f"identifying {highly_habitable} highly habitable stars and {habitable_exoplanets} "
        f"potentially habitable exoplanets."
    )
    ax.text(8, 5.35, statement,
            color=_INK_PRIMARY, ha="center", va="center",
            fontsize=18, linespacing=1.5)
    
    # Habitability breakdown row
    tier_y = 4.0
    tier_x = [4.6, 8.0, 11.4]
    tier_labels = ["Highly Habitable Stars", "Habitable Exoplanets", "Max Earth Similarity"]
    tier_emojis = ["🌟", "🪐", "🌍"]
    tier_values = [highly_habitable, habitable_exoplanets, f"{max_esi:.2f}"]
    for x, lbl, em, val in zip(tier_x, tier_labels, tier_emojis, tier_values):
        ax.text(x, tier_y + 0.55, em,
                color=_ACCENT_GOLD, ha="center", va="center",
                fontsize=22, fontweight="bold")
        ax.text(x, tier_y, str(val),
                color=_INK_PRIMARY, ha="center", va="center",
                fontsize=32, fontweight="bold")
        ax.text(x, tier_y - 0.55, lbl,
                color=_INK_MUTED, ha="center", va="center",
                fontsize=12)
    
    # Sample star IDs
    if sample_source_ids:
        ids = list(sample_source_ids)[:5]
        if ids:
            sample_text = "Top habitable stars include: " + " · ".join(_short_id(s) for s in ids)
            if total_stars > len(ids):
                sample_text += f"  (+{total_stars - len(ids)} more)"
            ax.text(8, 2.55, sample_text,
                    color=_INK_MUTED, ha="center", va="center",
                    fontsize=10, family="DejaVu Sans Mono")
    
    # Footer: ESI attribution (left), date + run id (right)
    ax.plot([1.0, 15.0], [1.5, 1.5], color=_ACCENT_LINE, linewidth=0.6)
    
    ax.text(1.2, 1.05, "Verified by Earth Similarity Index",
            color=_INK_PRIMARY, ha="left", va="center",
            fontsize=12, fontweight="bold")
    ax.text(1.2, 0.7, "ESI · habitability scoring · exoplanet potential",
            color=_INK_MUTED, ha="left", va="center", fontsize=9)
    
    issued_str = issued_at.strftime("Issued %Y-%m-%d %H:%M UTC")
    ax.text(14.8, 1.05, issued_str,
            color=_INK_PRIMARY, ha="right", va="center", fontsize=11)
    if run_id:
        ax.text(14.8, 0.7, f"Run ID: {run_id}",
                color=_INK_MUTED, ha="right", va="center",
                fontsize=8, family="DejaVu Sans Mono")
    
    # Tag line
    ax.text(8, 0.25, "ExoQ — Community Quest for Earth 2.0",
            color=_INK_MUTED, ha="center", va="center",
            fontsize=9, fontstyle="italic")
    
    buf = io.BytesIO()
    fig.savefig(buf, format="png", facecolor=_BG_OUTER, dpi=120)
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


def render_module4_certificate(
    *,
    display_name: str,
    total_stars: int,
    transit_candidates: int,
    passed_threshold: int,
    max_snr: float,
    average_period: float,
    sample_source_ids: Optional[Iterable] = None,
    run_id: str = "",
    issued_at: Optional[datetime] = None,
) -> bytes:
    """Return PNG bytes of a Module 4 Transit Detection Certificate."""
    
    issued_at = issued_at or datetime.now(timezone.utc)
    name = (display_name or "ExoQ Pioneer").strip() or "ExoQ Pioneer"
    
    fig = plt.figure(figsize=(16, 10), dpi=120, facecolor=_BG_OUTER)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 10)
    ax.axis("off")
    
    # Inner panel
    panel = mpatches.FancyBboxPatch(
        (0.5, 0.5), 15, 9,
        boxstyle="round,pad=0.02,rounding_size=0.25",
        linewidth=2,
        edgecolor=_ACCENT_LINE,
        facecolor=_BG_INNER,
    )
    ax.add_patch(panel)
    
    # Decorative thin gold accent rule under the title
    ax.plot([4.5, 11.5], [8.05, 8.05], color=_ACCENT_GOLD, linewidth=1.2, alpha=0.9)
    
    # Branding
    ax.text(8, 9.05, "ExoQ", color=_INK_PRIMARY,
            ha="center", va="center", fontsize=42, fontweight="bold",
            family="DejaVu Sans")
    ax.text(8, 8.45, "Module 4: Transit Detection Certificate",
            color=_INK_MUTED, ha="center", va="center",
            fontsize=18, fontstyle="italic", family="DejaVu Sans")
    
    # Recipient line
    ax.text(8, 7.4, "This certifies that",
            color=_INK_MUTED, ha="center", va="center", fontsize=14)
    ax.text(8, 6.55, name,
            color=_INK_PRIMARY, ha="center", va="center",
            fontsize=42, fontweight="bold")
    
    # Underline under name
    ax.plot([4.5, 11.5], [6.05, 6.05], color=_ACCENT_LINE, linewidth=0.8)
    
    # Achievement statement
    statement = (
        f"🎯 has successfully analyzed  {total_stars}  TESS light curves  "
        f"using the BLS periodogram algorithm,\n"
        f"identifying {transit_candidates} transit candidates with {passed_threshold} high-confidence detections."
    )
    ax.text(8, 5.35, statement,
            color=_INK_PRIMARY, ha="center", va="center",
            fontsize=18, linespacing=1.5)
    
    # Transit detection breakdown row
    tier_y = 4.0
    tier_x = [4.6, 8.0, 11.4]
    tier_labels = ["Transit Candidates", "Passed Threshold", "Max Signal-to-Noise"]
    tier_emojis = ["🎯", "✅", "📊"]
    tier_values = [transit_candidates, passed_threshold, f"{max_snr:.1f}"]
    for x, lbl, em, val in zip(tier_x, tier_labels, tier_emojis, tier_values):
        ax.text(x, tier_y + 0.55, em,
                color=_ACCENT_GOLD, ha="center", va="center",
                fontsize=22, fontweight="bold")
        ax.text(x, tier_y, str(val),
                color=_INK_PRIMARY, ha="center", va="center",
                fontsize=32, fontweight="bold")
        ax.text(x, tier_y - 0.55, lbl,
                color=_INK_MUTED, ha="center", va="center",
                fontsize=12)
    
    # Sample star IDs
    if sample_source_ids:
        ids = list(sample_source_ids)[:5]
        if ids:
            sample_text = "Transit candidate stars include: " + " · ".join(_short_id(s) for s in ids)
            if total_stars > len(ids):
                sample_text += f"  (+{total_stars - len(ids)} more)"
            ax.text(8, 2.55, sample_text,
                    color=_INK_MUTED, ha="center", va="center",
                    fontsize=10, family="DejaVu Sans Mono")
    
    # Footer: BLS attribution (left), date + run id (right)
    ax.plot([1.0, 15.0], [1.5, 1.5], color=_ACCENT_LINE, linewidth=0.6)
    
    ax.text(1.2, 1.05, "Verified by BLS Periodogram",
            color=_INK_PRIMARY, ha="left", va="center",
            fontsize=12, fontweight="bold")
    ax.text(1.2, 0.7, "Box Least Squares · transit detection · signal analysis",
            color=_INK_MUTED, ha="left", va="center", fontsize=9)
    
    issued_str = issued_at.strftime("Issued %Y-%m-%d %H:%M UTC")
    ax.text(14.8, 1.05, issued_str,
            color=_INK_PRIMARY, ha="right", va="center", fontsize=11)
    if run_id:
        ax.text(14.8, 0.7, f"Run ID: {run_id}",
                color=_INK_MUTED, ha="right", va="center",
                fontsize=8, family="DejaVu Sans Mono")
    
    # Tag line
    ax.text(8, 0.25, "ExoQ — Community Quest for Earth 2.0",
            color=_INK_MUTED, ha="center", va="center",
            fontsize=9, fontstyle="italic")
    
    buf = io.BytesIO()
    fig.savefig(buf, format="png", facecolor=_BG_OUTER, dpi=120)
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


def render_module2_certificate(
    *,
    display_name: str,
    total_stars: int,
    exoplanet_hosts: int,
    virgin_targets: int,
    sample_source_ids: Optional[Iterable] = None,
    run_id: str = "",
    issued_at: Optional[datetime] = None,
) -> bytes:
    """Return PNG bytes of a Module 2 Exoplanet Quest Certificate."""
    
    issued_at = issued_at or datetime.now(timezone.utc)
    name = (display_name or "ExoQ Pioneer").strip() or "ExoQ Pioneer"
    
    fig = plt.figure(figsize=(16, 10), dpi=120, facecolor=_BG_OUTER)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 10)
    ax.axis("off")
    
    # Inner panel
    panel = mpatches.FancyBboxPatch(
        (0.5, 0.5), 15, 9,
        boxstyle="round,pad=0.02,rounding_size=0.25",
        linewidth=2,
        edgecolor=_ACCENT_LINE,
        facecolor=_BG_INNER,
    )
    ax.add_patch(panel)
    
    # Decorative thin gold accent rule under the title
    ax.plot([4.5, 11.5], [8.05, 8.05], color=_ACCENT_GOLD, linewidth=1.2, alpha=0.9)
    
    # Branding
    ax.text(8, 9.05, "ExoQ", color=_INK_PRIMARY,
            ha="center", va="center", fontsize=42, fontweight="bold",
            family="DejaVu Sans")
    ax.text(8, 8.45, "Module 2: Exoplanet Quest Certificate",
            color=_INK_MUTED, ha="center", va="center",
            fontsize=18, fontstyle="italic", family="DejaVu Sans")
    
    # Recipient line
    ax.text(8, 7.4, "This certifies that",
            color=_INK_MUTED, ha="center", va="center", fontsize=14)
    ax.text(8, 6.55, name,
            color=_INK_PRIMARY, ha="center", va="center",
            fontsize=42, fontweight="bold")
    
    # Underline under name
    ax.plot([4.5, 11.5], [6.05, 6.05], color=_ACCENT_LINE, linewidth=0.8)
    
    # Achievement statement
    statement = (
        f"🪐 has successfully cross-matched  {total_stars}  K Dwarf stars  "
        f"with the NASA Exoplanet Archive,\n"
        f"identifying {exoplanet_hosts} exoplanet hosts and {virgin_targets} virgin discovery targets."
    )
    ax.text(8, 5.35, statement,
            color=_INK_PRIMARY, ha="center", va="center",
            fontsize=18, linespacing=1.5)
    
    # Cross-match breakdown row
    tier_y = 4.0
    tier_x = [4.6, 8.0, 11.4]
    tier_labels = ["Exoplanet Hosts", "Virgin Targets", "Total Stars"]
    tier_emojis = ["🪐", "🌟", "⭐"]
    tier_values = [exoplanet_hosts, virgin_targets, total_stars]
    for x, lbl, em, val in zip(tier_x, tier_labels, tier_emojis, tier_values):
        ax.text(x, tier_y + 0.55, em,
                color=_ACCENT_GOLD, ha="center", va="center",
                fontsize=22, fontweight="bold")
        ax.text(x, tier_y, str(val),
                color=_INK_PRIMARY, ha="center", va="center",
                fontsize=32, fontweight="bold")
        ax.text(x, tier_y - 0.55, lbl,
                color=_INK_MUTED, ha="center", va="center",
                fontsize=12)
    
    # Sample star IDs
    if sample_source_ids:
        ids = list(sample_source_ids)[:5]
        if ids:
            sample_text = "Cross-matched stars include: " + " · ".join(_short_id(s) for s in ids)
            if total_stars > len(ids):
                sample_text += f"  (+{total_stars - len(ids)} more)"
            ax.text(8, 2.55, sample_text,
                    color=_INK_MUTED, ha="center", va="center",
                    fontsize=10, family="DejaVu Sans Mono")
    
    # Footer: NASA attribution (left), date + run id (right)
    ax.plot([1.0, 15.0], [1.5, 1.5], color=_ACCENT_LINE, linewidth=0.6)
    
    ax.text(1.2, 1.05, "Verified by NASA Exoplanet Archive",
            color=_INK_PRIMARY, ha="left", va="center",
            fontsize=12, fontweight="bold")
    ax.text(1.2, 0.7, "exoplanetarchive.ipac.caltech.edu · PS Catalog · live API",
            color=_INK_MUTED, ha="left", va="center", fontsize=9)
    
    issued_str = issued_at.strftime("Issued %Y-%m-%d %H:%M UTC")
    ax.text(14.8, 1.05, issued_str,
            color=_INK_PRIMARY, ha="right", va="center", fontsize=11)
    if run_id:
        ax.text(14.8, 0.7, f"Run ID: {run_id}",
                color=_INK_MUTED, ha="right", va="center",
                fontsize=8, family="DejaVu Sans Mono")
    
    # Tag line
    ax.text(8, 0.25, "ExoQ — Community Quest for Earth 2.0",
            color=_INK_MUTED, ha="center", va="center",
            fontsize=9, fontstyle="italic")
    
    buf = io.BytesIO()
    fig.savefig(buf, format="png", facecolor=_BG_OUTER, dpi=120)
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


def render_certificate(
    *,
    display_name: str,
    survivors_count: int,
    inputs_count: int,
    gold: int,
    silver: int,
    failed: int,
    sample_source_ids: Optional[Iterable] = None,
    run_id: str = "",
    issued_at: Optional[datetime] = None,
) -> bytes:
    """Return PNG bytes of a single Certificate of Discovery."""

    issued_at = issued_at or datetime.now(timezone.utc)
    name = (display_name or "ExoQ Pioneer").strip() or "ExoQ Pioneer"

    fig = plt.figure(figsize=(16, 10), dpi=120, facecolor=_BG_OUTER)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 10)
    ax.axis("off")

    # Inner panel
    panel = mpatches.FancyBboxPatch(
        (0.5, 0.5), 15, 9,
        boxstyle="round,pad=0.02,rounding_size=0.25",
        linewidth=2,
        edgecolor=_ACCENT_LINE,
        facecolor=_BG_INNER,
    )
    ax.add_patch(panel)

    # Decorative thin gold accent rule under the title
    ax.plot([4.5, 11.5], [8.05, 8.05], color=_ACCENT_GOLD, linewidth=1.2, alpha=0.9)

    # Branding
    ax.text(8, 9.05, "ExoQ", color=_INK_PRIMARY,
            ha="center", va="center", fontsize=42, fontweight="bold",
            family="DejaVu Sans")
    ax.text(8, 8.45, "Certificate of Discovery",
            color=_INK_MUTED, ha="center", va="center",
            fontsize=18, fontstyle="italic", family="DejaVu Sans")

    # Recipient line
    ax.text(8, 7.4, "This certifies that",
            color=_INK_MUTED, ha="center", va="center", fontsize=14)
    ax.text(8, 6.55, name,
            color=_INK_PRIMARY, ha="center", va="center",
            fontsize=42, fontweight="bold")

    # Underline under name
    ax.plot([4.5, 11.5], [6.05, 6.05], color=_ACCENT_LINE, linewidth=0.8)

    # Achievement statement
    if survivors_count <= 0:
        statement = (
            f"completed a GAIA Survival Test on {inputs_count} stellar candidate(s) "
            f"using the ExoQ Pipeline."
        )
    else:
        word = "K Dwarf" if survivors_count == 1 else "K Dwarfs"
        statement = (
            f"🎉 has successfully discovered  {survivors_count}  {word}  "
            f"using the ExoQ Pipeline,\n"
            f"validated against the live ESA Gaia DR3 archive."
        )
    ax.text(8, 5.35, statement,
            color=_INK_PRIMARY, ha="center", va="center",
            fontsize=18, linespacing=1.5)

    # Tier breakdown row
    tier_y = 4.0
    tier_x = [4.6, 8.0, 11.4]
    tier_labels = ["Gaia Certified K Dwarf", "Need Follow Up", "Failed"]
    tier_emojis = ["I", "II", "III"]   # Roman numerals read more formal
    tier_values = [gold, silver, failed]
    for x, lbl, em, val in zip(tier_x, tier_labels, tier_emojis, tier_values):
        ax.text(x, tier_y + 0.55, em,
                color=_ACCENT_GOLD, ha="center", va="center",
                fontsize=22, fontweight="bold")
        ax.text(x, tier_y, str(val),
                color=_INK_PRIMARY, ha="center", va="center",
                fontsize=32, fontweight="bold")
        ax.text(x, tier_y - 0.55, lbl,
                color=_INK_MUTED, ha="center", va="center",
                fontsize=12)

    # Sample survivor IDs
    if sample_source_ids:
        ids = list(sample_source_ids)[:5]
        if ids:
            sample_text = "Survivors include: " + " · ".join(_short_id(s) for s in ids)
            if survivors_count > len(ids):
                sample_text += f"  (+{survivors_count - len(ids)} more)"
            ax.text(8, 2.55, sample_text,
                    color=_INK_MUTED, ha="center", va="center",
                    fontsize=10, family="DejaVu Sans Mono")

    # Footer: Gaia attribution (left), date + run id (right)
    ax.plot([1.0, 15.0], [1.5, 1.5], color=_ACCENT_LINE, linewidth=0.6)

    ax.text(1.2, 1.05, "Verified by ESA Gaia DR3",
            color=_INK_PRIMARY, ha="left", va="center",
            fontsize=12, fontweight="bold")
    ax.text(1.2, 0.7, "gaiadr3.gaia_source · astrophysical_parameters · live ADQL",
            color=_INK_MUTED, ha="left", va="center", fontsize=9)

    issued_str = issued_at.strftime("Issued %Y-%m-%d %H:%M UTC")
    ax.text(14.8, 1.05, issued_str,
            color=_INK_PRIMARY, ha="right", va="center", fontsize=11)
    if run_id:
        ax.text(14.8, 0.7, f"Run ID: {run_id}",
                color=_INK_MUTED, ha="right", va="center",
                fontsize=8, family="DejaVu Sans Mono")

    # Tag line
    ax.text(8, 0.25, "ExoQ — Community Quest for Earth 2.0",
            color=_INK_MUTED, ha="center", va="center",
            fontsize=9, fontstyle="italic")

    buf = io.BytesIO()
    fig.savefig(buf, format="png", facecolor=_BG_OUTER, dpi=120)
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()
