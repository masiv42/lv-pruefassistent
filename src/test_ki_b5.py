"""
test_ki_b5.py - Tests für src/ki_b5.py (Block B5) ohne API-Aufruf (Ersatz-Client), nur erfundene Texte (E12 (3)).

Aufruf aus der Projektwurzel (uv-Befehl siehe AGENTS.md):
  python src/test_ki_b5.py
Exit-Code 0 = alle Tests bestanden. Cache und Log nur im Temp-Ordner.
"""
import json
import sys
import tempfile
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ki_b5 as K                                                     # noqa: E402
from ki_client import KiAntwort                                       # noqa: E402
from ki_pruefung import KiKonfig, STATUS_GUELTIG, STATUS_ZITAT, STATUS_R7, STATUS_UNLESBAR   # noqa: E402
from lv_parser import COLUMNS                                         # noqa: E402

ergebnisse = []


def check(name, ok, detail=""):
    ergebnisse.append(ok)
    print(f"{'OK    ' if ok else 'FEHLER'} {name}" + (f" – {detail}" if detail and not ok else ""))


class Ersatz:
    """Ersatz-Client: gibt vorbereitete Antworten zurück und zählt Aufrufe."""
    anbieter = "groq"

    def __init__(self, antworten):
        self.antworten, self.n, self.schemas = list(antworten), 0, []

    def anfrage(self, modell, system, text, einordnungen=None, warte_hinweis=None, schema=None):
        self.n += 1
        self.schemas.append(schema)
        return KiAntwort(text=json.dumps(self.antworten.pop(0), ensure_ascii=False), stop_reason="end_turn",
                         modell=modell, usage={"input_tokens": 10, "output_tokens": 5,
                                               "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0},
                         dauer_s=0.0)


P = [{"oz": "1.1", "kurztext": "Bewehrrung liefern (erfunden)", "langtext": "Bewehrrung liefern (erfunden)",
      "menge": 1.0, "einheit": "t"}]
PL = [{"oz": "1.2", "kurztext": "Wartung durch [PERSON_115]", "langtext": "Wartung durch [PERSON_115]", "menge": 1.0,
       "einheit": "psch"}]
PAAR = [{"oz": "2.1", "kurztext": "Rohr DN 150 (erfunden)", "langtext": "Alle Rohre in PE-HD", "menge": 1.0, "einheit": "m"},
        {"oz": "2.2", "kurztext": "Rohr DN 150 PVC-U (erfunden)", "langtext": "PVC-U-Rohr DN 150", "menge": 5.0, "einheit": "m"}]
T = lambda b, z="", k="": {"befund": b, "zitat": z, "korrektur": k, "begruendung": "erfunden"}


def main():
    konfig = KiKonfig("test-modell", "geheim", "groq")
    check("Prompts eingefroren (SHA-256), Versionen B5-T1/B5-W1",
          K.prompt_eingefroren("tippfehler") and K.prompt_eingefroren("widerspruch") and K.VERSION == {"tippfehler": "B5-T1", "widerspruch": "B5-W1"})
    # bewerte
    check("Tippfehler mit wörtlichem Zitat -> gültig", K.bewerte("tippfehler", json.dumps(T("Tippfehler", "Bewehrrung", "Bewehrung")), P)[0] == STATUS_GUELTIG)
    check("Zitat nicht im Text -> verworfen (R5)", K.bewerte("tippfehler", json.dumps(T("Tippfehler", "Bewährung")), P)[0] == STATUS_ZITAT)
    check("Platzhalter als Tippfehler -> verworfen (R9)", K.bewerte("tippfehler", json.dumps(T("Tippfehler", "[PERSON_115]")), PL)[0] == K.STATUS_R9)
    check("R7-Begriff in der Antwort -> verworfen", K.bewerte("tippfehler", json.dumps(dict(T("kein Tippfehler"), begruendung="Anspruch")), P)[0] == STATUS_R7)
    check("unbekannter Befund -> unlesbar", K.bewerte("tippfehler", json.dumps(T("vielleicht")), P)[0] == STATUS_UNLESBAR)
    w = {"einordnung": "echter Widerspruch", "oz_a": "2.1", "oz_b": "2.2", "zitat_a": "Alle Rohre in PE-HD",
         "zitat_b": "PVC-U-Rohr DN 150", "begruendung": "erfunden", "rueckfrage": "Welches Material?"}
    check("Widerspruch: Zitate je in ihrer Position -> gültig", K.bewerte("widerspruch", json.dumps(w), PAAR)[0] == STATUS_GUELTIG)
    check("Widerspruch: Zitat in der falschen Position -> verworfen",
          K.bewerte("widerspruch", json.dumps(dict(w, oz_a="2.2", oz_b="2.1")), PAAR)[0] == STATUS_ZITAT)
    # pruefe: Cache, Obergrenze, E13
    with tempfile.TemporaryDirectory() as d:
        c, log = Path(d) / "c", Path(d) / "log.jsonl"
        e = Ersatz([T("Tippfehler", "Bewehrrung", "Bewehrung"), T("kein Tippfehler")])
        erg, st = K.pruefe("tippfehler", [P, PL], konfig, e, cache_dir=c, log_datei=log)
        check("pruefe: 2 Aufrufe mit Schema der Prüfung", e.n == 2 and e.schemas[0] == K.SCHEMA["tippfehler"], str(st))
        v = K.vorschlaege("tippfehler", erg)
        check("Vorschläge: nur der Tippfehler (E13: „kein Tippfehler“ erzeugt nichts), Kategorie/Stufe als Vorschlag",
              len(v) == 1 and v[0]["positionen"] == ["1.1"] and v[0]["stufe_vorschlag"] == 4)
        e2 = Ersatz([])
        erg2, st2 = K.pruefe("tippfehler", [P, PL], konfig, e2, cache_dir=c, log_datei=log)
        check("zweiter Lauf: 0 Aufrufe, alles aus dem Cache, gleiches Ergebnis (E14)",
              e2.n == 0 and st2["cache_treffer"] == 2 and [x["status"] for x in erg2] == [x["status"] for x in erg])
        e3 = Ersatz([T("kein Tippfehler")] * 5)
        gr = [[dict(P[0], oz=f"9.{i}", kurztext=f"Text {i} (erfunden)", langtext=f"Text {i}")] for i in range(5)]
        erg3, st3 = K.pruefe("tippfehler", gr, konfig, e3, max_aufrufe=2, cache_dir=c, log_datei=log)
        check("Obergrenze: höchstens 2 Aufrufe, Rest „noch nicht geprüft“ mit Hinweis",
              e3.n == 2 and st3["nicht_geprueft"] == 3 and "nächste Klick" in st3["meldung"], str(st3))
    erg4, st4 = K.pruefe("tippfehler", [P], KiKonfig(None, None, "groq"), Ersatz([]))
    check("ohne Key: kein Aufruf, Meldung „KI aus“", not erg4 and "KI aus" in st4["meldung"])
    # Vorauswahl der Paare
    def z(oz, kurz, lang):
        r = {c: None for c in COLUMNS}
        r.update(datei="x.X83", format="GAEB XML", typ="Position", oz=oz, kurztext=kurz, langtext=lang, menge=1.0, einheit="m")
        return r
    df = pd.DataFrame([z("3.1", "Rohr DN 150 liefern", "Rohr DN 150"), z("3.2", "Rohr DN 200 verlegen", "Rohr DN 200"),
                       z("3.3", "Schacht DN 1000", "Schacht"), z("4.1", "Rohr DN 300", "Rohr DN 300")], columns=COLUMNS)
    pa = K.paare(df)
    check("Paare: gleicher Abschnitt, gemeinsames Bauteilwort, verschiedene DN -> nur (3.1, 3.2)",
          [[p["oz"] for p in x] for x in pa] == [["3.1", "3.2"]], str([[p["oz"] for p in x] for x in pa]))
    check("Paare: feste Reihenfolge (E14)", K.paare(df) == pa)
    # Messung mit Ersatz-Client: immer „kein Tippfehler“/„unklar“ -> positive Fälle falsch, negative richtig
    import b5_testfaelle as BT
    n_t, n_w = len(BT.TIPPFEHLER), len(BT.WIDERSPRUCH)
    with tempfile.TemporaryDirectory() as d:
        e5 = Ersatz([T("kein Tippfehler")] * n_t + [{"einordnung": "unklar", "oz_a": "", "oz_b": "", "zitat_a": "",
                     "zitat_b": "", "begruendung": "erfunden", "rueckfrage": "Bitte klären?"}] * n_w)
        doc = K.messung(konfig, e5, ablage={"cache_dir": Path(d) / "c", "log_datei": Path(d) / "l.jsonl"})
        zs = doc["zusammenfassung"]
        check(f"Messung: {n_t + n_w} Fälle je ein Aufruf, Zuordnung Fall -> Antwort, positiv/negativ getrennt",
              e5.n == n_t + n_w and len(doc["faelle"]) == n_t + n_w and zs["tippfehler positiv"]["richtig"] == 0
              and zs["tippfehler negativ"]["richtig"] == zs["tippfehler negativ"]["faelle"], str(zs))
    print(f"\n{sum(ergebnisse)}/{len(ergebnisse)} Tests bestanden")
    return 0 if all(ergebnisse) else 1


if __name__ == "__main__":
    sys.exit(main())
