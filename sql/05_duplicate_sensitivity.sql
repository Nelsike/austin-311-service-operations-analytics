SELECT CASE WHEN is_business_duplicate=1 THEN 'Duplicate-marked' ELSE 'Nonduplicate' END AS intake_class,
 COUNT(*) AS requests,SUM(is_closed) AS closed,SUM(is_open) AS open_backlog,
 SUM(valid_closure) AS duration_n,AVG(closure_days) AS mean_closure_days
FROM fact_requests WHERE is_test=0
GROUP BY is_business_duplicate ORDER BY is_business_duplicate;
