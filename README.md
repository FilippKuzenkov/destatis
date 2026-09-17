# Destatis retail turnover

A comparison of online vs. physical retail performance in Germany, built on official government statistics (Destatis GENESIS-Online).

**What it answers:** whether online retail's turnover growth is outpacing physical retail, whether that growth survives seasonal adjustment, and whether it decouples from employment — framed as a real decision a retail merchandising/expansion-planning lead would act on. Full write-up, findings, and charts: [`ANALYSIS.md`](ANALYSIS.md).

## Data

Two tables from Destatis's GENESIS-Online API, both monthly, by WZ2008 retail sector:

- **Retail turnover index** (45212-0005) — raw and seasonally/calendar-adjusted, at constant and current prices.
- **Employment index** (45212-0002) — same sector breakdown.

Full acquisition steps, API auth, response format, and data-structure caveats: [`DATA_SOURCES.md`](DATA_SOURCES.md).

## Architecture

- **Bronze** — raw pulls, long-format, upserted into Supabase/Postgres (`scripts/pull_retail.py`, `scripts/pull_employment.py`).
- **Silver** — a star schema (`dim_sector`, `dim_date`, `fact_turnover`, `fact_employment`) built to let the two facts share filters on sector and period (`scripts/build_dimensions.py`, `sql/`).
- **Gold** — a view computing turnover YoY%, employment YoY%, and the gap between them per sector-month (`sql/006_gold_turnover_vs_employment.sql`).
- **Dashboard** — a Power BI report (two pages: overview KPIs/trend, category comparison) built directly against the star schema, plus an Excel workbook (`excel/`) as a second-tool cut of the gold data.
- **Automated refresh** — an n8n workflow re-runs both pulls monthly, timed to Destatis's own publication schedule. Detail in `DATA_SOURCES.md`.

## Repo layout

```
scripts/     ingestion, dimension-building, CSV export
sql/         star-schema and gold-view definitions
excel/       pivot workbook + exported CSV
charts/      Power BI page exports
n8n/         the monthly-refresh workflow's Code node scripts + a canvas screenshot
```

## Reproducing this

1. Get Destatis API access and pull both tables — see `DATA_SOURCES.md`.
2. Run `scripts/build_dimensions.py` to build the star schema's dimension tables, then apply `sql/` to create the fact views and gold view.
3. Connect Power BI (or any BI tool) to the star schema directly, or use `scripts/export_gold_csv.py` for a flat CSV cut.

## Tool stack

Python (ingestion) · Supabase/Postgres (star schema) · Power BI (dashboard) · Excel (pivot workbook) · n8n (scheduled refresh).
