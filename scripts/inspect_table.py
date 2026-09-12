"""Read-only procurement check for a GENESIS-Online table before any schema
or Supabase work. Pulls the table, dumps the raw CSV for inspection, and
prints structure stats. Never writes to Supabase.

Usage: python scripts/inspect_table.py 45212-0014
"""

import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()

GENESIS_USERNAME = os.environ["GENESIS_USERNAME"]
GENESIS_PASSWORD = os.environ["GENESIS_PASSWORD"]
API_URL = "https://genesis.destatis.de/genesisWS/rest/2020/data/table"


def fetch_raw_csv(table_name: str) -> str:
    response = requests.post(
        API_URL,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "username": GENESIS_USERNAME,
            "password": GENESIS_PASSWORD,
        },
        data={
            "name": table_name,
            "area": "all",
            "compress": "true",
            "timeslices": "3",
            "language": "en",
        },
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    status = payload["Status"]
    content = payload.get("Object")
    if content is None:
        raise RuntimeError(f"GENESIS API error: {status['Content']}")
    if status["Code"] != 0:
        print(f"GENESIS API warning (request still succeeded): {status['Content']}")
    return content["Content"]


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python scripts/inspect_table.py <table-name>")
        sys.exit(1)
    table_name = sys.argv[1]

    raw = fetch_raw_csv(table_name)

    debug_path = f"debug_{table_name}.txt"
    with open(debug_path, "w", encoding="utf-8") as f:
        f.write(raw)
    print(f"Raw response saved to {debug_path} (gitignored, inspection only).\n")

    data_lines = [line for line in raw.split("\n") if line.split(";")[0].startswith("WZ08-")]
    codes = {}
    years = set()
    value_col_counts = set()
    for line in data_lines:
        fields = line.split(";")
        code, description, year_str, month_name, *values = fields
        codes.setdefault(code, description)
        years.add(int(year_str))
        value_col_counts.add(len(values))

    print(f"Table: {table_name}")
    print(f"Data lines: {len(data_lines)}")
    print(f"Distinct WZ08 codes: {len(codes)}")
    print(f"Value columns per line (should be one consistent number): {sorted(value_col_counts)}")
    print(f"Year range: {min(years)}-{max(years)}" if years else "No years found")
    print(f"Projected long-format row count (data_lines x value_columns): "
          f"{len(data_lines) * (list(value_col_counts)[0] if len(value_col_counts) == 1 else '?')}")
    print("\nFirst 5 WZ08 codes found:")
    for code, desc in list(codes.items())[:5]:
        print(f"  {code}: {desc}")


if __name__ == "__main__":
    main()
