"""Google Search Console overview panels: totals stat chips + top-queries
mini-table. The striking-distance bar panel lives in the compose module
(`charts.py`) since it's the one panel existing tests monkeypatch directly.
"""

from typing import Any, Dict

from .charts_base import _draw_mini_table_panel, _draw_tiles_panel, _fmt_num, _fmt_pct, _fmt_position

TOP_QUERIES_TOP_N = 8
GSC_TOTALS_COLS = 4

# ---- panel: GSC totals --------------------------------------------------------------


def _draw_gsc_totals(fig, cell, gsc: Dict[str, Any]) -> None:
    totals = (gsc or {}).get("totals") or {}
    tiles = [
        {"value": _fmt_num(totals.get("clicks", 0)), "label": "Clicks", "value_fontsize": 15},
        {"value": _fmt_num(totals.get("impressions", 0)), "label": "Impressions", "value_fontsize": 15},
        {"value": _fmt_pct(totals.get("ctr", 0)), "label": "CTR", "value_fontsize": 15},
        {"value": _fmt_position(totals.get("avg_position", 0)), "label": "Avg Position", "value_fontsize": 15},
    ]
    _draw_tiles_panel(fig, cell, "Search Console Totals", tiles if totals else [], GSC_TOTALS_COLS,
                       "No Search Console totals available")


# ---- panel: GSC top queries -----------------------------------------------------------


def _draw_gsc_top_queries(fig, cell, gsc: Dict[str, Any]) -> None:
    top_queries = ((gsc or {}).get("top_queries") or [])[:TOP_QUERIES_TOP_N]
    rows = [
        [q["query"], _fmt_num(q["clicks"]), _fmt_num(q["impressions"]), _fmt_pct(q["ctr"]), _fmt_position(q["position"])]
        for q in top_queries
    ]
    _draw_mini_table_panel(
        fig, cell, "Top Queries", ["Query", "Clicks", "Impr", "CTR", "Pos"], rows,
        col_x=[0.0, 0.58, 0.72, 0.86, 1.0], col_align=["left", "right", "right", "right", "right"],
        empty_message="no query data",
    )
