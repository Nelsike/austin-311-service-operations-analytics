-- Window-based continuous percentiles; portable to SQLite without extensions.
-- rank positions are 1 + (N-1)*p, with linear interpolation (NumPy/PBI INC).
WITH ranked AS (
  SELECT service_key,closure_days,
    ROW_NUMBER() OVER(PARTITION BY service_key ORDER BY closure_days,request_number) AS rn,
    COUNT(*) OVER(PARTITION BY service_key) AS n
  FROM v_primary_requests WHERE valid_closure=1
), positions AS (
  SELECT *,1+(n-1)*0.5 AS med_pos,1+(n-1)*0.9 AS p90_pos FROM ranked
), percentiles AS (
  SELECT service_key,
    MAX(CASE WHEN rn=CAST(med_pos AS INTEGER) THEN closure_days END) AS med_lo,
    MAX(CASE WHEN rn=CAST(med_pos AS INTEGER)+(med_pos>CAST(med_pos AS INTEGER)) THEN closure_days END) AS med_hi,
    MAX(med_pos-CAST(med_pos AS INTEGER)) AS med_weight,
    MAX(CASE WHEN rn=CAST(p90_pos AS INTEGER) THEN closure_days END) AS p90_lo,
    MAX(CASE WHEN rn=CAST(p90_pos AS INTEGER)+(p90_pos>CAST(p90_pos AS INTEGER)) THEN closure_days END) AS p90_hi,
    MAX(p90_pos-CAST(p90_pos AS INTEGER)) AS p90_weight
  FROM positions GROUP BY service_key
), totals AS (
  SELECT service_key,service_description,COUNT(*) AS requests,SUM(is_closed) AS closed,
    SUM(is_open) AS open_backlog,SUM(valid_closure) AS duration_n,
    SUM(valid_deadline_closure) AS deadline_n,SUM(closed_by_deadline) AS closed_by_deadline,
    SUM(open_past_deadline) AS open_past_deadline
  FROM v_primary_requests GROUP BY service_key,service_description
)
SELECT t.*,med_lo+(med_hi-med_lo)*med_weight AS median_closure_days,
  p90_lo+(p90_hi-p90_lo)*p90_weight AS p90_closure_days,
  1.0*closed_by_deadline/NULLIF(deadline_n,0) AS closed_by_recorded_deadline_share
FROM totals t LEFT JOIN percentiles p USING(service_key)
ORDER BY requests DESC,service_key;
