"""
pruefung_widerspruch.py - Prüfung Nr. 1 und 2 aus input/pruefkatalog.md.

Möglicher Widerspruch zwischen Kurz- und Langtext einer Position bei
  Nr. 1: Nennweite (DN)
  Nr. 2: Betonfestigkeitsklasse (C../..)
Rein regelbasiert und deterministisch (docs/decisions.md, 20.11.2026).

Grundlage: src/heuristik_widerspruch_v0.py (Referenz). Übernommen:
- Werte im Kurztext und im Langtext suchen (gleiche Muster wie v0).
- Beginnt der Langtext mit dem Kurztext, wird dieser Anfang vorher abgeschnitten.
- Kandidat, wenn beide Seiten Werte haben und kein Wert gemeinsam ist.
Neu:
- DN nur melden, wenn der Langtext genau einen DN-Wert nennt (Team, 20.11.2026).
- Ausgabe als Fund nach docs/data-contracts.md (JSON-fähiges dict).
- Belege: Kurztext und ein Ausschnitt des Langtexts um jeden Langtext-Wert,
  Leerzeichenfolgen zu einem Leerzeichen zusammengefasst (Team, 20.11.2026).
- PDF (P1b, Team 21.11.2026): Ein Langtext-Ausschnitt muss zusammenhängend auf
  EINER Seite des Originals stehen. Der Parser verbindet Zeilen über Seiten-
  wechsel hinweg und lässt Ausfülllinien ("'.....'" nach "Fabrikat:", "Type:" …)
  sowie Kopf-/Fußzeilen weg; ein Ausschnitt über solche Stellen wäre im Original
  nicht wörtlich. Geprüft wird gegen den Seitentext mit derselben Extraktion wie
  lv_parser._pdf_lines, aber ohne dessen Filter. Passt das größte Fenster nicht,
  wird es verkleinert. GAEB XML und GAEB 90 lassen keinen Text weg.

B1q (Team, 21.11.2026, F5 B1b; Regeln an erfundenen Testfällen, E12 (3)):
- „DN a/b“ (auch „DN a / b“, „DN a/b/c“) ist EINE Angabe mit mehreren Werten, z. B. „DN 800/900“ = DN 800 oder
  DN 900. Kein Fund, wenn der Kurztext einen dieser Werte nennt. Die Regel „Langtext nennt genau eine DN-Angabe“
  zählt Angaben, nicht Werte; „DN 125/100“ ist also eine Angabe, ein Kurztext DN 150 bleibt ein Fund.
- Folgt dem zweiten Wert eine Länge („DN 300/1000 mm lg“, „… lang“, „Länge“, „Baulänge“), ist er keine
  Nennweite.
- Bereichsangaben (Team, 21.11.2026, F1 Lesart C): nennen Kurz- und Langtext je eine Obergrenze („bis DN y“) und
  stimmen die Werte nicht überein, bleibt der Fund; die Begründung nennt „Bereichsangaben, Obergrenzen
  verschieden“. Kein Fund geht still verloren.

Bekannte Grenzen (wie v0):
- Übersieht Fälle, in denen der Langtext den Kurztext-Wert UND einen anderen nennt.
- Erkennt nur "DN 100"/"DN100", keine Schreibvarianten wie "NW 100" oder "DA 110".

Aufruf (aus der Projektwurzel, uv-Befehl siehe AGENTS.md):
  python src/pruefung_widerspruch.py <datei> [<datei> ...] [--out funde.json]
Im Code: pruefe(parse(pfad), pfad) – bei PDF ist der Pfad Pflicht.
"""
import json
import re
import sys
from pathlib import Path

import pandas as pd

from lv_parser import parse

PATTERNS = {
    1: r"\bDN\s?\d{2,4}\b",        # Nennweite
    2: r"\bC\s?\d{2}/\d{2}\b",     # Betonfestigkeitsklasse
}
TITEL = {
    1: "Nennweite (DN) im Kurztext ≠ Langtext",
    2: "Betonfestigkeitsklasse im Kurztext ≠ Langtext",
}
KATEGORIE = "möglicher Widerspruch"
STUFE = 1                       # Stufe nach E3 (F1, Team 21.11.2026); Anzeige-Namen in bericht.STUFEN (F4)
# Rang in Stufe (Feld prioritaet_in_stufe) = Rang einer Prüfung innerhalb ihrer Stufe (1 = zuerst). Endgültige,
# zentrale Rangtabelle für alle Prüfungen (Team, 21.11.2026, 21:20; ersetzt F1/F10 (vorläufig) und die
# Rang-Konstanten der Module; E3: selten, sicher, geldrelevant gemeinsam abgewogen).
# Schlüssel: (Prüfungs-Nr., Stufe); (3, 2) = „Menge 0“, (3, 4) = Auftrags-LV ohne Menge und Einheit.
PRIORITAET_IN_STUFE = {
    (17, 1): 1, (4, 1): 2, (3, 1): 3, (16, 1): 4, (2, 1): 5, (15, 1): 6, (1, 1): 7,
    (6, 2): 1, (3, 2): 2, (5, 2): 3, (18, 2): 4,
    (9, 3): 1, (10, 3): 2, (7, 3): 3, (8, 3): 4, (19, 3): 5,
    (14, 4): 1, (3, 4): 2, (13, 4): 3, (11, 4): 4, (12, 4): 5,
}
FENSTER_WOERTER = 5   # höchstens so viele Wörter vor und nach dem Langtext-Wert im Beleg
SEITEN_FOLGE = 3      # PDF: Ausschnitt auf der Startseite der Position oder bis zu 3 Folgeseiten


def normalisiere_oz(oz):
    """OZ ohne führende Nullen je Abschnitt ("05.01.4" -> "5.1.4").
    Gleiche Logik wie key() in src/validate_parser.py (docs/data-contracts.md)."""
    parts = [p.lstrip("0") or "0" for p in str(oz).strip(".").split(".") if p != ""]
    return ".".join(parts)


def normalisiere_leerzeichen(text):
    """Folgen von Leerzeichen und Zeilenumbrüchen -> ein Leerzeichen; sonst nichts."""
    return re.sub(r"\s+", " ", text or "").strip()


def beleg_im_text(beleg, *texte):
    """True, wenn der Beleg wörtlich (nach Zusammenfassen der Leerzeichen) in einem Text steht."""
    b = normalisiere_leerzeichen(beleg)
    return bool(b) and any(b in normalisiere_leerzeichen(t) for t in texte)


def _wert(treffer):
    return re.sub(r"\s", "", treffer).upper()


DN_RE = re.compile(r"\bDN\s?(\d{2,4})\b", re.I)
DN_WEITER_RE = re.compile(r"\s?/\s?(\d{2,4})\b")
BIS_DN_RE = re.compile(r"\bbis\s+DN\s?\d", re.I)      # Obergrenze „bis DN y“ (F1 B1q, Lesart C)
LAENGE_RE = re.compile(r"\s*(?:mm\s*)?(?:lg\b|lang\b|Länge|Baulänge)", re.I)


def dn_angaben(text):
    """B1q: DN-Angaben eines Texts als Liste von Wert-Tupeln in Reihenfolge, ohne Wiederholung, z. B.
    „DN 125/100 … DN 150“ -> [("DN125", "DN100"), ("DN150",)]. Werte nach „/“ gehören zur selben Angabe,
    außer es folgt eine Länge („DN 300/1000 mm lg“ -> ("DN300",))."""
    out = []
    for m in DN_RE.finditer(text or ""):
        werte, pos = [f"DN{m.group(1)}"], m.end()
        while True:
            w = DN_WEITER_RE.match(text, pos)
            if not w or LAENGE_RE.match(text, w.end()):
                break
            werte.append(f"DN{w.group(1)}")
            pos = w.end()
        g = tuple(dict.fromkeys(werte))
        if all(set(g) != set(x) for x in out):
            out.append(g)
    return out


def _anzeige_angaben(angaben):
    """„DN 100, DN 125“ wie bisher; Angaben mit mehreren Werten als „DN 125/100“ (B1q)."""
    if all(len(a) == 1 for a in angaben):
        return ", ".join(_anzeige(w) for w in sorted({a[0] for a in angaben}))
    return ", ".join("/".join(_anzeige(w) if i == 0 else w[2:] for i, w in enumerate(a)) for a in angaben)


def werte(pattern, text):
    return {_wert(x) for x in re.findall(pattern, text or "", re.I)}


def _text(x):
    return x if isinstance(x, str) else ""


def _seite(x):
    return None if x is None or pd.isna(x) else int(x)


class PdfSeiten:
    """Seitentexte eines PDF (Leerzeichen zusammengefasst), nur bei Bedarf gelesen.
    Extraktion wie lv_parser._pdf_lines (Leerzeichen-Zeichen entfernt, layout=True,
    x_tolerance=1.5), aber ohne Kopf-/Fußzeilen- und Ausfülllinien-Filter."""

    def __init__(self, pdf):
        self.pdf = pdf
        self.texte = {}

    def text(self, nr):
        if nr not in self.texte:
            p = self.pdf.pages[nr - 1]
            fp = p.filter(lambda o: not (o.get("object_type") == "char" and o.get("text", "").isspace()))
            self.texte[nr] = normalisiere_leerzeichen(fp.extract_text(layout=True, x_tolerance=1.5) or "")
        return self.texte[nr]

    def auf_einer_seite(self, ausschnitt, seite):
        """True, wenn der Ausschnitt zusammenhängend auf einer Seite ab `seite` steht."""
        a = normalisiere_leerzeichen(ausschnitt)
        letzte = min(seite + SEITEN_FOLGE, len(self.pdf.pages))
        return any(a in self.text(nr) for nr in range(seite, letzte + 1))


def _fenster(t, start, ende, vor, nach):
    """Teilstring von t: Treffer t[start:ende] plus `vor` Wörter davor und `nach` Wörter danach."""
    s = start
    for _ in range(vor):
        i = t.rfind(" ", 0, max(s - 1, 0))
        if i < 0:
            s = 0
            break
        s = i + 1
    e = ende
    for _ in range(nach):
        i = t.find(" ", e + 1)
        if i < 0:
            e = len(t)
            break
        e = i
    return t[s:e].strip()


def _ausschnitt(text, pattern, wert, passt=lambda a: True):
    """Ausschnitt um das erste Vorkommen von `wert` in `text` (Leerzeichen zusammengefasst):
    das größte Fenster (bis zu FENSTER_WOERTER Wörter je Seite), für das `passt` gilt;
    bei gleicher Größe mit mehr Wörtern davor."""
    t = normalisiere_leerzeichen(text)
    for m in re.finditer(pattern, t, re.I):
        if _wert(m.group()) != wert:
            continue
        groessen = sorted(((v, n) for v in range(FENSTER_WOERTER + 1) for n in range(FENSTER_WOERTER + 1)),
                          key=lambda vn: (-(vn[0] + vn[1]), -vn[0]))
        for vor, nach in groessen:
            a = _fenster(t, m.start(), m.end(), vor, nach)
            if passt(a):
                return a
        return m.group()
    return None


def eigener_langtext(kurz, lang):
    """Langtext ohne den Kurztext am Anfang (wie bisher in _treffer). Leer, wenn die Position keinen
    eigenen Langtext hat (Langtext leer oder gleich dem Kurztext); dann kann Nr. 1/2 nichts finden."""
    kurz, lang = _text(kurz), _text(lang)
    return lang[len(kurz):] if lang.startswith(kurz) else lang


def _anzeige(wert):
    """DN125 -> DN 125; C25/30 bleibt."""
    return re.sub(r"^DN(\d)", r"DN \1", wert)


def _treffer(row, seiten=None):
    """Liefert je Prüfung (1, 2) die Rohdaten eines Funds oder nichts.
    `seiten`: PdfSeiten bei PDF, sonst None."""
    kurz = _text(row.kurztext)
    lang = _text(row.langtext)
    rest = eigener_langtext(kurz, lang)
    passt = (lambda a: True) if seiten is None or _seite(row.seite) is None \
        else (lambda a: seiten.auf_einer_seite(a, _seite(row.seite)))
    for nr, pat in PATTERNS.items():
        if nr == 1:                                    # B1q: „DN a/b“ = eine Angabe mit mehreren Werten
            ka, la = dn_angaben(kurz), dn_angaben(rest)
            k, l = {w for a in ka for w in a}, {w for a in la for w in a}
        else:
            k, l = werte(pat, kurz), werte(pat, rest)
        if not (k and l) or (k & l):
            continue
        if nr == 1 and len(la) != 1:                   # genau eine DN-Angabe im Langtext (Team, 20.11.2026)
            continue
        belege = [normalisiere_leerzeichen(kurz)]
        for w in sorted(l):
            a = _ausschnitt(rest, pat, w, passt)
            if a and a not in belege:
                belege.append(a)
        if nr == 1:
            begruendung = (f"Kurztext nennt {_anzeige_angaben(ka)}, Langtext nennt {_anzeige_angaben(la)}; "
                           f"kein Wert stimmt überein.")
            if BIS_DN_RE.search(kurz) and BIS_DN_RE.search(rest):       # F1 (B1q), Lesart C
                begruendung += " Bereichsangaben, Obergrenzen verschieden."
        else:
            begruendung = (f"Kurztext nennt {', '.join(_anzeige(w) for w in sorted(k))}, "
                           f"Langtext nennt {', '.join(_anzeige(w) for w in sorted(l))}; "
                           f"kein Wert stimmt überein.")
        yield nr, belege, begruendung


def pruefe(df, quelle=None):
    """Prüfung Nr. 1 und 2 auf einer Tabelle aus parse(). Gibt eine Liste von Funden
    (dicts nach docs/data-contracts.md) in der Reihenfolge der Tabelle zurück.
    Höchstens ein Fund je Prüfung, Datei und normalisierter OZ.
    `quelle`: Pfad der Originaldatei; bei PDF Pflicht (Belege seitengenau, siehe oben)."""
    if (df.format == "PDF").any():
        if quelle is None:
            raise ValueError("Für PDF den Pfad der Originaldatei angeben: pruefe(df, pfad)")
        import pdfplumber
        with pdfplumber.open(str(quelle)) as pdf:
            return _pruefe(df, PdfSeiten(pdf))
    return _pruefe(df, None)


def _pruefe(df, seiten):
    funde = {}
    for row in df[df.typ == "Position"].itertuples():
        for nr, belege, begruendung in _treffer(row, seiten):
            fid = f"{nr}|{row.datei}|{normalisiere_oz(row.oz)}"
            pos = {"datei": row.datei, "oz": row.oz, "seite": _seite(row.seite)}
            if fid in funde:   # doppelte OZ: ein Fund, mehrere Positionen
                f = funde[fid]
                f["positionen"].append(pos)
                f["belege"] += [b for b in belege if b not in f["belege"]]
                f["begruendung"] += f" Position {row.oz}: {begruendung}"
                continue
            funde[fid] = {
                "id": fid,
                "pruefung": nr,
                "kategorie": KATEGORIE,
                "titel": TITEL[nr],
                "positionen": [pos],
                "belege": belege,
                "begruendung": begruendung,
                "stufe": STUFE,
                "stufe_begruendung": f"Stufe {STUFE} laut input/pruefkatalog.md, Nr. {nr}",
                "prioritaet_in_stufe": PRIORITAET_IN_STUFE[(nr, STUFE)],
                "rueckfrage": None,
                "status": "offen",
            }
    return list(funde.values())


def pruefe_datei(path):
    return pruefe(parse(path), path)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Prüfung Nr. 1 und 2 (Kurz- gegen Langtext)")
    ap.add_argument("dateien", nargs="+")
    ap.add_argument("--out", help="Funde als JSON in diese Datei (nie in data/raw/)")
    a = ap.parse_args()
    alle = []
    for d in a.dateien:
        f = pruefe_datei(d)
        print(f"{Path(d).name}: {len(f)} Funde", file=sys.stderr)
        alle += f
    text = json.dumps(alle, ensure_ascii=False, indent=2)
    if a.out:
        if Path(a.out).resolve().is_relative_to(Path("data/raw").resolve()):
            sys.exit("--out darf nicht in data/raw/ liegen")
        Path(a.out).write_text(text + "\n", encoding="utf-8")
        print("gespeichert:", a.out, file=sys.stderr)
    else:
        print(text)
