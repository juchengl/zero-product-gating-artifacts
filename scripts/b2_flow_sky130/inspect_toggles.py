import json
s = json.load(open(r"C:\Users\Administrator\Desktop\科研\B2_MAC_Followup\results\replay_rtl_gate_smoke\summary.json", encoding="utf-8"))
row = s[0]
print("keys:", list(row.keys()))
print("sample toggles:", json.dumps(row.get("observed_rtl_toggles"), indent=0)[:300])
print()
for wl in ("p90_random_s101_n1000", "p30_random_s101_n1000", "p00_random_s101_n1000"):
    print("==", wl)
    for r in s:
        if r["workload"] == wl:
            t = r["observed_rtl_toggles"] or {}
            def g(*names):
                for n in names:
                    if n in t:
                        return t[n]
                return -1
            print(f"  {r['variant']}  a_q={g('core.a_q','-')}  b_q={g('core.b_q','-')}  "
                  f"product={g('core.product','-')}  acc={g('core.acc','-')}  "
                  f"zero_q={g('core.zero_q','-')}  total={sum(v for k,v in t.items() if isinstance(v,int))}")
