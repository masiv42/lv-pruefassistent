"""
test_durchlauf.py - Block B1t: Durchlauf-Test als Debug-Werkzeug (Sitzung B2, Team 21.11.2026, 19:55).

Jede Datei in data/raw: parse() → bericht.pruefe_lv() (alle_pruefungen Nr. 1–6 aus main) → zusätzlich die Module
von Sitzung B2, falls importierbar (Nr. 7–14/18 pruefung_hinweise, Nr. 15/16 pruefung_struktur, Nr. 19
pruefung_vollstaendigkeit) → Risikobericht über bericht.risikobericht() und Bieterfragen über
bieterfragen.schreibe_xlsx() in einen Temp-Ordner. Je Datei geprüft:
  - kein Absturz (Ausnahme = FEHLER mit Ursache)
  - R5-Vorcheck: jeder Beleg jedes Funds steht wörtlich (Leerraum zusammengefasst) in Kurztext, Langtext oder
    art_roh einer Position mit dieser OZ aus parse() – ersetzt nicht den Skeptiker am Original
  - Export lässt sich öffnen; Blatt „Funde“ hat genau die Pflichtspalten bericht.SPALTEN und eine Zeile je Fund;
    keine Zelle ist eine Formel (data_type „f“); Bieterfragen ebenso (Überschriften, keine Formel)
  - INFO: Fundzahl je Prüfung
Bekannte Grenzen werden als HINWEIS gemeldet, nicht als FEHLER:
  - Dateien in einem Format, das parse() nicht liest (LV-Positionen.docx; docs/abdeckung.md „43 von 44“)
  - INTEGRATION: bericht.PRUEFUNGEN kennt Nr. 7–19 noch nicht (Block B2-Integration, Sitzung B1). Der Test
    exportiert dann ein zweites Mal mit vorübergehend ergänzten Namen (aus TITEL der Module) und prüft diesen
    Export; die Ergänzung gilt nur in diesem Prozess und wird danach zurückgesetzt.
Eine Zeile je Datei, Zusammenfassung am Ende, Exit-Code 0 nur ohne FEHLER. Schreibt nichts in data/ (E12 (4)).

Aufruf aus src/ (uv-Befehl siehe AGENTS.md):  python test_durchlauf.py <data/raw> [--nur <datei> ...]
"""
import io
import sys
import tempfile
import time
import traceback
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from openpyxl import load_workbook

import bericht
import bericht_kalkulator
from lv_parser import parse
from pruefung_widerspruch import normalisiere_oz, beleg_im_text
from pruefung_formal import nur_preise

MODULE = {}
for name in ("pruefung_hinweise", "pruefung_struktur", "pruefung_vollstaendigkeit", "bieterfragen"):
    try:
        MODULE[name] = __import__(name)
    except ImportError:
        pass

ZEITPUNKT = datetime(2026, 11, 21, 20, 0, tzinfo=timezone.utc)     # fest, damit der Export gleich bleibt (E14)
NICHT_UNTERSTUETZT = {".docx"}


def namen_b2():
    """Prüfungsnamen der B2-Module (für den vorübergehend ergänzten Export)."""
    n = {}
    if "pruefung_hinweise" in MODULE:
        n.update(MODULE["pruefung_hinweise"].TITEL)
    if "pruefung_struktur" in MODULE:
        n.update(MODULE["pruefung_struktur"].TITEL)
    if "pruefung_vollstaendigkeit" in MODULE:
        n[MODULE["pruefung_vollstaendigkeit"].NR] = MODULE["pruefung_vollstaendigkeit"].TITEL
    return n


def b2_funde(df, pfad, f16):
    if nur_preise(df):
        return []
    f = []
    if "pruefung_hinweise" in MODULE:
        f += MODULE["pruefung_hinweise"].pruefe_hinweise(df, pfad, f16)
    if "pruefung_struktur" in MODULE:
        f += MODULE["pruefung_struktur"].pruefe_struktur(df, pfad, f16)
    if "pruefung_vollstaendigkeit" in MODULE:
        f += MODULE["pruefung_vollstaendigkeit"].pruefe_vollstaendigkeit(df, pfad)
    return f


def r5_fehler(funde, df):
    pos = df[df.typ == "Position"]
    texte = {}
    for r in pos.itertuples():
        texte.setdefault(normalisiere_oz(r.oz), []).extend(
            [x for x in (r.kurztext, r.langtext, r.art_roh) if isinstance(x, str)])
    fehler = []
    for f in funde:
        if not f["belege"] and not f.get("feldbelege"):   # Nr. 17 in reinen Preisdateien: Belege als Feldwerte
            fehler.append(f"{f['id']}: keine Belege")
        for p in f["positionen"]:
            t = texte.get(normalisiere_oz(p["oz"]), [])
            fehler += [f"{f['id']} OZ {p['oz']}: Beleg „{b[:50]}“ nicht im Positionstext" for b in f["belege"]
                       if not beleg_im_text(b, *t)]
    return fehler


def export_fehler(daten, mit_funden, anzahl):
    wb = load_workbook(io.BytesIO(daten))
    fehler = []
    soll = (bericht_kalkulator.BLAETTER if mit_funden else []) + ["Übersicht"] + (["Funde"] if mit_funden else [])
    if wb.sheetnames[:len(soll)] != soll:
        fehler.append(f"Blätter {wb.sheetnames}, erwartet {soll}")
    if mit_funden and "Funde" in wb.sheetnames:
        ws = wb["Funde"]
        kopf = [c.value for c in ws[1]]
        if kopf != bericht.SPALTEN:
            fehler.append(f"Pflichtspalten fehlen/abweichend: {set(bericht.SPALTEN) ^ set(kopf)}")
        if ws.max_row - 1 != anzahl:
            fehler.append(f"Zeilen {ws.max_row - 1} ≠ Funde {anzahl}")
    formeln = [f"{ws.title}!{c.coordinate}" for ws in wb for row in ws.iter_rows() for c in row if c.data_type == "f"]
    if formeln:
        fehler.append(f"Formel-Zellen: {formeln[:3]}")
    return fehler


def bieterfragen_fehler(funde, ziel):
    bf = MODULE["bieterfragen"]
    zeilen = bf.bieterfragen(funde)
    hinweise = bf.ausgenommen(funde) if hasattr(bf, "ausgenommen") else []
    wb = load_workbook(bf.schreibe_xlsx(zeilen, ziel, hinweise) if hinweise else bf.schreibe_xlsx(zeilen, ziel))
    fehler = []
    ws = wb["Bieterfragen"]
    if [c.value for c in ws[2]] != bf.SPALTEN:
        fehler.append("Bieterfragen: Überschriften abweichend")
    if ws.max_row - 2 != len(zeilen) + len(hinweise):
        fehler.append(f"Bieterfragen: Zeilen {ws.max_row - 2} ≠ {len(zeilen)} + {len(hinweise)} Hinweise")
    if any(c.data_type == "f" for w in wb for row in w.iter_rows() for c in row):
        fehler.append("Bieterfragen: Formel-Zelle")
    return fehler, len(zeilen), [h for _, h in hinweise]


def eine_datei(pfad, tmp, integration):
    t0 = time.time()
    if pfad.suffix.lower() in NICHT_UNTERSTUETZT:
        return "HINWEIS", f"Format {pfad.suffix} wird von parse() nicht gelesen (bekannt)", Counter(), 0
    funde16, texte, info = bericht.pruefe_lv(pfad)
    df = parse(pfad)
    # B2-Integration (21.11.2026): pruefe_lv liefert Nr. 1–19; die Module nur noch aufrufen, wenn sie fehlen
    integriert = any(f["pruefung"] >= 7 for f in funde16) or "pruefung_hinweise" in str(bericht.alle_pruefungen.__doc__ or "")
    extra = [] if integriert else b2_funde(df, pfad, funde16)
    alle = funde16 + extra
    fehler = r5_fehler(alle, df)
    pos = df[df.typ == "Position"]
    for f in extra:
        texte[f["id"]] = [{"oz": p["oz"], "kurztext": next((r.kurztext or "" for r in pos.itertuples()
                                                            if r.oz == p["oz"]), ""),
                           "langtext": next((r.langtext or "" for r in pos.itertuples() if r.oz == p["oz"]), "")}
                          for p in f["positionen"]]
    mit = not info["nur_preise"]
    fehler += [f"Export Nr. 1–6: {x}" for x in export_fehler(
        bericht.risikobericht(pfad.name, funde16, texte, info, zeitpunkt=ZEITPUNKT, commit="durchlauf"), mit, len(funde16))]
    if extra:
        try:
            daten = bericht.risikobericht(pfad.name, alle, texte, info, zeitpunkt=ZEITPUNKT, commit="durchlauf")
        except KeyError:
            fehlt = {f["pruefung"] for f in alle} - set(bericht.PRUEFUNGEN)
            if not fehlt:
                raise                                    # anderer KeyError = echter Fehler
            integration.update(fehlt)
            alt = dict(bericht.PRUEFUNGEN)
            bericht.PRUEFUNGEN.update({k: v for k, v in namen_b2().items() if k not in alt})
            try:
                daten = bericht.risikobericht(pfad.name, alle, texte, info, zeitpunkt=ZEITPUNKT, commit="durchlauf")
            finally:
                bericht.PRUEFUNGEN.clear()
                bericht.PRUEFUNGEN.update(alt)
        fehler += [f"Export mit Nr. 7–19: {x}" for x in export_fehler(daten, mit, len(alle))]
    nb, bh = 0, []
    if "bieterfragen" in MODULE and alle:
        x, nb, bh = bieterfragen_fehler(alle, tmp / f"bieterfragen_{abs(hash(pfad.name)) % 10**8}.xlsx")
        fehler += x
    zahl = Counter(f["pruefung"] for f in alle)
    st16 = dict(sorted(Counter(f["stufe"] for f in funde16).items()))
    st_alle = dict(sorted(Counter(f["stufe"] for f in alle).items()))
    text = (f"{info['format']}, {info['positionen']} Positionen, {len(alle)} Funde "
            f"{dict(sorted(zahl.items()))}, Stufen Nr. 1–6 {st16}, Stufen alle {st_alle}, {nb} Bieterfragen{' (' + bh[0] + ')' if bh else ''}, "
            f"{time.time() - t0:.1f} s")
    if info["nur_preise"]:
        text += " (nur Preise)"
    return ("FEHLER", text + " | " + "; ".join(fehler[:5]) + (f" … (+{len(fehler) - 5})" if len(fehler) > 5 else ""),
            zahl, nb) if fehler else ("OK", text, zahl, nb)


def main(argv):
    d = Path(argv[1]) if len(argv) > 1 and not argv[1].startswith("--") else Path("data/raw")
    nur = set(argv[argv.index("--nur") + 1:]) if "--nur" in argv else None
    dateien = sorted(p for p in d.iterdir() if not p.name.startswith(".") and (nur is None or p.name in nur))
    print(f"Durchlauf über {len(dateien)} Dateien; B2-Module: {sorted(MODULE) or 'keine (main)'}")
    summe, ergebnisse, integration, bieter = Counter(), Counter(), set(), 0
    with tempfile.TemporaryDirectory() as t:
        for p in dateien:
            try:
                stufe, text, zahl, nb = eine_datei(p, Path(t), integration)
            except Exception as e:                                    # Absturz = FEHLER mit Ursache
                stufe, text, zahl, nb = "FEHLER", f"Absturz {type(e).__name__}: {e} | " + \
                    traceback.format_exc().strip().splitlines()[-3].strip(), Counter(), 0
            ergebnisse[stufe] += 1
            summe.update(zahl)
            bieter += nb
            print(f"{stufe:<8} {p.name}: {text}")
    print("\nZusammenfassung")
    print(f"  Dateien: {dict(ergebnisse)}")
    print(f"  Funde je Prüfung (INFO): {dict(sorted(summe.items()))}, gesamt {sum(summe.values())}; "
          f"Bieterfragen: {bieter}")
    if integration:
        print(f"  HINWEIS INTEGRATION: bericht.PRUEFUNGEN kennt Nr. {sorted(integration)} nicht; Export mit "
              f"Nr. 7–19 nur mit vorübergehend ergänzten Namen geprüft (Block B2-Integration, Sitzung B1)")
    print(f"\n{'ohne FEHLER' if not ergebnisse['FEHLER'] else str(ergebnisse['FEHLER']) + ' Datei(en) mit FEHLER'}")
    return 0 if not ergebnisse["FEHLER"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
