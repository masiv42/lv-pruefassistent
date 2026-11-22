"""
test_parser_pdf.py - Tests für den PDF-Zweig von src/lv_parser.py (B1p, Team 21.11.2026, F3; R5, Kern 1).

Langtext nur aus dem Text der Position: Fuß-/Kopfzeilen, Zusammenstellungs- und Summenzeilen sowie umbrochene
Kurztext-Zeilen gehören nicht in den Langtext. Die Erwartungswerte stammen aus dem Original (Skeptiker,
21.11.2026): Seitentext der PDF-Seite, Schrift der Zeile, Kurztext derselben LV in einem anderen Ausdruck bzw.
in GAEB XML. Jeder Test prüft zusätzlich, dass der erwartete Text wörtlich auf der genannten Seite steht.

Aufruf aus der Projektwurzel (uv-Befehl siehe AGENTS.md):
  python src/test_parser_pdf.py data/raw
Exit-Code 0 = alle Tests bestanden. Schreibt nichts.
"""
import re
import sys
from pathlib import Path

import pdfplumber
from lxml import etree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lv_parser import norm_unit, parse                                        # noqa: E402
from pruefung_widerspruch import normalisiere_oz, normalisiere_leerzeichen as n  # noqa: E402

D = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/raw")
ergebnisse = []
_cache, _seiten = {}, {}


def check(name, ok, detail=""):
    ergebnisse.append(ok)
    print(f"{'OK    ' if ok else 'FEHLER'} {name}" + (f" – {detail}" if detail and not ok else ""))


def pos(datei, oz):
    if datei not in _cache:
        df = parse(D / datei)
        _cache[datei] = df[df.typ == "Position"]
    p = _cache[datei]
    return p[p.oz == oz].iloc[0]


def seite(datei, nr):
    """Seitentext des Originals (Leerzeichen-Zeichen entfernt, Leerraum zusammengefasst)."""
    if (datei, nr) not in _seiten:
        with pdfplumber.open(str(D / datei)) as pdf:
            pg = pdf.pages[nr - 1]
            fp = pg.filter(lambda o: not (o.get("object_type") == "char" and o.get("text", "").isspace()))
            _seiten[(datei, nr)] = n(fp.extract_text(layout=True, x_tolerance=1.5) or "")
    return _seiten[(datei, nr)]


def im_original(datei, nr, text):
    return n(text) in seite(datei, nr)


A, L = "Angebot AN24-0305.pdf", "Leistungsverzeichnis.pdf"


def test_angebot():
    """Angebot (Menge in der OZ-Zeile): eingerückter Text = Kurztext, kein Langtext gedruckt."""
    r = pos(A, "1.1.140")
    k = "Vorhandene Wurzelstöcke ausbauen, laden, abfahren und entsorgen"
    check("Angebot 1.1.140: Kurztext über zwei Zeilen (S. 2) vollständig, kein eigener Langtext",
          r.kurztext == k and r.langtext == k and im_original(A, 2, k), f"{r.kurztext!r} / {r.langtext!r}")
    r = pos(A, "1.1.100")
    check("Angebot 1.1.100: Fußzeile mit Bankdaten (S. 1) nicht im Langtext",
          "IBAN" not in r.langtext and r.langtext == "Ortsfesten Schutzzaun (h = 2,00 m)"
          and im_original(A, 1, "Sparkasse Dillingen IBAN"), r.langtext[:80])
    r = pos(A, "1.1.170")
    check("Angebot 1.1.170: „Zusammenstellung Bereich 1.“ (S. 2) nicht im Langtext",
          "Zusammenstellung" not in r.langtext and im_original(A, 2, "Zusammenstellung Bereich 1."), r.langtext)
    r = pos(A, "7.1.80")
    check("Angebot 7.1.80: „Hinweistext Verrechnungssätze …“ (S. 25) nicht im Langtext",
          "Hinweistext" not in r.langtext and im_original(A, 25, "Hinweistext Verrechnungssätze"), r.langtext)
    r = pos(A, "7.1.250")
    check("Angebot 7.1.250: Gesamtzusammenstellung und Mehrwertsteuer nicht im Langtext",
          r.langtext == "wie vor, jedoch Kies 16/32", r.langtext)
    p = _cache[A]
    check("Angebot: keine Position mit eigenem Langtext (Langtext = Kurztext)",
          all(x.langtext == x.kurztext for x in p.itertuples()))


def test_kurztext_umbruch():
    """Leistungsverzeichnis.pdf: Kurztext in Schrift F1, Langtext F2 (am Original geprüft)."""
    r = pos(L, "2.1.410")
    k = "wie vor, jedoch Längskreuzung Wasserleitung > DN 50 bis DN 300"
    check("LV 2.1.410: „bis DN 300“ gehört zum Kurztext (S. 15, zweite Zeile in F1)",
          r.kurztext == k and im_original(L, 15, k), r.kurztext)
    r = pos(L, "1.1.140")
    check("LV 1.1.140: Kurztext zwei Zeilen, Langtext beginnt danach mit „Durchmesser 20 - 50 cm“",
          r.kurztext == "Vorhandene Wurzelstöcke ausbauen, laden, abfahren und entsorgen"
          and r.langtext.startswith(r.kurztext + " Durchmesser 20 - 50 cm"), r.langtext[:120])
    r = pos(L, "2.1.430")
    check("LV 2.1.430: Überschrift „Hinweis:“ (F1) bleibt im Langtext, nicht im Kurztext",
          r.kurztext.endswith("ausbauen und fachgerecht entsorgen") and "Hinweis:" in r.langtext, r.kurztext)
    r = pos(L, "3.2.390")
    check("LV 3.2.390: Zeile mit Platzhalter „[PERSON_017] MDP 16 …“ (Langtext) nicht an den Kurztext gehängt",
          r.kurztext == "[PERSON_017] DN 100 weich-dichtend", r.kurztext)
    # dieselbe LV in zwei Ausdrucken: Angebot druckt nur Kurztexte
    a = {x.oz: x.kurztext for x in _cache[A].itertuples()}
    l = {x.oz: x.kurztext for x in _cache[L].itertuples()}
    abw = sorted(o for o in a if a[o] != l.get(o))
    # bekannt (Regressionsschutz, Stand nach B1p): die zweite Kurztext-Zeile beginnt mit einem Platzhalter
    # (Schrift am Original unbekannt, L45)
    bekannt = ["2.1.70", "5.3.30"]
    check(f"Kurztext Angebot = Leistungsverzeichnis.pdf in {len(a) - len(abw)} von {len(a)} (vor B1p 246); "
          f"Abweichungen nur {bekannt}", abw == bekannt, str(abw))


def test_gegen_gaeb():
    """PDF-Kurztext gegen den Kurztext derselben LV in GAEB XML (Original). Die Schwellen sind
    Regressionsschutz, abgelesen am Stand nach B1p (nicht aus dem Original abgeleitet)."""
    for xml, pdf, mind, vorher in (("[NUMMER_001]_leer.X83", "Leistungsverzeichnis_leer.pdf", 233, 209),
                                   ("[NUMMER_001]_leer.X83", "Abgabe LV.pdf", 233, 209),
                                   ("8209.003_Leistungsverzeichnis_leer.X83", "HEM2301-2_Gesamt-LV.pdf", 116, 117)):
        g = parse(D / xml)
        g = {normalisiere_oz(o): n(k) for o, k in zip(g[g.typ == "Position"].oz, g[g.typ == "Position"].kurztext)}
        d = parse(D / pdf)
        d = {normalisiere_oz(o): n(k) for o, k in zip(d[d.typ == "Position"].oz, d[d.typ == "Position"].kurztext)}
        gleich = sum(d[o] == g[o] for o in d if o in g)
        check(f"{pdf}: Kurztext gleich GAEB XML in mindestens {mind} Positionen (vor B1p {vorher})",
              gleich >= mind, str(gleich))
    # bekannte Abweichung: HEM 03.02.1 – fette Langtext-Überschrift nach Kurztext mit Platzhalter
    r = pos("HEM2301-2_Gesamt-LV.pdf", "03.02.1")
    check("HEM 03.02.1: bekannte Abweichung (Kurztext enthält die fette erste Langtext-Zeile)",
          r.kurztext.startswith("[PERSON_066] inkl. Verdichtereinheit Hochleistung-"), r.kurztext)


def test_schluss_und_kopf():
    r = pos("LV_02_PVC_Fussbodenbelag.pdf", "14.1.130")
    check("LV_02 14.1.130: Schluss „Zuzüglich der gesetzlichen Mehrwertsteuer …“ (S. 10) nicht im Langtext",
          "Mehrwertsteuer" not in r.langtext and n(r.langtext).endswith("Vorleistung: Bodenbelag")
          and im_original("LV_02_PVC_Fussbodenbelag.pdf", 10, "Zuzüglich der gesetzlichen Mehrwertsteuer"),
          r.langtext[-60:])
    r = pos("LV_09_Porenbetondach.pdf", "9.2.21")
    check("LV_09 9.2.21: „Zusammenstellung“ (S. 4) nicht im Langtext",
          "Zusammenstellung" not in r.langtext and n(r.langtext).endswith("Querschnitt: bis 150 cm2"), r.langtext[-60:])
    r = pos("LV_01_Fertigteiltreppen.pdf", "3.2.140")
    check("LV_01 3.2.140: Kopfzeile von S. 2 (Tel./Fax, „Projekt: …“) nicht im Langtext, Text danach bleibt",
          "Tel." not in r.langtext and "Projekt:" not in r.langtext and "Auftritt: ca. 27,50 cm" in r.langtext
          and im_original("LV_01_Fertigteiltreppen.pdf", 2, "Projekt: 79-222"), r.langtext[-120:])
    for f, oz in (("LV_15_Abdichtung_Aussenwaende.pdf", "1.1.20"), ("LV_15a_Abdichtung_Bodenplatte_Buero.pdf", "1.1.20")):
        r = pos(f, oz)
        check(f"{f[:6]} {oz}: weder Kopfzeile noch Schluss im Langtext",
              not re.search(r"Tel\.|Projekt:|Mehrwertsteuer|Unterschrift", r.langtext), r.langtext[-80:])


MENGE_FORM = re.compile(r"^\s*(\d{1,3}(?:\.\d{3})*,\d{3})(?:\s+([^\s.]{1,10}\.?))?\s+\.{5,}")
OZ_DOPPEL = re.compile(r"^\s*(\d+\.\d+\.\.\d+)\s")


def lv13_aus_original():
    """B1p3: OZ „a.b..c“ mit Menge und Einheit, nur aus dem Seitentext (ohne parse()); dazu alle Mengenzeilen."""
    paare, mengen, offen = {}, 0, None
    with pdfplumber.open(str(D / "LV_13_ELT.pdf")) as pdf:
        for pg in pdf.pages:
            fp = pg.filter(lambda o: not (o.get("object_type") == "char" and o.get("text", "").isspace()))
            for z in (fp.extract_text(layout=True, x_tolerance=1.5) or "").split("\n"):
                o, q = OZ_DOPPEL.match(z), MENGE_FORM.match(z)
                if o:
                    offen = o.group(1)
                elif q:
                    mengen += 1
                    if offen:
                        paare[offen] = (float(q.group(1).replace(".", "").replace(",", ".")), norm_unit(q.group(2) or ""))
                        offen = None
    return paare, mengen


def test_lv13_fehlende_positionen():
    """B1p3 (F2, 00:20): OZ „1.2..2“ und Mengenzeilen ohne Einheit. Erwartung aus dem Seitentext des Originals."""
    paare, mengen = lv13_aus_original()
    check("LV_13 Original: 56 OZ der Form a.b..c, 191 Mengenzeilen", len(paare) == 56 and mengen == 191,
          f"{len(paare)} / {mengen}")
    df = parse(D / "LV_13_ELT.pdf")
    p = df[df.typ == "Position"]
    check("LV_13: Positionen = Mengenzeilen im Original (191)", len(p) == mengen, str(len(p)))
    ist = {x.oz: (x.menge, x.einheit or "") for x in p.itertuples() if ".." in x.oz}
    abw = [o for o in paare if ist.get(o) != paare[o]]
    check("LV_13: alle 56 OZ a.b..c mit Menge und Einheit wie im Original", not abw and len(ist) == 56, str(abw[:5]))
    check("LV_13: 1.2, 2.1, 2.7 sind keine Positionen mehr", not set(p.oz) & {"1.2", "2.1", "2.7"})
    leer = [o for o, w in ist.items() if o.startswith("2.6..") and w[1] == ""]
    check("LV_13: 2.6..1–8 als Positionen mit leerer Einheit (S. 49/50)", len(leer) == 8, str(leer))
    r = pos("LV_13_ELT.pdf", "1.2..2")
    check("LV_13 1.2..2: Kurztext, 2,000 St (S. 2), kein Text der Nachbarposition",
          r.kurztext == "Schaltschranksockel 4-feldrig, 100 x 1050 x 350" and r.menge == 2.0 and r.einheit == "St"
          and "Standschrank" not in r.langtext and im_original("LV_13_ELT.pdf", 2, r.kurztext), f"{r.kurztext!r} {r.menge}")
    norm = [normalisiere_oz(o) for o in p.oz]
    check("LV_13: normalisierte OZ eindeutig (kein falscher Nr.-4-Fund)", len(norm) == len(set(norm)))
    for datei, oz, menge in (("LV_00_Roh_und_Erdauarbeiten.pdf", "1.4.7", 1.0), ("LV_21_Natursteinarbeiten.pdf", "13.4.210", 0.0)):
        r = pos(datei, oz)
        check(f"{datei[:5]} {oz}: Mengenzeile ohne Einheit ergibt eine Position", r.menge == menge and not r.einheit,
              f"{r.menge} {r.einheit!r}")


X83 = "[NUMMER_001]_leer.X83"
ohne_raum = lambda s: re.sub(r"\s", "", s or "")


def unterbeschreibungen_x83():
    """B1p3: {normalisierte OZ: [(Kurztext, Langtext) je SubDescr]}, direkt aus dem X83 (ohne parse())."""
    ln = lambda e: etree.QName(e).localname if isinstance(e.tag, str) else ""
    def text(el, name):
        return " ".join(" ".join(x.itertext()) for x in el.iter() if ln(x) == name)
    aus = {}
    for it in etree.parse(str(D / X83)).iter():
        if ln(it) != "Item":
            continue
        teile = [e.get("RNoPart") for e in it.iterancestors() if ln(e) == "BoQCtgy"][::-1] + [it.get("RNoPart")]
        for s in it:
            if ln(s) == "SubDescr":
                aus.setdefault(normalisiere_oz(".".join(teile)), []).append((text(s, "OutlTxt"), text(s, "DetailTxt")))
    return aus


def kerne(text):
    """Text ohne Platzhalter und ohne das Wort direkt daneben: Die Anonymisierung hat in PDF und GAEB 90 an diesen
    Stellen Satzzeichen oder ein Wort anders ersetzt (X83 „[PERSON_044], max.“, PDF „[PERSON_044] max.“; R9)."""
    teile = re.split(r"\[[^\]]*\]", text)
    aus = []
    for i, t in enumerate(teile):
        w = t.split()
        w = w[1:] if i > 0 else w
        w = w[:-1] if i < len(teile) - 1 else w
        if w:
            aus.append("".join(w))
    return aus


def endet_mit(langtext, texte):
    """True, wenn der Langtext (ohne Leerraum) mit allen Kernen der Texte in dieser Reihenfolge endet."""
    t, ende, erster = ohne_raum(langtext), None, True
    ende = len(t)
    for k in reversed([k for x in texte for k in kerne(x)]):
        i = t.rfind(k, 0, ende)
        if i < 0 or (erster and i + len(k) != len(t)):
            return False
        ende, erster = i, False
    return True


def marker_im_pdf(datei):
    with pdfplumber.open(str(D / datei)) as pdf:
        return sum(len(re.findall(r"^\s*Unterbeschreibung \d+:\s*$", p.extract_text(layout=True, x_tolerance=1.5) or "", re.M))
                   for p in pdf.pages)


def test_unterbeschreibungen():
    """B1p3 (F1, 00:20): Unterbeschreibung hinter der Mengenzeile bleibt Teil der Position (Erwartung aus dem X83)."""
    soll = unterbeschreibungen_x83()
    check("X83 Original: 13 Positionen mit 16 Unterbeschreibungen", len(soll) == 13 and sum(map(len, soll.values())) == 16)
    for datei in ("Abgabe LV.pdf", "Leistungsverzeichnis_leer.pdf"):
        check(f"{datei}: 16 Zeilen „Unterbeschreibung N:“ im Original", marker_im_pdf(datei) == 16, str(marker_im_pdf(datei)))
        df = parse(D / datei)
        p = {normalisiere_oz(x.oz): x for x in df[df.typ == "Position"].itertuples()}
        abw = [o for o, t in soll.items() if not endet_mit(p[o].langtext, [x for paar in t for x in paar])]
        check(f"{datei}: alle 13 Positionen enden mit dem Text ihrer Unterbeschreibungen laut X83", not abw, str(abw))
        for o in ("7.1.5", "7.1.6", "9.1.5"):
            r = p[o]
            check(f"{datei} {o}: Unterbeschreibung enthalten, Marker und fremde Einleitung nicht",
                  endet_mit(r.langtext, [x for paar in soll[o] for x in paar]) and "Unterbeschreibung" not in r.langtext
                  and "Leitbeschreibung" not in r.langtext and "Gemäß [" not in r.langtext, r.langtext[-90:])
    g = parse(D / X83)
    g = {normalisiere_oz(x.oz): x for x in g[g.typ == "Position"].itertuples()}
    abw = [o for o, t in soll.items()
           if not ohne_raum(g[o].langtext).endswith("".join(ohne_raum(x) for paar in t for x in paar))]
    check("GAEB XML: SubDescr-Texte aller 13 Positionen wörtlich am Ende des Langtexts", not abw, str(abw))
    d = parse(D / "StBALV23040.D86")
    d = {normalisiere_oz(x.oz): x.langtext for x in d[d.typ == "Position"].itertuples()}
    abw = [o for o, t in soll.items() if not endet_mit(d.get(o, ""), [paar[1] for paar in t])]
    check("GAEB 90 (D86): Langtexte der Unterbeschreibungen am Ende des Langtexts", not abw, str(abw))


def test_einheiten_b1p3():
    """B1p3 (L53, angenommen vorbehaltlich Team): Einheiten „pau“ und „Set“; Erwartung aus dem Seitentext."""
    for datei, seite_nr, oz, kurz in (("LV_04_Porenbetonfassade.pdf", 1, "9.1.10", "Maßnahmen zur Arbeitssicherheit gem. UVV"),
                                      ("LV_09_Porenbetondach.pdf", 1, "9.2.0", "Baustelleneinrichtung")):
        r = pos(datei, oz)
        check(f"{datei[:5]} {oz}: „1,000 pau“ (S. {seite_nr}) ist Position, Einheit psch, Roh-Einheit wie gedruckt",
              r.menge == 1.0 and r.einheit == "psch" and r.einheit_roh == "pau" and r.kurztext == kurz
              and im_original(datei, seite_nr, "1,000 pau"), f"{r.menge} {r.einheit} {r.kurztext!r}")
    for datei, n_soll in (("LV_04_Porenbetonfassade.pdf", 20), ("LV_09_Porenbetondach.pdf", 15), ("LV_14a_Betonkernaktivierung.pdf", 36)):
        anz = int((parse(D / datei).typ == "Position").sum())
        check(f"{datei[:6]}: {n_soll} Positionen", anz == n_soll, str(anz))
    for oz, seite_nr in ((".14", 8), (".25", 12)):
        r = pos("LV_14a_Betonkernaktivierung.pdf", oz)
        check(f"LV_14a {oz}: „8,000 Set“ bzw. Menge laut S. {seite_nr}, Einheit Set",
              r.einheit == "Set" and im_original("LV_14a_Betonkernaktivierung.pdf", seite_nr, f"{str(r.menge).split('.')[0]},000 Set"),
              f"{r.menge} {r.einheit}")


def test_fremder_text():
    """B1p3 (F1, 00:20): Text hinter der Mengenzeile, der nicht zur Position gehört, endet an der Positionsgrenze."""
    H, V, AU = "HEM2301-2_Gesamt-LV.pdf", "Leistungsverzeichnis_leer.pdf", "LV-Ausdruck-[PROJEKT_004].pdf"
    r = pos(H, "06.01.4")
    check("HEM 06.01.4 (S. 116): endet mit „liefern und montieren“, Spezifikation dahinter nicht im Langtext",
          n(r.langtext).endswith("liefern und montieren") and "Soweit möglich" not in r.langtext
          and im_original(H, 116, "Soweit möglich, werden im Bestand verbaute Armaturen"), r.langtext[-70:])
    r = pos(H, "06.01.6")
    check("HEM 06.01.6 (S. 117): endet mit „Gewicht ca. 55 kg“, Spezifikation Absperrklappe nicht im Langtext",
          n(r.langtext).endswith("Gewicht ca. 55 kg") and "Weichdichtende" not in r.langtext
          and im_original(H, 117, "Spezifikation Absperrklappe Zwischenflanschausführung"), r.langtext[-70:])
    r = pos(V, "3.1.8")
    check("Leistungsverzeichnis_leer 3.1.8 (S. 18/19): endet an der Mengenzeile, Abfallentsorgung nicht im Langtext",
          n(r.langtext).endswith("an der Entnahmestelle.") and "Standardbeschreibung" not in r.langtext
          and im_original(V, 19, "Standardbeschreibung Gebühren Entsorgung AN"), r.langtext[-70:])
    r = pos(AU, "04.0003")
    check("LV-Ausdruck 04.0003 (S. 20): Vorbemerkung Geräte und Fahrzeuge nicht im Langtext",
          "Vorbemerkung" not in r.langtext and "Verrechnungssatz" not in r.langtext
          and im_original(AU, 20, "Vorbemerkung Geräte und Fahrzeuge:"), r.langtext[-70:])
    r = pos("Abgabe LV.pdf", "3.2.3")
    check("Abgabe LV 3.2.3 (S. 34): Marker „*** Bezugsbeschreibung“ der Folgeposition nicht im Langtext",
          "***" not in r.langtext, r.langtext[-60:])
    r = pos("Abgabe LV.pdf", "7.1.1")
    check("Abgabe LV 7.1.1 (S. 63): Einleitung der Folgeposition nicht im Langtext",
          "Leitbeschreibung" not in r.langtext and "Gemäß [" not in r.langtext, r.langtext[-60:])
    # Bedingung F1 (00:20): je mindestens 3 Positionen aus beiden PDFs; fremder Text steht im Original hinter der Position
    for datei in ("Abgabe LV.pdf", V):
        for oz, fremd in (("3.1.8", "Standardbeschreibung Gebühren Entsorgung AN"), ("3.2.3", "*** Bezugsbeschreibung"),
                          ("7.1.1", "Leitbeschreibung:"), ("7.1.4", "Leitbeschreibung:")):
            r = pos(datei, oz)
            s = int(r.seite)
            check(f"{datei} {oz} (S. {s}): „{fremd}“ steht im Original dahinter, nicht im Langtext",
                  n(fremd) not in n(r.langtext) and "Gemäß [" not in r.langtext
                  and (im_original(datei, s, fremd) or im_original(datei, s + 1, fremd)), r.langtext[-70:])
    r = pos(L, "5.3.200")
    check("Leistungsverzeichnis 5.3.200 (S. 63): Hinweis für Rohrhalterungen nicht im Langtext",
          "Gewichtsbelastungen" not in r.langtext and im_original(L, 63, "Hinweis für Rohrhalterungen"), r.langtext[-60:])
    r = pos("LV_00_Roh_und_Erdauarbeiten.pdf", "2.2.75")
    check("LV_00 2.2.75 (S. 14): Abschnittstitel dahinter nicht im Langtext", "BODENAUSTAUSCH" not in r.langtext,
          r.langtext[-60:])


def main():
    test_angebot()
    test_kurztext_umbruch()
    test_gegen_gaeb()
    test_schluss_und_kopf()
    test_lv13_fehlende_positionen()
    test_unterbeschreibungen()
    test_fremder_text()
    test_einheiten_b1p3()
    print(f"\n{sum(ergebnisse)}/{len(ergebnisse)} Tests bestanden")
    return 0 if all(ergebnisse) else 1


if __name__ == "__main__":
    sys.exit(main())
