import io
from pathlib import Path
p = Path(r"C:\Users\Administrator\Desktop\科研\B2_MAC_Followup\results_sky130\phase1_energy_smoke.md")
banner = (
    "> **⚠️ 失效标注（2026-09-18）：本表数据已被验证为无效能耗结论（SPEF 未进模型 + 活动仅 53 引脚/其余为传播），"
    "仅保留作伪影证据。论文不得引用。见 docs\\D组_证据链诊断记录.md。**\n\n"
)
t = p.read_text(encoding="utf-8")
if "失效标注" not in t:
    p.write_text(banner + t, encoding="utf-8")
    print("banner added")
else:
    print("already marked")
# also mark the json
j = Path(r"C:\Users\Administrator\Desktop\科研\B2_MAC_Followup\results_sky130\phase1_energy_smoke.json")
import json
d = json.loads(j.read_text(encoding="utf-8"))
d["superseded"] = {"date": "2026-09-18",
                   "reason": "SPEF nets anonymous/unmapped in standalone OpenSTA (1328 net-not-found) and read_vcd annotated only 53 pins with propagation for the rest; superseded by in-session extraction + per-driver-pin activity injection results",
                   "do_not_cite": True}
j.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
print("json marked")