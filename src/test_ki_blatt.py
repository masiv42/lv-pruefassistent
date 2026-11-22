"""
test_ki_blatt.py - Tests für das Blatt „KI-Vorschläge“ im Risikobericht (M2, L48). Ohne API-Aufruf, nur erfundene Texte
(E12 (3)); Cache und Log nur im Temp-Ordner.

Aufruf aus der Projektwurzel (uv-Befehl siehe AGENTS.md):
  python src/test_ki_blatt.py
Exit-Code 0 = alle Tests bestanden.
"""
import io
import json
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import pandas as pd
from openpyxl import load_workbook

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ki_b5 as K                                                     # noqa: E402
import ki_blatt as B                                                  # noqa: E402
from bericht import VERBOTEN, risikobericht                           # noqa: E402
from ki_client import KiAntwort                                       # noqa: E402
from ki_pruefung import KiKonfig                                      # noqa: E402
from lv_parser import COLUMNS, make_row                               # noqa: E402
from pruefung_formal import alle_pruefungen                           # noqa: E402

ergebnisse = []
ZEIT = datetime(2026, 11, 22, 1, 30).astimezone()


def check(name, ok, detail=""):
    ergebnisse.append(ok)
    print(f"{'OK    ' if ok else 'FEHLER'} {name}" + (f" – {detail}" if detail and not ok else ""))


class Ersatz:
    anbieter = "groq"

    def __init__(self, antworten):
        self.antworten, self.n = list(antworten), 0

    def anfrage(self, modell, system, text, einordnungen=None, warte_hinweis=None, schema=None):
        self.n += 1
        return KiAntwort(text=json.dumps(self.antworten.pop(0), ensure_ascii=False), stop_reason="end_turn", modell=modell,
                         usage={"input_tokens": 1, "output_tokens": 1, "cache_creation_input_tokens": 0,
                                "cache_read_input_tokens": 0}, dauer_s=0.0)


P1 = [{"oz": "1.1", "kurztext": "Bewehrrung liefern (erfunden)", "langtext": "Bewehrrung liefern (erfunden)", "menge": 1.0,
       "einheit": "t"}]
P2 = [{"oz": "1.2", "kurztext": "Schalung herstellen (erfunden)", "langtext": "Schalung herstellen (erfunden)", "menge": 2.0,
       "einheit": "m²"}]
P3 = [{"oz": "1.3", "kurztext": "Beton einbauen (erfunden)", "langtext": "Beton einbauen (erfunden)", "menge": 3.0,
       "einheit": "m³"}]
PAAR = [{"oz": "2.1", "kurztext": "Rohr DN 150 (erfunden)", "langtext": "Alle Rohre in PE-HD", "menge": 1.0, "einheit": "m"},
        {"oz": "2.2", "kurztext": "Rohr DN 150 PVC-U (erfunden)", "langtext": "PVC-U-Rohr DN 150", "menge": 5.0, "einheit": "m"}]
T = lambda b, z="", k="": {"befund": b, "zitat": z, "korrektur": k, "begruendung": "erfunden"}
W = {"einordnung": "echter Widerspruch", "oz_a": "2.1", "oz_b": "2.2", "zitat_a": "Alle Rohre in PE-HD",
     "zitat_b": "PVC-U-Rohr DN 150", "begruendung": "Werkstoff verschieden (erfunden)", "rueckfrage": "Welcher Werkstoff gilt?"}


def lv_info(gruppen_t, gruppen_w):
    return {"format": "GAEB XML", "positionen": 1, "nur_preise": False, "hinweise": [], "fingerprint": "test",
            "b5": {"tippfehler": gruppen_t, "widerspruch": gruppen_w}}


def blatt_text(wb):
    return "\n".join(str(c.value) for r in wb[B.BLATT].iter_rows() for c in r if c.value is not None)


def main():
    konfig = KiKonfig("test-modell", "geheim", "groq")
    df = pd.DataFrame([make_row(datei="x.X83", format="GAEB XML", typ="Position", oz="9.1", kurztext="Baustelle einrichten",
                                langtext="Baustelle einrichten", menge=1.0, einheit="psch", einheit_roh="psch", art="Pauschal")],
                      columns=COLUMNS)
    funde = alle_pruefungen(df, None)
    texte = {f["id"]: [{"oz": "9.1", "kurztext": "Baustelle einrichten", "langtext": "Baustelle einrichten", "menge": 1.0,
                        "einheit": "psch", "ep": None, "gp": None}] for f in funde}
    with tempfile.TemporaryDirectory() as tmp:
        cache, log = Path(tmp) / "c", Path(tmp) / "log.jsonl"
        cache.mkdir()
        c = Ersatz([T("Tippfehler", "Bewehrrung", "Bewehrung"), T("kein Tippfehler"), T("Tippfehler", "Bewährung", "x")])
        K.pruefe("tippfehler", [P1, P2, P3], konfig, client=c, cache_dir=cache, log_datei=log)
        K.pruefe("widerspruch", [PAAR], konfig, client=Ersatz([W]), cache_dir=cache, log_datei=log)
        info = lv_info([P1, P2, P3], [PAAR])
        bericht = lambda i: load_workbook(io.BytesIO(risikobericht("x.X83", funde, texte, i, s2={}, zeitpunkt=ZEIT, commit="test",
                                                                  ki_konfig=konfig, ki_cache_dir=cache)))
        wb = bericht(info)
        check("Blatt „KI-Vorschläge“ steht neben den Regel-Funden", B.BLATT in wb.sheetnames and "Funde" in wb.sheetnames,
              str(wb.sheetnames))
        t = blatt_text(wb)
        check("Warnhinweis nach E13 oben im Blatt", wb[B.BLATT]["A2"].value == B.WARNHINWEIS and "entwarnt nie" in B.WARNHINWEIS)
        check("Quelle (Cache), Modell und Prompt-Versionen B5-T1/B5-W1", all(x in t for x in ("Cache", "test-modell", "B5-T1", "B5-W1")))
        check("Gültiger Tippfehler steht im Blatt, als KI-Vorschlag", "„Bewehrrung“" in t and "KI-Vorschlag: vermutlich „Bewehrung“" in t)
        check("Widerspruch mit beiden wörtlichen Zitaten und Rückfrage-Entwurf",
              "Alle Rohre in PE-HD" in t and "PVC-U-Rohr DN 150" in t and "Welcher Werkstoff gilt?" in t)
        check("Entwarnung („kein Tippfehler“) erzeugt keine Zeile (E13)", "Schalung" not in t, t[:80])
        check("Cache-Zitat, das nicht im aktuellen Text steht, kommt nicht ins Blatt (R5)", "Bewährung" not in t)
        check("Stand je KI-Prüfung gezählt", "Tippfehler: 3 von 3 geprüft, 1 KI-Vorschläge" in t
              and "Widerspruch zwischen Positionen: 1 von 1 geprüft, 1 KI-Vorschläge" in t, t[:300])
        check("Keine R7-Begriffe im Blatt", not VERBOTEN.search(t))
        ohne = bericht(lv_info([], []))
        zeilen = lambda w: [[c.value for c in r] for r in w["Funde"].iter_rows()]
        check("E13: Blatt „Funde“ mit und ohne KI-Vorschläge identisch", zeilen(wb) == zeilen(ohne) and len(zeilen(wb)) == 2)
        check("Ohne Vorschläge steht das klar im Blatt", B.KEINE in blatt_text(ohne))
        a, b = blatt_text(wb), blatt_text(bericht(info))
        check("E14: zweiter Export liefert dasselbe Blatt", a == b)
        wb2 = load_workbook(io.BytesIO(risikobericht("x.X83", funde, texte, info, s2={}, zeitpunkt=ZEIT, commit="test",
                                                     ki_konfig=KiKonfig(None, None, "groq"), ki_cache_dir=cache)))
        check("KI aus: Blatt nennt das, kein Vorschlag, kein Absturz",
              "KI aus" in blatt_text(wb2) and "Bewehrrung" not in blatt_text(wb2), blatt_text(wb2)[:120])
        n = sum(1 for _ in cache.iterdir())
        bericht(lv_info([P1, P2, P3, [dict(P3[0], oz="1.4", kurztext="neu")]], [PAAR]))
        check("Export macht keinen API-Aufruf und schreibt keinen Cache", sum(1 for _ in cache.iterdir()) == n and c.n == 3)
        for name, feld, wert in (("Link", "begruendung", "Siehe https://beispiel.invalid/angebot"),
                                 ("E-Mail", "begruendung", "Bitte an kontakt@beispiel.invalid melden"),
                                 ("Markdown-Verweis", "korrektur", "[Bewehrung](http://beispiel.invalid)"),
                                 ("Zeilenumbruch", "begruendung", "erste Zeile\nzweite Zeile"),
                                 ("Überlänge", "begruendung", "x" * (B.MAX_FREITEXT + 1))):
            a = dict(T("Tippfehler", "Bewehrrung", "Bewehrung"), **{feld: wert})
            check(f"L59: KI-Text mit {name} wird nicht übernommen",
                  not B.unbedenklich({"antwort": a}) and B.unbedenklich({"antwort": T("Tippfehler", "Bewehrrung", "Bewehrung")}))
        P5 = [{"oz": "1.5", "kurztext": "Dämung einbauen (erfunden)", "langtext": "Dämung einbauen (erfunden)", "menge": 1.0,
               "einheit": "m²"}]
        bad = dict(T("Tippfehler", "Dämung", "Dämmung"), begruendung="Siehe https://beispiel.invalid/angebot")
        K.pruefe("tippfehler", [P5], konfig, client=Ersatz([bad]), cache_dir=cache, log_datei=log)
        t5 = blatt_text(bericht(lv_info([P1, P5], [])))
        check("L59: auffälliger Vorschlag fehlt im Blatt und wird gezählt, nichts fällt still weg",
              "beispiel.invalid" not in t5 and "Dämung" not in t5 and "1 wegen auffälligem KI-Text nicht übernommen" in t5, t5[:360])
        info_preise = dict(info, nur_preise=True)
        w3 = load_workbook(io.BytesIO(risikobericht("x.D84", [], {}, info_preise, s2={}, zeitpunkt=ZEIT, commit="test",
                                                    ki_konfig=konfig, ki_cache_dir=cache)))
        check("Reine Preisdatei ohne Funde: kein KI-Blatt", B.BLATT not in w3.sheetnames, str(w3.sheetnames))
    print(f"\n{sum(ergebnisse)}/{len(ergebnisse)} Tests bestanden")
    return 0 if all(ergebnisse) else 1


if __name__ == "__main__":
    sys.exit(main())
