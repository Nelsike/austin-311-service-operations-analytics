// Create a blank query named LoadCsv, paste this function, and disable its load.
// Create a TEXT parameter pProjectFolder pointing to the project folder, without a trailing slash.
(FileName as text) as table =>
let
    Source = Csv.Document(File.Contents(pProjectFolder & "\data\powerbi\" & FileName & ".csv"),
        [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Nulls = Table.ReplaceValue(Headers, "", null, Replacer.ReplaceValue, Table.ColumnNames(Headers))
in
    Nulls
