"""
etiketten.py - Etikettenliste für Person B (P4, B9) erzeugen und wieder einlesen.

Eine Zeile je Position mit offenem Fund Nr. 1/2; dieselbe Position in mehreren Dateien
(PDF, GAEB XML, GAEB 90) nur einmal (gleiche normalisierte OZ und gleiche Regelwerte).
Spalte „Einordnung“ mit Auswahlliste. Es stehen KEINE KI-Ergebnisse in der Liste.
Nach „Etiketten fertig“ werden ausgefüllte Zeilen mit Quelle „Person B, am Original, vor dem
KI-Lauf“ in data/qa/ki_goldstandard.json übernommen.

Zeilen mit Hinweis auf einen T2-Positiv-Test (Team, 21.11.2026): Weicht Person B vom bisherigen
Goldstandard-Eintrag ab, wird nichts überschrieben. Die Position wird „strittig“: beide Einordnungen
stehen mit Quelle im Goldstandard, die Messung weist sie getrennt aus (nicht in der Trefferquote).

Aufruf (aus der Projektwurzel, uv-Befehl siehe README.md):
  python src/etiketten.py erzeugen data/raw
  python src/etiketten.py einlesen              # nur zählen
  python src/etiketten.py uebernehmen [xlsx] [herkunft]   # in den Goldstandard übernehmen
"""
import json
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font
from openpyxl.worksheet.datavalidation import DataValidation

from pruefung_widerspruch import normalisiere_oz, normalisiere_leerzeichen

ROOT = Path(__file__).resolve().parent.parent
XLSX = ROOT / "data" / "qa" / "etiketten_person_b.xlsx"
GOLD = ROOT / "data" / "qa" / "ki_goldstandard.json"
EINORDNUNGEN = ["echter Widerspruch", "anderes Bauteil", "Bereichs- oder Mehrfachangabe", "unklar"]
SPALTEN = ["Datei", "OZ", "Seite", "Kurztext-Auszug", "Regelwert Kurztext", "Regelwert Langtext", "Einordnung",
           "Auch in (gleiche Position)", "Hinweis", "Fund-IDs"]
BREITEN = [36, 12, 7, 60, 18, 18, 30, 60, 50, 70]
QUELLE_B = "Person B, am Original, vor dem KI-Lauf"


def _wert(w):
    return w.replace("DN", "DN ", 1) if w.startswith("DN") else w


def gruppen(funde_texte):
    """funde_texte: Liste (fund, texte). Gibt Gruppen je Position zurück (Liste von Listen)."""
    from ki_pruefung import regelwerte
    g = defaultdict(list)
    for f, texte in funde_texte:
        t = texte[f["id"]][0]
        wk, wl = regelwerte(f, t["kurztext"], t["langtext"])
        g[(normalisiere_oz(f["positionen"][0]["oz"]), tuple(wk), tuple(wl))].append((f, t, wk, wl))
    return [g[k] for k in sorted(g)]


def erzeuge(rohdaten=ROOT / "data" / "raw", ziel=XLSX, gold_datei=GOLD):
    from bericht import pruefe_lv
    from ki_pruefung import ki_funde
    gold = {e["fund_id"]: e for e in json.loads(Path(gold_datei).read_text(encoding="utf-8"))["eintraege"]}
    alle = []
    for p in sorted(Path(rohdaten).iterdir()):
        try:
            funde, texte, _ = pruefe_lv(p)
        except ValueError:
            continue
        alle += [(f, texte) for f in ki_funde(funde)]
    wb = Workbook()
    ws = wb.active
    ws.title = "Etiketten"
    for j, s in enumerate(SPALTEN, start=1):
        ws.cell(row=1, column=j, value=s).font = Font(bold=True)
    zeile = 1
    for gr in gruppen(alle):
        offen = [x for x in gr if not gold.get(x[0]["id"], {}).get("zaehlt")]
        if not offen:
            continue                                   # Position schon im Goldstandard (z. B. T2)
        t2 = [x[0]["id"] for x in gr if gold.get(x[0]["id"], {}).get("zaehlt")]
        offen.sort(key=lambda x: (x[0]["positionen"][0]["seite"] is None, x[0]["id"]))   # PDF mit Seite zuerst
        f, t, wk, wl = offen[0]
        p = f["positionen"][0]
        weitere = [f"{x[0]['positionen'][0]['datei']} {x[0]['positionen'][0]['oz']}" for x in offen[1:]]
        hinweis = (f"gleiche Position wie Positiv-Test aus T2 ({', '.join(t2)}; dort im Goldstandard "
                   f"„{gold[t2[0]]['einordnung']}“) – bitte am Original bestätigen" if t2 else "")
        zeile += 1
        werte = [p["datei"], p["oz"], p["seite"] if p["seite"] is not None else "–",
                 normalisiere_leerzeichen(t["kurztext"])[:120], ", ".join(map(_wert, wk)), ", ".join(map(_wert, wl)),
                 None, "\n".join(weitere), hinweis, "\n".join(x[0]["id"] for x in offen)]
        for j, v in enumerate(werte, start=1):
            c = ws.cell(row=zeile, column=j, value=v)
            if isinstance(v, str):
                c.data_type = "s"
            c.alignment = Alignment(wrap_text=True, vertical="top")
    for j, b in enumerate(BREITEN, start=1):
        ws.column_dimensions[ws.cell(row=1, column=j).column_letter].width = b
    ws.freeze_panes = "A2"
    sp = ws.cell(row=1, column=SPALTEN.index("Einordnung") + 1).column_letter
    dv = DataValidation(type="list", formula1='"' + ",".join(EINORDNUNGEN) + '"', allow_blank=True,
                        showErrorMessage=True, errorTitle="Einordnung", error="Bitte einen Wert aus der Liste wählen.")
    dv.add(f"{sp}2:{sp}{max(zeile, 2)}")
    ws.add_data_validation(dv)
    ws.auto_filter.ref = f"A1:{ws.cell(row=1, column=len(SPALTEN)).column_letter}{max(zeile, 2)}"
    Path(ziel).parent.mkdir(parents=True, exist_ok=True)
    wb.save(ziel)
    return zeile - 1


def zeilen(quelle=XLSX):
    """Alle Zeilen der Liste als dicts: fund_ids, einordnung (bereinigt, None = leer), t2_ids, datei, oz."""
    ws = load_workbook(quelle)["Etiketten"]
    kopf = [c.value for c in ws[1]]
    i = {n: kopf.index(n) for n in ("Datei", "OZ", "Einordnung", "Hinweis", "Fund-IDs")}
    aus = []
    for r in ws.iter_rows(min_row=2, values_only=True):
        if not any(r):
            continue
        e = r[i["Einordnung"]]
        e = e.strip() if isinstance(e, str) else e
        m = re.search(r"Positiv-Test aus T2 \((.*?); dort", r[i["Hinweis"]] or "")
        aus.append({"datei": r[i["Datei"]], "oz": r[i["OZ"]], "einordnung": e or None,
                    "fund_ids": [x.strip() for x in (r[i["Fund-IDs"]] or "").split("\n") if x.strip()],
                    "t2_ids": [x.strip() for x in m.group(1).split(",")] if m else []})
    return aus


def einlesen(quelle=XLSX):
    """Gibt (ausgefüllte Zeilen, Zeilen gesamt, ungültige Werte) zurück; Zeile = (Fund-IDs, Einordnung)."""
    gefuellt, gesamt, ungueltig = [], 0, []
    for z in zeilen(quelle):
        gesamt += 1
        if not z["einordnung"]:
            continue
        if z["einordnung"] not in EINORDNUNGEN:
            ungueltig.append(("\n".join(z["fund_ids"]), z["einordnung"]))
            continue
        gefuellt.append((z["fund_ids"], z["einordnung"]))
    return gefuellt, gesamt, ungueltig


def uebernehmen(quelle=XLSX, gold_datei=GOLD, herkunft=None):
    """Ausgefüllte Zeilen in den Goldstandard übernehmen (Quelle QUELLE_B). Nichts wird überschrieben:
    - Eintrag „offen“: Einordnung von Person B, zaehlt=true.
    - Eintrag mit Einordnung (T2-Position oder schon belegt): gleich → nur Vermerk „bestätigt“;
      abweichend → Position „strittig“ (beide Einordnungen mit Quelle, zählt nicht in der Trefferquote).
    Gibt einen Bericht (dict) zurück; wirft ValueError bei unbekannten Fund-IDs oder ungültigen Werten."""
    gold = json.loads(Path(gold_datei).read_text(encoding="utf-8"))
    if gold.get("etiketten"):
        raise ValueError(f"Etiketten schon übernommen ({gold['etiketten']['eingelesen']}); nichts geändert")
    idx = {e["fund_id"]: e for e in gold["eintraege"]}
    alle = zeilen(quelle)
    ungueltig = [z for z in alle if z["einordnung"] and z["einordnung"] not in EINORDNUNGEN]
    unbekannt = [fid for z in alle for fid in z["fund_ids"] + z["t2_ids"] if fid not in idx]
    if ungueltig or unbekannt:
        raise ValueError(f"ungültige Werte: {[(z['oz'], z['einordnung']) for z in ungueltig]}; "
                         f"unbekannte Fund-IDs: {unbekannt}")
    bericht = {"gefuellt": 0, "gesamt": len(alle), "neu": [], "bestaetigt": [], "strittig": []}
    for z in alle:
        b = z["einordnung"]
        if not b:
            continue
        bericht["gefuellt"] += 1
        # bisherige Einordnung der Position: T2-Eintrag oder ein schon belegter Eintrag der Zeile
        vorher = [idx[fid] for fid in z["t2_ids"] + z["fund_ids"] if idx[fid]["einordnung"] not in ("offen", "strittig")]
        alt = vorher[0] if vorher else None
        if alt is None or alt["einordnung"] == b:
            for fid in z["fund_ids"]:
                e = idx[fid]
                if e["einordnung"] == "offen":
                    e.update(einordnung=b, zaehlt=True, quelle=QUELLE_B)
                    bericht["neu"].append(fid)
            if alt is not None:
                for e in vorher:
                    e["bestaetigt_durch"] = QUELLE_B
                bericht["bestaetigt"].append(z["oz"])
            continue
        beide = [{"einordnung": alt["einordnung"], "quelle": alt["quelle"]}, {"einordnung": b, "quelle": QUELLE_B}]
        for e in vorher:                               # bisherige Einträge bleiben, nur Vermerk
            e.update(strittig=True, einordnung_person_b=b, quelle_person_b=QUELLE_B)
        for fid in z["fund_ids"]:
            e = idx[fid]
            if e["einordnung"] == "offen":
                e.update(einordnung="strittig", zaehlt=False, strittig=True, einordnungen=beide,
                         quelle="strittig: Einordnungen siehe „einordnungen“")
        bericht["strittig"].append({"oz": z["oz"], "datei": z["datei"], "einordnungen": beide,
                                    "fund_ids": z["fund_ids"] + z["t2_ids"]})
    gold["etiketten"] = {"datei": str(Path(quelle).name), "eingelesen": datetime.now().astimezone().isoformat(
        timespec="seconds"), "gespeichert": datetime.fromtimestamp(Path(quelle).stat().st_mtime).astimezone().isoformat(
        timespec="seconds"), "gefuellt": bericht["gefuellt"], "gesamt": bericht["gesamt"], "quelle": QUELLE_B}
    if herkunft:
        gold["etiketten"]["herkunft"] = herkunft
    Path(gold_datei).write_text(json.dumps(gold, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return bericht


if __name__ == "__main__":
    if sys.argv[1:2] == ["erzeugen"]:
        n = erzeuge(Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "data" / "raw")
        print(f"{n} Zeilen in {XLSX.relative_to(ROOT)}")
    elif sys.argv[1:2] == ["einlesen"]:
        g, n, u = einlesen()
        print(f"{len(g)} von {n} Zeilen ausgefüllt; ungültige Werte: {u or 'keine'}")
    elif sys.argv[1:2] == ["uebernehmen"]:
        quelle = Path(sys.argv[2]) if len(sys.argv) > 2 else XLSX
        herkunft = sys.argv[3] if len(sys.argv) > 3 else None
        b = uebernehmen(quelle, herkunft=herkunft)
        print(f"{b['gefuellt']} von {b['gesamt']} Zeilen ausgefüllt; neu im Goldstandard: {len(b['neu'])} Fund-IDs; "
              f"T2 bestätigt: {b['bestaetigt'] or 'keine'}; strittig: {len(b['strittig'])}")
        for x in b["strittig"]:
            print("  strittig:", x["datei"], x["oz"], " / ".join(f"{e['einordnung']} ({e['quelle'][:40]}…)"
                                                                for e in x["einordnungen"]))
