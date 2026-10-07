from pathlib import Path
exec(Path(r"C:\Users\Administrator\Desktop\科研\B2_MAC_Followup\flow_sky130\make_fig5.py").read_text().split("nm_zd, ev_zd = parse(ZD)")[0])
nm_zd, ev_zd = parse(ZD)
print("zd: names", len(nm_zd), "event nets", len(ev_zd))
nm_gl, ev_gl = parse(GL)
print("gl: names", len(nm_gl), "event nets", len(ev_gl))
# check a couple of names present in both
common = set(nm_zd) & set(nm_gl)
print("common names:", len(common))
print("sample gl names:", list(nm_gl)[:5])