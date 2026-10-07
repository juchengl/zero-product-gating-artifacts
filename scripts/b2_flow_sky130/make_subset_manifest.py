"""Write a subset replay manifest filtered by workload-name substring.

Usage: python make_subset_manifest.py <src_manifest> <dst_manifest> <substr,...>
"""
import json, sys
from pathlib import Path

src, dst, pattern = sys.argv[1], sys.argv[2], sys.argv[3]
subs = [s.strip() for s in pattern.split(",") if s.strip()]
records = json.loads(Path(src).read_text(encoding="utf-8"))
picked = [r for r in records if any(s in r["name"] for s in subs)]
Path(dst).write_text(json.dumps(picked, indent=2), encoding="utf-8")
print(f"{len(picked)}/{len(records)} workloads -> {dst}")
for r in picked:
    print(" ", r["name"])
