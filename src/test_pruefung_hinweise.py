"""
test_pruefung_hinweise.py - Tests für src/pruefung_hinweise.py (Prüfungen Nr. 7–14 und 18, Block B2, Sitzung B2).

Teile:
  1. kleine selbst gebaute Tabellen: je Prüfung Positiv- und Negativfälle (bekannte Fehlalarm-Klassen als Negativ)
  2. echte Dateien: Beispiele aus input/pruefkatalog.md, „nur Preise“, Datenvertrag, R5, R7, Sortierung
  3. Doppellauf (E14): zweimal prüfen, das zweite Mal in umgekehrter Dateireihenfolge, Ergebnis gleich
  4. Skeptiker am Original (E2 e): jeder Beleg jedes Funds wird in der Rohdatei gesucht, ohne parse():
     GAEB XML per lxml (Item über BoQCtgy/Item RNoPart, Text der Description), GAEB 90 zeilenweise (Block der
     Position von Satz 21 bis zum nächsten Satz außer 22–30), PDF über den Seitentext von pdfplumber
     (Start- und bis zu 3 Folgeseiten, ohne Leerzeichen verglichen, wie S2 in docs/pruefprotokoll.md).
     Funde, deren Beleg nur hinter dem Positionsblock steht (GAEB 90: Vorbemerkung Satz 20 des nächsten
     Bereichs, Lücke B2-L1 in docs/uebergabe_sitzung_B2.md), werden gezählt und gemeldet, nicht still gefiltert.

Aufruf aus der Projektwurzel (uv-Befehl siehe AGENTS.md), Ordner mit den Originaldaten als Argument:
  python src/test_pruefung_hinweise.py data/raw [--bericht ziel.json]
Exit-Code 0 = alle Tests bestanden. Schreibt nichts in data/ (E12 (4)).
"""
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd
import pdfplumber
from lxml import etree

from lv_parser import parse, COLUMNS
from pruefung_widerspruch import normalisiere_leerzeichen, normalisiere_oz, beleg_im_text
from pruefung_formal import nur_preise, sortiere, pruefe_formal
from pruefung_hinweise import (pruefe_hinweise, KATALOG, RANG_VORSCHLAG, NUMMERN, FELDWERT, KENNZEICHEN,
                               MAX_AUSSCHNITTE, KOSTENWIRKUNG, ausschnitt)

D = Path(sys.argv[1]) if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else Path("data/raw")
BERICHT = sys.argv[sys.argv.index("--bericht") + 1] if "--bericht" in sys.argv else None
FELDER = ["id", "pruefung", "kategorie", "titel", "positionen", "belege", "feldbelege",
          "begruendung", "stufe", "stufe_begruendung", "prioritaet_in_stufe", "rueckfrage", "status"]
KATEGORIEN = {"nachweisbarer Fehler", "möglicher Widerspruch", "Unklarheit", "Risikohinweis"}
VERBOTEN = re.compile(r"Anspruch|berechtigt|durchsetzbar|§")          # R7, Team 21.11.2026
IM_BLOCK = {str(n) for n in range(22, 31)}   # GAEB 90: Sätze nach Satz 21, die zur Position gehören (Original)

ergebnisse = []


def check(name, ok, detail=""):
    ergebnisse.append(ok)
    print(f"{'OK    ' if ok else 'FEHLER'} {name}" + (f" – {detail}" if detail and not ok else ""))


def zeile(oz, kurz="Position", lang="", menge=1.0, einheit="St", einheit_roh=None, fmt="GAEB XML",
          art_roh="", datei="test.X83", typ="Position", seite=None):
    z = {c: None for c in COLUMNS}
    z.update(datei=datei, format=fmt, typ=typ, oz=oz, kurztext=kurz, langtext=lang, menge=menge,
             einheit=einheit, einheit_roh=einheit_roh if einheit_roh is not None else einheit,
             art_roh=art_roh, seite=seite)
    return z


def tabelle(*zeilen):
    return pd.DataFrame(list(zeilen), columns=COLUMNS)


def nrn(funde, oz=None):
    return sorted({f["pruefung"] for f in funde if oz is None or f["positionen"][0]["oz"] == oz})


def nur(nr, **kw):
    """Funde einer einzelnen Position."""
    return [f["pruefung"] for f in pruefe_hinweise(tabelle(zeile("1.1", **kw)))]


# --------------------------------------------------------------------------- 1. kleine Tabellen

def test_klein():
    check("Rangtabelle (Team 21:20): Stufe 2 Nr. 18 → 4; Stufe 3 Nr. 9, 10, 7, 8 → 1–4; Stufe 4 Nr. 14 → 1, 13 → 3, "
          "11 → 4, 12 → 5", RANG_VORSCHLAG == {(18, 2): 4, (9, 3): 1, (10, 3): 2, (7, 3): 3, (8, 3): 4,
                                              (14, 4): 1, (13, 4): 3, (11, 4): 4, (12, 4): 5})
    # Nr. 7
    check("Nr. 7: „oder gleichwertig“", 7 in nur(7, lang="Fabrikat: Wilo Stratos oder gleichwertig"))
    check("Nr. 7: „o. glw.“ und „oder glw.“", 7 in nur(7, lang="Richtfabrikat: Brillux ELF 900 oder glw.")
          and 7 in nur(7, lang="Fabrikat Hersteller X o. glw."))
    check("Nr. 7 negativ: nur „Fabrikat:“ ohne gleichwertig", 7 not in nur(7, lang="Angebotenes Fabrikat: ......"))
    # Nr. 8
    check("Nr. 8: „Bestehende Bachverrohrung“", 8 in nur(8, kurz="Bestehende Bachverrohrung DN 600 ausbauen"))
    check("Nr. 8: „vorhandene Leitung“, „im Bestand“",
          8 in nur(8, lang="an vorhandene Leitung anschließen") and 8 in nur(8, lang="Arbeiten im Bestand"))
    for neg in ("Schalung bestehend aus Brettern", "Bestandsunterlagen übergeben", "Bestandslageplan erstellen",
                "Bestandteil der Leistung", "Verbau herstellen und rückbauen", "sofern vorhanden",
                "auf bauseitig vorhandenem Sockel montieren", "ist vorhanden"):
        check(f"Nr. 8 negativ: „{neg}“", 8 not in nur(8, lang=neg))
    # Nr. 9
    check("Nr. 9: „abbrechen und entsorgen“, „LAGA“, „Deponie“",
          all(9 in nur(9, lang=t) for t in ("Beton abbrechen und entsorgen", "Einstufung nach LAGA",
                                            "Deponiegebühren einrechnen")))
    for neg in ("Versorgungs-, Entsorgungsleitungen und Kabel", "Entsorgungseinrichtungen der Baustelle",
                "Netz der öffentlichen Ver- und Entsorgungsträger", "Ver- und Entsorgung der Baustelle",
                "Heizung Ver-/Entsorgungseinr. warten",
                "Homogenbereich B 0, DIN 18300", "Bodenklasse 3 bis 5"):
        check(f"Nr. 9 negativ: „{neg}“", 9 not in nur(9, lang=neg))
    # Nr. 10
    check("Nr. 10: Text „vorhalten“", 10 in nur(10, kurz="Bauzaun H 2m vorhalten"))
    f = pruefe_hinweise(tabelle(zeile("1.1", kurz="Bauzaun", einheit="mWo")))
    check("Nr. 10: nur Zeiteinheit mWo, Feldbeleg „Einheit: mWo“",
          nrn(f) == [10] and f[0]["feldbelege"] == [{"art": FELDWERT, "text": "Einheit: mWo"}])
    check("Nr. 10 negativ: „Standzeit der Verschleißteile“", 10 not in nur(10, lang="deren Standzeit unter üblichen"))
    check("Nr. 10 negativ: „Ersatzteillisten mit Vorhaltungsempfehlung“",
          10 not in nur(10, lang="Ersatzteillisten mit Vorhaltungsempfehlung und Bezugsquellen"))
    # Nr. 11: nur in Kombination mit Nr. 5–10
    check("Nr. 11 negativ: „ggf.“ ohne weiteren Fund", 11 not in nur(11, lang="ggf. umsetzen"))
    check("Nr. 11: „ggf.“ mit Nr. 10 an derselben Position", nur(11, lang="vorhalten, ggf. umsetzen") == [10, 11])
    f = pruefe_hinweise(tabelle(zeile("1.1", kurz="Wasserhaltung", einheit="psch", lang="nach Aufwand")))
    check("Nr. 11: mit Nr. 6 (psch, aus pruefe_formal), Begründung nennt Nr. 6",
          nrn(f) == [11] and "Fund Nr. 6" in f[0]["begruendung"])
    f = pruefe_hinweise(tabelle(zeile("1.1", lang="nach Aufwand")),
                        weitere_funde=[{"pruefung": 5, "positionen": [{"datei": "test.X83", "oz": "01.1"}]}])
    check("Nr. 11: Kombination über `weitere_funde` (OZ normalisiert)", nrn(f) == [11])
    check("Nr. 11 negativ: „etc.“/„usw.“ zählen nicht", 11 not in nur(11, lang="vorhalten, Formteile usw. etc."))
    # Nr. 12
    check("Nr. 12: „wie vor, jedoch“", 12 in nur(12, kurz="wie vor, jedoch DN 250"))
    check("Nr. 12: „Leistung wie Position …, jedoch“",
          12 in nur(12, lang="Leistung wie Position zuletzt in vollem Wortlaut beschrieben, jedoch DN 200"))
    check("Nr. 12: „Wie Position 3. 2. 4., jedoch“", 12 in nur(12, kurz="Wie Position 3. 2. 4., jedoch Wurzelbeh."))
    f = pruefe_hinweise(tabelle(zeile("1.1", kurz="Rohr", lang="Rohr DN 100 wie vor beschrieben, jedoch DN 150")))
    check("Nr. 12: Beleg enthält Verweis und „jedoch“",
          any("wie vor" in b and "jedoch" in b for b in f[0]["belege"]))
    for neg in ("Einlaufteil: wie beschrieben, jedoch breiter", "jedoch ohne Deckel", "wie vorgegeben",
                "Leistung wie Position zuletzt in vollem Wortlaut beschrieben,", "sonst wie vor",
                "wie vor; Material jedoch bauseits"):
        check(f"Nr. 12 negativ: „{neg}“", 12 not in nur(12, lang=neg))
    # Nr. 13
    check("Nr. 13: „Stundenlohnarbeiten“, Feldbeleg Einheit h",
          (lambda f: nrn(f) == [13] and {"art": FELDWERT, "text": "Einheit: h"} in f[0]["feldbelege"])(
              pruefe_hinweise(tabelle(zeile("1.1", kurz="Polier", einheit="h", lang="Stundenlohnarbeiten durch")))))
    check("Nr. 13 negativ: nur Einheit h (Betrieb Pumpe)", 13 not in nur(13, kurz="Betrieb der Pumpen", einheit="h"))
    check("Nr. 13 negativ: „Verrechnungssatz für das Gerät“", 13 not in nur(13, lang="Verrechnungssatz für das Gerät"))
    check("Nr. 13: Kennzeichen <HourIt> (GAEB XML)",
          (lambda f: {"art": KENNZEICHEN, "text": "<HourIt>"} in f[0]["feldbelege"])(
              pruefe_hinweise(tabelle(zeile("1.1", kurz="Facharbeiter", art_roh="Stundenlohn")))))
    # Nr. 14
    check("Nr. 14: Kennzeichen Bild in GAEB XML", nur(14, art_roh="enthält Bild/Skizze") == [14])
    check("Nr. 14 negativ: Wort „Skizze“ im Text, „Kennzeichnung“", 14 not in nur(14, lang="siehe Skizze, Kennzeichnung"))
    # Nr. 18
    f = pruefe_hinweise(tabelle(zeile("1.1", kurz="Beton abbrechen", einheit="m³", einheit_roh="m3")))
    check("Nr. 18: Menge 1 m³, Feldbelege Menge und Einheit wie im Original",
          18 in nrn(f) and [x for x in f if x["pruefung"] == 18][0]["feldbelege"] ==
          [{"art": FELDWERT, "text": "Menge: 1"}, {"art": FELDWERT, "text": "Einheit: m3"}])
    check("Nr. 18 negativ: Menge 1 St, Menge 2 m³",
          18 not in nur(18, einheit="St") and 18 not in nur(18, einheit="m³", menge=2.0))
    check("Nr. 18 negativ: Bedarfsposition (Nr. 5) mit Menge 1 m",
          18 not in nur(18, einheit="m", art_roh="Bedarfsposition WithoutTotal"))
    # Allgemein
    check("ohne Kurztext kein Fund (R5)", nur(7, kurz="", lang="oder gleichwertig") == [])
    df = tabelle(zeile("1.1", kurz="", menge=1.0, einheit="m³"), zeile("1.2", kurz="", einheit="St"))
    check("reine Preisdatei (kein Kurztext): keine Funde", nur_preise(df) and pruefe_hinweise(df) == [])
    t = "a b c d e f g h oder gleichwertig i j k l m n"
    m = re.search("gleichwertig", t)
    check("Ausschnitt: 6 Wörter davor, 4 danach, wörtlich", ausschnitt(t, m) == "d e f g h oder gleichwertig i j k l")
    t = "wie vor, jedoch 02) Schacht 2 , nach Lageplan"
    m = re.search("jedoch", t)
    check("Ausschnitt endet nicht auf reinem Satzzeichen (FS-B2-1)", ausschnitt(t, m, 6, 3) == "wie vor, jedoch 02) Schacht 2")
    f = pruefe_hinweise(tabelle(zeile("1.1", kurz="X", lang=" ".join(f"w{i} vorhalten" for i in range(20)))))
    check(f"höchstens Kurztext + {MAX_AUSSCHNITTE} Ausschnitte", len(f[0]["belege"]) == 1 + MAX_AUSSCHNITTE)
    zwei = tabelle(zeile("1.1", kurz="Bestand vorhalten oder gleichwertig"), zeile("01.1", kurz="Bestand"))
    ids = [f["id"] for f in pruefe_hinweise(zwei)]
    check("höchstens ein Fund je Prüfung, Datei und normalisierter OZ", len(ids) == len(set(ids)))


# --------------------------------------------------------------------------- 2. echte Dateien

def dateien():
    return sorted(p for p in D.iterdir() if not p.name.startswith(".") and p.suffix.lower() != ".docx")


def finde(funde, nr, datei, oz):
    return [f for f in funde if f["pruefung"] == nr and f["positionen"][0]["datei"] == datei
            and normalisiere_oz(f["positionen"][0]["oz"]) == normalisiere_oz(oz)]


def test_echt(cache, alle):
    beispiele = [  # input/pruefkatalog.md, Spalte „Beleg im Datensatz“
        (7, "8209.003_Leistungsverzeichnis_leer.X83", None),
        (8, "GAEB-[PROJEKT_004].X83", "02.0017"),
        (9, "[ORT_024] LV24069.D86", "8.2.1"),
        (10, "[NUMMER_001]_leer.X83", "1.2.3"),
        (12, "LV-Ausdruck-[PROJEKT_004].pdf", "02.0015"),
        (14, "501-24-01_GAEB-XML_sas.x83", "03.03.0018"),
    ]
    for nr, datei, oz in beispiele:
        if oz:
            check(f"Katalog-Beispiel Nr. {nr}: {datei} {oz}", len(finde(alle, nr, datei, oz)) == 1)
        else:
            n = sum(f["pruefung"] == nr and f["positionen"][0]["datei"] == datei for f in alle)
            check(f"Katalog-Beispiel Nr. {nr}: {datei} hat Funde ({n})", n > 0)
    f = finde(alle, 10, "[NUMMER_001]_leer.X83", "1.2.3")
    check("Nr. 10 Bauzaun 1.2.3: Feldbeleg Einheit mWo",
          bool(f) and {"art": FELDWERT, "text": "Einheit: mWo"} in f[0]["feldbelege"])
    f = finde(alle, 14, "501-24-01_GAEB-XML_sas.x83", "03.03.0018")
    check("Nr. 14 ist im Datensatz genau einmal", sum(x["pruefung"] == 14 for x in alle) == 1 and bool(f))
    # Katalog-Beispiel Nr. 13 ist der Titel 04 in GAEB-[PROJEKT_004].X83; ein Titel ist kein Positionstext (R5).
    # Die Positionen dort nennen „Stundenlohn“ nicht und haben Einheit h: Nr. 13 findet sie nicht (B2-F3).
    df = cache.get("GAEB-[PROJEKT_004].X83")
    if df is not None:
        t04 = df[(df.typ == "Position") & df.oz.str.startswith("04.")]
        check("Nr. 13 Katalog-Beispiel Titel 04: Positionen mit Einheit h, ohne „Stundenlohn“ im Text, kein Fund (B2-F3)",
              len(t04) > 0 and not finde([f for f in alle if f["pruefung"] == 13], 13, "GAEB-[PROJEKT_004].X83",
                                         t04.oz.iloc[0]))
    for name in ("StBALV23040.D84", "Angebot AN24-0305.D84"):
        if name in cache:
            check(f"nur Preise: {name} ohne Funde", nur_preise(cache[name])
                  and pruefe_hinweise(cache[name], D / name) == [])
    try:
        pruefe_hinweise(tabelle(zeile("1.1", kurz="Bestand", fmt="PDF")))
        check("PDF ohne Quelle: Fehler statt ungeprüfter Belege", False)
    except ValueError:
        check("PDF ohne Quelle: Fehler statt ungeprüfter Belege", True)
    # Datenvertrag
    check("Datenvertrag: genau die Felder", all(list(f) == FELDER for f in alle))
    check("Kategorie, Stufe, Rang laut KATALOG/RANG_VORSCHLAG",
          all(f["kategorie"] in KATEGORIEN and (f["kategorie"], f["stufe"]) == KATALOG[f["pruefung"]][:2]
              and f["prioritaet_in_stufe"] == RANG_VORSCHLAG[(f["pruefung"], f["stufe"])] for f in alle))
    check("nur Prüfungen Nr. 7–14, 18", {f["pruefung"] for f in alle} <= set(NUMMERN))
    check("Kostenwirkung für jede Prüfung beschrieben", set(KOSTENWIRKUNG) == set(NUMMERN))
    check("Fund-IDs eindeutig", len({f["id"] for f in alle}) == len(alle))
    check("Status offen, keine Rückfrage", all(f["status"] == "offen" and f["rueckfrage"] is None for f in alle))
    # R5 gegen die Parser-Ausgabe (Original: Teil 4)
    texte = {}
    for name, df in cache.items():
        for r in df[df.typ == "Position"].itertuples():
            texte[(name, normalisiere_oz(r.oz))] = (r.kurztext if isinstance(r.kurztext, str) else "",
                                                    r.langtext if isinstance(r.langtext, str) else "")
    falsch = [f["id"] for f in alle if not all(beleg_im_text(b, *texte[(f["positionen"][0]["datei"],
                                                                         normalisiere_oz(f["positionen"][0]["oz"]))])
                                                for b in f["belege"])]
    check("R5: jeder Beleg wörtlich in Kurz- oder Langtext der Position", not falsch, str(falsch[:5]))
    check("R5: erster Beleg = Kurztext",
          all(f["belege"][0] == normalisiere_leerzeichen(texte[(f["positionen"][0]["datei"],
                                                                normalisiere_oz(f["positionen"][0]["oz"]))][0])
              for f in alle))
    r7 = [f["id"] for f in alle if VERBOTEN.search(f["titel"] + " " + f["begruendung"])]
    check("R7: keine verbotenen Begriffe in Titel und Begründung", not r7, str(r7[:5]))
    for name, df in cache.items():
        f = [x for x in alle if x["positionen"][0]["datei"] == name]
        if f != sortiere(list(f)):
            check(f"Sortierung Stufe → Rang → OZ: {name}", False)
            break
    else:
        check("Sortierung Stufe → Rang → OZ in jeder Datei", True)


# --------------------------------------------------------------------------- 3. Doppellauf

def lauf(cache, namen):
    return {n: pruefe_hinweise(cache[n], D / n) for n in namen}


def test_doppellauf(cache):
    namen = sorted(cache)
    a, b = lauf(cache, namen), lauf(cache, list(reversed(namen)))
    check("Doppellauf (E14): gleiche Funde, IDs, Belege und Reihenfolge, auch in umgekehrter Dateireihenfolge",
          json.dumps(a, ensure_ascii=False, sort_keys=True) == json.dumps(b, ensure_ascii=False, sort_keys=True))
    neu = {n: parse(str(D / n)) for n in namen[:3]}
    check("Doppellauf mit neu gelesenen Dateien (3 Dateien)",
          all(pruefe_hinweise(neu[n], D / n) == a[n] for n in neu))
    return a


# --------------------------------------------------------------------------- 4. Skeptiker am Original

def _ohne_ws(s):
    return re.sub(r"\s+", "", s)


def original_xml(pfad):
    """OZ (normalisiert) -> (Item-ID, Text der Description, Einheit QU, hat Bild) direkt aus der Rohdatei."""
    root = etree.parse(str(pfad), etree.XMLParser(huge_tree=True, recover=True)).getroot()
    ln = lambda e: etree.QName(e).localname if isinstance(e.tag, str) else ""
    aus = {}
    for it in root.iter():
        if ln(it) != "Item":
            continue
        teile = [it.get("RNoPart", "")]
        p = it.getparent()
        while p is not None:
            if ln(p) == "BoQCtgy":
                teile.insert(0, p.get("RNoPart", ""))
            p = p.getparent()
        desc = next((c for c in it if ln(c) == "Description"), None)
        stuecke = []
        if desc is not None:
            for e in desc.iter():
                if ln(e) in ("image", "Image"):
                    continue
                if ln(e) in ("p", "br"):
                    stuecke.append(" ")
                if e.text and ln(e.getparent()) not in ("image", "Image") and ln(e) not in ("image", "Image"):
                    stuecke.append(e.text)
                if e.tail and e is not desc:
                    stuecke.append(e.tail)
        bild = desc is not None and any(ln(e) in ("image", "Image") for e in desc.iter())
        qu = next((c.text or "" for c in it if ln(c) == "QU"), "")
        aus[normalisiere_oz(".".join(teile))] = (it.get("ID", ""), normalisiere_leerzeichen("".join(stuecke)),
                                                 qu.strip(), bild)
    return aus


def original_gaeb90(pfad):
    """OZ ohne Leerzeichen -> (Zeile Satz 21, Text Satz 25/26 des Blocks, Einheit Spalten 35–38, Menge Spalten 24–34)
    und je OZ der Text der Sätze 25/26, die hinter dem Block (nach einem anderen Satz) bis zum nächsten Satz 21
    stehen, z. B. die Vorbemerkung (Satz 20) des nächsten Bereichs."""
    zeilen = pfad.read_bytes().decode("cp850").replace("\r\n", "\n").split("\n")
    bloecke, hinter, oz, im_block = {}, defaultdict(lambda: {"25": [], "26": []}), None, False
    for nr, l in enumerate(zeilen, 1):
        sa = l[:2]
        if sa == "21":
            oz, im_block = re.sub(r"\s", "", l[2:11]), True
            bloecke[oz] = [nr, {"25": [], "26": []}, l[34:38].strip(), l[23:34]]
        elif sa in IM_BLOCK:
            if sa in ("25", "26") and oz is not None:
                (bloecke[oz][1] if im_block else hinter[oz])[sa].append(l[2:72].strip())
        else:
            im_block = False
    n = lambda v: normalisiere_leerzeichen(" ".join(v))
    # Text im Block: Kurztext (Satz 25) und Langtext (Satz 26) wie im Original; „verlängert“: so, wie parse() ihn
    # zusammensetzt, wenn Text hinter dem Block mitgenommen wird (nur für die Einordnung B2-L1)
    return ({k: (v[0], n(v[1]["25"]) + " " + n(v[1]["26"]), v[2], v[3]) for k, v in bloecke.items()},
            {k: n(v[1]["25"] + hinter[k]["25"]) + " " + n(v[1]["26"] + hinter[k]["26"]) for k, v in bloecke.items()})


class PdfOriginal:
    def __init__(self, pfad):
        with pdfplumber.open(str(pfad)) as pdf:
            self.seiten = [_ohne_ws(p.extract_text() or "") for p in pdf.pages]

    def finde(self, text, seite):
        z = _ohne_ws(text)
        for s in range(seite, min(seite + 4, len(self.seiten) + 1)):
            if z in self.seiten[s - 1]:
                return s
        return None


def skeptiker(alle):
    """Je Fund: Ergebnis, Fundstelle im Original und fehlende Belege. Ohne parse()."""
    roh = {}
    ergebnis = []
    for f in alle:
        p = f["positionen"][0]
        pfad = D / p["datei"]
        endung = pfad.suffix.lower()
        if p["datei"] not in roh:
            if endung.startswith(".x"):
                roh[p["datei"]] = ("xml", original_xml(pfad))
            elif endung.startswith(".d"):
                roh[p["datei"]] = ("g90", original_gaeb90(pfad))
            else:
                roh[p["datei"]] = ("pdf", PdfOriginal(pfad))
        art, daten = roh[p["datei"]]
        fehlt, stelle, hinter = [], None, False
        if art == "xml":
            e = daten.get(normalisiere_oz(p["oz"]))
            if e is None:
                fehlt = ["Position nicht gefunden"]
            else:
                stelle = f"Item {e[0]}"
                fehlt = [b for b in f["belege"] if b not in e[1]]
                for fb in f["feldbelege"]:
                    if fb["text"].startswith("Einheit: ") and fb["text"][9:] != e[2]:
                        fehlt.append(fb["text"])
                    if fb["text"].startswith("<image>") and not e[3]:
                        fehlt.append(fb["text"])
        elif art == "g90":
            bloecke, nachtext = daten
            k = p["oz"].replace(".", "")
            e = bloecke.get(k)
            if e is None:
                fehlt = ["Position nicht gefunden"]
            else:
                stelle = f"Satz 21 Z. {e[0]}"
                fehlt = [b for b in f["belege"] if b not in e[1]]
                hinter = bool(fehlt) and all(b in nachtext.get(k, "") for b in fehlt)
                for fb in f["feldbelege"]:
                    if fb["text"].startswith("Einheit: ") and fb["text"][9:] != e[2]:
                        fehlt.append(fb["text"])
        else:
            s0 = p["seite"] or 1
            seiten = [daten.finde(b, s0) for b in f["belege"]]
            fehlt = [b for b, s in zip(f["belege"], seiten) if s is None]
            stelle = "S. " + ", ".join(sorted({str(s) for s in seiten if s}))
            for fb in f["feldbelege"]:
                if fb["text"].startswith("Einheit: ") and daten.finde(fb["text"][9:], s0) is None:
                    fehlt.append(fb["text"])
        ergebnis.append({"id": f["id"], "pruefung": f["pruefung"], "datei": p["datei"], "oz": p["oz"],
                         "stelle": stelle, "fehlt": fehlt, "nur_hinter_block": hinter,
                         "ergebnis": "Beleg im Original gefunden" if not fehlt else
                         ("Beleg nur hinter dem Positionsblock (B2-L1)" if hinter else "Beleg nicht im Original")})
    return ergebnis


def test_skeptiker(alle):
    erg = skeptiker(alle)
    z = Counter(e["ergebnis"] for e in erg)
    print("       Skeptiker:", dict(z))
    je = defaultdict(Counter)
    for e in erg:
        je[e["pruefung"]][e["ergebnis"]] += 1
    for nr in sorted(je):
        print(f"       Nr. {nr}: {dict(je[nr])}")
    falsch = [e for e in erg if e["ergebnis"] == "Beleg nicht im Original"]
    check("Skeptiker: kein Beleg fehlt im Original (außer B2-L1, gemeldet)", not falsch,
          "; ".join(f"{e['id']}: {e['fehlt'][:1]}" for e in falsch[:5]))
    stich = defaultdict(list)
    for e in erg:
        if len(stich[e["pruefung"]]) < 5:
            stich[e["pruefung"]].append(e)
    check("Skeptiker-Stichprobe: je Prüfung mindestens 5 Funde (oder alle) am Original gesucht",
          all(len(stich[nr]) >= min(5, sum(f["pruefung"] == nr for f in alle)) for nr in je))
    return erg


# --------------------------------------------------------------------------- main

if __name__ == "__main__":
    test_klein()
    if not D.is_dir():
        sys.exit(f"Ordner {D} fehlt")
    cache = {}
    for p in dateien():
        cache[p.name] = parse(str(p))
    alle = [f for n in sorted(cache) for f in pruefe_hinweise(cache[n], D / n)]
    print(f"       {len(alle)} Funde in {len({f['positionen'][0]['datei'] for f in alle})} Dateien: "
          + str(dict(sorted(Counter(f['pruefung'] for f in alle).items()))))
    test_echt(cache, alle)
    test_doppellauf(cache)
    erg = test_skeptiker(alle)
    if BERICHT:
        ziel = Path(BERICHT).resolve()
        if ziel.is_relative_to(D.resolve()) or ziel.is_relative_to(Path("data").resolve()):
            sys.exit("--bericht nie in data/ (E12 (4)); Ziel z. B. im Temp-Ordner")
        Path(BERICHT).write_text(json.dumps({"funde": alle, "skeptiker": erg}, ensure_ascii=False, indent=1),
                                 encoding="utf-8")
    print(f"\n{sum(ergebnisse)}/{len(ergebnisse)} Tests bestanden")
    sys.exit(0 if all(ergebnisse) else 1)
