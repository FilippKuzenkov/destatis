-- Bronze layer: raw employment index in retail trade, all WZ08 codes, no filtering.
-- One series per sector-month (unlike retail_turnover's 6-way price/adjustment split) —
-- own table rather than the same long shape, since there's no equivalent
-- multi-method-revision reason to split index_value/yoy_change_pct into rows.

create table if not exists employment_index (
    wz08_code      text not null,
    description    text not null,
    period         date not null,                -- first day of the month, e.g. 2024-01-01
    index_value    numeric,                       -- 2021=100, null for the source's "-"
    yoy_change_pct numeric,                       -- change on previous year's period, null for "-"
    pulled_at      timestamptz not null default now(),
    primary key (wz08_code, period)
);

comment on table employment_index is
    'Destatis GENESIS-Online, table 45212-0002. Index of persons employed in retail trade, 2021=100. Bronze: raw, unfiltered, upserted on each pull.';
