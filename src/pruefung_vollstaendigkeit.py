"""
pruefung_vollstaendigkeit.py - Block B3: mögliche fehlende Leistung (höchstens 5 Paarregeln auf LV-Ebene).

Scope D (Team, 21.11.2026): Risikohinweis, kein Fehler; höchstens 5 Paarregeln; Hinweistext „prüfen, ob in anderem
Gewerk/LV enthalten“. Beleg = Text der auslösenden Position (R5). Gebaut in Sitzung B2 (Team, 18:50); Einbindung
in alle_pruefungen(), App und Export durch Sitzung B1. Prüfungs-Nr. 19, Stufe 3, Rang 5: bestätigt (B2-F11, 19:55).

Regel: Gibt es im LV eine Auslöser-Position, aber keine Position, deren **Kurztext** das Gegenstück ist, entsteht
ein Fund an der ersten Auslöser-Position (in Reihenfolge des LV). Das Gegenstück wird im Kurztext gesucht, damit
ein Satz wie „Schalung und Bewehrung in gesonderter Position“ im Langtext des Auslösers nicht als vorhandene Schalung
zählt. Ausnahme Regel 4: Aushub-Positionen enthalten Abfuhr oder Lagerung oft selbst („seitlich lagern“, „laden,
abfahren“), dort zählt der ganze Positionstext aller Positionen. Ein Fund je Regel und LV; trifft die erste
Auslöser-Position mehrerer Regeln dieselbe OZ, steht ein Fund mit allen Regeln.

  R1 Ortbeton → Schalung        Auslöser: Betonfestigkeitsklasse (C x/y) und „Ortbeton“, „Stahlbeton“ oder „bewehrt“
                                 im Text, Kurztext ohne Fertigteil, Rohr, Abbruch, Regie
                                 Gegenstück (Kurztext): Schalung, schalen; nicht „o. Schalung“, „ohne Schalung“
  R2 Stahlbeton → Bewehrung     Auslöser wie R1, aber „Stahlbeton“ oder „bewehrt“
                                 Gegenstück (Kurztext): Bewehrung, Betonstahl, Betonstahlmatte, B500, Baustahl
  R3 Rohr verlegen → Graben     Auslöser (Kurztext): Kanal-, Druck-, Muffendruck-, Steinzeug-, KG-, PE-HD-, Guss-,
                                 GGG-Rohr, Grundleitung, Wasserleitung, Abwasserleitung, jeweils mit „verlegen“
                                 oder „einbauen“ im Text
                                 Gegenstück (Kurztext): Rohrgraben, Graben, Aushub, ausheben, Baugrube, Boden lösen
  R4 Aushub → Verfüllen/Abfuhr  Auslöser (Kurztext): Aushub, ausheben, Boden lösen, Baugrube, Rohrgraben
                                 Gegenstück (ganzer Text): verfüllen, Abfuhr, abfahren, Abtransport, entsorgen,
                                 seitlich lagern, Verwertung, wiedereinbauen
  R5 Asphalt aufbrechen → wiederherstellen
                                 Auslöser: Asphalt mit aufbrechen, aufnehmen, abbrechen, fräsen, ausbauen
                                 Gegenstück (Kurztext): Asphalttrag-/-deck-/-binderschicht, Asphaltbeton,
                                 Asphalt … herstellen/einbauen, Tragdeckschicht; nicht, wenn der Kurztext Rückbau
                                 nennt (entsorgen, Abbruch, fräsen, aufnehmen, aufbrechen, ausbauen), z. B. LV_00
                                 2.1.50 „Teilentsorgung PAK-haltige Asphaltdecke“

Aufruf (aus der Projektwurzel, uv-Befehl siehe AGENTS.md):
  python src/pruefung_vollstaendigkeit.py <datei> [<datei> ...] [--out funde.json]
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

from lv_parser import parse
from pruefung_widerspruch import normalisiere_oz, normalisiere_leerzeichen, PdfSeiten, eigener_langtext, PRIORITAET_IN_STUFE
from pruefung_formal import nur_preise, sortiere
from pruefung_hinweise import Gaeb90Bloecke, _txt, _seite
from pruefung_struktur import _beleg_ausschnitt, _passt_fuer

NR = 19
KATEGORIE = "Risikohinweis"
STUFE = 3                                        # Team 21.11.2026, 19:55 (B2-F11)
RANG_VORSCHLAG = {(NR, 3): 5}                    # Rangtabelle Team 21:20: nach Nr. 9, 10, 7, 8
EMPFEHLUNG = "vormerken"
HINWEIS = "prüfen, ob in anderem Gewerk/LV enthalten"
TITEL = "Mögliche fehlende Leistung"
KOSTENWIRKUNG = ("direkt möglich: Fehlt die Leistung auch in anderen Gewerken, wird sie in der Ausführung "
                 "zusätzlich nötig; Höhe nicht bezifferbar.")

KLASSE = r"\bC\s?\d{1,3}\s?/\s?\d{2,3}\b"
OHNE_R12 = re.compile(r"fertigteil|rohr|abbruch|abbrech|abtragen|regie|stundenlohn|kernbohr|bohren", re.I)

REGELN = [
    {"id": "R1", "name": "Ortbeton → Schalung", "fehlt": "Schalung",
     "ausloeser": lambda k, x: re.search(KLASSE, x) and re.search(r"\bOrtbeton|\bStahlbeton(?!fertig)|\bbewehrt", x, re.I)
     and not OHNE_R12.search(k),
     "wort": re.compile(r"\bOrtbeton\w*|\bStahlbeton\w*|\bbewehrt\w*|" + KLASSE, re.I),
     "gegen": re.compile(r"\bSchalung\w*|\bschalen\b|\beinschalen", re.I), "gegen_im": "kurz",
     "gegen_ohne": re.compile(r"\bo\.\s?Schal|\bohne\s+Schal", re.I)},
    {"id": "R2", "name": "Stahlbeton → Bewehrung", "fehlt": "Bewehrung",
     "ausloeser": lambda k, x: re.search(KLASSE, x) and re.search(r"\bStahlbeton(?!fertig)|\bbewehrt", x, re.I)
     and not OHNE_R12.search(k),
     "wort": re.compile(r"\bStahlbeton\w*|\bbewehrt\w*", re.I),
     "gegen": re.compile(r"\bBewehrung\w*|\bBetonstahl\w*|\bB\s?500|\bBaustahl\w*", re.I), "gegen_im": "kurz"},
    {"id": "R3", "name": "Rohr verlegen → Rohrgraben/Aushub", "fehlt": "Rohrgraben bzw. Aushub",
     "ausloeser": lambda k, x: re.search(r"\b(?:Kanalrohr|Druckrohr|Muffendruckrohr|Steinzeugrohr|KG-Rohr|PE-HD-Rohr"
                                         r"|Gussrohr|GGG-Rohr|Grundleitung|Wasserleitung|Abwasserleitung)\w*", k, re.I)
     and re.search(r"\b(?:verlegen|einbauen)\b", x, re.I),
     "wort": re.compile(r"\b(?:Kanalrohr|Druckrohr|Muffendruckrohr|Steinzeugrohr|KG-Rohr|PE-HD-Rohr|Gussrohr|GGG-Rohr"
                        r"|Grundleitung|Wasserleitung|Abwasserleitung)\w*", re.I),
     "gegen": re.compile(r"\bRohrgraben\w*|\bGraben\w*|\bAushub\w*|\bausheben\b|\bBaugrube\w*|\bBoden\w*\s+lösen", re.I),
     "gegen_im": "kurz"},
    {"id": "R4", "name": "Aushub → Verfüllen/Abfuhr", "fehlt": "Verfüllen bzw. Abfuhr",
     "ausloeser": lambda k, x: re.search(r"\bAushub\w*|\bausheben\b|\bBoden\w*\s+lösen|\bBaugrube\w*|\bRohrgraben\w*",
                                         k, re.I) and not re.search(r"^\s*(?:zulage|zul\.)", k, re.I),
     "wort": re.compile(r"\bAushub\w*|\bausheben\b|\bBoden\w*\s+lösen|\bBaugrube\w*|\bRohrgraben\w*", re.I),
     "gegen": re.compile(r"\bverfüll\w*|\bWiederverfüll\w*|\bAbfuhr\b|\babfahren\b|\bAbtransport\w*|\bentsorg\w*"
                         r"|\bseitlich\s+(?:zwischen)?lager\w*|\bVerwertung|\bwieder\s?einbau\w*", re.I),
     "gegen_im": "text"},
    {"id": "R5", "name": "Asphalt aufbrechen → Asphalt wiederherstellen", "fehlt": "Asphalt herstellen",
     "ausloeser": lambda k, x: re.search(r"\bAsphalt\w*\b[^.;]{0,40}?\b(?:aufbrechen|aufnehmen|abbrechen|fräsen|ausbauen)\b"
                                         r"|\b(?:Fräsen|Aufbrechen|Abbruch|Aufnehmen)\b[^.;]{0,20}?\bAsphalt", x, re.I),
     "wort": re.compile(r"\bAsphalt\w*", re.I),
     "gegen": re.compile(r"\bAsphalt\w*(?:trag|deck|binder)\w*|\bAsphaltbeton\w*|\bTragdeckschicht\w*"
                         r"|\bAsphalt\w*\b[^.;]{0,40}?\b(?:herstellen|einbauen|wiederherstellen)\b", re.I),
     "gegen_im": "kurz",
     "gegen_ohne": re.compile(r"entsorg|abbruch|abbrech|fräs|aufnehm|aufbrech|ausbau", re.I)},
]
assert len(REGELN) <= 5                          # Scope D: höchstens 5 Paarregeln


def _texte(r):
    kurz = normalisiere_leerzeichen(_txt(r.kurztext))
    lang = normalisiere_leerzeichen(eigener_langtext(_txt(r.kurztext), _txt(r.langtext)))
    return kurz, lang, (kurz + " " + lang).strip()


def _pruefe(pos, seiten, bloecke):
    zeilen = [(r,) + _texte(r) for r in pos.itertuples()]
    zeilen = [z for z in zeilen if z[1]]                       # ohne Kurztext kein Beleg (R5)
    treffer = {}                                               # OZ -> (Zeile, [(Regel, Ausloeserzahl)])
    for regel in REGELN:
        ausl = [z for z in zeilen if regel["ausloeser"](z[1], z[3])]
        if not ausl:
            continue
        feld = 1 if regel["gegen_im"] == "kurz" else 3
        ohne = regel.get("gegen_ohne")
        if any(regel["gegen"].search(z[feld]) and not (ohne and ohne.search(z[1])) for z in zeilen):
            continue
        erste = ausl[0]
        treffer.setdefault(normalisiere_oz(erste[0].oz), (erste, []))[1].append((regel, len(ausl)))
    funde = []
    for oz, ((r, kurz, lang, _), regeln) in treffer.items():
        passt = _passt_fuer(r, seiten, bloecke)
        belege = [kurz]
        for regel, _ in regeln:
            if regel["wort"].search(kurz):
                continue
            m = regel["wort"].search(lang)
            z = _beleg_ausschnitt(lang, m, passt) if m else None
            if z and z not in belege:
                belege.append(z)
        # Das Fehlen ist eine abgeleitete Aussage, kein Feldwert der Datei: steht in der Begründung, nicht in
        # feldbelege (Datenvertrag; Skeptiker prüft es über alle Seiten bzw. den ganzen Text der Rohdatei)
        regel_text = "; ".join(f"{regel['id']} {regel['name']}: keine Position mit „{regel['fehlt']}“ im "
                               f"{'Kurztext' if regel['gegen_im'] == 'kurz' else 'Text'} "
                               f"({n} Auslöser-Position{'en' if n > 1 else ''} im LV)" for regel, n in regeln)
        fehlt = " und ".join(regel["fehlt"] for regel, _ in regeln)
        namen = "; ".join(regel["name"] for regel, _ in regeln)
        funde.append({
            "id": f"{NR}|{r.datei}|{oz}",
            "pruefung": NR,
            "kategorie": KATEGORIE,
            "titel": f"{TITEL}: {fehlt}",
            "positionen": [{"datei": r.datei, "oz": r.oz, "seite": _seite(r.seite)}],
            "belege": belege,
            "feldbelege": [],
            "begruendung": f"Paarregel {regel_text}. Das LV enthält die auslösende Leistung, aber keine eigene "
                           f"Position für {fehlt}. Hinweis: {HINWEIS}. Empfehlung: {EMPFEHLUNG}.",
            "stufe": STUFE,
            "stufe_begruendung": f"Stufe {STUFE} laut Team 21.11.2026 (B2-F11)",
            "prioritaet_in_stufe": PRIORITAET_IN_STUFE[(NR, STUFE)],     # zentrale Rangtabelle (Team 21:20)
            "rueckfrage": None,
            "status": "offen",
        })
    return funde


def pruefe_vollstaendigkeit(df, quelle=None):
    """Block B3 auf einer Tabelle aus parse(). `quelle` bei PDF und GAEB 90 Pflicht (Belege am Original)."""
    if nur_preise(df):
        return []
    formate = set(df.format)
    if formate & {"PDF", "GAEB 90"} and quelle is None:
        raise ValueError("Für PDF und GAEB 90 den Pfad der Originaldatei angeben: pruefe_vollstaendigkeit(df, pfad)")
    pos = df[df.typ == "Position"]
    if "PDF" in formate:
        import pdfplumber
        with pdfplumber.open(str(quelle)) as pdf:
            return sortiere(_pruefe(pos, PdfSeiten(pdf), None))
    return sortiere(_pruefe(pos, None, Gaeb90Bloecke(quelle) if "GAEB 90" in formate else None))


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Block B3: mögliche fehlende Leistung")
    ap.add_argument("dateien", nargs="+")
    ap.add_argument("--out")
    a = ap.parse_args()
    alle = []
    for d in a.dateien:
        df = parse(d)
        if nur_preise(df):
            continue
        f = pruefe_vollstaendigkeit(df, d)
        print(f"{Path(d).name}: {len(f)} Funde", file=sys.stderr)
        alle += f
    text = json.dumps(alle, ensure_ascii=False, indent=2)
    if a.out:
        if Path(a.out).resolve().is_relative_to(Path("data").resolve()):
            sys.exit("--out nie in data/ (E12 (4))")
        Path(a.out).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
