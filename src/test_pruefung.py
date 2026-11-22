"""
test_pruefung.py - Tests für src/pruefung_widerspruch.py (Prüfung Nr. 1 und 2).

Erwartungen aus docs/acceptance.md T2 und T3, Fund-Format aus docs/data-contracts.md.
Aufruf aus der Projektwurzel (uv-Befehl siehe AGENTS.md):
  python src/test_pruefung.py data/raw            # Stufe 1 (5 Testdateien)
  python src/test_pruefung.py data/raw --stufe2   # zusätzlich Stufe 2 (32 Dateien)
Exit-Code 0 = alle Tests bestanden.
"""
import ast
import json
import sys
from pathlib import Path

import pandas as pd

import re

import pdfplumber

from lv_parser import parse, _pdf_lines
from heuristik_widerspruch_v0 import DATEIEN
from pruefung_widerspruch import (
    normalisiere_oz, normalisiere_leerzeichen, beleg_im_text, pruefe, PATTERNS, werte,
    PdfSeiten, SEITEN_FOLGE,
)

D = Path(sys.argv[1]) if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else Path("data/raw")
STUFE2 = "--stufe2" in sys.argv

STUFE1_DATEIEN = [
    "8209.003_Leistungsverzeichnis_leer.X83",
    "[NUMMER_001]_leer.X83",
    "Leistungsverzeichnis.pdf",
    "LV_00_Roh_und_Erdauarbeiten.pdf",
    "501-24-01_GAEB-XML_sas.x83",
]
GAEB = "501-24-01_GAEB-XML_sas.x83"

# T2 Positiv: (datei, oz) -> (prüfung, Belege, die in einem Beleg des Funds stehen müssen)
# "139,7 x 2,6 mm" ist ausgenommen (Team, Chat 20.11.2026).
POSITIV = {
    ("8209.003_Leistungsverzeichnis_leer.X83", "05.01.4"): (1, ["Edelstahl-Rohr DN 125", "Edelstahlrohr DN 100"]),
    ("8209.003_Leistungsverzeichnis_leer.X83", "05.01.46"): (1, ["Losflansch DN 125, PN 10", "Losflansch, DN 100, PN 10"]),
    ("[NUMMER_001]_leer.X83", "3.3.3"): (2, ["Rückenstütze C20/25", "Normalbeton C25/30 (LP) XF2"]),
    ("LV_00_Roh_und_Erdauarbeiten.pdf", "3.1.180"): (2, ["Stützwand,Stb,C30/37", "Beton: C25/30"]),
    ("Leistungsverzeichnis.pdf", "3.2.60"): (1, ["Muffenschutz aus Gummi DN 300", "Muffenschutz aus Gummi DN 500"]),
}
# T2 Negativ
NEGATIV = [(GAEB, "02.05.0005"), (GAEB, "02.05.0007"), (GAEB, "02.05.0009")]
# T2 Stufe 1: 8 ungeprüfte Kandidaten (Status "offen").
# B1p (Team, 21.11.2026, F3): Leistungsverzeichnis.pdf 2.1.410 und 4.1.200 entfallen – „bis DN 300“ ist die
# umbrochene zweite Kurztext-Zeile (am Original S. 15 in der Kurztext-Schrift F1; Angebot AN24-0305.pdf druckt
# dieselben zwei Zeilen als Kurztext); neu 5.3.210 – der Kurztext endet erst mit „bis DN 250“ (zweite Zeile in F1),
# der Langtext nennt „bis DN 300“.
UNGEPRUEFT = [
    ("[NUMMER_001]_leer.X83", "1.1.4"), ("[NUMMER_001]_leer.X83", "3.3.4"), ("[NUMMER_001]_leer.X83", "5.3.3"),
    ("Leistungsverzeichnis.pdf", "5.3.100"), ("Leistungsverzeichnis.pdf", "5.3.210"),
    ("LV_00_Roh_und_Erdauarbeiten.pdf", "2.3.90"), (GAEB, "02.03.0023"), (GAEB, "03.03.0019"),
]
FELDER = ["id", "pruefung", "kategorie", "titel", "positionen", "belege", "begruendung",
          "stufe", "stufe_begruendung", "prioritaet_in_stufe", "rueckfrage", "status"]
KATEGORIEN = {"nachweisbarer Fehler", "möglicher Widerspruch", "Unklarheit", "Risikohinweis"}

ergebnisse = []


def check(name, ok, detail=""):
    ergebnisse.append(ok)
    print(f"{'OK    ' if ok else 'FEHLER'} {name}" + (f" – {detail}" if detail and not ok else ""))


def key_aus_validate_parser():
    """key() aus src/validate_parser.py laden, ohne das Modul auszuführen
    (es startet beim Import den ganzen Prüflauf)."""
    src = (Path(__file__).parent / "validate_parser.py").read_text(encoding="utf-8")
    fn = next(n for n in ast.parse(src).body if isinstance(n, ast.FunctionDef) and n.name == "key")
    ns = {}
    exec(compile(ast.Module(body=[fn], type_ignores=[]), "validate_parser.py", "exec"), ns)
    return ns["key"]


def paare(funde):
    return {(p["datei"], p["oz"]) for f in funde for p in f["positionen"]}


def pruefe_dateien(namen, cache):
    funde = []
    for n in namen:
        if n not in cache:
            cache[n] = parse(D / n)
        funde += pruefe(cache[n], D / n)
    return funde


def pdf_seiten_checks(stufe, funde):
    """P1b: Jeder Beleg eines PDF-Funds steht zusammenhängend auf EINER Seite.
    Gegenprobe mit einer anderen Extraktion als im Prüfmodul (pdfplumber-Standardtext,
    ohne Leerzeichen verglichen, weil dieser Text Leerzeichen einfügt oder weglässt)."""
    ohne = lambda s: re.sub(r"\s+", "", s or "")
    fehlt, seiten = [], {}
    for f in funde:
        p = f["positionen"][0]
        if not p["datei"].lower().endswith(".pdf"):
            continue
        if p["datei"] not in seiten:
            with pdfplumber.open(str(D / p["datei"])) as pdf:
                seiten[p["datei"]] = [ohne(s.extract_text()) for s in pdf.pages]
        bereich = seiten[p["datei"]][p["seite"] - 1:p["seite"] + SEITEN_FOLGE]
        for b in f["belege"]:
            if not any(ohne(b) in s for s in bereich):
                fehlt.append((f["id"], b))
    check(f"{stufe}: PDF-Belege je auf einer Seite des Originals (Gegenprobe)", not fehlt, str(fehlt[:3]))


def allgemeine_checks(stufe, funde, cache):
    ids = [f["id"] for f in funde]
    check(f"{stufe}: Fund-IDs eindeutig", len(ids) == len(set(ids)))
    check(f"{stufe}: Felder nach Datenvertrag", all(list(f) == FELDER for f in funde))
    check(f"{stufe}: Kategorie aus R6", all(f["kategorie"] in KATEGORIEN for f in funde))
    check(f"{stufe}: Status 'offen'", all(f["status"] == "offen" for f in funde))
    check(f"{stufe}: ID = Prüfung|Datei|normalisierte OZ",
          all(f["id"] == f"{f['pruefung']}|{f['positionen'][0]['datei']}|{normalisiere_oz(f['positionen'][0]['oz'])}"
              for f in funde))
    check(f"{stufe}: JSON-fähig", bool(json.dumps(funde, ensure_ascii=False)))
    # R5: jeder Beleg wörtlich im Kurz- oder Langtext der Position
    fehlt = []
    for f in funde:
        for p in f["positionen"]:
            df = cache[p["datei"]]
            r = df[(df.typ == "Position") & (df.oz == p["oz"])].iloc[0]
            for b in f["belege"]:
                if not beleg_im_text(b, r.kurztext if isinstance(r.kurztext, str) else "",
                                     r.langtext if isinstance(r.langtext, str) else ""):
                    fehlt.append((f["id"], b))
    check(f"{stufe}: jeder Beleg wörtlich in der Position (R5)", not fehlt, str(fehlt[:3]))
    check(f"{stufe}: jeder Fund hat Beleg aus Kurz- und Langtext", all(len(f["belege"]) >= 2 for f in funde))


def test_oz(cache):
    key = key_aus_validate_parser()
    abw, n = [], 0
    for name in STUFE1_DATEIEN:
        for oz in cache[name].oz.dropna():
            n += 1
            if normalisiere_oz(oz) != key(oz):
                abw.append((name, oz, normalisiere_oz(oz), key(oz)))
    check(f"OZ: normalisiere_oz == key() auf allen {n} OZ der 5 Testdateien", n > 0 and not abw, str(abw[:3]))
    beispiele = {"01.01.0001": "1.1.1", "05.01.4": "5.1.4", "10.01.0001": "10.1.1", "3.1.180": "3.1.180"}
    check("OZ: Beispiele aus docs/data-contracts.md",
          all(normalisiere_oz(k) == v for k, v in beispiele.items()))


def test_stufe1(cache):
    funde = pruefe_dateien(STUFE1_DATEIEN, cache)
    p = paare(funde)
    erwartet = set(POSITIV) | set(UNGEPRUEFT)
    check("Stufe 1: 13 Funde (vor B1p 14)", len(funde) == 13, f"{len(funde)} Funde")
    check("Stufe 1: genau 5 Positiv-Tests + 8 ungeprüfte", p == erwartet,
          f"zu viel {sorted(p - erwartet)}, fehlt {sorted(erwartet - p)}")
    for (datei, oz), (nr, zitate) in POSITIV.items():
        f = next((f for f in funde if (datei, oz) in paare([f])), None)
        if f is None:
            check(f"T2 positiv {datei} {oz}", False, "nicht gefunden")
            continue
        fehlt = [z for z in zitate if not any(normalisiere_leerzeichen(z) in normalisiere_leerzeichen(b)
                                               for b in f["belege"])]
        check(f"T2 positiv {datei} {oz}: Prüfung {nr}, möglicher Widerspruch, Belege",
              f["pruefung"] == nr and f["kategorie"] == "möglicher Widerspruch" and not fehlt,
              f"Prüfung {f['pruefung']}, fehlende Zitate {fehlt}, Belege {f['belege']}")
    for datei, oz in NEGATIV:
        check(f"T2 negativ {datei} {oz} nicht gemeldet", (datei, oz) not in p)
    seiten = {(q["datei"], q["oz"]): q["seite"] for f in funde for q in f["positionen"]}
    check("Seite: 3.1.180 S. 29, 3.2.60 S. 30, GAEB ohne Seite",
          seiten[("LV_00_Roh_und_Erdauarbeiten.pdf", "3.1.180")] == 29
          and seiten[("Leistungsverzeichnis.pdf", "3.2.60")] == 30
          and all(v is None for (d, _), v in seiten.items() if not d.endswith(".pdf")))
    allgemeine_checks("Stufe 1", funde, cache)
    pdf_seiten_checks("Stufe 1", funde)
    # Wiederholbarkeit: neu parsen, gleiche Funde
    neu = []
    for n in STUFE1_DATEIEN:
        neu += pruefe(parse(D / n), D / n)
    check("Stufe 1: gleiche Eingabe -> gleiche Funde (neu geparst)",
          json.dumps(neu, ensure_ascii=False) == json.dumps(funde, ensure_ascii=False))
    return funde


def test_platzhalter_und_dubletten():
    texte = ["[NUMMER_001]", "[PERSON_115]", "[P,ERSON_132]", "TE.L0.0009", "TEL00009", "[PERSON_006] rund"]
    check("T3: Platzhalter ergeben keine DN-/Betonwerte",
          all(not werte(p, t) for p in PATTERNS.values() for t in texte))

    def zeile(oz, kurz, lang, datei="test.X83"):
        return {"datei": datei, "format": "GAEB XML", "seite": None, "typ": "Position", "oz": oz,
                "kurztext": kurz, "langtext": lang}
    df = pd.DataFrame([
        zeile("1.1", "[PERSON_115] Rohr [NUMMER_001]", "Rohr TE.L0.0009 [P,ERSON_132] DN 100"),
        zeile("1.2", "Rohr DN 100", "Rohr DN 100, [PERSON_115]"),
    ])
    check("T3: Platzhalter erzeugen keinen Fund", pruefe(df) == [])
    df = pd.DataFrame([
        zeile("05.01.4", "Rohr DN 125", "Rohr DN 100"),
        zeile("5.1.4", "Flansch DN 125", "Flansch DN 100"),
    ])
    f = pruefe(df)
    check("Doppelte OZ (verschiedene Schreibweise) -> ein Fund mit zwei Positionen",
          len(f) == 1 and [p["oz"] for p in f[0]["positionen"]] == ["05.01.4", "5.1.4"]
          and f[0]["id"] == "1|test.X83|5.1.4")
    df = pd.DataFrame([zeile("1", "Schacht DN 1000", "Schacht mit Anschluss DN 150 und DN 200")])
    check("DN-Filter: zwei DN-Werte im Langtext -> kein Fund", pruefe(df) == [])
    df = pd.DataFrame([zeile("1", "Beton C20/25", "Beton:     C25/30")])
    check("Beleg mit Layout-Leerzeichen wird zusammengefasst",
          pruefe(df)[0]["belege"] == ["Beton C20/25", "Beton: C25/30"])


def test_p1b(cache, stufe1):
    """Belege laufen nicht über Seitenwechsel oder weggelassene Ausfülllinien (S2, 21.11.2026)."""
    lv = "Leistungsverzeichnis.pdf"
    f = {x["id"]: x for x in stufe1}
    b_3260 = f[f"1|{lv}|3.2.60"]["belege"]
    check("P1b 3.2.60: kein Beleg über den Seitenwechsel S. 30/31",
          not any("Schrumpfmanschette" in b for b in b_3260), str(b_3260))
    b_53100 = f[f"1|{lv}|5.3.100"]["belege"]
    check("P1b 5.3.100: kein Beleg über Ausfülllinien nach „Fabrikat:“/„Type:“, „DN 150“ belegt",
          not any(re.search(r"Fabrikat:|Typ:|Type:|Hersteller:", b) for b in b_53100)
          and any("DN 150" in b for b in b_53100), str(b_53100))
    # Seitentext im Prüfmodul = gleiche Extraktion wie der Parser: jede Zeile, die der
    # Parser behält, steht im Seitentext derselben Seite
    abw = []
    for n in [x for x in STUFE1_DATEIEN if x.lower().endswith(".pdf")]:
        with pdfplumber.open(str(D / n)) as pdf:
            s = PdfSeiten(pdf)
            for seite, zeile in _pdf_lines(D / n):
                if normalisiere_leerzeichen(zeile) not in s.text(seite):
                    abw.append((n, seite, zeile[:40]))
    check("P1b: Seitentext im Prüfmodul enthält jede Parser-Zeile (gleiche Extraktion)", not abw, str(abw[:3]))
    try:
        pruefe(cache[lv])
        check("P1b: PDF ohne Pfad wird abgelehnt", False, "kein Fehler")
    except ValueError:
        check("P1b: PDF ohne Pfad wird abgelehnt", True)


def test_stufe2(cache, stufe1):
    namen = DATEIEN + sorted(f.name for f in D.iterdir() if f.name.startswith("LV_"))
    check("Stufe 2: 32 Dateien", len(namen) == 32, f"{len(namen)} Dateien")
    funde = pruefe_dateien(namen, cache)
    check("Stufe 2: 14 Funde (vor B1p 16; B1p −1, B1q −1: GAEB-[PROJEKT_004].X83 02.0009 „DN 800/900“)",
          len(funde) == 14, f"{len(funde)} Funde")
    check("Stufe 2: enthält alle Funde aus Stufe 1",
          {f["id"] for f in stufe1} <= {f["id"] for f in funde})
    check("Stufe 2: Negativ-Tests nicht gemeldet", not (set(NEGATIV) & paare(funde)))
    allgemeine_checks("Stufe 2", funde, cache)
    pdf_seiten_checks("Stufe 2", funde)
    neu = sorted(paare(funde) - paare(stufe1))
    print("       zusätzlich in Stufe 2:", neu)


if __name__ == "__main__":
    cache = {}
    for n in STUFE1_DATEIEN:
        cache[n] = parse(D / n)
    test_oz(cache)
    test_platzhalter_und_dubletten()
    s1 = test_stufe1(cache)
    test_p1b(cache, s1)
    if STUFE2:
        test_stufe2(cache, s1)
    print(f"\n{sum(ergebnisse)} von {len(ergebnisse)} Tests bestanden")
    sys.exit(0 if all(ergebnisse) else 1)
