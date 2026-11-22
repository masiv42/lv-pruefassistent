"""
test_pruefabdeckung.py - Tests für src/pruefabdeckung.py (B1b, Nachtrag 3) mit erfundener Mini-Datei.

Die Mini-Datei ist eine selbst gebaute Tabelle wie aus parse() (keine Datei aus data/raw).
Am echten Datensatz nur eine Gegenprobe: Angebot AN24-0305.pdf druckt nur Kurztexte (B0b, Skeptiker) –
seit B1p 0 von 274 (vorher 67, L38).
Aufruf aus der Projektwurzel (uv-Befehl siehe AGENTS.md):
  python src/test_pruefabdeckung.py data/raw
Exit-Code 0 = alle Tests bestanden. Schreibt nichts.
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lv_parser import COLUMNS, parse                                     # noqa: E402
from pruefabdeckung import abdeckung, text, eingeschraenkt, OHNE_KURZTEXT, OHNE_LANGTEXT   # noqa: E402
from pruefung_formal import alle_pruefungen                                # noqa: E402

D = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/raw")
ergebnisse = []


def check(name, ok, detail=""):
    ergebnisse.append(ok)
    print(f"{'OK    ' if ok else 'FEHLER'} {name}" + (f" – {detail}" if detail and not ok else ""))


def zeile(oz, kurz, lang, typ="Position", menge=1.0, einheit="m"):
    r = {c: None for c in COLUMNS}
    r.update(datei="mini.X83", format="GAEB XML", typ=typ, oz=oz, kurztext=kurz, langtext=lang, menge=menge,
             einheit=einheit, einheit_roh=einheit, art="Normal", art_roh="")
    return r


MINI = pd.DataFrame([
    zeile("1", "Titel", "", typ="Titel"),                                         # zählt nicht
    zeile("1.1", "Rohr DN 100", "Rohr DN 100 liefern und verlegen, DN 150"),     # eigener Langtext, Fund Nr. 1
    zeile("1.2", "Rohr DN 200", ""),                                             # Langtext leer
    zeile("1.3", "Rohr DN 300", "Rohr DN 300"),                                  # Langtext = Kurztext
    zeile("1.4", "", "Nur Langtext DN 400"),                                     # ohne Kurztext
    zeile("1.5", "Schacht", "Schacht aus Beton C25/30", einheit="psch"),         # eigener Langtext
], columns=COLUMNS)


def main():
    a = abdeckung(MINI)
    nr = {e["pruefung"]: e for e in a}
    check("Mini: ein Eintrag je Prüfung Nr. 1–19, feste Reihenfolge (B2-Integration)", [e["pruefung"] for e in a] == list(range(1, 20)))
    check("Mini: Nr. 16 wie Nr. 1/2 (Kurztext und eigener Langtext), Nr. 7–15/18/19 wie Nr. 3 (Kurztext)",
          nr[16]["pruefbar"] == nr[1]["pruefbar"] and all(nr[n]["pruefbar"] == nr[3]["pruefbar"] for n in (7, 12, 15, 18, 19)))
    check("Mini: Nr. 17 „Rechenprüfung: 0 Positionen nachgerechnet, 0 Abweichungen“ (unbepreist, B1e)",
          text(nr[17]) == "Rechenprüfung: 0 Positionen nachgerechnet, 0 Abweichungen", text(nr[17]))
    check("Mini: Nr. 1/2 prüfbar in 2 von 5 (Titel zählt nicht)",
          (nr[1]["pruefbar"], nr[1]["gesamt"]) == (2, 5) and nr[1]["pruefbar"] == nr[2]["pruefbar"], str(nr[1]))
    check("Mini: Gründe Nr. 1/2 – 1 ohne Kurztext, 2 ohne eigenen Langtext",
          nr[1]["gruende"] == [(OHNE_KURZTEXT, 1), (OHNE_LANGTEXT, 2)], str(nr[1]["gruende"]))
    check("Mini: Nr. 3, 5, 6 prüfbar in 4 von 5 (übrige ohne Kurztext)",
          all((nr[n]["pruefbar"], nr[n]["gruende"]) == (4, [(OHNE_KURZTEXT, 1)]) for n in (3, 5, 6)))
    check("Mini: Nr. 4 prüfbar in allen 5 Positionen, kein Grund", (nr[4]["pruefbar"], nr[4]["gruende"]) == (5, []))
    check("Mini: Text „prüfbar in 2 von 5 Positionen; übrige 1 ohne Kurztext, 2 ohne eigenen Langtext …“",
          text(nr[1]) == f"prüfbar in 2 von 5 Positionen; übrige 1 {OHNE_KURZTEXT}, 2 {OHNE_LANGTEXT}", text(nr[1]))
    check("Mini: ohne Einschränkung kein „übrige“", text(nr[4]) == "prüfbar in 5 von 5 Positionen")
    check("Mini: eingeschränkt = alle außer Nr. 4 und 17 (Nr. 17 steht eigens im Kopf)",
          [e["pruefung"] for e in eingeschraenkt(a)] == [n for n in range(1, 20) if n not in (4, 17)])
    vorher = alle_pruefungen(MINI)
    abdeckung(MINI)
    check("Mini: Hinweis unterdrückt keinen Fund (Funde vor/nach gleich, Fund Nr. 1 zu 1.1 vorhanden)",
          alle_pruefungen(MINI) == vorher and any(f["id"] == "1|mini.X83|1.1" for f in vorher))
    check("Mini: gleiche Eingabe, gleiche Abdeckung (E14)", abdeckung(MINI) == a)
    preise = MINI.copy()
    preise["kurztext"] = ""
    check("Mini: reine Preisdatei -> nur Nr. 17 (B1e)", [e["pruefung"] for e in abdeckung(preise)] == [17])
    n = "Angebot AN24-0305.pdf"
    e = abdeckung(parse(D / n))[0]
    check(f"Gegenprobe {n}: Nr. 1 prüfbar in 0 von 274 (nur Kurztexte gedruckt; vor B1p 67, L38)",
          (e["pruefbar"], e["gesamt"]) == (0, 274), str(e))
    print(f"\n{sum(ergebnisse)}/{len(ergebnisse)} Tests bestanden")
    return 0 if all(ergebnisse) else 1


if __name__ == "__main__":
    sys.exit(main())
