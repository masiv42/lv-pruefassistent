"""
test_ui_belegbild.py - B8b / P5 (Sitzung UI2, Team 22.11.2026): Beleg am Original als Bild (nur PDF, nur auf Klick).

Teil 1 und 2 nur mit einer erfundenen PDF (Team F4), die der Test selbst erzeugt. Teil 3 (nur mit Argument data/raw):
Zählung über die PDFs des Datensatzes, ob das Zitat eines Funds auf der angegebenen Seite gefunden wird; ausgegeben
werden nur Dateinamen und Zahlen, kein Text und kein Bild.
Aufruf aus der Projektwurzel: python src/test_ui_belegbild.py [data/raw]
"""
import io
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("LV_FINDINGS_DIR", tempfile.mkdtemp(prefix="lv-belegbild-"))
SRC = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC))
import belegbild as B  # noqa: E402

ergebnisse = []


def check(name, ok, detail=""):
    ergebnisse.append(bool(ok))
    print(("OK    " if ok else "FEHLT ") + name + ("" if ok else f"  [{detail}]"))


def erfundene_pdf(seiten, format_=(595, 842)):
    """Erfundene PDF ohne Zusatzbibliothek: je Seite eine Liste von Textzeilen (Helvetica 11)."""
    objs = ["<< /Type /Catalog /Pages 2 0 R >>", None, "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    kids = []
    for zeilen in seiten:
        inhalt = "BT /F1 11 Tf 50 780 Td 14 TL " + " ".join(f"({z}) Tj T*" for z in zeilen) + " ET"
        objs.append(f"<< /Length {len(inhalt)} >>\nstream\n{inhalt}\nendstream")
        objs.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {format_[0]} {format_[1]}] /Resources << /Font << /F1 3 0 R >> >> "
                    f"/Contents {len(objs)} 0 R >>")
        kids.append(len(objs))
    objs[1] = f"<< /Type /Pages /Kids [{' '.join(f'{k} 0 R' for k in kids)}] /Count {len(kids)} >>"
    out, pos = b"%PDF-1.4\n", []
    for i, o in enumerate(objs, 1):
        pos.append(len(out))
        out += f"{i} 0 obj\n{o}\nendobj\n".encode("latin-1")
    x = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    out += b"".join(f"{p:010d} 00000 n \n".encode() for p in pos)
    return out + f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{x}\n%%EOF\n".encode()


PDF = erfundene_pdf([["Erste Seite, erfunden"],
                     ["Pos 1.10 Erfundenes Rohr DN 150", "liefern und im Graben verlegen", "Preis: 12,50 EUR [x]"]])


def bild(png):
    from PIL import Image                                       # kommt mit pdfplumber
    return Image.open(io.BytesIO(png)).convert("RGB")


if __name__ == "__main__":
    # Teil 1: Funktion
    ohne = B.belegbild(PDF, 2, [])
    mit = B.belegbild(PDF, 2, ["Rohr DN 150 liefern"])           # über zwei Zeilen
    check("Zitat über zwei Zeilen gefunden, je Zeile ein Rahmen", mit["gefunden"] == [True] and mit["rahmen"] == 2,
          str(mit["gefunden"]) + str(mit["rahmen"]))
    check("Bild ist PNG", (mit["png"] or b"")[:8] == b"\x89PNG\r\n\x1a\n")
    check("Rahmen ist im Bild sichtbar", ohne["png"] and mit["png"] and bild(ohne["png"]).tobytes() != bild(mit["png"]).tobytes())
    weg = B.belegbild(PDF, 2, ["Dieser Text steht nicht auf der Seite"])
    check("Zitat nicht gefunden: kein Rahmen (R5)", weg["gefunden"] == [False] and weg["rahmen"] == 0)
    check("Zitat nicht gefunden: Bild ohne Kasten, gleich der leeren Seite",
          weg["png"] and bild(weg["png"]).tobytes() == bild(ohne["png"]).tobytes())
    falsch = B.belegbild(PDF, 1, ["Rohr DN 150"])
    check("Zitat auf anderer Seite: nicht gefunden", falsch["gefunden"] == [False] and falsch["rahmen"] == 0)
    check("Sonderzeichen wörtlich (Klammern, Komma, Doppelpunkt)", B.belegbild(PDF, 2, ["Preis: 12,50 EUR [x]"])["gefunden"] == [True])
    check("Leerraum der Textebene zählt nicht (z. B. „C 3 0/37“)", B.muster("C30/37") == B.muster("C 3 0/37"))
    check("Seite außerhalb des PDF: Hinweis, kein Bild", B.belegbild(PDF, 9, ["x"])["png"] is None
          and "Seite 9" in (B.belegbild(PDF, 9, ["x"])["fehler"] or ""))
    check("Keine PDF: Hinweis statt Absturz", B.belegbild(b"keine pdf", 1, ["x"])["fehler"] is not None)
    # Zuschnitt (Browser-Abnahme 0684e6a, Punkt 2)
    def innen(r, a):
        return a[0] <= r[0] and a[1] <= r[1] and r[2] <= a[2] and r[3] <= a[3]
    check("Zuschnitt: gefundenes Zitat → Ausschnitt statt ganzer Seite", mit["ausschnitt"] is not None
          and mit["ausschnitt"][2] - mit["ausschnitt"][0] < 595 and mit["ausschnitt"][3] - mit["ausschnitt"][1] < 842)
    check("Zuschnitt: alle Rahmen im Ausschnitt", all(innen(r, mit["ausschnitt"]) for r in mit["rahmen_liste"]))
    breite_pt = mit["ausschnitt"][2] - mit["ausschnitt"][0]
    check("Zuschnitt: Schrift (11 pt) bei ~450 px Anzeigebreite ≥ 12 px", 11 * 450 / breite_pt >= 12, f"{breite_pt:.0f} pt")
    check("Zuschnitt: Bild in voller Auflösung des Ausschnitts", bild(mit["png"]).size[0] >= 600, str(bild(mit["png"]).size))
    zwei = B.belegbild(PDF, 2, ["Rohr DN 150", "Preis: 12,50 EUR [x]"])
    check("Mehrere Zitate auf einer Seite: beide gefunden, beide im Ausschnitt", zwei["gefunden"] == [True, True]
          and zwei["rahmen"] >= 2 and all(innen(r, zwei["ausschnitt"]) for r in zwei["rahmen_liste"]))
    check("Nicht gefunden: kein Ausschnitt, ganze Seite", weg["ausschnitt"] is None
          and bild(weg["png"]).size == bild(ohne["png"]).size)
    gross = B.belegbild(erfundene_pdf([["Riesenformat erfunden"]], (14400, 14400)), 1, ["Riesenformat"])
    check("Großes Seitenformat: Bild höchstens MAX_PIXEL je Seite", gross["png"] and max(bild(gross["png"]).size) <= B.MAX_PIXEL,
          str(bild(gross["png"]).size) if gross["png"] else str(gross["fehler"]))
    extrem = B.belegbild(erfundene_pdf([["x"]], (14400 * 20, 14400 * 20)), 1, ["x"])
    check("Extremes Seitenformat: Hinweis statt Bild", extrem["png"] is None and "zu groß" in (extrem["fehler"] or ""),
          str(extrem["fehler"]))

    # Teil 2: Anzeige nur auf Klick, Hinweistext bei nicht gefundenem Zitat
    from streamlit.testing.v1 import AppTest

    def seite(zitat):
        import sys as s
        from pathlib import Path as P
        s.path.insert(0, str(P(__file__).resolve().parent) if "__file__" in dir() else ".")
        import streamlit as st
        import belegbild
        belegbild.anzeigen(st.session_state["pdf"], "sha-test", 2, [st.session_state["zitat"]], "f1")

    for zitat, gefunden in (("Rohr DN 150 liefern", True), ("Steht nicht drin", False)):
        at = AppTest.from_function(seite, args=(zitat,))
        at.session_state["pdf"], at.session_state["zitat"] = PDF, zitat
        at.run(timeout=60)
        check(f"vor dem Klick kein Bild ({'gefunden' if gefunden else 'nicht gefunden'})",
              not at.exception and not at.get("image") and len(at.button) == 1, str(at.exception))
        at.button[0].click().run(timeout=60)
        hinweis = [x.value for x in at.info]
        check(f"nach dem Klick Bild ({'gefunden' if gefunden else 'nicht gefunden'})", not at.exception and at.get("image"),
              str(at.exception))
        if gefunden:
            check("gefunden: kein Hinweis", B.NICHT_GEFUNDEN not in hinweis, str(hinweis))
        else:
            check("nicht gefunden: Hinweistext wörtlich (R5)", hinweis == [B.NICHT_GEFUNDEN], str(hinweis))

    # Teil 2b: in der App (LV-Prüfung) mit einer erfundenen PDF-LV; Status und Datenbank in Temp-Ordnern
    os.environ["LV_ERFAHRUNG_DB"] = str(Path(tempfile.mkdtemp(prefix="lv-belegbild-db-")) / "erfahrung.sqlite3")
    lv_pdf = erfundene_pdf([["Leistungsverzeichnis erfunden", "1.10 Druckrohr PE-HD DN 150",
                             "Druckrohr PE-HD DN 200 liefern und verlegen.", "20,000 m ........ ........",
                             "1.20 Fundament Beton C25/30", "Ortbeton C30/37 herstellen.", "5,000 m3 ........ ........"]])
    at = AppTest.from_file(str(SRC / "app.py"), default_timeout=180).run()
    at.get("file_uploader")[0].upload("Erfunden-Beleg.pdf", lv_pdf).run()
    at.switch_page("pages/funde.py").run()                        # UI3: Detailansicht auf „Funde prüfen“
    knopf = [b for b in at.button if b.label.startswith("Beleg im Original zeigen")]
    check("App, PDF: Knopf „Beleg im Original zeigen (Seite …)“, noch kein Bild", not at.exception and knopf
          and not at.get("image"), str(at.exception))
    if knopf:
        knopf[0].click().run()
        check("App, PDF: nach dem Klick Bild der Originalseite", not at.exception and at.get("image"), str(at.exception))
    at2 = AppTest.from_file(str(SRC / "app.py"), default_timeout=180).run()
    import test_ui_sitzung as TS
    at2.get("file_uploader")[0].upload("Erfunden.X83", TS.x83(["0010"])).run()
    at2.switch_page("pages/funde.py").run()
    check("App, GAEB: kein Bild-Knopf (nur PDF)", not at2.exception
          and not [b for b in at2.button if b.label.startswith("Beleg im Original")], str(at2.exception))

    # Teil 3: Datensatz (nur Zählung, keine Inhalte)
    if len(sys.argv) > 1:
        from bericht import pruefe_lv
        dateien_ok, gesamt, treffer = set(), 0, 0
        for pfad in sorted(Path(sys.argv[1]).iterdir()):
            if pfad.suffix.lower() != ".pdf":
                continue
            funde, _, _ = pruefe_lv(pfad)
            daten = pfad.read_bytes()
            n = t = 0
            for f in funde:
                p = f["positionen"][0]
                if p["seite"] is None or not f["belege"]:
                    continue
                n += 1
                if B.belegbild(daten, int(p["seite"]), f["belege"][:1], aufloesung=20)["gefunden"] == [True]:
                    t += 1
            gesamt, treffer = gesamt + n, treffer + t
            if t:
                dateien_ok.add(pfad.name)
            print(f"  {pfad.name}: {t} von {n} Funden mit Seite – Zitat auf der Seite gefunden")
        check(f"Datensatz: in mindestens 5 verschiedenen PDFs Zitat auf der richtigen Seite ({len(dateien_ok)} PDFs, "
              f"{treffer} von {gesamt} Funden)", len(dateien_ok) >= 5, str(len(dateien_ok)))
    print(f"\n{sum(ergebnisse)}/{len(ergebnisse)} Tests bestanden")
    sys.exit(0 if all(ergebnisse) else 1)
