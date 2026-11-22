"""
test_bericht.py - Tests für den Risikobericht-Export (src/bericht.py, P3).

Aufruf aus der Projektwurzel (uv-Befehl siehe AGENTS.md):
  python src/test_bericht.py data/raw
Exit-Code 0 = alle Tests bestanden.
"""
import hashlib
import re
import io
import sys
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.utils import get_column_letter

import bericht_kalkulator as K

from lv_parser import parse, fingerprint
from pruefung_formal import sortiere, HINWEIS_PHASE_86
from bericht import (pruefe_lv, risikobericht, dateiname, r7_verstoesse, SPALTEN, SCHLUSSSATZ,
                     NUR_PREISE_TEXT, ENTSCHEIDUNGEN, lade_s2, zeit_text, ki_liste, ki_spalten,
                     ki_warnhinweis, KI_WARNHINWEIS, KI_LISTE_HINWEIS, KI_ENTWARNEND, RANG_EXPORT,
                     BELEG_STATUS, DIRTY_WARNUNG, STUFEN)

D = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/raw")
BERLIN = ZoneInfo("Europe/Berlin")
T1, T2 = datetime(2026, 11, 21, 9, 0, tzinfo=BERLIN), datetime(2026, 11, 21, 17, 30, tzinfo=BERLIN)
ergebnisse = []
ENT = get_column_letter(SPALTEN.index("Entscheidung Kalkulator") + 1)


def check(name, ok, detail=""):
    ergebnisse.append(ok)
    print(f"{'OK    ' if ok else 'FEHLER'} {name}" + (f" – {detail}" if detail and not ok else ""))


def oeffne(daten):
    return load_workbook(io.BytesIO(daten))


def werte(ws):
    return [[c.value for c in zeile] for zeile in ws.iter_rows()]


def alle_texte(wb):
    return [c.value for ws in wb.worksheets for zeile in ws.iter_rows() for c in zeile if isinstance(c.value, str)]


def uebersicht(wb):
    return {zeile[0]: zeile[1] for zeile in werte(wb["Übersicht"]) if zeile[0] is not None}


def test_lv00():
    n = "LV_00_Roh_und_Erdauarbeiten.pdf"
    funde, texte, info = pruefe_lv(D / n)
    daten = risikobericht(n, funde, texte, info, zeitpunkt=T1, commit="test")
    wb = oeffne(daten)
    ws = wb["Funde"]
    zeilen = werte(ws)
    check("LV_00: Kalkulatorsicht vorn, dann „Übersicht“, „Funde“, „Legende“ (B1r), „Nachtrag und Streitpunkte“ (M2b), "
          "„KI-Vorschläge“ (M2)",
          wb.sheetnames == K.BLAETTER + ["Übersicht", "Funde", "Legende", "Nachtrag und Streitpunkte", "KI-Vorschläge"]
          and wb.active.title == "Zusammenfassung", str(wb.sheetnames))
    check("LV_00: Kopfzeile wie vorgegeben", zeilen[0] == SPALTEN, str(zeilen[0]))
    # B1p3: 131 → 132 (neu Nr. 3 an 1.4.7 und Nr. 16 an 3.1.280/330, entfällt Nr. 13 an 3.4.89.0); 268 → 269 Positionen
    check("LV_00: Zeilen im Blatt „Funde“ = Funde in der App (132 nach B1p3; Nr. 1–6, 17: 69)",
          len(zeilen) - 1 == len(funde) == 132 and sum(f["pruefung"] in (1, 2, 3, 4, 5, 6, 17) for f in funde) == 69,
          f"{len(zeilen) - 1} Zeilen, {len(funde)} Funde")
    check("LV_00: Sortierung wie in der App (Fund-ID-Reihenfolge)",
          [z[SPALTEN.index("Fund-ID")] for z in zeilen[1:]] == [f["id"] for f in sortiere(funde)])
    check("LV_00: Kopfzeile fixiert, Autofilter über alle Spalten",
          ws.freeze_panes == "A2" and ws.auto_filter.ref == f"A1:{get_column_letter(len(SPALTEN))}{len(funde) + 1}", f"{ws.freeze_panes} {ws.auto_filter.ref}")
    dv = ws.data_validations.dataValidation
    check("LV_00: Auswahlliste „Entscheidung Kalkulator“ (bestätigt / verworfen / Rückfrage stellen)",
          len(dv) == 1 and dv[0].formula1 == '"' + ",".join(ENTSCHEIDUNGEN) + '"'
          and str(dv[0].sqref) == f"{ENT}2:{ENT}{len(funde) + 1}", f"{[(d.formula1, str(d.sqref)) for d in dv]}")
    check("LV_00: Entscheidung und Notiz leer",
          all(z[SPALTEN.index("Entscheidung Kalkulator")] is None and z[SPALTEN.index("Notiz")] is None for z in zeilen[1:]))
    check("LV_00: keine Formelzelle im Bericht",
          all(c.data_type != "f" for w in wb.worksheets for r in w.iter_rows() for c in r))
    seite = {z[SPALTEN.index("Fund-ID")]: z[SPALTEN.index("Fundstelle (Seite)")] for z in zeilen[1:]}
    check("LV_00: Fundstelle 3.1.180 = „S. 29“", seite.get("2|LV_00_Roh_und_Erdauarbeiten.pdf|3.1.180") == "S. 29")
    ue = uebersicht(wb)
    check("LV_00: Übersicht mit Datei, Prüfsumme, Zeitpunkt, Commit, Positionen",
          ue["LV-Datei"] == n and ue["Prüfsumme (fingerprint)"] == fingerprint(parse(D / n))
          and ue["Zeitpunkt der Prüfung"] == "2026-11-21 09:00 MEZ" and ue["Git-Commit des Tools"] == "test"
          and ue["Anzahl Positionen"] == info["positionen"] == 269)
    prio = sum(v for k, v in ue.items() if k.startswith("Funde Stufe "))
    kat = sum(v for k, v in ue.items() if k.startswith("Funde ") and not k.startswith("Funde Stufe")
              and k != "Funde gesamt")
    check("LV_00: Funde je Stufe und je Kategorie ergeben je 132", prio == kat == ue["Funde gesamt"] == 132,
          f"{prio}/{kat}/{ue['Funde gesamt']}")
    check("F4: Übersicht „Funde Stufe 1 (Fehlerprüfung)“ … „Funde Stufe 4 (Unklarheit)“ und Sortierhinweis",
          all(k in ue for k in ("Funde Stufe 1 (Fehlerprüfung)", "Funde Stufe 2 (Kalkulationsrisiko)",
                                "Funde Stufe 3 (mögliches Nachtragspotenzial)", "Funde Stufe 4 (Unklarheit)"))
          and ue["Sortierung"] == "Stufe, dann Rang in Stufe, dann OZ")
    check("B1a L24: Prüfstand in der Übersicht (Versionen, Prompt-Version, SHA-256 der Datei)",
          ue["SHA-256 der geprüften Datei"] == hashlib.sha256((D / n).read_bytes()).hexdigest()
          and "pdfplumber" in ue["Bibliotheksversionen"] and ue["Prompt-Version (KI)"] == "P4-v2")
    st_sp, pr_sp = SPALTEN.index("Stufe"), SPALTEN.index(RANG_EXPORT)
    check("B1r: Spalten „Stufe“ (Text) und Rang mit Erklärung ganz hinten (keine Spalte „Priorität“), Sortierung Stufe, Rang",
          SPALTEN[-1] == RANG_EXPORT and
          "Priorität" not in SPALTEN and
          [(z[st_sp], z[pr_sp]) for z in zeilen[1:]] == sorted((z[st_sp], z[pr_sp]) for z in zeilen[1:])
          and {z[pr_sp] for z in zeilen[1:]} <= set(range(1, 8)))
    check("B1b: Übersicht nennt die Prüfabdeckung je Prüfung Nr. 1–6 („prüfbar in N von M Positionen“)",
          all(any(k.startswith(f"Prüfabdeckung Nr. {nr} ") and str(v).startswith("prüfbar in ") for k, v in ue.items())
              for nr in range(1, 7)) and "Prüfabdeckung" in ue)
    check("LV_00: fester Satz in der Übersicht", SCHLUSSSATZ in ue)
    check("LV_00: R7 – keine verbotenen Begriffe im Export", not r7_verstoesse(alle_texte(wb)),
          str(r7_verstoesse(alle_texte(wb))[:3]))
    # Wiederholbarkeit: zweiter Export (anderer Zeitpunkt, neu geparst) -> Blatt „Funde“ identisch
    funde2, texte2, info2 = pruefe_lv(D / n)
    wb2 = oeffne(risikobericht(n, funde2, texte2, info2, zeitpunkt=T2, commit="test"))
    check("Wiederholbarkeit: Blatt „Funde“ bei zweimal Export inhaltlich identisch",
          werte(wb2["Funde"]) == zeilen)
    check("Wiederholbarkeit (E14): Kalkulatorsicht bei zweimal Export identisch",
          all(werte(wb2[b]) == werte(wb[b]) for b in K.BLAETTER))
    u1, u2 = uebersicht(wb), uebersicht(wb2)
    check("Wiederholbarkeit: Übersicht unterscheidet sich nur im Zeitpunkt",
          [k for k in u1 if u1[k] != u2.get(k)] == ["Zeitpunkt der Prüfung"])


def test_preise_und_phase86():
    n = "StBALV23040.D84"
    funde, texte, info = pruefe_lv(D / n)
    wb = oeffne(risikobericht(n, funde, texte, info, zeitpunkt=T1, commit="test"))
    ue = uebersicht(wb)
    check("Nur Preise: Bericht nur mit Übersicht und Hinweis",
          wb.sheetnames == ["Übersicht", "Legende"] and ue.get("Datei-Hinweise") == NUR_PREISE_TEXT
          and ue["Funde gesamt"] == 0 and SCHLUSSSATZ in ue, str(ue))
    n = "[ORT_024] LV24069.D86"
    funde, texte, info = pruefe_lv(D / n)
    wb = oeffne(risikobericht(n, funde, texte, info, zeitpunkt=T1, commit="test"))
    check("Austauschphase 86: Datei-Hinweis in der Übersicht, kein Fund unterdrückt",
          uebersicht(wb).get("Datei-Hinweise") == HINWEIS_PHASE_86 and wb["Funde"].max_row - 1 == len(funde) == 103
          and sum(f["pruefung"] <= 6 for f in funde) == 54)
    check("R7 – keine verbotenen Begriffe im Export (D86)", not r7_verstoesse(alle_texte(wb)))


def test_formel_und_text():
    f = {"id": "1|t.X83|1.1", "pruefung": 1, "kategorie": "möglicher Widerspruch", "titel": "=Titel",
         "positionen": [{"datei": "t.X83", "oz": "1.1", "seite": None}], "belege": ["=SUMME(A1:A9)", "+1-2"],
         "feldbelege": [{"art": "Feldwert", "text": "=HYPERLINK(\"x\")"}], "begruendung": "=1+1",
         "stufe": 1, "stufe_begruendung": "", "prioritaet_in_stufe": 4, "rueckfrage": None, "status": "offen"}
    texte = {f["id"]: [{"oz": "1.1", "kurztext": "=A1\x07", "langtext": ""}]}
    info = {"format": "GAEB XML", "positionen": 1, "nur_preise": False, "fingerprint": "=abc", "hinweise": []}
    wb = oeffne(risikobericht("=t.X83", [f], texte, info, s2={}, zeitpunkt=T1, commit="test"))
    zellen = [c for w in wb.worksheets for r in w.iter_rows() for c in r if c.value is not None]
    check("Texte mit „=“ bleiben Text, keine Formel", all(c.data_type != "f" for c in zellen)
          and "=SUMME(A1:A9)" in wb["Funde"][f"{get_column_letter(SPALTEN.index('Zitat/Beleg') + 1)}2"].value and uebersicht(wb)["LV-Datei"] == "=t.X83")
    check("Steuerzeichen werden entfernt", wb["Funde"][f"{get_column_letter(SPALTEN.index('Kurztext') + 1)}2"].value == "=A1")


def test_alle_stufe1_r7():
    s2 = lade_s2()[0]
    treffer = []
    for n in ["8209.003_Leistungsverzeichnis_leer.X83", "[NUMMER_001]_leer.X83", "Leistungsverzeichnis.pdf",
              "501-24-01_GAEB-XML_sas.x83"]:
        funde, texte, info = pruefe_lv(D / n)
        wb = oeffne(risikobericht(n, funde, texte, info, s2=s2, zeitpunkt=T1, commit="test"))
        treffer += [(n, t[:60]) for t in r7_verstoesse(alle_texte(wb))]
        if n == "8209.003_Leistungsverzeichnis_leer.X83":
            st = {z[SPALTEN.index("Fund-ID")]: z[SPALTEN.index("Beleg-Status")] for z in werte(wb["Funde"])[1:]}
            # Öffentliches Abgabe-Repo (Team 22.11.2026): Datei fehlt dort bewusst und steht in .gitignore. Im Arbeits-Repo bleibt Fehlen ein Fehler.
            if not s2 and "data/qa/s2_ergebnis.json" in (Path(__file__).resolve().parent.parent / ".gitignore").read_text(encoding="utf-8"):
                print("ÜBERSPRUNGEN Beleg-Status 05.01.4: data/qa/s2_ergebnis.json ist im Abgabe-Repo bewusst nicht enthalten")
            else:
                check("Beleg-Status aus S2: 05.01.4 „Zitat wörtlich im Original bestätigt …“ (B1r)",
                      st.get("1|8209.003_Leistungsverzeichnis_leer.X83|5.1.4") == BELEG_STATUS["geprüft"])
    check("R7 – keine verbotenen Begriffe in den Exporten der übrigen Testdateien", not treffer, str(treffer[:3]))


def test_p3b():
    n = "LV_00_Roh_und_Erdauarbeiten.pdf"
    funde, texte, info = pruefe_lv(D / n)
    funde = sortiere(funde)
    gesetzt = {funde[0]["id"]: "bestätigt", funde[1]["id"]: "verworfen", funde[2]["id"]: "Rückfrage stellen",
               funde[3]["id"]: "offen"}
    mit_status = [dict(f, status=gesetzt.get(f["id"], "offen")) for f in funde]
    wb = oeffne(risikobericht(n, mit_status, texte, info, zeitpunkt=T1, commit="test"))
    ent = {z[SPALTEN.index("Fund-ID")]: z[SPALTEN.index("Entscheidung Kalkulator")] for z in werte(wb["Funde"])[1:]}
    check("P3b A1: Entscheidungen aus der App vorausgefüllt (bestätigt / verworfen / Rückfrage stellen)",
          [ent[funde[i]["id"]] for i in range(3)] == ["bestätigt", "verworfen", "Rückfrage stellen"])
    check("P3b A1: „offen“ bleibt leer", ent[funde[3]["id"]] is None and ent[funde[10]["id"]] is None)
    dv = wb["Funde"].data_validations.dataValidation
    check("P3b A1: Auswahlliste bleibt, Werte in Excel änderbar", len(dv) == 1 and f"{ENT}2" in str(dv[0].sqref))
    check("P3b A2: Zeitzone Winter „MEZ“, Sommer „MESZ“",
          zeit_text(T1) == "2026-11-21 09:00 MEZ"
          and zeit_text(datetime(2026, 7, 1, 12, 0, tzinfo=BERLIN)) == "2026-07-01 12:00 MESZ")
    check("P3b A2: andere Zone mit Kürzel oder UTC-Versatz",
          zeit_text(datetime(2026, 11, 21, 9, 0, tzinfo=ZoneInfo("UTC"))) == "2026-11-21 09:00 UTC"
          and zeit_text(datetime(2026, 11, 21, 9, 0, tzinfo=ZoneInfo("Asia/Kolkata"))) == "2026-11-21 09:00 IST")
    check("P3b A2: Zeit ohne Zone bekommt die lokale Zone", len(zeit_text(datetime(2026, 11, 21, 9, 0)).split()) == 3)


def test_dateiname():
    check("Dateiname Risikobericht_<LV-Dateiname>_<JJJJ-MM-TT>.xlsx",
          dateiname("LV_00_Roh_und_Erdauarbeiten.pdf", T1) == "Risikobericht_LV_00_Roh_und_Erdauarbeiten_2026-11-21.xlsx"
          and dateiname("[ORT_024] LV24069.D86", T1) == "Risikobericht_[ORT_024] LV24069_2026-11-21.xlsx")


def ki_vorschlag(einordnung):
    return {"status": "KI-Vorschlag gültig", "einordnung": einordnung, "begruendung": "B", "rueckfrage": "R",
            "zitat_kurztext": "K", "zitat_langtext": "L", "zitat_status": "beide Zitate im Text gefunden",
            "modell": "m", "prompt_version": "P4-v2", "quelle": "Cache"}


def test_abdeckung_angebot():
    """B1b Nachtrag 3 / B1p: Angebot AN24-0305.pdf druckt nur Kurztexte – Nr. 1/2 „prüfbar in 0 von 274“
    (vor B1p 67: Fußzeilen, Zusammenstellung und umbrochene Kurztexte zählten als Langtext, L38)."""
    n = "Angebot AN24-0305.pdf"
    funde, texte, info = pruefe_lv(D / n)
    ue = uebersicht(oeffne(risikobericht(n, funde, texte, info, zeitpunkt=T1, commit="test")))
    k1 = next(k for k in ue if k.startswith("Prüfabdeckung Nr. 1 "))
    k2 = next(k for k in ue if k.startswith("Prüfabdeckung Nr. 2 "))
    check(f"B1p: {n} Übersicht Nr. 1/2 „prüfbar in 0 von 274 Positionen; übrige 274 ohne eigenen Langtext …“",
          ue[k1] == ue[k2] and ue[k1].startswith("prüfbar in 0 von 274 Positionen; übrige 274 ohne eigenen Langtext"),
          ue[k1])
    check(f"B1b: {n} Prüfabdeckung ändert die Funde nicht (Funde gesamt = Funde der Prüfung)",
          ue["Funde gesamt"] == len(funde))


def test_b1r():
    """B1r (Team, 21.11.2026, L43): Bericht für Kalkulatoren lesbar. Werte am Original: docs/bericht_B1r.md."""
    n = "Abgabe LV.pdf"
    funde, texte, info = pruefe_lv(D / n)
    wb = oeffne(risikobericht(n, funde, texte, info, zeitpunkt=T1, commit="abc1234"))
    ws = wb["Funde"]
    kopf = [c.value for c in ws[1]]
    check("B1r: Überschriften vollständig lesbar (Umbruch, Spaltenbreite ≥ halbe Länge, Kopfzeile 3 Zeilen hoch)",
          all(ws.cell(row=1, column=j).alignment.wrap_text and
              ws.column_dimensions[get_column_letter(j)].width * 3 >= len(h) for j, h in enumerate(kopf, start=1))
          and ws.row_dimensions[1].height >= 45)
    check("B1r: erste Spalte „Nr.“ = laufende Nummer 1 … n in Sortierreihenfolge",
          kopf[0] == "Nr." and [z[0] for z in werte(ws)[1:]] == list(range(1, len(funde) + 1)))
    st = SPALTEN.index("Stufe")
    check("B1r: Stufe als Text („1 – Fehlerprüfung“ …)",
          all(isinstance(z[st], str) and z[st][:4] in {f"{s} – " for s in STUFEN} for z in werte(ws)[1:]))
    check("B1r: Blatt „Legende“ erklärt jede Spalte, die Stufen und den Beleg-Status",
          set(SPALTEN) <= {z[0] for z in werte(wb["Legende"])}
          and all(f"{s} – {STUFEN[s]}" in {z[0] for z in werte(wb["Legende"])} for s in STUFEN)
          and BELEG_STATUS["geprüft"] in {z[0] for z in werte(wb["Legende"])})
    check("B1r: kein Dateipfad („data/“) in einer Zelle", not [x for x in alle_texte(wb) if "data/" in x])
    df = parse(D / n)
    pos = df[df.typ == "Position"]
    idx = {s: SPALTEN.index(s) for s in ("OZ", "Menge", "Einheit", "EP (€)", "GP (€)")}
    abw = []
    for z in werte(ws)[1:]:
        r = pos[pos.oz == z[idx["OZ"]].split(", ")[0]].iloc[0]
        for s, feld in (("Menge", "menge"), ("EP (€)", "ep"), ("GP (€)", "gp")):
            soll = getattr(r, feld)
            soll = "" if soll is None or soll != soll else float(soll)
            ist = "" if z[idx[s]] is None else z[idx[s]]
            if soll != ist:
                abw.append((z[idx["OZ"]], s, soll, ist))
    check(f"B1r: {n} Menge, EP und GP je Fund gleich parse() ({len(funde)} Funde)", not abw and len(funde) > 0, str(abw[:3]))
    ue = werte(wb["Übersicht"])
    check("B1r: Übersicht zweigeteilt („Für den Kalkulator“ vor „Prüfstand (technisch)“), Erklärung je Zeile",
          [z[0] for z in ue].index("Für den Kalkulator") < [z[0] for z in ue].index("Prüfstand (technisch)")
          and all(z[2] for z in ue if z[0] in ("LV-Datei", "Prüfsumme (fingerprint)", "SHA-256 der geprüften Datei",
                                               "Git-Commit des Tools", "Funde gesamt")))
    erkl = {z[0]: z[2] for z in ue if z[0]}
    check("B1r: Erklärungen passen zur Zeile („Funde gesamt“ ≠ „Funde dieser Kategorie“)",
          erkl["Funde gesamt"].startswith("alle Funde") and erkl["Funde Risikohinweis"] == "Funde dieser Kategorie")
    check("B1e: Übersicht „Rechenprüfung: 248 Positionen nachgerechnet, 0 Abweichungen“ (Abgabe LV.pdf)",
          erkl and any(z[0].startswith("Prüfabdeckung Nr. 17") and z[1] == "Rechenprüfung: 248 Positionen nachgerechnet, "
                       "0 Abweichungen" for z in ue if z[0]), str([z[:2] for z in ue if z[0] and "17" in str(z[0])]))
    pr = SPALTEN.index("Prüfer")
    from bericht import PRUEFER as bericht_PRUEFER
    check("B1e: Spalte „Prüfer“ je Fund gefüllt (Nr. 2 → Widerspruch, Nr. 6 → Mengen)",
          all(z[pr] for z in werte(ws)[1:]) and {(z[SPALTEN.index("Prüfung")].split(" – ")[0], z[pr]) for z in werte(ws)[1:]}
          == {(z[SPALTEN.index("Prüfung")].split(" – ")[0], bericht_PRUEFER[int(z[SPALTEN.index("Prüfung")].split(" – ")[0])])
              for z in werte(ws)[1:]})
    check("B1r: ohne „-dirty“ keine Warnzeile", "WARNUNG" not in [z[0] for z in ue])
    ue2 = werte(oeffne(risikobericht(n, funde, texte, info, zeitpunkt=T1, commit="abc1234-dirty"))["Übersicht"])
    check("B1r: bei „-dirty“ Warnzeile oben „Prüfstand nicht committet – nicht für Abgabe oder Demo verwenden“",
          ue2[1][0] == "WARNUNG" and ue2[1][1] == DIRTY_WARNUNG
          and DIRTY_WARNUNG == "Prüfstand nicht committet – nicht für Abgabe oder Demo verwenden")
    check("B1r: Beleg-Status ohne „Person“ oder „Mensch“ (Kern 3)",
          not [v for v in BELEG_STATUS.values() if re.search(r"Person|Mensch", v)])
    zweimal = oeffne(risikobericht(n, funde, texte, info, zeitpunkt=T1, commit="abc1234"))
    check("B1r: gleiche Eingabe, gleiches Blatt „Funde“ (E14)", werte(zweimal["Funde"]) == werte(ws))


def test_e13():
    """B0b.6 / Leitplanke E13: die KI darf nie entwarnen."""
    funde, texte, info = pruefe_lv(D / "8209.003_Leistungsverzeichnis_leer.X83")
    nr1 = [f for f in funde if f["pruefung"] in (1, 2)]
    andere = next(f for f in funde if f["pruefung"] not in (1, 2))
    check("E13: Testdatei hat Funde Nr. 1/2 und andere Funde", len(nr1) >= 2 and andere is not None)
    a, b = nr1[0], nr1[1]
    for e in KI_ENTWARNEND:
        ki = {a["id"]: ki_vorschlag(e), b["id"]: ki_vorschlag("echter Widerspruch")}
        check(f"E13: Fundliste zeigt bei „{e}“ nur „{KI_LISTE_HINWEIS}“", ki_liste(a, ki) == KI_LISTE_HINWEIS)
        check(f"E13: Warnhinweis bei „{e}“ (Detail und Export)", ki_warnhinweis(ki[a["id"]]) == KI_WARNHINWEIS
              and ki_spalten(a, ki)[2] == KI_WARNHINWEIS)
        check(f"E13: Export behält bei „{e}“ alle KI-Spalten", ki_spalten(a, ki)[0] == f"KI-Vorschlag: {e}"
              and ki_spalten(a, ki)[3:] == ["B", "beide Zitate im Text gefunden: „K“ / „L“", "R", "m", "P4-v2"])
        check(f"L25: Export nennt bei „{e}“ die KI-Quelle", ki_spalten(a, ki)[1] == "Cache")
        check("E13: „echter Widerspruch“ darf in der Liste stehen, ohne Warnhinweis",
              ki_liste(b, ki) == "KI-Vorschlag: echter Widerspruch" and ki_spalten(b, ki)[2] == "")
        ohne = risikobericht("x.X83", funde, texte, info, zeitpunkt=T1, commit="c")
        mit = risikobericht("x.X83", funde, texte, info, zeitpunkt=T1, commit="c", ki=ki)
        z0, z1 = werte(oeffne(ohne)["Funde"]), werte(oeffne(mit)["Funde"])
        fest = [SPALTEN.index(s) for s in ("Fund-ID", "Stufe", RANG_EXPORT, "Kategorie", "Prüfung", "OZ")]
        check(f"E13: KI-Vorschlag „{e}“ ändert weder Reihenfolge noch Stufe, Rang oder Kategorie im Export",
              [[r[i] for i in fest] for r in z0] == [[r[i] for i in fest] for r in z1])
        zeile = next(r for r in z1[1:] if r[SPALTEN.index("Fund-ID")] == a["id"])
        check(f"E13: Export-Spalte „KI-Warnhinweis“ gefüllt bei „{e}“", zeile[SPALTEN.index("KI-Warnhinweis")] == KI_WARNHINWEIS)
    check("E13: kein Warnhinweis ohne KI-Vorschlag und bei anderen Prüfungen",
          ki_warnhinweis(None) == "" and ki_spalten(andere, {})[2] == "" and ki_liste(andere, {}) == "")
    check("L25: ohne KI-Ergebnis steht „noch nicht KI-geprüft“ auch in der Spalte KI-Quelle",
          ki_spalten(a, {})[:2] == ["noch nicht KI-geprüft", "noch nicht KI-geprüft"])
    api = dict(ki_vorschlag("echter Widerspruch"), quelle="API")
    check("L25: KI-Quelle „API“ wird übernommen", ki_spalten(a, {a["id"]: api})[1] == "API")
    check("B1r: Warnhinweis ohne Dateipfad, Wortlaut des Teams",
          KI_WARNHINWEIS == "Messung vom 21.11.: bei echten Widersprüchen nicht zuverlässig – bitte selbst prüfen.")
    check("R7 – Warnhinweis ohne verbotene Begriffe", not r7_verstoesse([KI_WARNHINWEIS, KI_LISTE_HINWEIS]))


def test_kalkulator():
    """Kalkulatorsicht (22.11.2026): Nr. 1–15, jede Fundstelle einmal, Gruppen vollständig, nichts verändert."""
    for n in ("LV_00_Roh_und_Erdauarbeiten.pdf", "8209.003_Leistungsverzeichnis_leer.X83", "[ORT_024] LV24069.D86"):
        funde, texte, info = pruefe_lv(D / n)
        vorher = [dict(f) for f in funde]
        wb = oeffne(risikobericht(n, funde, texte, info, zeitpunkt=T1, commit="test"))
        check(f"{n}: Funde unverändert (Stufe, Kategorie, Rang, Belege)", funde == vorher)
        soll = [f["id"] for f in sortiere(funde) if f["pruefung"] <= 15]
        det = werte(wb["Risiken je Position"])
        kopf = det[0]
        ids = [z[kopf.index("Fund-ID")] for z in det[1:]]
        check(f"{n}: „Risiken je Position“ = jede Fundstelle Nr. 1–15 genau einmal, Sortierung wie App",
              ids == soll, f"{len(ids)} / {len(soll)}")
        neu = [wb[b] for b in K.BLAETTER]
        texte_neu = [c for w in neu for r in w.iter_rows(values_only=True) for c in r if isinstance(c, str)]
        check(f"{n}: keine Fund-ID der Prüfungen Nr. 16–19 in der Kalkulatorsicht",
              not any(re.match(r"(1[6-9])\|", t) for t in texte_neu))
        reg = werte(wb["Risikoregister"])
        anz = sum(z[reg[0].index("Anzahl Fundstellen")] for z in reg[1:])
        check(f"{n}: Risikoregister fasst alle Fundstellen zusammen (Summe Anzahl = {len(soll)})", anz == len(soll),
              str(anz))
        by_id = {f["id"]: f for f in funde}
        st = kopf.index("Stufe")
        ka = kopf.index("Kategorie")
        check(f"{n}: Stufe und Kategorie je Fundstelle wie im Fund",
              all(z[st] == f"{by_id[z[kopf.index('Fund-ID')]]['stufe']} – {STUFEN[by_id[z[kopf.index('Fund-ID')]]['stufe']]}"
                  and z[ka] == by_id[z[kopf.index("Fund-ID")]]["kategorie"] for z in det[1:]))
        og = kopf.index("Originaltext (wörtlich aus dem LV)")
        check(f"{n}: Originaltext = wörtliche Belege des Funds (R5)",
              all(z[og] == "\n".join(f"„{b}“" for b in by_id[z[kopf.index('Fund-ID')]]["belege"]) for z in det[1:]))
        check(f"{n}: R7 – keine verbotenen Begriffe in der Kalkulatorsicht", not r7_verstoesse(texte_neu),
              str(r7_verstoesse(texte_neu)[:3]))
        check(f"{n}: keine KI-Angabe in der Kalkulatorsicht (E13)", not any("KI-" in t for t in texte_neu))
        check(f"{n}: keine Formelzelle", all(c.data_type != "f" for w in neu for r in w.iter_rows() for c in r))
        zus = {z[0]: z[1] for z in werte(wb["Zusammenfassung"]) if z[0] is not None}
        check(f"{n}: Zusammenfassung nennt Funde im Bericht und Nr. 16–19 getrennt",
              zus["Funde in diesem Bericht"] == len(soll)
              and zus.get("Prüfungen Nr. 16–19", 0) == sum(f["pruefung"] > 15 for f in funde)
              and SCHLUSSSATZ in zus)
        fr = werte(wb["Bieterfragen"])
        if n.endswith(".D86"):
            check(f"{n}: Auftrags-LV – keine Bieterfragen, mit Hinweis",
                  len(fr) == 3 and fr[2][3] == "Auftrags-LV – keine Bieterfragen", str(fr[2:]))
        else:
            check(f"{n}: Bieterfragen nur zu Funden mit Rückfrage-Empfehlung, mit Beleg",
                  len(fr) > 2 and all(r[4] for r in fr[2:]))
    funde, texte, info = pruefe_lv(D / "StBALV23040.D84")
    wb = oeffne(risikobericht("StBALV23040.D84", funde, texte, info, zeitpunkt=T1, commit="test"))
    check("Reine Preisdatei: keine Kalkulatorsicht", wb.sheetnames == ["Übersicht", "Legende"], str(wb.sheetnames))


if __name__ == "__main__":
    test_kalkulator()
    test_lv00()
    test_preise_und_phase86()
    test_formel_und_text()
    test_alle_stufe1_r7()
    test_dateiname()
    test_p3b()
    test_e13()
    test_abdeckung_angebot()
    test_b1r()
    print(f"\n{sum(ergebnisse)} von {len(ergebnisse)} Tests bestanden")
    sys.exit(0 if all(ergebnisse) else 1)
