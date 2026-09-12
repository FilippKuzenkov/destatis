-- Bronze layer: raw retail turnover index, all WZ08 codes, no filtering.
-- Filtering/category selection happens in silver/gold, not here.

create table if not exists retail_turnover (
    wz08_code   text not null,
    description text not null,
    period      date not null,                -- first day of the month, e.g. 2024-01-01
    price_type  text not null check (price_type in ('constant', 'current')),
    adjustment  text not null check (adjustment in ('unadjusted', 'calendar_adjusted', 'calendar_seasonal_adjusted')),
    value       numeric,                       -- null for the source's "-" (not applicable / suppressed)
    pulled_at   timestamptz not null default now(),
    primary key (wz08_code, period, price_type, adjustment)
);

comment on table retail_turnover is
    'Destatis GENESIS-Online, table 45212-0005. Turnover index in retail trade, 2021=100. Bronze: raw, unfiltered, upserted on each pull.';
