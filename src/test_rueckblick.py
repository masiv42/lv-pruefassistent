"""
test_rueckblick.py - Backlog B3: Rückblick-Test mit den Nachträgen aus [ORT_024] LV24069.D86 (Sitzung B2).

Frage: Hätte das Tool im Hauptauftrag dieses Auftrags-LV (OZ 1–7) vorab auf die Stelle hingewiesen, an der später ein
Nachtrag kam (Titel 8.1–8.6 „Nachtrag 1–6“)? Das ist eine **Messung**, keine Regel und kein Goldstandard für Regeln:
An diesem Ergebnis wird keine Prüfung eingestellt (E12 (3)); es zählt Treffer und Fehlschläge, nichts wird gefiltert.

Anlass je Nachtragsposition (fest, aus dem Kurztext der Nachtragsposition, nur für die Messung):
  „VAG“, „Fabrikat“, „Ausführung“ → Nr. 7 · „Bestand“ → Nr. 8 · „Entsorg“ → Nr. 9 · „Bauzeit“ → Nr. 10
  sonst „kein Anlass aus Nr. 7–10 erkennbar“ (nicht gezählt, aber aufgeführt)
Treffer: Im Hauptauftrag gibt es einen Fund dieser Prüfung an einer Position, deren Kurztext oder Beleg mit dem
Kurztext der Nachtragsposition mindestens ein Fachwort teilt (Wort ab 4 Zeichen ohne WORT_AUS). Sonst Fehlschlag.
Funde für den Hauptauftrag: pruefe_hinweise, pruefe_struktur, pruefe_vollstaendigkeit über die ganze Datei,
dann nur OZ 1–7.

Aufruf aus src/:  python test_rueckblick.py <data/raw> [--bericht ziel.json]
Exit-Code 0 = Messung lief und ist reproduzierbar (Doppellauf gleich); die Trefferquote ist kein Testkriterium.
"""
import json
import re
import sys
from pathlib import Path

from lv_parser import parse
from pruefung_widerspruch import normalisiere_leerzeichen
from pruefung_formal import pruefe_formal
from pruefung_hinweise import pruefe_hinweise
from pruefung_struktur import pruefe_struktur
from pruefung_vollstaendigkeit import pruefe_vollstaendigkeit

D = Path(sys.argv[1]) if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else Path("data/raw")
BERICHT = sys.argv[sys.argv.index("--bericht") + 1] if "--bericht" in sys.argv else None
DATEI = "[ORT_024] LV24069.D86"
ANLASS = [(re.compile(r"\bVAG\b|Fabrikat|Ausführung", re.I), 7), (re.compile(r"Bestand", re.I), 8),
          (re.compile(r"Entsorg", re.I), 9), (re.compile(r"Bauzeit", re.I), 10)]
WORT_AUS = {"zulage", "mehrkosten", "wegen", "verschobener", "bauzeit", "liefern", "montieren", "für", "ohne",
            "ausführung", "kosten"}
ergebnisse = []


def check(name, ok, detail=""):
    ergebnisse.append(ok)
    print(f"{'OK    ' if ok else 'FEHLER'} {name}" + (f" – {detail}" if detail and not ok else ""))


def fachwoerter(t):
    return {w for w in re.findall(r"[a-zäöüß0-9-]{4,}", normalisiere_leerzeichen(t).lower()) if w not in WORT_AUS}


def messung(df):
    f16 = pruefe_formal(df)
    funde = pruefe_hinweise(df, D / DATEI, f16) + pruefe_struktur(df, D / DATEI, f16) + \
        pruefe_vollstaendigkeit(df, D / DATEI)
    haupt = [f for f in funde if not re.match(r"^0*8\.", f["positionen"][0]["oz"])]
    kurz = {r.oz: r.kurztext or "" for r in df[df.typ == "Position"].itertuples()}
    zeilen = []
    for r in df[(df.typ == "Position") & df.oz.str.match(r"^0*8\.")].itertuples():
        k = normalisiere_leerzeichen(r.kurztext or "")
        nr = next((n for m, n in ANLASS if m.search(k)), None)
        z = {"oz": r.oz, "kurztext": k, "anlass": nr, "treffer": [], "ergebnis": "kein Anlass aus Nr. 7–10 erkennbar"}
        if nr:
            w = fachwoerter(k)
            for f in haupt:
                if f["pruefung"] != nr:
                    continue
                p = f["positionen"][0]
                gemeinsam = w & (fachwoerter(kurz.get(p["oz"], "")) | set().union(*map(fachwoerter, f["belege"])))
                if gemeinsam:
                    z["treffer"].append({"id": f["id"], "oz": p["oz"], "woerter": sorted(gemeinsam)})
            z["ergebnis"] = "Treffer" if z["treffer"] else "Fehlschlag"
            z["funde_nr_im_hauptauftrag"] = sum(f["pruefung"] == nr for f in haupt)
        zeilen.append(z)
    return zeilen


if __name__ == "__main__":
    df = parse(str(D / DATEI))
    a = messung(df)
    b = messung(parse(str(D / DATEI)))
    check("Doppellauf gleich (E14)", json.dumps(a, ensure_ascii=False) == json.dumps(b, ensure_ascii=False))
    check("38 Nachtragspositionen in 8.1–8.6 gemessen (7 + 1 + 19 + 1 + 2 + 8)", len(a) == 38, str(len(a)))
    mit = [z for z in a if z["anlass"]]
    tr = [z for z in mit if z["ergebnis"] == "Treffer"]
    print(f"       Nachtragspositionen mit Anlass aus Nr. 7–10: {len(mit)}; davon Treffer {len(tr)}, "
          f"Fehlschläge {len(mit) - len(tr)}; ohne erkennbaren Anlass: {len(a) - len(mit)}")
    for z in mit:
        print(f"       {z['oz']} Nr. {z['anlass']} {z['ergebnis']:<10} „{z['kurztext'][:55]}“ "
              f"(Funde Nr. {z['anlass']} im Hauptauftrag: {z['funde_nr_im_hauptauftrag']}) "
              + "; ".join(f"{t['oz']} {t['woerter']}" for t in z["treffer"][:3]))
    if BERICHT:
        ziel = Path(BERICHT).resolve()
        if ziel.is_relative_to(D.resolve()) or ziel.is_relative_to(Path("data").resolve()):
            sys.exit("--bericht nie in data/")
        ziel.write_text(json.dumps(a, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n{sum(ergebnisse)}/{len(ergebnisse)} Tests bestanden")
    sys.exit(0 if all(ergebnisse) else 1)
