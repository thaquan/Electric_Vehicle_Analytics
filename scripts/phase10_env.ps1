param(
    [string]$JavaHome = $env:JAVA_HOME,
    [string]$HadoopHome = $env:HADOOP_HOME,
    [string]$PythonExecutable = 'python'
)

# Validate all dependencies before changing this PowerShell session.
if (-not $JavaHome) {
    $jdk = Get-ChildItem 'C:\Program Files\Microsoft\jdk-17*' -Directory -ErrorAction SilentlyContinue |
        Sort-Object Name -Descending | Select-Object -First 1
    if ($jdk) { $JavaHome = $jdk.FullName }
}
if (-not $JavaHome -or -not (Test-Path -LiteralPath "$JavaHome\bin\java.exe")) {
    throw 'Java 17 not found. Pass -JavaHome <JDK directory> or set JAVA_HOME.'
}
$javaVersion = & "$JavaHome\bin\java.exe" -version 2>&1 | Out-String
if ($LASTEXITCODE -ne 0 -or $javaVersion -notmatch 'version "17\.') {
    throw 'This local runtime requires Java 17. Check -JavaHome or JAVA_HOME.'
}
if (-not $HadoopHome) {
    $HadoopHome = Join-Path (Split-Path $PSScriptRoot -Parent) '.tools\hadoop-3.3.5'
}
foreach ($binary in @('winutils.exe', 'hadoop.dll')) {
    if (-not (Test-Path -LiteralPath "$HadoopHome\bin\$binary")) {
        throw "Missing $binary. Pass -HadoopHome <helper directory>; see docs/pipelines/standalone_pipeline.md."
    }
}
$pythonPath = & $PythonExecutable -c 'import sys; print(sys.executable)'
if ($LASTEXITCODE -ne 0 -or -not $pythonPath -or -not (Test-Path -LiteralPath $pythonPath)) {
    throw 'Python not found. Pass -PythonExecutable <venv/Scripts/python.exe>.'
}
$env:JAVA_HOME = (Resolve-Path -LiteralPath $JavaHome).Path
$env:HADOOP_HOME = (Resolve-Path -LiteralPath $HadoopHome).Path
$env:Path = "$env:JAVA_HOME\bin;$env:HADOOP_HOME\bin;$env:Path"
$env:PYSPARK_PYTHON = $pythonPath
$env:PYSPARK_DRIVER_PYTHON = $pythonPath
$env:SPARK_LOCAL_IP = '127.0.0.1'
