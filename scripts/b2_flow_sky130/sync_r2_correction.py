from pathlib import Path
BASE = Path("/mnt/c/Users/Administrator/Desktop/科研/B2_MAC_Followup")

# 1) draft_v0.4.md §4.5 replacement
d = BASE / "paper/draft_v0.4.md"
t = d.read_text(encoding="utf-8")
old_md = """B3（输入保持）在每一个布局内的配对比较中都是最优——排序结论对布局稳健。
2. **绝对量随布局波动明显**（B3−B0 在 −4.8%…−7.4% 之间；B0 自身跨布局差 8%）——诚实承认单布局绝对值的局限。
3. **u38 下 B1 反常劣于 B0**——恰好实证了"跨布局绝对比较不可靠、同布局配对比较才有效"这一方法学点（已写入论文 §4.5，作为方法学贡献的一部分而非掩盖）。"""
new_md = """B3（输入保持）在每一个布局内的配对比较中都是最优，且是从不劣于基线的唯一变体（B3−B0 = 0…−7.4%）。
2. **B1（valid 隔离）的符号随布局翻转**（u38 +6.8%、u40 −5.5%、u42 +3.4%）：其使能 mux 的内部功耗可以超过它节省的切换功耗——单布局正收益不构成稳健性证据。
3. **绝对量随布局波动 ±5%（大于效应本身）**：只有同布局配对比较有效。审计更正：初版 R2 误用了带 0.01ns 占位延迟的模型与零延迟基准比较，方法一致化后得出本结论（2026-09-19 审计发现并修正）。"""
if old_md in t:
    t = t.replace(old_md, new_md)
    print("draft §4.5 updated")
else:
    print("draft §4.5: pattern not found (check manually)")
d.write_text(t, encoding="utf-8")

# 2) anticipated responses #3
a = BASE / "paper/anticipated_reviewer_responses.md"
t = a.read_text(encoding="utf-8")
old_a = "Response: **ADDRESSED via R2.** Layout perturbation (CORE_UTILIZATION 38/40/42, all five variants, p90): B3 is the best variant *within every layout* (paired), though absolute magnitudes vary −4.8…−7.4% and B1 at u38 anomalously flips vs B0 — we state that cross-layout absolute comparisons are unreliable while within-layout paired ordering is robust. Reported in manuscript §4.5 / tab:layout."
new_a = "Response: **ADDRESSED via R2 (method-corrected).** Layout perturbation (CORE_UTILIZATION 38/40/42, all five variants, p90, identical zero-delay method): B3 is best *within every layout* and never regresses vs B0 (0…−7.4%); but B1 flips sign across layouts (+6.8/−5.5/+3.4%) — its enable-mux internal power can exceed the switching it saves. We report this as a finding (isolation benefits are layout-specific; single-layout positives are not robust evidence), not a footnote. Absolute energies vary ±5% across layouts, larger than the effects; only within-layout paired comparisons are meaningful. Reported in manuscript §4.5 / tab:layout."
if old_a in t:
    t = t.replace(old_a, new_a)
    print("responses #3 updated")
else:
    print("responses #3: pattern not found")
a.write_text(t, encoding="utf-8")

# 3) D-group record R2 correction note
g = BASE / "docs/D组_证据链诊断记录.md"
t = g.read_text(encoding="utf-8")
marker = "数据 `results_sky130/r2_layout_compare.json`。"
corr = ("数据 `results_sky130/r2_layout_compare.json`。\n\n"
        "**审计更正（2026-09-19）**：初版 R2 误用 `sky130_delayed.v`（0.01ns 占位延迟）与零延迟基准比较，方法不一致；"
        "以零延迟模型重跑 u38/u42 后数字修正为 u38 B0=3.544/B1=3.784/B2=3.584/B3=3.503/B4=3.684、"
        "u42 B0=3.503/B1=3.624/B2=3.524/B3=3.503/B4=3.704。结论相应加强：B1 符号随布局翻转（+6.8/−5.5/+3.4%），"
        "B3 是唯一从不劣于基线的变体（0…−7.4%）。10 次仿真重验 10/10 PASS（1005 周期）。")
if marker in t and "审计更正（2026-09-19）" not in t:
    t = t.replace(marker, corr)
    print("D-group R2 correction added")
else:
    print("D-group: marker missing or already corrected")
g.write_text(t, encoding="utf-8")