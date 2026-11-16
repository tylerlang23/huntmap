#!/usr/bin/env python3
"""Read newline-delimited GeoJSON parcels on stdin, keep only what the map needs, write to stdout.
Usage: slim.py [County name]   (the name is used when the file has no county column)"""
import json, re, sys

county = sys.argv[1] if len(sys.argv) > 1 else ""
PATS = {
    "owner": [r"^owner_?name$", r"^own.*name", r"^ownname", r"^owner1?$", r"own", r"^tax_?name$", r"taxpayer", r"^name$"],
    "tax": [r"^tax_?name$"],
    "acres": [r"^acres_deed$", r"deed.*ac|ac.*deed", r"^acres_poly$", r"acre"],
    "pin": [r"^county_pin$", r"^pin$|^pid$", r"parcel.?(id|no|num)", r"prop.?id", r"pin|pid"],
    "addr": [r"site.*add|prop.*add|phys.*add|^address$", r"situs"],
    "co": [r"^co_name$", r"^county$|^county_?name$"],
}
keymap = None

def find(keys, pats):
    for p in pats:
        for k in keys:
            if re.search(p, k, re.I):
                return k
    return None

def rnd(c):
    return [round(c[0], 6), round(c[1], 6)] if isinstance(c[0], (int, float)) else [rnd(x) for x in c]

n = 0
for line in sys.stdin:
    line = line.strip().lstrip("\x1e")
    if not line:
        continue
    try:
        f = json.loads(line)
    except ValueError:
        continue
    g = f.get("geometry")
    if not g or "Polygon" not in g.get("type", ""):
        continue
    p = f.get("properties") or {}
    if keymap is None:
        keys = list(p.keys())
        keymap = {name: find(keys, pats) for name, pats in PATS.items()}
        low = {k.lower(): k for k in keys}
        keymap["num"], keymap["st"], keymap["typ"] = low.get("anumber"), low.get("st_name"), low.get("st_pos_typ")
        print("slim.py columns:", keymap, file=sys.stderr)
    def val(name):
        k = keymap.get(name)
        v = p.get(k) if k else None
        return "" if v is None else str(v).strip()
    out = {}
    owner = val("owner") or val("tax")
    if owner:
        out["owner_name"] = owner[:80]
    try:
        ac = float(val("acres") or 0)
        if ac > 0:
            out["acres_deed"] = round(ac, 1)
    except ValueError:
        pass
    if val("pin"):
        out["county_pin"] = val("pin")
    addr = val("addr") or " ".join(x for x in (val("num") if val("num") not in ("0", "") else "", val("st"), val("typ")) if x)
    if addr:
        out["st_name"] = addr[:60]
    co = val("co") or county
    if co:
        out["co_name"] = co
    sys.stdout.write(json.dumps({"type": "Feature", "properties": out, "geometry": {"type": g["type"], "coordinates": rnd(g["coordinates"])}}, separators=(",", ":")) + "\n")
    n += 1
print(f"slim.py wrote {n} parcels", file=sys.stderr)
