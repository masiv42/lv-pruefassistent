"""
skeptiker_s2.py - Belegprüfung am Original für die 31 Funde aus B1p3 (Team, 22.11.2026, F2, Lücke L57).

Prüft ohne parse() am PDF-Seitentext, ob jeder Textbeleg wörtlich im Block der eigenen Position steht (von der OZ-Zeile bis
zur letzten Mengenzeile, dazu Unterbeschreibungen) und ob jeder Feldwert an der Mengenzeile steht. parse() liefert nur die
Liste der zu prüfenden Funde. Nur bestandene Einträge kommen in data/qa/s2_ergebnis.json; nicht bestandene werden als
Fehlalarm gemeldet. Bestehende Einträge bleiben unverändert, außer ein Ziel-Fund hat seit B1p3 andere Belege.

Aufruf aus der Projektwurzel (uv-Befehl siehe AGENTS.md):
  python src/skeptiker_s2.py data/raw               nur prüfen, schreibt nichts
  python src/skeptiker_s2.py data/raw --schreiben   bestandene Einträge ergänzen
  python src/skeptiker_s2.py data/raw --alle [--schreiben] [--bericht ziel.json]
      S3 (L60): alle noch nicht bestätigten Funde in GAEB XML, GAEB 90 und PDF, Reihenfolge Stufe 1 (zuerst Nr. 1, 2), 2, 3, 4
Exit-Code 0 = alle Ziel-Funde bestanden.
"""
import argparse
import json
import os
import re
import sys
import tempfile
from collections import Counter
from pathlib import Path

import pdfplumber
from lxml import etree

ROOT = Path(__file__).resolve().parent.parent
S2 = ROOT / "data" / "qa" / "s2_ergebnis.json"
BESTANDEN = "Beleg im Original gefunden"
NICHT_BESTANDEN = "Beleg nicht im Original"
STICHPROBE = "S2 B1p3 automatisch (src/skeptiker_s2.py, PDF-Seitentext, ohne parse(), 22.11.2026)"
METHODE = "PDF-Seitentext im Block der Position, ohne parse(); nur Leerraum zusammengefasst"
STICHPROBE_S3 = "S3 automatisch (src/skeptiker_s2.py --alle, Original ohne parse(), 22.11.2026)"
METHODE_S3 = "Rohdatei im Block der Position (GAEB XML: Item, GAEB 90: Sätze 21–30, PDF: Seitentext), ohne parse()"
ZIELE = {
    "LV_00_Roh_und_Erdauarbeiten.pdf": ["16|3.1.280", "3|1.4.7"],
    "LV_04_Porenbetonfassade.pdf": ["6|9.1.10", "6|9.1.20", "6|9.1.30"],
    "LV_08_Fliesen_und_Natursteinarbeiten.pdf": ["16|13.2.8"],
    "LV_09_Porenbetondach.pdf": ["10|9.2.0", "6|9.2.0", "6|9.2.1", "6|9.2.2", "6|9.2.3"],
    "LV_13_ELT.pdf": ["3|2.6.1", "3|2.6.2", "3|2.6.3", "3|2.6.4", "3|2.6.5", "3|2.6.6", "3|2.6.7", "3|2.6.8", "7|1.2.6",
                      "7|2.6.1", "7|2.6.2", "7|2.6.3", "7|2.6.4", "7|2.6.5", "7|2.6.6", "7|2.6.7", "7|2.6.8", "7|2.7.9",
                      "8|2.7.19"],
    "HEM2301-2_Gesamt-LV.pdf": ["7|6.4.1"],
}
ZAHL = r"(?:\d{1,3}(?:\.\d{3})+|\d+)(?:,\d{1,4})?"
PREISFELD = r"(?:\.{3,}|…+|EP\.*|GP\.*|Nur\s*Einh\.?\s*-?\s*Pr\.?|\d{1,3}(?:\.\d{3})*,\d{2,3})"
MENGE_RE = re.compile(r"^\s*(?P<menge>" + ZAHL + r")(?:\s+(?P<einheit>[^\s.]{1,10}\.?))?\s+" + PREISFELD + r"(?:\s+" + PREISFELD + r")*\s*$")
MENGE_OHNE_PREIS_RE = re.compile(r"^\s*(?P<menge>\d[\d.]*,\d{3})\s+(?P<einheit>[A-Za-zÄÖÜäöüß²³][\wÄÖÜäöüß²³/]{0,7}\.?)\s*$")
OZ_ZEILE_RE = re.compile(r"^(?P<ind>\s*)(?P<oz>(?:\d{1,4}[a-z]?(?:\.{1,2}\d{1,4}){1,5}|(?:\.\d{1,4}){1,5})\.?)(?=\s|$)")
RAUSCHEN_RE = re.compile(r"Übertrag|Seite\s*:?\s*\d|Druckdatum|Alle Einzelbeträge|Fortsetzung auf nächster Seite|Netto\s*:|in EUR\s*$")
UNTER_START_RE = re.compile(r"^Unterbeschreibung \d+:$")
UNTER_ENDE_RE = re.compile(r"^(?:Gemäß\b.*\b\d+:|Leitbeschreibung:|\*\*\*.*)$")


def zusammen(text):
    """Nur Folgen von Leerzeichen und Zeilenumbrüchen werden zu einem Leerzeichen (Regel S2)."""
    return re.sub(r"\s+", " ", text or "").strip()


def mengenzeile(zeile):
    """(Menge als Text, Einheit oder „“) oder None."""
    m = MENGE_RE.match(zeile) or MENGE_OHNE_PREIS_RE.match(zeile)
    return (m.group("menge"), m.group("einheit") or "") if m else None


def seitenzeilen(pfad):
    """[(Seite, Zeile)] aus dem PDF, ohne Zeilen, die sich auf vielen Seiten wiederholen (Kopf und Fuß)."""
    seiten = []
    with pdfplumber.open(str(pfad)) as pdf:
        for p in pdf.pages:
            fp = p.filter(lambda o: not (o.get("object_type") == "char" and o.get("text", "").isspace()))
            seiten.append([z.rstrip() for z in (fp.extract_text(layout=True, x_tolerance=1.5) or "").split("\n") if z.strip()])
    return ohne_kopf_fuss(seiten)


def ohne_kopf_fuss(seiten):
    schluessel = lambda z: re.sub(r"\d", "#", zusammen(z))
    geschuetzt = lambda z: mengenzeile(z) is not None or OZ_ZEILE_RE.match(z) is not None
    zahl = Counter(k for s in seiten for k in {schluessel(z) for z in s if not geschuetzt(z)})
    grenze = max(3, 0.4 * len(seiten)) if len(seiten) >= 4 else max(len(seiten), 2)
    wdh = {k for k, n in zahl.items() if n >= grenze}
    return [(i, z) for i, s in enumerate(seiten, 1) for z in s
            if geschuetzt(z) or not (schluessel(z) in wdh or RAUSCHEN_RE.search(z))]


def block(zeilen, oz, seite):
    """Block der Position im Original: {text, menge, einheit, seiten} oder None. `oz` wie gedruckt, ohne Schlusspunkt."""
    muster = re.compile(r"^(?P<ind>\s*)" + re.escape(oz) + r"\.?(?=\s|$)")
    start = next((i for i, (s, z) in enumerate(zeilen) if s >= (seite or 1) and muster.match(z)), None)
    if start is None:
        return None
    m = muster.match(zeilen[start][1])
    einzug = len(m.group("ind"))
    gesehen, teile = {zusammen(z) for _, z in zeilen[:start + 1]}, []
    for s, z in zeilen[start + 1:]:
        # Kopfzeile, die auf der Folgeseite wiederkommt („01.01 Bereich …“): weder Text noch Ende der Position
        if len(z) - len(z.lstrip()) <= einzug + 2 and zusammen(z) in gesehen and mengenzeile(z) is None:
            continue
        o = OZ_ZEILE_RE.match(z)
        if o and abs(len(o.group("ind")) - einzug) <= 2 and mengenzeile(z) is None:
            break
        teile.append((s, z))
    kopf = zeilen[start][1][m.end():].strip()
    if mengenzeile(kopf):                      # Angebots-Ausdruck: Menge in der OZ-Zeile, eingerückter Text = Kurztext
        text = []
        for _, z in teile:
            if len(z) - len(z.lstrip()) <= einzug + 2:
                break
            text.append(z)
        menge, einheit = mengenzeile(kopf)
        return {"text": zusammen(" ".join(text)), "menge": menge, "einheit": einheit,
                "seiten": [zeilen[start][0]]}
    letzte = max((i for i, (_, z) in enumerate(teile) if mengenzeile(z)), default=None)
    if letzte is None:
        return None
    menge, einheit = mengenzeile(teile[letzte][1])
    text = [zeilen[start][1][m.end():]] + [z for _, z in teile[:letzte]]
    in_unter = False
    for _, z in teile[letzte + 1:]:
        t = z.strip()
        if UNTER_START_RE.match(t):
            in_unter = True
        elif UNTER_ENDE_RE.match(t):
            in_unter = False
        elif in_unter:
            text.append(t)
    return {"text": zusammen(" ".join(text)), "menge": menge, "einheit": einheit,
            "seiten": sorted({zeilen[start][0]} | {s for s, _ in teile[:letzte + 1]})}


def _zahl(wert):
    """Menge als Zahl; Text in deutscher Schreibweise („1.234,500“), sonst unverändert."""
    if wert is None or isinstance(wert, (int, float)):
        return wert
    try:
        return float(wert.replace(".", "").replace(",", "."))
    except ValueError:
        return None


def _bewerte(fund, bloecke, fehlt, fundstelle):
    """Prüft Textbelege und Feldwerte gegen die Blöcke [(OZ, Block)]; Ergebnis wie pruefe_fund."""
    for oz, b in bloecke:
        fehlt += [f"OZ {oz}: Beleg „{t}“" for t in fund["belege"] if zusammen(t) not in b["text"]]
    oze = {p["oz"] for p in fund["positionen"]}
    for fb in fund.get("feldbelege") or []:
        t = fb["text"]
        if t.startswith("OZ: "):
            if t[4:] not in oze:
                fehlt.append(t)
        elif t.startswith("Einheit: "):
            soll = "" if t == "Einheit: (leer)" else t[9:]
            fehlt += [f"OZ {oz}: {t}, im Original „{b['einheit']}“" for oz, b in bloecke if b["einheit"] != soll]
        elif t.startswith("Menge: "):
            w = t[7:]
            if w != "(leer)" and not re.fullmatch(r"\d[\d.]*(?:,\d+)?", w):
                fehlt.append(f"Feldwert nicht prüfbar: {t}")
                continue
            soll = None if w == "(leer)" else _zahl(w)
            fehlt += [f"OZ {oz}: {t}, im Original „{b['menge']}“" for oz, b in bloecke if _zahl(b["menge"]) != soll]
        elif t.startswith("<Provis>"):
            fehlt += [f"OZ {oz}: Kennzeichen {t} fehlt" for oz, b in bloecke if t not in b.get("kennzeichen", ())]
        else:
            fehlt.append(f"Feldwert nicht prüfbar: {t}")
    return {"id": fund["id"], "ergebnis": BESTANDEN if not fehlt else NICHT_BESTANDEN, "fundstelle": fundstelle, "fehlt": fehlt}


def pruefe_fund(fund, zeilen):
    """Ergebnis eines PDF-Funds gegen die Originalzeilen: {id, ergebnis, fundstelle, fehlt}."""
    fehlt, seiten, bloecke = [], set(), []
    for p in fund["positionen"]:
        b = block(zeilen, p["oz"].rstrip("."), p.get("seite"))
        if b is None:
            fehlt.append(f"Position {p['oz']} nicht gefunden")
            continue
        bloecke.append((p["oz"], b))
        seiten |= set(b["seiten"])
    return _bewerte(fund, bloecke, fehlt, "S. " + ", ".join(str(s) for s in sorted(seiten)))


def oz_schluessel(oz):
    """OZ ohne führende Nullen je Ebene, ohne leere Ebenen (eigene Fassung, unabhängig von der Prüflogik)."""
    return ".".join(x.lstrip("0") or "0" for x in str(oz).strip(".").split(".") if x != "")


def _xml_text(el, ln):
    """Text eines Elements wie im Original; nur <p> und <br> trennen, Bilder zählen nicht."""
    stuecke = []
    for e in el.iter():
        if not isinstance(e.tag, str) or ln(e).lower() == "image":
            if e is not el and e.tail:
                stuecke.append(e.tail)
            continue
        if ln(e) in ("p", "br"):
            stuecke.append(" ")
        if e.text and ln(e.getparent()).lower() != "image":
            stuecke.append(e.text)
        if e.tail and e is not el:
            stuecke.append(e.tail)
    return "".join(stuecke)


def original_xml(pfad):
    """{OZ-Schlüssel: Block} direkt aus der Rohdatei: Description und SubDescr, QU, Qty, Provis."""
    ln = lambda e: etree.QName(e).localname if isinstance(e.tag, str) else ""
    aus = {}
    for it in etree.parse(str(pfad), etree.XMLParser(huge_tree=True, recover=True)).getroot().iter():
        if ln(it) != "Item":
            continue
        teile = [e.get("RNoPart", "") for e in it.iterancestors() if ln(e) == "BoQCtgy"][::-1]
        kind = {ln(c): c for c in it}
        texte = [_xml_text(c, ln) for c in it if ln(c) in ("Description", "SubDescr")]
        menge = (kind["Qty"].text or "").strip() if "Qty" in kind else ""
        provis = kind.get("Provis")
        schluessel = oz_schluessel(".".join(teile + [it.get("RNoPart", "") + (it.get("RNoIndex") or "")]))
        aus[schluessel] = {"text": zusammen(" ".join(texte)), "menge": float(menge) if menge else None,
                           "einheit": ((kind["QU"].text or "").strip() if "QU" in kind else ""),
                           "kennzeichen": {f"<Provis>{(provis.text or '').strip()}</Provis>"} if provis is not None else set(),
                           "stelle": f"Item {it.get('ID', '')}"}
    return aus


def original_gaeb90(pfad):
    """{OZ ohne Trennzeichen: Block}: nur die Sätze 21–30 einer Position (Text Satz 25/26, Menge und Einheit Satz 21)."""
    aus, cur = {}, None
    im_block = {str(n) for n in range(22, 31)}
    for nr, z in enumerate(pfad.read_bytes().decode("cp850").replace("\r\n", "\n").split("\n"), 1):
        sa = z[:2]
        if sa == "21":
            m = z[23:34].strip()
            cur = {"25": [], "26": [], "menge": int(m) / 1000 if m.isdigit() else None, "einheit": z[34:38].strip(),
                   "stelle": f"Satz 21 Z. {nr}"}
            aus[re.sub(r"\s", "", z[2:11])] = cur
        elif sa in im_block and cur is not None:
            if sa in ("25", "26"):
                cur[sa].append(z[2:72].strip())
        else:
            cur = None
    for b in aus.values():
        b["text"] = zusammen(zusammen(" ".join(b.pop("25"))) + " " + zusammen(" ".join(b.pop("26"))))
    return aus


def lies_original(pfad):
    """(Art, Daten) der Rohdatei, ohne parse()."""
    endung = Path(pfad).suffix.lower()
    if endung.startswith(".x"):
        return "xml", original_xml(Path(pfad))
    if endung.startswith(".d"):
        return "g90", original_gaeb90(Path(pfad))
    return "pdf", seitenzeilen(pfad)


def pruefe_fund_format(fund, original):
    """Wie pruefe_fund, für alle Formate; `original` aus lies_original()."""
    art, daten = original
    if art == "pdf":
        return pruefe_fund(fund, daten)
    fehlt, bloecke, stellen = [], [], []
    for p in fund["positionen"]:
        b = daten.get(oz_schluessel(p["oz"]) if art == "xml" else p["oz"].replace(".", ""))
        if b is None:
            fehlt.append(f"Position {p['oz']} nicht gefunden")
            continue
        bloecke.append((p["oz"], b))
        stellen.append(b["stelle"])
    return _bewerte(fund, bloecke, fehlt, ", ".join(stellen))


def ursache(fund, r):
    """Einordnung eines nicht bestandenen Funds für den Bericht."""
    x = " ".join(r["fehlt"])
    if "nicht gefunden" in x:
        return "Position nicht gefunden"
    if "Feldwert nicht prüfbar" in x:
        return "Feldwert nicht prüfbar"
    if "Beleg" not in x:
        return "Feldwert weicht ab"
    return "Beleg nicht wörtlich im Block"


def eintrag(fund, erg, stichprobe=STICHPROBE, methode=METHODE):
    aus = {"id": fund["id"], "stichprobe": stichprobe, "fundstelle": erg["fundstelle"],
           "belege": [{"text": t, "gefunden": True, "methode": methode} for t in fund["belege"]],
           "ergebnis": BESTANDEN}
    if "feldbelege" in fund:                   # Nr. 1/2 haben kein Feld „feldbelege“; der Eintrag bildet den Fund genau ab
        aus["feldbelege"] = [{"art": b["art"], "text": b["text"], "gefunden": True} for b in fund["feldbelege"]]
    return aus


def ergaenze(doc, funde, ergebnisse, stichprobe=STICHPROBE, methode=METHODE, stand_schluessel="stand_b1p3",
             stand_text="22.11.2026 B1p3 (Sitzung B4, src/skeptiker_s2.py)"):
    """Neues Dokument: bestandene Funde ergänzt; ein vorhandener Eintrag wird nur ersetzt, wenn sich seine Belege geändert haben.
    Gibt (dokument, neu, ersetzt) zurück."""
    aus = json.loads(json.dumps(doc, ensure_ascii=False))
    je_id = {e["id"]: i for i, e in enumerate(aus["funde"])}
    f = {x["id"]: x for x in funde}
    neu = ersetzt = 0
    for r in ergebnisse:
        if r["ergebnis"] != BESTANDEN:
            continue
        e = eintrag(f[r["id"]], r, stichprobe, methode)
        if r["id"] not in je_id:
            aus["funde"].append(e)
            neu += 1
        elif ([b["text"] for b in aus["funde"][je_id[r["id"]]]["belege"]] != [b["text"] for b in e["belege"]]
              or [b["text"] for b in aus["funde"][je_id[r["id"]]].get("feldbelege", [])] != [b["text"] for b in e.get("feldbelege", [])]):
            aus["funde"][je_id[r["id"]]] = e
            ersetzt += 1
    if neu or ersetzt:
        aus["stand"] = "2026-11-22"          # die App zeigt diesen Stand bei „Beleg am Original geprüft“
        aus[stand_schluessel] = stand_text
    return aus, neu, ersetzt


def schreibe(doc, ziel):
    ziel = Path(ziel)
    if (ROOT / "data" / "raw").resolve() in [ziel.resolve(), *ziel.resolve().parents]:
        raise ValueError("Nie in data/raw schreiben (E11)")
    fd, tmp = tempfile.mkstemp(dir=ziel.parent, suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as h:
        h.write(json.dumps(doc, ensure_ascii=False, indent=2) + "\n")
    os.replace(tmp, ziel)


def ziel_ids():
    return [f"{e.split('|')[0]}|{d}|{e.split('|')[1]}" for d, liste in ZIELE.items() for e in liste]


def lade_funde(d):
    """Nur die Liste der zu prüfenden Funde kommt aus der Prüfung; die Belegprüfung selbst nutzt parse() nicht."""
    from lv_parser import parse
    from pruefung_formal import alle_pruefungen
    aus = []
    for datei in ZIELE:
        je = {f["id"]: f for f in alle_pruefungen(parse(d / datei), d / datei)}
        aus += [je[i] for i in ziel_ids() if i.split("|")[1] == datei and i in je]
    return aus


def reihenfolge(f):
    """Stufe 1 (zuerst Nr. 1 und 2), dann 2, 3, 4; innerhalb fest nach Prüfung und Fund-ID (E14)."""
    return f["stufe"], 0 if f["pruefung"] in (1, 2) else 1, f["pruefung"], f["id"]


def lade_offene(d):
    """Alle Funde, die die App als „noch nicht geprüft“ zeigt, in der Reihenfolge des Teams."""
    from bericht import beleg_pruefung, lade_s2
    from lv_parser import parse
    from pruefung_formal import alle_pruefungen
    s2 = lade_s2()[0]
    aus = []
    for p in sorted(d.iterdir(), key=lambda x: x.name):
        if p.name == ".DS_Store" or p.suffix.lower() == ".docx":
            continue
        aus += [f for f in alle_pruefungen(parse(p), p) if beleg_pruefung(f, s2) == "ungeprüft"]
    return sorted(aus, key=reihenfolge)


def lauf_alle(a):
    funde = lade_offene(a.raw)
    original, ergebnisse = {}, []
    for f in funde:
        datei = f["positionen"][0]["datei"]
        if datei not in original:
            original[datei] = lies_original(a.raw / datei)
        ergebnisse.append(pruefe_fund_format(f, original[datei]))
    je = {f["id"]: f for f in funde}
    stufen = Counter((je[r["id"]]["stufe"], r["ergebnis"] == BESTANDEN) for r in ergebnisse)
    for s in (1, 2, 3, 4):
        print(f"Stufe {s}: {stufen[(s, True)]} bestanden, {stufen[(s, False)]} nicht bestanden")
    gut = sum(r["ergebnis"] == BESTANDEN for r in ergebnisse)
    print(f"{gut} von {len(funde)} offenen Funden bestanden")
    fehl = [dict(r, stufe=je[r["id"]]["stufe"], pruefung=je[r["id"]]["pruefung"], ursache=ursache(je[r["id"]], r))
            for r in ergebnisse if r["ergebnis"] != BESTANDEN]
    print("Nicht bestanden je Ursache:", dict(Counter(x["ursache"] for x in fehl)))
    if a.bericht:
        ziel = Path(a.bericht).resolve()
        if ziel.is_relative_to((ROOT / "data").resolve()):
            sys.exit("--bericht nie in data/ (E12 (4))")
        ziel.write_text(json.dumps(fehl, ensure_ascii=False, indent=1), encoding="utf-8")
    if a.schreiben:
        doc = json.loads(S2.read_text(encoding="utf-8"))
        neu_doc, neu, ersetzt = ergaenze(doc, funde, ergebnisse, STICHPROBE_S3, METHODE_S3, "stand_s3",
                                         "22.11.2026 S3 (Sitzung B4, src/skeptiker_s2.py --alle)")
        if neu or ersetzt:
            schreibe(neu_doc, S2)
        print(f"s2_ergebnis.json: {neu} ergänzt, {ersetzt} ersetzt, {len(neu_doc['funde'])} Einträge")
    return 0 if not fehl else 1


def main():
    ap = argparse.ArgumentParser(description="Belegprüfung am Original für die Funde aus B1p3")
    ap.add_argument("raw", type=Path)
    ap.add_argument("--schreiben", action="store_true", help="bestandene Einträge in data/qa/s2_ergebnis.json ergänzen")
    ap.add_argument("--alle", action="store_true", help="S3: alle noch nicht bestätigten Funde, alle Formate")
    ap.add_argument("--bericht", help="nicht bestandene Funde als JSON (nie in data/)")
    a = ap.parse_args()
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    if a.alle:
        return lauf_alle(a)
    funde = lade_funde(a.raw)
    fehlende = sorted(set(ziel_ids()) - {f["id"] for f in funde})
    original, ergebnisse = {}, []
    for f in funde:
        datei = f["positionen"][0]["datei"]
        original.setdefault(datei, seitenzeilen(a.raw / datei))
        ergebnisse.append(pruefe_fund(f, original[datei]))
    gut = sum(r["ergebnis"] == BESTANDEN for r in ergebnisse)
    print(f"{gut} von {len(ziel_ids())} Ziel-Funden bestanden")
    for i in fehlende:
        print(f"FEHLALARM {i}: Fund gibt es nicht mehr")
    for r in ergebnisse:
        if r["ergebnis"] != BESTANDEN:
            print(f"FEHLALARM {r['id']} ({r['fundstelle']}): " + "; ".join(x[:110] for x in r["fehlt"]))
    if a.schreiben:
        doc = json.loads(S2.read_text(encoding="utf-8"))
        neu_doc, neu, ersetzt = ergaenze(doc, funde, ergebnisse)
        if neu or ersetzt:
            schreibe(neu_doc, S2)
        print(f"s2_ergebnis.json: {neu} ergänzt, {ersetzt} mit neuen Belegen ersetzt, {len(neu_doc['funde'])} Einträge")
    return 0 if gut == len(ziel_ids()) and not fehlende else 1


if __name__ == "__main__":
    sys.exit(main())
