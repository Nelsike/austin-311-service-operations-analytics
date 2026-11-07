-- Zero elapsed closure time can reflect administrative workflow.
-- It is not evidence that field work completed instantly.
SELECT service_description,COUNT(*) AS requests,SUM(valid_closure) AS duration_n,
 SUM(CASE WHEN valid_closure=1 AND closure_days=0 THEN 1 ELSE 0 END) AS zero_elapsed_closures,
 SUM(CASE WHEN is_closed=1 AND closed_date_key>=20260101 THEN 1 ELSE 0 END) AS closures_in_2026,
 MIN(julianday(deadline_local)-julianday(created_local)) AS min_recorded_deadline_calendar_days,
 MAX(julianday(deadline_local)-julianday(created_local)) AS max_recorded_deadline_calendar_days
FROM v_primary_requests GROUP BY service_description ORDER BY zero_elapsed_closures DESC,service_description;
