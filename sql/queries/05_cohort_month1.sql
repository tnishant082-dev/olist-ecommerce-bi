-- average share of a cohort that comes back in months 1, 3 and 6
select month_n, round(avg(retention), 4) as avg_retention, count(*) as cohorts
from mart_cohort_retention where month_n in (1, 3, 6) group by 1 order by 1;
