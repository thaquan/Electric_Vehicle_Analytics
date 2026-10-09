param(
    [string]$DataDirectory = (Join-Path $PSScriptRoot '..\data\raw\kaggle'),
    [string]$MetadataDirectory = (Join-Path $PSScriptRoot '..\metadata'),
    [string]$DocsDirectory = (Join-Path $PSScriptRoot '..\docs')
)

$ErrorActionPreference = 'Stop'
$sourceUrl = 'https://www.kaggle.com/competitions/playground-series-s6e9'
$sourceNotebook = 'https://www.kaggle.com/code/thuandao/predicting-electric-vehicle-full-eda'
$numericColumns = @{
    'id' = $true; 'Age' = $true; 'Annual_Income_USD' = $true
    'Daily_Commute_km' = $true; 'Number_of_Cars_Owned' = $true
    'Charging_Stations_Near_Home' = $true; 'Charging_Stations_Near_Work' = $true
}

New-Item -ItemType Directory -Force -Path $MetadataDirectory, $DocsDirectory | Out-Null

function New-ColumnStats([string]$name) {
    [ordered]@{
        name = $name; null_count = 0; non_null_count = 0; distinct_values = @{}
        min = $null; max = $null; sum = [double]0; sum_of_squares = [double]0
    }
}

function Get-CsvProfile([System.IO.FileInfo]$file) {
    $reader = [System.IO.StreamReader]::new($file.FullName)
    try {
        $header = $reader.ReadLine().Split(',')
        $stats = @{}
        foreach ($column in $header) { $stats[$column] = New-ColumnStats $column }
        $rows = 0
        while (($line = $reader.ReadLine()) -ne $null) {
            $rows++
            $fields = $line.Split(',')
            if ($fields.Count -ne $header.Count) {
                throw "Unexpected field count in $($file.Name) at data row $rows."
            }
            for ($i = 0; $i -lt $header.Count; $i++) {
                $column = $header[$i]
                $value = $fields[$i].Trim()
                $columnStats = $stats[$column]
                if ([string]::IsNullOrWhiteSpace($value)) {
                    $columnStats.null_count++
                    continue
                }
                $columnStats.non_null_count++
                if ($numericColumns.ContainsKey($column)) {
                    try {
                        $number = [double]::Parse($value, [Globalization.CultureInfo]::InvariantCulture)
                    } catch {
                        throw "Invalid numeric value in $($file.Name), data row $rows, column ${column}: '$value'."
                    }
                    if ($null -eq $columnStats.min -or $number -lt $columnStats.min) { $columnStats.min = $number }
                    if ($null -eq $columnStats.max -or $number -gt $columnStats.max) { $columnStats.max = $number }
                    $columnStats.sum += $number
                    $columnStats.sum_of_squares += $number * $number
                } else {
                    if (-not $columnStats.distinct_values.ContainsKey($value)) { $columnStats.distinct_values[$value] = 0 }
                    $columnStats.distinct_values[$value]++
                }
            }
        }
    } finally { $reader.Dispose() }

    $columnProfiles = foreach ($column in $header) {
        $columnStats = $stats[$column]
        $profile = [ordered]@{
            name = $column
            null_count = $columnStats.null_count
            null_percentage = if ($rows) { [math]::Round(100 * $columnStats.null_count / $rows, 6) } else { 0 }
        }
        if ($numericColumns.ContainsKey($column)) {
            $mean = if ($columnStats.non_null_count) { $columnStats.sum / $columnStats.non_null_count } else { $null }
            $variance = if ($columnStats.non_null_count -gt 1) { ($columnStats.sum_of_squares - $columnStats.non_null_count * $mean * $mean) / ($columnStats.non_null_count - 1) } else { 0 }
            $profile.type = 'numeric'
            $profile.min = $columnStats.min
            $profile.max = $columnStats.max
            $profile.mean = if ($null -ne $mean) { [math]::Round($mean, 6) } else { $null }
            $profile.stddev = [math]::Round([math]::Sqrt([math]::Max([double]0, [double]$variance)), 6)
        } else {
            $profile.type = 'categorical'
            $profile.distinct_count = $columnStats.distinct_values.Count
            if ($column -eq 'Buyer_ID') {
                $profile.value_counts_omitted = 'Record identifiers are not published.'
            } else {
                $profile.value_counts = [ordered]@{}
                foreach ($item in ($columnStats.distinct_values.GetEnumerator() | Sort-Object -Property @{ Expression = 'Value'; Descending = $true }, @{ Expression = 'Key'; Descending = $false })) {
                    $profile.value_counts[$item.Key] = $item.Value
                }
            }
        }
        [PSCustomObject]$profile
    }
    [PSCustomObject]@{ file = $file.Name; data_rows = $rows; columns = $header; column_profiles = $columnProfiles }
}

$files = Get-ChildItem -LiteralPath $DataDirectory -Filter '*.csv' | Sort-Object Name
$profiles = foreach ($file in $files) { Get-CsvProfile $file }
$manifestFiles = foreach ($file in $files) {
    $profile = $profiles | Where-Object file -eq $file.Name
    [ordered]@{
        name = $file.Name
        bytes = $file.Length
        data_rows = $profile.data_rows
        columns = $profile.columns
        sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $file.FullName).Hash
    }
}

$manifest = [ordered]@{
    source = 'Kaggle Playground Series S6E9: Predicting Electric Vehicle Purchases'
    competition_url = $sourceUrl
    notebook_reference = $sourceNotebook
    acquisition_note = 'Retrieved from the public repository referenced by the Kaggle notebook; validate against a direct Kaggle download when API access is configured.'
    profiled_at_utc = [DateTime]::UtcNow.ToString('o')
    files = $manifestFiles
}
$manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $MetadataDirectory 'source_manifest.json') -Encoding utf8

$categorical = [ordered]@{}
foreach ($profile in $profiles) {
    $categorical[$profile.file] = @($profile.column_profiles | Where-Object type -eq 'categorical')
}
$categorical | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $MetadataDirectory 'categorical_profile.json') -Encoding utf8
$profiles | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $MetadataDirectory 'profiling_summary.json') -Encoding utf8

$dictionary = @('# Data dictionary', '', 'This dictionary is generated from the first profiling run. Column meanings are based on the Kaggle notebook description; types and observed values are derived from the local CSV files.', '', '| Field | Logical type | Role |', '| --- | --- | --- |')
$roles = @{
    id = 'Competition record key'; Buyer_ID = 'Original-source record key'; Will_Buy_EV = 'EV purchase-interest target';
    Age = 'Buyer demographic'; Gender = 'Buyer demographic'; Annual_Income_USD = 'Financial attribute'; City_Type = 'Location segment';
    Daily_Commute_km = 'Mobility attribute'; Number_of_Cars_Owned = 'Vehicle ownership'; Current_Car_Type = 'Current vehicle';
    Charging_Stations_Near_Home = 'Charging infrastructure'; Charging_Stations_Near_Work = 'Charging infrastructure';
    Home_Charging_Possible = 'Charging accessibility'; Environmental_Concern_Level = 'Environmental attitude';
    Subsidy_Available = 'Policy/incentive'; Range_Anxiety_Level = 'EV adoption barrier'
}
$allColumns = @($profiles | ForEach-Object column_profiles | Group-Object name | ForEach-Object { $_.Group[0] })
foreach ($column in $allColumns) {
    $logicalType = if ($column.type -eq 'numeric') { 'Numeric' } else { 'Categorical' }
    $dictionary += "| $($column.name) | $logicalType | $($roles[$column.name]) |"
}
$dictionary += '', 'Important: this is a synthetic competition dataset. Analytical results describe this dataset only and are not causal or population-level EV-market claims.'
$dictionary | Set-Content -LiteralPath (Join-Path $DocsDirectory 'data_dictionary.md') -Encoding utf8

Write-Host "Profiled $($files.Count) CSV files. Artifacts written to $MetadataDirectory and $DocsDirectory."
