from pathlib import Path
BASE = Path(r"C:\Users\Administrator\Desktop\科研\B2_MAC_Followup")

# anticipated responses #4
a = BASE / "paper/anticipated_reviewer_responses.md"
t = a.read_text(encoding="utf-8")
old_start = "4. **\"Single corner tt; ranking may invert at ff/ss.\"** (EIC-#3, DA)"
idx = t.find(old_start)
if idx >= 0:
    end = t.find("\n\n", idx)
    end = end if end > 0 else len(t)
    new_block = ("4. **\"Single corner tt; ranking may invert at ff/ss.\"** (EIC-#3, DA)\n"
       "   Response: **RESOLVED via R3.** Three-corner sweep (tt 25C 1.80V / ff 100C 1.95V / ss 100C 1.60V, "
       "one current PDK build, p90, identical injected activities): the ordering and boundary are corner-stable "
       "— per-variant delta variation < ±0.15 pp across a 1.60–1.95 V / 25–100 C spread. Reported in manuscript "
       "§4.6 / tab:corner.\n"
       "   Status: CLOSED (R3 done 2026-09-19).")
    t = t[:idx] + new_block + t[end:]
    print("responses #4 updated")
a.write_text(t, encoding="utf-8")

# D-group record: R3 section
g = BASE / "docs/D组_证据链诊断记录.md"
t = g.read_text(encoding="utf-8")
add = ("\n\n## R3 完成（2026-09-19）：三角扫描角稳健性\n\n"
       "ff/ss 合并 liberty 的获取路径重启成功：volare（已迁至 chipfoundry）发行包按库拆分，"
       "`sky130_fd_sc_hd.tar.zst`（166.7 MB）含全部工艺角已合并 liberty（sky130B 构建），无需 libify。"
       "三角（tt 25C 1.80V / ff 100C 1.95V / ss 100C 1.60V，同一构建保证自洽）× 五版 p90，"
       "复用既有活动注入（活动与角无关），几何寄生不变。结果（Δ vs B0, %）："
       "B1 −5.46/−5.60/−5.54、B2 −6.07/−6.06/−6.08、**B3 −7.53/−7.60/−7.47**、B4 −4.56/−4.75/−4.67"
       "（tt/ff/ss）——排序与边界角稳健，每变体变化 <±0.15pp；绝对量随角缩放（ff +27%、ss −19%）；"
       "重建 tt 与 ORFS tt 一致 ±0.4%。数据 `results_sky130/r3_corner_compare.json`；论文 §4.6/tab:corner。")
if "## R3 完成" not in t:
    t += add
    print("D-group R3 added")
g.write_text(t, encoding="utf-8")