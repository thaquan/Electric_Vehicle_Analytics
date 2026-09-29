param([int]$DesktopPid=5580,[string]$Match='.',[string]$Action='List',[string]$ExactName='', [int]$Occurrence=-1)
$ErrorActionPreference='Stop'
Add-Type -AssemblyName UIAutomationClient
$condition=New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ProcessIdProperty,$DesktopPid)
$windows=[System.Windows.Automation.AutomationElement]::RootElement.FindAll([System.Windows.Automation.TreeScope]::Children,$condition)
$reportWindows=@($windows | Where-Object {$_.Current.Name -match 'RPT_EV_Analytics'})
if($reportWindows.Count -eq 1){$window=$reportWindows[0]}elseif($windows.Count -eq 1){$window=$windows[0]}else{throw 'Cannot identify a unique report window'}
if(-not $window){throw 'Desktop window not found'}
$elements=$window.FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition)
$reportTabs=@($elements | Where-Object {$_.Current.ControlType -eq [System.Windows.Automation.ControlType]::TabItem -and $_.Current.Name -match 'RPT_EV_Analytics - Power BI$'})
if($reportTabs.Count -eq 1){
 ([System.Windows.Automation.SelectionItemPattern]$reportTabs[0].GetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern)).Select()
 $elements=$window.FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition)
}
if($Action -eq 'List'){
 $elements | ForEach-Object {if($_.Current.Name -match $Match -and -not $_.Current.IsOffscreen){[pscustomobject]@{Name=$_.Current.Name;Type=$_.Current.ControlType.ProgrammaticName;Id=$_.Current.AutomationId;Rect=$_.Current.BoundingRectangle.ToString();Patterns=($_.GetSupportedPatterns().ProgrammaticName -join ',')}}} | ConvertTo-Json -Depth 3
}else{
 $target=@($elements | Where-Object {$_.Current.Name -eq $ExactName -and -not $_.Current.IsOffscreen -and (($Action -in @('CtrlClick','Click')) -or ($_.GetSupportedPatterns().ProgrammaticName -contains $Action))})
 if($Occurrence -ge 0){if($Occurrence -ge $target.Count){throw 'Requested control occurrence not found'};$target=@($target[$Occurrence])}
 if($target.Count -ne 1){throw "Expected one actionable control, found $($target.Count)"}
 if($Action -in @('CtrlClick','Click')){
 Add-Type 'using System; using System.Runtime.InteropServices; public class EvInput { [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h); [DllImport("user32.dll")] public static extern bool SetCursorPos(int x,int y); [DllImport("user32.dll")] public static extern void mouse_event(uint f,uint x,uint y,uint d,UIntPtr e); [DllImport("user32.dll")] public static extern void keybd_event(byte v,byte s,uint f,UIntPtr e); }'
 $r=$target[0].Current.BoundingRectangle
 [EvInput]::SetForegroundWindow([IntPtr]$window.Current.NativeWindowHandle) | Out-Null
 [EvInput]::SetCursorPos([int]($r.X+$r.Width/2),[int]($r.Y+$r.Height/2)) | Out-Null
 try{if($Action -eq 'CtrlClick'){[EvInput]::keybd_event(17,0,0,[UIntPtr]::Zero)};Start-Sleep -Milliseconds 150;[EvInput]::mouse_event(2,0,0,0,[UIntPtr]::Zero);[EvInput]::mouse_event(4,0,0,0,[UIntPtr]::Zero);Start-Sleep -Milliseconds 300}finally{[EvInput]::keybd_event(17,0,2,[UIntPtr]::Zero)}
 }
 elseif($Action -eq 'InvokePatternIdentifiers.Pattern'){([System.Windows.Automation.InvokePattern]$target[0].GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern)).Invoke()}
 elseif($Action -eq 'SelectionItemPatternIdentifiers.Pattern'){([System.Windows.Automation.SelectionItemPattern]$target[0].GetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern)).Select()}
 elseif($Action -eq 'ExpandCollapsePatternIdentifiers.Pattern'){([System.Windows.Automation.ExpandCollapsePattern]$target[0].GetCurrentPattern([System.Windows.Automation.ExpandCollapsePattern]::Pattern)).Expand()}
 else{throw 'Unsupported action'}
 Write-Output "Action completed: $ExactName"
}
