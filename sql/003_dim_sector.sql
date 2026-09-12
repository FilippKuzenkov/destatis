-- Silver layer: sector dimension, conformed across fact_turnover and fact_employment.
-- Two real classification schemes coexist in the source (see DATA_SOURCES.md) —
-- code_family keeps them distinct rather than forcing one hierarchy onto both.
-- parent_code/level are only meaningful for code_family = 'standard'; the
-- alternate scheme's true grouping logic isn't documented by Destatis (e.g.
-- WZ08-45-01's base '45' isn't even a standard code in this data), so it's
-- kept flat — related_base_code is informational only, not a real FK.

create table if not exists dim_sector (
    wz08_code         text primary key,
    description       text not null,
    code_family       text not null check (code_family in ('standard', 'alternate')),
    level             int,                          -- 1=section, 2=division, 3=group, 4=class; null for alternate
    parent_code       text references dim_sector(wz08_code),
    related_base_code text                          -- e.g. '45' for WZ08-45-01; informational only, no FK
);

comment on table dim_sector is
    'Star schema dimension: WZ08 sector, conformed across fact_turnover and fact_employment.';
