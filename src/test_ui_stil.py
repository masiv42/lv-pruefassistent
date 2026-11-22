"""
test_ui_stil.py - Tests für src/ui_stil.py (Sitzung UI). Nur AppTest im Prozess, kein Port, schreibt nichts.
Aufruf aus src/ (mit --with streamlit==1.67.0 …):  python test_ui_stil.py
"""
import os
import re
import sys
from pathlib import Path

from streamlit.testing.v1 import AppTest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ui_stil  # noqa: E402

ergebnisse = []


def check(name, ok, detail=""):
    ergebnisse.append(bool(ok))
    print(f"{'OK    ' if ok else 'FEHLER'} {name}" + (f" – {detail}" if detail and not ok else ""))


def fund(nr, stufe, kategorie, status="offen"):
    return {"id": f"{nr}|d.X83|1.{nr}", "pruefung": nr, "kategorie": kategorie, "titel": "T", "stufe": stufe,
            "positionen": [{"datei": "d.X83", "oz": f"1.{nr}", "seite": None}], "belege": ["b"], "status": status}


EINTRAG = {"lv_name": "/Users/jemand/geheim/[ORT_024] LV.D86", "format": "GAEB 90", "positionen": 1248,
           "funde": [fund(1, 1, "möglicher Widerspruch"), fund(6, 2, "Risikohinweis"), fund(12, 4, "Unklarheit")],
           "abdeckung": [{"pruefung": 1, "name": "N", "pruefbar": 3, "gesamt": 4, "gruende": []},
                         {"pruefung": 3, "name": "M", "pruefbar": 4, "gesamt": 4, "gruende": []},
                         {"pruefung": 17, "name": "R", "pruefbar": 4, "gesamt": 4, "gruende": [],
                          "text": "Rechenprüfung: 248 Positionen nachgerechnet, 0 Abweichungen"}]}


def seite():
    import os as _os
    import sys as _sys
    _sys.path.insert(0, _os.environ["LV_TEST_SRC"])
    import ui_stil as u
    u.stil_einbinden()
    u.kopf("Testseite", "[ORT_024] LV.D86 · GAEB 90", [u.abzeichen_stufe(1), u.abzeichen_kategorie("Unklarheit")])
    u.kacheln([u.Kachel("Positionen", "12", "laut Parser")])
    u.beleg("Beton *C30/37* <b>$x$</b>")


def lauf(ohne_css):
    os.environ["LV_TEST_SRC"] = str(Path(__file__).resolve().parent)
    if ohne_css:
        os.environ[ui_stil.OHNE_CSS] = "1"
    else:
        os.environ.pop(ui_stil.OHNE_CSS, None)
    try:
        return AppTest.from_function(seite).run(timeout=30)
    finally:
        os.environ.pop(ui_stil.OHNE_CSS, None)


if __name__ == "__main__":
    # R6: Farbe nach Kategorie
    check("Rot nur für nachweisbaren Fehler",
          [k for k, f in ui_stil.KATEGORIE_FARBE.items() if f == "red"] == ["nachweisbarer Fehler"])
    check("Widerspruch und Risikohinweis in Bernstein", ui_stil.KATEGORIE_FARBE["möglicher Widerspruch"] == "orange"
          and ui_stil.KATEGORIE_FARBE["Risikohinweis"] == "orange")
    check("Unklarheit neutral", ui_stil.KATEGORIE_FARBE["Unklarheit"] == "gray")
    gruen = [s for s, f in ui_stil.STATUS_FARBE.items() if f == "green"]
    check("Grün nur für „bestätigt“ und „Beleg geprüft“", gruen == ["bestätigt"]
          and [b for b, (f, _) in ui_stil.BELEG_ABZEICHEN.items() if f == "green"] == ["geprüft"])
    check("Stufen neutral, mit Namen", all(ui_stil.abzeichen_stufe(s).startswith(":gray-badge[") for s in (1, 2, 3, 4))
          and "3 – mögliches Nachtragspotenzial" in ui_stil.abzeichen_stufe(3))
    check("KI-Vorschlag neutral, nie grün (E13)", ui_stil.abzeichen_ki() == ":gray-badge[KI-Vorschlag]")
    check("„Beleg nicht im Original“ in Bernstein, nicht Rot", ui_stil.BELEG_ABZEICHEN["nicht im Original"][0] == "orange")

    # Kennzahlen: nur Zählungen und Angaben aus der Prüfung
    k = {x.bezeichnung: x for x in ui_stil.kacheln_lv(EINTRAG)}
    check("Acht Kacheln", len(k) == 8)
    check("Tausenderpunkt", k["Positionen"].wert == "1.248")
    check("Stufen-Summe = Fundzahl", sum(int(k[ui_stil.stufe_name(s)].wert) for s in (1, 2, 3, 4)) == len(EINTRAG["funde"]))
    check("Stufe ohne Fund bleibt sichtbar", k["3 – mögliches Nachtragspotenzial"].wert == "0")
    check("Prüfabdeckung gezählt, Nr. 17 ausgenommen", k["Prüfabdeckung"].wert == "1 von 2")
    check("Rechenprüfung aus dem Text der Prüfung", k["Rechenprüfung"].wert == "0 Abweichungen"
          and k["Rechenprüfung"].hinweis == "248 Positionen nachgerechnet")
    leer = {x.bezeichnung: x for x in ui_stil.kacheln_lv({**EINTRAG, "abdeckung": [], "funde": []})}
    check("Ohne Abdeckung „–“ statt erfundener Zahl", leer["Prüfabdeckung"].wert == "–" and leer["Rechenprüfung"].wert == "–")
    ohne_rechnung = {**EINTRAG, "abdeckung": [{"pruefung": 17, "name": "R", "pruefbar": 0, "gesamt": 4, "gruende": [],
                                               "text": "Rechenprüfung: 0 Positionen nachgerechnet, 0 Abweichungen"}]}
    r = {x.bezeichnung: x for x in ui_stil.kacheln_lv(ohne_rechnung)}["Rechenprüfung"]
    check("Nichts nachgerechnet: keine Entwarnung „0 Abweichungen“", r.wert == "–" and "Menge, EP und GP" in r.hinweis)
    check("Prüfabdeckung-Hinweis fasst gleiche Texte zusammen",
          ui_stil.abdeckung_hinweis([{"pruefung": n, "name": "N", "pruefbar": 3, "gesamt": 4, "gruende": []}
                                     for n in (1, 2)]).count("prüfbar in 3 von 4") == 1)
    alle = " ".join(f"{x.bezeichnung} {x.wert} {x.hinweis}" for x in k.values())
    check("Keine Euro-Beträge, kein Score", "€" not in alle and not re.search(r"score|confidence|konfidenz", alle, re.I))
    check("Kontext ohne Pfad", ui_stil.kontext_lv(EINTRAG) == "[ORT_024] LV.D86 · GAEB 90 · 1.248 Positionen")

    # Text bleibt wörtlich und ist sicher eingebunden
    check("HTML wird maskiert", "<script" not in ui_stil.beleg_html("<script>x</script>")
          and "&lt;script&gt;" in ui_stil.beleg_html("<script>x</script>"))
    check("Kachel maskiert HTML", "<img" not in ui_stil.kacheln_html([ui_stil.Kachel("<img src=x>", "1")]))
    check("Markdown maskiert", ui_stil.md_text("[ORT_024]*a*") == r"\[ORT\_024\]\*a\*")

    # CSS: eine Stelle, keine Fremdquellen, keine verbotenen Muster
    css = ui_stil.css()
    check("CSS ohne externe Quellen", not re.search(r"@import|url\(|https?:", css))
    check("CSS folgt dem Streamlit-Theme statt der Systemeinstellung", "prefers-color-scheme" not in css)
    check("Keine Verläufe, Glaseffekte, Animationen", not re.search(r"gradient|backdrop-filter|@keyframes|animation", css))
    check("Keine farbigen Seitenstreifen", not re.search(r"border-(left|right)\s*:", css))
    check("Ohne Theme-Abschnitte: Systemfarben statt Fehler", ui_stil._farbe({}, "textColor") == "CanvasText")
    quelle = Path(ui_stil.__file__).read_text(encoding="utf-8")
    check("Keine verbotenen Begriffe (R7, R11)",
          not re.search(r"Risk Score|AI confidence|Anspruch|berechtigt|durchsetzbar|§", quelle))

    # App bleibt mit und ohne CSS vollständig
    for ohne, name in ((False, "mit CSS"), (True, "ohne CSS")):
        at = lauf(ohne)
        html = " ".join(x.proto.body for x in at.get("html"))
        check(f"{name}: keine Ausnahme", not at.exception, str(at.exception))
        check(f"{name}: Titel, Kontext und Abzeichen", at.title[0].value == "Testseite"
              and "ORT" in at.caption[0].value and any("1 – Fehlerprüfung" in m.value for m in at.markdown))
        check(f"{name}: Kacheln und Beleg", "Positionen" in html and "Beton *C30/37*" in html and "&lt;b&gt;" in html)
        hat_stil = any("<style>" in m.value for m in at.markdown)
        check(f"{name}: CSS {'eingebunden' if not ohne else 'weggelassen'}", hat_stil is (not ohne))

    print(f"\n{sum(ergebnisse)}/{len(ergebnisse)} Tests bestanden")
    sys.exit(0 if all(ergebnisse) else 1)
