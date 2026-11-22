"""Prüft den PDF-Parser gegen GAEB-Dateien desselben LVs (GAEB = Referenz)
und prüft die Wiederholbarkeit (zweimal parsen -> gleiche Prüfsumme)."""
import sys
from pathlib import Path
from lv_parser import parse, fingerprint

D = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")

PAIRS = [
    ("LV-Ausdruck-[PROJEKT_004].pdf", "GAEB-[PROJEKT_004].X83"),
    ("Leistungsverzeichnis_leer.pdf", "[NUMMER_001]_leer.X83"),
    ("Abgabe LV.pdf", "StBALV23040.D86"),
    ("HEM2301-2_Gesamt-LV.pdf", "8209.003_Leistungsverzeichnis_leer.X83"),
    ("Angebot AN24-0305.pdf", "Angebot AN24-0305.D84"),
    ("Leistungsverzeichnis.pdf", "Angebot AN24-0305.D84"),
]


def key(oz):
    parts = [p.lstrip("0") or "0" for p in str(oz).strip(".").split(".") if p != ""]
    return ".".join(parts)


def close(a, b, tol=0.005):
    if a is None or b is None or a != a or b != b:
        return None
    return abs(a - b) <= tol * max(1, abs(b))


rows = []
for pdf, ref in PAIRS:
    if not (D / pdf).exists() or not (D / ref).exists():
        continue
    p = parse(D / pdf)
    r = parse(D / ref)
    p = p[p.typ == "Position"].copy()
    r = r[r.typ == "Position"].copy()
    p["k"] = p.oz.map(key)
    r["k"] = r.oz.map(key)
    P = {k: g.iloc[0] for k, g in p.groupby("k")}
    R = {k: g.iloc[0] for k, g in r.groupby("k")}
    found = [k for k in R if k in P]
    qty_ok = sum(1 for k in found if close(P[k].menge, R[k].menge))
    unit_ok = sum(1 for k in found if (P[k].einheit or "") == (R[k].einheit or "") or not R[k].einheit)
    price_pairs = [k for k in found if R[k].ep == R[k].ep and R[k].ep is not None and P[k].ep is not None]
    ep_ok = sum(1 for k in price_pairs if close(P[k].ep, R[k].ep))
    extra = [k for k in P if k not in R]
    rows.append((pdf, ref, len(R), len(found), qty_ok, unit_ok, len(price_pairs), ep_ok, len(extra)))
    print(f"\n{pdf}  vs  {ref}")
    print(f"  Positionen Referenz {len(R)} | im PDF gefunden {len(found)} | Menge gleich {qty_ok} | Einheit gleich {unit_ok}"
          f" | EP verglichen {len(price_pairs)}, gleich {ep_ok} | nur im PDF {len(extra)}")
    miss = [k for k in R if k not in P][:5]
    if miss:
        print("  fehlt im PDF z. B.:", miss)
    if extra[:5]:
        print("  nur im PDF z. B.:", extra[:5])
    bad = [(k, P[k].menge, P[k].einheit, R[k].menge, R[k].einheit) for k in found
           if not close(P[k].menge, R[k].menge) or ((P[k].einheit or "") != (R[k].einheit or "") and R[k].einheit)][:5]
    for b in bad:
        print("  Abweichung OZ %s: PDF %s %s | Referenz %s %s" % b)

print("\nWiederholbarkeit (zweimal parsen):")
for f in sorted(D.iterdir()):
    if f.suffix.lower() in (".pdf", ".x83", ".d83", ".d84", ".d86"):
        a, b = fingerprint(parse(f)), fingerprint(parse(f))
        if a != b:
            print("  UNTERSCHIED:", f.name)
print("  fertig – alle Dateien geprüft")
