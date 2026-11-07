// Create a blank query named fact_requests. Requires the LoadCsv function and pProjectFolder.
let
    Source = LoadCsv("fact_requests"),
    WholeNumberColumns = {"service_key","organization_key","channel_key","created_date_key","closed_date_key",
        "deadline_date_key","is_business_duplicate","is_test","in_primary","is_closed","is_open","valid_closure",
        "valid_deadline_closure","closed_by_deadline","open_past_deadline","source_is_open","source_is_closed",
        "source_fiscal_year","source_is_overdue","source_closed_on_time","status_flag_conflict",
        "deadline_flag_conflict","timestamp_ambiguity"},
    DecimalColumns = {"closure_days","open_age_days","source_response_days","source_age_days","longitude","latitude"},
    LocalDateTimeColumns = {"created_local","closed_local","deadline_local","last_updated_local"},
    Types = List.Transform(WholeNumberColumns, each {_, Int64.Type}) &
        List.Transform(DecimalColumns, each {_, type number}) &
        List.Transform(LocalDateTimeColumns, each {_, type datetime}) &
        {{"request_number",type text},{"source_status",type text},{"status_class",type text},
         {"created_utc",type text},{"closed_utc",type text},{"deadline_utc",type text}},
    Typed = Table.TransformColumnTypes(Source, Types, "en-US")
in
    Typed
