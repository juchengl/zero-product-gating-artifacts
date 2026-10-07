param($vcdDir)
$v = Get-ChildItem (Join-Path $vcdDir "*_B?.vcd")
Write-Output ("vcds: " + $v.Count)
foreach ($f in $v) {
    $out = $f.FullName -replace '\.vcd$', '.window.vcd'
    python scripts/window_vcd.py $f.FullName $out --start-tick 60000 --end-tick 20080000 2>&1 | Out-Null
}
$w = Get-ChildItem (Join-Path $vcdDir "*.window.vcd")
Write-Output ("trimmed: " + $w.Count)