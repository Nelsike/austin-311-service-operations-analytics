-- Closure events for the 2025-created cohort, including closures in 2026.
-- This is not ALL work closed by TPW in a calendar month.
SELECT SUBSTR(closed_local,1,7) AS closure_month,COUNT(*) AS cohort_closures
FROM v_primary_requests WHERE is_closed=1 AND closed_local IS NOT NULL
GROUP BY closure_month ORDER BY closure_month;
