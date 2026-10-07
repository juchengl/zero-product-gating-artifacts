@echo off & setlocal enabledelayedexpansion
REM Full 48x5 matrix: step 1-2 on Windows (replay), step 3-4 in WSL (injection power)
cd /d "C:\Users\Administrator\Desktop\科研\B2_MAC_Followup"
set VCD_DIR=results\replay_gate_gate_smoke
set MANIFEST=data\gate_smoke\manifest.json
set NETLIST_DIR=results_sky130\netlists
set MODEL=results_sky130\models_flat\sky130_fd_sc_hd_selfcontained.v

REM Step 1: gate replays 48 workloads x 5 variants with VCD retention
echo %date% %time% Starting 240 gate replays...
python scripts\replay.py --netlist-dir %NETLIST_DIR% --cells %MODEL% --manifest %MANIFEST% --keep-vcd > gate_replay_full.log 2>&1
if %ERRORLEVEL% neq 0 type gate_replay_full.log & exit /b %ERRORLEVEL%
echo %date% %time% Gate replays done

REM Step 2: trim all VCDs to measurement window
for %%f in (%VCD_DIR%\*_B?.vcd) do python scripts\window_vcd.py "%%f" "%%~nf.window.vcd" --start-tick 60000 --end-tick 20080000 >> trim.log 2>&1
echo %date% %time% VCD trim done

REM Step 3: injection + power in WSL
wsl -d Ubuntu-22.04 -u research -- bash -c "
cd ~
WL=\$(python3 -c \"import json; print(' '.join(r['name'] for r in json.load(open('/mnt/c/Users/Administrator/Desktop/科研/B2_MAC_Followup/data/gate_smoke/manifest.json')))))\"
for wl in \$WL; do
  for n in 0 1 2 3 4; do
    ~/run_insession_power.sh \"\$wl\" \"\$n\" >> /mnt/c/Users/Administrator/Desktop/科研/B2_MAC_Followup/matrix_full_odo.log 2>&1
  done
done
echo FULL-MATRIX-DONE \$(date +%%T)
" >> matrix_wsl.log 2>&1

REM Step 4: collect final table
wsl -d Ubuntu-22.04 -- python3 /mnt/c/Users/Administrator/Desktop/科研/B2_MAC_Followup/flow_sky130/collect_phase2.py /home/research/b2_sky130/odo /mnt/c/Users/Administrator/Desktop/科研/B2_MAC_Followup/results_sky130 >> collect_full.log 2>&1
echo %date% %time% ALL DONE