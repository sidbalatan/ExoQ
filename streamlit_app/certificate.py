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
            f"has identified  {survivors_count}  {word}  "
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
