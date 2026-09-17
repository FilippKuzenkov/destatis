"""Pull Destatis GENESIS-Online table 45212-0005 (retail turnover index) and
upsert into Supabase. Bronze layer: all WZ08 codes, unfiltered — filtering
happens downstream, in silver/gold.
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

TABLE_NAME = "45212-0005"
API_URL = "https://genesis.destatis.de/genesisWS/rest/2020/data/table"

MONTH_NUMBER = {
    "January": 1, "February": 2, "March": 3, "April": 4,
    "May": 5, "June": 6, "July": 7, "August": 8,
    "September": 9, "October": 10, "November": 11, "December": 12,
}

# Order matches the raw CSV's own embedded header — the JSON wrapper doesn't
# expose per-column semantics.
VALUE_COLUMNS = [
    ("constant", "unadjusted"),
    ("constant", "calendar_adjusted"),
    ("constant", "calendar_seasonal_adjusted"),
    ("current", "unadjusted"),
    ("current", "calendar_adjusted"),
    ("current", "calendar_seasonal_adjusted"),
]


def fetch_raw_csv() -> str:
    response = requests.post(
        API_URL,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "username": GENESIS_USERNAME,
            "password": GENESIS_PASSWORD,
        },
        data={
            # Minimal parameter set — omit optional fields entirely rather than
            # pass them blank. An explicitly empty startyear/endyear narrows the
            # result to the current year only; omitting them returns full history.
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
        # A missing Object means the request failed; Code alone isn't reliable
        # since the API also returns non-zero codes on benign auto-corrections.
        raise RuntimeError(f"GENESIS API error: {status['Content']}")
    if status["Code"] != 0:
        print(f"GENESIS API warning (request still succeeded): {status['Content']}")
    return content["Content"]


def parse_rows(raw_csv: str) -> list[dict]:
    # Only lines starting with "WZ08-" are data rows — header/footer length varies.
    rows = []
    for line in raw_csv.split("\n"):
        fields = line.split(";")
        if not fields[0].startswith("WZ08-"):
            continue
        wz08_code, description, year_str, month_name, *values = fields
        if len(values) != len(VALUE_COLUMNS):
            raise ValueError(f"Expected {len(VALUE_COLUMNS)} value columns, got {len(values)}: {line!r}")
        period = date(int(year_str), MONTH_NUMBER[month_name], 1)
        for (price_type, adjustment), raw_value in zip(VALUE_COLUMNS, values):
            rows.append({
                "wz08_code": wz08_code,
                "description": description,
                "period": period.isoformat(),
                "price_type": price_type,
                "adjustment": adjustment,
                "value": None if raw_value == "-" else float(raw_value),
            })
    return rows


def upsert(rows: list[dict]) -> None:
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    chunk_size = 1000
    for i in range(0, len(rows), chunk_size):
        chunk = rows[i:i + chunk_size]
        client.table("retail_turnover").upsert(
            chunk, on_conflict="wz08_code,period,price_type,adjustment"
        ).execute()


if __name__ == "__main__":
    raw = fetch_raw_csv()
    with open("debug_raw.txt", "w", encoding="utf-8") as f:
        f.write(raw)
    parsed = parse_rows(raw)
    print(f"Parsed {len(parsed)} rows from {TABLE_NAME}.")
    upsert(parsed)
    print(f"Upserted {len(parsed)} rows into retail_turnover.")
