"""Inline all `include directives of the consolidated sky130 model file,
producing a single self-contained simulation source (no -I needed).

Usage: python make_selfcontained.py <flat_dir> <consolidated.v> <out.v>
"""
import sys
from pathlib import Path

flat = Path(sys.argv[1])
src = Path(sys.argv[2])
out = Path(sys.argv[3])
seen = set()

def expand(path: Path, depth=0):
    if depth > 6:
        return
    text = path.read_text(encoding="utf-8", errors="replace")
    result = []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("`include"):
            target = s.split('"')[1] if '"' in s else s.split()[1]
            inc = flat / target
            if inc.exists() and str(inc) not in seen:
                seen.add(str(inc))
                result.append(f"// ---- inlined from {target} ----")
                result.append(expand(inc, depth + 1))
            else:
                result.append(f"// include skipped (missing or seen): {target}")
        else:
            result.append(line)
    return "\n".join(result)

out.write_text(expand(src) + "\n", encoding="utf-8")
print(f"self-contained model: {out} ({out.stat().st_size/1e6:.1f} MB, {len(seen)} includes inlined)")
