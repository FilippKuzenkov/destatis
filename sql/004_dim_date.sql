-- Silver layer: calendar-month dimension, conformed across fact_turnover and
-- fact_employment. Populated from the real periods present in bronze, not a
-- generated range — see scripts/build_dimensions.py.

create table if not exists dim_date (
    period      date primary key,   -- first of month
    year        int not null,
    month       int not null,
    month_name  text not null,
    quarter     int not null
);

comment on table dim_date is
    'Star schema dimension: calendar month, conformed across fact_turnover and fact_employment.';
