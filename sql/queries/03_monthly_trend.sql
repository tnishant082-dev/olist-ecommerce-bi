select strftime(month, '%Y-%m') as month, orders, round(revenue, 2) as revenue, round(aov, 2) as aov,
       round(late_rate, 4) as late_rate, round(avg_review, 3) as avg_review
from mart_monthly where month between date '2017-01-01' and date '2018-08-01' order by 1;
