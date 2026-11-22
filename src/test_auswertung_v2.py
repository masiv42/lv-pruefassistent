"""
test_auswertung_v2.py - Tests für src/auswertung_v2.py (L29) mit erfundenen Mini-Daten.

Leitplanke E12 (3): nicht am Goldstandard, sondern an erfundenen Fällen. Liest und schreibt keine
Projektdateien.
Aufruf aus der Projektwurzel:
  python src/test_auswertung_v2.py
Exit-Code 0 = alle Tests bestanden.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from auswertung_v2 import zeilen, worst_case, auswertung, GUELTIG     # noqa: E402

ergebnisse = []
EW, AB, BM, UK = "echter Widerspruch", "anderes Bauteil", "Bereichs- oder Mehrfachangabe", "unklar"


def check(name, ok, detail=""):
    ergebnisse.append(ok)
    print(f"{'OK    ' if ok else 'FEHLER'} {name}" + (f" – {detail}" if detail and not ok else ""))


def ki(e):
    return {"status": GUELTIG, "einordnung": e}


# Erfundene Positionen P1–P5 in den Dateien a/b; P6 Zusatzfall; P7 strittig; P8 ohne KI-Ergebnis
LAUF = {
    "prompt_version": "TEST", "modell": "test",
    "ergebnisse": {
        "1|a|1": ki(EW), "1|b|1": ki(EW),            # P1 echt, überall erkannt
        "1|a|2": ki(EW), "1|b|2": ki(AB),            # P2 echt, uneinheitlich: gefährlich
        "1|a|3": ki(BM),                             # P3 Fehlalarm, erkannt
        "1|a|4": ki(EW),                             # P4 Fehlalarm, KI sagt echt: falsch, nicht gefährlich
        "1|a|5": ki(EW),                             # P5 Gold „unklar“: grob ausgelassen, fein falsch
        "1|a|6": ki(AB),                             # P6 Zusatzfall
        "1|a|7": ki(EW),                             # P7 strittig
        "1|a|9": {"status": "KI-Vorschlag verworfen: Zitat nicht im Original", "einordnung": ""},
    },
    "positionen": {f"1|{d}|{n}": f"P{n}" for d in "ab" for n in range(1, 10)},
}
GOLD = {"eintraege": [
    {"fund_id": "1|a|1", "einordnung": EW, "zaehlt": True}, {"fund_id": "1|b|1", "einordnung": EW, "zaehlt": True},
    {"fund_id": "1|a|2", "einordnung": EW, "zaehlt": True}, {"fund_id": "1|b|2", "einordnung": EW, "zaehlt": True},
    {"fund_id": "1|a|3", "einordnung": BM, "zaehlt": True},
    {"fund_id": "1|a|4", "einordnung": AB, "zaehlt": True},
    {"fund_id": "1|a|5", "einordnung": UK, "zaehlt": True},
    {"fund_id": "1|a|6", "einordnung": AB, "zaehlt": True, "regel_fund": False},
    {"fund_id": "1|a|7", "einordnung": "strittig", "zaehlt": False, "strittig": True},
    {"fund_id": "1|a|8", "einordnung": EW, "zaehlt": True},
    {"fund_id": "1|a|9", "einordnung": EW, "zaehlt": True},
    {"fund_id": "1|b|9", "einordnung": "offen", "zaehlt": False},
]}


def main():
    zs = zeilen(LAUF, GOLD)
    gr = {z["fund_id"]: z["gruppe"] for z in zs}
    check("Gruppen: regel / zusatz / strittig; „offen“ ohne zaehlt fehlt",
          gr["1|a|6"] == "zusatz" and gr["1|a|7"] == "strittig" and "1|b|9" not in gr)
    ur = {z["fund_id"]: z["urteil"] for z in zs}
    check("Urteile: nicht geprüft und verworfen getrennt", ur["1|a|8"] == "nicht geprüft" and ur["1|a|9"] == "verworfen")
    regel = [z for z in zs if z["gruppe"] == "regel"]
    g = worst_case(regel, "grob")
    check("Worst Case grob: 4 Positionen bewertet (P5 „unklar“ ausgelassen), 2 richtig",
          (g["positionen_bewertet"], g["richtig"], g["gold_unklar_ausgelassen"]) == (4, 2, ["P5"]), str(g))
    check("Worst Case grob: uneinheitliche Position P2 zählt als falsch", "P2" in g["falsch_liste"]
          and "P2" in g["uneinheitlich"])
    check("Worst Case grob: gefährliche Richtung nur P2, Datei b",
          [(x["position"], x["dateien"], x["ki"]) for x in g["gefaehrliche_richtung"]] == [("P2", ["b"], [AB])])
    check("Worst Case grob: echte Widersprüche 1 von 2 in jeder Datei erkannt",
          (g["echte_widersprueche"], g["echte_widersprueche_in_jeder_datei_erkannt"]) == (2, 1))
    check("Fehlalarm als „echt“ (P4) ist falsch, aber nicht gefährlich",
          "P4" in g["falsch_liste"] and all(x["position"] != "P4" for x in g["gefaehrliche_richtung"]))
    f = worst_case(regel, "fein")
    check("Worst Case fein: 5 bewertet, 2 richtig (P1, P3)", (f["positionen_bewertet"], f["richtig"]) == (5, 2), str(f))
    a = auswertung(LAUF, GOLD)
    check("Auswertung: 0 KI-Aufrufe, Zusatz und strittig getrennt",
          a["quelle"]["ki_aufrufe"] == 0 and len(a["zusatz"]) == 1 and len(a["strittig"]) == 1)
    print(f"\n{sum(ergebnisse)}/{len(ergebnisse)} Tests bestanden")
    return 0 if all(ergebnisse) else 1


if __name__ == "__main__":
    sys.exit(main())
