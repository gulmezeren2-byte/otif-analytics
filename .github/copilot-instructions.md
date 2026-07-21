# Copilot instructions — otif-analytics

Python study + Streamlit explorer arguing that a reported 98% "on-time" delivery KPI is really ~59% OTIF, shown via a five-rung "metric ladder"; the metric definitions and business interpretation are the product, the code is the vehicle.

## Build, test, lint

Flat repo with no package structure — run every script from the repo root, since all paths are relative (`data/orders.csv`, `charts/`). Python 3.10+.

```bash
pip install -r requirements.txt   # pandas>=2.2, numpy>=1.26, matplotlib>=3.8, streamlit>=1.49
python generate_data.py           # writes data/orders.csv (4000 orders, gitignored) + data/orders_sample.csv (300 rows, committed)
python analysis.py                # reads data/orders.csv -> 5 SVGs in charts/ + headline metrics as JSON on stdout
streamlit run app.py              # interactive explorer: uploads a CSV, else falls back to the sample
```

No test suite, linter, formatter, or CI workflow exists — do not reference or invent them.

## Architecture

Three independent scripts sharing `data/orders.csv`:
- `generate_data.py` — seeded synthetic generator (`np.random.default_rng(42)`, `N_ORDERS=4000`) injecting the failure patterns the study relies on: sales padding, one weak "Carrier B", month-end congestion, partial shipments in "Endustriyel Ekipman", ~3% cancellations.
- `analysis.py` — computes the 5-rung ladder (`metric_ladder`) and renders publication SVGs (`chart_*` helpers, shared palette + `mpl.rcParams`).
- `app.py` — Streamlit app; recomputes reported-vs-OTIF live from a tolerance slider and enforces `REQUIRED_COLS` on uploads.

Ordering gotcha: `analysis.py` reads only `data/orders.csv` (gitignored), so `generate_data.py` must run first; `app.py` alone falls back to committed `data/orders_sample.csv`.

## Conventions

- OTIF is defined identically in `analysis.py` and `app.py`: `(actual − requested).days <= 0` AND `lines_delivered_complete == lines_total`. Keep both in sync.
- README headline numbers (98.0/78.0/64.3/59.1/57.4) are tied to seed 42 — changing the generator invalidates them; regenerate and update both READMEs.
- Docs are bilingual: `README.md` and `README.tr.md` must be edited together.
- Every module starts with `from __future__ import annotations`, uses builtin-generic type hints, and follows the functions + `main()` + `if __name__ == "__main__"` pattern.
- Charts are always `.svg` saved into `charts/` with `svg.fonttype="none"` (text stays selectable); reuse the module-level palette constants and `style_ax()`.
- Data keeps Turkish domain values ASCII-only (`Ic Anadolu`, `Yapi Malzemeleri`); `carrier` is optional but enables the carrier breakdown.
