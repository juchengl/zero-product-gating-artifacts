from pathlib import Path
p = Path("/mnt/c/Users/Administrator/Desktop/科研/B2_MAC_Followup/paper/draft_v0.4.md")
t = p.read_text(encoding="utf-8")
note = ("**注（2026-09-19）：本 Markdown 稿为 v0.2 时期草稿；权威版本为 manuscript.tex"
        "（已含 §4.4 毛刺真值、§4.5 布局稳健性、摘要/结论的布局限定更新）。**\n\n")
if "权威版本为 manuscript.tex" not in t:
    lines = t.splitlines()
    for i, l in enumerate(lines):
        if l.startswith("# "):
            lines.insert(i + 1, "\n" + note)
            break
    p.write_text("\n".join(lines), encoding="utf-8")
    print("note added")
else:
    print("already noted")