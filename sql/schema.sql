PRAGMA foreign_keys = ON;
CREATE TABLE dim_service(service_key INTEGER PRIMARY KEY, service_description TEXT NOT NULL UNIQUE);
CREATE TABLE dim_organization(organization_key INTEGER PRIMARY KEY, department TEXT NOT NULL, group_description TEXT NOT NULL, UNIQUE(department, group_description));
CREATE TABLE dim_channel(channel_key INTEGER PRIMARY KEY, method_received TEXT NOT NULL UNIQUE);
CREATE TABLE dim_date(date_key INTEGER PRIMARY KEY, date TEXT NOT NULL UNIQUE, year INTEGER NOT NULL, quarter INTEGER NOT NULL, month INTEGER NOT NULL, month_name TEXT NOT NULL, year_month TEXT NOT NULL, month_sort INTEGER NOT NULL, weekday TEXT NOT NULL);
CREATE TABLE snapshot(snapshot_date TEXT NOT NULL, age_cutoff_local TEXT NOT NULL, age_cutoff_utc TEXT NOT NULL, cohort_start TEXT NOT NULL, cohort_end_exclusive TEXT NOT NULL, source_file_sha256 TEXT NOT NULL);
CREATE TABLE fact_requests(
    request_number TEXT PRIMARY KEY,
    service_key INTEGER NOT NULL REFERENCES dim_service(service_key),
    organization_key INTEGER NOT NULL REFERENCES dim_organization(organization_key),
    channel_key INTEGER NOT NULL REFERENCES dim_channel(channel_key),
    created_date_key INTEGER NOT NULL REFERENCES dim_date(date_key),
    closed_date_key INTEGER REFERENCES dim_date(date_key),
    deadline_date_key INTEGER REFERENCES dim_date(date_key),
    created_local TEXT NOT NULL, created_utc TEXT,
    closed_local TEXT, closed_utc TEXT,
    deadline_local TEXT, deadline_utc TEXT,
    last_updated_local TEXT,
    source_status TEXT NOT NULL,
    status_class TEXT NOT NULL CHECK(status_class IN ('Closed','Open','Excluded','Unknown')),
    is_business_duplicate INTEGER NOT NULL CHECK(is_business_duplicate IN (0,1)),
    is_test INTEGER NOT NULL CHECK(is_test IN (0,1)),
    in_primary INTEGER NOT NULL CHECK(in_primary IN (0,1)),
    is_closed INTEGER NOT NULL CHECK(is_closed IN (0,1)),
    is_open INTEGER NOT NULL CHECK(is_open IN (0,1)),
    valid_closure INTEGER NOT NULL CHECK(valid_closure IN (0,1)),
    closure_days REAL CHECK(closure_days>=0),
    valid_deadline_closure INTEGER NOT NULL CHECK(valid_deadline_closure IN (0,1)),
    closed_by_deadline INTEGER CHECK(closed_by_deadline IN (0,1)),
    open_age_days REAL CHECK(open_age_days>=0),
    open_past_deadline INTEGER CHECK(open_past_deadline IN (0,1)),
    source_is_open INTEGER, source_is_closed INTEGER,
    source_response_days REAL, source_age_days REAL, source_fiscal_year INTEGER,
    source_is_overdue INTEGER, source_closed_on_time INTEGER,
    status_flag_conflict INTEGER NOT NULL,
    deadline_flag_conflict INTEGER NOT NULL,
    timestamp_ambiguity INTEGER NOT NULL,
    longitude REAL, latitude REAL,
    CHECK(valid_closure=0 OR (is_closed=1 AND closure_days IS NOT NULL)),
    CHECK(is_open+is_closed<=1)
);
CREATE INDEX idx_fact_service ON fact_requests(service_key);
CREATE INDEX idx_fact_created ON fact_requests(created_date_key);
CREATE INDEX idx_fact_closed ON fact_requests(closed_date_key);
CREATE INDEX idx_fact_primary ON fact_requests(in_primary,status_class);
CREATE VIEW v_primary_requests AS
SELECT f.*,s.service_description,o.department,o.group_description,c.method_received
FROM fact_requests f JOIN dim_service s USING(service_key)
JOIN dim_organization o USING(organization_key) JOIN dim_channel c USING(channel_key)
WHERE in_primary=1;
