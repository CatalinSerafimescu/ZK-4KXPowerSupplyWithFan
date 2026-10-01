"""Minimal S-expression reader/writer for KiCad files."""
import math
import re
from pathlib import Path

KICAD = Path(r"C:\Program Files\KiCad\10.0\share\kicad")


class Q(str):
    """A quoted string atom."""


_TOK = re.compile(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()"]+')


def parse(text: str):
    stack, cur = [], []
    for m in _TOK.finditer(text):
        t = m.group(0)
        if t == "(":
            stack.append(cur)
            cur = []
        elif t == ")":
            done = cur
            cur = stack.pop()
            cur.append(done)
        elif t[0] == '"':
            cur.append(Q(t[1:-1].replace('\\"', '"').replace("\\\\", "\\")))
        else:
            cur.append(t)
    return cur[0]


def dump(node, indent=0) -> str:
    if isinstance(node, Q):
        return '"' + node.replace("\\", "\\\\").replace('"', '\\"') + '"'
    if not isinstance(node, list):
        return str(node)
    if all(not isinstance(x, list) for x in node):
        return "(" + " ".join(dump(x) for x in node) + ")"
    pad = "\t" * (indent + 1)
    parts, i = [], 0
    head = []
    while i < len(node) and not isinstance(node[i], list):
        head.append(dump(node[i]))
        i += 1
    out = "(" + " ".join(head)
    for x in node[i:]:
        out += "\n" + pad + dump(x, indent + 1)
    return out + "\n" + "\t" * indent + ")"


def find(node, key):
    return [x for x in node if isinstance(x, list) and x and x[0] == key]


def first(node, key):
    r = find(node, key)
    return r[0] if r else None


# ── Library symbols ───────────────────────────────────────────────────────────
_LIBS: dict[str, list] = {}


def _lib(path: Path):
    k = str(path)
    if k not in _LIBS:
        _LIBS[k] = parse(path.read_text(encoding="utf-8"))
    return _LIBS[k]


def lib_symbol(lib_id: str, lib_path: Path | None = None):
    """Return a flattened copy of a library symbol, named 'Lib:Name'."""
    import copy
    lib, name = lib_id.split(":")
    path = lib_path or KICAD / "symbols" / f"{lib}.kicad_sym"
    syms = {s[1]: s for s in find(_lib(path), "symbol")}
    sym = copy.deepcopy(syms[name])
    ext = first(sym, "extends")
    if ext:
        parent = copy.deepcopy(syms[ext[1]])
        props = {p[1]: p for p in find(sym, "property")}
        merged = [parent[0], Q(name)]
        for x in parent[2:]:
            if isinstance(x, list) and x[0] == "property" and x[1] in props:
                merged.append(props.pop(x[1]))
            elif isinstance(x, list) and x[0] == "symbol":
                x[1] = Q(x[1].replace(ext[1], name, 1))
                merged.append(x)
            else:
                merged.append(x)
        # remaining child-only properties go before sub-symbols
        idx = next(i for i, x in enumerate(merged) if isinstance(x, list) and x[0] == "symbol")
        merged[idx:idx] = list(props.values())
        sym = merged
    sym[1] = Q(lib_id)
    return sym


def pins(sym, unit: int):
    """[(number, name, x, y, angle)] for the given unit (unit 0 = common)."""
    out = []
    base = sym[1].split(":")[-1]
    for sub in find(sym, "symbol"):
        m = re.match(re.escape(base) + r"_(\d+)_(\d+)$", sub[1])
        if not m:
            continue
        u, b = int(m.group(1)), int(m.group(2))
        if u not in (0, unit) or b not in (0, 1):
            continue
        for p in find(sub, "pin"):
            at = first(p, "at")
            num = first(p, "number")[1]
            nm = first(p, "name")[1]
            out.append((str(num), str(nm), float(at[1]), float(at[2]), float(at[3]) if len(at) > 3 else 0.0))
    return out


def outward(angle: float):
    """Unit vector (schematic coords, y down) pointing away from the body."""
    a = math.radians(angle)
    return (-round(math.cos(a)), round(math.sin(a)))
