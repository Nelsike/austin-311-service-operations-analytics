SELECT source_status,source_is_open,source_is_closed,is_open,is_closed,
       COUNT(*) AS requests,SUM(status_flag_conflict) AS conflicting_flags
FROM fact_requests
GROUP BY source_status,source_is_open,source_is_closed,is_open,is_closed
ORDER BY source_status,source_is_open;
