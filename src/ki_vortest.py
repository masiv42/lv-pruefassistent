"""
ki_vortest.py - Vortest der KI-Gegenprüfung mit erfundenen Positionen (P4, Team 21.11.2026).

Fälle: data/qa/ki_vortest.json (8 erfundene Positionen mit Soll-Einordnung; keine aus dem
Datensatz). Varianten: A) reasoning_effort „low“, B) „medium“, beide temperature 0, Prompt wie
in src/ki_pruefung.py. Gleiche Prüfkette wie im echten Lauf (einmal neu fragen bei unlesbarer
Antwort). Kein Cache. Tokens je Aufruf im Log (data/qa/ki_log.jsonl, fund_id „VORTEST-…“).
Budget: höchstens 25.000 Tokens für den ganzen Vortest.
Wahl: meiste Treffer, bei Gleichstand weniger Tokens. Erkennt keine Variante alle echten
Widersprüche: keine Wahl (Meldung an das Team).

Stabilitätscheck (Team, 21.11.2026): `--stabilitaet` wiederholt nur Variante A einmal ohne
Cache (Log „VORTEST2-…“), schreibt data/qa/ki_vortest_stabilitaet.json und meldet die Fälle,
deren Einordnung gegenüber dem ersten Vortest-Lauf wechselt.

Aufruf (aus der Projektwurzel, uv-Befehl siehe README.md):
  python src/ki_vortest.py
  python src/ki_vortest.py --stabilitaet
"""
import json
import sys
from datetime import datetime
from pathlib import Path

import ki_pruefung as K
from ki_client import TechnischerFehler

ROOT = Path(__file__).resolve().parent.parent
FAELLE = ROOT / "data" / "qa" / "ki_vortest.json"
ERGEBNIS = ROOT / "data" / "qa" / "ki_vortest_ergebnis.json"
STABILITAET = ROOT / "data" / "qa" / "ki_vortest_stabilitaet.json"
VARIANTEN = [("A", "low"), ("B", "medium")]
BUDGET = 25_000
RESERVE_JE_AUFRUF = 2_500      # vor jedem Aufruf: Budget muss dafür noch reichen


def lauf(konfig, faelle, log_datei=K.LOG_DATEI, varianten=VARIANTEN, kennung="VORTEST"):
    verbraucht = 0
    erg = {"prompt_version": K.PROMPT_VERSION, "modell": konfig.modell, "anbieter": konfig.anbieter,
           "zeit": datetime.now().astimezone().isoformat(timespec="seconds"), "varianten": {}, "abbruch": None}
    for name, effort in varianten:
        client = konfig.client(reasoning_effort=effort)
        v = {"reasoning_effort": effort, "faelle": [], "tokens": 0, "dauer_s": 0.0, "treffer": 0}
        for c in faelle:
            f = {"id": c["id"], "pruefung": c["pruefung"]}
            texte = {c["id"]: [{"oz": "-", "kurztext": c["kurztext"], "langtext": c["langtext"]}]}
            text = K.positionstext(f, texte)
            status, d, tok, dauer, versuch = None, None, 0, 0.0, 0
            while versuch < 2:
                if verbraucht + RESERVE_JE_AUFRUF > BUDGET:
                    erg["abbruch"] = f"Budget {BUDGET} Tokens erreicht (verbraucht {verbraucht})"
                    break
                versuch += 1
                try:
                    a = client.anfrage(konfig.modell, K.SYSTEM_PROMPT, text, K.EINORDNUNGEN)
                except TechnischerFehler as e:
                    status = f"technischer Fehler: {e.art}"
                    break
                n = a.usage["input_tokens"] + a.usage["output_tokens"]
                verbraucht += n
                tok += n
                dauer += a.dauer_s
                status, d = K.bewerte(a.text, c["kurztext"], c["langtext"], a.stop_reason)
                K.schreibe_log({"zeit": datetime.now().astimezone().isoformat(timespec="seconds"),
                                "fund_id": f"{kennung}-{c['id']}-{name}", "anbieter": konfig.anbieter,
                                "modell": konfig.modell, "modell_antwort": a.modell,
                                "prompt_version": K.PROMPT_VERSION, "reasoning_effort": effort, "versuch": versuch,
                                "stop_reason": a.stop_reason, "usage": a.usage, "dauer_s": round(a.dauer_s, 2),
                                "wartezeit_s": a.wartezeit_s, "kosten_usd": 0, "ergebnis": status}, log_datei)
                if status != K.STATUS_UNLESBAR:
                    break
            if erg["abbruch"] and status is None:
                break
            ein = d["einordnung"] if d else None
            treffer = status == K.STATUS_GUELTIG and ein == c["soll"]
            v["faelle"].append({"id": c["id"], "soll": c["soll"], "ki": ein, "status": status, "treffer": treffer,
                                "begruendung": d["begruendung"] if d else "", "rueckfrage": d["rueckfrage"] if d else "",
                                "tokens": tok, "dauer_s": round(dauer, 2)})
            v["tokens"] += tok
            v["dauer_s"] = round(v["dauer_s"] + dauer, 2)
            v["treffer"] += treffer
        erg["varianten"][name] = v
        if erg["abbruch"]:
            break
    erg["tokens_gesamt"] = verbraucht
    echte = {c["id"] for c in faelle if c["soll"] == "echter Widerspruch"}
    kandidaten = [(n, v) for n, v in erg["varianten"].items()
                  if len(v["faelle"]) == len(faelle) and echte <= {x["id"] for x in v["faelle"] if x["treffer"]}]
    if kandidaten:
        n, v = sorted(kandidaten, key=lambda nv: (-nv[1]["treffer"], nv[1]["tokens"]))[0]
        erg["wahl"] = {"variante": n, "reasoning_effort": v["reasoning_effort"],
                       "regel": "meiste Treffer, bei Gleichstand weniger Tokens; alle echten Widersprüche erkannt"}
    else:
        erg["wahl"] = None
        erg["meldung"] = "Keine Variante erkennt alle echten Widersprüche: anhalten und melden (Team, 21.11.2026)."
    return erg


def vergleich(erg_1, erg_2, variante="A"):
    """Einordnung je Fall in Lauf 1 und Lauf 2; gewechselt = andere Einordnung oder anderer Status."""
    l1 = {x["id"]: x for x in erg_1["varianten"][variante]["faelle"]}
    zeilen = []
    for x in erg_2["varianten"][variante]["faelle"]:
        a = l1.get(x["id"], {})
        e1, e2 = a.get("ki") or a.get("status") or "–", x["ki"] or x["status"] or "–"
        zeilen.append({"id": x["id"], "soll": x["soll"], "lauf_1": e1, "lauf_2": e2, "gewechselt": e1 != e2})
    return {"faelle": zeilen, "gewechselt": [z["id"] for z in zeilen if z["gewechselt"]]}


if __name__ == "__main__":
    konfig = K.lade_konfig()
    print(K.ki_status(konfig))
    if not (konfig.aktiv and konfig.anbieter == "groq"):
        raise SystemExit("Vortest braucht KI_ANBIETER=groq und GROQ_API_KEY in der .env")
    if not K.prompt_eingefroren():
        raise SystemExit("Systemprompt passt nicht zur eingefrorenen Version")
    faelle = json.loads(FAELLE.read_text(encoding="utf-8"))["faelle"]
    if "--stabilitaet" in sys.argv[1:]:
        erg = lauf(konfig, faelle, varianten=VARIANTEN[:1], kennung="VORTEST2")
        erg.pop("wahl", None); erg.pop("meldung", None)
        erg["vergleich"] = vergleich(json.loads(ERGEBNIS.read_text(encoding="utf-8")), erg)
        STABILITAET.write_text(json.dumps(erg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        v = erg["varianten"]["A"]
        print(f"Wiederholung A ({v['reasoning_effort']}): {v['treffer']}/{len(faelle)} Treffer, "
              f"{v['tokens']} Tokens, {v['dauer_s']} s | Abbruch: {erg['abbruch']}")
        for z in erg["vergleich"]["faelle"]:
            print(f"{z['id']:4} Soll {z['soll']:32} Lauf 1: {z['lauf_1']:32} Lauf 2: {z['lauf_2']:32}"
                  f"{'GEWECHSELT' if z['gewechselt'] else ''}")
        print("Gewechselt:", erg["vergleich"]["gewechselt"] or "keiner")
        raise SystemExit(0)
    erg = lauf(konfig, faelle)
    ERGEBNIS.write_text(json.dumps(erg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{'Fall':5} {'Soll':32} " + " ".join(f"{n} ({v['reasoning_effort']}):".ljust(40) for n, v in erg["varianten"].items()))
    for i, c in enumerate(faelle):
        zellen = []
        for v in erg["varianten"].values():
            x = v["faelle"][i] if i < len(v["faelle"]) else None
            zellen.append((f"{'✓' if x['treffer'] else '✗'} {x['ki'] or x['status']} ({x['tokens']} T)" if x else "–").ljust(40))
        print(f"{c['id']:5} {c['soll']:32} " + " ".join(zellen))
    for n, v in erg["varianten"].items():
        print(f"Variante {n}: {v['treffer']}/{len(faelle)} Treffer, {v['tokens']} Tokens, {v['dauer_s']} s")
    print("Tokens Vortest gesamt:", erg["tokens_gesamt"], "| Wahl:", erg["wahl"] or erg.get("meldung"),
          "| Abbruch:", erg["abbruch"])
