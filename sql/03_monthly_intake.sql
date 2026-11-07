-- Group by CREATION month, not closure month. Zero months retained.
SELECT d.year_month,COUNT(f.request_number) AS requests,
       COALESCE(SUM(f.is_closed),0) AS eventually_closed_in_snapshot,
       COALESCE(SUM(f.is_open),0) AS still_open_in_snapshot
FROM (SELECT DISTINCT year_month,year FROM dim_date WHERE year=2025) d
LEFT JOIN (SELECT *,SUBSTR(created_local,1,7) AS created_month FROM fact_requests WHERE in_primary=1) f
ON f.created_month=d.year_month
GROUP BY d.year_month ORDER BY d.year_month;
