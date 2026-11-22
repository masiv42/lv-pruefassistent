"""
test_ui_sitzung.py - B8e (Sitzung UI2, Team 22.11.2026): Das aktuelle LV liegt in einem zentralen Session-Eintrag,
unabhängig vom Upload-Feld (A1). Seitenwechsel verliert weder LV noch Status noch Begründungstext.

Nur erfundene Dateien (Team F4). Status und Erfahrungsdatenbank liegen in Temp-Ordnern (LV_FINDINGS_DIR,
LV_ERFAHRUNG_DB), nie im Projekt (E12 (4)). Aufruf aus der Projektwurzel:
  python src/test_ui_sitzung.py
"""
import os
import re
import sys
import tempfile
from pathlib import Path

TEMP = Path(tempfile.mkdtemp(prefix="lv-ui-sitzung-"))
os.environ["LV_FINDINGS_DIR"] = str(TEMP / "findings")
os.environ["LV_ERFAHRUNG_DB"] = str(TEMP / "erfahrung.sqlite3")
os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")

from streamlit.testing.v1 import AppTest  # noqa: E402

SRC = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC))
import lv_sitzung  # noqa: E402
import bericht  # noqa: E402

if "tabelle" not in bericht.pruefe_lv.__code__.co_consts and "tabelle" not in Path(bericht.__file__).read_text(
        encoding="utf-8"):
    # Nur im Testprozess: simuliert Vorschlag 1 (info["tabelle"], docs/uebergabe_sitzung_UI2.md), solange B4 ihn nicht
    # übertragen hat; dieselbe Feldliste aus einem parse() derselben Datei. Die App selbst bleibt unverändert.
    _original = bericht.pruefe_lv

    def _mit_tabelle(pfad, zuordnung=None):
        funde, texte, info = _original(pfad, zuordnung)
        df = bericht.parse(Path(pfad))
        bericht.alle_pruefungen(df, Path(pfad))                     # wie in pruefe_lv: gleicher Stand von df (OZ)
        pos = df[df.typ == "Position"]
        info["tabelle"] = [{"oz": r.oz, "titel": r.titel or "", "kurztext": r.kurztext or "", "langtext": r.langtext or "",
                            "menge": r.menge, "einheit": r.einheit or "", "ep": r.ep, "gp": r.gp, "seite": None}
                           for r in pos.itertuples()]
        return funde, texte, info
    bericht.pruefe_lv = _mit_tabelle
    print("Hinweis: info[\"tabelle\"] im Test simuliert (Vorschlag 1 noch nicht in bericht.py)")

ergebnisse = []


def check(name, ok, detail=""):
    ergebnisse.append(bool(ok))
    print(("OK    " if ok else "FEHLT ") + name + ("" if ok else f"  [{detail}]"))


def x83(rnos):
    """Erfundenes GAEB-XML-LV: je RNo eine Position mit DN-Widerspruch zwischen Kurz- und Langtext (Prüfung Nr. 1)."""
    items = "".join(
        f'<Item RNoPart="{r}"><Qty>2</Qty><QU>m</QU><Description><CompleteText><DetailTxt><Text><p><span>'
        f'Erfundenes Rohr DN 200 verlegen.</span></p></Text></DetailTxt><OutlineText><OutlTxt><TextOutlTxt><p>'
        f'<span>Erfundenes Rohr DN 150</span></p></TextOutlTxt></OutlTxt></OutlineText></CompleteText>'
        f'</Description></Item>' for r in rnos)
    return ('<?xml version="1.0" encoding="UTF-8"?><GAEB xmlns="http://www.gaeb.de/GAEB_DA_XML/DA83/3.2"><Award>'
            '<BoQ><BoQBody><BoQCtgy RNoPart="01"><LblTx>Erfundener Abschnitt</LblTx><BoQBody><Itemlist>'
            f'{items}</Itemlist></BoQBody></BoQCtgy></BoQBody></BoQ></Award></GAEB>').encode()


def texte(at):
    """Markdown und Captions ohne Markdown-Maskierung (ui_stil.md_text setzt Backslashes)."""
    teile = [x.value.replace("\\", "") for x in list(at.markdown) + list(at.caption)]
    teile += [x.proto.body for x in at.get("html")]                 # UI3: Kopf und Bausteine als HTML
    return " ".join(teile)


def knoepfe(at):
    return {b.label: b for b in at.button}


def lade(at, name, daten):
    at.get("file_uploader")[0].upload(name, daten).run()
    return at


if __name__ == "__main__":
    # Schlüssel: gleiche Datei ohne Zuordnung wie bisher; andere Excel-Zuordnung = anderer Schlüssel (Auflage 2)
    alt = "lv-" + __import__("hashlib").sha256(b"a.X83" + b"x").hexdigest()[:16]
    check("Schlüssel ohne Zuordnung unverändert", lv_sitzung.status_schluessel("a.X83", b"x", ()) == alt)
    k1 = lv_sitzung.status_schluessel("a.xlsx", b"x", (("OZ", "A"), ("Kurztext", "B")))
    k2 = lv_sitzung.status_schluessel("a.xlsx", b"x", (("OZ", "A"), ("Kurztext", "C")))
    check("Andere Excel-Zuordnung, anderer Schlüssel", k1 != k2 and k1 != alt)

    at = AppTest.from_file(str(SRC / "app.py"), default_timeout=180).run()
    check("Start ohne LV: keine Ausnahme", not at.exception, str(at.exception))
    lade(at, "Erfunden-Sitzung.X83", x83(["0010", "0020"]))
    check("Nach dem Upload: Entscheidungsübersicht", not at.exception and "Zuerst klären" in texte(at), str(at.exception))
    at.switch_page("pages/funde.py").run()                          # UI3: Status wird auf „Funde prüfen“ gesetzt
    check("LV geladen: Statusknöpfe da", "Bestätigen" in knoepfe(at) and not at.exception, str(at.exception))
    knoepfe(at)["Bestätigen"].click().run()
    check("Status gesetzt", knoepfe(at)["Bestätigen"].disabled)
    # Auflage 6: Downloads entstehen erst beim Klick (Funktion), mit dem angezeigten Stand
    dl = at.session_state["lv_downloads"] if "lv_downloads" in at.session_state else []
    check("Downloads als Funktion (data=callable)", len(dl) == 2 and all(callable(d["daten"]) for d in dl))
    if dl:
        import io
        from openpyxl import load_workbook
        roh = dl[0]["daten"]()
        werte = {str(c.value) for ws in load_workbook(io.BytesIO(roh)).worksheets for r in ws.iter_rows() for c in r}
        check("Risikobericht aus der Funktion: .xlsx mit gesetztem Status", roh[:2] == b"PK" and "bestätigt" in werte)
        check("Bieterfragen aus der Funktion: .xlsx", dl[1]["daten"]()[:2] == b"PK")
    feld = [t for t in at.text_input if str(t.key).startswith("begr-")]
    check("Begründungsfeld vorhanden", len(feld) == 1)
    if feld:
        feld[0].input("Erfundene Begründung").run()

    at.switch_page("pages/uebersicht.py").run()
    check("Übersicht zeigt das LV", not at.exception and "Erfunden-Sitzung.X83" in texte(at), str(at.exception))
    # Auflage 7 gilt für die bisherige Übersichtsseite (0_Uebersicht.py, seit UI3 nicht in der Navigation): einzeln geprüft
    import json
    alt = AppTest.from_file(str(SRC / "pages" / "0_Uebersicht.py"), default_timeout=60)
    alt.session_state["lv_uebersicht"] = at.session_state["lv_uebersicht"]
    alt.run()
    charts = alt.get("vega_lite_chart")
    spec = json.loads(charts[0].proto.spec) if charts else {}
    marks = [(l.get("mark") or {}) for l in spec.get("layer", [])]
    kodiert = [l.get("encoding", {}) for l in spec.get("layer", [])]
    check("Diagramm: Zahl am Balken, ein neutraler Ton, keine Farbcodierung (Auflage 7)",
          [m.get("type") for m in marks] == ["bar", "text"] and marks[0].get("color") == "#7C8BA3"
          and not any("color" in k for k in kodiert), str(marks)[:200])
    at.switch_page("pages/funde.py").run()
    b = knoepfe(at)
    check("Nach Seitenwechsel: LV noch geladen (B8e)", "Bestätigen" in b, str(list(b)))
    check("Nach Seitenwechsel: Status bleibt", "Bestätigen" in b and b["Bestätigen"].disabled)
    feld = [t for t in at.text_input if str(t.key).startswith("begr-")]
    check("Nach Seitenwechsel: Begründungstext bleibt (Auflage 3)",
          feld and feld[0].value == "Erfundene Begründung", str([t.value for t in feld]))
    check("Kopf nennt das aktuelle LV", "Erfunden-Sitzung.X83" in texte(at), texte(at)[:200])

    # A3: Fund → Position → Fund, Filter bleiben (Auflage A3)
    at.multiselect(key="pf_stufe").set_value([1]).run()
    zur = [b for b in at.button if b.label == "Zur Position"]
    check("Detail: Knopf „Zur Position“", bool(zur))
    if zur:
        fid0 = at.session_state["pf_fund"]
        oz0 = next(f["positionen"][0]["oz"] for f in at.session_state["lv_uebersicht"]["funde"] if f["id"] == fid0)
        zur[0].click().run()
        wahl = [s for s in at.selectbox if s.key == "pos_wahl"]
        text = str(wahl[0].format_func(wahl[0].value)) if wahl else ""
        check("Sprung landet auf der Position des Funds", not at.exception and text.startswith(f"OZ {oz0}"),
              f"{at.exception} {text} {oz0}")
        oeffnen = [b for b in at.button if b.label == "Fund öffnen"]
        check("Position: Knopf „Fund öffnen“", bool(oeffnen))
        if oeffnen:
            fid1 = re.match(r"fund-oeffnen-(.*)-\d+$", str(oeffnen[0].key)).group(1)
            oeffnen[0].click().run()
            check("Rücksprung öffnet genau diesen Fund", not at.exception and "pf_fund" in at.session_state
                  and at.session_state["pf_fund"] == fid1, f"{at.exception} {fid1}")
            check("Rücksprung: Filter so erweitert, dass der Fund sichtbar ist",
                  "pf_stufe" in at.session_state and 1 in at.session_state["pf_stufe"])
            at.multiselect(key="pf_stufe").set_value([1]).run()
    at.switch_page("pages/uebersicht.py").run()
    at.switch_page("pages/funde.py").run()
    check("Filter übersteht Seitenwechsel", "pf_stufe" in at.session_state and at.session_state["pf_stufe"] == [1],
          str(at.session_state["pf_stufe"]) if "pf_stufe" in at.session_state else "fehlt")

    # Positionsseite und Zuschlagsseite: keine Ausnahme mit geladenem LV
    for seite in ("pages/2_Positionen.py", "pages/1_Zuschlag_und_What-if.py"):
        at.switch_page(seite).run()
        check(f"{seite}: keine Ausnahme", not at.exception, str(at.exception))
    at.switch_page("pages/funde.py").run()

    # Neuer Upload ersetzt das aktuelle LV sichtbar
    lade(at, "Erfunden-Zweites.X83", x83(["0030"]))
    akt = (at.session_state[lv_sitzung.AKTUELL] if lv_sitzung.AKTUELL in at.session_state else None) or {}
    check("Neuer Upload ersetzt das LV", akt.get("name") == "Erfunden-Zweites.X83", str(akt.get("name")))
    check("Ersetzen wird angezeigt", any("ersetzt" in x.value for x in list(at.caption) + list(at.info)),
          str([x.value for x in at.caption][:5]))

    # Upload-Feld leeren (X) entfernt das LV nicht; nur „Anderes LV laden“ tut das
    at.get("file_uploader")[0].clear().run() if hasattr(at.get("file_uploader")[0], "clear") else None
    check("Leeren des Upload-Felds behält das LV", "Bestätigen" in knoepfe(at), str(list(knoepfe(at))))
    if "Anderes LV laden" in knoepfe(at):
        knoepfe(at)["Anderes LV laden"].click().run()
    check("„Anderes LV laden“ entfernt das aktuelle LV", "Bestätigen" not in knoepfe(at)
          and lv_sitzung.AKTUELL in at.session_state and at.session_state[lv_sitzung.AKTUELL] is None)

    # Navigation vollständig (UI3): jede Seite in pages/ ist in app.py registriert, außer der abgelösten
    # 0_Uebersicht.py (Lücke an das Team gemeldet); die Seitenleiste zeichnet app.py für jede Seite (Auflage 5)
    router = (SRC / "app.py").read_text(encoding="utf-8")
    registriert = set(re.findall(r'st\.Page\("([^"]+)"', router))
    dateien = {f"pages/{p.name}" for p in (SRC / "pages").glob("*.py")} - {"pages/0_Uebersicht.py"}
    check("Navigation nennt jede Seite", dateien == registriert, str(dateien ^ registriert))
    check("Startseite ist die Entscheidungsübersicht (Drehbuch beginnt dort)",
          re.search(r'st\.Page\("pages/uebersicht\.py"[^)]*default=True', router) is not None)
    check("Seitenleiste und Statusleiste für alle Seiten im Router (Auflage 5)",
          "ui.seitenleiste(" in router and "ui.statusleiste(" in router and "position=\"hidden\"" in router)
    projekt = SRC.parent / "data" / "findings"
    check("Keine Statusdatei im Projekt (E12 (4))", not (projekt / "Erfunden-Sitzung.X83.json").exists())
    print(f"\n{sum(ergebnisse)}/{len(ergebnisse)} Tests bestanden")
    sys.exit(0 if all(ergebnisse) else 1)
