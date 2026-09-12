-- Gold layer: the actual North Star comparison, not just a bigger aggregate.
-- Turnover uses constant prices + calendar-seasonal-adjustment: comparing a
-- real/inflation-stripped quantity against employment (a headcount, not a
-- monetary figure) is the defensible like-for-like pairing — current prices
-- would conflate "more people working" with "prices went up."
--
-- Not filtered to code_family = 'standard' — each row is its own sector's
-- trend, so the alternate-scheme double-counting risk (documented on
-- dim_sector) only applies if this view is later SUMMED across sectors.
-- Filter on dim_sector.code_family = 'standard' at that point, not here.

create or replace view gold_turnover_vs_employment as
with turnover_yoy as (
    select
        wz08_code,
        period,
        value,
        lag(value, 12) over (partition by wz08_code order by period) as value_prior_year
    from fact_turnover
    where price_type = 'constant' and adjustment = 'calendar_seasonal_adjusted'
),
turnover_growth as (
    select
        wz08_code,
        period,
        round((value - value_prior_year) / nullif(value_prior_year, 0) * 100, 1) as turnover_yoy_pct
    from turnover_yoy
    where value_prior_year is not null
)
select
    t.wz08_code,
    s.description,
    s.code_family,
    t.period,
    t.turnover_yoy_pct,
    e.yoy_change_pct as employment_yoy_pct,
    t.turnover_yoy_pct - e.yoy_change_pct as growth_gap_pct
from turnover_growth t
join dim_sector s on s.wz08_code = t.wz08_code
left join fact_employment e on e.wz08_code = t.wz08_code and e.period = t.period
order by t.wz08_code, t.period;

comment on view gold_turnover_vs_employment is
    'Gold: turnover YoY% (constant prices, calendar-seasonal-adjusted) vs. employment YoY%, per sector-month. growth_gap_pct > 0 means turnover outpacing employment.';
