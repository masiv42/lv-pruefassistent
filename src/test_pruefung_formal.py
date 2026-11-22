"""
test_pruefung_formal.py - Tests für src/pruefung_formal.py (Prüfungen Nr. 3–6, P2).

Nr. 3 und 4 kommen in den echten Daten nur selten bzw. gar nicht vor; sie werden mit
kleinen selbst gebauten Tabellen geprüft (Team, Chat 21.11.2026). Nr. 5 und 6 sowie
„nur Preise“ zusätzlich an echten Dateien.
Aufruf aus der Projektwurzel (uv-Befehl siehe AGENTS.md):
  python src/test_pruefung_formal.py data/raw
Exit-Code 0 = alle Tests bestanden.
"""
import json
import re
import sys
from pathlib import Path

import pandas as pd

from lv_parser import parse, COLUMNS
from pruefung_widerspruch import normalisiere_leerzeichen, normalisiere_oz, PRIORITAET_IN_STUFE
from pruefung_formal import (
    pruefe_formal, alle_pruefungen, nur_preise, sortiere, oz_sortkey, MENGE_0, MENGE_0_TEXT,
    FEHLER, RISIKO, UNKLARHEIT, FELDWERT, KENNZEICHEN, datei_hinweis, HINWEIS_PHASE_86,
    AUFTRAG_OHNE_ME, AUFTRAG_OHNE_ME_TITEL, AUFTRAG_OHNE_ME_TEXT,
)

D = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/raw")
FELDER = ["id", "pruefung", "kategorie", "titel", "positionen", "belege", "feldbelege",
          "begruendung", "stufe", "stufe_begruendung", "prioritaet_in_stufe", "rueckfrage", "status"]
KATEGORIEN = {"nachweisbarer Fehler", "möglicher Widerspruch", "Unklarheit", "Risikohinweis"}
VERBOTEN = re.compile(r"Anspruch|berechtigt|durchsetzbar|§")          # R7, Team 21.11.2026

ergebnisse = []


def check(name, ok, detail=""):
    ergebnisse.append(ok)
    print(f"{'OK    ' if ok else 'FEHLER'} {name}" + (f" – {detail}" if detail and not ok else ""))


def zeile(oz, kurz="Position", menge=1.0, einheit="St", einheit_roh=None, fmt="GAEB XML",
          lang="", art_roh="", datei="test.X83", typ="Position", seite=None):
    r = {c: None for c in COLUMNS}
    r.update(datei=datei, format=fmt, seite=seite, typ=typ, oz=oz, kurztext=kurz, langtext=lang,
             menge=menge, einheit=einheit, einheit_roh=einheit if einheit_roh is None else einheit_roh,
             art="Normal", art_roh=art_roh)
    return r


def tabelle(*zeilen):
    return pd.DataFrame(list(zeilen), columns=COLUMNS)


def nach_nr(funde, nr):
    return [f for f in funde if f["pruefung"] == nr]


def allgemein(name, funde):
    check(f"{name}: Felder nach Datenvertrag", all(list(f) == FELDER for f in funde))
    check(f"{name}: Kategorie aus R6", all(f["kategorie"] in KATEGORIEN for f in funde))
    check(f"{name}: Feldbelege nur Feldwert/Kennzeichen",
          all(b["art"] in (FELDWERT, KENNZEICHEN) for f in funde for b in f["feldbelege"]))
    check(f"{name}: keine verbotenen Begriffe (R7)",
          not [f["id"] for f in funde if VERBOTEN.search(f["titel"] + " " + f["begruendung"])])
    check(f"{name}: Fund-IDs eindeutig", len({f["id"] for f in funde}) == len(funde))
    check(f"{name}: JSON-fähig", bool(json.dumps(funde, ensure_ascii=False)))


# --------------------------------------------------------------------------- Nr. 3

def test_nr3():
    df = tabelle(
        zeile("1.1", "Rohr DN 100", menge=None),                    # Menge fehlt
        zeile("1.2", "Formstück", einheit=None),                    # Einheit None
        zeile("1.3", "Schieber", einheit=""),                       # Einheit ""
        zeile("1.4", "Hydrant", menge=0.0),                         # Menge 0
        zeile("1.5", "Nachtrag Pumpe", menge=0.0, einheit=""),      # Menge 0 und Einheit fehlt
        zeile("1.6", "Bogen", menge=None, einheit=None),            # beides fehlt
        zeile("1.7", "Normale Position"),                           # kein Fund
        zeile("1", "Titel ohne Menge", menge=None, einheit=None, typ="Titel"),   # Titel: kein Fund
    )
    f = {x["positionen"][0]["oz"]: x for x in nach_nr(pruefe_formal(df), 3)}
    check("Nr. 3: genau 6 Funde, keiner für normale Position oder Titel",
          sorted(f) == ["1.1", "1.2", "1.3", "1.4", "1.5", "1.6"], str(sorted(f)))
    check("Nr. 3: Menge None = „Menge fehlt“, nachweisbarer Fehler, Prio 1, Feldwert „Menge: (leer)“",
          f["1.1"]["titel"] == "Menge fehlt" and f["1.1"]["kategorie"] == FEHLER and f["1.1"]["stufe"] == 1
          and f["1.1"]["feldbelege"] == [{"art": FELDWERT, "text": "Menge: (leer)"}])
    check("Nr. 3: Einheit None und \"\" = „Einheit fehlt“ mit Feldwert „Einheit: (leer)“",
          all(f[o]["titel"] == "Einheit fehlt" and f[o]["feldbelege"] == [{"art": FELDWERT, "text": "Einheit: (leer)"}]
              for o in ("1.2", "1.3")))
    check("Nr. 3: Menge 0 = eigener Hinweis „Menge 0“ (kein Fehler), Kategorie/Prio wie MENGE_0",
          f["1.4"]["titel"] == "Menge 0" and (f["1.4"]["kategorie"], f["1.4"]["stufe"]) == MENGE_0
          and f["1.4"]["kategorie"] != FEHLER)
    check("Nr. 3: Menge 0 und Einheit fehlt = ein Fund, Fehler, beide Feldwerte",
          f["1.5"]["kategorie"] == FEHLER and f["1.5"]["titel"] == "Einheit fehlt (Menge 0)"
          and {b["text"] for b in f["1.5"]["feldbelege"]} == {"Menge: 0", "Einheit: (leer)"})
    check("Nr. 3: Menge und Einheit fehlen = ein Fund", f["1.6"]["titel"] == "Menge und Einheit fehlen")
    check("F2: „Menge 0“ = Risikohinweis, Stufe 2, Rang 2, Befundtext des Teams, keine Annahme mehr",
          (f["1.4"]["kategorie"], f["1.4"]["stufe"], f["1.4"]["prioritaet_in_stufe"]) == (RISIKO, 2, 2)
          and (RISIKO, 2) == MENGE_0 and "F2" in f["1.4"]["stufe_begruendung"]
          and f["1.4"]["begruendung"] == MENGE_0_TEXT
          and "Annahme" not in f["1.4"]["stufe_begruendung"])
    check("Nr. 3: Beleg = Kurztext wörtlich", all(x["belege"] == [df[df.oz == o].kurztext.iloc[0]]
                                                   for o, x in f.items()))
    df = tabelle(zeile("2.1", "", menge=None))
    check("Nr. 3: Position ohne Kurztext ergibt keinen Fund (kein wörtlicher Beleg, R5)",
          nach_nr(pruefe_formal(df), 3) == [])
    allgemein("Nr. 3", list(f.values()))


# --------------------------------------------------------------------------- Nr. 4

def test_nr4():
    df = tabelle(
        zeile("05.01.4", "Edelstahl-Rohr DN 125"),
        zeile("5.1.4", "Losflansch DN 125"),
        zeile("5.1.5", "Bogen"),
        zeile("5.1.6", "Flansch"),
        zeile("5.1.6", "Flansch"),                       # gleicher Kurztext: Beleg einmal
        zeile("5", "Titel", typ="Titel"),
        zeile("5", "Position mit Titel-OZ"),             # Titel zählt nicht
    )
    f = {x["id"]: x for x in nach_nr(pruefe_formal(df), 4)}
    check("Nr. 4: zwei Funde (5.1.4 in zwei Schreibweisen, 5.1.6 doppelt), keiner für Titel-OZ",
          sorted(f) == ["4|test.X83|5.1.4", "4|test.X83|5.1.6"], str(sorted(f)))
    a = f["4|test.X83|5.1.4"]
    check("Nr. 4: ein Fund mit allen betroffenen Positionen (Original-OZ)",
          [p["oz"] for p in a["positionen"]] == ["05.01.4", "5.1.4"])
    check("Nr. 4: Belege = Kurztexte der Positionen",
          a["belege"] == ["Edelstahl-Rohr DN 125", "Losflansch DN 125"])
    check("Nr. 4: gleiche Kurztexte nur einmal, zwei Positionen",
          f["4|test.X83|5.1.6"]["belege"] == ["Flansch"] and len(f["4|test.X83|5.1.6"]["positionen"]) == 2)
    check("Nr. 4: nachweisbarer Fehler, Stufe 1", all(x["kategorie"] == FEHLER and x["stufe"] == 1
                                                      for x in f.values()))
    check("Nr. 4: keine doppelte OZ -> kein Fund", nach_nr(pruefe_formal(tabelle(zeile("1.1"), zeile("1.2"))), 4) == [])
    allgemein("Nr. 4", list(f.values()))


def test_f1_f2_b1b():
    """F1 (B1b): Auftrags-LV (Austauschphase 86) mit Menge 0 und leerer Einheit -> Unklarheit, Stufe 4;
    in Ausschreibungs-LVs bleibt es ein Fehler in Stufe 1. F2 (B1b): Bedarfsposition mit Menge 0 -> ein Fund."""
    for d, erwartet in (("auftrag.D86", AUFTRAG_OHNE_ME), ("auftrag.X86", AUFTRAG_OHNE_ME), ("lv.D83", (FEHLER, 1)),
                        ("lv.X83", (FEHLER, 1)), ("lv.pdf", (FEHLER, 1))):
        f = pruefe_formal(tabelle(zeile("8.1.1", "Pumpe", menge=0.0, einheit="", datei=d)))
        check(f"F1 (B1b): {d} Menge 0 + Einheit leer -> {erwartet}",
              len(f) == 1 and (f[0]["kategorie"], f[0]["stufe"]) == erwartet, str([(x["kategorie"], x["stufe"]) for x in f]))
    f = pruefe_formal(tabelle(zeile("8.1.2", "Pumpe", menge=1.0, einheit="", datei="auftrag.D86")))
    check("F1 (B1b): Auftrags-LV mit Menge 1 und leerer Einheit bleibt „Einheit fehlt“ (Stufe 1)",
          len(f) == 1 and f[0]["titel"] == "Einheit fehlt" and f[0]["stufe"] == 1)
    f = pruefe_formal(tabelle(zeile("8.1.3", "Pumpe", menge=0.0, einheit="St", datei="auftrag.D86")))
    check("F1 (B1b): Auftrags-LV mit Menge 0 und Einheit bleibt „Menge 0“ (Stufe 2)",
          len(f) == 1 and f[0]["titel"] == "Menge 0" and f[0]["stufe"] == 2)
    check("F1 (B1b): Text ohne Rechtsaussage (R7)", not VERBOTEN.search(AUFTRAG_OHNE_ME_TEXT + AUFTRAG_OHNE_ME_TITEL))
    df = tabelle(zeile("3.1", "Hydrant", menge=0.0, fmt="PDF", art_roh="Bedarfsposition ohne GB", datei="t.pdf", seite=1),
                 zeile("3.2", "Schieber", menge=0.0, datei="t.pdf", fmt="PDF", seite=1))
    f = pruefe_formal(df)
    by = {(x["pruefung"], x["positionen"][0]["oz"]): x for x in f}
    check("F2 (B1b): Bedarfsposition mit Menge 0 -> nur Nr.-5-Fund, kein „Menge 0“-Fund",
          (3, "3.1") not in by and (5, "3.1") in by, str(sorted(by)))
    check("F2 (B1b): „Menge: 0“ steht als Feldwert im Nr.-5-Fund (nichts geht verloren)",
          {"art": FELDWERT, "text": "Menge: 0"} in by[(5, "3.1")]["feldbelege"])
    check("F2 (B1b): ohne Bedarfsposition bleibt „Menge 0“ ein eigener Fund",
          (3, "3.2") in by and by[(3, "3.2")]["titel"] == "Menge 0")
    allgemein("F1/F2 (B1b)", f)


# --------------------------------------------------------------------------- Nr. 5 / 6

def test_nr5_nr6_klein():
    df = tabelle(
        zeile("1.1", "Wasserhaltung", art_roh="Bedarfsposition WithoutTotal"),                  # GAEB XML
        zeile("1.2", "Stundenlohn", fmt="PDF", art_roh="Bedarfsposition ohne GB", seite=3,
              datei="t.pdf"),                                                                   # PDF-Vermerk
        zeile("1.3", "Schieber", lang="Schieber liefern. Nur Einh.-Pr."),                       # Text
        zeile("1.4", "Baustelleneinrichtung", einheit="psch", einheit_roh="PSCH"),              # Pauschale
        zeile("1.5", "Normal"),
    )
    f = pruefe_formal(df)
    n5 = {x["positionen"][0]["oz"]: x for x in nach_nr(f, 5)}
    check("Nr. 5: drei Funde (Kennzeichen, PDF-Vermerk, Textvermerk)", sorted(n5) == ["1.1", "1.2", "1.3"], str(sorted(n5)))
    check("Nr. 5: GAEB XML <Provis> als „Kennzeichen in der Datei“, nicht als Zitat",
          n5["1.1"]["feldbelege"] == [{"art": KENNZEICHEN, "text": "<Provis>WithoutTotal</Provis>"}]
          and n5["1.1"]["belege"] == ["Wasserhaltung"])
    check("Nr. 5: PDF-Vermerk wörtlich als Zitat", n5["1.2"]["belege"] == ["Stundenlohn", "Bedarfsposition ohne GB"])
    check("Nr. 5: Textvermerk „Nur Einh.-Pr.“ wörtlich", "Nur Einh.-Pr." in n5["1.3"]["belege"])
    check("Nr. 5: Risikohinweis, Stufe 2", all(x["kategorie"] == RISIKO and x["stufe"] == 2 for x in n5.values()))
    n6 = nach_nr(f, 6)
    check("Nr. 6: Einheit psch -> Fund mit Feldwert der Original-Einheit",
          len(n6) == 1 and n6[0]["feldbelege"] == [{"art": FELDWERT, "text": "Einheit: PSCH"}]
          and n6[0]["kategorie"] == RISIKO and n6[0]["stufe"] == 2)
    allgemein("Nr. 5/6", f)
    # Negativ-Tests (E2 c, B1b): ähnliche Wörter ohne Vermerk bzw. „pauschal“ nur im Text
    neg = pruefe_formal(tabelle(
        zeile("2.1", "Bedarfsgerecht dimensionierte Leitung", lang="Einheitspreis inkl. Material"),
        zeile("2.2", "Pauschal vergütete Nebenleistung", lang="pauschal abgegolten", einheit="m"),
        zeile("2.3", "Wasserhaltung", art_roh="Normal"),
    ))
    check("Nr. 5 negativ: „Bedarfsgerecht“, „Einheitspreis“ ohne „nur“, art_roh ohne Bedarfsposition -> kein Fund",
          nach_nr(neg, 5) == [], str([x["id"] for x in nach_nr(neg, 5)]))
    check("Nr. 6 negativ: „pauschal“ im Text, Einheit m -> kein Fund (nur die Einheit psch zählt)",
          nach_nr(neg, 6) == [], str([x["id"] for x in nach_nr(neg, 6)]))


# --------------------------------------------------------------------------- nur Preise, Sortierung

def test_nur_preise_und_sortierung(cache):
    df = tabelle(zeile("1.1", "", menge=None, einheit=None), zeile("1.2", "", menge=None, einheit=None))
    check("Nur Preise: Tabelle ohne Kurztext erkannt, keine Funde",
          nur_preise(df) and pruefe_formal(df) == [] and alle_pruefungen(df) == [])
    for n in ("StBALV23040.D84", "Angebot AN24-0305.D84"):
        check(f"Nur Preise: {n} erkannt, keine Funde", nur_preise(cache[n]) and alle_pruefungen(cache[n]) == [])
    check("Nur Preise: die 5 Testdateien nicht betroffen",
          not any(nur_preise(cache[n]) for n in STUFE1))
    df = tabelle(zeile("10.1", "A", einheit="psch"), zeile("2.1", "B", menge=None), zeile("2.10", "C", einheit="psch"),
                 zeile("2.9", "D", menge=0.0))
    s = sortiere(pruefe_formal(df))
    check("Sortierung: nach Stufe, dann Rang in Stufe, dann OZ (numerisch)",
          [(x["stufe"], x["prioritaet_in_stufe"], x["positionen"][0]["oz"]) for x in s]
          == [(1, 3, "2.1"), (2, 1, "2.10"), (2, 1, "10.1"), (MENGE_0[1], 2, "2.9")],
          str([(x["stufe"], x["prioritaet_in_stufe"], x["positionen"][0]["oz"]) for x in s]))
    # erfundene Funde: Priorität schlägt OZ innerhalb derselben Stufe (F1)
    def f_(nr, stufe, prio, oz):
        return {"pruefung": nr, "stufe": stufe, "prioritaet_in_stufe": prio, "positionen": [{"oz": oz}]}
    s = sortiere([f_(1, 1, 4, "1.1"), f_(4, 1, 1, "9.9"), f_(5, 2, 2, "1.1"), f_(6, 2, 1, "5.5"), f_(3, 3, 1, "0.1")])
    check("F1: Sortierung Stufe vor Priorität vor OZ",
          [(x["pruefung"]) for x in s] == [4, 1, 6, 5, 3], str([x["pruefung"] for x in s]))
    check("F1: jede Prüfung Nr. 1–6 hat eine feste Priorität in ihrer Stufe",
          {(1, 1), (2, 1), (3, 1), (4, 1), (5, 2), (6, 2), (3, 2), (3, 4)} <= set(PRIORITAET_IN_STUFE)
          and all(sorted(v for (n, s_), v in PRIORITAET_IN_STUFE.items() if s_ == s) == list(range(1, k + 1))
                  for s, k in ((1, 7), (2, 4), (3, 5), (4, 5))))
    check("Rangtabelle (Team, 21.11.2026, 21:20): Stufe 1 Nr. 17, 4, 3, 16, 2, 15, 1; Stufe 4 Nr. 14, 3, 13, 11, 12",
          [n for (n, s_), v in sorted(PRIORITAET_IN_STUFE.items(), key=lambda x: x[1]) if s_ == 1] == [17, 4, 3, 16, 2, 15, 1]
          and [n for (n, s_), v in sorted(PRIORITAET_IN_STUFE.items(), key=lambda x: x[1]) if s_ == 4] == [14, 3, 13, 11, 12]
          and [n for (n, s_), v in sorted(PRIORITAET_IN_STUFE.items(), key=lambda x: x[1]) if s_ == 3] == [9, 10, 7, 8, 19])
    check("F2: Rang in Stufe 2 – Nr. 6 Pauschale 1, Menge 0 2, Nr. 5 Bedarfsposition 3",
          (PRIORITAET_IN_STUFE[(6, 2)], PRIORITAET_IN_STUFE[(3, 2)], PRIORITAET_IN_STUFE[(5, 2)]) == (1, 2, 3))
    check("Sortierung: OZ-Schlüssel numerisch", oz_sortkey("2.9") < oz_sortkey("2.10") < oz_sortkey("10.1"))


# --------------------------------------------------------------------------- echte Dateien

STUFE1 = ["8209.003_Leistungsverzeichnis_leer.X83", "[NUMMER_001]_leer.X83", "Leistungsverzeichnis.pdf",
          "LV_00_Roh_und_Erdauarbeiten.pdf", "501-24-01_GAEB-XML_sas.x83"]


def test_echte_dateien(cache):
    alle = []
    for n in STUFE1:
        f = alle_pruefungen(cache[n], D / n)
        alle += f
        pos = cache[n][cache[n].typ == "Position"]
        check(f"{n}: Nr. 6 = Anzahl Positionen mit Einheit psch",
              len(nach_nr(f, 6)) == (pos.einheit == "psch").sum())
        check(f"{n}: Liste sortiert nach Stufe, Rang in Stufe, dann OZ", f == sortiere(f))
    p1 = [f for f in alle if f["pruefung"] in (1, 2)]
    check("Echte Dateien: Prüfung 1/2 13 Funde (B1p: Leistungsverzeichnis.pdf −2.1.410, −4.1.200, +5.3.210)",
          len(p1) == 13, str(len(p1)))
    # Nr. 5 in 501-24-01: Kennzeichen <Provis> wörtlich in der Rohdatei (R5 für Kennzeichen)
    roh = (D / "501-24-01_GAEB-XML_sas.x83").read_text(encoding="utf-8")
    n5 = [f for f in alle if f["pruefung"] == 5 and f["positionen"][0]["datei"] == "501-24-01_GAEB-XML_sas.x83"]
    check("501-24-01: 24 Bedarfspositionen mit Kennzeichen <Provis>",
          len(n5) == 24 == roh.count("<Provis>WithoutTotal</Provis>")
          and all(b["text"] in roh for f in n5 for b in f["feldbelege"]))
    # R5: jedes Zitat wörtlich in Kurz-/Langtext oder (PDF) im Vermerk art_roh der Position
    fehlt = []
    for f in alle:
        if f["pruefung"] in (1, 2):
            continue                                  # durch test_pruefung.py abgedeckt
        for p in f["positionen"]:
            df = cache[p["datei"]]
            r = df[(df.typ == "Position") & (df.oz == p["oz"])].iloc[0]
            texte = [normalisiere_leerzeichen(x) for x in (r.kurztext, r.langtext, r.art_roh) if isinstance(x, str)]
            for b in f["belege"]:
                if not any(normalisiere_leerzeichen(b) in t for t in texte):
                    fehlt.append((f["id"], b))
    check("Echte Dateien: jedes Zitat wörtlich in der Position (R5)", not fehlt, str(fehlt[:3]))
    check("Echte Dateien: ID = Prüfung|Datei|normalisierte OZ",
          all(f["id"] == f"{f['pruefung']}|{f['positionen'][0]['datei']}|{normalisiere_oz(f['positionen'][0]['oz'])}"
              for f in alle))
    allgemein("Echte Dateien Nr. 3–6", [f for f in alle if f["pruefung"] >= 3])
    neu = []
    for n in STUFE1:
        neu += alle_pruefungen(parse(D / n), D / n)
    check("Echte Dateien: gleiche Eingabe -> gleiche Funde (neu geparst)",
          json.dumps(neu, ensure_ascii=False) == json.dumps(alle, ensure_ascii=False))
    # Nr. 3 an der einzigen Datei mit Menge 0 und fehlender Einheit
    n = "[ORT_024] LV24069.D86"
    f3 = nach_nr(alle_pruefungen(cache[n], D / n), 3)
    check(f"F1 (B1b) {n}: 38 Funde Nr. 3 „{AUFTRAG_OHNE_ME_TITEL}“, Unklarheit, Stufe 4, Rang 2 (Rangtabelle 21:20), „vormerken“",
          len(f3) == 38 and all(x["titel"] == AUFTRAG_OHNE_ME_TITEL and (x["kategorie"], x["stufe"]) == AUFTRAG_OHNE_ME
                                 and x["prioritaet_in_stufe"] == 2 and x["begruendung"] == AUFTRAG_OHNE_ME_TEXT
                                 and {b["text"] for b in x["feldbelege"]} == {"Menge: 0", "Einheit: (leer)"}
                                 for x in f3), str(len(f3)))


def test_datei_hinweis():
    check("E2: Datei-Hinweis bei Austauschphase 86 (.D86/.X86, Groß-/Kleinschreibung egal)",
          all(datei_hinweis(n) == HINWEIS_PHASE_86 for n in ("[ORT_024] LV24069.D86", "StBALV23040.D86", "x.x86")))
    check("E2: kein Datei-Hinweis bei anderen Phasen und PDF",
          all(datei_hinweis(n) is None for n in ("a.D83", "a.X83", "a.D84", "a.pdf")))


def test_s2_ergebnis(cache):
    """Jeder am Original geprüfte Fund (data/qa/s2_ergebnis.json) hat noch genau dieselben
    Zitate und Feldbelege – sonst zeigt die App ihn als ungeprüft."""
    s2 = Path("data/qa/s2_ergebnis.json")
    # Öffentliches Abgabe-Repo (Team 22.11.2026): Datei fehlt dort bewusst und steht in .gitignore. Im Arbeits-Repo bleibt Fehlen ein Fehler.
    if not s2.exists() and "data/qa/s2_ergebnis.json" in Path(".gitignore").read_text(encoding="utf-8"):
        print("ÜBERSPRUNGEN Belegprüfung: data/qa/s2_ergebnis.json ist im Abgabe-Repo bewusst nicht enthalten")
        return
    doc = json.loads(s2.read_text(encoding="utf-8"))
    aktuell, abw = {}, []
    # F2 (B1b, Team 21.11.2026): diese geprüften „Menge 0“-Funde entfallen; „Menge: 0“ steht im Nr.-5-Fund
    entfallen_f2 = {"3|LV_00_Roh_und_Erdauarbeiten.pdf|3.1.340", "3|LV_00_Roh_und_Erdauarbeiten.pdf|3.1.350"}
    # B1p (Team, 21.11.2026, F3): „bis DN 300“ ist umbrochener Kurztext, kein Langtext – Fund entfällt
    entfallen_b1p = {"1|Leistungsverzeichnis.pdf|2.1.410", "1|Leistungsverzeichnis.pdf|4.1.200"}
    # B1p3 (Team, 22.11.2026, F1/F2): Beleg stand hinter der Mengenzeile (10) bzw. in einer Sammelposition, die es nicht
    # mehr gibt (LV_13 1.2, 2.1); jeder Fall am Original geprüft (docs/bericht_B1p3.md). s2_ergebnis.json bleibt unverändert.
    entfallen_b1p |= {"9|Abgabe LV.pdf|3.1.8", "9|Leistungsverzeichnis_leer.pdf|3.1.8",
                      "7|HEM2301-2_Gesamt-LV.pdf|6.1.6", "7|HEM2301-2_Gesamt-LV.pdf|6.4.4",
                      "8|HEM2301-2_Gesamt-LV.pdf|6.1.4", "8|HEM2301-2_Gesamt-LV.pdf|6.2.1",
                      "10|LV-Ausdruck-[PROJEKT_004].pdf|4.3", "13|LV_00_Roh_und_Erdauarbeiten.pdf|3.4.89.0",
                      "13|Leistungsverzeichnis.pdf|7.1.80", "11|LV_13_ELT.pdf|1.3.2.12",
                      "7|LV_13_ELT.pdf|1.2", "8|LV_13_ELT.pdf|2.1"}
    # B1p3: Fund bleibt, der letzte Beleg stand hinter der Mengenzeile (Spezifikation Rückschlagklappe, HEM S. 127/128)
    gekuerzt_b1p3 = {"7|HEM2301-2_Gesamt-LV.pdf|6.4.1": 3}
    for e in doc["funde"]:
        datei = e["id"].split("|")[1]
        if datei not in aktuell:
            df = cache.get(datei)
            df = parse(D / datei) if df is None else df
            aktuell[datei] = {f["id"]: f for f in alle_pruefungen(df, D / datei)}
        f = aktuell[datei].get(e["id"])
        if e["id"] in entfallen_b1p:
            if f is not None:
                abw.append(e["id"])
            continue
        if e["id"] in entfallen_f2:
            n5 = aktuell[datei].get(e["id"].replace("3|", "5|", 1))
            if f is not None or n5 is None or {"art": FELDWERT, "text": "Menge: 0"} not in n5["feldbelege"]:
                abw.append(e["id"])
            continue
        if e["id"] in gekuerzt_b1p3:
            if f is None or [b["text"] for b in e["belege"]][:gekuerzt_b1p3[e["id"]]] != f["belege"]:
                abw.append(e["id"])
            continue
        if (f is None or [b["text"] for b in e["belege"]] != f["belege"]
                or ("feldbelege" in e and [b["text"] for b in e["feldbelege"]] != [b["text"] for b in f["feldbelege"]])):
            abw.append(e["id"])
    check(f"S2: alle {len(doc['funde'])} geprüften Funde stimmen mit den aktuellen Belegen überein "
          f"({len(entfallen_f2)} durch F2 entfallen, „Menge: 0“ im Nr.-5-Fund; {len(entfallen_b1p)} durch B1p/B1p3 "
          f"entfallen, {len(gekuerzt_b1p3)} durch B1p3 mit gekürztem Beleg)",
          not abw, str(abw[:3]))
    check("S2: alle Einträge „Beleg im Original gefunden“",
          all(e["ergebnis"] == "Beleg im Original gefunden" for e in doc["funde"]))


if __name__ == "__main__":
    cache = {n: parse(D / n) for n in STUFE1 + ["StBALV23040.D84", "Angebot AN24-0305.D84", "[ORT_024] LV24069.D86"]}
    test_nr3()
    test_f1_f2_b1b()
    test_nr4()
    test_nr5_nr6_klein()
    test_nur_preise_und_sortierung(cache)
    test_echte_dateien(cache)
    test_datei_hinweis()
    test_s2_ergebnis(cache)
    print(f"\n{sum(ergebnisse)} von {len(ergebnisse)} Tests bestanden")
    sys.exit(0 if all(ergebnisse) else 1)
