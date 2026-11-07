# Source fields and how they are used

The actual official definitions, API field names and Socrata types are preserved in `data/raw/city_metadata.json`, fetched from [the City metadata endpoint](https://data.austintexas.gov/api/views/38mr-dwji.json). This table explains their analytical use in plain language. `docs/source_fields.csv` provides a machine-readable mapping back to the publisher's schema.

| Export column | API name | Meaning and analytical use |
| --- | --- | --- |
| Service Request Number | service_request_sr_number | Request identifier; preserve as text and require a unique, nonblank value |
| Department | department | Published assigned department; source dataset is already limited to Transportation/Public Works |
| Group Description | group_description | Published assigned group; preserve label variants without an unverified crosswalk |
| Service Request Description | sr_description | Request type/category; trim surrounding whitespace for service grouping |
| Method Received | method_received | Intake channel; not evidence of requester identity or channel effectiveness |
| Service Request Status | sr_status | Published administrative status; explicit mapping drives open/closed classification |
| Is Duplicate | is_duplicate_1_0 | Indicator that the source marks the report as a duplicate of another request; no parent ID is supplied |
| Status Change Date | status_change_date | Most recent status-change timestamp; not a full sequence of transitions |
| Created Date | created_date | Creation timestamp; selects the 2025 calendar cohort and starts elapsed time |
| Overdue On Date | overdue_on_date | Recorded deadline; varies by request and is used as recorded, rather than assigning 30 days to every service |
| Last Update Date | last_update_date | Latest published update timestamp; not necessarily a staff action or visit |
| Close Date | close_date | Administrative closure timestamp; no independent resolution verification |
| Service Request Age Days | sr_age_days | Publisher-derived age; retain for comparison and recalculate open age from the fixed reporting cutoff |
| Response Days | response_days | Publisher-derived response interval; no first-response event timestamp is supplied to validate its exact meaning |
| Is Open | open_count | Source open indicator; preserve, compare to status, and flag disagreement |
| Is Closed | closed_count | Source closed indicator; preserve and compare to status |
| Is Overdue | overdue_count | Source overdue indicator; compare with derived open-past-deadline at the fixed cutoff |
| Is Closed on Time | closed_on_time | Source on-time closure indicator; validate against usable closure/deadline timestamps |
| Is Closed Late | closed_late | Source late-closure indicator; retain original in cleaned/raw data |
| Number of Days Late | of_days_late | Publisher-derived lateness; preserve rather than assume it is the desired metric |
| Fiscal Year | fiscal_year | Publisher fiscal year; parse comma-formatted number but do not use it to select calendar 2025 |
| Service Request Location | sr_location | Published address/location label; leave missing values empty |
| State Plane X Coordinate | state_plane_x_coordinate | Projected x value; do not use directly as longitude |
| State Plane Y Coordinate | state_plane_y_coordinate | Projected y value; do not use directly as latitude |
| Location | location | WKT point; parse longitude first, latitude second, and validate world coordinate bounds |

## Derived fact columns

`docs/fact_schema.csv` lists SQL types, nullability and primary-key status for the exact delivered fact table.

| Field(s) | Meaning |
| --- | --- |
| request_number | Unique request ID in this full snapshot build |
| service_key / organization_key / channel_key | Foreign keys to unique dimension rows |
| created_date_key / closed_date_key / deadline_date_key | Integer YYYYMMDD keys from the local calendar date, not the UTC date |
| created_local / closed_local / deadline_local / last_updated_local | Parsed local date/time represented without an offset; retains the City calendar context |
| created_utc / closed_utc / deadline_utc | Unambiguous UTC instant as ISO text; blank when missing or ambiguous |
| source_status / status_class | Published status and explicit analytical mapping |
| is_business_duplicate / is_test | Distinct source-business-duplicate and testing indicators |
| in_primary | 1 when not duplicate-marked and not testing |
| is_closed / is_open | Status-based administrative classification; testing is neither |
| valid_closure | 1 for Closed with valid creation/close instants, nonnegative interval and closure at/before cutoff |
| closure_days | Actual elapsed UTC seconds / 86,400, only when valid_closure is 1 |
| valid_deadline_closure | Valid closure plus usable deadline at/after creation |
| closed_by_deadline | 1 when valid close <= recorded due time; 0 when later; null when ineligible |
| open_age_days | Actual elapsed time from creation to fixed cutoff for Open records; null otherwise |
| open_past_deadline | 1 when Open with valid due time < cutoff; 0 when not yet due; null when inapplicable/unusable |
| source_is_open / source_is_closed / source_is_overdue / source_closed_on_time | Original boolean flags, kept separate from derived status/time values |
| source_response_days / source_age_days / source_fiscal_year | Original numeric values parsed without thousands separators |
| status_flag_conflict | Recognized open/closed status disagrees with at least one source open/closed flag |
| deadline_flag_conflict | Eligible timestamp calculation disagrees with source on-time flag |
| timestamp_ambiguity | At least one populated local timestamp cannot be uniquely localized because of a clock change |
| longitude / latitude | Parsed geographic point; null when not supplied |

Zero and null have different meanings. For example, a zero closure duration is an observed same-instant closure, while a null duration is ineligible or unavailable. Neither is verified physical resolution.
