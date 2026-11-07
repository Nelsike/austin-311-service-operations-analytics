// Create each query below separately, with the shown name.

// dim_service
let Source=LoadCsv("dim_service") in
Table.TransformColumnTypes(Source,{{"service_key",Int64.Type},{"service_description",type text}})

// dim_organization
let Source=LoadCsv("dim_organization") in
Table.TransformColumnTypes(Source,{{"organization_key",Int64.Type},{"department",type text},{"group_description",type text}})

// dim_channel
let Source=LoadCsv("dim_channel") in
Table.TransformColumnTypes(Source,{{"channel_key",Int64.Type},{"method_received",type text}})

// dim_date
let Source=LoadCsv("dim_date") in
Table.TransformColumnTypes(Source,{{"date_key",Int64.Type},{"date",type date},{"year",Int64.Type},
    {"quarter",Int64.Type},{"month",Int64.Type},{"month_name",type text},{"year_month",type text},
    {"month_sort",Int64.Type},{"weekday",type text}},"en-US")

// snapshot (disconnected; there is exactly one row)
let Source=LoadCsv("snapshot") in
Table.TransformColumnTypes(Source,{{"snapshot_date",type date},{"age_cutoff_local",type text},
    {"age_cutoff_utc",type text},{"cohort_start",type date},{"cohort_end_exclusive",type date},
    {"source_file_sha256",type text}},"en-US")
