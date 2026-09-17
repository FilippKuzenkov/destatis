"""Pull Destatis GENESIS-Online table 45212-0002 (employment index in retail
trade) and upsert into Supabase. Bronze layer: all WZ08 codes, unfiltered —
filtering happens downstream, in silver/gold. Same fetch logic and minimal
parameter set as pull_retail.py.
"""

import os
from datetime import date

import requests
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

GENESIS_USERNAME = os.environ["GENESIS_USERNAME"]
GENESIS_PASSWORD = os.environ["GENESIS_PASSWORD"]
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

TABLE_NAME = "45212-0002"
API_URL = "https://genesis.destatis.de/genesisWS/rest/2020/data/table"

MONTH_NUMBER = {
    "January": 1, "February": 2, "March": 3, "April": 4,
    "May": 5, "June": 6, "July": 7, "August": 8,
    "September": 9, "October": 10, "November": 11, "December": 12,
}

# Two missing-value placeholders: "-" (nothing to report) and "x" (not
# computable, e.g. no prior-year baseline for a YoY change).
MISSING_VALUES = {"-", "x"}


def parse_value(raw: str) -> float | None:
    return None if raw in MISSING_VALUES else float(raw)


def fetch_raw_csv() -> str:
    response = requests.post(
        API_URL,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "username": GENESIS_USERNAME,
            "password": GENESIS_PASSWORD,
        },
        data={
            "name": TABLE_NAME,
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


def parse_rows(raw_csv: str) -> list[dict]:
    # Fixed 6-field shape: code;description;year;month;index;yoy_change_pct.
    rows = []
    for line in raw_csv.split("\n"):
        fields = line.split(";")
        if not fields[0].startswith("WZ08-"):
            continue
        if len(fields) != 6:
            raise ValueError(f"Expected 6 fields, got {len(fields)}: {line!r}")
        wz08_code, description, year_str, month_name, index_str, change_str = fields
        period = date(int(year_str), MONTH_NUMBER[month_name], 1)
        rows.append({
            "wz08_code": wz08_code,
            "description": description,
            "period": period.isoformat(),
            "index_value": parse_value(index_str),
            "yoy_change_pct": parse_value(change_str),
        })
    return rows


def upsert(rows: list[dict]) -> None:
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    chunk_size = 1000
    for i in range(0, len(rows), chunk_size):
        chunk = rows[i:i + chunk_size]
        client.table("employment_index").upsert(
            chunk, on_conflict="wz08_code,period"
        ).execute()


if __name__ == "__main__":
    raw = fetch_raw_csv()
    parsed = parse_rows(raw)
    print(f"Parsed {len(parsed)} rows from {TABLE_NAME}.")
    upsert(parsed)
    print(f"Upserted {len(parsed)} rows into employment_index.")
