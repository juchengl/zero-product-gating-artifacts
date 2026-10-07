"""Inject minimal specify blocks (IOPATH) into sky130 wrapper modules so Icarus
can annotate SDF IOPATH delays -> glitch-true gate simulation.

For each module sky130_fd_sc_hd__<cell>_<N> (the wrapper the netlist instantiates),
emit a specify block with IOPATH in=>out for every input/output pair (placeholder
delays; SDF overrides them). FF cells get IOPATH (posedge CLK)=>(Q). No timing
checks (avoids needing notifier/AWAKE helper wires); Icarus annotates only delays.

Usage: python inject_specify.py <model_in.v> <model_out.v>
"""
import re, sys
from pathlib import Path

DEL = "= (0.01, 0.01)"
CLK_SENS = {"dfxtp", "sdfrbp", "sdfrtn", "sdfrtp", "sdfncp", "latcht", "dlatch", "dfrtp", "dfcpb", "dfrn", "sdfrp", "mux2d1", "clkintbuf"}


def split_modules(text):
    # yield (module_name, body_start, body_end) spans
    for m in re.finditer(r"\bmodule\s+(sky130_fd_sc_hd__\w+)", text):
        name = m.group(1)
        # find matching endmodule from m.end()
        e = text.find("\nendmodule", m.end())
        if e == -1:
            continue
        yield name, m.start(), e


def ports_of(body):
    ins, outs = [], []
    for m in re.finditer(r"\b(input|output)\s+(?:wire\s+|reg\s+|supply1\s+|supply0\s+)?(?:\[[^\]]*\]\s*)?(\w+)", body):
        kind, nm = m.group(1), m.group(2)
        if nm in ("VPWR", "VGND", "VPB", "VNB"):
            continue
        (ins if kind == "input" else outs).append(nm)
    return ins, outs


def main():
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    text = src.read_text(errors="replace")
    # collect edits (insertion offset, specify text)
    edits = []
    for name, ms, me in split_modules(text):
        if not re.search(r"__\w+_\d+$", name):  # wrapper = ends with _<size>
            continue
        body = text[ms:me]
        ins, outs = ports_of(body)
        if not outs:
            continue
        cell = re.sub(r"^sky130_fd_sc_hd__", "", name)
        base = re.sub(r"_\d+$", "", cell)
        lines = ["specify"]
        if base in CLK_SENS:
            clk = "CLK" if "CLK" in ins else None
            if clk:
                for i in ins:
                    if i == clk:
                        continue
                    lines.append(f"(posedge {clk} => ({outs[0]} : {i})) {DEL};")
            else:
                for o in outs:
                    for i in ins:
                        lines.append(f"({i} => {o}) {DEL};")
        else:
            for o in outs:
                for i in ins:
                    lines.append(f"({i} => {o}) {DEL};")
        lines.append("endspecify")
        edits.append((me, "\n" + "\n".join(lines) + "\n"))
    # apply edits back-to-front
    for off, block in sorted(edits, key=lambda x: -x[0]):
        text = text[:off] + block + text[off:]
    dst.write_text(text)
    print(f"injected specify into {len(edits)} wrapper modules -> {dst}")


if __name__ == "__main__":
    main()