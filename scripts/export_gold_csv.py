"""Export gold_turnover_vs_employment to a flat CSV for the Excel workbook.

Filtered to the 5 sectors this project's write-up actually analyzed and
checked (README.md's Evidence section, insights_log.md) — not all 68 codes,
since the Excel Data tab should reflect exactly the data the findings were
drawn from, not an arbitrary larger slice.
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
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
