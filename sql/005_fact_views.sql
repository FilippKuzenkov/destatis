-- Silver layer: fact views over bronze, not materialized copies. Always
-- current after every future pull — no re-sync step to remember, unlike a
-- copied table would need. Description is dropped here on purpose: it's a
-- dimension attribute (lives in dim_sector), not a fact measure.

create or replace view fact_turnover as
select wz08_code, period, price_type, adjustment, value, pulled_at
from retail_turnover;

create or replace view fact_employment as
select wz08_code, period, index_value, yoy_change_pct, pulled_at
from employment_index;

comment on view fact_turnover is
    'Star schema fact: retail turnover, conformed to dim_sector/dim_date. Live view over retail_turnover bronze, not a copy.';
comment on view fact_employment is
    'Star schema fact: employment index, conformed to dim_sector/dim_date. Live view over employment_index bronze, not a copy.';
