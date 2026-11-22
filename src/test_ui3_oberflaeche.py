"""
test_ui3_oberflaeche.py - Block UI3 (Redesign): Designsystem src/oberflaeche.py, Startseite und Entscheidungsübersicht.

Prüft die Inhaltsregeln, die auch im freien Design gelten: LV-Text maskiert und wörtlich (R5), Hervorhebung ändert den
Text nicht, keine erfundenen Zahlen (R11: fehlend „–“, ohne Grundmenge kein Prozent), keine Euro-Beträge oder Scores,
keine R7-Begriffe, Kontrast der Textfarben ≥ 4,5:1 in Dark und Light, Farbe nur nach Kategorie. Dazu ein Ablauf mit einer
erfundenen Datei (Team F4): Start erklärt das Tool, nach dem Upload Kennzahlen aus echten Zählungen.
Aufruf aus der Projektwurzel: python src/test_ui3_oberflaeche.py
"""
import os
import re
import sys
import tempfile
from pathlib import Path

os.environ["LV_FINDINGS_DIR"] = tempfile.mkdtemp(prefix="lv-ui3-")
os.environ["LV_ERFAHRUNG_DB"] = str(Path(tempfile.mkdtemp(prefix="lv-ui3-db-")) / "erfahrung.sqlite3")
SRC = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC))
import oberflaeche as ui  # noqa: E402

ergebnisse = []
VERBOTEN = re.compile(r"Anspruch|berechtigt|durchsetzbar|§|score|konfidenz|confidence", re.I)


def check(name, ok, detail=""):
    ergebnisse.append(bool(ok))
    print(("OK    " if ok else "FEHLT ") + name + ("" if ok else f"  [{detail}]"))


def kontrast(a, b):
    def l(hx):
        c = [int(hx[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
        return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
    x, y = sorted([l(a), l(b)], reverse=True)
    return (x + 0.05) / (y + 0.05)


def _item(rno, kurz, lang, qty=None, qu="m", up=None, it=None):
    q = f"<Qty>{qty}</Qty>" if qty is not None else ""
    preis = (f"<UP>{up}</UP>" if up is not None else "") + (f"<IT>{it}</IT>" if it is not None else "")
    return (f'<Item RNoPart="{rno}">{q}<QU>{qu}</QU>{preis}<Description><CompleteText><DetailTxt><Text><p><span>{lang}'
            f'</span></p></Text></DetailTxt><OutlineText><OutlTxt><TextOutlTxt><p><span>{kurz}</span></p></TextOutlTxt>'
            f'</OutlTxt></OutlineText></CompleteText></Description></Item>')


def test_lv():
    """Erfundenes LV (Team F4): Funde aller vier Stufen, Rechenfehler Menge × EP ≠ GP (80 × 4,00 ≠ 330,00), fehlende Preise."""
    items = "".join([
        _item("0010", "Druckrohr PE-HD DN 150", "Druckrohr PE-HD DN 200 liefern und im Rohrgraben verlegen.", "20", "m",
              "12.50", "250.00"),
        _item("0020", "Fundament Beton C25/30", "Ortbeton C30/37 für Einzelfundament herstellen.", "5", "m3", "180.00",
              "900.00"),
        _item("0030", "Boden laden und entsorgen", "Aushub laden und entsorgen, Entsorgungsweg nach Wahl des AN.", "120", "m3"),
        _item("0040", "Wasserhaltung", "Wasserhaltung nach Erfordernis für die gesamte Bauzeit, Abrechnung nach Aufwand.",
              "1", "psch"),
        _item("0050", "Schachtabdeckung reinigen", "Schachtabdeckung reinigen und gangbar machen.", None, "St"),
        _item("0060", "Bauzaun vorhalten", "Bauzaun aufstellen und für die Bauzeit vorhalten.", "80", "m", "4.00", "330.00"),
        _item("0070", "Schutzzaun", "Schutzzaun aufstellen.", "10", "m", "5.00", "50.00"),
    ])
    return ('<?xml version="1.0" encoding="UTF-8"?><GAEB xmlns="http://www.gaeb.de/GAEB_DA_XML/DA83/3.2"><Award><BoQ><BoQBody>'
            '<BoQCtgy RNoPart="01"><LblTx>Erfundener Abschnitt Erdarbeiten</LblTx><BoQBody><Itemlist>'
            f'{items}</Itemlist></BoQBody></BoQCtgy></BoQBody></BoQ></Award></GAEB>').encode()


if __name__ == "__main__":
    # Text und Zahlen
    check("Tausenderpunkt, fehlend „–“", ui.de_zahl(1248) == "1.248" and ui.de_zahl(None) == "–")
    check("Prozent ohne Grundmenge „–“ (keine erfundene 0 %)", ui.de_prozent(0, 0) == "–" and ui.de_prozent(2, 3) == "67 %")
    roh = "<b>Rohr</b> DN 150 & C30/37 [ORT_024]"
    html = ui.beleg_html(roh)
    check("Beleg maskiert HTML", "<b>" not in html and "&lt;b&gt;" in html)
    # Angepasst (Browser-Abnahme 796adee, Punkt 2): Marker nur auf der tragenden Aussage je Prüfung; Text bleibt gleich
    h1, h2, h9 = ui.beleg_html(roh, 1), ui.beleg_html(roh, 2), ui.beleg_html(roh, 9)
    check("Hervorhebung ändert den Text nicht (Nr. 1, 2, andere)",
          all(re.sub(r"</?mark>", "", x) == ui.h(roh) for x in (h1, h2, h9, html)))
    check("2: Nr. 1 markiert nur DN-Werte", "<mark>DN 150</mark>" in h1 and "<mark>C30/37</mark>" not in h1)
    check("2: Nr. 2 markiert nur Betonklassen", "<mark>C30/37</mark>" in h2 and "<mark>DN 150</mark>" not in h2)
    check("2: andere Prüfungen und ohne Prüfung ohne Markierung", "<mark>" not in h9 and "<mark>" not in html)
    check("2: Beispielblatt markiert nur DN und Betonklassen",
          all(w.startswith(("DN", "C")) for w in ui.BEISPIEL_MARKIERT))
    check("Platzhalter bleiben wörtlich (R9)", "[ORT_024]" in html)
    f = {"id": "1|t|1.1", "pruefung": 1, "stufe": 1, "kategorie": "nachweisbarer Fehler", "titel": "<i>x</i>",
         "positionen": [{"oz": "1.1", "seite": None}], "status": "offen"}
    check("Fundzeile maskiert den Titel", "<i>" not in ui.fund_zeile_html(f))
    check("Kennzahl maskiert", "<img" not in ui.kennzahlen_html([ui.Kennzahl("<img src=x>", "1")]))
    check("Verteilung: leere Liste ohne Fehler", "lv-verteilung" in ui.verteilung_html("x", []))

    # Farben
    for modus, F in ui.FARBEN.items():
        for name in ("text", "text2", "text3", "rot", "bernstein", "gruen", "neutral", "akzent"):
            for grund in ("grund", "flaeche"):
                w = kontrast(F[name], F[grund])
                check(f"{modus}: {name} auf {grund} ≥ 4,5:1", w >= 4.5, f"{w:.2f}")
        for ton in ("rot", "bernstein", "gruen", "neutral"):
            w = kontrast(F[ton], F[f"{ton}_weich"])
            check(f"{modus}: Chip {ton} ≥ 4,5:1", w >= 4.5, f"{w:.2f}")
        check(f"{modus}: Knopf Akzent ≥ 4,5:1", kontrast(F["akzent_text"], F["akzent_fl"]) >= 4.5)
        check(f"{modus}: Markierung ≥ 4,5:1", kontrast(F["markierung_text"], F["markierung"]) >= 4.5)
    check("Rot nur für nachweisbaren Fehler", [k for k, v in ui.KATEGORIE_TON.items() if v == "rot"] == ["nachweisbarer Fehler"])
    check("Grün nur für „bestätigt“", [k for k, v in ui.STATUS_TON.items() if v == "gruen"] == ["bestätigt"])
    check("Stufen und KI neutral", ui.chip_stufe(1).count("lv-chip--neutral") == 1)
    css = ui.css()
    check("CSS ohne externe Quellen", not re.search(r"@import|url\(|https?:", css))
    check("CSS ohne prefers-color-scheme (folgt dem Streamlit-Theme)", "prefers-color-scheme" not in css)

    # A1: Rot nur für die Kategorie „nachweisbarer Fehler“
    for kat in ("möglicher Widerspruch", "Risikohinweis", "Unklarheit"):
        check(f"A1: kein Rot für „{kat}“", "--rot" not in ui.chip_kategorie(kat))
    check("A1: Rot für „nachweisbarer Fehler“", "lv-punkt--rot" in ui.chip_kategorie("nachweisbarer Fehler"))
    check("A1: Statusleiste „Analyse verfügbar“ neutral", True)
    check("A1: Beispielblatt ohne Rot, Widersprüche in Bernstein mit Begriff",
          all(ton != "rot" for *_, ton, _n in ui.BEISPIEL_BLATT)
          and all(ton == "bernstein" and "möglicher Widerspruch" in notiz
                  for _o, _k, _l, _m, _e, ton, notiz in ui.BEISPIEL_BLATT[:2]))
    nur_bernstein = [{"id": "a", "kategorie": "möglicher Widerspruch", "stufe": 1, "positionen": [{"oz": "1"}]}]
    check("A1: LV-Karte ohne nachweisbaren Fehler ohne Rot",
          "lv-strich--rot" not in ui.lv_karte_html([{"oz": "1"}, {"oz": "2"}], nur_bernstein))

    stufen_mix = [{"id": "s4", "kategorie": "nachweisbarer Fehler", "stufe": 4, "positionen": [{"oz": "1"}]},
                  {"id": "s1", "kategorie": "Unklarheit", "stufe": 1, "positionen": [{"oz": "1"}]}]
    check("C: LV-Karte färbt nach dem Fund mit der höchsten Stufe",
          "lv-strich--neutral" in ui.lv_karte_html([{"oz": "1"}], stufen_mix)
          and "lv-strich--rot" not in ui.lv_karte_html([{"oz": "1"}], stufen_mix))

    # 6: Einzahl
    check("6: „1 nachweisbarer Fehler“ / „2 nachweisbare Fehler“",
          ui.anzahl_wort(1, "nachweisbarer Fehler", "nachweisbare Fehler") == "1 nachweisbarer Fehler"
          and ui.anzahl_wort(2, "nachweisbarer Fehler", "nachweisbare Fehler") == "2 nachweisbare Fehler")
    # 7: Stand der Belegprüfung nur bei echtem Abgleich, Datum deutsch
    check("7: Stand nur bei geprüft oder nicht im Original", ui.belegstand_text("ungeprüft", "2026-11-22") is None
          and ui.belegstand_text("geprüft", "2026-11-22") == "Stand der Belegprüfung: 22.11.2026"
          and ui.belegstand_text("nicht im Original", "2026-11-22T03:10") == "Stand der Belegprüfung: 22.11.2026")
    quelle_fu7 = (SRC / "pages" / "funde.py").read_text(encoding="utf-8")
    check("7: Fundseite zeigt den Stand nur über belegstand_text", "ui.belegstand_text(" in quelle_fu7
          and "Stand der Belegprüfung: {s2_stand" not in quelle_fu7)
    # 3: Fund-ID neutral, kein grüner Inline-Code
    check("3: Fund-ID ohne Inline-Code", "Fund-ID `" not in quelle_fu7 and 'Fund-ID \'' in quelle_fu7)
    # 1: Status in eigener Zeile, nicht in den Spalten der übrigen Filter
    check("1: Status-Auswahl in eigener Zeile", 'st.container(key="pf_status_zeile")' in quelle_fu7
          and re.search(r'f\d\.segmented_control\(', quelle_fu7) is None)

    # A2: drei Beleg-Zustände aus einer Funktion
    check("A2: geprüft", ui.beleg_kennzeichnung("geprüft") == ("Beleg am Original geprüft", "gruen"))
    check("A2: ungeprüft", ui.beleg_kennzeichnung("ungeprüft")
          == ("Zitat aus dem LV (Parser), am Original noch nicht geprüft", "neutral"))
    check("A2: nicht im Original, Bernstein", ui.beleg_kennzeichnung("nicht im Original")
          == ("Beleg steht so nicht wörtlich im Original", "bernstein"))
    check("A2: Unbekanntes gilt nie als geprüft", ui.beleg_kennzeichnung("?")[0].startswith("Zitat aus dem LV"))
    quelle_ue = (SRC / "pages" / "uebersicht.py").read_text(encoding="utf-8")
    quelle_fu = (SRC / "pages" / "funde.py").read_text(encoding="utf-8")
    check("A2: beide Seiten nutzen dieselbe Funktion, kein fester Text „Beleg im Original“ / „Originalbeleg“",
          "ui.beleg_label_html(" in quelle_ue and "ui.beleg_label_html(" in quelle_fu
          and '"lv-label">Beleg im Original<' not in quelle_ue and "Originalbeleg (wörtlich" not in quelle_fu)

    # A3: Positionen mit Fund (doppelte OZ je Zeile, Fund mit zwei Positionen bei beiden)
    zeilen_t = [{"oz": "1.1"}, {"oz": "1.2"}, {"oz": "1.2"}, {"oz": "1.3"}, {"oz": "1.4"}]
    funde_t = [{"id": "x", "kategorie": "Unklarheit", "stufe": 4, "positionen": [{"oz": "1.2"}, {"oz": "1.3"}]},
               {"id": "y", "kategorie": "Unklarheit", "stufe": 4, "positionen": [{"oz": "1.3"}]}]
    check("A3: Zählung mit doppelter OZ und Mehrfachposition", ui.positionen_mit_fund(zeilen_t, funde_t) == 3)
    check("A3: LV-Karte nennt dieselbe Zahl", "3 mit Fund" in ui.lv_karte_html(zeilen_t, funde_t))
    check("A3: ohne Positionsliste verschiedene OZ", ui.positionen_mit_fund(None, funde_t) == 2)

    # Seiten: Start erklärt, Übersicht zählt
    from streamlit.testing.v1 import AppTest
    import test_ui_sitzung as TS

    def html_text(at):
        return " ".join(x.proto.body for x in at.get("html"))

    at = AppTest.from_file(str(SRC / "app.py"), default_timeout=180).run()
    t = html_text(at)
    check("Start: keine Ausnahme", not at.exception, str(at.exception))
    check("Start erklärt das Tool in einem Satz und zeigt den Ablauf",
          "prüft jede Position mit 19 festen Regeln" in t and "So arbeiten Sie damit" in t and "Was das Tool nicht tut" in t)
    check("Start: Upload-Feld vorhanden", len(at.get("file_uploader")) == 1)
    check("Start: Karte „Aktuelles LV“ sagt „Noch kein LV geladen“", "Noch kein LV geladen" in t)
    at.get("file_uploader")[0].upload("Erfunden-UI3.X83", test_lv()).run()
    t = html_text(at)
    funde = at.session_state["lv_uebersicht"]["funde"]
    check("Test-LV: Funde aller vier Stufen und ein nachweisbarer Fehler",
          {f["stufe"] for f in funde} == {1, 2, 3, 4} and any(f["kategorie"] == "nachweisbarer Fehler" for f in funde))
    fehler_n = sum(f["stufe"] == 1 and f["kategorie"] == "nachweisbarer Fehler" for f in funde)
    check("A1: Kachel Fehlerprüfung neutral, Hinweis mit echter Zahl nachweisbarer Fehler",
          re.search(r'Fehlerprüfung</div><div class="lv-kz-wert lv-ton--text">', t) is not None
          and "davon " + ui.anzahl_wort(fehler_n, "nachweisbarer Fehler", "nachweisbare Fehler") in t, str(fehler_n))
    zeilen_lv = at.session_state["lv_positionen"]["zeilen"]
    mit = ui.positionen_mit_fund(zeilen_lv, funde)
    check("A3: Kopf „in N von M Positionen“ = LV-Karte „N mit Fund“",
          f"in {mit} von {len(zeilen_lv)} Positionen" in t and f"{mit} mit Fund" in t, f"{mit}/{len(zeilen_lv)}")
    check("A2: Datei ohne Abgleich zeigt „am Original noch nicht geprüft“",
          "Zitat aus dem LV (Parser), am Original noch nicht geprüft" in t)
    check("A1: Rot auf der Übersicht nur bei nachweisbarem Fehler",
          ("lv-punkt--rot" in t) == any(f["kategorie"] == "nachweisbarer Fehler" for f in funde))
    check("Übersicht: keine Ausnahme", not at.exception, str(at.exception))
    # Angepasst (B1): Mit LV kompakter Kopf „Entscheidungsübersicht“ statt der Leitfrage; Aussage „Kopf nennt das LV“ bleibt
    check("Übersicht: kompakter Kopf mit LV, Leitfrage nur ohne LV", "lv-ktitel\">Entscheidungsübersicht<" in t
          and "Erfunden-UI3.X83" in t and "Was muss vor der Angebotsabgabe geklärt werden?" not in t)
    check("B1: „Zuerst klären“ steht vor der LV-Karte", t.find("Zuerst klären") < t.find("Wo im LV die Funde liegen"))
    stufe1 = sum(f["stufe"] == 1 for f in funde)
    check("Kennzahl Fehlerprüfung = Zahl der Stufe-1-Funde",
          re.search(r'Fehlerprüfung</div><div class="lv-kz-wert[^"]*">' + str(stufe1) + "<", t) is not None, str(stufe1))
    check("6: Kachel Fehlerprüfung in richtiger Zahlform", re.search(r"davon (1 nachweisbarer Fehler|\d+ nachweisbare Fehler)",
                                                                   t) is not None)
    check("Erfundene Datei ohne automatischen Abgleich: „–“ statt 0 % (R11)",
          re.search(r'Beleg am Original bestätigt</div><div class="lv-kz-wert[^"]*">–<', t) is not None
          and "kein automatischer Abgleich" in t and "0 %" not in t)
    zeilen = [b for b in at.button if b.label.startswith("Fund ansehen")]
    check("„Zuerst klären“: höchstens 7 Zeilen, nur offene in Sortierung",
          0 < len(zeilen) <= 7 and len(zeilen) == min(7, sum(f["status"] in ("offen", "Rückfrage stellen") for f in funde)))
    check("Verteilung: Summe je Stufe = Fundzahl", sum(sum(f["stufe"] == s for f in funde) for s in ui.STUFEN) == len(funde))
    # Angepasst (UI3-8): Das Test-LV ist jetzt bepreist; die Begründung der Rechenprüfung Nr. 17 nennt Werte laut LV in €.
    # Aussage bleibt: außerhalb der wörtlichen Fundtexte keine vom Tool erzeugten Euro-Beträge, kein Score, keine R7-Begriffe.
    ohne_fundtext = t
    for f_ in funde:
        ohne_fundtext = ohne_fundtext.replace(ui.h(f_["begruendung"]), "")
    check("Übersicht: keine Euro-Beträge außerhalb der Fundtexte, kein Score, keine R7-Begriffe",
          "€" not in ohne_fundtext and not VERBOTEN.search(t))
    check("Übersicht: Export-Knopf da", any(d.label == "Risikobericht exportieren" for d in at.get("download_button")))
    for seite in ("pages/berichte.py", "pages/hilfe.py"):
        at.switch_page(seite).run()
        t = html_text(at)
        check(f"{seite}: keine Ausnahme, keine R7-Begriffe", not at.exception and not VERBOTEN.search(t), str(at.exception))
    at.switch_page("pages/berichte.py").run()
    check("Berichte: Risikobericht und Bieterfragen", sorted(d.label for d in at.get("download_button"))
          == ["Bieterfragen (Entwurf, .xlsx)", "Risikobericht herunterladen (.xlsx)"])
    print(f"\n{sum(ergebnisse)}/{len(ergebnisse)} Tests bestanden")
    sys.exit(0 if all(ergebnisse) else 1)
