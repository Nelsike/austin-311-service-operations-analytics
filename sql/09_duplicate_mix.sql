SELECT s.service_description,COUNT(*) AS total_intake,
 SUM(f.is_business_duplicate) AS duplicate_marked,
 1.0*SUM(f.is_business_duplicate)/COUNT(*) AS duplicate_marked_share
FROM fact_requests f JOIN dim_service s USING(service_key)
WHERE f.is_test=0 GROUP BY s.service_description
ORDER BY duplicate_marked DESC,s.service_description;
