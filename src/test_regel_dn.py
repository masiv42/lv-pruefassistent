"""
test_regel_dn.py - Tests der Regel Nr. 1 für Mehrfachangaben „DN a/b“ (B1q, Team 21.11.2026, F5 B1b).

Leitplanke E12 (3): Die Regel ist nur an erfundenen Texten entwickelt; keine Texte aus data/raw oder dem
Goldstandard. Der Datensatz dient danach nur zur Messung (docs/bericht_B1q.md).
Aufruf aus der Projektwurzel (uv-Befehl siehe AGENTS.md):
  python src/test_regel_dn.py
Exit-Code 0 = alle Tests bestanden. Liest und schreibt keine Projektdateien.
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lv_parser import COLUMNS                                    # noqa: E402
from pruefung_widerspruch import pruefe, dn_angaben              # noqa: E402

ergebnisse = []


def check(name, ok, detail=""):
    ergebnisse.append(ok)
    print(f"{'OK    ' if ok else 'FEHLER'} {name}" + (f" – {detail}" if detail and not ok else ""))


def funde(kurz, lang):
    """Nr.-1-Funde für eine erfundene Position (GAEB XML, Langtext beginnt mit dem Kurztext)."""
    r = {c: None for c in COLUMNS}
    r.update(datei="erfunden.X83", format="GAEB XML", typ="Position", oz="9.9.1", kurztext=kurz,
             langtext=f"{kurz} {lang}", menge=1.0, einheit="m", einheit_roh="m", art="Normal", art_roh="")
    return [f for f in pruefe(pd.DataFrame([r], columns=COLUMNS)) if f["pruefung"] == 1]


def main():
    # Zerlegung
    check("dn_angaben: „DN 125/100“ ist eine Angabe mit zwei Werten",
          dn_angaben("Rohr DN 125/100 liefern") == [("DN125", "DN100")])
    check("dn_angaben: Leerzeichen um „/“ und drei Werte", dn_angaben("Bogen DN 50 / 65/80") == [("DN50", "DN65", "DN80")])
    check("dn_angaben: Länge nach „/“ ist kein Wert („DN 350/2000 mm lg“, „… lang“, „Baulänge“)",
          dn_angaben("Passstück DN 350/2000 mm lg") == [("DN350",)]
          and dn_angaben("Passstück DN 350/1500 lang") == [("DN350",)]
          and dn_angaben("Passstück DN 350/700 Baulänge") == [("DN350",)])
    check("dn_angaben: Wiederholung derselben Angabe zählt einmal, verschiedene Angaben getrennt",
          dn_angaben("Schieber DN 65, Schieber DN 65 und Bogen DN 40") == [("DN65",), ("DN40",)])
    # Regel
    check("Kurztext-Wert in „DN a/b“ des Langtexts -> kein Fund",
          funde("Leitung DN 450", "als Leitung DN 400/450 ausführen") == [])
    f = funde("Leitung DN 150", "als Leitung DN 125/100 ausführen")
    check("Kein Kurztext-Wert in „DN a/b“ -> Fund bleibt (eine Angabe, zwei Werte)",
          len(f) == 1 and any("DN 125/100" in b for b in f[0]["belege"])
          and "Langtext nennt DN 125/100" in f[0]["begruendung"], str(f))
    check("Kurztext „DN a/b“ mit einem Langtext-Wert darin -> kein Fund",
          funde("Formstück DN 80/100", "Formstück DN 100 aus Guss") == [])
    f = funde("Formstück DN 80/100", "Formstück DN 150 aus Guss")
    check("Kurztext „DN a/b“ ohne gemeinsamen Wert -> Fund", len(f) == 1, str(f))
    f = funde("Passstück DN 200", "Passstück DN 250/1000 mm lg aus Guss")
    check("Länge nach „/“: DN 200 gegen DN 250 -> Fund (1000 ist keine Nennweite)",
          len(f) == 1 and "Langtext nennt DN 250;" in f[0]["begruendung"], str(f))
    check("Länge nach „/“: DN 250 gegen „DN 250/1000 mm lg“ -> kein Fund",
          funde("Passstück DN 250", "Passstück DN 250/1000 mm lg aus Guss") == [])
    check("Unverändert: zwei getrennte DN-Angaben im Langtext -> kein Fund (Regel vom 20.11.2026)",
          funde("Kanal DN 700", "Kanal DN 500 und DN 600 anschließen") == [])
    f = funde("Kanal DN 700", "Kanal DN 600 anschließen")
    check("Unverändert: ein Wert, verschieden -> Fund mit bisheriger Begründung",
          len(f) == 1 and f[0]["begruendung"] == "Kurztext nennt DN 700, Langtext nennt DN 600; kein Wert stimmt überein.",
          str(f))
    # F1 (B1q, Team 21.11.2026): Lesart C – Fund bleibt, Begründung nennt die Bereichsangaben
    f = funde("Halter bis DN 150", "Halter für Leitungen bis DN 200 liefern")
    check("F1 Lesart C: „bis DN 150“ gegen „bis DN 200“ -> Fund bleibt, Begründung „Bereichsangaben, Obergrenzen verschieden.“",
          len(f) == 1 and f[0]["begruendung"].endswith("Bereichsangaben, Obergrenzen verschieden."), str(f))
    f = funde("Halter DN 150", "Halter für Leitungen bis DN 200 liefern")
    check("F1 Lesart C: nur eine Seite mit „bis“ -> Fund ohne Bereichs-Zusatz",
          len(f) == 1 and "Bereichsangaben" not in f[0]["begruendung"], str(f))
    check("F1 Lesart C: gleiche Obergrenze -> kein Fund", funde("Halter bis DN 150", "Halter bis DN 150 liefern") == [])
    print(f"\n{sum(ergebnisse)}/{len(ergebnisse)} Tests bestanden")
    return 0 if all(ergebnisse) else 1


if __name__ == "__main__":
    sys.exit(main())
