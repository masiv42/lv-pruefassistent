"""
bericht.py - Risikobericht als Excel-Datei (P3) und gemeinsame Auswertung für App und Bericht.

Vorgaben des Teams (Chat 21.11.2026, P3):
- Dateiname: Risikobericht_<LV-Dateiname ohne Endung>_<JJJJ-MM-TT>.xlsx
- Blatt „Übersicht“: Datei, Prüfsumme (fingerprint), Zeitpunkt der Prüfung, Git-Commit des
  Tools, Anzahl Positionen, Funde je Priorität und je Kategorie, Datei-Hinweise und der feste
  Satz „Automatisch erzeugte Hinweise zur Prüfung durch den Kalkulator. Keine Rechtsberatung.“
- Blatt „Funde“: immer alle Funde (unabhängig vom Filter der App), Sortierung wie in der App;
  Kopfzeile fixiert, Autofilter; Spalte „Entscheidung Kalkulator“ mit Auswahlliste,
  vorausgefüllt mit der Entscheidung aus der App (P3b), in Excel änderbar.
- Zeitpunkt der Prüfung mit Zeitzone, z. B. „2026-11-21 03:30 MEZ“ (P3b).
- Alle Texte werden als Text geschrieben (auch wenn sie mit „=“ beginnen: keine Formeln).
- Reine Preisdatei: nur Blatt „Übersicht“ mit Hinweis.
- KI-Gegenprüfung (P4): Spalten KI-Einordnung, KI-Begründung, KI-Zitat geprüft,
  Rückfrage-Entwurf (KI), KI-Modell, Prompt-Version; nur für Funde Nr. 1/2.
- B0b.6 / Leitplanke E13 (Team, 21.11.2026): Die KI darf nie entwarnen. Bei den KI-Einordnungen
  „anderes Bauteil“ und „Bereichs- oder Mehrfachangabe“ steht in der Fundliste der App nur
  „KI-Hinweis im Detail“; Detailansicht und Export zeigen die Einordnung mit KI_WARNHINWEIS
  (Export-Spalte „KI-Warnhinweis“). Stufe, Priorität, Kategorie und Sortierung bleiben unverändert.
- B1a (Team, 21.11.2026): Spalten „Stufe“ und „Priorität“ (Rang innerhalb der Stufe, F1); Sortierung
  Stufe, Priorität, OZ; Übersicht „Funde je Stufe“ und Prüfstand (Commit, Bibliotheksversionen,
  Prompt-Version, SHA-256 der Datei; src/pruefstand.py, L24); Spalte „KI-Quelle“ (Cache / API /
  noch nicht KI-geprüft, L25).
- B1b (Team, 21.11.2026, Nachtrag 3): Übersicht „Prüfabdeckung Nr. n“ je Prüfung („prüfbar in N von M
  Positionen“ mit Grund; src/pruefabdeckung.py).
- B1r (Team, 21.11.2026, L43): Bericht für Kalkulatoren lesbar – Spalte „Nr.“ (laufende Nummer in
  Sortierreihenfolge), Stufe als Text, Menge/Einheit/EP (€)/GP (€) aus der Position (keine eigene Rechnung,
  E9), Rang ganz hinten mit Erklärung in der Überschrift, Überschriften umbrochen und vollständig lesbar;
  Übersicht zweigeteilt („Für den Kalkulator“ / „Prüfstand (technisch)“) mit Erklärung je Zeile; Warnzeile bei
  „-dirty“; KI-Warnhinweis ohne Dateipfad; Beleg-Status nach docs/pruefprotokoll.md; Blatt „Legende“.
- B1b (Team, 21.11.2026, F4): Stufen-Namen „1 – Fehlerprüfung“, „2 – Kalkulationsrisiko“,
  „3 – mögliches Nachtragspotenzial“, „4 – Unklarheit“; Spalte „Rang in Stufe“ statt „Priorität“.
"""
import io
import json
import re
from datetime import datetime
from pathlib import Path

from openpyxl import Workbook
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
from openpyxl.styles import Alignment, Font
from openpyxl.worksheet.datavalidation import DataValidation

import pruefabdeckung
import pruefstand
from lv_parser import parse, fingerprint
from pruefung_formal import alle_pruefungen, nur_preise, sortiere, datei_hinweis
from pruefung_widerspruch import normalisiere_leerzeichen

ROOT = Path(__file__).resolve().parent.parent
S2_ERGEBNIS = ROOT / "data" / "qa" / "s2_ergebnis.json"     # Prüfung der Belege am Original

NUR_PREISE_TEXT = "Datei enthält nur Preise, bitte das LV mit Texten hochladen."
SCHLUSSSATZ = "Automatisch erzeugte Hinweise zur Prüfung durch den Kalkulator. Keine Rechtsberatung."
PRUEFUNGEN = {1: "Nennweite (DN) im Kurztext ≠ Langtext", 2: "Betonfestigkeitsklasse im Kurztext ≠ Langtext",
              3: "Menge oder Einheit fehlt", 4: "OZ doppelt im selben LV", 5: "Bedarfsposition", 6: "Pauschale",
              7: "Produktvorgabe „oder gleichwertig“", 8: "Bestand, vorhandene Anlagen", 9: "Entsorgung, Boden",
              10: "Vorhalten, bauzeitabhängig", 11: "Vage Formulierung", 12: "Verweistext („wie vor, jedoch“)",
              13: "Stundenlohnarbeiten", 14: "Position enthält Bild/Skizze",
              15: "Zulage ohne erkennbare Grundposition", 16: "Gleiche Leistung zweimal im selben Abschnitt",
              17: "Rechenprüfung Menge × EP ≠ GP", 18: "Ungewöhnliche Mengen (Menge 1 bei Mengeneinheit)",
              19: "Mögliche fehlende Leistung"}           # Namen laut input/pruefkatalog.md (FS-B2-9)
# Anzeige-Namen der Stufen in App und Export (Team, 21.11.2026, F4; E3 bleibt unverändert)
# Prüfer-Zuordnung je Prüfung (B1e; vom Team festgelegt, 21.11.2026, F1 in docs/decisions.md). Prüfer laut
# Backlog: Formal, Widerspruch, Nachtrag, Klarheit, Mengen, Vollständigkeit, Preis, Tippfehler (Tippfehler: B5, KI).
PRUEFER = {1: "Widerspruch", 2: "Widerspruch", 3: "Formal", 4: "Formal", 5: "Mengen", 6: "Mengen",
           7: "Nachtrag", 8: "Nachtrag", 9: "Nachtrag", 10: "Nachtrag", 11: "Klarheit", 12: "Klarheit",
           13: "Mengen", 14: "Klarheit", 15: "Formal", 16: "Widerspruch", 17: "Preis", 18: "Mengen",
           19: "Vollständigkeit"}
STUFEN = {1: "Fehlerprüfung", 2: "Kalkulationsrisiko", 3: "mögliches Nachtragspotenzial", 4: "Unklarheit"}
RANG = "Rang in Stufe"                       # Spaltenname für prioritaet_in_stufe (Team, 21.11.2026, F4)
SORTIERUNG = f"Stufe, dann {RANG}, dann OZ"
KATEGORIEN = ["nachweisbarer Fehler", "möglicher Widerspruch", "Unklarheit", "Risikohinweis"]   # R6
ENTSCHEIDUNGEN = ["bestätigt", "verworfen", "Rückfrage stellen"]
RANG_EXPORT = "Rang der Prüfung in der Stufe (1 = zuerst)"     # B1r: ganz hinten, mit Erklärung
SPALTEN = ["Nr.", "Stufe", "Kategorie", "Prüfung", "Prüfer", "OZ", "Kurztext", "Menge", "Einheit", "EP (€)", "GP (€)",
           "Befund", "Zitat/Beleg", "Fundstelle (Seite)", "Feldwerte", "Beleg-Status",
           "KI-Einordnung", "KI-Quelle", "KI-Warnhinweis", "KI-Begründung", "KI-Zitat geprüft", "Rückfrage-Entwurf (KI)",
           "KI-Modell", "Prompt-Version",
           "Fund-ID", "Entscheidung Kalkulator", "Notiz", RANG_EXPORT]
BREITEN = [6, 24, 22, 34, 16, 14, 40, 12, 10, 12, 14, 60, 60, 12, 30, 40, 34, 12, 40, 50, 50, 50, 20, 12, 44, 14, 40, 24]
UMBRUCH = {"Kurztext", "Befund", "Zitat/Beleg", "Feldwerte", "Beleg-Status", "KI-Warnhinweis", "KI-Begründung",
           "KI-Zitat geprüft", "Rückfrage-Entwurf (KI)", "Notiz"}
ZAHLENFORMAT = {"Menge": "#,##0.000", "EP (€)": "#,##0.00#", "GP (€)": "#,##0.00"}   # wie im LV gedruckt
DIRTY_WARNUNG = "Prüfstand nicht committet – nicht für Abgabe oder Demo verwenden"
# Leitplanke E13 (Team, 21.11.2026): KI-Einordnungen, die einen Regel-Fund entwarnen würden
KI_ENTWARNEND = ("anderes Bauteil", "Bereichs- oder Mehrfachangabe")
KI_LISTE_HINWEIS = "KI-Hinweis im Detail"
KI_WARNHINWEIS = "Messung vom 21.11.: bei echten Widersprüchen nicht zuverlässig – bitte selbst prüfen."   # B1r
# B1r (Team, 21.11.2026), sachlich nach docs/pruefprotokoll.md (S2: Skript liest nur das Original, ohne parse())
BELEG_STATUS = {"geprüft": "Zitat wörtlich im Original bestätigt (automatische Prüfung, unabhängig vom Parser; "
                           "keine fachliche Bewertung)",
                "ungeprüft": "Zitat aus der automatischen Auswertung; Abgleich mit dem Original steht für diesen "
                             "Fund noch aus",
                "nicht im Original": "Zitat steht so nicht wörtlich im Original"}
VERBOTEN = re.compile(r"Anspruch|berechtigt|durchsetzbar|§")    # R7, Team 21.11.2026


# --------------------------------------------------------------------------- Auswertung

def pruefe_lv(pfad, zuordnung=None):
    """Parst ein LV und prüft es (Nr. 1–6). Gibt (funde, texte, info) zurück:
    texte = je Fund-ID die Positionen mit Kurz- und Langtext, info = Kennzahlen und Hinweise."""
    pfad = Path(pfad)
    if pfad.suffix.lower() in (".xlsx", ".xlsm"):            # B2-Integration (B4): Excel-Weiche
        from excel_import import lies_excel, KENNZEICHNUNG
        df = lies_excel(pfad, zuordnung)
        hinweise_excel = [KENNZEICHNUNG]
    else:
        df = parse(pfad)
        hinweise_excel = []
    preise = nur_preise(df)
    funde = alle_pruefungen(df, pfad)       # PDF: Seitentexte aus der Datei; reine Preisdatei: nur Nr. 17 (B1e)
    pos = df[df.typ == "Position"]
    texte = {}
    for f in funde:
        texte[f["id"]] = []
        for p in f["positionen"]:
            r = pos[pos.oz == p["oz"]].iloc[0]
            texte[f["id"]].append({
                "oz": p["oz"],
                "kurztext": r.kurztext if isinstance(r.kurztext, str) else "",
                "langtext": r.langtext if isinstance(r.langtext, str) else "",
                # B1r: Werte der Position für den Bericht (aus parse(), keine eigene Rechnung, E9)
                "menge": _zahl(r.menge), "einheit": (r.einheit_roh if isinstance(r.einheit_roh, str) and
                                                     r.einheit_roh.strip() else r.einheit if isinstance(r.einheit, str)
                                                     else ""),
                "ep": _zahl(r.ep), "gp": _zahl(r.gp),
            })
    hinweise = hinweise_excel + ([NUR_PREISE_TEXT] if preise else []) + ([datei_hinweis(pfad.name)] if datei_hinweis(pfad.name) else [])
    info = {"format": df.format.iloc[0] if len(df) else "–", "positionen": len(pos), "nur_preise": preise,
            "fingerprint": fingerprint(df), "hinweise": hinweise,
            "pruefstand": pruefstand.erstellen(pfad.read_bytes()),
            "abdeckung": pruefabdeckung.abdeckung(df),          # Hinweis, unterdrückt keinen Fund (B1b)
            # B2-Integration: für Übersichtsseite und Vergleichspreise
            "kurztexte": {r.oz: (r.kurztext if isinstance(r.kurztext, str) else "") for r in pos.itertuples()},
            "gp": {r.oz: _zahl(r.gp) for r in pos.itertuples()},
            "einheiten": {r.oz: (r.einheit if isinstance(r.einheit, str) else "") for r in pos.itertuples()}}
    # Sitzung UI: alle Positionen aus demselben parse()-Lauf wie die Funde (Positions-Explorer)
    info["tabelle"] = [{"oz": r.oz, "titel": r.titel if isinstance(r.titel, str) else "",
                        "kurztext": r.kurztext if isinstance(r.kurztext, str) else "",
                        "langtext": r.langtext if isinstance(r.langtext, str) else "",
                        "menge": _zahl(r.menge),
                        "einheit": (r.einheit_roh if isinstance(r.einheit_roh, str) and r.einheit_roh.strip()
                                    else r.einheit if isinstance(r.einheit, str) else ""),
                        "ep": _zahl(r.ep), "gp": _zahl(r.gp),
                        "seite": None if r.seite is None or r.seite != r.seite else int(r.seite)}
                       for r in pos.itertuples()]
    # B5: Eingaben der KI-Prüfungen (nur auf Knopfdruck in der App; reine Preisdatei ohne Texte: leer)
    from ki_b5 import einzelpositionen, paare
    info["b5"] = {"tippfehler": [] if preise else einzelpositionen(df), "widerspruch": [] if preise else paare(df)}
    return funde, texte, info


ABDECKUNG_HINWEIS = ("zählt je Prüfung, in wie vielen Positionen sie etwas finden kann; "
                     "ein Hinweis, der keinen Fund unterdrückt")


def abdeckung_zeilen(info):
    """Zeilen „Prüfabdeckung Nr. n (Name)“ für das Blatt „Übersicht“ (B1b, Nachtrag 3)."""
    eintraege = info.get("abdeckung") or []
    if not eintraege:
        return []
    return [("Prüfabdeckung", ABDECKUNG_HINWEIS)] + [
        (f"Prüfabdeckung Nr. {e['pruefung']} ({e['name']})", pruefabdeckung.text(e)) for e in eintraege]


def _zahl(x):
    """Zahl aus parse() oder None (leer im Bericht, z. B. unbepreiste Position)."""
    try:
        return None if x is None or x != x else float(x)
    except (TypeError, ValueError):
        return None


def stufe_text(s):
    """„1 – Fehlerprüfung“ (B1r: Stufe im Bericht als Text)."""
    return f"{s} – {STUFEN[s]}"


def lade_s2():
    """Ergebnis der Belegprüfung am Original je Fund-ID (docs/pruefprotokoll.md, S2)."""
    if not S2_ERGEBNIS.exists():
        return {}, None
    doc = json.loads(S2_ERGEBNIS.read_text(encoding="utf-8"))
    return {e["id"]: e for e in doc["funde"]}, doc.get("stand")


def beleg_pruefung(f, s2):
    """'geprüft', 'nicht im Original' oder 'ungeprüft'. Geprüft gilt nur, wenn die geprüften
    Zitate und Feldbelege genau denen des aktuellen Funds entsprechen."""
    e = s2.get(f["id"])
    if not e or [b["text"] for b in e["belege"]] != f["belege"]:
        return "ungeprüft"
    if "feldbelege" in e and [b["text"] for b in e["feldbelege"]] != [b["text"] for b in f.get("feldbelege", [])]:
        return "ungeprüft"
    if e["ergebnis"] == "Beleg im Original gefunden":
        return "geprüft"
    if e["ergebnis"] == "Beleg nicht im Original":
        return "nicht im Original"
    return "ungeprüft"                                # z. B. Rückfrage an Team offen


def git_commit():
    """Stand des Tools (src/pruefstand.py)."""
    return pruefstand.git_commit()


# --------------------------------------------------------------------------- Excel

ZONEN = {"CET": "MEZ", "CEST": "MESZ"}               # deutsche Kürzel für Mitteleuropa


def zeit_text(zeitpunkt):
    """„2026-11-21 03:30 MEZ“. Ohne Zeitzone gilt die lokale Zeit des Rechners."""
    z = zeitpunkt if zeitpunkt.tzinfo else zeitpunkt.astimezone()
    name = z.tzname() or ""
    if name in ZONEN:
        name = ZONEN[name]
    elif not name or name.startswith(("+", "-")):
        off = z.utcoffset()
        minuten = int(off.total_seconds() // 60) if off is not None else 0
        name = f"UTC{'+' if minuten >= 0 else '-'}{abs(minuten) // 60:02d}:{abs(minuten) % 60:02d}"
    return f"{z:%Y-%m-%d %H:%M} {name}"


def dateiname(lv_name, datum):
    stamm = re.sub(r'[\\/:*?"<>|]', "_", Path(lv_name).stem)
    return f"Risikobericht_{stamm}_{datum:%Y-%m-%d}.xlsx"


def _schreibe(ws, zeile, spalte, wert, fett=False, umbruch=False):
    """Text immer als Text (data_type 's'), auch bei führendem „=“; Steuerzeichen entfernt."""
    c = ws.cell(row=zeile, column=spalte)
    if isinstance(wert, str):
        c.value = ILLEGAL_CHARACTERS_RE.sub("", wert)
        c.data_type = "s"
    else:
        c.value = wert
    if fett:
        c.font = Font(bold=True)
    if umbruch:
        c.alignment = Alignment(wrap_text=True, vertical="top")
    return c


def ki_warnhinweis(k):
    """Warnhinweis (B0b.6) bei einer entwarnenden KI-Einordnung, sonst leer."""
    return KI_WARNHINWEIS if k and k.get("einordnung") in KI_ENTWARNEND else ""


def ki_liste(f, ki):
    """Kurzangabe für die Fundliste der App (E13): entwarnende Einordnungen erst im Detail."""
    if f["pruefung"] not in (1, 2):
        return ""
    k = (ki or {}).get(f["id"])
    if k is None:
        return "noch nicht geprüft"
    if not k["einordnung"]:
        return k["status"]
    if k["einordnung"] in KI_ENTWARNEND:
        return KI_LISTE_HINWEIS
    return f"KI-Vorschlag: {k['einordnung']}"


def ki_spalten(f, ki):
    """Spalten der KI-Gegenprüfung (P4). Nur Funde Nr. 1/2; Inhalt nur bei gültigem Vorschlag.
    Alle KI-Spalten bleiben zur Nachvollziehbarkeit erhalten, dazu der Warnhinweis (E13)."""
    if f["pruefung"] not in (1, 2):
        return ["", "", "", "", "", "", "", ""]
    k = (ki or {}).get(f["id"])
    if k is None:
        return ["noch nicht KI-geprüft", "noch nicht KI-geprüft", "", "", "", "", "", ""]
    if not k["einordnung"]:
        return [k["status"], k.get("quelle", ""), "", "", k["zitat_status"], "", k["modell"], k["prompt_version"]]
    zitat = f"{k['zitat_status']}: „{k['zitat_kurztext']}“ / „{k['zitat_langtext']}“"
    return [f"KI-Vorschlag: {k['einordnung']}", k.get("quelle", ""), ki_warnhinweis(k), k["begruendung"], zitat,
            k["rueckfrage"], k["modell"], k["prompt_version"]]


def fund_zeile(f, texte, s2, ki=None, nr=None):
    """Werte einer Zeile im Blatt „Funde“ (Reihenfolge wie SPALTEN); `nr` = laufende Nummer (B1r)."""
    kurz = []
    for t in texte.get(f["id"], []):
        k = normalisiere_leerzeichen(t["kurztext"])
        if k and k not in kurz:
            kurz.append(k)
    seiten = [str(p["seite"]) for p in f["positionen"] if p["seite"] is not None]
    befund = f["begruendung"] if f["begruendung"].startswith(f["titel"]) else f"{f['titel']}: {f['begruendung']}"
    erste = (texte.get(f["id"]) or [{}])[0]         # Werte der ersten Position (Nr. 4: mehrere Positionen)
    leer = lambda v: "" if v is None else v
    return [
        nr,
        stufe_text(f["stufe"]),
        f["kategorie"],
        f"{f['pruefung']} – {PRUEFUNGEN[f['pruefung']]}",
        PRUEFER.get(f["pruefung"], ""),
        ", ".join(p["oz"] for p in f["positionen"]),
        " | ".join(kurz),
        leer(erste.get("menge")),
        erste.get("einheit") or "",
        leer(erste.get("ep")),
        leer(erste.get("gp")),
        befund,
        "\n".join(f"„{b}“" for b in f["belege"]),
        ("S. " + ", ".join(seiten)) if seiten else "–",
        "\n".join(f"{b['art']}: {b['text']}" for b in f.get("feldbelege", [])),
        BELEG_STATUS[beleg_pruefung(f, s2)],
        *ki_spalten(f, ki),
        f["id"],
        f.get("status") if f.get("status") in ENTSCHEIDUNGEN else "",   # Entscheidung aus der App
        "",                                           # Notiz
        f["prioritaet_in_stufe"],
    ]


ERKLAERUNG = {
    "LV-Datei": "Name der geprüften Datei",
    "Format": "Dateiformat, aus dem das LV gelesen wurde",
    "Zeitpunkt der Prüfung": "wann dieser Bericht erzeugt wurde",
    "Anzahl Positionen": "Positionen im LV (ohne Titel und Hinweistexte)",
    "Funde gesamt": "alle Funde der Prüfungen Nr. 1–19; jede Zeile im Blatt „Funde“ ist ein Fund",
    "Sortierung": "Reihenfolge der Zeilen im Blatt „Funde“",
    "Datei-Hinweise": "Hinweis zur ganzen Datei; unterdrückt keinen Fund",
    "Prüfabdeckung": "in wie vielen Positionen eine Prüfung überhaupt etwas finden kann",
    "Prüfabdeckung Nr. 17 (Rechenprüfung Menge × EP ≠ GP)": "Positionen mit Menge, EP und GP; nachgerechnet wird, ob "
                                                          "Menge × EP zum gedruckten GP passt (Rundung berücksichtigt)",
    "Prüfungen": "welche Prüfungen gelaufen sind",
    "Prüfsumme (fingerprint)": "Prüfsumme über die gelesenen Inhalte des LV (OZ, Texte, Mengen, Preise); gleich, "
                               "wenn derselbe Inhalt erneut gelesen wird",
    "SHA-256 der geprüften Datei": "Prüfsumme der Datei selbst; zeigt, dass genau diese Datei geprüft wurde",
    "Git-Commit des Tools": "Stand des Prüfprogramms; „-dirty“ = nicht gespeicherte Änderungen",
    "Bibliotheksversionen": "Versionen der Programmbibliotheken; Abweichungen von den festgelegten mit „(fest: …)“",
    "Prompt-Version (KI)": "Fassung der Anweisung an die KI-Gegenprüfung (nur Nr. 1/2)",
}


def _erklaerung(name):
    if name in ERKLAERUNG:
        return ERKLAERUNG[name]
    if name.startswith("Funde Stufe "):
        return "Funde dieser Stufe (1 = zuerst klären)"
    if name.startswith("Funde "):
        return "Funde dieser Kategorie"
    if name.startswith("Prüfabdeckung Nr. "):
        return "Positionen, in denen diese Prüfung etwas finden kann; die übrigen mit Grund"
    return ERKLAERUNG.get(name, "")


# Kostenwirkung je Prüfung (Rolle Wirtschaft): Nr. 1–6, 17 laut input/pruefkatalog.md, Nr. 7–16, 18, 19 aus den
# Modulen von Sitzung B2 (KOSTENWIRKUNG). Qualitativ, keine Beträge (R11, E9).
KOSTENWIRKUNG = {1: "direkt: andere Nennweite ändert Material- und Einbaupreis; Höhe ohne Preisbasis nicht bezifferbar",
                 2: "direkt: andere Betonklasse ändert den Materialpreis",
                 3: "direkt: ohne Menge oder Einheit geht die Position nicht oder falsch in die Angebotssumme ein",
                 4: "direkt: Preise und Abrechnung lassen sich der OZ nicht eindeutig zuordnen",
                 5: "bei Abruf: nicht in der Angebotssumme, der EP bindet bei Beauftragung, Menge offen",
                 6: "direkt: das Mengenrisiko liegt vollständig im Pauschalpreis",
                 17: "direkt: GP weicht vom Produkt Menge × EP ab, Angebotssumme betroffen"}


def _kostenwirkung():
    k = dict(KOSTENWIRKUNG)
    try:
        from pruefung_hinweise import KOSTENWIRKUNG as k7
        from pruefung_struktur import KOSTENWIRKUNG as k15
        from pruefung_vollstaendigkeit import KOSTENWIRKUNG as k19, NR as nr19
        k.update(k7)
        k.update(k15)
        k[nr19] = k19
    except ImportError:
        pass
    return k


def _legende():
    """Zeilen (Begriff, Bedeutung) für das Blatt „Legende“ (B1r; B2-Integration: Prüfungen 1–19 mit Prüfer und
    Kostenwirkung)."""
    spalten = {
        "Nr.": "laufende Nummer in der Sortierreihenfolge des Berichts",
        "Stufe": "Art des Funds: 1 – Fehlerprüfung, 2 – Kalkulationsrisiko, 3 – mögliches Nachtragspotenzial, "
                 "4 – Unklarheit; die Liste ist nach Stufe sortiert",
        "Kategorie": "nachweisbarer Fehler, möglicher Widerspruch, Unklarheit oder Risikohinweis – ein Hinweis ist "
                     "kein Fehler",
        "Prüfung": "Nummer und Name der Prüfung laut Prüfkatalog",
        "Prüfer": "Prüfbereich der Prüfung: Formal, Widerspruch, Nachtrag, Klarheit, Mengen, Vollständigkeit, Preis "
                  "(Tippfehler folgt)",
        "OZ": "Ordnungszahl der Position im LV (bei „OZ doppelt“ alle betroffenen)",
        "Kurztext": "Kurztext der Position, wörtlich aus dem LV",
        "Menge": "Menge der Position, wie im LV angegeben (bei mehreren Positionen: die erste)",
        "Einheit": "Einheit der Position, wie im LV angegeben",
        "EP (€)": "Einheitspreis in Euro, wie im LV angegeben; leer, wenn die Position keinen Preis hat. "
                  "Das Programm rechnet und bewertet keine Preise",
        "GP (€)": "Gesamtpreis in Euro, wie im LV angegeben; leer, wenn die Position keinen Preis hat",
        "Befund": "was die Prüfung festgestellt hat, mit Empfehlung (klärende Rückfrage, Risiko einpreisen, "
                  "vormerken)",
        "Zitat/Beleg": "wörtliche Zitate aus dem Text der Position, die den Fund belegen",
        "Fundstelle (Seite)": "Seite im PDF; „–“ bei GAEB-Dateien (ohne Seiten)",
        "Feldwerte": "Werte aus Datenfeldern der Position (z. B. „Einheit: (leer)“) oder Kennzeichen in der Datei",
        "Beleg-Status": "ob das Zitat automatisch am Original abgeglichen wurde (siehe unten)",
        "KI-Einordnung": "Vorschlag der KI-Gegenprüfung (nur Nr. 1/2); verändert weder Stufe, Kategorie noch "
                         "Reihenfolge – die KI entwarnt nie",
        "KI-Quelle": "„Cache“ = gespeicherte Antwort, „API“ = neu abgefragt, „noch nicht KI-geprüft“",
        "KI-Warnhinweis": "steht bei KI-Vorschlägen, die einen Fund entwarnen würden; bitte selbst prüfen",
        "KI-Begründung": "Begründung der KI, nur zur Nachvollziehbarkeit",
        "KI-Zitat geprüft": "ob die von der KI zitierten Stellen wörtlich im Text stehen",
        "Rückfrage-Entwurf (KI)": "Formulierungsvorschlag der KI für eine Rückfrage an den Auftraggeber",
        "KI-Modell": "verwendetes KI-Modell",
        "Prompt-Version": "Fassung der Anweisung an die KI",
        "Fund-ID": "eindeutige Kennung des Funds (Prüfung|Datei|OZ); gleich bei jeder erneuten Prüfung",
        "Entscheidung Kalkulator": "Ihre Entscheidung: bestätigt, verworfen oder Rückfrage stellen (aus der App "
                                   "übernommen, hier änderbar)",
        "Notiz": "Ihre Notiz",
        RANG_EXPORT: "Rang der Prüfung innerhalb ihrer Stufe (1 = zuerst); die Zeilen sind bereits danach "
                     "sortiert",
    }
    zeilen = [("Spalten im Blatt „Funde“", None)] + [(s, spalten[s]) for s in SPALTEN]
    zeilen += [(None, None), ("Stufen", None)] + [(stufe_text(s), b) for s, b in (
        (1, "zuerst klären: Fehler oder möglicher Widerspruch im LV"),
        (2, "Kalkulationsrisiko: beim Preis berücksichtigen (z. B. Pauschale, Bedarfsposition)"),
        (3, "mögliches Nachtragspotenzial: vormerken"),
        (4, "Unklarheit: vormerken bzw. nur Hinweis"))]
    zeilen += [(None, None), ("Beleg-Status", None)] + [(v, b) for v, b in (
        (BELEG_STATUS["geprüft"], "das Zitat wurde von einem Prüfskript wörtlich im Original gefunden; das sagt "
                                  "nichts darüber, ob der Fund fachlich zutrifft"),
        (BELEG_STATUS["ungeprüft"], "das Zitat stammt aus der automatischen Auswertung; bitte am Original prüfen"),
        (BELEG_STATUS["nicht im Original"], "das Zitat wurde so nicht im Original gefunden; der Fund ist zu "
                                            "prüfen"))]
    zeilen += [(None, None), ("Einheiten", "Beträge in Euro wie im LV angegeben (EP, GP); Mengen in der Einheit der "
                                           "Position")]
    kw = _kostenwirkung()
    zeilen += [(None, None), ("Prüfungen (Prüfer · Kostenwirkung)", None)] + [
        (f"{nr} – {PRUEFUNGEN[nr]}", f"Prüfer: {PRUEFER.get(nr, '–')} · Kostenwirkung: {kw.get(nr, 'nicht bewertet')}")
        for nr in sorted(PRUEFUNGEN)]
    zeilen += [(None, None), (SCHLUSSSATZ, None)]
    return zeilen


def risikobericht(lv_name, funde, texte, info, s2=None, zeitpunkt=None, commit=None, ki=None, ki_konfig=None,
                  ki_cache_dir=None):
    """Erzeugt den Risikobericht als .xlsx (bytes). `ki_konfig`, `ki_cache_dir`: nur für Tests des Blatts „KI-Vorschläge“."""
    s2 = lade_s2()[0] if s2 is None else s2
    zeitpunkt = zeitpunkt or datetime.now().astimezone()
    stand = dict(info.get("pruefstand") or {"commit": git_commit(), "versionen": pruefstand.versionen(),
                                              "prompt_version": pruefstand.prompt_version(), "sha256": "–"})
    if commit:
        stand["commit"] = commit
    funde = sortiere(funde)                            # gleiche Sortierung wie die App
    wb = Workbook()
    ue = wb.active
    ue.title = "Übersicht"
    zeilen = [("Risikobericht – LV-Prüfassistent", None)]
    if str(stand.get("commit", "")).endswith("-dirty"):
        zeilen += [("WARNUNG", DIRTY_WARNUNG)]
    zeilen += [
        ("Für den Kalkulator", None),
        ("LV-Datei", lv_name),
        ("Zeitpunkt der Prüfung", zeit_text(zeitpunkt)),
        ("Format", info["format"]),
        ("Anzahl Positionen", info["positionen"]),
        ("Funde gesamt", len(funde)),
    ]
    if not info["nur_preise"] or funde:
        zeilen += [(f"Funde Stufe {s} ({STUFEN[s]})", sum(f["stufe"] == s for f in funde)) for s in (1, 2, 3, 4)]
        zeilen += [(f"Funde {k}", sum(f["kategorie"] == k for f in funde)) for k in KATEGORIEN]
        zeilen += [("Sortierung", SORTIERUNG)]
    zeilen += [("Datei-Hinweise", h) for h in info["hinweise"]] or [("Datei-Hinweise", "keine")]
    zeilen += abdeckung_zeilen(info)
    zeilen += [(None, None), ("Prüfstand (technisch)", None),
               ("Prüfungen", "Nr. 1–19 laut Prüfkatalog"),
               ("Prüfsumme (fingerprint)", info["fingerprint"]),
               *pruefstand.zeilen(stand)]
    zeilen += [(None, None), (SCHLUSSSATZ, None)]
    ueberschriften = {"Risikobericht – LV-Prüfassistent", "Für den Kalkulator", "Prüfstand (technisch)",
                      SCHLUSSSATZ, "WARNUNG"}
    for i, (k, v) in enumerate(zeilen, start=1):
        if k is not None:
            _schreibe(ue, i, 1, k, fett=k in ueberschriften)
            if v is not None and _erklaerung(k):
                _schreibe(ue, i, 3, _erklaerung(k), umbruch=True)
        if v is not None:
            _schreibe(ue, i, 2, v, fett=k == "WARNUNG", umbruch=True)
    ue.column_dimensions["A"].width = 40
    ue.column_dimensions["B"].width = 80
    ue.column_dimensions["C"].width = 60

    if not info["nur_preise"] or funde:              # reine Preisdatei: Blatt nur bei Rechenfehlern (Nr. 17)
        ws = wb.create_sheet("Funde")
        for j, s in enumerate(SPALTEN, start=1):
            _schreibe(ws, 1, j, s, fett=True, umbruch=True)
        ws.row_dimensions[1].height = 45                # Überschriften umbrochen, vollständig lesbar (B1r)
        for i, f in enumerate(funde, start=2):
            for j, v in enumerate(fund_zeile(f, texte, s2, ki, nr=i - 1), start=1):
                c = _schreibe(ws, i, j, v, umbruch=SPALTEN[j - 1] in UMBRUCH)
                if SPALTEN[j - 1] in ZAHLENFORMAT and isinstance(v, float):
                    c.number_format = ZAHLENFORMAT[SPALTEN[j - 1]]
        for j, b in enumerate(BREITEN, start=1):
            ws.column_dimensions[ws.cell(row=1, column=j).column_letter].width = b
        ws.freeze_panes = "A2"
        letzte = max(len(funde) + 1, 2)
        ws.auto_filter.ref = f"A1:{ws.cell(row=1, column=len(SPALTEN)).column_letter}{letzte}"
        dv = DataValidation(type="list", formula1='"' + ",".join(ENTSCHEIDUNGEN) + '"', allow_blank=True)
        sp = ws.cell(row=1, column=SPALTEN.index("Entscheidung Kalkulator") + 1).column_letter
        dv.add(f"{sp}2:{sp}{letzte}")
        ws.add_data_validation(dv)

    lg = wb.create_sheet("Legende")
    for i, (k, v) in enumerate(_legende(), start=1):
        if k is not None:
            _schreibe(lg, i, 1, k, fett=v is None, umbruch=True)
        if v is not None:
            _schreibe(lg, i, 2, v, umbruch=True)
    lg.column_dimensions["A"].width = 45
    lg.column_dimensions["B"].width = 100

    if not info["nur_preise"] or funde:                            # M2b: Sicht auf die vorhandenen Regel-Funde
        import nachtrag_streit
        nachtrag_streit.schreibe(wb, funde, texte, _schreibe)
    if (not info["nur_preise"] or funde) and "b5" in info:         # M2 (L48): getrennt von den Regel-Funden (E13)
        import ki_blatt
        ki_blatt.schreibe(wb, info, _schreibe, konfig=ki_konfig, cache_dir=ki_cache_dir)
    if not info["nur_preise"] or funde:          # Kalkulatorsicht (22.11.2026): Nr. 1–15, vor den bestehenden Blättern
        import bericht_kalkulator
        bericht_kalkulator.schreibe(wb, lv_name, funde, texte, info, s2, _schreibe, beleg_pruefung, PRUEFUNGEN,
                                    STUFEN, _kostenwirkung(), SCHLUSSSATZ)

    puffer = io.BytesIO()
    wb.save(puffer)
    return puffer.getvalue()


def r7_verstoesse(texte):
    """Texte, die verbotene Begriffe enthalten (R7)."""
    return [t for t in texte if isinstance(t, str) and VERBOTEN.search(t)]
