param($LogPath)
$c = Get-Content -LiteralPath $LogPath
Write-Output ("lines: " + $c.Count)
$errs = $c | Select-String -Pattern "error" -CaseSensitive:$false
Write-Output ("errors: " + @($errs).Count)
$errs | Select-Object -First 4 | ForEach-Object { Write-Output $_.Line }
Write-Output "--- last 2 non-UNIT_DELAY lines ---"
$c | Where-Object { $_ -notmatch "UNIT_DELAY" } | Select-Object -Last 2
