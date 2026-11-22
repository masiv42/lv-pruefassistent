"""
test_pruefung_rechnung.py - Tests für Nr. 17 Rechenprüfung (src/pruefung_rechnung.py, Block B1e).

Erfundene Mini-Datei (Tabelle wie aus parse()) mit einer Abweichung; am Datensatz nur Messung: 1.242 nachgerechnete
Positionen in 5 Dateien, 0 Abweichungen (Erhebung 21.11.2026, Skeptiker: docs/bericht_B1e.md).
Aufruf aus der Projektwurzel (uv-Befehl siehe AGENTS.md):
  python src/test_pruefung_rechnung.py data/raw
Exit-Code 0 = alle Tests bestanden. Schreibt nichts.
"""
import json
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lv_parser import COLUMNS, parse                                         # noqa: E402
from pruefung_rechnung import pruefe_rechnung, abdeckung_eintrag, toleranz, de, de_ep   # noqa: E402
from pruefung_formal import alle_pruefungen, sortiere                          # noqa: E402
from pruefabdeckung import abdeckung, text                                     # noqa: E402
import bericht                                                                 # noqa: E402

D = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/raw")
ergebnisse = []
VERBOTEN = re.compile(r"Anspruch|berechtigt|durchsetzbar|§")


def check(name, ok, detail=""):
    ergebnisse.append(ok)
    print(f"{'OK    ' if ok else 'FEHLER'} {name}" + (f" – {detail}" if detail and not ok else ""))


def zeile(oz, kurz, menge, ep, gp, einheit="m", datei="mini.X84"):
    r = {c: None for c in COLUMNS}
    r.update(datei=datei, format="GAEB XML", typ="Position", oz=oz, kurztext=kurz, langtext=kurz, menge=menge,
             einheit=einheit, einheit_roh=einheit, ep=ep, gp=gp, art="Normal", art_roh="")
    return r


MINI = pd.DataFrame([
    zeile("1.1", "Rohr liefern", 12.0, 45.5, 546.0),                  # stimmt
    zeile("1.2", "Schacht setzen", 3.0, 1200.0, 3800.0),              # Abweichung: 3 × 1200 = 3600
    zeile("1.3", "Kies einbauen", 545.27, 0.34, 185.39),               # nur Rundung (0,0018 €)
    zeile("1.4", "Bauzaun", 100.0, None, None),                        # unbepreist
    zeile("1.5", "Pumpe", 0.0, 3279.2, 0.0, einheit=""),              # Menge 0, GP 0: stimmt
], columns=COLUMNS)


def main():
    n, f = pruefe_rechnung(MINI)
    check("Mini: 4 Positionen nachgerechnet (unbepreiste ausgenommen), genau 1 Abweichung (1.2)",
          n == 4 and [x["positionen"][0]["oz"] for x in f] == ["1.2"], f"{n} {[x['id'] for x in f]}")
    x = f[0]
    check("Fund: nachweisbarer Fehler, Stufe 1, Rang 1 (Rangtabelle 21:20), ID 17|Datei|OZ",
          (x["kategorie"], x["stufe"], x["prioritaet_in_stufe"], x["id"]) == ("nachweisbarer Fehler", 1, 1, "17|mini.X84|1.2"))
    check("Fund: Beleg Menge, EP und GP als Feldwerte, Kurztext als Zitat",
          [b["text"] for b in x["feldbelege"]] == ["Menge: 3,000 m", "EP: 1.200,00", "GP: 3.800,00"]
          and x["belege"] == ["Schacht setzen"], str(x["feldbelege"]))
    check("Fund: Begründung nennt Produkt, GP und Abweichung, ohne verbotene Begriffe (R7)",
          "Menge × EP = 3.600,00 €" in x["begruendung"] and "Abweichung 200,00 €" in x["begruendung"]
          and not VERBOTEN.search(x["begruendung"]), x["begruendung"])
    check("Toleranz: 0,01 € + |Menge| × 0,0005 € (Rundung von GP und gedrucktem EP)",
          abs(toleranz(545.27) - 0.282635) < 1e-9 and abs(toleranz(0) - 0.01) < 1e-12)
    check("Rundung 0,0018 € (1.3) ist kein Fund, Menge 0 mit GP 0 auch nicht",
          all(y["positionen"][0]["oz"] not in ("1.3", "1.5") for y in f))
    check("Formate: de(6803.4, 2) = „6.803,40“, EP mit 3 Stellen nur bei Bedarf",
          de(6803.4, 2) == "6.803,40" and de_ep(80.04) == "80,04" and de_ep(80.045) == "80,045")
    e = abdeckung_eintrag(MINI)
    check("Prüfabdeckung: „Rechenprüfung: 4 Positionen nachgerechnet, 1 Abweichungen“, Grund für die übrigen",
          e["text"] == "Rechenprüfung: 4 Positionen nachgerechnet, 1 Abweichungen" and e["gruende"][0][1] == 1, str(e))
    a = alle_pruefungen(MINI)
    check("alle_pruefungen enthält den Nr.-17-Fund ganz oben (Stufe 1, Rang 1)",
          a and a[0]["pruefung"] == 17 and a == sortiere(a), str([y["id"] for y in a][:3]))
    preise = MINI.assign(kurztext="", langtext="")
    p = alle_pruefungen(preise)
    check("Reine Preisdatei: nur Nr. 17 läuft, Abweichung wird trotzdem gefunden",
          [y["pruefung"] for y in p] == [17] and [y["pruefung"] for y in abdeckung(preise)] == [17])
    check("Reine Preisdatei: Fund ohne Kurztext hat leere Zitate, Belege als Feldwerte", p[0]["belege"] == []
          and len(p[0]["feldbelege"]) == 3)
    check("Gleiche Eingabe, gleiches Ergebnis (E14)", json.dumps(pruefe_rechnung(MINI)[1]) == json.dumps(f))
    check("Bericht: Prüfung 17 hat Namen und Prüfer „Preis“", bericht.PRUEFUNGEN[17].startswith("Rechenprüfung")
          and bericht.PRUEFER[17] == "Preis")
    check("Prüfer: jede Prüfung Nr. 1–19 hat einen der acht Prüfer des Backlogs",
          set(bericht.PRUEFER) == set(range(1, 20)) and set(bericht.PRUEFER.values()) <=
          {"Formal", "Widerspruch", "Nachtrag", "Klarheit", "Mengen", "Vollständigkeit", "Preis", "Tippfehler"})
    # Messung am Datensatz (keine Einstellung der Regel): Erhebung 21.11.2026
    erwartet = {"Abgabe LV.pdf": 248, "Angebot AN24-0305.D84": 274, "Angebot AN24-0305.pdf": 274,
                "StBALV23040.D86": 249, "[ORT_024] LV24069.D86": 197, "StBALV23040.D84": 0}
    ist = {d: pruefe_rechnung(parse(D / d)) for d in erwartet}
    check("Datensatz: 1.242 Positionen in 5 Dateien nachgerechnet (StBALV23040.D84: Preise ohne Menge, 0)",
          {d: v[0] for d, v in ist.items()} == erwartet, str({d: v[0] for d, v in ist.items()}))
    check("Datensatz: 0 Abweichungen", all(not v[1] for v in ist.values()), str({d: len(v[1]) for d, v in ist.items()}))
    print(f"\n{sum(ergebnisse)}/{len(ergebnisse)} Tests bestanden")
    return 0 if all(ergebnisse) else 1


if __name__ == "__main__":
    sys.exit(main())
