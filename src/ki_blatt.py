"""
ki_blatt.py - Blatt „KI-Vorschläge“ im Risikobericht (M2, Lücke L48; Team 21.11.2026, 23:55).

Zeigt die KI-Vorschläge aus B5 (Tippfehler, Widerspruch zwischen Positionen) getrennt von den Regel-Funden. Liest nur den
KI-Cache (kein API-Aufruf, E14). Ins Blatt kommen nur gültige Vorschläge: `ki_b5.bewerte` prüft jedes Zitat gegen den
aktuellen Text der Position (R5), Entwarnungen erzeugen keine Zeile (E13). Das Blatt ändert keinen Regel-Fund.
"""
import re

import ki_b5
from ki_pruefung import lade_konfig

BLATT = "KI-Vorschläge"
TITEL = "KI-Vorschläge – getrennt von den Regel-Funden"
WARNHINWEIS = ("Nur KI-Vorschlag, kein Regel-Fund. Die KI entwarnt nie: Diese Zeilen ändern weder Priorität, Kategorie, "
               "Sortierung, Filter noch Hervorhebung eines Regel-Funds. Fehlt hier ein Vorschlag, heißt das nicht, dass "
               "kein Fehler vorliegt. Bitte jeden Vorschlag am Text der Position prüfen; die Entscheidung trifft die "
               "kalkulierende Person.")
MESSUNG = ("Messung an 32 erfundenen Fällen (Stand 21.11.2026): 27 richtig, kein falscher Vorschlag sichtbar, "
           "3 von 8 Widersprüchen nicht erkannt. Keine Treffsicherheit am Datensatz.")
NAMEN = {"tippfehler": "Tippfehler", "widerspruch": "Widerspruch zwischen Positionen"}
SPALTEN = ["Nr.", "KI-Prüfung", "OZ", "Zitat (wörtlich aus dem LV)", "KI-Vorschlag", "KI-Begründung", "Rückfrage-Entwurf (KI)",
           "Kategorie (Vorschlag)", "Stufe (Vorschlag)", "Empfehlung", "Quelle", "KI-Modell", "Prompt-Version"]
BREITEN = [6, 28, 18, 60, 34, 50, 50, 20, 10, 16, 10, 24, 12]
UMBRUCH = {"Zitat (wörtlich aus dem LV)", "KI-Vorschlag", "KI-Begründung", "Rückfrage-Entwurf (KI)"}
KEINE = "Keine KI-Vorschläge im Cache für dieses LV."
# Das LV ist fremder Text und könnte die KI beeinflussen. Freitext der KI wird deshalb nur übernommen, wenn er kurz und
# einzeilig ist und weder Link noch Kontaktdaten oder Markdown-Verweise enthält (L59). Prompt und Prüfkette bleiben (E12 (3)).
MAX_FREITEXT = 600
AUFFAELLIG_RE = re.compile(r"https?:|www\.|\b[\w.+-]+@[\w-]+\.\w+|\b(?:\+|00)\d[\d /-]{6,}|!?\[[^\]]*\]\(|<[a-zA-Z/!]", re.I)
FREITEXT = ("korrektur", "begruendung", "rueckfrage")


def unbedenklich(v):
    """False, wenn ein Freitextfeld der KI-Antwort auffällig ist; der Vorschlag wird dann nicht angezeigt."""
    for k in FREITEXT:
        t = v["antwort"].get(k) or ""
        if len(t) > MAX_FREITEXT or "\n" in t or "\r" in t or AUFFAELLIG_RE.search(t):
            return False
    return True


def lade(info, konfig=None, cache_dir=None):
    """Je KI-Prüfung {gesamt, geprueft, vorschlaege, zurueckgehalten, aktiv}; nur aus dem Cache (max_aufrufe=0)."""
    konfig = konfig if konfig is not None else lade_konfig()
    kw = {"cache_dir": cache_dir} if cache_dir is not None else {}
    aus = {}
    for pr in NAMEN:
        gruppen = (info.get("b5") or {}).get(pr) or []
        erg, stat = ki_b5.pruefe(pr, gruppen, konfig, max_aufrufe=0, **kw)
        alle = ki_b5.vorschlaege(pr, erg)
        gut = [v for v in alle if unbedenklich(v)]
        aus[pr] = {"gesamt": len(gruppen), "geprueft": stat["cache_treffer"], "vorschlaege": gut,
                   "zurueckgehalten": len(alle) - len(gut), "aktiv": bool(konfig.aktiv and konfig.modell)}
    return aus


def zeile(v, nr):
    """Werte einer Zeile (Reihenfolge wie SPALTEN)."""
    a = v["antwort"]
    if v["pruefung"] == "tippfehler":
        oz, zitat, vorschlag, rueckfrage = v["positionen"][0], f"„{a['zitat']}“", f"vermutlich „{a['korrektur']}“", ""
    else:
        oz = f"{a['oz_a']} ↔ {a['oz_b']}"
        zitat = f"OZ {a['oz_a']}: „{a['zitat_a']}“\nOZ {a['oz_b']}: „{a['zitat_b']}“"
        vorschlag, rueckfrage = a["einordnung"], a["rueckfrage"]
    return [nr, NAMEN[v["pruefung"]], oz, zitat, f"KI-Vorschlag: {vorschlag}", a["begruendung"], rueckfrage,
            v["kategorie_vorschlag"], v["stufe_vorschlag"], v["empfehlung"], v["quelle"], v["modell"], v["prompt_version"]]


def stand_zeile(pr, e):
    if not e["aktiv"]:
        return f"{NAMEN[pr]}: KI aus (kein API-Key), Cache nicht gelesen"
    zurueck = f", {e['zurueckgehalten']} wegen auffälligem KI-Text nicht übernommen" if e["zurueckgehalten"] else ""
    return (f"{NAMEN[pr]}: {e['geprueft']} von {e['gesamt']} geprüft, {len(e['vorschlaege'])} KI-Vorschläge{zurueck} "
            f"(Prompt {ki_b5.VERSION[pr]})")


def schreibe(wb, info, schreibe_zelle, konfig=None, cache_dir=None):
    """Hängt das Blatt an die Arbeitsmappe an. `schreibe_zelle` = bericht._schreibe (Text bleibt Text)."""
    daten = lade(info, konfig, cache_dir)
    ws = wb.create_sheet(BLATT)
    schreibe_zelle(ws, 1, 1, TITEL, fett=True)
    schreibe_zelle(ws, 2, 1, WARNHINWEIS, fett=True, umbruch=True)
    schreibe_zelle(ws, 3, 1, MESSUNG, umbruch=True)
    z = 4
    for pr, e in daten.items():
        schreibe_zelle(ws, z, 1, stand_zeile(pr, e))
        z += 1
    for k in (2, 3):
        ws.merge_cells(start_row=k, start_column=1, end_row=k, end_column=7)
        ws.row_dimensions[k].height = 48
    z += 1
    kopf = z
    for j, s in enumerate(SPALTEN, start=1):
        schreibe_zelle(ws, kopf, j, s, fett=True, umbruch=True)
    vorschlaege = [v for e in daten.values() for v in e["vorschlaege"]]
    for i, v in enumerate(vorschlaege, start=1):
        for j, w in enumerate(zeile(v, i), start=1):
            schreibe_zelle(ws, kopf + i, j, w, umbruch=SPALTEN[j - 1] in UMBRUCH)
    if not vorschlaege:
        schreibe_zelle(ws, kopf + 1, 1, KEINE)
    for j, b in enumerate(BREITEN, start=1):
        ws.column_dimensions[ws.cell(row=kopf, column=j).column_letter].width = b
    return len(vorschlaege)
