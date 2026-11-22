"""
auswertung_v2.py - Messung Lauf 1 neu auswerten (B0b.5, L10), ohne einen einzigen KI-Aufruf.

Liest nur gespeicherte Daten: die KI-Ergebnisse und Positionszuordnung aus
data/qa/ki_messung_lauf1.json (bleibt unverändert) und den aktuellen Goldstandard
data/qa/ki_goldstandard.json. Importiert nichts aus ki_client / ki_pruefung.

Neu gegenüber Lauf 1: „je Position, Worst Case“ – eine Position zählt als falsch, wenn die KI in
mindestens einer Datei falsch liegt; uneinheitliche Positionen werden so mitgezählt. Die
gefährliche Richtung (Gold „echter Widerspruch“, KI hält es für einen Fehlalarm) steht je Position
getrennt. Diese Worst-Case-Zahl ist ab B0b die Zahl für Bericht und Pitch (Team, 21.11.2026).

Aufruf aus der Projektwurzel:
  python src/auswertung_v2.py            → schreibt data/qa/ki_messung_lauf1_auswertung_v2.json
  python src/auswertung_v2.py --pruefen  → nur ausgeben, nichts schreiben
"""
import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LAUF1 = ROOT / "data" / "qa" / "ki_messung_lauf1.json"
GOLD = ROOT / "data" / "qa" / "ki_goldstandard.json"
ZIEL = ROOT / "data" / "qa" / "ki_messung_lauf1_auswertung_v2.json"
GUELTIG = "KI-Vorschlag gültig"
FEHLALARM = ("anderes Bauteil", "Bereichs- oder Mehrfachangabe")


def grob(e):
    return "echt" if e == "echter Widerspruch" else ("unklar" if e == "unklar" else "Fehlalarm")


def zeilen(lauf, gold):
    """KI gegen Goldstandard je Fund (zählende Einträge). Strittige Einträge getrennt."""
    aus = []
    for g in gold["eintraege"]:
        strittig = bool(g.get("strittig"))
        if not (g.get("zaehlt") or strittig):
            continue
        k = lauf["ergebnisse"].get(g["fund_id"])
        if k is None:
            urteil, ki = "nicht geprüft", "–"
        elif k["status"] != GUELTIG:
            urteil, ki = "verworfen", k["status"]
        else:
            ki = k["einordnung"]
            urteil = "Treffer" if ki == g["einordnung"] else "Abweichung"
        gruppe = "strittig" if strittig else ("regel" if g.get("regel_fund", True) else "zusatz")
        aus.append({"fund_id": g["fund_id"], "position": lauf["positionen"].get(g["fund_id"], g["fund_id"]),
                    "gold": g["einordnung"], "ki": ki, "urteil": urteil, "gruppe": gruppe})
    return aus


def worst_case(zs, sicht):
    """Je Position: richtig nur, wenn die KI in jeder Datei richtig liegt (sicht = grob | fein)."""
    pos = defaultdict(list)
    for z in zs:
        if z["urteil"] in ("Treffer", "Abweichung"):
            pos[z["position"]].append(z)
    bewertet, richtig, falsch, gefaehrlich, gold_unklar = [], [], [], [], []
    for p, rs in sorted(pos.items()):
        gold = rs[0]["gold"]
        if sicht == "grob" and grob(gold) == "unklar":
            gold_unklar.append(p)
            continue
        bewertet.append(p)
        ok = all((grob(r["ki"]) == grob(gold)) if sicht == "grob" else (r["ki"] == gold) for r in rs)
        (richtig if ok else falsch).append(p)
        if gold == "echter Widerspruch" and any(r["ki"] in FEHLALARM for r in rs):
            gefaehrlich.append({"position": p, "dateien": [r["fund_id"].split("|")[1] for r in rs if r["ki"] in FEHLALARM],
                                "ki": sorted({r["ki"] for r in rs if r["ki"] in FEHLALARM})})
    echte = [p for p in bewertet if pos[p][0]["gold"] == "echter Widerspruch"]
    return {"positionen_bewertet": len(bewertet), "richtig": len(richtig), "falsch": len(falsch),
            "falsch_liste": falsch, "gold_unklar_ausgelassen": gold_unklar,
            "echte_widersprueche": len(echte),
            "echte_widersprueche_in_jeder_datei_erkannt": len([p for p in echte if p in richtig]),
            "gefaehrliche_richtung": gefaehrlich,
            "uneinheitlich": [p for p, rs in sorted(pos.items()) if len({r["ki"] for r in rs}) > 1]}


def auswertung(lauf, gold):
    zs = zeilen(lauf, gold)
    regel = [z for z in zs if z["gruppe"] == "regel"]
    return {
        "zeit": datetime.now().astimezone().isoformat(timespec="seconds"),
        "quelle": {"ki_ergebnisse": "data/qa/ki_messung_lauf1.json („ergebnisse“, „positionen“; unverändert)",
                   "goldstandard": "data/qa/ki_goldstandard.json (Stand B0b, 05.01.4/05.01.46 entschieden)",
                   "ki_aufrufe": 0, "prompt_version": lauf["prompt_version"], "modell": lauf["modell"]},
        "regel_worst_case_grob": worst_case(regel, "grob"),
        "regel_worst_case_fein": worst_case(regel, "fein"),
        "zusatz": [z for z in zs if z["gruppe"] == "zusatz"],
        "strittig": [z for z in zs if z["gruppe"] == "strittig"],
        "zeilen": zs,
        "hinweis": ("grob: echt / Fehlalarm (anderes Bauteil, Bereichs- oder Mehrfachangabe); Positionen mit Gold „unklar“ "
                    "werden in grob ausgelassen und in fein gezählt. Gefährliche Richtung: Gold „echter Widerspruch“, "
                    "KI in mindestens einer Datei „anderes Bauteil“ oder „Bereichs- oder Mehrfachangabe“. "
                    "Zusatzfälle (vom DN-Filter aussortiert) und strittige Einträge getrennt, nicht in der Quote."),
    }


def main(pruefen=False):
    lauf = json.loads(LAUF1.read_text(encoding="utf-8"))
    gold = json.loads(GOLD.read_text(encoding="utf-8"))
    a = auswertung(lauf, gold)
    for s in ("grob", "fein"):
        w = a[f"regel_worst_case_{s}"]
        print(f"Worst Case je Position ({s}): {w['richtig']} von {w['positionen_bewertet']} richtig; "
              f"echte Widersprüche in jeder Datei erkannt: {w['echte_widersprueche_in_jeder_datei_erkannt']} von "
              f"{w['echte_widersprueche']}; gefährliche Richtung: {len(w['gefaehrliche_richtung'])} "
              f"({', '.join(g['position'] for g in w['gefaehrliche_richtung'])})")
    print(f"strittig: {len(a['strittig'])} Zeilen; Zusatzfälle: {len(a['zusatz'])} Zeilen")
    if not pruefen:
        ZIEL.write_text(json.dumps(a, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("gespeichert:", ZIEL.relative_to(ROOT))


if __name__ == "__main__":
    main("--pruefen" in sys.argv)
