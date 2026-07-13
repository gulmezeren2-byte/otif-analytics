"""Synthetic order/delivery dataset generator for OTIF analytics.

Generates a realistic one-year order book for a mid-size distributor:
- Sales teams pad promised dates vs. what the customer requested
- One carrier underperforms systematically
- Month-end dispatch congestion adds delays
- One product category suffers partial (incomplete) deliveries

Seeded for reproducibility. Output: data/orders.csv
"""

from __future__ import annotations

import numpy as np
import pandas as pd

RNG = np.random.default_rng(42)
N_ORDERS = 4000

CARRIERS = np.array(["Carrier A", "Carrier B", "Carrier C"])
CARRIER_P = np.array([0.45, 0.30, 0.25])

REGIONS = np.array(["Marmara", "Ege", "Ic Anadolu", "Karadeniz", "Export-EU"])
REGION_P = np.array([0.38, 0.22, 0.18, 0.10, 0.12])

CATEGORIES = np.array(
    ["Yapi Malzemeleri", "Endustriyel Ekipman", "Elektrik", "Hirdavat", "Kimyasal"]
)
CATEGORY_P = np.array([0.30, 0.20, 0.20, 0.18, 0.12])


def main() -> None:
    start = np.datetime64("2025-07-01")
    order_offsets = RNG.integers(0, 365, N_ORDERS)
    order_dates = start + order_offsets.astype("timedelta64[D]")

    carrier = RNG.choice(CARRIERS, N_ORDERS, p=CARRIER_P)
    region = RNG.choice(REGIONS, N_ORDERS, p=REGION_P)
    category = RNG.choice(CATEGORIES, N_ORDERS, p=CATEGORY_P)

    # Customer asks for delivery in 3-14 days
    requested_lead = RNG.integers(3, 15, N_ORDERS)
    requested_date = order_dates + requested_lead.astype("timedelta64[D]")

    # Sales padding: 45% of promises add 1-2 days on top of the request
    pad = np.where(
        RNG.random(N_ORDERS) < 0.45, RNG.integers(1, 3, N_ORDERS), 0
    )
    promised_date = requested_date + pad.astype("timedelta64[D]")

    # --- Delay vs. the PROMISED date -------------------------------------
    # Base: most orders arrive a bit early or on the day
    delay = RNG.normal(loc=-1.2, scale=1.4, size=N_ORDERS)

    # Carrier effect: Carrier B is systematically late
    hizli = carrier == "Carrier B"
    delay = delay + np.where(
        hizli & (RNG.random(N_ORDERS) < 0.35), RNG.uniform(1.0, 4.0, N_ORDERS), 0.0
    )

    # Month-end congestion: promises falling on day >= 24 slip more often
    promised_day = pd.DatetimeIndex(promised_date).day.to_numpy()
    month_end = promised_day >= 24
    delay = delay + np.where(
        month_end & (RNG.random(N_ORDERS) < 0.25), RNG.uniform(1.0, 3.0, N_ORDERS), 0.0
    )

    # Export orders: customs variance
    export = region == "Export-EU"
    delay = delay + np.where(
        export & (RNG.random(N_ORDERS) < 0.25), RNG.uniform(1.0, 5.0, N_ORDERS), 0.0
    )

    delay_days = np.clip(np.round(delay), -3, 20).astype(int)
    actual_date = promised_date + delay_days.astype("timedelta64[D]")

    # --- Completeness (in-full) ------------------------------------------
    lines_total = RNG.integers(1, 9, N_ORDERS)
    # Endustriyel Ekipman suffers partial shipments; everyone has a small base rate
    partial_p = np.where(category == "Endustriyel Ekipman", 0.16, 0.05)
    is_partial = RNG.random(N_ORDERS) < partial_p
    lines_missing = np.where(
        is_partial, np.maximum(1, (lines_total * RNG.uniform(0.1, 0.5, N_ORDERS)).astype(int)), 0
    )
    lines_complete = lines_total - lines_missing

    # --- Cancellations -----------------------------------------------------
    cancelled = RNG.random(N_ORDERS) < 0.03

    df = pd.DataFrame(
        {
            "order_id": [f"SO-{100000 + i}" for i in range(N_ORDERS)],
            "order_date": order_dates,
            "requested_delivery_date": requested_date,
            "promised_delivery_date": promised_date,
            "actual_delivery_date": actual_date,
            "carrier": carrier,
            "region": region,
            "product_category": category,
            "lines_total": lines_total,
            "lines_delivered_complete": np.where(cancelled, 0, lines_complete),
            "status": np.where(cancelled, "cancelled", "delivered"),
        }
    )
    df.loc[cancelled, "actual_delivery_date"] = pd.NaT

    df.to_csv("data/orders.csv", index=False)
    df.head(300).to_csv("data/orders_sample.csv", index=False)
    print(f"Wrote data/orders.csv with {len(df)} orders (+ 300-row sample)")
    print(df["status"].value_counts().to_dict())


if __name__ == "__main__":
    main()
