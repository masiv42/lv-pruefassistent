"""
nachtrag_streit.py - M2b: Sicht „Nachtragspotenzial und Streitpunkte“ (Team, 22.11.2026, 01:25).

Keine neue Regel und keine neuen Funde: Die Sicht ordnet vorhandene Regel-Funde mit wörtlichem Beleg (R5) zwei Abschnitten
zu. Zahlen sind nur Zählungen je LV, keine Beträge und kein Score (R11, E9). Begriffe nach R7. KI-Vorschläge stehen hier
nicht (E13). Die Zuordnung steht nur in ABSCHNITTE; NICHT_ZUGEORDNET nennt, was nach Prüfung am Katalog herausgefallen ist.
"""
from bericht import PRUEFUNGEN, STUFEN
from bieterfragen import bieterfragen, empfehlung
from pruefung_formal import sortiere
from pruefung_widerspruch import normalisiere_leerzeichen

HINWEIS = "Hinweise zur Prüfung, keine Rechtsaussage."
BLATT = "Nachtrag und Streitpunkte"
SEITENTITEL = "Nachtragspotenzial und Streitpunkte"
# Zentrale Zuordnung (Team 01:25): A = alle Prüfungen der Stufe 3; B = widersprüchliche Angaben und Unklarheiten
ABSCHNITTE = {
    "A": {"titel": "mögliches Nachtragspotenzial", "pruefungen": (7, 8, 9, 10, 19),
          "erklaerung": "Funde der Stufe 3: Leistungen, bei denen Kosten oder Umfang in der Ausführung offen sein können."},
    "B": {"titel": "möglicher Streitpunkt in der Ausführung", "pruefungen": (1, 2, 16, 11, 12, 14),
          "erklaerung": "Widersprüchliche oder unklare Angaben im LV, die in der Ausführung unterschiedlich gelesen werden "
                        "können."},
}
# Prüflogik gegen input/pruefkatalog.md (Team 01:25: „Passt eine nicht, fällt sie heraus, mit Eintrag“, Lücke L58)
NICHT_ZUGEORDNET = {13: "Stundenlohnarbeiten: Kategorie laut Katalog „Risikohinweis“, weder Widerspruch noch Unklarheit; die "
                        "Kostenwirkung betrifft Verrechnungssatz und Stundenansatz, nicht die Lesart des LV-Textes."}
SPALTEN = ["Nr.", "Abschnitt", "OZ", "Kurztext", "Beleg (wörtlich aus dem LV)", "Prüfung", "Kategorie", "Stufe",
           "Handlungsempfehlung", "Bieterfrage (Entwurf)", "Status", "Fund-ID"]
BREITEN = [6, 34, 14, 40, 60, 34, 22, 26, 20, 60, 16, 44]
UMBRUCH = {"Kurztext", "Beleg (wörtlich aus dem LV)", "Bieterfrage (Entwurf)"}
KEINE = "Keine Funde in diesem Abschnitt. Das heißt nicht, dass es hier keine offenen Punkte gibt."


def auswahl(funde):
    """{Abschnitt: Funde}, je Abschnitt sortiert nach Stufe, Rang in Stufe, OZ (E14). Ändert keinen Fund."""
    return {k: sortiere([f for f in funde if f["pruefung"] in a["pruefungen"]]) for k, a in ABSCHNITTE.items()}


def zaehlung(funde):
    """Nur Zählungen je Abschnitt und Prüfung (R11, E9)."""
    aus = {}
    for k, liste in auswahl(funde).items():
        je = {nr: sum(f["pruefung"] == nr for f in liste) for nr in ABSCHNITTE[k]["pruefungen"]}
        aus[k] = {"gesamt": len(liste), "je_pruefung": je}
    return aus


def _kurztext(f, kurztext_von):
    teile = []
    for p in f["positionen"]:
        k = normalisiere_leerzeichen(kurztext_von(p["oz"]) or "")
        if k and k not in teile:
            teile.append(k)
    return " | ".join(teile)


def zeilen(funde, kurztext_von):
    """Zeilen (Dict je Fund, Schlüssel = SPALTEN) in der Reihenfolge A, B. `kurztext_von(oz)` liefert den Kurztext."""
    fragen = {z["Fund-ID"]: z["Frage (Entwurf)"] for z in bieterfragen(funde)}
    aus = []
    for k, liste in auswahl(funde).items():
        for f in liste:
            aus.append({"Nr.": len(aus) + 1, "Abschnitt": ABSCHNITTE[k]["titel"],
                        "OZ": ", ".join(p["oz"] for p in f["positionen"]), "Kurztext": _kurztext(f, kurztext_von),
                        "Beleg (wörtlich aus dem LV)": "\n".join(f"„{b}“" for b in f["belege"]),
                        "Prüfung": f"{f['pruefung']} – {PRUEFUNGEN[f['pruefung']]}", "Kategorie": f["kategorie"],
                        "Stufe": f"{f['stufe']} – {STUFEN[f['stufe']]}", "Handlungsempfehlung": empfehlung(f)[0],
                        "Bieterfrage (Entwurf)": fragen.get(f["id"], ""), "Status": f.get("status") or "offen",
                        "Fund-ID": f["id"]})
    return aus


def schreibe(wb, funde, texte, schreibe_zelle):
    """Hängt das Blatt an die Arbeitsmappe an. `schreibe_zelle` = bericht._schreibe (Text bleibt Text)."""
    kurz = {t["oz"]: t["kurztext"] for ts in texte.values() for t in ts}
    ws = wb.create_sheet(BLATT)
    schreibe_zelle(ws, 1, 1, SEITENTITEL, fett=True)
    schreibe_zelle(ws, 2, 1, HINWEIS, fett=True)
    z = 3
    for k, e in zaehlung(funde).items():
        je = ", ".join(f"Nr. {nr}: {n}" for nr, n in e["je_pruefung"].items())
        schreibe_zelle(ws, z, 1, f"{ABSCHNITTE[k]['titel']}: {e['gesamt']} Funde ({je})")
        z += 1
    kopf = z + 1
    for j, s in enumerate(SPALTEN, start=1):
        schreibe_zelle(ws, kopf, j, s, fett=True, umbruch=True)
    daten = zeilen(funde, kurz.get)
    for i, r in enumerate(daten, start=1):
        for j, s in enumerate(SPALTEN, start=1):
            schreibe_zelle(ws, kopf + i, j, r[s], umbruch=s in UMBRUCH)
    if not daten:
        schreibe_zelle(ws, kopf + 1, 1, KEINE)
    for j, b in enumerate(BREITEN, start=1):
        ws.column_dimensions[ws.cell(row=kopf, column=j).column_letter].width = b
    ws.freeze_panes = ws.cell(row=kopf + 1, column=1)
    ws.auto_filter.ref = f"A{kopf}:{ws.cell(row=kopf, column=len(SPALTEN)).column_letter}{kopf + max(len(daten), 1)}"
    return len(daten)
