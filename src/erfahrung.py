"""
erfahrung.py - M2c: Erfahrungsdatenbank aus menschlichen Entscheidungen (Team, 22.11.2026, 01:25).

SQLite aus der Standardbibliothek. Gespeichert wird nur, wenn ein Mensch in der App einen Fund bestätigt oder verwirft.
Die Anzeige „Frühere Entscheidung …“ erscheint nur bei exakt gleicher Prüfung und gleichem Belegtext nach Normalisierung
(Leerzeichen, Groß- und Kleinschreibung) in einem anderen LV. Keine Ähnlichkeitssuche, keine KI.
Die Erfahrung entwarnt nie (analog E13): Sie ändert keinen Fund, keine Priorität, Kategorie, Sortierung, Filter oder
Hervorhebung, und sie ist kein Beleg (E12 (2)).

Pfad: LV_ERFAHRUNG_DB; ohne die Variable in Agenten- und Testläufen (LV_FINDINGS_DIR gesetzt) im dortigen Temp-Ordner, sonst
data/erfahrung/erfahrung.sqlite3 (in .gitignore, außerhalb von data/findings).
"""
import os
import re
import sqlite3
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UMGEBUNG = "LV_ERFAHRUNG_DB"
AGENT_UMGEBUNG = "LV_FINDINGS_DIR"
STANDARD = ROOT / "data" / "erfahrung" / "erfahrung.sqlite3"
KENNZEICHNUNG = "Erfahrung aus früherer Prüfung, kein Beleg"
ENTSCHEIDUNGEN = ("bestätigt", "verworfen")
TABELLE = """CREATE TABLE IF NOT EXISTS entscheidungen (
    id INTEGER PRIMARY KEY,
    pruefung INTEGER NOT NULL,
    belegtext TEXT NOT NULL,
    entscheidung TEXT NOT NULL CHECK (entscheidung IN ('bestätigt', 'verworfen')),
    begruendung TEXT NOT NULL DEFAULT '',
    datei TEXT NOT NULL,
    oz TEXT NOT NULL,
    zeitpunkt TEXT NOT NULL,
    aktiv INTEGER NOT NULL DEFAULT 1,
    UNIQUE (pruefung, belegtext, datei, oz))"""
INDEX = "CREATE INDEX IF NOT EXISTS idx_treffer ON entscheidungen (pruefung, belegtext, aktiv)"


def pfad():
    wert = os.environ.get(UMGEBUNG, "").strip()
    if wert:
        return Path(wert)
    agent = os.environ.get(AGENT_UMGEBUNG, "").strip()
    return Path(agent) / "erfahrung.sqlite3" if agent else STANDARD


def normalisiere(text):
    """Nur Leerzeichen und Groß-/Kleinschreibung (Team 01:25)."""
    return re.sub(r"\s+", " ", text or "").strip().lower()


def belegtext(fund):
    """Normalisierter Belegtext des Funds; leer, wenn der Fund keinen Textbeleg hat."""
    return normalisiere(" | ".join(b for b in fund.get("belege") or [] if b))


def _oz(fund):
    return ", ".join(p["oz"] for p in fund["positionen"])


def _schreibend():
    p = pfad()
    p.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(p, timeout=5)
    con.execute(TABELLE)
    con.execute(INDEX)
    return con


def status_geaendert(fund, status, datei, begruendung="", zeitpunkt=None):
    """Nur aus der menschlichen Aktion in der App aufrufen. bestätigt/verworfen wird gespeichert; jeder andere Status nimmt
    eine frühere Entscheidung zu diesem Fund zurück (Eintrag bleibt, aktiv = 0). Gibt False bei einem Datenbankfehler zurück;
    der Status des Funds ist davon nicht betroffen."""
    text = belegtext(fund)
    if not text:
        return True
    if status not in ENTSCHEIDUNGEN and not pfad().exists():
        return True
    zeit = (zeitpunkt or datetime.now().astimezone()).isoformat(timespec="seconds")
    try:
        con = _schreibend()
        try:
            with con:
                if status in ENTSCHEIDUNGEN:
                    con.execute("""INSERT INTO entscheidungen (pruefung, belegtext, entscheidung, begruendung, datei, oz,
                                   zeitpunkt, aktiv) VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                                   ON CONFLICT (pruefung, belegtext, datei, oz) DO UPDATE SET
                                   entscheidung = excluded.entscheidung, begruendung = excluded.begruendung,
                                   zeitpunkt = excluded.zeitpunkt, aktiv = 1""",
                                (fund["pruefung"], text, status, (begruendung or "").strip(), datei, _oz(fund), zeit))
                else:
                    con.execute("UPDATE entscheidungen SET aktiv = 0 WHERE pruefung = ? AND belegtext = ? AND datei = ? "
                                "AND oz = ?", (fund["pruefung"], text, datei, _oz(fund)))
        finally:
            con.close()
    except (sqlite3.Error, OSError):
        return False
    return True


def fruehere(fund, datei):
    """Frühere Entscheidungen zur gleichen Prüfung mit gleichem Belegtext in einem anderen LV (feste Reihenfolge, E14).
    Liest nur; legt keine Datei an."""
    text, p = belegtext(fund), pfad()
    if not text or not p.exists():
        return []
    try:
        con = sqlite3.connect(p.resolve().as_uri() + "?mode=ro", uri=True, timeout=5)
        try:
            zeilen = con.execute("""SELECT entscheidung, datei, oz, begruendung, zeitpunkt FROM entscheidungen
                                    WHERE pruefung = ? AND belegtext = ? AND aktiv = 1 AND datei <> ?
                                    ORDER BY zeitpunkt, datei, oz""", (fund["pruefung"], text, datei)).fetchall()
        finally:
            con.close()
    except sqlite3.Error:
        return []
    return [dict(zip(("entscheidung", "datei", "oz", "begruendung", "zeitpunkt"), z)) for z in zeilen]


def anzeige(eintrag):
    """„Frühere Entscheidung: bestätigt in <Datei>, OZ <…>“, mit Begründung, falls eingegeben."""
    text = f"Frühere Entscheidung: {eintrag['entscheidung']} in {eintrag['datei']}, OZ {eintrag['oz']}"
    return text + (f" – Begründung: {eintrag['begruendung']}" if eintrag["begruendung"] else "")
