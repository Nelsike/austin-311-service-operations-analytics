-- Snapshot backlog ONLY for requests created in 2025.
-- Not the department's all-years backlog; no status history is available.
SELECT request_number,service_description,source_status,created_local,deadline_local,
       open_age_days,open_past_deadline,status_flag_conflict,last_updated_local
FROM v_primary_requests WHERE is_open=1
ORDER BY open_age_days DESC,request_number;
