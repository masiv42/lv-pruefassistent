"""
test_nachtrag_streit.py - Tests für M2b (Sicht „Nachtragspotenzial und Streitpunkte“, Team 22.11.2026, 01:25).

Teil 1 mit erfundenen Funden, Teil 2 mit AppTest (kein Port, schreibt nichts), Teil 3 über alle Dateien in data/raw (R7, keine
neuen Funde, E14).
Aufruf aus der Projektwurzel (uv-Befehl siehe AGENTS.md, mit --with streamlit==1.67.0):
  python src/test_nachtrag_streit.py data/raw
Exit-Code 0 = alle Tests bestanden.
"""
import copy
import io
import re
import sys
from datetime import datetime
from pathlib import Path

from openpyxl import load_workbook
from streamlit.testing.v1 import AppTest

SRC = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC))
import nachtrag_streit as N                                            # noqa: E402
from bericht import risikobericht                                      # noqa: E402
from lv_parser import parse                                            # noqa: E402
from pruefung_formal import alle_pruefungen, sortiere                  # noqa: E402
from pruefung_widerspruch import PRIORITAET_IN_STUFE                   # noqa: E402

D = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/raw")
SEITE = str(SRC / "pages" / "3_Nachtrag_und_Streitpunkte.py")
VERBOTEN = re.compile(r"Anspruch|berechtigt|durchsetzbar|§")
ZEIT = datetime(2026, 11, 22, 2, 0).astimezone()
ergebnisse = []


def check(name, ok, detail=""):
    ok = bool(ok)
    ergebnisse.append(ok)
    print(f"{'OK    ' if ok else 'FEHLER'} {name}" + (f" – {detail}" if detail and not ok else ""))


def fund(nr, stufe, rang, oz, kat, beleg, datei="demo.X83", status="offen", begr="b. Empfehlung: vormerken."):
    return {"id": f"{nr}|{datei}|{oz}", "pruefung": nr, "kategorie": kat, "titel": f"Titel {nr}",
            "positionen": [{"datei": datei, "oz": oz, "seite": None}], "belege": [beleg], "feldbelege": [],
            "begruendung": begr, "stufe": stufe, "stufe_begruendung": "s", "prioritaet_in_stufe": rang, "rueckfrage": None,
            "status": status}


FUNDE = [fund(12, 4, 5, "1.9", "Unklarheit", "wie vor, jedoch H 2,5 m"), fund(9, 3, 1, "1.8", "Risikohinweis", "Bauschutt entsorgen"),
         fund(1, 1, 7, "1.2", "möglicher Widerspruch", "Druckrohr DN 150", begr="Kurztext DN 150, Langtext DN 200."),
         fund(7, 3, 3, "1.1", "Risikohinweis", "oder gleichwertig"), fund(16, 1, 4, "1.3", "möglicher Widerspruch", "Rinne 30 cm",
                                                                         begr="gleiche Leistung."),
         fund(13, 4, 3, "1.4", "Risikohinweis", "Stundenlohn Bauwerker"), fund(6, 2, 1, "1.5", "Risikohinweis", "Wasserhaltung"),
         fund(3, 1, 2, "1.6", "nachweisbarer Fehler", "Rohr ohne Einheit"), fund(19, 3, 5, "1.7", "Risikohinweis", "Ortbeton")]
KURZ = {f["positionen"][0]["oz"]: f"Kurztext {f['positionen'][0]['oz']}" for f in FUNDE}


def katalog():
    """{Nr: (Kategorie, Stufe)} aus der Haupttabelle von input/pruefkatalog.md (erste Tabelle mit Spalte „Kategorie“)."""
    aus = {}
    for z in (SRC.parent / "input" / "pruefkatalog.md").read_text(encoding="utf-8").splitlines():
        t = [x.strip() for x in z.split("|")]
        if len(t) > 12 and t[1].isdigit():
            aus.setdefault(int(t[1]), (t[3], t[4]))
    return aus


def test_zuordnung():
    k = katalog()
    stufe3 = sorted({nr for (nr, s) in PRIORITAET_IN_STUFE if s == 3})
    check("Abschnitt A = alle Prüfungen der Stufe 3 laut zentraler Rangtabelle (Nr. 7, 8, 9, 10, 19)",
          sorted(N.ABSCHNITTE["A"]["pruefungen"]) == stufe3 == [7, 8, 9, 10, 19], str(stufe3))
    check("Abschnitt A: im Katalog alle Stufe 3", all(k[n][1].startswith("3") for n in N.ABSCHNITTE["A"]["pruefungen"]))
    b = N.ABSCHNITTE["B"]["pruefungen"]
    check("Abschnitt B: jede Nr. im Katalog „möglicher Widerspruch“ oder „Unklarheit“",
          all(k[n][0] in ("möglicher Widerspruch", "Unklarheit") for n in b), str({n: k[n][0] for n in b}))
    check("Nr. 13 fällt heraus: Katalog „Risikohinweis“, mit Eintrag", k[13][0] == "Risikohinweis" and 13 not in b and 13 in N.NICHT_ZUGEORDNET)
    check("Keine Prüfung in beiden Abschnitten", not set(b) & set(N.ABSCHNITTE["A"]["pruefungen"]))


def test_sicht():
    vorher = copy.deepcopy(FUNDE)
    z = N.zeilen(FUNDE, KURZ.get)
    check("Keine neuen Funde: jede Zeile ist ein vorhandener Fund", {r["Fund-ID"] for r in z} <= {f["id"] for f in FUNDE})
    check("Funde werden nicht verändert", FUNDE == vorher)
    nr = {int(r["Fund-ID"].split("|")[0]) for r in z}
    check("Positiv: Nr. 7, 9, 19, 1, 16, 12 enthalten", nr == {7, 9, 19, 1, 16, 12}, str(nr))
    check("Negativ: Nr. 3, 6, 13 nicht enthalten", not nr & {3, 6, 13})
    a = [r["Fund-ID"] for r in z if r["Abschnitt"] == N.ABSCHNITTE["A"]["titel"]]
    b = [r["Fund-ID"] for r in z if r["Abschnitt"] == N.ABSCHNITTE["B"]["titel"]]
    check("Abschnitt A sortiert nach Rang in Stufe (Nr. 9, 7, 19)", [i.split("|")[0] for i in a] == ["9", "7", "19"], str(a))
    check("Abschnitt B sortiert nach Stufe und Rang (Nr. 16, 1, 12)", [i.split("|")[0] for i in b] == ["16", "1", "12"], str(b))
    r = next(x for x in z if x["Fund-ID"].startswith("1|"))
    check("Je Fund OZ, Kurztext, Beleg, Kategorie, Stufe, Empfehlung, Bieterfrage",
          r["OZ"] == "1.2" and r["Kurztext"] == "Kurztext 1.2" and "„Druckrohr DN 150“" in r["Beleg (wörtlich aus dem LV)"]
          and r["Kategorie"] == "möglicher Widerspruch" and r["Stufe"].startswith("1 –")
          and r["Handlungsempfehlung"] == "klärende Rückfrage" and r["Bieterfrage (Entwurf)"], str(r))
    check("Ohne Rückfrage-Empfehlung keine Bieterfrage", next(x for x in z if x["Fund-ID"].startswith("9|"))["Bieterfrage (Entwurf)"] == "")
    v = [fund(1, 1, 7, "1.2", "möglicher Widerspruch", "Rohr", status="verworfen", begr="x")]
    check("Verworfener Fund bleibt in der Sicht, ohne Bieterfrage", N.zeilen(v, KURZ.get)[0]["Bieterfrage (Entwurf)"] == ""
          and N.zeilen(v, KURZ.get)[0]["Status"] == "verworfen")
    au = [fund(1, 1, 7, "1.2", "möglicher Widerspruch", "Rohr", datei="demo.D86", begr="x")]
    check("Auftrags-LV: keine Bieterfrage", N.zeilen(au, KURZ.get)[0]["Bieterfrage (Entwurf)"] == "")
    za = N.zaehlung(FUNDE)
    check("Zählung je Abschnitt und Prüfung", za["A"]["gesamt"] == 3 and za["B"]["gesamt"] == 3 and za["A"]["je_pruefung"][8] == 0, str(za))
    check("Keine Geld- oder Score-Spalten", not any(re.search(r"€|EP|GP|Score|Betrag|Konfidenz", s) for s in N.SPALTEN))
    check("E14: zweiter Aufruf identisch, auch bei anderer Eingabereihenfolge", z == N.zeilen(list(reversed(FUNDE)), KURZ.get))


def lauf(zustand):
    at = AppTest.from_file(SEITE)
    if zustand is not None:
        at.session_state["lv_uebersicht"] = zustand
    return at.run(timeout=60)


def seitentext(at):
    teile = [x.value for art in (at.title, at.info, at.markdown, at.caption, at.subheader) for x in art]
    teile += [m.label for m in at.metric]
    return "\n".join(str(t) for t in teile)


def test_seite():
    at = lauf({"lv_name": "Demo.X83", "positionen": 9, "funde": FUNDE, "kurztexte": KURZ})
    check("Seite läuft ohne Ausnahme", not at.exception, str(at.exception))
    t = seitentext(at)
    check("Hinweistext oben", at.info[0].value == "Hinweise zur Prüfung, keine Rechtsaussage.")
    check("Beide Abschnitte mit Zählung", all(a["titel"] in t for a in N.ABSCHNITTE.values())
          and [m.value for m in at.metric] == ["3", "3"], str([m.value for m in at.metric]))
    check("Je Abschnitt eine Tabelle", len(at.dataframe) == 2, str(len(at.dataframe)))
    tabelle = "\n".join(str(v) for d in at.dataframe for v in d.value.astype(str).values.ravel())
    check("Tabelle enthält den wörtlichen Beleg", "Druckrohr DN 150" in tabelle and "Bauschutt entsorgen" in tabelle)
    check("Seite: keine verbotenen Begriffe (R7)", not VERBOTEN.search(t + tabelle))
    check("Seite: keine Geldbeträge", "€" not in t + tabelle)
    leer = lauf({"lv_name": "Leer.X83", "positionen": 2, "funde": [], "kurztexte": {}})
    check("Ohne Funde: klare Aussage, keine Ausnahme", not leer.exception and N.KEINE in "\n".join(m.value for m in leer.markdown))
    ohne = lauf(None)
    check("Ohne geprüftes LV: Hinweis auf die Hauptseite", not ohne.exception and "Hauptseite" in "\n".join(m.value for m in ohne.markdown))


def blatt(funde, texte):
    info = {"format": "PDF", "positionen": 1, "nur_preise": False, "hinweise": [], "fingerprint": "t"}
    return load_workbook(io.BytesIO(risikobericht("demo.X83", funde, texte, info, s2={}, zeitpunkt=ZEIT, commit="test")))


def test_export():
    texte = {f["id"]: [{"oz": f["positionen"][0]["oz"], "kurztext": KURZ[f["positionen"][0]["oz"]], "langtext": "l", "menge": 1.0,
                        "einheit": "St", "ep": None, "gp": None}] for f in FUNDE}
    wb = blatt(FUNDE, texte)
    check("Export: eigenes Blatt „Nachtrag und Streitpunkte“", N.BLATT in wb.sheetnames, str(wb.sheetnames))
    ws = wb[N.BLATT]
    check("Export: Hinweistext oben", ws["A2"].value == N.HINWEIS)
    werte = [c.value for r in ws.iter_rows() for c in r if c.value is not None]
    kopf = next(i for i, r in enumerate(ws.iter_rows(values_only=True), 1) if r[0] == "Nr.")
    ids = [r[N.SPALTEN.index("Fund-ID")] for r in ws.iter_rows(min_row=kopf + 1, values_only=True)]
    check("Export: Zeilen wie die Sicht, in gleicher Reihenfolge", ids == [z["Fund-ID"] for z in N.zeilen(FUNDE, KURZ.get)], str(ids))
    check("Export: keine verbotenen Begriffe, keine Geldbeträge",
          not any(isinstance(v, str) and (VERBOTEN.search(v) or "€" in v) for v in werte))
    leer = blatt([], {})
    check("Export ohne Funde: Blatt mit klarer Aussage", N.KEINE in [c.value for r in leer[N.BLATT].iter_rows() for c in r])


def test_datensatz():
    if not D.is_dir():
        check(f"Ordner {D} vorhanden", False)
        return
    funde_alle, abw, r7 = 0, [], []
    for p in sorted(D.iterdir(), key=lambda x: x.name):
        if p.name == ".DS_Store" or p.suffix.lower() == ".docx":
            continue
        df = parse(p)
        funde = alle_pruefungen(df, p)
        pos = df[df.typ == "Position"]
        kurz = {r.oz: (r.kurztext if isinstance(r.kurztext, str) else "") for r in pos.itertuples()}
        z = N.zeilen(funde, kurz.get)
        soll = [f["id"] for k in N.ABSCHNITTE for f in sortiere(funde) if f["pruefung"] in N.ABSCHNITTE[k]["pruefungen"]]
        if [r["Fund-ID"] for r in z] != soll or not all(r["Handlungsempfehlung"] for r in z):
            abw.append(p.name)
        funde_alle += len(z)
        r7 += [(p.name, r["Fund-ID"]) for r in z if any(isinstance(v, str) and VERBOTEN.search(v) for v in r.values())]
    print(f"INFO   Sicht über alle Dateien: {funde_alle} Zeilen")
    check("Datensatz: Sicht = genau die Funde der Zuordnung, sortiert, jede Zeile mit Handlungsempfehlung", not abw, str(abw[:3]))
    check("Datensatz: Seite und Export ohne verbotene Begriffe (R7)", not r7, str(r7[:3]))


def main():
    test_zuordnung()
    test_sicht()
    test_seite()
    test_export()
    test_datensatz()
    print(f"\n{sum(ergebnisse)}/{len(ergebnisse)} Tests bestanden")
    return 0 if all(ergebnisse) else 1


if __name__ == "__main__":
    sys.exit(main())
