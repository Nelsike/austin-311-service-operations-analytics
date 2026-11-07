param(
  [Parameter(Mandatory=$true)][string]$AdomdPath,
  [Parameter(Mandatory=$true)][int]$Port
)
$ErrorActionPreference='Stop'
$ProjectRoot=Split-Path -Parent $PSScriptRoot
[void][System.Reflection.Assembly]::LoadFrom((Resolve-Path -LiteralPath $AdomdPath).Path)
$Queries=Get-Content -Raw -LiteralPath (Join-Path $ProjectRoot 'powerbi\validation_queries.json') | ConvertFrom-Json -AsHashtable
$Connection=[Microsoft.AnalysisServices.AdomdClient.AdomdConnection]::new("Data Source=localhost:$Port")
$Results=[ordered]@{}
try {
  $Connection.Open()
  foreach($QueryName in $Queries.Keys) {
    $Command=$Connection.CreateCommand()
    $Command.CommandText=$Queries[$QueryName]
    $Reader=$Command.ExecuteReader()
    $Rows=[System.Collections.Generic.List[object]]::new()
    while($Reader.Read()) {
      $Row=[ordered]@{}
      for($Index=0;$Index -lt $Reader.FieldCount;$Index++) {
        $Column=$Reader.GetName($Index)
        if($Column -match '\[([^\]]+)\]$') { $Column=$Matches[1] }
        $Row[$Column]=if($Reader.IsDBNull($Index)) { $null } else { $Reader.GetValue($Index) }
      }
      $Rows.Add($Row)
    }
    $Reader.Close()
    $Results[$QueryName]=$Rows.ToArray()
  }
} finally { $Connection.Close() }
$Results | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $ProjectRoot 'reports\powerbi_actual_results.json') -Encoding utf8
Write-Output ('Executed '+$Queries.Count+' read-only DAX validation queries against Power BI Desktop.')
