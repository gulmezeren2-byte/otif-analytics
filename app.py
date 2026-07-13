"""OTIF Analyzer - interactive delivery-performance explorer.

Run locally:
    pip install -r requirements.txt
    streamlit run app.py

Upload your own order file (see README for the expected columns) or explore
the bundled sample dataset.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="OTIF Analyzer", page_icon="📦", layout="wide")

REQUIRED_COLS = [
    "order_id",
    "requested_delivery_date",
    "promised_delivery_date",
    "actual_delivery_date",
    "lines_total",
    "lines_delivered_complete",
    "status",
]


@st.cache_data
def load_sample() -> pd.DataFrame:
    from pathlib import Path

    path = "data/orders.csv" if Path("data/orders.csv").exists() else "data/orders_sample.csv"
    return pd.read_csv(
        path,
        parse_dates=["requested_delivery_date", "promised_delivery_date", "actual_delivery_date"],
    )


def prepare(df: pd.DataFrame) -> pd.DataFrame:
    delivered = df[df.status == "delivered"].copy()
    delivered["late_vs_promised"] = (
        delivered.actual_delivery_date - delivered.promised_delivery_date
    ).dt.days
    delivered["late_vs_requested"] = (
        delivered.actual_delivery_date - delivered.requested_delivery_date
    ).dt.days
    delivered["in_full"] = delivered.lines_delivered_complete == delivered.lines_total
    return delivered


st.title("📦 OTIF Analyzer")
st.caption(
    "How honest is your on-time KPI? Compare tolerant definitions with strict "
    "OTIF (On-Time-In-Full) on your own order data."
)

uploaded = st.file_uploader("Upload orders CSV (or use the sample below)", type="csv")
if uploaded is not None:
    raw = pd.read_csv(
        uploaded,
        parse_dates=["requested_delivery_date", "promised_delivery_date", "actual_delivery_date"],
    )
    missing = [c for c in REQUIRED_COLS if c not in raw.columns]
    if missing:
        st.error(f"Missing required columns: {missing}")
        st.stop()
else:
    raw = load_sample()
    st.info("Using the bundled synthetic sample (4,000 orders). Upload a CSV to analyze your own data.")

df = prepare(raw)

tolerance = st.slider("Tolerance window for the 'reported' KPI (days after promised date)", 0, 7, 3)

naive = float((df.late_vs_promised <= tolerance).mean() * 100)
otif = float(((df.late_vs_requested <= 0) & df.in_full).mean() * 100)
gap = naive - otif
avg_late = float(df.late_vs_requested.mean())

c1, c2, c3, c4 = st.columns(4)
c1.metric("Reported on-time", f"{naive:.1f}%", help=f"vs promised date, +{tolerance}d tolerance")
c2.metric("OTIF (strict)", f"{otif:.1f}%", help="vs requested date, complete orders only")
c3.metric("Perception gap", f"{gap:.1f} pts")
c4.metric("Avg days vs request", f"{avg_late:+.1f}")

st.divider()

left, right = st.columns(2)

with left:
    st.subheader("The metric ladder")
    ladder = pd.DataFrame(
        {
            "Definition": [
                f"Promised +{tolerance}d",
                "Promised, strict",
                "Requested, strict",
                "OTIF",
            ],
            "Share %": [
                naive,
                float((df.late_vs_promised <= 0).mean() * 100),
                float((df.late_vs_requested <= 0).mean() * 100),
                otif,
            ],
        }
    ).set_index("Definition")
    st.bar_chart(ladder, horizontal=True)

with right:
    st.subheader("Monthly trend")
    tmp = df.copy()
    tmp["month"] = tmp.promised_delivery_date.dt.to_period("M").dt.to_timestamp()
    trend = tmp.groupby("month").apply(
        lambda g: pd.Series(
            {
                "Reported": (g.late_vs_promised <= tolerance).mean() * 100,
                "OTIF": ((g.late_vs_requested <= 0) & g.in_full).mean() * 100,
            }
        ),
        include_groups=False,
    )
    st.line_chart(trend)

if "carrier" in df.columns:
    st.subheader("OTIF by carrier")
    by_carrier = (
        df.assign(otif=((df.late_vs_requested <= 0) & df.in_full))
        .groupby("carrier")["otif"]
        .agg(otif_pct=lambda s: s.mean() * 100, orders="size")
        .sort_values("otif_pct")
    )
    st.dataframe(by_carrier.style.format({"otif_pct": "{:.1f}%"}), use_container_width=True)

st.caption(
    "Built by Eren Gülmez — part of an open industrial-engineering toolkit. "
    "github.com/gulmezeren2-byte"
)
