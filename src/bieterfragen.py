"""
bieterfragen.py - Backlog B3: Bieterfragen-Export (Sitzung B2, Team 21.11.2026). Regelbasiert, keine KI.

Auswahl nach der Empfehlung des **einzelnen Funds** (Team 21.11.2026, 21:20; FS-B2-11), nicht pauschal nach
Prüfungsnummer: Feld `empfehlung`, sonst „Empfehlung …: X“ in der Begründung; nur wenn der Fund keine eigene
Empfehlung trägt (heute Nr. 1/2 und „Menge 0“), die Empfehlung seiner Prüfung laut Katalog (KATALOG_EMPFEHLUNG).
Eine Frage entsteht nur bei „Rückfrage stellen“ bzw. „klärende Rückfrage“. Dateien der Austauschphase 86
(.D86/.X86) sind Auftrags-LVs: dort keine Bieterfragen, Hinweis „Auftrags-LV – keine Bieterfragen“.
Je ausgewähltem Fund wird ein Entwurf einer Bieterfrage gebaut: feste Vorlage je Prüfung, OZ und wörtlicher Beleg aus
dem Fund (R5). Der Entwurf ist eine Frage, keine Bewertung und keine Rechtsaussage (R6, R7); er wird erst durch den
Kalkulator verschickt. Funde mit Status „verworfen“ (menschliche Entscheidung) fallen weg, alle übrigen bleiben,
der Status steht in einer eigenen Spalte.

Ausgabe: Liste von Zeilen (SPALTEN) und `schreibe_xlsx(zeilen, pfad)` (Blatt „Bieterfragen“ und „Legende“,
Überschriften lesbar). Reihenfolge: Datei, OZ, Prüfungs-Nr. (fest, E14). Nie in data/ schreiben (E12 (4)).
Einbindung in App und Risikobericht: Vorschlag für Sitzung B1 (eigener Knopf „Bieterfragen (Entwurf)“).
"""
import re
from pathlib import Path

from pruefung_formal import oz_sortkey

EMPFEHLUNG_RE = re.compile(r"Empfehlung[^.:]*:\s*([^.;]+)")
RUECKFRAGE_WERTE = {"rückfrage stellen", "klärende rückfrage"}
# nur für Funde ohne eigene Empfehlung: Spalte Handlungsempfehlung in input/pruefkatalog.md
KATALOG_EMPFEHLUNG = {1: "klärende Rückfrage", 2: "klärende Rückfrage", 3: "klärende Rückfrage",
                      4: "klärende Rückfrage", 15: "Rückfrage stellen", 16: "Rückfrage stellen", 17: "Rückfrage stellen"}
PHASE_86 = (".d86", ".x86")
HINWEIS_AUFTRAG = "Auftrags-LV – keine Bieterfragen"
SPALTEN = ["Nr.", "Datei", "OZ", "Prüfung", "Frage (Entwurf)", "Beleg (wörtlich aus dem LV)", "Status des Funds",
           "Fund-ID"]
LEGENDE = [
    ("Nr.", "laufende Nummer der Frage in der Reihenfolge Datei, OZ, Prüfung"),
    ("Datei", "LV-Datei, aus der der Fund stammt"),
    ("OZ", "Ordnungszahl wie im LV; bei mehreren Positionen alle, durch Komma getrennt"),
    ("Prüfung", "Nummer und Name der Prüfung laut Prüfkatalog"),
    ("Frage (Entwurf)", "regelbasierter Entwurf; vor dem Versand durch den Kalkulator prüfen und anpassen"),
    ("Beleg (wörtlich aus dem LV)", "Zitat(e) aus dem Fund, durch „ | “ getrennt"),
    ("Status des Funds", "Entscheidung des Kalkulators in der App (offen, bestätigt, Rückfrage stellen)"),
    ("Fund-ID", "eindeutige Kennung des Funds (Prüfung|Datei|OZ)"),
]
PROJEKT_DATA = Path(__file__).resolve().parents[1] / "data"        # data/ des Projekts, unabhängig vom Arbeitsordner
HINWEIS = "Entwurf: Fragen ohne rechtliche Bewertung; vor dem Versand prüfen."


def _q(t):
    return f"„{t}“"


def frage(f):
    """Entwurf einer Bieterfrage zu einem Fund (Text)."""
    nr, b, p = f["pruefung"], f["belege"], f["positionen"]
    oz = ", ".join(x["oz"] for x in p)
    if nr == 1 and len(b) >= 2:
        return f"Pos. {oz}: Im Kurztext steht {_q(b[0])}, im Langtext {_q(b[1])}. Welche Nennweite ist auszuführen?"
    if nr == 2 and len(b) >= 2:
        return (f"Pos. {oz}: Im Kurztext steht {_q(b[0])}, im Langtext {_q(b[1])}. Welche Betonfestigkeitsklasse "
                f"ist auszuführen?")
    if nr == 3:
        return f"Pos. {oz} ({_q(b[0])}): Menge bzw. Einheit fehlen oder sind 0. Bitte Menge und Einheit angeben."
    if nr == 4:
        return (f"Die OZ {p[0]['oz']} ist im LV {len(p)}-mal vergeben ({', '.join(_q(x) for x in b)}). "
                f"Bitte die Ordnungszahlen klarstellen.")
    if nr == 15:
        if f.get("kategorie") == "nachweisbarer Fehler":
            return f"Pos. {oz} ({_q(b[0])}): Die genannte Bezugsposition kommt im LV nicht vor. Welche Position ist gemeint?"
        return f"Pos. {oz} ({_q(b[0])}): Auf welche Position bezieht sich diese Zulage?"
    if nr == 16:
        return (f"Pos. {oz} beschreiben dieselbe Leistung ({_q(b[0])}). Sind beide Positionen auszuführen, und wie "
                f"grenzen sie sich voneinander ab?")
    if nr == 17:
        return f"Pos. {oz} ({_q(b[0])}): Menge × Einheitspreis ergibt nicht den Gesamtpreis. Bitte die Werte bestätigen."
    return f"Pos. {oz} ({_q(b[0])}): Bitte klarstellen: {f['titel']}."


def empfehlung(f):
    """(Empfehlung, Quelle) des Funds: Feld, sonst Begründung, sonst Katalog der Prüfung (nur ohne eigene Angabe)."""
    if f.get("empfehlung"):
        return f["empfehlung"], "Fund"
    m = EMPFEHLUNG_RE.search(f.get("begruendung", ""))
    if m:
        return m.group(1).strip(), "Fund"
    return KATALOG_EMPFEHLUNG.get(f["pruefung"], ""), "Katalog"


def auftrags_lv(datei):
    return Path(datei).suffix.lower() in PHASE_86


def ausgenommen(funde):
    """Dateien mit Funden, für die es keine Bieterfragen gibt (Auftrags-LV), mit Hinweis."""
    return sorted({(f["positionen"][0]["datei"], HINWEIS_AUFTRAG) for f in funde
                   if auftrags_lv(f["positionen"][0]["datei"])})


def bieterfragen(funde):
    """Zeilen für den Export (Dict je Frage, Schlüssel = SPALTEN)."""
    auswahl = [f for f in funde if empfehlung(f)[0].lower() in RUECKFRAGE_WERTE
               and not auftrags_lv(f["positionen"][0]["datei"])
               and f.get("status") != "verworfen" and f.get("belege")]
    auswahl.sort(key=lambda f: (f["positionen"][0]["datei"], oz_sortkey(f["positionen"][0]["oz"]), f["pruefung"]))
    return [{"Nr.": i, "Datei": f["positionen"][0]["datei"], "OZ": ", ".join(p["oz"] for p in f["positionen"]),
             "Prüfung": f"Nr. {f['pruefung']} {f['titel']}", "Frage (Entwurf)": frage(f),
             "Beleg (wörtlich aus dem LV)": " | ".join(f["belege"]), "Status des Funds": f.get("status", "offen"),
             "Fund-ID": f["id"]} for i, f in enumerate(auswahl, 1)]


def schreibe_xlsx(zeilen, pfad, hinweise=()):
    """`hinweise`: Liste (Datei, Hinweis), z. B. aus ausgenommen(funde); steht unter der Tabelle."""
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font
    from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
    pfad = Path(pfad)
    if pfad.resolve().is_relative_to(PROJEKT_DATA) or pfad.resolve().is_relative_to(Path("data").resolve()):
        raise ValueError("Bieterfragen nie in data/ schreiben (E12 (4))")
    wb = Workbook()
    ws = wb.active
    ws.title = "Bieterfragen"
    ws.append([HINWEIS])
    ws.append(SPALTEN)
    for z in zeilen:          # Steuerzeichen durch ein Leerzeichen ersetzt, nicht gelöscht (R5, Team 19:55)
        ws.append([ILLEGAL_CHARACTERS_RE.sub(" ", v) if isinstance(v, str) else v for v in (z[s] for s in SPALTEN)])
    breiten = {"Nr.": 6, "Datei": 30, "OZ": 14, "Prüfung": 36, "Frage (Entwurf)": 70,
               "Beleg (wörtlich aus dem LV)": 60, "Status des Funds": 18, "Fund-ID": 40}
    for i, s in enumerate(SPALTEN, 1):
        ws.column_dimensions[ws.cell(2, i).column_letter].width = breiten[s]
        ws.cell(2, i).font = Font(bold=True)
        ws.cell(2, i).alignment = Alignment(wrap_text=True)
    for datei, h in hinweise:
        ws.append([None, ILLEGAL_CHARACTERS_RE.sub(" ", datei), None, None, h])
    for row in ws.iter_rows(min_row=3):
        for c in row:
            c.alignment = Alignment(wrap_text=True, vertical="top")
            if isinstance(c.value, str):
                c.data_type = "s"     # Text bleibt Text: kein Formel-Einschleusen über „=…“, „+…“, „@…“ aus dem LV;
                                      # kein vorangestelltes „'“, damit der Beleg wörtlich bleibt (R5)
    lg = wb.create_sheet("Legende")
    lg.append(["Spalte", "Bedeutung"])
    for z in LEGENDE:
        lg.append(list(z))
    lg.column_dimensions["A"].width, lg.column_dimensions["B"].width = 30, 90
    wb.save(pfad)
    return pfad


def xlsx_bytes(zeilen, hinweise=()):
    """Wie schreibe_xlsx, aber als Bytes für st.download_button (Datei nur im Temp-Ordner, E12 (4))."""
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        return schreibe_xlsx(zeilen, Path(d) / "bieterfragen.xlsx", hinweise).read_bytes()

