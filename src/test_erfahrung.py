"""
test_erfahrung.py - Tests für die Erfahrungsdatenbank (M2c, Team 22.11.2026, 01:25). Nur erfundene Funde, Datenbank nur im
Temp-Ordner (E12 (4)); die echte Datenbank wird nie geöffnet.

Aufruf aus der Projektwurzel (uv-Befehl siehe AGENTS.md):
  python src/test_erfahrung.py
Exit-Code 0 = alle Tests bestanden.
"""
import copy
import io
import json
import os
import re
import sqlite3
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

from openpyxl import load_workbook

SRC = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC))
import erfahrung as E                                                 # noqa: E402
from bericht import VERBOTEN, risikobericht                           # noqa: E402
from pruefung_formal import sortiere                                  # noqa: E402

ergebnisse = []
Z1 = datetime(2026, 11, 22, 3, 0).astimezone()
Z2 = datetime(2026, 11, 22, 3, 5).astimezone()


def check(name, ok, detail=""):
    ok = bool(ok)
    ergebnisse.append(ok)
    print(f"{'OK    ' if ok else 'FEHLER'} {name}" + (f" – {detail}" if detail and not ok else ""))


def fund(nr, oz, beleg, datei, stufe=3, rang=1):
    return {"id": f"{nr}|{datei}|{oz}", "pruefung": nr, "kategorie": "Risikohinweis", "titel": f"T{nr}",
            "positionen": [{"datei": datei, "oz": oz, "seite": None}], "belege": [beleg] if beleg else [], "feldbelege": [],
            "begruendung": "b", "stufe": stufe, "stufe_begruendung": "s", "prioritaet_in_stufe": rang, "rueckfrage": None,
            "status": "offen"}


def zeilen_db():
    con = sqlite3.connect(E.pfad())
    try:
        return con.execute("SELECT pruefung, belegtext, entscheidung, begruendung, datei, oz, zeitpunkt, aktiv FROM entscheidungen "
                           "ORDER BY id").fetchall()
    finally:
        con.close()


def test_pfad(tmp):
    alt = {k: os.environ.pop(k, None) for k in (E.UMGEBUNG, E.AGENT_UMGEBUNG)}
    check("Standardpfad außerhalb von data/findings", E.pfad() == E.STANDARD and "findings" not in E.pfad().parts)
    r = subprocess.run(["git", "-C", str(E.ROOT), "check-ignore", "-q", str(E.STANDARD)])
    check("Standardpfad steht in .gitignore", r.returncode == 0)
    os.environ[E.AGENT_UMGEBUNG] = str(tmp)
    check("Agenten-/Testlauf (LV_FINDINGS_DIR) schreibt nie in die echte Datenbank", E.pfad() == Path(tmp) / "erfahrung.sqlite3")
    os.environ[E.UMGEBUNG] = str(Path(tmp) / "x.sqlite3")
    check("LV_ERFAHRUNG_DB hat Vorrang", E.pfad() == Path(tmp) / "x.sqlite3")
    for k, v in alt.items():
        os.environ.pop(k, None)
        if v is not None:
            os.environ[k] = v


def test_treffer():
    a = fund(9, "1.1", "Bauschutt  laden und\nENTSORGEN", "A.X83")
    b = fund(9, "7.4", "bauschutt laden und entsorgen", "B.pdf")
    check("Lesen legt keine Datenbank an", E.fruehere(b, "B.pdf") == [] and not E.pfad().exists())
    check("Normalisierung nur Leerzeichen und Groß-/Kleinschreibung", E.normalisiere(" A  b\nC ") == "a b c")
    check("„Rückfrage stellen“ schreibt nichts", E.status_geaendert(a, "Rückfrage stellen", "A.X83") and not E.pfad().exists())
    check("Entscheidung wird gespeichert", E.status_geaendert(a, "bestätigt", "A.X83", "am Plan geprüft", Z1))
    z = zeilen_db()
    check("Gespeichert: Prüfung, normalisierter Beleg, Entscheidung, Begründung, Datei, OZ, Zeitpunkt",
          z == [(9, "bauschutt laden und entsorgen", "bestätigt", "am Plan geprüft", "A.X83", "1.1", Z1.isoformat(timespec="seconds"), 1)], str(z))
    t = E.fruehere(b, "B.pdf")
    check("Treffer: gleiche Prüfung, gleicher Beleg nach Normalisierung, anderes LV", len(t) == 1 and t[0]["datei"] == "A.X83", str(t))
    check("Anzeige wie vorgegeben", E.anzeige(t[0]) == "Frühere Entscheidung: bestätigt in A.X83, OZ 1.1 – Begründung: am Plan geprüft", E.anzeige(t[0]))
    check("Kennzeichnung", E.KENNZEICHNUNG == "Erfahrung aus früherer Prüfung, kein Beleg")
    check("Kein Treffer im selben LV", E.fruehere(a, "A.X83") == [])
    check("Kein Treffer bei anderer Prüfung", E.fruehere(fund(8, "7.4", "bauschutt laden und entsorgen", "B.pdf"), "B.pdf") == [])
    check("Kein Treffer bei ähnlichem Beleg (keine Ähnlichkeitssuche)", E.fruehere(fund(9, "7.4", "bauschutt laden, entsorgen", "B.pdf"), "B.pdf") == [])
    check("Kein Treffer bei Teilstring", E.fruehere(fund(9, "7.4", "bauschutt laden", "B.pdf"), "B.pdf") == [])
    check("Fund ohne Textbeleg: nichts gespeichert, kein Treffer",
          E.status_geaendert(fund(17, "2.1", "", "A.X83"), "bestätigt", "A.X83") and len(zeilen_db()) == 1
          and E.fruehere(fund(17, "2.1", "", "B.pdf"), "B.pdf") == [])
    E.status_geaendert(a, "verworfen", "A.X83", "", Z2)
    t = E.fruehere(b, "B.pdf")
    check("Neue Entscheidung ersetzt die alte, keine zweite Zeile", len(zeilen_db()) == 1 and t[0]["entscheidung"] == "verworfen"
          and E.anzeige(t[0]) == "Frühere Entscheidung: verworfen in A.X83, OZ 1.1", str(t))
    E.status_geaendert(a, "offen", "A.X83", "", Z2)
    check("„Zurück auf offen“ nimmt die Entscheidung zurück, Eintrag bleibt", E.fruehere(b, "B.pdf") == [] and zeilen_db()[0][-1] == 0)
    E.status_geaendert(a, "bestätigt", "A.X83", "", Z2)
    check("Erneut bestätigt: wieder aktiv", len(E.fruehere(b, "B.pdf")) == 1)
    c = fund(9, "2.2", "BAUSCHUTT laden und entsorgen", "C.X83")
    E.status_geaendert(c, "verworfen", "C.X83", "", Z1)
    r1, r2 = E.fruehere(b, "B.pdf"), E.fruehere(b, "B.pdf")
    check("E14: feste Reihenfolge (Zeitpunkt, Datei, OZ)", r1 == r2 and [x["datei"] for x in r1] == ["C.X83", "A.X83"], str(r1))
    boese = fund(9, "1'; DROP TABLE entscheidungen; --", "x' OR '1'='1", "D'.X83")
    E.status_geaendert(boese, "bestätigt", "D'.X83", "", Z1)
    check("Sonderzeichen werden als Daten gespeichert (SQL-Parameter)", len(zeilen_db()) == 3
          and E.fruehere(fund(9, "1.1", "anderer text", "B.pdf"), "B.pdf") == [])


def test_entwarnt_nie():
    funde = [fund(9, "1.1", "bauschutt laden und entsorgen", "B.pdf", 3, 1), fund(7, "1.2", "oder gleichwertig", "B.pdf", 3, 3),
             fund(1, "1.3", "Rohr DN 150", "B.pdf", 1, 7)]
    vorher, ordnung = copy.deepcopy(funde), [f["id"] for f in sortiere(funde)]
    for f in funde:
        E.fruehere(f, "B.pdf")
    check("Abfrage ändert keinen Fund (Priorität, Kategorie, Stufe)", funde == vorher)
    check("Keine Wirkung auf die Reihenfolge", [f["id"] for f in sortiere(funde)] == ordnung)
    texte = {f["id"]: [{"oz": f["positionen"][0]["oz"], "kurztext": "k", "langtext": "l", "menge": 1.0, "einheit": "St", "ep": None,
                        "gp": None}] for f in funde}
    info = {"format": "PDF", "positionen": 3, "nur_preise": False, "hinweise": [], "fingerprint": "t"}
    zeit = datetime(2026, 11, 22, 3, 0).astimezone()
    werte = lambda: [[c.value for c in r] for w in load_workbook(io.BytesIO(risikobericht("B.pdf", funde, texte, info, s2={}, zeitpunkt=zeit,
                                                                                        commit="test"))).worksheets for r in w.iter_rows()]
    mit = werte()
    db, E_pfad = E.pfad(), str(E.pfad()) + ".weg"
    os.replace(db, E_pfad)
    ohne = werte()
    check("Risikobericht mit und ohne Erfahrungsdatenbank identisch", mit == ohne)
    check("Bericht legt keine Datenbank an", not db.exists())
    os.replace(E_pfad, db)
    a = json.dumps(sortiere(funde), ensure_ascii=False, sort_keys=True)
    E.status_geaendert(funde[1], "verworfen", "X.X83", "", Z1)
    check("Doppellauf: Funde vor und nach einer gespeicherten Entscheidung byte-gleich",
          a == json.dumps(sortiere(funde), ensure_ascii=False, sort_keys=True))


def test_nur_menschliche_aktion():
    aufrufe = []
    for p in sorted(SRC.rglob("*.py")):
        if p.name.startswith("test_") or p.name == "erfahrung.py":
            continue
        t = p.read_text(encoding="utf-8")
        if re.search(r"\.status_geaendert\(", t):
            aufrufe.append(p.name)
        check_sql = "sqlite3" in t
        if check_sql:
            aufrufe.append(f"sqlite3:{p.name}")
    check("Geschrieben wird nur aus app.py, kein anderes Modul nutzt SQLite", aufrufe == ["app.py"], str(aufrufe))
    t = (SRC / "app.py").read_text(encoding="utf-8")
    block = t[t.index("def setze_status"):t.index("# ---", t.index("def setze_status"))]
    check("Aufruf nur in setze_status (Klick auf Bestätigen, Verwerfen, Rückfrage, Offen)",
          t.count("erfahrung.status_geaendert(") == 1 and "erfahrung.status_geaendert(" in block)
    check("Keine R7-Begriffe in den Anzeigetexten", not VERBOTEN.search(E.KENNZEICHNUNG + E.anzeige(
        {"entscheidung": "bestätigt", "datei": "A", "oz": "1", "begruendung": ""})))


def main():
    with tempfile.TemporaryDirectory() as tmp:
        test_pfad(tmp)
        os.environ[E.UMGEBUNG] = str(Path(tmp) / "test" / "erfahrung.sqlite3")
        test_treffer()
        test_entwarnt_nie()
        test_nur_menschliche_aktion()
    print(f"\n{sum(ergebnisse)}/{len(ergebnisse)} Tests bestanden")
    return 0 if all(ergebnisse) else 1


if __name__ == "__main__":
    sys.exit(main())
