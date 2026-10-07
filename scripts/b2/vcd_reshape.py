"""Reshape a replay VCD for OpenSTA read_vcd annotation on a flat netlist.

Transformations:
  1. Remove all $scope hierarchy - every variable lands at VCD root, so
     read_vcd (without -scope) matches design nets by flat name.
  2. Strip the leading "core." prefix from variable names that carry it
     (the ORFS post-route netlist is flattened with escaped names like
     \\core.a_q[0]; pair this with stripping "core." from the netlist).
  3. Expand vector variables into per-bit scalar variables, because
     annotation targets are scalar pins.

Usage: python vcd_reshape.py <in.vcd> <out.vcd> [--strip-prefix core.]
"""
import sys
from pathlib import Path

PREFIX = "core."


def new_name(name: str) -> str:
    # Strip the leading backslash of escaped-identifier VCD names (iverilog
    # dumps \a_q[7] for a net named a_q[7]), then any core. prefix.
    name = name.lstrip("\\")
    if name.startswith(PREFIX):
        return name[len(PREFIX):]
    return name


def main():
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    lines = src.read_text().splitlines()
    out = []
    var_map = {}   # old id -> {"width": w, "bits": [(new_id, bitindex_from_lsb), ...]}
    in_defs = True
    for line in lines:
        t = line.strip()
        if in_defs:
            if t.startswith("$scope") or t.startswith("$upscope"):
                continue  # drop hierarchy
            if t.startswith("$var"):
                # $var wire 8 ! a [7:0] $end
                parts = t.split()
                width = int(parts[2])
                vid = parts[3]
                name = parts[4]
                var_map[vid] = {"width": width, "bits": []}
                if width == 1:
                    var_map[vid]["bits"].append((vid, 0))
                    out.append("$var wire 1 {} {} $end".format(vid, new_name(name)))
                else:
                    for i in range(width):
                        nid = vid + "#" + str(i)
                        var_map[vid]["bits"].append((nid, i))
                        out.append("$var wire 1 {} {}[{}] $end".format(nid, new_name(name), i))
                continue
            if t.startswith("$enddefinitions"):
                in_defs = False
                out.append(t)
                continue
            out.append(line)
            continue
        # value change section
        if t.startswith("#") or t.startswith("$"):
            out.append(line)
            continue
        if t.startswith("b") or t.startswith("B"):
            bits, vid = t[1:].split()
            info = var_map.get(vid)
            if info is None:
                continue
            w = info["width"]
            bits = bits.rjust(w, "x")  # VCD truncates leading zeros/x
            for nid, i in info["bits"]:
                out.append(bits[w - (i + 1)] + nid)
            continue
        if len(t) >= 2 and t[0] in "01xXzZ":
            vid = t[1:]
            if vid in var_map:
                out.append(line)
            continue
        out.append(line)
    dst.write_text("\n".join(x for x in out if x is not None) + "\n")
    print("reshaped {} -> {} ({} mapped ids)".format(src.name, dst.name, len(var_map)))


if __name__ == "__main__":
    main()
