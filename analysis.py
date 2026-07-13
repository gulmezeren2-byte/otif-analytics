"""OTIF analysis: how measurement choices change the delivery-performance story.

Reads data/orders.csv, computes a ladder of five increasingly honest metrics,
saves publication-ready SVG charts into charts/, and prints the headline
numbers as JSON (consumed by the README).
"""

from __future__ import annotations

import json

import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import pandas as pd

# ---------------------------------------------------------------- palette ---
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
BASELINE = "#c3c2b7"
BLUE = "#2a78d6"          # categorical slot 1
AQUA = "#1baf7a"          # categorical slot 2
# ordinal ramp steps (250 -> 650) for the 5-rung metric ladder
LADDER = ["#86b6ef", "#5598e7", "#2a78d6", "#1c5cab", "#104281"]

mpl.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["Segoe UI", "DejaVu Sans", "Arial"],
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
        "text.color": INK,
        "axes.edgecolor": BASELINE,
        "axes.labelcolor": INK_2,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "axes.grid": True,
        "grid.color": GRID,
        "grid.linewidth": 0.8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "svg.fonttype": "none",  # keep text as text
    }
)


def style_ax(ax, xgrid: bool = True, ygrid: bool = False) -> None:
    ax.grid(axis="x" if xgrid else "y", visible=True)
    ax.grid(axis="y" if xgrid else "x", visible=ygrid)
    ax.set_axisbelow(True)


def load() -> pd.DataFrame:
    df = pd.read_csv(
        "data/orders.csv",
        parse_dates=[
            "order_date",
            "requested_delivery_date",
            "promised_delivery_date",
            "actual_delivery_date",
        ],
    )
    return df


def metric_ladder(df: pd.DataFrame) -> dict[str, float]:
    delivered = df[df.status == "delivered"].copy()
    n_all = len(df)
    n_del = len(delivered)

    late_vs_prom = (delivered.actual_delivery_date - delivered.promised_delivery_date).dt.days
    late_vs_req = (delivered.actual_delivery_date - delivered.requested_delivery_date).dt.days
    in_full = delivered.lines_delivered_complete == delivered.lines_total

    m1 = (late_vs_prom <= 3).mean()                        # tolerant: promised +3d
    m2 = (late_vs_prom <= 0).mean()                        # on-time vs promised
    m3 = (late_vs_req <= 0).mean()                         # on-time vs requested
    m4 = ((late_vs_req <= 0) & in_full).mean()             # OTIF (delivered base)
    m5 = ((late_vs_req <= 0) & in_full).sum() / n_all      # OTIF incl. cancellations

    return {
        "m1_tolerant_promised_3d": round(float(m1) * 100, 1),
        "m2_ontime_promised": round(float(m2) * 100, 1),
        "m3_ontime_requested": round(float(m3) * 100, 1),
        "m4_otif": round(float(m4) * 100, 1),
        "m5_otif_incl_cancelled": round(float(m5) * 100, 1),
        "n_orders": int(n_all),
        "n_delivered": int(n_del),
        "avg_padding_days": round(
            float((df.promised_delivery_date - df.requested_delivery_date).dt.days.mean()), 2
        ),
    }


def chart_ladder(metrics: dict[str, float]) -> None:
    labels = [
        "Promised date, +3 day tolerance",
        "Promised date, strict",
        "Requested date, strict",
        "OTIF  (requested + in-full)",
        "OTIF incl. cancellations",
    ]
    values = [
        metrics["m1_tolerant_promised_3d"],
        metrics["m2_ontime_promised"],
        metrics["m3_ontime_requested"],
        metrics["m4_otif"],
        metrics["m5_otif_incl_cancelled"],
    ]
    fig, ax = plt.subplots(figsize=(8.6, 4.4))
    y = np.arange(len(labels))[::-1]
    bars = ax.barh(y, values, height=0.58, color=LADDER, zorder=3)
    for yi, v in zip(y, values):
        ax.text(v + 1.2, yi, f"{v:.1f}%", va="center", ha="left", fontsize=11, color=INK)
    ax.set_yticks(y, labels, fontsize=10.5, color=INK_2)
    ax.set_xlim(0, 105)
    ax.set_xlabel("Share of orders (%)")
    style_ax(ax, xgrid=True)
    gap = values[0] - values[3]
    ax.set_title(
        "The same deliveries, five honest-to-strict definitions",
        fontsize=13, loc="left", color=INK, pad=28,
    )
    ax.text(
        0, 1.06,
        f"A {gap:.0f}-point gap separates the KPI on the slide from the one the customer feels",
        transform=ax.transAxes, fontsize=10.5, color=INK_2,
    )
    fig.tight_layout()
    fig.savefig("charts/metric_ladder.svg")
    plt.close(fig)


def chart_trend(df: pd.DataFrame) -> dict[str, float]:
    delivered = df[df.status == "delivered"].copy()
    delivered["month"] = delivered.promised_delivery_date.dt.to_period("M").dt.to_timestamp()
    late_vs_prom = (delivered.actual_delivery_date - delivered.promised_delivery_date).dt.days
    late_vs_req = (delivered.actual_delivery_date - delivered.requested_delivery_date).dt.days
    in_full = delivered.lines_delivered_complete == delivered.lines_total
    delivered["naive"] = (late_vs_prom <= 3).astype(float)
    delivered["otif"] = ((late_vs_req <= 0) & in_full).astype(float)

    g = delivered.groupby("month")[["naive", "otif"]].mean().mul(100)
    g = g.iloc[1:-1] if len(g) > 13 else g  # trim partial edge months

    fig, ax = plt.subplots(figsize=(8.6, 4.2))
    ax.plot(g.index, g.naive, color=BLUE, linewidth=2, zorder=3)
    ax.plot(g.index, g.otif, color=AQUA, linewidth=2, zorder=3)
    ax.text(g.index[-1], g.naive.iloc[-1] + 1.5, "Reported (tolerant)", color=BLUE, fontsize=10.5, ha="right")
    ax.text(g.index[-1], g.otif.iloc[-1] - 3.5, "OTIF (strict)", color="#0d7a55", fontsize=10.5, ha="right")
    ax.set_ylim(40, 100)
    ax.set_ylabel("Share of orders (%)")
    style_ax(ax, xgrid=False, ygrid=True)
    ax.set_title(
        "Twelve months, two stories: the reported KPI vs. OTIF",
        fontsize=13, loc="left", color=INK, pad=12,
    )
    fig.autofmt_xdate(rotation=0, ha="center")
    fig.tight_layout()
    fig.savefig("charts/monthly_trend.svg")
    plt.close(fig)
    return {"avg_gap_pts": round(float((g.naive - g.otif).mean()), 1)}


def chart_carriers(df: pd.DataFrame) -> dict[str, float]:
    delivered = df[df.status == "delivered"].copy()
    late_vs_req = (delivered.actual_delivery_date - delivered.requested_delivery_date).dt.days
    in_full = delivered.lines_delivered_complete == delivered.lines_total
    delivered["otif"] = ((late_vs_req <= 0) & in_full).astype(float)
    g = delivered.groupby("carrier")["otif"].mean().mul(100).sort_values()

    fig, ax = plt.subplots(figsize=(8.0, 3.4))
    y = np.arange(len(g))
    ax.barh(y, g.values, height=0.52, color=BLUE, zorder=3)
    for yi, v in zip(y, g.values):
        ax.text(v + 1.2, yi, f"{v:.1f}%", va="center", fontsize=11, color=INK)
    ax.set_yticks(y, g.index, fontsize=11, color=INK_2)
    ax.set_xlim(0, 100)
    ax.set_xlabel("OTIF (%)")
    style_ax(ax, xgrid=True)
    worst = g.index[0]
    spread = g.values[-1] - g.values[0]
    ax.set_title(
        f"Carrier choice moves OTIF by {spread:.0f} points",
        fontsize=13, loc="left", color=INK, pad=10,
    )
    fig.tight_layout()
    fig.savefig("charts/carrier_otif.svg")
    plt.close(fig)
    return {"worst_carrier": str(worst), "carrier_spread_pts": round(float(spread), 1)}


def chart_lateness(df: pd.DataFrame) -> dict[str, float]:
    delivered = df[df.status == "delivered"]
    late = (delivered.actual_delivery_date - delivered.requested_delivery_date).dt.days
    fig, ax = plt.subplots(figsize=(8.0, 3.8))
    bins = np.arange(-4, 16) - 0.5
    ax.hist(late, bins=bins, color=BLUE, zorder=3, rwidth=0.9)
    ax.axvline(0.5, color=INK_2, linewidth=1.2, linestyle="--")
    ax.text(0.8, ax.get_ylim()[1] * 0.92, "requested date", fontsize=10, color=INK_2)
    ax.set_xlabel("Days vs. requested delivery date (negative = early)")
    ax.set_ylabel("Orders")
    style_ax(ax, xgrid=False, ygrid=True)
    p_gt3 = float((late > 3).mean() * 100)
    ax.set_title(
        f"The average hides the tail: {p_gt3:.0f}% of orders run 4+ days late",
        fontsize=13, loc="left", color=INK, pad=10,
    )
    fig.tight_layout()
    fig.savefig("charts/lateness_distribution.svg")
    plt.close(fig)
    return {"avg_lateness_days": round(float(late.mean()), 2), "pct_4plus_days_late": round(p_gt3, 1)}


def chart_tolerance(df: pd.DataFrame) -> None:
    delivered = df[df.status == "delivered"]
    late_vs_prom = (delivered.actual_delivery_date - delivered.promised_delivery_date).dt.days
    tolerances = np.arange(0, 8)
    shares = [float((late_vs_prom <= t).mean() * 100) for t in tolerances]
    fig, ax = plt.subplots(figsize=(8.0, 3.8))
    ax.plot(tolerances, shares, color=BLUE, linewidth=2, marker="o", markersize=6, zorder=3)
    for t, s in zip(tolerances, shares):
        if t in (0, 3, 7):
            ax.annotate(f"{s:.1f}%", (t, s), textcoords="offset points", xytext=(0, 9),
                        ha="center", fontsize=10, color=INK)
    ax.set_xlabel("Tolerance window (days after promised date)")
    ax.set_ylabel('"On-time" (%)')
    ax.set_ylim(min(shares) - 5, 101)
    style_ax(ax, xgrid=False, ygrid=True)
    ax.set_title(
        "Every extra tolerance day buys free KPI points",
        fontsize=13, loc="left", color=INK, pad=10,
    )
    fig.tight_layout()
    fig.savefig("charts/tolerance_sensitivity.svg")
    plt.close(fig)


def main() -> None:
    df = load()
    results = metric_ladder(df)
    chart_ladder(results)
    results |= chart_trend(df)
    results |= chart_carriers(df)
    results |= chart_lateness(df)
    chart_tolerance(df)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
