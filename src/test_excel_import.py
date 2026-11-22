"""
test_excel_import.py - Tests für src/excel_import.py (Block B4, Sitzung B2). Ohne Orga-Beispiel getestet.

Alle Excel-Dateien entstehen in einem Temp-Ordner (E12 (4)); data/raw wird nur gelesen.
  1. kleine selbst erzeugte Excel-Datei: Zuordnung, Titel, Zahlen, Einheiten, Fehlermeldung, Doppellauf
  2. Rundreise je Format: parse(Original) → Excel (Spalten OZ, Kurztext, Langtext, Menge, Einheit, EP, GP) →
     lies_excel() → Spalten gleich parse() (außer datei, format, seite, art_roh; `art` nur dort, wo parse() kein
     Kennzeichen aus art_roh hatte; `titel` nur bei GAEB-XML-Positionen, weil parse() den Pfad je Format anders
     bildet: GAEB 90 Titelzeilen leer, PDF mit Summenbeträgen der Titelzeile, FS-B2-2)
  3. Prüfungen laufen auf der Excel-Tabelle (Nr. 3–6, 7–14/18, 15/16) ohne Fehler und finden die eingebauten Fälle

Aufruf aus src/:  python test_excel_import.py <data/raw>
"""
import sys
import tempfile
from pathlib import Path

import pandas as pd

from lv_parser import parse, COLUMNS, fingerprint
from excel_import import lies_excel, spalten_vorschlag, KENNZEICHNUNG, FORMAT
from pruefung_formal import pruefe_formal
from pruefung_hinweise import pruefe_hinweise
from pruefung_struktur import pruefe_struktur

D = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/raw")
ergebnisse = []


def check(name, ok, detail=""):
    ergebnisse.append(ok)
    print(f"{'OK    ' if ok else 'FEHLER'} {name}" + (f" – {detail}" if detail and not ok else ""))


def py(x):
    return None if x is None or (isinstance(x, float) and pd.isna(x)) else x


def test_klein(tmp):
    zeilen = [
        {"Pos.-Nr.": "1", "Bezeichnung": "Erdarbeiten", "Beschreibung": None, "Menge": None, "ME": None, "EP": None, "GP": None},
        {"Pos.-Nr.": "1.1", "Bezeichnung": "Baustelleneinrichtung", "Beschreibung": "einrichten, vorhalten, räumen",
         "Menge": 1, "ME": "psch", "EP": 1200.5, "GP": 1200.5},
        {"Pos.-Nr.": "1.2", "Bezeichnung": "Boden lösen", "Beschreibung": "Boden lösen, laden, abfahren",
         "Menge": "3.200,000", "ME": "m3", "EP": "12,50", "GP": "40.000,00"},
        {"Pos.-Nr.": "1.3", "Bezeichnung": "Zulage Fels", "Beschreibung": "", "Menge": None, "ME": "m3", "EP": None, "GP": None},
        {"Pos.-Nr.": None, "Bezeichnung": None, "Beschreibung": None, "Menge": None, "ME": None, "EP": None, "GP": None},
        {"Pos.-Nr.": "1.4", "Bezeichnung": "Schieber", "Beschreibung": "Fabrikat VAG oder gleichwertig",
         "Menge": 2, "ME": "Stk", "EP": None, "GP": None},
    ]
    pfad = tmp / "klein.xlsx"
    pd.DataFrame(zeilen).to_excel(pfad, index=False)
    vorschlag = spalten_vorschlag(["Pos.-Nr.", "Bezeichnung", "Beschreibung", "Menge", "ME", "EP", "GP"])
    check("Spalten-Vorschlag aus Spaltenköpfen",
          vorschlag == {"oz": "Pos.-Nr.", "kurztext": "Bezeichnung", "langtext": "Beschreibung", "menge": "Menge",
                        "einheit": "ME", "ep": "EP", "gp": "GP"}, str(vorschlag))
    df = lies_excel(pfad)
    check("Ausgabe hat genau die Spalten von parse()", list(df.columns) == COLUMNS)
    check("Leerzeile übersprungen, Titel „1“ erkannt, 4 Positionen",
          list(df.typ) == ["Titel", "Position", "Position", "Position", "Position"])
    p = df[df.typ == "Position"].set_index("oz")
    check("Zahlen: Zelle 1 → 1.0, Text „3.200,000“ → 3200.0, „12,50“ → 12.5",
          p.loc["1.1", "menge"] == 1.0 and p.loc["1.2", "menge"] == 3200.0 and p.loc["1.2", "ep"] == 12.5
          and p.loc["1.2", "gp"] == 40000.0)
    check("Einheit normalisiert wie im Parser, Rohwert bleibt", p.loc["1.2", "einheit"] == "m³"
          and p.loc["1.2", "einheit_roh"] == "m3" and p.loc["1.4", "einheit"] == "St")
    check("art wie im Parser (psch → Pauschal, Zulage)", p.loc["1.1", "art"] == "Pauschal" and p.loc["1.3", "art"] == "Zulage")
    check("titel-Pfad = übergeordneter Titel", p.loc["1.2", "titel"] == "Erdarbeiten")
    check("format „Excel“, seite leer, datei ohne Pfad", set(df.format) == {FORMAT} and df.seite.isna().all()
          and set(df.datei) == {"klein.xlsx"})
    check("Kennzeichnung „ohne Orga-Beispiel getestet“", "ohne Orga-Beispiel getestet" in KENNZEICHNUNG)
    check("Doppellauf: gleiche Prüfsumme (E14)", fingerprint(lies_excel(pfad)) == fingerprint(df))
    # Prüfungen auf der Excel-Tabelle
    nr = sorted({f["pruefung"] for f in pruefe_formal(df) + pruefe_hinweise(df) + pruefe_struktur(df)})
    check("Prüfungen laufen: Nr. 3 (1.3 ohne Menge), Nr. 6 (psch), Nr. 7 (gleichwertig), Nr. 10 (vorhalten)",
          {3, 6, 7, 10} <= set(nr), str(nr))
    # ausdrückliche Zuordnung und Fehler
    pd.DataFrame([{"A": "1.1", "B": "Text", "C": 2, "Dim": "m"}]).to_excel(tmp / "frei.xlsx", index=False)
    try:
        lies_excel(tmp / "frei.xlsx")
        check("fehlende Pflichtspalten → Fehlermeldung mit vorhandenen Spalten", False)
    except ValueError as e:
        check("fehlende Pflichtspalten → Fehlermeldung mit vorhandenen Spalten", "fehlt ['oz', 'kurztext']" in str(e)
              and "'Dim'" in str(e))
    df2 = lies_excel(tmp / "frei.xlsx", {"oz": "A", "kurztext": "B", "menge": "C", "einheit": "Dim"})
    check("ausdrückliche Zuordnung", df2.iloc[0].oz == "1.1" and df2.iloc[0].menge == 2.0 and df2.iloc[0].einheit == "m")
    try:
        lies_excel(tmp / "frei.xlsx", {"oz": "A", "kurztext": "X"})
        check("Zuordnung auf nicht vorhandene Spalte → Fehler", False)
    except ValueError:
        check("Zuordnung auf nicht vorhandene Spalte → Fehler", True)
    pd.DataFrame([{"OZ": "1", "Kurztext": "Los 1", "Typ": "Titel"}, {"OZ": "1.1", "Kurztext": "Pos", "Typ": "Position",
                  "Menge": 1, "Einheit": "St"}]).to_excel(tmp / "typ.xlsx", index=False)
    check("Spalte Typ hat Vorrang", list(lies_excel(tmp / "typ.xlsx").typ) == ["Titel", "Position"])


def rundreise(tmp, name):
    orig = parse(str(D / name))
    tab = pd.DataFrame({"OZ": orig.oz, "Kurztext": orig.kurztext, "Langtext": orig.langtext, "Menge": orig.menge,
                        "Einheit": orig.einheit_roh, "EP": orig.ep, "GP": orig.gp})
    pfad = tmp / (Path(name).stem + ".xlsx")
    tab.to_excel(pfad, index=False)
    neu = lies_excel(pfad)
    abw = []
    if len(neu) != len(orig):
        return [f"Zeilen {len(orig)} → {len(neu)}"]
    for i in range(len(orig)):
        a, b = orig.iloc[i], neu.iloc[i]
        for c in ("typ", "oz", "titel", "kurztext", "langtext", "menge", "einheit", "einheit_roh", "ep", "gp"):
            if c == "titel" and (a.format != "GAEB XML" or a.typ == "Titel"):
                continue        # titel-Pfad baut parse() je Format anders (FS-B2-2, B2-L8); Import folgt GAEB XML
            x, y = py(a[c]), py(b[c])
            if a.typ == "Titel" and c in ("menge", "einheit", "einheit_roh", "ep", "gp"):
                continue
            if c in ("einheit", "einheit_roh", "kurztext", "langtext", "titel"):
                x, y = x or "", y or ""
            if x != y:
                abw.append(f"{a.oz} {c}: {x!r} → {y!r}")
        if a.typ == "Position" and not py(a.art_roh) and a.art != b.art:
            abw.append(f"{a.oz} art: {a.art!r} → {b.art!r}")
    return abw


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        test_klein(tmp)
        for name in ("GAEB-[PROJEKT_004].X83", "8209.003_Leistungsverzeichnis_leer.D83", "LV-Schachtbauwerk.pdf",
                     "Abgabe LV.pdf"):
            abw = rundreise(tmp, name)
            check(f"Rundreise parse() → Excel → lies_excel(): {name}", not abw, f"{len(abw)} Abweichungen: {abw[:4]}")
    print(f"\n{sum(ergebnisse)}/{len(ergebnisse)} Tests bestanden")
    sys.exit(0 if all(ergebnisse) else 1)
