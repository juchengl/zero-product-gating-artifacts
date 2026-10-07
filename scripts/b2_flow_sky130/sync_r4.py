from pathlib import Path
BASE = Path(r"C:\Users\Administrator\Desktop\科研\B2_MAC_Followup")

# anticipated responses: #4 R4 done
a = BASE / "paper/anticipated_reviewer_responses.md"
t = a.read_text(encoding="utf-8")
old = ("4. **\"Single corner tt; ranking may invert at ff/ss.\"** (EIC-#3, DA)\n"
       "   Response: Dynamic-energy *ratios* are relatively corner-robust; single non-tt corner at 90 % (R3) would confirm. Deferred.\n"
       "   Status: R3 open.")
new = ("4. **\"Single corner tt; ranking may invert at ff/ss.\"** (EIC-#3, DA)\n"
       "   Response: Dynamic-energy *ratios* are relatively corner-robust; leakage at tt/25 C is ~0.002 % of total, so corner effects on the ranking are expected to be small. Non-tt corner (R3) deferred: the upstream consolidation tooling for ff/ss liberty (efabless/libify) is no longer available (Efabless shut down 2025); full multi-corner sign-off belongs to the second-paper tapeout track.\n"
       "   Status: R3 deferred with rationale; R4 DONE (detection cost re-measured at 6 digits: +0.77 % vs the rounded +0.47 %).")
if old in t:
    t = t.replace(old, new); print("responses #4 updated")
else:
    print("responses #4 pattern not found")
a.write_text(t, encoding="utf-8")

# D-group record: R4 section
g = BASE / "docs/D组_证据链诊断记录.md"
t = g.read_text(encoding="utf-8")
add = ("\n\n## R4 完成（2026-09-19）：6 位分辨率重测检测代价\n\n"
       "p00 全 9 负载 × B0/B1/B4 用 `report_power -digits 6` 重跑（27 次）。高精度均值（pJ/tx）："
       "B0=4.2417、B1=4.0176、B4=4.0503。**检测代价 = +0.77%**（此前 3 位舍入低估为 +0.47%，低估约 40%）——"
       "分辨率问题真实存在且已修正。p90 五版高精度单种子值与主表均值一致（B0 4.101 在 4.089±0.018 内）。"
       "数据 `results_sky130/r4_p00_digits6.json` 与 `r1/../odo/*_digits6/`。\n\n"
       "## R3 状态：推迟（有据）\n\n"
       "efabless/libify（ff/ss liberty 合并工具）已随 Efabless 2025 年关停而下线（codeload 404）；"
       "ORFS sky130hd 平台只带 tt。自写 JSON→Liberty 合并器风险高。EIC 席位评估单角在此档位属常规，"
       "且 tt/25C 泄漏仅占 0.002%；多角完整签核列入第二篇流片路线。")
if "## R4 完成" not in t:
    t += add
    print("D-group R4 added")
else:
    print("D-group already has R4")
g.write_text(t, encoding="utf-8")