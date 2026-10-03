$jdk = Get-ChildItem 'C:\Program Files\Microsoft\jdk-17*' -Directory | Sort-Object Name -Descending | Select-Object -First 1
if (-not $jdk) { throw 'Microsoft OpenJDK 17 not found' }
$hadoop = 'D:\electric_vehical_sales\.tools\hadoop-3.3.5'
if (-not (Test-Path "$hadoop\bin\winutils.exe")) { throw 'winutils.exe not found for Phase 10 runtime' }
$env:JAVA_HOME = $jdk.FullName
$env:HADOOP_HOME = $hadoop
$env:Path = "$($jdk.FullName)\bin;$hadoop\bin;$env:Path"
$env:SPARK_LOCAL_IP = '127.0.0.1'
