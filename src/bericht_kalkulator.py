"""
bericht_kalkulator.py - Kalkulatorsicht im Risikobericht (Team, 22.11.2026): Zusammenfassung, Risikoregister,
Risiken je Position und Bieterfragen als eigene Blätter vor den bestehenden Blättern.

Keine neue Regel, kein neuer Fund, keine geänderte Stufe, Kategorie oder Reihenfolge: Die Blätter ordnen die
vorhandenen Regel-Funde der Prüfungen Nr. 1–15 (Auftrag: „R1–R15“, Nr. 16–19 ausgeschlossen) nur an. Funde der
Prüfungen Nr. 16–19 stehen weiter vollständig im Blatt „Funde“; die Zusammenfassung nennt ihre Anzahl (E5).

Getrennt wird überall zwischen
- belegter Auffälligkeit: wörtliches Zitat aus dem LV (R5) und Befund der Regel, und
- möglicher kaufmännischer Folge: qualitative Kostenwirkung der Prüfung laut Prüfkatalog, nicht belegt und nicht
  beziffert (R11, E9). Keine Beträge, keine Summen, kein Score, keine Rechtsaussage (R7). KI-Angaben stehen hier
  nicht (E13). Reihenfolge fest aus sortiere() (E14).
"""
import re

from openpyxl.styles import Font, PatternFill

from bieterfragen import HINWEIS as HINWEIS_FRAGEN, ausgenommen, bieterfragen, empfehlung
from pruefung_formal import sortiere
from pruefung_widerspruch import normalisiere_leerzeichen

BIS_NR = 15                                          # Prüfungen Nr. 1–15 (Auftrag 22.11.2026)
BLAETTER = ["Zusammenfassung", "Risikoregister", "Risiken je Position", "Bieterfragen"]
TITEL = "Risikobericht für die Kalkulation"
TRENNUNG = ("Belegt = wörtlich im LV zitiert und von der Regel festgestellt. Mögliche kaufmännische Folge = "
            "Einordnung laut Prüfkatalog: nicht belegt, nicht beziffert, keine Rechtsaussage.")
AUSGESCHLOSSEN = "nicht Gegenstand dieses Berichts; vollständig im Blatt „Funde“ aufgeführt"
STUFE_FARBE = {1: "F4CCCC", 2: "FCE5CD", 3: "FFF2CC", 4: "D9EAD3"}
KOPF_FARBE = "D9D9D9"
# Handlungsempfehlungen in fester Reihenfolge; Werte aus bieterfragen.empfehlung() (je Fund, FS-B2-11)
MASSNAHMEN = [
    ("Rückfrage stellen", ("klärende rückfrage", "rückfrage stellen"),
     "vor der Angebotsabgabe beim Auftraggeber klären; Entwürfe im Blatt „Bieterfragen“"),
    ("Risiko einpreisen", ("risiko einpreisen",),
     "Mengen-, Abruf- bzw. Pauschalrisiko bei der Kalkulation dieser Positionen berücksichtigen; die Höhe legt der "
     "Kalkulator fest"),
    ("vormerken", ("vormerken",),
     "für Arbeitsvorbereitung und Ausführung vormerken (mögliches Nachtragspotenzial, offene Kosten in der Ausführung)"),
    ("nur Hinweis", ("nur hinweis",), "beim Lesen der Position beachten; keine eigene Maßnahme"),
]
REGISTER_SPALTEN = ["Risiko-Nr.", "Stufe", "Regel (Prüfung)", "Kategorie", "Anzahl Fundstellen", "OZ (alle Fundstellen)",
                    "Belegte Auffälligkeit (Regel)", "Art der Kostenwirkung",
                    "Mögliche kaufmännische Folge (nicht belegt, nicht beziffert)", "Handlungsempfehlung",
                    "Bieterfragen (Anzahl)"]
REGISTER_BREITEN = [10, 26, 36, 22, 12, 50, 40, 16, 70, 22, 12]
DETAIL_SPALTEN = ["Nr.", "Risiko-Nr.", "Stufe", "Regel (Prüfung)", "Kategorie", "OZ", "Kurztext",
                  "Originaltext (wörtlich aus dem LV)", "Fundstelle", "Beleg am Original",
                  "Belegte Auffälligkeit (Befund)", "Mögliche kaufmännische Folge (nicht belegt, nicht beziffert)",
                  "Handlungsempfehlung", "Bieterfrage (Entwurf)", "Menge (LV)", "Einheit (LV)", "EP (€, LV)",
                  "GP (€, LV)", "Status", "Fund-ID"]
DETAIL_BREITEN = [6, 10, 26, 34, 22, 14, 40, 60, 14, 22, 50, 60, 20, 60, 12, 10, 12, 14, 16, 44]
FRAGEN_SPALTEN = ["Nr.", "OZ", "Regel (Prüfung)", "Frage (Entwurf)", "Beleg (wörtlich aus dem LV)", "Risiko-Nr.",
                  "Status des Funds", "Fund-ID"]
FRAGEN_BREITEN = [6, 14, 36, 70, 60, 10, 18, 44]
ZAHLEN = {"Menge (LV)": "#,##0.000", "EP (€, LV)": "#,##0.00#", "GP (€, LV)": "#,##0.00"}
BELEG_KURZ = {"geprüft": "wörtlich im Original bestätigt", "ungeprüft": "Abgleich mit dem Original steht aus",
              "nicht im Original": "so nicht im Original – prüfen"}
EMPFEHLUNG_SATZ = re.compile(r"\s*Empfehlung[^.:]*:[^.]*\.?\s*$")


def im_bericht(funde):
    """Funde der Prüfungen Nr. 1–15 in der Sortierung der App (Stufe, Rang in Stufe, OZ)."""
    return [f for f in sortiere(funde) if f["pruefung"] <= BIS_NR]


def gruppen(funde):
    """Zusammengehörige Funde: gleiche Prüfung, Kategorie, Stufe und Rang. Reihenfolge = erstes Auftreten in der
    Sortierung; jede Fundstelle bleibt in `funde` der Gruppe erhalten."""
    aus = {}
    for f in im_bericht(funde):
        aus.setdefault((f["stufe"], f["prioritaet_in_stufe"], f["pruefung"], f["kategorie"]), []).append(f)
    return [{"nr": i, "stufe": k[0], "pruefung": k[2], "kategorie": k[3], "funde": fs}
            for i, (k, fs) in enumerate(aus.items(), start=1)]


def _oz(f):
    return ", ".join(p["oz"] for p in f["positionen"])


def _befund(f):
    """Befund der Regel ohne den angehängten Empfehlungssatz (der steht in eigener Spalte)."""
    return EMPFEHLUNG_SATZ.sub("", f["begruendung"]).strip() or f["titel"]


def _empfehlungen(fs):
    werte = []
    for f in fs:
        e = empfehlung(f)[0]
        if e and e not in werte:
            werte.append(e)
    return ", ".join(werte)


def _kostenart(text):
    return text.split(":", 1)[0] if ":" in text else ""


def _kostenfolge(text):
    return text.split(":", 1)[1].strip() if ":" in text else text


def _aufzaehlung(werte, hoechstens=12):
    werte = list(werte)
    if len(werte) <= hoechstens:
        return ", ".join(werte)
    return ", ".join(werte[:hoechstens]) + f" und {len(werte) - hoechstens} weitere"


def _kopf(ws, zeile, spalten, breiten, schreibe):
    fill = PatternFill("solid", fgColor=KOPF_FARBE)
    for j, s in enumerate(spalten, start=1):
        schreibe(ws, zeile, j, s, fett=True, umbruch=True).fill = fill
        ws.column_dimensions[ws.cell(row=zeile, column=j).column_letter].width = breiten[j - 1]
    ws.row_dimensions[zeile].height = 45


def _druck(ws):
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True


def schreibe(wb, lv_name, funde, texte, info, s2, schreibe_zelle, beleg_pruefung, pruefungen, stufen, kostenwirkung,
             schlusssatz):
    """Hängt die vier Blätter vor die bestehenden. Parameter aus bericht.py, damit es keinen Kreisimport gibt."""
    alle = sortiere(funde)
    liste = im_bericht(funde)
    grp = gruppen(funde)
    risiko_nr = {f["id"]: g["nr"] for g in grp for f in g["funde"]}
    fragen = [z for z in bieterfragen(liste)]
    frage_von = {z["Fund-ID"]: z["Frage (Entwurf)"] for z in fragen}
    auftrag = ausgenommen(liste)
    stufe_text = lambda s: f"{s} – {stufen[s]}"
    regel = lambda nr: f"Nr. {nr} – {pruefungen[nr]}"

    # ------------------------------------------------------------------ Zusammenfassung
    ws = wb.create_sheet(BLAETTER[0])
    z = [1]

    def zeile(a=None, b=None, c=None, fett=False, farbe=None):
        if a is not None:
            zelle = schreibe_zelle(ws, z[0], 1, a, fett=fett, umbruch=True)
            if farbe:
                zelle.fill = PatternFill("solid", fgColor=farbe)
        if b is not None:
            schreibe_zelle(ws, z[0], 2, b, umbruch=True)
        if c is not None:
            schreibe_zelle(ws, z[0], 3, c, umbruch=True)
        z[0] += 1

    zeile(f"{TITEL} – {lv_name}", fett=True)
    ws.cell(row=1, column=1).font = Font(bold=True, size=14)
    zeile(TRENNUNG)
    ws.merge_cells("A1:C1")
    ws.merge_cells("A2:C2")
    ws.row_dimensions[2].height = 32              # verbundene Zelle: Excel passt die Höhe nicht selbst an
    zeile()
    zeile("Kurzfassung", fett=True)
    zeile("LV-Datei", lv_name)
    zeile("Positionen im LV", info["positionen"])
    zeile("Funde in diesem Bericht", len(liste), f"Prüfungen Nr. 1–{BIS_NR}; von {len(alle)} Funden gesamt")
    rest = [f for f in alle if f["pruefung"] > BIS_NR]
    if rest:
        je = {}
        for f in rest:
            je[f["pruefung"]] = je.get(f["pruefung"], 0) + 1
        zeile(f"Prüfungen Nr. {BIS_NR + 1}–19", len(rest),
              AUSGESCHLOSSEN + " (" + ", ".join(f"Nr. {k}: {v}" for k, v in sorted(je.items())) + ")")
    for s in (1, 2, 3, 4):
        zeile(f"Stufe {stufe_text(s)}", sum(f["stufe"] == s for f in liste), farbe=STUFE_FARBE[s])
    zeile("Zusammengefasste Risiken", len(grp), "Zeilen im Blatt „Risikoregister“; jede Fundstelle steht einzeln im "
                                                "Blatt „Risiken je Position“")
    zeile("Bieterfragen (Entwurf)", len(fragen), auftrag[0][1] if auftrag else "Blatt „Bieterfragen“")
    zeile()
    zeile("Fazit", fett=True)
    for s, satz in ((1, "Zuerst klären"), (2, "Beim Preis berücksichtigen"), (3, "Für die Ausführung vormerken"),
                    (4, "Beim Lesen beachten")):
        fs = [f for f in liste if f["stufe"] == s]
        if fs:
            nrn = []
            for f in fs:
                if f["pruefung"] not in nrn:
                    nrn.append(f["pruefung"])
            zeile(satz, f"{len(fs)} Fundstellen der Stufe {stufe_text(s)}: "
                        + "; ".join(f"{pruefungen[n]} ({sum(f['pruefung'] == n for f in fs)})" for n in nrn))
    if not liste:
        zeile("Keine Funde", f"Die Prüfungen Nr. 1–{BIS_NR} haben in diesem LV nichts gefunden. Das heißt nicht, "
                             "dass das LV vollständig oder fehlerfrei ist.")
    zeile()
    zeile("Wichtigste Risiken (Reihenfolge wie im Risikoregister)", fett=True)
    for g in grp[:10]:
        zeile(f"Risiko-Nr. {g['nr']} · Stufe {stufe_text(g['stufe'])}",
              f"{regel(g['pruefung'])} ({g['kategorie']}) · {len(g['funde'])} Fundstelle(n): OZ "
              + _aufzaehlung(_oz(f) for f in g["funde"]),
              _empfehlungen(g["funde"]), farbe=STUFE_FARBE[g["stufe"]])
    zeile()
    zeile("Mögliche kaufmännische Auswirkungen (nicht belegt, nicht beziffert)", fett=True)
    gesehen = []
    for g in grp:
        if g["pruefung"] in gesehen:
            continue
        gesehen.append(g["pruefung"])
        n = sum(f["pruefung"] == g["pruefung"] for f in liste)
        kw = kostenwirkung.get(g["pruefung"], "nicht bewertet")
        zeile(f"{regel(g['pruefung'])} ({n})", _kostenfolge(kw), _kostenart(kw))
    zeile()
    zeile("Handlungsempfehlungen", fett=True)
    for name, werte, was in MASSNAHMEN:
        fs = [f for f in liste if empfehlung(f)[0].lower() in werte]
        if fs:
            nrn = []
            for f in fs:
                if f["pruefung"] not in nrn:
                    nrn.append(f["pruefung"])
            zeile(f"{name} ({len(fs)})", was, "Prüfungen " + ", ".join(f"Nr. {n}" for n in sorted(nrn)))
    zeile()
    zeile(schlusssatz, fett=True)
    ws.column_dimensions["A"].width = 46
    ws.column_dimensions["B"].width = 95
    ws.column_dimensions["C"].width = 55
    _druck(ws)

    # ------------------------------------------------------------------ Risikoregister (zusammengefasst)
    ws = wb.create_sheet(BLAETTER[1])
    _kopf(ws, 1, REGISTER_SPALTEN, REGISTER_BREITEN, schreibe_zelle)
    for i, g in enumerate(grp, start=2):
        titel = []
        for f in g["funde"]:
            if f["titel"] not in titel:
                titel.append(f["titel"])
        kw = kostenwirkung.get(g["pruefung"], "nicht bewertet")
        werte = [g["nr"], stufe_text(g["stufe"]), regel(g["pruefung"]), g["kategorie"], len(g["funde"]),
                 ", ".join(_oz(f) for f in g["funde"]), "; ".join(titel), _kostenart(kw), _kostenfolge(kw),
                 _empfehlungen(g["funde"]), sum(f["id"] in frage_von for f in g["funde"])]
        for j, v in enumerate(werte, start=1):
            c = schreibe_zelle(ws, i, j, v, umbruch=True)
            if j == 2:
                c.fill = PatternFill("solid", fgColor=STUFE_FARBE[g["stufe"]])
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:{ws.cell(row=1, column=len(REGISTER_SPALTEN)).column_letter}{max(len(grp) + 1, 2)}"
    _druck(ws)

    # ------------------------------------------------------------------ Risiken je Position (jede Fundstelle)
    ws = wb.create_sheet(BLAETTER[2])
    _kopf(ws, 1, DETAIL_SPALTEN, DETAIL_BREITEN, schreibe_zelle)
    for i, f in enumerate(liste, start=2):
        ts = texte.get(f["id"], [])
        kurz = []
        for t in ts:
            k = normalisiere_leerzeichen(t["kurztext"])
            if k and k not in kurz:
                kurz.append(k)
        erste = ts[0] if ts else {}
        seiten = [str(p["seite"]) for p in f["positionen"] if p["seite"] is not None]
        leer = lambda v: "" if v is None else v
        werte = [i - 1, risiko_nr[f["id"]], stufe_text(f["stufe"]), regel(f["pruefung"]), f["kategorie"], _oz(f),
                 " | ".join(kurz), "\n".join(f"„{b}“" for b in f["belege"]),
                 ("S. " + ", ".join(seiten)) if seiten else "OZ (Datei ohne Seiten)",
                 BELEG_KURZ[beleg_pruefung(f, s2)], _befund(f),
                 kostenwirkung.get(f["pruefung"], "nicht bewertet"), empfehlung(f)[0], frage_von.get(f["id"], ""),
                 leer(erste.get("menge")), erste.get("einheit") or "", leer(erste.get("ep")), leer(erste.get("gp")),
                 f.get("status") or "offen", f["id"]]
        for j, v in enumerate(werte, start=1):
            c = schreibe_zelle(ws, i, j, v, umbruch=True)
            if DETAIL_SPALTEN[j - 1] in ZAHLEN and isinstance(v, float):
                c.number_format = ZAHLEN[DETAIL_SPALTEN[j - 1]]
            if j == 3:
                c.fill = PatternFill("solid", fgColor=STUFE_FARBE[f["stufe"]])
    ws.freeze_panes = "B2"
    ws.auto_filter.ref = f"A1:{ws.cell(row=1, column=len(DETAIL_SPALTEN)).column_letter}{max(len(liste) + 1, 2)}"
    _druck(ws)

    # ------------------------------------------------------------------ Bieterfragen
    ws = wb.create_sheet(BLAETTER[3])
    schreibe_zelle(ws, 1, 1, HINWEIS_FRAGEN, fett=True)
    _kopf(ws, 2, FRAGEN_SPALTEN, FRAGEN_BREITEN, schreibe_zelle)
    zeile_nr = 3
    for q in fragen:
        werte = [q["Nr."], q["OZ"], regel(int(q["Fund-ID"].split("|", 1)[0])), q["Frage (Entwurf)"],
                 q["Beleg (wörtlich aus dem LV)"], risiko_nr[q["Fund-ID"]], q["Status des Funds"], q["Fund-ID"]]
        for j, v in enumerate(werte, start=1):
            schreibe_zelle(ws, zeile_nr, j, v, umbruch=True)
        zeile_nr += 1
    for _datei, h in auftrag:
        schreibe_zelle(ws, zeile_nr, 4, h, fett=True)
        zeile_nr += 1
    if not fragen and not auftrag:
        schreibe_zelle(ws, zeile_nr, 4, "Keine Funde mit der Empfehlung „Rückfrage stellen“ in diesem LV.")
    ws.freeze_panes = "A3"
    _druck(ws)

    # vor die bestehenden Blätter stellen, Zusammenfassung beim Öffnen sichtbar
    for k, name in enumerate(BLAETTER):
        blatt = wb[name]
        wb.move_sheet(blatt, offset=k - wb.index(blatt))
    wb.active = 0
    for blatt in wb.worksheets:
        blatt.sheet_view.tabSelected = blatt is wb.worksheets[0]
