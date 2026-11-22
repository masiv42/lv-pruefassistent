"""
ki_b5.py - Block B5: KI-Prüfungen „Tippfehler“ und „Widerspruch zwischen Positionen“ (Team 21.11.2026, 21:20).

Grundlage: Prompt-Entwurf und erfundene Testfälle von Sitzung B2 (docs/b5_prompt_entwurf.md, src/b5_testfaelle.py).
Die Prompts sind eingefroren als B5-T1 (Tippfehler) und B5-W1 (Widerspruch zwischen Positionen), geprüft über SHA-256.

Leitplanken:
- Nur KI-Vorschläge (Kern 4, E12 (5)); die KI findet, der Code prüft gegen. Kein Regel-Fund wird verändert (E13);
  „kein Tippfehler“ bzw. „gewollt verschieden“ erzeugen einfach keinen Vorschlag.
- Zitate müssen wörtlich im Text der Position stehen (R5), sonst verworfen; Platzhalter in eckigen Klammern und
  anonymisierte Ordnungszahlen sind nie ein Tippfehler (R9, im Code verworfen); R7-Begriffe verworfen.
- Nur auf Knopfdruck je LV, höchstens MAX_AUFRUFE API-Aufrufe je Lauf; Antworten über den Cache (E14).
- Kategorie und Stufe sind ein Vorschlag (Team entscheidet): Tippfehler „Unklarheit“, Stufe 4, „nur Hinweis“;
  Widerspruch zwischen Positionen „möglicher Widerspruch“, Stufe 1, „Rückfrage stellen“.
"""
import hashlib
import json
import re
from datetime import datetime

import ki_client
from ki_client import TechnischerFehler
from ki_pruefung import (CACHE_DIR, LOG_DATEI, MAX_AUFRUFE, STATUS_GUELTIG, STATUS_UNLESBAR, STATUS_ZITAT,
                         STATUS_R7, lies_cache, schreibe_cache, schreibe_log, denkaufwand, kosten)
from pruefung_widerspruch import beleg_im_text, normalisiere_leerzeichen, dn_angaben, werte, normalisiere_oz

VERSION = {"tippfehler": "B5-T1", "widerspruch": "B5-W1"}
STATUS_R9 = "KI-Vorschlag verworfen: Platzhalter (R9)"
BEFUNDE = {"tippfehler": ["Tippfehler", "kein Tippfehler", "unklar"],
           "widerspruch": ["echter Widerspruch", "gewollt verschieden", "unklar"]}
FUND = {"tippfehler": "Tippfehler", "widerspruch": "echter Widerspruch"}
VORSCHLAG = {"tippfehler": ("Unklarheit", 4, "nur Hinweis"),
             "widerspruch": ("möglicher Widerspruch", 1, "Rückfrage stellen")}       # Vorschlag, Team entscheidet
PLATZHALTER_RE = re.compile(r"\[[^\]]*\]|TE\.?L0|TEL0")
VERBOTEN = re.compile(r"Anspruch|berechtigt|durchsetzbar|§")
MAX_PAARE = 50

PROMPT = {"tippfehler": """Du prüfst eine einzelne Position aus einem Leistungsverzeichnis (LV) auf Tippfehler, für eine kalkulierende Person eines ausführenden Unternehmens. Du entscheidest nichts; die Entscheidung trifft die kalkulierende Person.

Ein Tippfehler ist ein Wort, das erkennbar falsch geschrieben ist (fehlender, doppelter oder vertauschter Buchstabe), zum Beispiel „Bewehrrung“ statt „Bewehrung“.

Kein Tippfehler sind:
- Platzhalter in eckigen Klammern wie [PERSON_115], [NUMMER_001], [FIRMA_012], auch verstümmelt wie [P,ERSON_132], und anonymisierte Ordnungszahlen wie TEL00009 oder TE.L0.0009. Sie stammen aus der Anonymisierung.
- Fachabkürzungen und Kurzzeichen (z. B. GGG, PE-HD, KG2000, SN 8, DN/OD, Stb., Zul., Bkl., o.glw., XC4, C30/37, W2.1-E).
- Schreibvarianten wie „ss“ und „ß“ oder alte und neue Rechtschreibung.
- Produkt- und Firmennamen.

Wähle genau einen Befund:
- "Tippfehler": genau ein Wort ist erkennbar falsch geschrieben. Gibt es mehrere, nenne das erste.
- "kein Tippfehler": kein Wort ist erkennbar falsch geschrieben.
- "unklar": Du kannst es nicht sicher entscheiden.

Regeln:
1. "zitat": das falsch geschriebene Wort wörtlich, genau wie im Text, ohne Anführungszeichen. Bei "kein Tippfehler" leer "".
2. "korrektur": die vermutlich gemeinte Schreibweise, nur bei "Tippfehler", sonst "".
3. "begruendung": höchstens ein Satz, sachlich, auf Deutsch.
4. Keine Aussagen zu Ansprüchen, Vergütung, Haftung oder Vertragsauslegung. Verwende nicht die Wörter "Anspruch", "berechtigt" und "durchsetzbar" und verweise auf keine Paragraphen.
5. Nimm nichts an, was nicht im Text steht.

Antworte ausschließlich mit einem JSON-Objekt ohne weiteren Text, genau mit diesen Feldern:
{"befund": "...", "zitat": "...", "korrektur": "...", "begruendung": "..."}""",
          "widerspruch": """Du prüfst zwei Positionen (oder eine Vorbemerkung und eine Position) aus demselben Leistungsverzeichnis (LV) für eine kalkulierende Person eines ausführenden Unternehmens. Eine Regel hat sie ausgewählt, weil sie dasselbe Bauteil nennen und verschiedene Werte enthalten. Du ordnest ein, was dieser Unterschied wahrscheinlich bedeutet. Du entscheidest nichts; die Entscheidung trifft die kalkulierende Person.

Wähle genau eine Einordnung:
- "echter Widerspruch": Beide Texte beschreiben dieselbe Leistung oder dasselbe Bauteil mit unvereinbaren Angaben, zum Beispiel eine Vorbemerkung „alle Rohre in PE-HD“ und eine Position „PVC-U-Rohr“, oder eine Zulage mit größerer Menge als ihre Grundposition.
- "gewollt verschieden": nur, wenn der Text selbst den Unterschied erklärt, zum Beispiel „wie vor, jedoch DN 200“, „Alternativposition“, „sofern nicht anders angegeben“, ein ausdrücklich anderes, benanntes Bauteil oder eine Bedarfsposition.
- "unklar": Der Text reicht nicht aus, um sicher einzuordnen.

Im Zweifel wähle "unklar", niemals "gewollt verschieden" raten. Grund: Wird ein echter Widerspruch als „gewollt verschieden“ eingeordnet, übersieht die kalkulierende Person ihn womöglich; das ist für sie teurer als eine Rückfrage.

Regeln:
1. Zitiere wörtlich. "zitat_a" ist ein zusammenhängender Ausschnitt aus dem Text der Position "oz_a", "zitat_b" aus dem Text der Position "oz_b", jeweils mit der betroffenen Angabe. Nichts umformulieren, nichts auslassen, keine Auslassungszeichen, keine Anführungszeichen hinzufügen.
2. "oz_a" und "oz_b": die Ordnungszahlen genau wie im Text.
3. "begruendung": höchstens zwei Sätze, sachlich, auf Deutsch. Nenne darin, welche Angabe in welcher Position steht.
4. "rueckfrage": nur bei "echter Widerspruch" oder "unklar" eine kurze, neutrale Frage des Bieters an den Auftraggeber; sonst "".
5. Keine Aussagen zu Ansprüchen, Vergütung, Haftung oder Vertragsauslegung. Verwende nicht die Wörter "Anspruch", "berechtigt" und "durchsetzbar" und verweise auf keine Paragraphen.
6. Platzhalter in eckigen Klammern wie [PERSON_...], [NUMMER_...], [FIRMA_...] oder [ORT_...] stammen aus der Anonymisierung. Sie sind keine Fehler und kein Grund für eine Einordnung.
7. Nimm nichts an, was nicht im Text steht.

Antworte ausschließlich mit einem JSON-Objekt ohne weiteren Text, genau mit diesen Feldern:
{"einordnung": "...", "oz_a": "...", "oz_b": "...", "zitat_a": "...", "zitat_b": "...", "begruendung": "...", "rueckfrage": "..."}"""}
PROMPT_SHA256 = {"tippfehler": "90570d408e8466e15f44b04b9759f6890df4ee595e9c5f800d2b94be3e113e54", "widerspruch": "6f3d4c72248b11558c293b7193bfce7a7e2594ea1015955356938cb9d1c8e184"}

SCHEMA = {
    "tippfehler": {"type": "object", "properties": {
        "befund": {"type": "string", "enum": BEFUNDE["tippfehler"]}, "zitat": {"type": "string"},
        "korrektur": {"type": "string"}, "begruendung": {"type": "string"}},
        "required": ["befund", "zitat", "korrektur", "begruendung"], "additionalProperties": False},
    "widerspruch": {"type": "object", "properties": {
        "einordnung": {"type": "string", "enum": BEFUNDE["widerspruch"]}, "oz_a": {"type": "string"},
        "oz_b": {"type": "string"}, "zitat_a": {"type": "string"}, "zitat_b": {"type": "string"},
        "begruendung": {"type": "string"}, "rueckfrage": {"type": "string"}},
        "required": ["einordnung", "oz_a", "oz_b", "zitat_a", "zitat_b", "begruendung", "rueckfrage"],
        "additionalProperties": False},
}


def prompt_eingefroren(pruefung):
    return hashlib.sha256(PROMPT[pruefung].encode("utf-8")).hexdigest() == PROMPT_SHA256[pruefung]


def positionstext(positionen):
    """Eingabe je Aufruf: OZ, Kurztext, Langtext, Menge und Einheit je Position (wie src/b5_testfaelle.py)."""
    return "\n\n".join(f"OZ {p['oz']}\nKurztext: {p['kurztext']}\nLangtext: {p['langtext']}\n"
                        f"Menge: {(p.get('menge') or 0):g} {p.get('einheit') or ''}" for p in positionen)


def cache_schluessel(pruefung, anbieter, modell, text):
    roh = json.dumps([anbieter, modell, denkaufwand(anbieter), VERSION[pruefung], PROMPT[pruefung], text],
                     ensure_ascii=False)
    return hashlib.sha256(roh.encode("utf-8")).hexdigest()


def lies_antwort(pruefung, antworttext):
    """JSON-Objekt mit genau den Feldern aus SCHEMA (alle Text), sonst None. Eigener Leser, weil
    ki_pruefung.lies_json nur die Felder der Gegenprüfung Nr. 1/2 kennt."""
    s = (antworttext or "").strip()
    a, e = s.find("{"), s.rfind("}")
    if a < 0 or e < a:
        return None
    try:
        d = json.loads(s[a:e + 1])
    except json.JSONDecodeError:
        return None
    felder = SCHEMA[pruefung]["required"]
    if not isinstance(d, dict) or any(not isinstance(d.get(k), str) for k in felder):
        return None
    return {k: d[k] for k in felder}


def bewerte(pruefung, antworttext, positionen):
    """(Status, Antwort-dict). Prüft Schema, R7, Wörtlichkeit der Zitate und R9 (Platzhalter)."""
    d = lies_antwort(pruefung, antworttext)
    feld = "befund" if pruefung == "tippfehler" else "einordnung"
    if d is None or d.get(feld) not in BEFUNDE[pruefung]:
        return STATUS_UNLESBAR, None
    if VERBOTEN.search(json.dumps(d, ensure_ascii=False)):
        return STATUS_R7, d
    if d[feld] != FUND[pruefung]:
        return STATUS_GUELTIG, d
    texte = {normalisiere_oz(p["oz"]): (p["kurztext"], p["langtext"]) for p in positionen}
    alle = [t for kl in texte.values() for t in kl]
    if pruefung == "tippfehler":
        if not beleg_im_text(d.get("zitat", ""), *alle):
            return STATUS_ZITAT, d
        if PLATZHALTER_RE.search(d.get("zitat", "")):
            return STATUS_R9, d
        return STATUS_GUELTIG, d
    a, b = texte.get(normalisiere_oz(d.get("oz_a", ""))), texte.get(normalisiere_oz(d.get("oz_b", "")))
    if not (a and b and beleg_im_text(d.get("zitat_a", ""), *a) and beleg_im_text(d.get("zitat_b", ""), *b)):
        return STATUS_ZITAT, d
    return STATUS_GUELTIG, d


def pruefe(pruefung, gruppen, konfig, client=None, max_aufrufe=MAX_AUFRUFE, cache_dir=CACHE_DIR,
           log_datei=LOG_DATEI, fortschritt=None):
    """KI-Prüfung für eine Liste von Positionsgruppen (Tippfehler: je 1 Position, Widerspruch: je Paar).
    Gibt (ergebnisse, statistik) zurück; ergebnis = {schluessel, positionen, status, antwort, quelle}."""
    stat = {"aufrufe": 0, "cache_treffer": 0, "nicht_geprueft": 0, "technische_fehler": [], "meldung": "",
            "input_tokens": 0, "output_tokens": 0, "kosten_usd": 0.0}
    erg = []
    if not konfig.aktiv or not konfig.modell:
        stat["meldung"] = "KI aus (kein API-Key)"
        return erg, stat
    if not prompt_eingefroren(pruefung):
        stat["meldung"] = f"Prompt {VERSION[pruefung]} geändert – erst neue Version vergeben"
        return erg, stat
    ki = None
    for i, gruppe in enumerate(gruppen, start=1):
        text = positionstext(gruppe)
        sch = cache_schluessel(pruefung, konfig.anbieter, konfig.modell, text)
        c = lies_cache(sch, cache_dir)
        if c is not None:
            stat["cache_treffer"] += 1
            status, d = bewerte(pruefung, c["antwort_text"], gruppe)
            erg.append({"schluessel": sch, "positionen": [p["oz"] for p in gruppe], "status": status, "antwort": d,
                        "quelle": "Cache", "modell": c.get("modell_antwort") or konfig.modell})
            continue
        if stat["aufrufe"] >= max_aufrufe:
            stat["nicht_geprueft"] += 1
            continue
        if ki is None:
            ki = ki_client.als_client(client if client is not None else konfig.client(), konfig.anbieter)
        if fortschritt:
            fortschritt(i, len(gruppen))
        stat["aufrufe"] += 1
        zeit = datetime.now().astimezone().isoformat(timespec="seconds")
        try:
            antwort = ki.anfrage(konfig.modell, PROMPT[pruefung], text, BEFUNDE[pruefung], schema=SCHEMA[pruefung])
        except TechnischerFehler as e:
            stat["technische_fehler"].append(e.art)
            stat["nicht_geprueft"] += 1
            schreibe_log({"zeit": zeit, "b5": pruefung, "anbieter": konfig.anbieter, "modell": konfig.modell,
                          "prompt_version": VERSION[pruefung], "ergebnis": f"technischer Fehler: {e.art}"}, log_datei)
            if e.art.startswith("429"):
                stat["meldung"] = f"Limit erreicht ({e.art})"
                break
            continue
        stat["input_tokens"] += antwort.usage.get("input_tokens", 0)
        stat["output_tokens"] += antwort.usage.get("output_tokens", 0)
        stat["kosten_usd"] += kosten(antwort.usage, konfig.anbieter)
        status, d = bewerte(pruefung, antwort.text, gruppe)
        schreibe_log({"zeit": zeit, "b5": pruefung, "anbieter": konfig.anbieter, "modell": konfig.modell,
                      "modell_antwort": antwort.modell, "prompt_version": VERSION[pruefung], "usage": antwort.usage,
                      "ergebnis": status}, log_datei)
        if status == STATUS_UNLESBAR:
            stat["nicht_geprueft"] += 1                       # nicht cachen
            continue
        schreibe_cache(sch, {"b5": pruefung, "anbieter": konfig.anbieter, "modell": konfig.modell,
                             "modell_antwort": antwort.modell, "prompt_version": VERSION[pruefung],
                             "positionstext": text, "antwort_text": antwort.text, "status": status,
                             "erstellt": zeit}, cache_dir)
        erg.append({"schluessel": sch, "positionen": [p["oz"] for p in gruppe], "status": status, "antwort": d,
                    "quelle": "API", "modell": antwort.modell})
    if stat["nicht_geprueft"] and not stat["meldung"]:
        stat["meldung"] = (f"{stat['nicht_geprueft']} noch nicht geprüft (höchstens {max_aufrufe} Aufrufe je Klick; "
                           f"der nächste Klick macht weiter, Geprüftes kommt aus dem Cache)")
    return erg, stat


def vorschlaege(pruefung, ergebnisse):
    """Nur gültige Funde als KI-Vorschlag (E13: Entwarnungen erzeugen nichts)."""
    out = []
    for e in ergebnisse:
        d = e["antwort"] or {}
        if e["status"] != STATUS_GUELTIG or d.get("befund", d.get("einordnung")) != FUND[pruefung]:
            continue
        kat, stufe, empf = VORSCHLAG[pruefung]
        out.append({"pruefung": pruefung, "positionen": e["positionen"], "kategorie_vorschlag": kat,
                    "stufe_vorschlag": stufe, "empfehlung": empf, "antwort": d, "quelle": e["quelle"],
                    "prompt_version": VERSION[pruefung], "modell": e["modell"]})
    return out


# --------------------------------------------------------------------------- Vorauswahl (Regel)

BAUTEIL_RE = re.compile(r"[A-Za-zÄÖÜäöüß][a-zäöüß]{3,}")             # ab 4 Buchstaben (z. B. „Rohr“)
STOPP = {"liefern", "einbauen", "verlegen", "setzen", "eine", "alle", "sind", "wird", "bzw", "herstellen", "montieren", "inkl", "einschl", "gemäß", "sowie", "nach", "oder",
         "werden", "mit", "und", "für", "eines", "einer", "position", "leistung", "gleichwertig"}


def _werte(text):
    dn = {w for a in dn_angaben(text) for w in a}
    c = werte(r"\bC\s?\d{2}/\d{2}\b", text)
    return dn, c


def paare(df, max_paare=MAX_PAARE):
    """Regel-Vorauswahl der Positionspaare (Vorschlag B2, umgesetzt B5): gleicher Abschnitt (OZ ohne letzte Stelle),
    ein gemeinsames Bauteilwort im Kurztext und verschiedene Werte derselben Art (DN oder Betonklasse) im Text.
    Feste Reihenfolge (E14), höchstens `max_paare`."""
    pos = df[df.typ == "Position"]
    zeilen = []
    for r in pos.itertuples():
        kurz = r.kurztext if isinstance(r.kurztext, str) else ""
        lang = r.langtext if isinstance(r.langtext, str) else ""
        if not kurz:
            continue
        n = normalisiere_oz(r.oz)
        wort = {w.lower() for w in BAUTEIL_RE.findall(kurz)} - STOPP
        zeilen.append((n.rsplit(".", 1)[0] if "." in n else "", r, wort, _werte(f"{kurz} {lang}")))
    out = []
    for i, (ab_a, a, wa, (dna, ca)) in enumerate(zeilen):
        for ab_b, b, wb, (dnb, cb) in zeilen[i + 1:]:
            if ab_a != ab_b or not (wa & wb):
                continue
            if (dna and dnb and not (dna & dnb)) or (ca and cb and not (ca & cb)):
                out.append([{"oz": x.oz, "kurztext": normalisiere_leerzeichen(x.kurztext),
                             "langtext": normalisiere_leerzeichen(x.langtext if isinstance(x.langtext, str) else ""),
                             "menge": x.menge if x.menge == x.menge else None, "einheit": x.einheit or ""}
                            for x in (a, b)])
                if len(out) >= max_paare:
                    return out
    return out


def einzelpositionen(df):
    """Je Position eine Gruppe für die Tippfehler-Prüfung (Reihenfolge wie im LV)."""
    pos = df[df.typ == "Position"]
    return [[{"oz": r.oz, "kurztext": normalisiere_leerzeichen(r.kurztext if isinstance(r.kurztext, str) else ""),
              "langtext": normalisiere_leerzeichen(r.langtext if isinstance(r.langtext, str) else ""),
              "menge": r.menge if r.menge == r.menge else None, "einheit": r.einheit or ""}]
            for r in pos.itertuples() if isinstance(r.kurztext, str) and r.kurztext.strip()]


# --------------------------------------------------------------------------- Messung (32 erfundene Fälle)

def messung(konfig, client=None, ausgabe=None, ablage=None):
    """Alle 32 erfundenen Fälle (src/b5_testfaelle.py) über pruefe() und bewerte_antwort(); Ergebnis getrennt nach
    Prüfung und positiv/negativ, ohne Prozent (R11). Fälle werden nicht an Antworten angepasst (E12 (3))."""
    import b5_testfaelle as T
    zeilen = []
    for pr, faelle in (("tippfehler", T.TIPPFEHLER), ("widerspruch", T.WIDERSPRUCH)):
        for f in faelle:                                       # je Fall ein Lauf: Zuordnung Fall -> Antwort eindeutig
            erg, stat = pruefe(pr, [f["positionen"]], konfig, client, max_aufrufe=1, **(ablage or {}))
            e = erg[0] if erg else {"status": stat["meldung"] or "nicht geprüft", "antwort": None, "quelle": "-"}
            fall = dict(f, pruefung=pr)
            b = T.bewerte_antwort(fall, e["antwort"]) if e["antwort"] else {"gueltig": False, "richtig": False,
                                                                              "grund": e["status"]}
            zeilen.append({"id": f["id"], "pruefung": pr, "erwartet": f["erwartet"], "status": e["status"],
                           "quelle": e["quelle"], "gueltig": b["gueltig"], "richtig": b["richtig"], "grund": b["grund"],
                           "antwort": e["antwort"]})
    zus = {}
    for z in zeilen:
        k = f"{z['pruefung']} {'positiv' if z['erwartet'] == 'Fund' else 'negativ'}"
        s = zus.setdefault(k, {"faelle": 0, "gueltig": 0, "richtig": 0})
        s["faelle"] += 1
        s["gueltig"] += z["gueltig"]
        s["richtig"] += z["richtig"]
    doc = {"stand": datetime.now().astimezone().isoformat(timespec="seconds"), "prompt_versionen": VERSION,
           "modell": konfig.modell, "anbieter": konfig.anbieter, "zusammenfassung": zus, "faelle": zeilen,
           "hinweis": "erfundene Fälle (Sitzung B2), keine Messung der Treffsicherheit am Datensatz"}
    if ausgabe:
        from pathlib import Path
        Path(ausgabe).write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return doc
