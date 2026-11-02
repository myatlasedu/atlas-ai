"""Shared styling and visualization policy for Atlas AI summaries."""

from __future__ import annotations

import re
from typing import Mapping, Optional


# These colors are intentionally independent of the host theme. They are selected
# to remain visually distinct on both light and dark chart surfaces.
ATLAS_CHART_PALETTE = {
    "present": "#14B8A6",       # teal
    "absent": "#F43F5E",        # rose
    "late": "#F59E0B",          # amber
    "excused": "#8B5CF6",       # violet
    "healthroom": "#38BDF8",    # sky
    "primary": "#6366F1",       # indigo
    "secondary": "#06B6D4",     # cyan
    "tertiary": "#A3E635",      # lime
    "quaternary": "#F472B6",    # pink
    "neutral": "#94A3B8",       # slate
}


VISUALIZATION_PROMPT = """
SHARED ATLAS VISUALIZATION POLICY
- Make a deliberate presentation choice based on the actual structured data.
  Use compact KPI cards, charts/graphs, and tables when they add useful
  information; do not force a chart into a response with no meaningful data.
- Use only supplied records and values. Never invent points, dates, labels,
  totals, percentages, trends, or statuses. Do not calculate unless the
  intent-specific instructions explicitly permit it.
- Use bar charts for comparable categories, line charts for ordered numeric
  values over time, donut charts only for mutually exclusive parts of a known
  whole, and tables for detailed records or non-numeric event lists.
- Attendance: if period counts exist, distinguish present, absent/missed, late,
  excused, and health-room counts. Never label periods as days. Show the
  supplied attendance percentage as a KPI when present. Use daily records only
  when they are supplied; do not create missing dates.
- Keep prose concise and avoid repeating every chart value in prose.
- Return a self-contained HTML fragment, not Markdown, JSON, code fences, or
  commentary. Use semantic classes: atlas-response, atlas-card, atlas-text,
  atlas-muted, atlas-border, atlas-accent, atlas-badge, atlas-chart,
  atlas-chart__legend, atlas-table, atlas-table__head, atlas-table__row,
  atlas-table__cell.
- Text and surface styling must use injectable CSS variables with fallbacks:
  --atlas-text, --atlas-muted, --atlas-background, --atlas-card,
  --atlas-border, and --atlas-accent. Do not hard-code text/background colors
  on individual elements.
- CHART COLORS ARE THE EXCEPTION: use a stable, high-contrast palette that is
  independent of the active light/dark theme. Prefer these colors by meaning:
  present/positive #14B8A6, absent/negative #F43F5E, late/caution #F59E0B,
  excused #8B5CF6, health-room #38BDF8, primary #6366F1, secondary #06B6D4,
  tertiary #A3E635, and additional series #F472B6. Keep chart segments distinct
  with visible boundaries; never derive chart colors from text/background
  colors. Include labels or a legend so color is never the only indicator.
- When drawing charts, include an accessible label and a readable table/list
  fallback. Prefer CSS-based horizontal bars for category comparisons. Static
  inline SVG is permitted for exact, supplied data points. Never use scripts,
  event handlers, iframes, external libraries, external URLs, or external fonts.
- Include a scoped style block only when styling is needed. Keep the result
  responsive and compact for a narrow mobile chat. Escape dynamic text and
  close all HTML tags.
"""


class AtlasVisualizationStyle:
    """Build reusable Atlas CSS with injectable surfaces and fixed chart colors.

    Pass a mapping such as:
        {"text": "#F5F5F7", "muted": "#94A3B8",
         "background": "#000000", "card": "#1F1F23",
         "border": "#303038", "accent": "#6366F1"}

    Theme values affect text/surfaces only. The chart palette remains fixed so
    graph colors do not disappear when the host switches theme.
    """

    CHART_PALETTE = ATLAS_CHART_PALETTE
    DEFAULT_THEME = {
        "text": "#F5F5F7",
        "muted": "#94A3B8",
        "background": "transparent",
        "card": "#26262B",
        "border": "#303038",
        "accent": "#6366F1",
    }

    # CSS values are deliberately restricted to common safe color forms.
    _HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3})?$")
    _RGB_COLOR = re.compile(
        r"^(?:rgb|rgba|hsl|hsla)\(\s*[\d.%\s,/-]+\s*\)$",
        re.IGNORECASE,
    )
    _NAMED_COLORS = {"transparent", "black", "white", "currentColor"}

    @classmethod
    def _safe_color(cls, value: object, fallback: str) -> str:
        if not isinstance(value, str):
            return fallback
        candidate = value.strip()
        if (
            cls._HEX_COLOR.fullmatch(candidate)
            or cls._RGB_COLOR.fullmatch(candidate)
            or candidate in cls._NAMED_COLORS
        ):
            return candidate
        return fallback

    @classmethod
    def resolve_theme(
        cls,
        theme: Optional[Mapping[str, object]] = None,
    ) -> dict[str, str]:
        resolved = dict(cls.DEFAULT_THEME)
        if isinstance(theme, Mapping):
            for key in resolved:
                if key in theme:
                    resolved[key] = cls._safe_color(
                        theme[key],
                        resolved[key],
                    )
        return resolved

    @classmethod
    def css(cls, theme: Optional[Mapping[str, object]] = None) -> str:
        """Return the shared scoped stylesheet for Atlas visual summaries."""
        colors = cls.resolve_theme(theme)
        palette = cls.CHART_PALETTE
        return f"""
<style>
.atlas-response {{
  --atlas-text: {colors['text']};
  --atlas-muted: {colors['muted']};
  --atlas-background: {colors['background']};
  --atlas-card: {colors['card']};
  --atlas-border: {colors['border']};
  --atlas-accent: {colors['accent']};
  --atlas-chart-present: {palette['present']};
  --atlas-chart-absent: {palette['absent']};
  --atlas-chart-late: {palette['late']};
  --atlas-chart-excused: {palette['excused']};
  --atlas-chart-healthroom: {palette['healthroom']};
  --atlas-chart-primary: {palette['primary']};
  --atlas-chart-secondary: {palette['secondary']};
  --atlas-chart-tertiary: {palette['tertiary']};
  --atlas-chart-quaternary: {palette['quaternary']};
  color: var(--atlas-text);
  background: var(--atlas-background);
  font: 14px/1.45 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  max-width: 100%;
  box-sizing: border-box;
}}
.atlas-response *, .atlas-response *::before, .atlas-response *::after {{
  box-sizing: border-box;
}}
.atlas-response .atlas-text {{ color: var(--atlas-text); }}
.atlas-response .atlas-muted {{ color: var(--atlas-muted); }}
.atlas-response .atlas-card {{
  color: var(--atlas-text);
  background: var(--atlas-card);
  border: 1px solid var(--atlas-border);
  border-radius: 12px;
  padding: 12px;
  margin: 10px 0;
  min-width: 0;
}}
.atlas-response .atlas-border {{ border-color: var(--atlas-border); }}
.atlas-response .atlas-accent {{ color: var(--atlas-accent); }}
.atlas-response .atlas-chart {{ width: 100%; min-width: 0; overflow: hidden; }}
.atlas-response .atlas-chart__legend {{ list-style: none; margin: 0; padding: 0; }}
.atlas-response .atlas-table {{
  width: 100%; border-collapse: collapse; display: block;
  max-width: 100%; overflow-x: auto; font-size: 12px;
}}
.atlas-response .atlas-table__head,
.atlas-response .atlas-table__row {{ border-bottom: 1px solid var(--atlas-border); }}
.atlas-response .atlas-table__cell {{
  padding: 7px 8px; text-align: left; vertical-align: top;
  overflow-wrap: anywhere;
}}
.atlas-response .atlas-badge {{
  display: inline-block; border-radius: 999px; padding: 2px 7px;
  font-size: 11px;
}}
.atlas-response .atlas-chart__bar {{
  min-height: 8px; border-radius: 999px;
  border: 1px solid rgba(127,127,127,.35);
}}
.atlas-response .atlas-chart__swatch {{
  display: inline-block; width: 9px; height: 9px; border-radius: 3px;
  border: 1px solid rgba(127,127,127,.55); margin-right: 6px;
}}
.atlas-response .atlas-chart__present {{ color: {palette['present']}; }}
.atlas-response .atlas-chart__absent {{ color: {palette['absent']}; }}
.atlas-response .atlas-chart__late {{ color: {palette['late']}; }}
.atlas-response .atlas-chart__excused {{ color: {palette['excused']}; }}
.atlas-response .atlas-chart__healthroom {{ color: {palette['healthroom']}; }}
@media (max-width: 420px) {{
  .atlas-response .atlas-card {{ padding: 10px; }}
  .atlas-response .atlas-table__cell {{ padding: 6px; }}
}}
</style>
"""
