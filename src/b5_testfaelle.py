"""
b5_testfaelle.py - Block B5-Vorbereitung (Sitzung B2, Team 21.11.2026, 19:55): erfundene Testfälle für die KI-Prüfungen
„Tippfehler“ und „Widerspruch zwischen Positionen“. Keine KI-Aufrufe hier; die Läufe führt Sitzung B1 aus.

E12 (3): Alle Fälle sind **erfunden** (Texte nach dem Muster der LV-Sprache, keine Zeile aus data/raw, kein Goldstandard).
Prompts dürfen an diesen Fällen entwickelt werden; gemessen wird danach getrennt an echten Funden.
R9: Anonymisierungsplatzhalter („[PERSON_115]“, verstümmelt „[P,ERSON_132]“, Ordnungszahl „TE.L0.0009“) sind keine
Tippfehler; sie stehen deshalb in negativen Fällen.

Aufbau je Fall: id, pruefung („tippfehler“ | „widerspruch“), erwartet („Fund“ | „kein Fund“), positionen
[{oz, kurztext, langtext, menge, einheit}], bei „Fund“ das erwartete wörtliche Zitat (zitat bzw. zitat_a/zitat_b mit
oz_a/oz_b) und eine Begründung des Falls. Prompt-Entwurf und Ausgabeschema: docs/b5_prompt_entwurf.md.

Aufruf (Eigenprüfung der Fälle):  python src/b5_testfaelle.py   → Exit-Code 0, wenn alle Fälle wohlgeformt sind.
"""
import json
import re
import sys

ERFUNDEN = "erfunden (Sitzung B2, 21.11.2026), nicht aus data/raw"
PROMPT_ENTWURF = "B5-Entwurf-v0"
TIPPFEHLER_BEFUNDE = ["Tippfehler", "kein Tippfehler", "unklar"]
WIDERSPRUCH_EINORDNUNGEN = ["echter Widerspruch", "gewollt verschieden", "unklar"]


def _p(oz, kurz, lang="", menge=1.0, einheit="St"):
    return {"oz": oz, "kurztext": kurz, "langtext": lang or kurz, "menge": menge, "einheit": einheit}


TIPPFEHLER = [
    # positiv: genau ein Tippfehler, Zitat = das falsche Wort
    {"id": "T+01", "erwartet": "Fund", "zitat": "Bewehrrung",
     "positionen": [_p("1.1", "Bewehrrung B500A liefern", "Bewehrrung B500A als Matten liefern und verlegen.", 2.5, "t")],
     "fall": "doppeltes r"},
    {"id": "T+02", "erwartet": "Fund", "zitat": "Abdichtug",
     "positionen": [_p("1.2", "Abdichtug Bodenplatte", "Abdichtug der Bodenplatte mit Bitumenbahn, zweilagig.", 120, "m²")],
     "fall": "fehlendes n"},
    {"id": "T+03", "erwartet": "Fund", "zitat": "verlgen",
     "positionen": [_p("1.3", "PE-HD-Rohr DN 150", "PE-HD-Rohr DN 150 liefern und im Rohrgraben verlgen.", 80, "m")],
     "fall": "fehlendes e"},
    {"id": "T+04", "erwartet": "Fund", "zitat": "Einzelfundamnet",
     "positionen": [_p("1.4", "Einzelfundamnet C25/30", "Einzelfundamnet aus Ortbeton C25/30 herstellen.", 6, "m³")],
     "fall": "vertauschte Buchstaben"},
    {"id": "T+05", "erwartet": "Fund", "zitat": "Mauerwrek",
     "positionen": [_p("1.5", "Mauerwrek KS 17,5 cm", "Mauerwrek aus Kalksandstein, d = 17,5 cm.", 45, "m²")],
     "fall": "vertauschte Buchstaben"},
    {"id": "T+06", "erwartet": "Fund", "zitat": "Estirch",
     "positionen": [_p("1.6", "Zementestrich CT-C25-F4", "Estirch als schwimmender Estrich, d = 50 mm.", 300, "m²")],
     "fall": "Tippfehler im Langtext, Kurztext richtig"},
    {"id": "T+07", "erwartet": "Fund", "zitat": "Schachtabdekcung",
     "positionen": [_p("1.7", "Schachtabdekcung D400", "Schachtabdekcung Klasse D 400 liefern und einbauen.", 4, "St")],
     "fall": "vertauschte Buchstaben"},
    {"id": "T+08", "erwartet": "Fund", "zitat": "Pflastersteinne",
     "positionen": [_p("1.8", "Betonpflaster 8 cm", "Pflastersteinne aus Beton, 8 cm, in Splittbett verlegen.", 210, "m²")],
     "fall": "doppeltes n"},
    # negativ: kein Tippfehler
    {"id": "T-01", "erwartet": "kein Fund",
     "positionen": [_p("2.1", "Wartung durch [PERSON_115]", "Einweisung durch [PERSON_115] vor Ort.", 1, "psch")],
     "fall": "Anonymisierungsplatzhalter (R9)"},
    {"id": "T-02", "erwartet": "kein Fund",
     "positionen": [_p("2.2", "Ansprechpartner [P,ERSON_132]", "Abstimmung mit [P,ERSON_132] vor Baubeginn.", 1, "psch")],
     "fall": "verstümmelter Platzhalter (R9)"},
    {"id": "T-03", "erwartet": "kein Fund",
     "positionen": [_p("TE.L0.0009", "Telefonanschluss Baustelle", "Telefonanschluss TEL00009 einrichten.", 1, "St")],
     "fall": "anonymisierte Ordnungszahl (R9)"},
    {"id": "T-04", "erwartet": "kein Fund",
     "positionen": [_p("2.4", "GGG-Rohr DN 300 o.glw.", "Duktiles Gussrohr GGG DN 300, BRS, o.glw.", 60, "m")],
     "fall": "Fachabkürzungen (GGG, BRS, o.glw.)"},
    {"id": "T-05", "erwartet": "kein Fund",
     "positionen": [_p("2.5", "Zul.Deckenschalung,SB2", "Zul. f. Deckenschalung SB 2, Bkl. 3-5.", 1, "m²")],
     "fall": "Abkürzungen ohne Leerzeichen (Zul., SB2, Bkl.)"},
    {"id": "T-06", "erwartet": "kein Fund",
     "positionen": [_p("2.6", "Fussbodenaufbau", "Fussbodenaufbau gemäß Detail, Fußleiste separat.", 90, "m²")],
     "fall": "Schreibvarianten ss/ß im selben Text"},
    {"id": "T-07", "erwartet": "kein Fund",
     "positionen": [_p("2.7", "Stb.-Wand C30/37 XC4 XF1", "Stb.-Wand C30/37, XC4, XF1, WU, d = 30 cm.", 25, "m³")],
     "fall": "Expositionsklassen und Kurzzeichen"},
    {"id": "T-08", "erwartet": "kein Fund",
     "positionen": [_p("2.8", "KG-Rohr DN 110 SN8", "KG2000 SN 8 DN/OD 110, Steckmuffe, liefern.", 35, "m")],
     "fall": "Produkt- und Normkürzel (KG2000, SN 8, DN/OD)"},
]

WIDERSPRUCH = [
    # positiv: zwei Positionen widersprechen sich zu derselben Leistung
    {"id": "W+01", "erwartet": "Fund", "oz_a": "0.1", "oz_b": "1.2", "zitat_a": "alle Rohre in PE-HD SDR 11",
     "zitat_b": "PVC-U-Rohr DN 150",
     "positionen": [_p("0.1", "Vorbemerkung Rohrleitungen", "Material: alle Rohre in PE-HD SDR 11.", 1, "psch"),
                    _p("1.2", "PVC-U-Rohr DN 150", "PVC-U-Rohr DN 150 im Rohrgraben verlegen.", 80, "m")],
     "fall": "Vorbemerkung vs. Position, Material"},
    {"id": "W+02", "erwartet": "Fund", "oz_a": "0.2", "oz_b": "2.1", "zitat_a": "Fundamente in C30/37",
     "zitat_b": "Streifenfundament C20/25",
     "positionen": [_p("0.2", "Vorbemerkung Beton", "Sämtliche Fundamente in C30/37, XC2.", 1, "psch"),
                    _p("2.1", "Streifenfundament C20/25", "Streifenfundament C20/25 herstellen.", 12, "m³")],
     "fall": "Vorbemerkung vs. Position, Betonklasse"},
    {"id": "W+03", "erwartet": "Fund", "oz_a": "3.1", "oz_b": "3.2", "zitat_a": "Bordstein Hochbord 15/30",
     "zitat_b": "Zulage Rundbord zu Pos. 3.1",
     "positionen": [_p("3.1", "Bordstein Hochbord 15/30", "Bordstein Hochbord 15/30 setzen.", 120, "m"),
                    _p("3.2", "Zulage Rundbord zu Pos. 3.1", "Zulage Rundbord zu Pos. 3.1.", 150, "m")],
     "fall": "Zulage-Menge größer als Grundposition"},
    {"id": "W+04", "erwartet": "Fund", "oz_a": "0.3", "oz_b": "4.1", "zitat_a": "Türen in RAL 7016",
     "zitat_b": "Innentür RAL 9010",
     "positionen": [_p("0.3", "Vorbemerkung Türen", "Alle Türen in RAL 7016 beschichtet.", 1, "psch"),
                    _p("4.1", "Innentür RAL 9010", "Innentür 88,5/213, Oberfläche RAL 9010.", 6, "St")],
     "fall": "Farbe Vorbemerkung vs. Position"},
    {"id": "W+05", "erwartet": "Fund", "oz_a": "5.1", "oz_b": "5.2", "zitat_a": "Boden lösen, laden, 100 m³",
     "zitat_b": "Abfuhr 200 m³",
     "positionen": [_p("5.1", "Aushub Baugrube", "Boden lösen, laden, 100 m³ laut Massenermittlung.", 100, "m³"),
                    _p("5.2", "Abfuhr Aushub", "Abfuhr 200 m³ des Aushubs aus Pos. 5.1.", 200, "m³")],
     "fall": "Abfuhr der Aushubmenge doppelt so groß"},
    {"id": "W+06", "erwartet": "Fund", "oz_a": "0.4", "oz_b": "6.1", "zitat_a": "Aushub nur in Handschachtung",
     "zitat_b": "Grabenaushub maschinell",
     "positionen": [_p("0.4", "Vorbemerkung Leitungszone", "Im Bereich der Gasleitung Aushub nur in Handschachtung.", 1, "psch"),
                    _p("6.1", "Grabenaushub maschinell", "Grabenaushub maschinell an der Gasleitung.", 40, "m³")],
     "fall": "Ausführungsart widerspricht Vorbemerkung"},
    {"id": "W+07", "erwartet": "Fund", "oz_a": "7.1", "oz_b": "7.2", "zitat_a": "Schacht DN 1000",
     "zitat_b": "Schachtabdeckung DN 625 für Schacht DN 800",
     "positionen": [_p("7.1", "Schacht DN 1000", "Schacht DN 1000, Tiefe 2,5 m.", 1, "St"),
                    _p("7.2", "Schachtabdeckung zu 7.1", "Schachtabdeckung DN 625 für Schacht DN 800 aus Pos. 7.1.", 1, "St")],
     "fall": "Bezug nennt anderen Durchmesser"},
    {"id": "W+08", "erwartet": "Fund", "oz_a": "8.1", "oz_b": "8.2", "zitat_a": "Abdichtung nach DIN 18533, W2.1-E",
     "zitat_b": "W1-E",
     "positionen": [_p("8.1", "Abdichtung Kellerwand", "Abdichtung nach DIN 18533, W2.1-E (drückendes Wasser).", 80, "m²"),
                    _p("8.2", "Abdichtung Kellerwand Hohlkehle", "Hohlkehle zur Abdichtung aus 8.1, W1-E.", 30, "m")],
     "fall": "Wassereinwirkungsklasse unterschiedlich für dieselbe Abdichtung"},
    # negativ: gewollt verschieden oder kein Bezug
    {"id": "W-01", "erwartet": "kein Fund",
     "positionen": [_p("1.1", "Hausanschluss DN 150", "Hausanschlussleitung DN 150.", 20, "m"),
                    _p("1.2", "Hauptleitung DN 300", "Hauptleitung DN 300.", 200, "m")],
     "fall": "verschiedene Bauteile mit eigenen Nennweiten"},
    {"id": "W-02", "erwartet": "kein Fund",
     "positionen": [_p("2.1", "Fundament C25/30", "Fundament C25/30, sofern nicht anders angegeben.", 10, "m³"),
                    _p("2.2", "Wand C30/37", "Außenwand C30/37 WU.", 20, "m³")],
     "fall": "verschiedene Bauteile, Betonklasse je Bauteil"},
    {"id": "W-03", "erwartet": "kein Fund",
     "positionen": [_p("3.1", "Rohr DN 150", "PE-HD-Rohr DN 150 verlegen.", 50, "m"),
                    _p("3.2", "wie vor, jedoch DN 200", "wie vor, jedoch DN 200.", 30, "m")],
     "fall": "gewollte Abweichung „wie vor, jedoch“"},
    {"id": "W-04", "erwartet": "kein Fund",
     "positionen": [_p("4.1", "Pflaster grau", "Betonpflaster grau.", 100, "m²"),
                    _p("4.2", "Pflaster anthrazit, Alternativposition", "Alternativposition zu 4.1: Pflaster anthrazit.", 100, "m²")],
     "fall": "Alternativposition"},
    {"id": "W-05", "erwartet": "kein Fund",
     "positionen": [_p("5.1", "Bordstein Hochbord", "Hochbord 15/30.", 120, "m"),
                    _p("5.2", "Zulage Rundbord zu Pos. 5.1", "Zulage Rundbord zu Pos. 5.1.", 20, "m")],
     "fall": "Zulage-Menge kleiner als Grundposition"},
    {"id": "W-06", "erwartet": "kein Fund",
     "positionen": [_p("6.1", "Einweisung [PERSON_115]", "Einweisung durch [PERSON_115].", 1, "psch"),
                    _p("6.2", "Abnahme [PERSON_116]", "Abnahme durch [PERSON_116].", 1, "psch")],
     "fall": "verschiedene Platzhalter (R9), kein Widerspruch"},
    {"id": "W-07", "erwartet": "kein Fund",
     "positionen": [_p("7.1", "Aushub", "Boden lösen, laden, 100 m³.", 100, "m³"),
                    _p("7.2", "Abfuhr", "Abfuhr 80 m³, Rest Wiedereinbau aus Pos. 7.1.", 80, "m³")],
     "fall": "Mengen passen (Rest wird wieder eingebaut)"},
    {"id": "W-08", "erwartet": "kein Fund",
     "positionen": [_p("8.1", "Bedarfsposition Fels", "Bedarfsposition: Fels lösen.", 1, "m³"),
                    _p("8.2", "Boden lösen", "Boden der Klasse 3–5 lösen.", 400, "m³")],
     "fall": "Bedarfsposition mit Menge 1 neben Hauptposition"},
]

for f in TIPPFEHLER:
    f["pruefung"], f["quelle"] = "tippfehler", ERFUNDEN
for f in WIDERSPRUCH:
    f["pruefung"], f["quelle"] = "widerspruch", ERFUNDEN
FAELLE = TIPPFEHLER + WIDERSPRUCH
VERBOTEN = re.compile(r"Anspruch|berechtigt|durchsetzbar|§")


def _norm(t):
    return re.sub(r"\s+", " ", t or "").strip()


def _im(zitat, texte):
    return bool(zitat) and any(_norm(zitat) in _norm(t) for t in texte)


def positionstext(fall):
    """Eingabetext für den Prompt (OZ, Kurztext, Langtext, Menge, Einheit je Position)."""
    return "\n\n".join(f"OZ {p['oz']}\nKurztext: {p['kurztext']}\nLangtext: {p['langtext']}\n"
                       f"Menge: {p['menge']:g} {p['einheit']}" for p in fall["positionen"])


def bewerte_antwort(fall, antwort):
    """Bewertet eine KI-Antwort (JSON-Text oder dict) gegen den Fall. Rückgabe {gueltig, richtig, grund}.
    gültig = Schema stimmt, Zitate wörtlich, keine R7-Begriffe; richtig = Befund passt zum Erwarteten."""
    try:
        d = json.loads(antwort) if isinstance(antwort, str) else dict(antwort)
    except (json.JSONDecodeError, TypeError, ValueError):
        return {"gueltig": False, "richtig": False, "grund": "kein JSON"}
    texte = [t for p in fall["positionen"] for t in (p["kurztext"], p["langtext"])]
    if VERBOTEN.search(json.dumps(d, ensure_ascii=False)):
        return {"gueltig": False, "richtig": False, "grund": "R7"}
    if fall["pruefung"] == "tippfehler":
        if d.get("befund") not in TIPPFEHLER_BEFUNDE:
            return {"gueltig": False, "richtig": False, "grund": "befund unbekannt"}
        if d["befund"] == "Tippfehler" and not _im(d.get("zitat"), texte):
            return {"gueltig": False, "richtig": False, "grund": "Zitat nicht wörtlich"}
        fund = d["befund"] == "Tippfehler"
        richtig = (fund and _norm(d["zitat"]) == _norm(fall["zitat"])) if fall["erwartet"] == "Fund" else not fund
        return {"gueltig": True, "richtig": richtig, "grund": d["befund"]}
    if d.get("einordnung") not in WIDERSPRUCH_EINORDNUNGEN:
        return {"gueltig": False, "richtig": False, "grund": "einordnung unbekannt"}
    if d["einordnung"] == "echter Widerspruch" and not (_im(d.get("zitat_a"), texte) and _im(d.get("zitat_b"), texte)):
        return {"gueltig": False, "richtig": False, "grund": "Zitat nicht wörtlich"}
    fund = d["einordnung"] == "echter Widerspruch"
    richtig = (fund and {d.get("oz_a"), d.get("oz_b")} == {fall["oz_a"], fall["oz_b"]}) \
        if fall["erwartet"] == "Fund" else not fund
    return {"gueltig": True, "richtig": richtig, "grund": d["einordnung"]}


def eigenpruefung():
    """Liste von Fehlern im Fallbestand (leer = in Ordnung)."""
    fehler = []
    ids = [f["id"] for f in FAELLE]
    if len(ids) != len(set(ids)):
        fehler.append("doppelte id")
    for name, liste in (("tippfehler", TIPPFEHLER), ("widerspruch", WIDERSPRUCH)):
        pos = sum(f["erwartet"] == "Fund" for f in liste)
        if pos < 8 or len(liste) - pos < 8:
            fehler.append(f"{name}: {pos} positiv, {len(liste) - pos} negativ (je mindestens 8)")
    platzhalter = [f for f in FAELLE if f["erwartet"] == "kein Fund" and any(
        re.search(r"\[P,?ERSON_\d+\]|TE\.?L0\.?0+9|TEL0+9", p["kurztext"] + p["langtext"] + p["oz"]) for p in f["positionen"])]
    if len(platzhalter) < 3:
        fehler.append("zu wenige negative Fälle mit Anonymisierungsplatzhaltern (R9)")
    for f in FAELLE:
        texte = [t for p in f["positionen"] for t in (p["kurztext"], p["langtext"])]
        if f["erwartet"] == "Fund":
            for k in (("zitat",) if f["pruefung"] == "tippfehler" else ("zitat_a", "zitat_b")):
                if not _im(f.get(k), texte):
                    fehler.append(f"{f['id']}: {k} „{f.get(k)}“ steht nicht wörtlich im Fall")
            if f["pruefung"] == "widerspruch" and not {f["oz_a"], f["oz_b"]} <= {p["oz"] for p in f["positionen"]}:
                fehler.append(f"{f['id']}: oz_a/oz_b nicht im Fall")
        if f["quelle"] != ERFUNDEN:
            fehler.append(f"{f['id']}: nicht als erfunden gekennzeichnet")
    # bewerte_antwort an je einem Beispiel prüfen
    t, w = TIPPFEHLER[0], WIDERSPRUCH[0]
    beispiele = [
        (t, {"befund": "Tippfehler", "zitat": "Bewehrrung", "korrektur": "Bewehrung", "begruendung": "x"}, True, True),
        (t, {"befund": "Tippfehler", "zitat": "Bewehrrrung", "korrektur": "", "begruendung": "x"}, False, False),
        (TIPPFEHLER[8], {"befund": "Tippfehler", "zitat": "[PERSON_115]", "korrektur": "", "begruendung": "x"}, True, False),
        (w, {"einordnung": "echter Widerspruch", "oz_a": "0.1", "oz_b": "1.2", "zitat_a": "alle Rohre in PE-HD SDR 11",
             "zitat_b": "PVC-U-Rohr DN 150", "begruendung": "x", "rueckfrage": "Welches Material gilt?"}, True, True),
        (WIDERSPRUCH[8], {"einordnung": "gewollt verschieden", "begruendung": "x", "rueckfrage": ""}, True, True),
        (w, "kein json", False, False),
        (w, {"einordnung": "echter Widerspruch", "oz_a": "0.1", "oz_b": "1.2", "zitat_a": "alle Rohre in PE-HD SDR 11",
             "zitat_b": "PVC-U-Rohr DN 150", "begruendung": "Der Bieter ist berechtigt …", "rueckfrage": ""}, False, False),
    ]
    for fall, antwort, gueltig, richtig in beispiele:
        e = bewerte_antwort(fall, antwort)
        if (e["gueltig"], e["richtig"]) != (gueltig, richtig):
            fehler.append(f"bewerte_antwort {fall['id']}: {e} statt gültig={gueltig}, richtig={richtig}")
    return fehler


if __name__ == "__main__":
    f = eigenpruefung()
    for x in f:
        print("FEHLER", x)
    t_pos = sum(x["erwartet"] == "Fund" for x in TIPPFEHLER)
    w_pos = sum(x["erwartet"] == "Fund" for x in WIDERSPRUCH)
    print(f"Tippfehler: {t_pos} positiv, {len(TIPPFEHLER) - t_pos} negativ; Widerspruch: {w_pos} positiv, "
          f"{len(WIDERSPRUCH) - w_pos} negativ; {'in Ordnung' if not f else f'{len(f)} Fehler'}")
    sys.exit(0 if not f else 1)
