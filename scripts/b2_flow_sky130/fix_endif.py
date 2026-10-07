import re
from pathlib import Path
p = Path.home() / "b2_sky130/models_flat/sky130_fd_sc_hd_selfcontained.v"
t = p.read_text(encoding="utf-8")
t2 = re.sub(r"^`endif (SKY130_FD_SC_HD__LPFLOW_BLEEDER_FUNCTIONAL_V)\s*$",
            r"`endif // \1", t, flags=re.M)
p.write_text(t2, encoding="utf-8")
print("fixed:", t != t2)
