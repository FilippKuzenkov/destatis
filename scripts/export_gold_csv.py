"""Export gold_turnover_vs_employment to a flat CSV for the Excel workbook.

Filtered to the 5 sectors analyzed in README.md/insights_log.md, not all 68
codes — the Data tab should reflect exactly what the findings were drawn from.

Semicolon-delimited, comma-decimal on the numeric columns — matches Destatis's
own CSV convention and what German-locale Excel parses correctly on import.
"""

import csv
import os

from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

PAGE_SIZE = 1000

ANALYZED_CODES = ["WZ08-4791", "WZ08-472", "WZ08-47", "WZ08-4799", "WZ08-4741"]

COLUMNS = [
    "wz08_code",
    "description",
    "period",
    "turnover_yoy_pct",
    "employment_yoy_pct",
    "growth_gap_pct",
]

NUMERIC_COLUMNS = {"turnover_yoy_pct", "employment_yoy_pct", "growth_gap_pct"}


def fetch_all_rows(client) -> list[dict]:
    rows = []
    offset = 0
    while True:
        page = (
            client.table("gold_turnover_vs_employment")
            .select(",".join(COLUMNS))
            .in_("wz08_code", ANALYZED_CODES)
            .order("wz08_code")
            .order("period")
            .range(offset, offset + PAGE_SIZE - 1)
            .execute()
        )
        rows.extend(page.data)
        if len(page.data) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
    return rows


def main() -> None:
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    rows = fetch_all_rows(client)
    print(f"Fetched {len(rows)} rows across {len(ANALYZED_CODES)} sectors.")

    os.makedirs("excel", exist_ok=True)
    out_path = "excel/gold_turnover_vs_employment.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, delimiter=";")
        writer.writeheader()
        for row in rows:
            for col in NUMERIC_COLUMNS:
                if row[col] is not None:
                    row[col] = str(row[col]).replace(".", ",")
            writer.writerow(row)

    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
