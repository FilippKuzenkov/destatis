"""Populate dim_sector and dim_date (silver layer) from the verified real
code list and period range already confirmed in bronze (scan_bronze.py,
2026-09-12). Reads from and writes to Supabase only — no local files.
"""

import os
from datetime import date

from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

PAGE_SIZE = 1000

MONTH_NAME = {
    1: "January", 2: "February", 3: "March", 4: "April",
    5: "May", 6: "June", 7: "July", 8: "August",
    9: "September", 10: "October", 11: "November", 12: "December",
}


def fetch_all_rows(client, table: str, columns: str) -> list[dict]:
    rows = []
    offset = 0
    while True:
        page = client.table(table).select(columns).range(offset, offset + PAGE_SIZE - 1).execute()
        rows.extend(page.data)
        if len(page.data) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
    return rows


def classify_sector(code: str) -> dict:
    # code looks like "WZ08-47", "WZ08-4711", "WZ08-G", "WZ08-47-02", "WZ08-G-05".
    # Verified against the real 68-code list (scan_bronze.py, 2026-09-12) —
    # every standard code fits length-based level 1-4, no exceptions found.
    suffix = code[len("WZ08-"):]
    if "-" in suffix:
        base, _, _ = suffix.partition("-")
        return {"code_family": "alternate", "level": None, "parent_code": None, "related_base_code": base}
    if suffix == "G":
        return {"code_family": "standard", "level": 1, "parent_code": None, "related_base_code": None}
    if len(suffix) == 2:
        return {"code_family": "standard", "level": 2, "parent_code": "WZ08-G", "related_base_code": None}
    if len(suffix) == 3:
        return {"code_family": "standard", "level": 3, "parent_code": f"WZ08-{suffix[:2]}", "related_base_code": None}
    if len(suffix) == 4:
        return {"code_family": "standard", "level": 4, "parent_code": f"WZ08-{suffix[:3]}", "related_base_code": None}
    raise ValueError(f"Unrecognized WZ08 code shape: {code!r}")


def build_dim_sector(client) -> None:
    rows = fetch_all_rows(client, "retail_turnover", "wz08_code,description")
    by_code = {row["wz08_code"]: row["description"] for row in rows}

    dim_rows = []
    for code, description in by_code.items():
        dim_rows.append({"wz08_code": code, "description": description, **classify_sector(code)})

    # Parents before children — not strictly required (Postgres checks a
    # self-referencing FK at end-of-statement for a bulk upsert, not per row),
    # but keeps the batch readable and is a cheap safety net regardless.
    dim_rows.sort(key=lambda r: (r["level"] is None, r["level"] or 0))

    client.table("dim_sector").upsert(dim_rows).execute()
    print(f"Upserted {len(dim_rows)} rows into dim_sector.")


def build_dim_date(client) -> None:
    turnover_periods = {row["period"] for row in fetch_all_rows(client, "retail_turnover", "period")}
    employment_periods = {row["period"] for row in fetch_all_rows(client, "employment_index", "period")}
    all_periods = sorted(turnover_periods | employment_periods)

    dim_rows = []
    for period_str in all_periods:
        d = date.fromisoformat(period_str)
        dim_rows.append({
            "period": period_str,
            "year": d.year,
            "month": d.month,
            "month_name": MONTH_NAME[d.month],
            "quarter": (d.month - 1) // 3 + 1,
        })

    client.table("dim_date").upsert(dim_rows).execute()
    print(f"Upserted {len(dim_rows)} rows into dim_date.")


if __name__ == "__main__":
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    build_dim_sector(client)
    build_dim_date(client)
