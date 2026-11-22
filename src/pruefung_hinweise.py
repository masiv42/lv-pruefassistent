"""
pruefung_hinweise.py - Prüfungen Nr. 7–14 und 18 aus input/pruefkatalog.md (Block B2, Sitzung B2).

Dateigetrennt von Block B1 (Team, 21.11.2026, 17:45): Sitzung B2 legt nur diese Datei, ihren Test und
docs/uebergabe_sitzung_B2.md an. Die Einbindung in alle_pruefungen(), App und Export macht Sitzung B1 im Block
„B2-Integration“. Bis dahin ist B2 nicht fertig (E2 f, j; E7).

Prüfungen (Kategorie, Stufe und Handlungsempfehlung laut input/pruefkatalog.md):
  Nr. 7  Produktvorgabe „oder gleichwertig“   Risikohinweis, Stufe 3, vormerken
  Nr. 8  Bestand, vorhandene Anlagen          Risikohinweis, Stufe 3, vormerken
  Nr. 9  Entsorgung                           Risikohinweis, Stufe 3, vormerken
  Nr. 10 Vorhalten, bauzeitabhängig           Risikohinweis, Stufe 3, vormerken
  Nr. 11 Vage Formulierung                    Unklarheit,    Stufe 4, nur Hinweis – nur an Positionen, die auch
                                              einen Fund Nr. 5–10 haben („vage nur in Kombination“, Backlog B2)
  Nr. 12 Verweistext („wie vor, jedoch“)       Unklarheit,    Stufe 4, nur Hinweis – nur mit „jedoch“ (B2-F2)
  Nr. 13 Stundenlohnarbeiten                  Risikohinweis, Stufe 4, nur Hinweis
  Nr. 14 Position enthält Bild/Skizze         Unklarheit,    Stufe 4, nur Hinweis
  Nr. 18 Ungewöhnliche Mengen: Menge 1 bei m, m², m³, t, kg (ohne Bedarfspositionen = Nr. 5)
                                              Risikohinweis, Stufe 2, Risiko einpreisen
Die Regeln sind nur Stichwort- bzw. Feldregeln. Sie benennen, sie urteilen nicht (Kern 2): kein Fund ist eine
Aussage über einen Nachtrag, nur „mögliches Nachtragspotenzial“ (R7). Die KI-Anteile laut Katalog (Nr. 8, 9, 11)
baut Sitzung B2 nicht (Team, 21.11.2026, 17:45).

Belege (R5): Der Kurztext ist immer der erste Beleg (wie Nr. 3, 5, 6). Dazu je Treffer ein wörtlicher Ausschnitt
aus Kurz- oder Langtext (Leerraum zusammengefasst, sonst unverändert), höchstens MAX_AUSSCHNITTE je Fund.
Jeder Ausschnitt wird am Original geprüft, bevor er Beleg wird (wie Nr. 1/2 in pruefung_widerspruch.py):
  PDF     zusammenhängend auf der Startseite der Position oder bis zu 3 Folgeseiten (PdfSeiten); parse() lässt
          Kopfzeilen, „STLB-Bau …“- und Punktezeilen weg, ein Ausschnitt darüber hinweg stünde so nicht im Original;
  GAEB 90 im eigenen Block der Position (Satz 21 bis zum nächsten Satz außer 22–30, Gaeb90Bloecke); parse() hängt
          Text hinter dem Block (z. B. Vorbemerkung Satz 20 des nächsten Bereichs) an die vorige Position (B2-L1).
Passt kein Ausschnitt, wird er kleiner gewählt (bis zum Trefferwort selbst); passt auch das nicht, fällt der
Treffer weg. Ohne Treffer mit wörtlichem Beleg kein Fund.
Feldwerte (Einheit, Menge) und Kennzeichen stehen in `feldbelege` (docs/data-contracts.md).
Positionen ohne Kurztext und reine Preisdateien ergeben keinen Fund.

Rang in Stufe (`prioritaet_in_stufe`): RANG_VORSCHLAG, vom Team bestätigt (B2-F1, 21.11.2026, 18:50); Sitzung B1
trägt ihn bei der Integration in PRIORITAET_IN_STUFE ein.

Aufruf (aus der Projektwurzel, uv-Befehl siehe AGENTS.md):
  python src/pruefung_hinweise.py <datei> [<datei> ...] [--out funde.json]
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

from lv_parser import parse, _decode_gaeb90
from pruefung_widerspruch import normalisiere_oz, normalisiere_leerzeichen, PdfSeiten, PRIORITAET_IN_STUFE
from pruefung_formal import nur_preise, sortiere, pruefe_formal

RISIKO, UNKLARHEIT = "Risikohinweis", "Unklarheit"
FELDWERT, KENNZEICHEN = "Feldwert", "Kennzeichen in der Datei"

# Nr. -> (Kategorie, Stufe, Handlungsempfehlung) laut input/pruefkatalog.md
KATALOG = {
    7: (RISIKO, 3, "vormerken"),
    8: (RISIKO, 3, "vormerken"),
    9: (RISIKO, 3, "vormerken"),
    10: (RISIKO, 3, "vormerken"),
    11: (UNKLARHEIT, 4, "nur Hinweis"),
    12: (UNKLARHEIT, 4, "nur Hinweis"),
    13: (RISIKO, 4, "nur Hinweis"),
    14: (UNKLARHEIT, 4, "nur Hinweis"),
    18: (RISIKO, 2, "Risiko einpreisen"),
}
NUMMERN = tuple(KATALOG)

# Rang in Stufe, endgültige Rangtabelle (Team 21.11.2026, 21:20; ersetzt B2-F1): Stufe 2 Nr. 6 → 1, „Menge 0“ → 2,
# Nr. 5 → 3, Nr. 18 → 4; Stufe 3 Nr. 9 → 1, Nr. 10 → 2, Nr. 7 → 3, Nr. 8 → 4, Nr. 19 → 5; Stufe 4 Nr. 14 → 1,
# Nr. 3 (Auftrags-LV) → 2, Nr. 13 → 3, Nr. 11 → 4, Nr. 12 → 5. Bei der Integration eine zentrale Tabelle (Sitzung B1).
RANG_VORSCHLAG = {(18, 2): 4,
                  (9, 3): 1, (10, 3): 2, (7, 3): 3, (8, 3): 4,
                  (14, 4): 1, (13, 4): 3, (11, 4): 4, (12, 4): 5}

TITEL = {
    7: "Produktvorgabe „oder gleichwertig“",
    8: "Bestand, vorhandene Anlagen",
    9: "Entsorgung, Boden",          # Katalog-Titel (Team B2-F5); Anteil Bodenklasse/Homogenbereich offen (B2-L6)
    10: "Vorhalten, bauzeitabhängig",
    11: "Vage Formulierung",
    12: "Verweistext („wie vor, jedoch“)",
    13: "Stundenlohnarbeiten",
    14: "Position enthält Bild/Skizze",
    18: "Menge 1 bei Mengeneinheit",
}

# Warum der Beleg den Fund trägt (sachlich, ohne Rechtsaussage: R7)
GRUND = {
    7: "Die Position gibt ein Produkt vor und lässt „gleichwertige“ Produkte zu. Ob ein anderes Produkt als "
       "gleichwertig angenommen wird, ist offen: mögliches Nachtragspotenzial bzw. möglicher Streitpunkt in der "
       "Ausführung.",
    8: "Die Position bezieht sich auf Bestand bzw. vorhandene Anlagen. Zustand und Umfang des Bestands sind aus dem "
       "Text nicht sicher abzuschätzen: mögliches Nachtragspotenzial.",
    9: "Die Position nennt Entsorgung oder Schadstoffe. Menge, Belastung und Entsorgungsweg bestimmen die Kosten "
       "stark: mögliches Nachtragspotenzial.",
    10: "Die Position wird nach Zeit vorgehalten bzw. abgerechnet. Verschiebt sich die Bauzeit, ändert sich die "
        "Vorhaltedauer: mögliches Nachtragspotenzial.",
    11: "Die Position enthält eine vage Formulierung und hat an derselben Stelle schon einen Risikohinweis. "
        "Der Leistungsumfang ist dadurch weniger klar.",
    12: "Die Position verweist auf eine andere Position und weicht davon ab („wie vor …, jedoch“). Der vollständige "
        "Leistungsumfang steht nur zusammen mit der Bezugsposition fest.",
    13: "Stundenlohnarbeiten: Die Menge ist meist ein Ansatz, der Verrechnungssatz muss alle Kosten decken.",
    14: "Die Position enthält ein Bild bzw. eine Skizze. Die Prüfung liest nur den Text; was das Bild zeigt, ist "
        "nicht geprüft.",
    18: "Menge 1 bei einer Längen-, Flächen-, Raum- oder Gewichtseinheit. Prüfen, ob die Menge zur Leistung passt.",
}

# Kostenwirkung je Prüfung (Rolle Wirtschaftlichkeit & Kosten, E2 d); keine Zahlen ohne Quelle (R11)
KOSTENWIRKUNG = {
    7: "indirekt: Ein abgelehntes Alternativprodukt kann Mehrkosten beim Material verursachen (Beispiel im "
       "Datensatz: [ORT_024] LV24069.D86, Nachtrag 1 „Mehrkosten Armaturen …“); Höhe nicht bezifferbar.",
    8: "indirekt: unbekannter Zustand des Bestands wirkt auf Aufwand und Entsorgung; Höhe nicht bezifferbar.",
    9: "direkt: Entsorgungskosten hängen von Belastung und Menge ab (Beispiel im Datensatz: [ORT_024] LV24069.D86, "
       "Nachtrag 2 „Zulage Entsorgungskosten …“); Höhe nicht bezifferbar.",
    10: "direkt: Vorhaltekosten steigen mit der Bauzeit (Beispiel im Datensatz: [ORT_024] LV24069.D86, zwei "
        "Zulagen „… wegen verschobener Bauzeit“); Höhe nicht bezifferbar.",
    11: "keine direkte Kostenwirkung: Die Formulierung macht den Umfang unklar; die Kostenwirkung trägt der "
        "Risikohinweis an derselben Position.",
    12: "keine direkte Kostenwirkung: Der Verweis selbst kostet nichts; Abweichungen zur Bezugsposition können den "
        "Preis ändern.",
    13: "indirekt: Der Verrechnungssatz muss Lohn und Zuschläge decken; die Stundenmenge ist meist ein Ansatz.",
    14: "keine direkte Kostenwirkung: Der Inhalt des Bildes ist nicht ausgewertet.",
    18: "direkt möglich: Weicht die Ausführungsmenge von 1 ab, ändert sich der Positionspreis entsprechend.",
}

MAX_AUSSCHNITTE = 3
VOR, NACH = 6, 4            # höchstens so viele Wörter vor und nach dem Treffer im Ausschnitt

MUSTER = {
    7: re.compile(r"\bgleichwertig\w*|\bglw\b\.?", re.I),
    8: re.compile(r"\bbestehend(?:e|en|er|em|es)?\b(?!\s+aus\b)"
                  r"|(?<!bauseits )(?<!bauseitig )(?<!bauseitigem )(?<!bauseitigen )\bvorhanden(?:e|en|er|em|es)\b"
                  r"|\bBestand\b|\bBestands(?!unterlage|dokumentation|pl[aä]n|lagepl[aä]n)\w+"
                  r"|\bAltbestand\w*|\bAltanlage\w*|\bAltleitung\w*", re.I),
    9: re.compile(r"(?<!Ver- und )(?<!Ver-/)\bentsorg(?!ungsleitung|ungsltg|ungseinr|ungsanschl|ungsbetrieb|ungstr)\w*|\bDeponie\w*|\bLAGA\b|\bAVV\b|\bschadstoff\w*|\bkontaminiert\w*"
                  r"|\bAltlast\w*|\bteerhaltig\w*|\bpechhaltig\w*", re.I),
    10: re.compile(r"\bvorhalt(?!ungsempfehlung)\w*|\bVorhaltung(?!sempfehlung)\w*|\bGebrauchsüberlassung\w*|\bMietzeit\w*|\bMietdauer\w*", re.I),
    11: re.compile(r"\bnach\s+Aufwand\b|\bggf\.|\bgegebenenfalls\b|\bnach\s+Erfordernis\w*|\b(?:nach|bei)\s+Bedarf\b"
                   r"|\bnach\s+Wahl\b|\bnach\s+Angabe\w*|\bnach\s+Anweisung\w*|\bnach\s+Absprache\w*"
                   r"|\bnach\s+örtlich\w*\s+\w+|\b(?:soweit|falls|wenn|sofern)\s+erforderlich\b"
                   r"|\b(?:sofern|falls|soweit)\s+vorhanden\b|\bsinngemäß\w*|\bo\.\s?ä\.|\boder\s+ähnlich\w*", re.I),
    # Nr. 12 nur Verweise mit Abweichung: Verweis und „jedoch“ im selben Satzteil (Team, 21.11.2026, B2-F2)
    12: re.compile(r"(?:\bwie\s+vor\b|\bwie\s+vorbeschrieben\w*|\bwie\s+zuvor\b"
                   r"|\bwie\s+(?:Pos\.?|Position|OZ)\b|\bLeistung\s+wie\s+Position\b)[^;]{0,80}?\bjedoch\b", re.I),
    13: re.compile(r"\bStundenlohn\w*|\bRegiearbeit\w*|\bRegiestunde\w*", re.I),
}
ZEIT_EINHEITEN = {"StWo", "mWo", "m2Wo", "m2d", "md", "Wo", "d", "Mt", "Jahr"}   # Nr. 10, Einheiten im Datensatz
MENGEN_EINHEITEN = {"m", "m²", "m³", "t", "kg"}                                  # Nr. 18
KOMBINATION_11 = (5, 6, 7, 8, 9, 10)                                            # Nr. 11 nur mit diesen Funden
BILD_FLAG = "enthält Bild/Skizze"          # art_roh bei GAEB XML (Element image/Image in der Beschreibung)
STUNDENLOHN_FLAG = "Stundenlohn"           # art_roh bei GAEB XML (Element HourIt)
SAETZE_IM_BLOCK = {f"{n}" for n in range(22, 31)}   # GAEB 90: Sätze, die zur Position gehören (nach Satz 21)


def _txt(x):
    return x if isinstance(x, str) else ""


def _seite(x):
    return None if x is None or pd.isna(x) else int(x)


def _zahl(x):
    return f"{x:g}".replace(".", ",")


def eigener_langtext(kurz, lang):
    """Langtext ohne den Kurztext am Anfang (viele Formate wiederholen ihn dort)."""
    return lang[len(kurz):].strip() if kurz and lang.startswith(kurz) else lang


class Gaeb90Bloecke:
    """Text der Sätze 25/26 je Position direkt aus der GAEB-90-Datei: Block von Satz 21 bis zum nächsten Satz außer
    22–30 (Satz 11, 12, 20, 31, 32, 41, 42, 99, T… beenden ihn; Satz 24, 28, 30 stehen im Datensatz
    innerhalb von Positionen, z. B. [ORT_024] LV24069.D86 Satz 30 zwischen Satz 23 und 25). Schlüssel: OZ aus Satz 21, Spalten 3–11, ohne Leerzeichen."""

    def __init__(self, pfad):
        zeilen = _decode_gaeb90(Path(pfad).read_bytes()).replace("\r\n", "\n").split("\n")
        bloecke, oz = {}, None
        for l in zeilen:
            sa = l[:2]
            if sa == "21":
                oz = re.sub(r"\s", "", l[2:11])
                bloecke.setdefault(oz, [])
            elif sa in SAETZE_IM_BLOCK:
                if sa in ("25", "26") and oz is not None:
                    bloecke[oz].append(l[2:72].strip())
            else:
                oz = None
        self.bloecke = {k: normalisiere_leerzeichen(" ".join(v)) for k, v in bloecke.items()}

    def im_block(self, ausschnitt, oz):
        return normalisiere_leerzeichen(ausschnitt) in self.bloecke.get(str(oz).replace(".", ""), "")


def ausschnitt(text, m, vor=VOR, nach=NACH):
    """Wörtlicher Ausschnitt um den Treffer m: bis zu `vor` Wörter davor und `nach` Wörter danach."""
    woerter = [w.span() for w in re.finditer(r"\S+", text)]
    i = next(k for k, (a, e) in enumerate(woerter) if e > m.start())
    j = next(k for k, (a, e) in enumerate(woerter) if e >= m.end())
    a, e = max(0, i - vor), min(len(woerter) - 1, j + nach)
    nur_zeichen = lambda k: re.fullmatch(r"[^\w\[\]]+", text[woerter[k][0]:woerter[k][1]]) is not None
    while e > j and nur_zeichen(e):           # kein Rand aus reinen Satzzeichen (z. B. „ ,“, FS-B2-1)
        e -= 1
    while a < i and nur_zeichen(a):
        a += 1
    return text[woerter[a][0]:woerter[e][1]]


GROESSEN = sorted(((v, n) for v in range(VOR + 1) for n in range(NACH + 1)), key=lambda vn: (-(vn[0] + vn[1]), -vn[0]))


def treffer(muster, kurz, lang, passt=lambda a: True):
    """Belege für ein Muster: Kurztext (falls Treffer dort) und Ausschnitte aus dem eigenen Langtext. Je Treffer das
    größte Fenster, für das `passt` gilt (Prüfung am Original); sonst fällt der Treffer weg."""
    belege = []
    if muster.search(kurz):
        belege.append(kurz)
    rest = eigener_langtext(kurz, lang)
    for m in muster.finditer(rest):
        z = next((a for a in (ausschnitt(rest, m, v, n) for v, n in GROESSEN) if passt(a)), None)
        if z and z not in belege and not any(z in b for b in belege):
            belege.append(z)
    return belege


def _position(r):
    return {"datei": r.datei, "oz": r.oz, "seite": _seite(r.seite)}


def _neu(nr, r, kurz, ausschnitte, feldbelege, zusatz=""):
    kat, stufe, empf = KATALOG[nr]
    belege = [kurz] + [z for z in ausschnitte if z != kurz][:MAX_AUSSCHNITTE]
    return {
        "id": f"{nr}|{r.datei}|{normalisiere_oz(r.oz)}",
        "pruefung": nr,
        "kategorie": kat,
        "titel": TITEL[nr],
        "positionen": [_position(r)],
        "belege": belege,
        "feldbelege": feldbelege,
        "begruendung": f"{GRUND[nr]}{zusatz} Empfehlung laut Prüfkatalog: {empf}.",
        "stufe": stufe,
        "stufe_begruendung": f"Stufe {stufe} laut input/pruefkatalog.md, Nr. {nr}",
        "prioritaet_in_stufe": PRIORITAET_IN_STUFE[(nr, stufe)],     # zentrale Rangtabelle (Team 21:20)
        "rueckfrage": None,
        "status": "offen",
    }


def _text_pruefung(nr, r, kurz, lang, passt):
    b = treffer(MUSTER[nr], kurz, lang, passt)
    return _neu(nr, r, kurz, b, []) if b else None


def _nr10(r, kurz, lang, passt):
    b = treffer(MUSTER[10], kurz, lang, passt)
    feld = []
    if r.einheit in ZEIT_EINHEITEN:
        feld.append({"art": FELDWERT, "text": f"Einheit: {_txt(r.einheit_roh).strip() or r.einheit}"})
    return _neu(10, r, kurz, b, feld) if (b or feld) else None


def _nr13(r, kurz, lang, passt):
    b = treffer(MUSTER[13], kurz, lang, passt)
    kennz = r.format == "GAEB XML" and STUNDENLOHN_FLAG in _txt(r.art_roh).split("; ")
    feld = [{"art": KENNZEICHEN, "text": "<HourIt>"}] if kennz else []
    if not (b or feld):
        return None
    if r.einheit == "h":
        feld.append({"art": FELDWERT, "text": f"Einheit: {_txt(r.einheit_roh).strip() or r.einheit}"})
    return _neu(13, r, kurz, b, feld)


def _nr14(r, kurz):
    if not (r.format == "GAEB XML" and BILD_FLAG in _txt(r.art_roh)):
        return None
    return _neu(14, r, kurz, [], [{"art": KENNZEICHEN, "text": "<image> in der Positionsbeschreibung"}])


def _nr18(r, kurz):
    m = r.menge
    if m is None or pd.isna(m) or m != 1 or r.einheit not in MENGEN_EINHEITEN:
        return None
    roh = _txt(r.einheit_roh).strip() or r.einheit
    f = _neu(18, r, kurz, [], [{"art": FELDWERT, "text": f"Menge: {_zahl(m)}"},
                                {"art": FELDWERT, "text": f"Einheit: {roh}"}])
    f["titel"] = f"{TITEL[18]} ({r.einheit})"
    return f


def _schluessel(f):
    p = f["positionen"][0]
    return p["datei"], normalisiere_oz(p["oz"])


def pruefe_hinweise(df, quelle=None, weitere_funde=None):
    """Prüfungen Nr. 7–14 und 18 auf einer Tabelle aus parse(), sortiert wie alle_pruefungen().

    `quelle`: Pfad der Originaldatei; bei PDF und GAEB 90 Pflicht (Ausschnitte werden am Original geprüft).
    `weitere_funde`: schon berechnete Funde Nr. 1–6 derselben Datei (für Nr. 11 „nur in Kombination“ und für den
    Ausschluss von Bedarfspositionen bei Nr. 18). Fehlt die Liste, rechnet die Funktion Nr. 5 und 6 selbst mit
    pruefe_formal(); diese Funde gibt sie nicht zurück."""
    if nur_preise(df):
        return []
    formate = set(df.format)
    if formate & {"PDF", "GAEB 90"} and quelle is None:
        raise ValueError("Für PDF und GAEB 90 den Pfad der Originaldatei angeben: pruefe_hinweise(df, pfad)")
    if "PDF" in formate:
        import pdfplumber
        with pdfplumber.open(str(quelle)) as pdf:
            return _pruefe(df, weitere_funde, PdfSeiten(pdf), None)
    return _pruefe(df, weitere_funde, None, Gaeb90Bloecke(quelle) if "GAEB 90" in formate else None)


def _pruefe(df, weitere_funde, seiten, bloecke):
    if weitere_funde is None:
        weitere_funde = pruefe_formal(df)
    vorher = {}
    for f in weitere_funde:
        for p in f["positionen"]:
            vorher.setdefault((p["datei"], normalisiere_oz(p["oz"])), set()).add(f["pruefung"])
    funde = {}
    for r in df[df.typ == "Position"].itertuples():
        kurz = normalisiere_leerzeichen(_txt(r.kurztext))
        if not kurz:
            continue                                         # ohne Kurztext kein wörtlicher Beleg (R5)
        lang = normalisiere_leerzeichen(_txt(r.langtext))
        nrn = set(vorher.get((r.datei, normalisiere_oz(r.oz)), set()))
        if seiten is not None and _seite(r.seite) is not None:
            passt = (lambda s: lambda a: seiten.auf_einer_seite(a, s))(_seite(r.seite))
        elif bloecke is not None:
            passt = (lambda oz: lambda a: bloecke.im_block(a, oz))(r.oz)
        else:
            passt = lambda a: True
        eigene = [_text_pruefung(7, r, kurz, lang, passt), _text_pruefung(8, r, kurz, lang, passt),
                  _text_pruefung(9, r, kurz, lang, passt), _nr10(r, kurz, lang, passt)]
        nrn |= {f["pruefung"] for f in eigene if f}
        if nrn & set(KOMBINATION_11):
            f11 = _text_pruefung(11, r, kurz, lang, passt)
            if f11:
                mit = ", ".join(str(n) for n in sorted(nrn & set(KOMBINATION_11)))
                f11["begruendung"] = f11["begruendung"].replace(
                    " Empfehlung", f" An derselben Position: Fund Nr. {mit}. Empfehlung", 1)
                eigene.append(f11)
        eigene += [_text_pruefung(12, r, kurz, lang, passt), _nr13(r, kurz, lang, passt), _nr14(r, kurz)]
        if 5 not in nrn:
            eigene.append(_nr18(r, kurz))
        for f in eigene:
            if f and f["id"] not in funde:                 # höchstens ein Fund je Prüfung, Datei und OZ
                funde[f["id"]] = f
    return sortiere(list(funde.values()))


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Prüfungen Nr. 7–14 und 18")
    ap.add_argument("dateien", nargs="+")
    ap.add_argument("--out", help="Funde als JSON in diese Datei (nie in data/raw/)")
    a = ap.parse_args()
    alle = []
    for d in a.dateien:
        df = parse(d)
        if nur_preise(df):
            print(f"{Path(d).name}: nur Preise, keine Prüfung", file=sys.stderr)
            continue
        f = pruefe_hinweise(df, d)
        zahl = Counter(x["pruefung"] for x in f)
        print(f"{Path(d).name}: {len(f)} Funde " + str(dict(sorted(zahl.items()))), file=sys.stderr)
        alle += f
    text = json.dumps(alle, ensure_ascii=False, indent=2)
    if a.out:
        ziel = Path(a.out).resolve()
        if any(ziel.is_relative_to(Path(d).resolve().parent) and Path(d).resolve().parent.name == "raw"
               for d in a.dateien) or ziel.is_relative_to(Path("data/raw").resolve()):
            sys.exit("--out darf nicht in data/raw/ liegen")
        Path(a.out).write_text(text + "\n", encoding="utf-8")
        print("gespeichert:", a.out, file=sys.stderr)
    else:
        print(text)
