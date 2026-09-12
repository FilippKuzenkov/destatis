"""Read-only SCAN pass (Columns & coverage, Aggregates & anomalies) over the
real bronze tables in Supabase. No writes, no local files — just prints.

Paginates explicitly rather than trusting a single select() — PostgREST/
Supabase caps unfiltered queries at 1000 rows by default, which silently
returns a partial (and misleadingly ordered) slice of any table over that
size, not an error.
"""

import os

from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

PAGE_SIZE = 1000


def fetch_all_values(client, table: str, column: str) -> list:
    values = []
    offset = 0
    while True:
        page = client.table(table).select(column).range(offset, offset + PAGE_SIZE - 1).execute()
        values.extend(row[column] for row in page.data)
        if len(page.data) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
    return values


def scan_table(client, table: str, code_col: str = "wz08_code") -> None:
    print(f"\n=== {table} ===")

    total = client.table(table).select("*", count="exact", head=True).execute()
    print(f"Row count: {total.count}")

    all_codes = fetch_all_values(client, table, code_col)
    print(f"Rows fetched for code scan: {len(all_codes)} (should match row count above)")
    distinct_codes = sorted(set(all_codes))
    print(f"Distinct {code_col}: {len(distinct_codes)}")

    standard = [c for c in distinct_codes if "-" not in c[len("WZ08-"):]]
    alternate = [c for c in distinct_codes if "-" in c[len("WZ08-"):]]
    print(f"  Standard hierarchy codes ({len(standard)}): {standard}")
    print(f"  Alternate '-01/-02' regrouping codes ({len(alternate)}): {alternate}")

    min_period = client.table(table).select("period").order("period").limit(1).execute()
    max_period = client.table(table).select("period").order("period", desc=True).limit(1).execute()
    print(f"Period range: {min_period.data[0]['period']} to {max_period.data[0]['period']}")


def main() -> None:
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    scan_table(client, "retail_turnover")
    scan_table(client, "employment_index")


if __name__ == "__main__":
    main()
