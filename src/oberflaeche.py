"""
oberflaeche.py - Designsystem und Bausteine des LV-Prüfassistenten (Sitzung UI2, Block UI3 „Redesign“, Team 22.11.2026).

Richtung (UI3-6, „unslop“): akribisch, nüchtern, beweisend. Die Welt ist die geprüfte LV-Seite – Papier, Ordnungszahlen
am Rand, der Textmarker des Prüfers. Die Oberfläche bleibt ruhig (Graphit, Haarlinien, Serifen-Überschriften, OZ in
Monospace); die Farbe steckt in zwei Momenten: dem Beleg als Ausschnitt einer LV-Seite mit Textmarker (Signatur) und
der LV-Karte, die zeigt, wo im LV die Funde liegen.

Inhaltsregeln bleiben (Kern): Text aus dem LV wird immer maskiert und wörtlich gezeigt (R5); der Textmarker umschließt nur
wörtliche Treffer im maskierten Text, der Text selbst bleibt gleich; jede Zahl ist eine Zählung vorhandener Daten (R11);
KI-Vorschläge neutral und nie entwarnend (E13). Farbe nur nach Kategorie (R6). LV_UI_OHNE_CSS=1 lässt das CSS weg.
Schriften: nur Systemschriften des Rechners (ui-serif = New York auf dem Mac, sonst Georgia), keine Downloads.
"""
import html
import os
import re
from dataclasses import dataclass
from pathlib import Path

import streamlit as st

OHNE_CSS = "LV_UI_OHNE_CSS"
STUFEN = {1: "Fehlerprüfung", 2: "Kalkulationsrisiko", 3: "mögliches Nachtragspotenzial", 4: "Unklarheit"}
# Farbe nur nach Kategorie (R6): Rot = nachweisbarer Fehler, Bernstein = möglicher Widerspruch und Risikohinweis,
# neutral = Unklarheit. Stufen, Status „offen“/„verworfen“/„Rückfrage stellen“ und KI sind neutral; Grün nur „bestätigt“.
KATEGORIE_TON = {"nachweisbarer Fehler": "rot", "möglicher Widerspruch": "bernstein", "Risikohinweis": "bernstein",
                 "Unklarheit": "neutral"}
STATUS_TON = {"offen": "neutral", "bestätigt": "gruen", "verworfen": "neutral", "Rückfrage stellen": "neutral"}
SERIF = 'ui-serif, "New York", "Iowan Old Style", Charter, Georgia, serif'
MONO = 'ui-monospace, "SF Mono", SFMono-Regular, Menlo, Consolas, monospace'

# Farben je Modus. Graphit statt Blau; Papier nur für den Beleg. Kontraste geprüft in test_ui3_oberflaeche.py.
FARBEN = {
    "dark": {"grund": "#141415", "leiste": "#0F0F10", "flaeche": "#19191B", "flaeche2": "#202023", "erhoben": "#232325",
             "rand": "#2A2A2D", "rand_stark": "#3A3A3E", "text": "#EDEDED", "text2": "#A1A1A6", "text3": "#8E8E94",
             "akzent": "#8FB0FF", "akzent_fl": "#EDEDED", "akzent_text": "#141415", "akzent_weich": "#24262D",
             "rot": "#F2918A", "rot_balken": "#E5484D", "rot_weich": "#2C1A1A",
             "bernstein": "#E9BC5C", "bernstein_balken": "#D9A03A", "bernstein_weich": "#2A2416",
             "gruen": "#74D1A0", "gruen_balken": "#4CC38A", "gruen_weich": "#17271F",
             "neutral": "#B4B4BA", "neutral_balken": "#5C5C62", "neutral_weich": "#232325",
             "papier": "#F3EFE6", "papier_text": "#1F1B16", "papier_rand": "#DAD3C5", "papier_meta": "#6E665A",
             "markierung": "#F4DC5C", "markierung_text": "#1F1B16"},
    "light": {"grund": "#F7F7F5", "leiste": "#EFEFEC", "flaeche": "#FFFFFF", "flaeche2": "#F3F3F1", "erhoben": "#FFFFFF",
              "rand": "#E3E3E0", "rand_stark": "#CFCFCB", "text": "#171717", "text2": "#4F4F4F", "text3": "#666666",
              "akzent": "#2A55C9", "akzent_fl": "#171717", "akzent_text": "#FFFFFF", "akzent_weich": "#ECEEF4",
              "rot": "#B42318", "rot_balken": "#D92D20", "rot_weich": "#FDECEA",
              "bernstein": "#875700", "bernstein_balken": "#D99A1E", "bernstein_weich": "#FBF1DC",
              "gruen": "#146C3E", "gruen_balken": "#2E9E66", "gruen_weich": "#E6F4EA",
              "neutral": "#4F4F4F", "neutral_balken": "#A3A3A3", "neutral_weich": "#F1F1EF",
              "papier": "#FBF8F1", "papier_text": "#1F1B16", "papier_rand": "#E4DDCF", "papier_meta": "#6E665A",
              "markierung": "#F6E27A", "markierung_text": "#1F1B16"},
}


# --------------------------------------------------------------------------- Text und Zahlen

def de_zahl(n):
    """Ganze Zahl mit Tausenderpunkt; fehlend → „–“."""
    if n is None:
        return "–"
    return f"{int(n):,}".replace(",", ".")


def de_prozent(teil, ganz):
    """Anteil in ganzen Prozent; ohne Grundmenge „–“ (keine erfundene 0 %)."""
    if not ganz:
        return "–"
    return f"{round(100 * teil / ganz)} %"


def h(text):
    """HTML-maskiert (LV-Text, Dateinamen)."""
    return html.escape("" if text is None else str(text), quote=True)


def md_text(text):
    """Für Markdown maskiert: wird wörtlich angezeigt (z. B. „[ORT_024] LV.D86“)."""
    return re.sub(r"([\\`*_{}\[\]<>$:~#|])", r"\\\1", "" if text is None else str(text))


# Textmarker nur auf dem, was die Aussage des Funds trägt (Team, Browser-Abnahme 796adee): Prüfung Nr. 1 die DN-Werte,
# Nr. 2 die Betonfestigkeitsklassen; alle anderen Prüfungen ohne Markierung. Der Text bleibt Zeichen für Zeichen gleich.
MARKER_JE_PRUEFUNG = {1: re.compile(r"\bDN\s?\d+(?:[.,]\d+)?\b"),
                      2: re.compile(r"\bL?C\s?\d{1,3}\s?/\s?\d{1,3}\b")}


def beleg_html(text, pruefung=None):
    """Beleg wörtlich: erst maskieren, dann nur die tragenden wörtlichen Treffer der Prüfung mit <mark> umschließen."""
    roh = h(text)
    muster = MARKER_JE_PRUEFUNG.get(pruefung)
    if muster is not None:
        roh = muster.sub(lambda m: f"<mark>{m.group(0)}</mark>", roh)
    return roh


def de_datum(wert):
    """ISO-Datum (auch mit Uhrzeit) deutsch: „2026-11-22“ → „22.11.2026“; Unbekanntes unverändert, leer → „–“."""
    if not wert:
        return "–"
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", str(wert))
    return f"{m.group(3)}.{m.group(2)}.{m.group(1)}" if m else str(wert)


def belegstand_text(status, stand):
    """„Stand der Belegprüfung“ nur, wenn für diesen Fund ein Abgleich vorliegt (geprüft oder nicht im Original)."""
    if status not in ("geprüft", "nicht im Original"):
        return None
    return f"Stand der Belegprüfung: {de_datum(stand)}"


def anzahl_wort(n, einzahl, mehrzahl):
    """„1 nachweisbarer Fehler“ / „2 nachweisbare Fehler“."""
    return f"{de_zahl(n)} {einzahl if n == 1 else mehrzahl}"


# --------------------------------------------------------------------------- Bausteine (HTML)

@dataclass
class Kennzahl:
    titel: str
    wert: str
    hinweis: str = ""
    ton: str = "text"          # text | rot | bernstein | gruen | neutral


def _ton(ton):
    return ton if ton in ("rot", "bernstein", "gruen", "neutral", "akzent") else "text"


def chip(text, ton="neutral"):
    """Ruhiges Etikett: Punkt in der Bedeutungsfarbe, Text in Sekundärfarbe, Haarlinie. Farbe nie allein."""
    return (f'<span class="lv-chip lv-chip--{_ton(ton)}"><span class="lv-punkt lv-punkt--{_ton(ton)}" aria-hidden="true">'
            f'</span>{h(text)}</span>')


def chip_kategorie(kategorie):
    return chip(kategorie, KATEGORIE_TON.get(kategorie, "neutral"))


def chip_status(status):
    return chip(status, STATUS_TON.get(status, "neutral"))


def chip_stufe(stufe):
    return chip(f"Stufe {stufe} · {STUFEN.get(stufe, '')}", "neutral")


def kennzahlen_html(liste):
    """Kennzahlen als Zeile eines Prüfprotokolls: Haarlinien, keine Kacheln."""
    zellen = "".join(
        f'<div class="lv-kz"><div class="lv-kz-titel">{h(k.titel)}</div>'
        f'<div class="lv-kz-wert lv-ton--{_ton(k.ton)}">{h(k.wert)}</div>'
        + (f'<div class="lv-kz-hinweis">{h(k.hinweis)}</div>' if k.hinweis else "") + "</div>"
        for k in liste)
    rest = max(0, len(liste) - 1)
    spalten = "1.35fr" + (f" repeat({rest}, minmax(0, 1fr))" if rest else "")
    return f'<div class="lv-kennzahlen" style="grid-template-columns:{spalten}">{zellen}</div>'


def kennzahlen(liste):
    st.html(kennzahlen_html(liste))


def seitenkopf(titel, untertitel="", eyebrow=""):
    st.html('<header class="lv-kopf">'
            + (f'<div class="lv-eyebrow">{h(eyebrow)}</div>' if eyebrow else "")
            + f'<h1 class="lv-titel">{h(titel)}</h1>'
            + (f'<p class="lv-untertitel">{h(untertitel)}</p>' if untertitel else "") + "</header>")


def kompaktkopf(titel, meta=""):
    """Kompakter Seitenkopf für Arbeitsseiten mit geladenem LV (B1): kleiner Titel, eine Metazeile."""
    st.html(f'<header class="lv-kkopf"><h1 class="lv-ktitel">{h(titel)}</h1>'
            + (f'<p class="lv-kmeta">{h(meta)}</p>' if meta else "") + "</header>")


def kennzeile(eintraege):
    """Schmale Kennzahlenzeile (B2): [(Bezeichnung, Wert)] als eine Textzeile mit Haarlinien."""
    st.html('<div class="lv-kennzeile">' + "".join(
        f'<span><span class="lv-kennzeile-wert">{h(w)}</span> {h(b)}</span>' for b, w in eintraege) + "</div>")


def abschnitt(titel, rechts=""):
    st.html(f'<div class="lv-abschnitt"><h2>{h(titel)}</h2>'
            + (f'<span class="lv-abschnitt-rechts">{h(rechts)}</span>' if rechts else "") + "</div>")


def fortschritt(titel, teil, ganz, ton="gruen", hinweis=""):
    anteil = 0 if not ganz else max(0.0, min(1.0, teil / ganz))
    st.html(f'<div class="lv-fortschritt"><div class="lv-fortschritt-kopf"><span>{h(titel)}</span>'
            f'<span class="lv-zahl">{de_zahl(teil)} von {de_zahl(ganz)}</span></div>'
            f'<div class="lv-balken" role="progressbar" aria-valuemin="0" aria-valuemax="{ganz or 0}" '
            f'aria-valuenow="{teil}" aria-label="{h(titel)}"><div class="lv-balken-fuell lv-fuell--{_ton(ton)}" '
            f'style="width:{anteil * 100:.1f}%"></div></div>'
            + (f'<div class="lv-fortschritt-hinweis">{h(hinweis)}</div>' if hinweis else "") + "</div>")


def verteilung_html(titel, eintraege):
    """Verteilung als Rangliste mit dünnen Balken: eintraege [(Bezeichnung, Anzahl, Ton)]."""
    hoch = max([n for _, n, _ in eintraege] + [1])
    zeilen = "".join(
        f'<div class="lv-vt-zeile"><span class="lv-vt-name"><span class="lv-punkt lv-punkt--{_ton(ton)}" '
        f'aria-hidden="true"></span>{h(name)}</span>'
        f'<span class="lv-vt-spur"><span class="lv-vt-balken lv-fuell--{_ton(ton)}" style="width:{100 * n / hoch:.1f}%">'
        f'</span></span><span class="lv-vt-zahl">{de_zahl(n)}</span></div>' for name, n, ton in eintraege)
    return f'<div class="lv-verteilung"><div class="lv-label">{h(titel)}</div>{zeilen}</div>'


def verteilung(titel, eintraege):
    st.html(verteilung_html(titel, eintraege))


RANG_TON = {"rot": 0, "bernstein": 1, "neutral": 2}


# Beleg-Status (Kern 1, R5): eine Kennzeichnung für alle Seiten. Quelle: bericht.beleg_pruefung (S2-Liste).
BELEG_STATUS = {
    "geprüft": ("Beleg am Original geprüft", "gruen"),
    "ungeprüft": ("Zitat aus dem LV (Parser), am Original noch nicht geprüft", "neutral"),
    "nicht im Original": ("Beleg steht so nicht wörtlich im Original", "bernstein"),
}


def beleg_kennzeichnung(status):
    """(Text, Ton) für den Beleg-Status; Unbekanntes gilt als nicht geprüft (nie als geprüft)."""
    return BELEG_STATUS.get(status, BELEG_STATUS["ungeprüft"])


def beleg_label_html(status):
    text, ton = beleg_kennzeichnung(status)
    return (f'<div class="lv-label lv-beleg-status lv-beleg-status--{ton}"><span class="lv-punkt lv-punkt--{ton}" '
            f'aria-hidden="true"></span>{h(text)}</div>')


def positionen_mit_fund(zeilen, funde):
    """Zahl der Positionszeilen mit mindestens einem Fund. Ein Fund mit mehreren Positionen zählt bei jeder; eine
    doppelte OZ zählt je Zeile (wie in der LV-Karte und im Positions-Explorer). Ohne Positionsliste: verschiedene OZ."""
    oz_mit_fund = {p["oz"] for f in funde for p in f["positionen"]}
    if not zeilen:
        return len(oz_mit_fund)
    return sum(1 for z in zeilen if z["oz"] in oz_mit_fund)


def lv_karte_html(zeilen, funde):
    """Die LV-Karte: jede Position ein Strich in OZ-Reihenfolge; Positionen mit Fund in der Farbe der Kategorie des Funds
    mit der höchsten Stufe (Stufe 1 vor 2 …; bei gleicher Stufe zuerst nachweisbarer Fehler). Nur echte Daten."""
    rang_je_oz, ton_je_oz = {}, {}
    for f in funde:
        ton = KATEGORIE_TON.get(f["kategorie"], "neutral")
        rang = (f.get("stufe", 9), RANG_TON[ton])
        for p in f["positionen"]:
            if p["oz"] not in rang_je_oz or rang < rang_je_oz[p["oz"]]:
                rang_je_oz[p["oz"]], ton_je_oz[p["oz"]] = rang, ton
    if not zeilen:
        return ""
    striche = "".join(
        f'<span class="lv-strich{" lv-strich--" + ton_je_oz[z["oz"]] if z["oz"] in ton_je_oz else ""}" '
        f'title="OZ {h(z["oz"])}"></span>' for z in zeilen)
    mit = positionen_mit_fund(zeilen, funde)
    # Abschnittsmarken: erster Strich jedes obersten Abschnitts (OZ bis zum ersten Punkt), nur bei überschaubarer Zahl
    marken, gesehen = [], set()
    for i, z in enumerate(zeilen):
        kopf = str(z["oz"]).split(".")[0]
        if kopf not in gesehen:
            gesehen.add(kopf)
            marken.append((i, kopf, (str(z.get("titel") or "").split(" > ")[0])[:40]))
    marken_html = ""
    if 1 < len(marken) <= 24:
        marken_html = '<div class="lv-karte-marken">' + "".join(
            f'<span class="lv-karte-marke" style="left:{100 * i / len(zeilen):.2f}%" title="{h(titel)}">'
            f'<span class="lv-mono">{h(kopf)}</span></span>' for i, kopf, titel in marken) + "</div>"
    return (f'<figure class="lv-karte"><div class="lv-karte-striche" style="--n:{len(zeilen)}">{striche}</div>'
            f'{marken_html}'
            f'<figcaption><span class="lv-mono">OZ {h(zeilen[0]["oz"])}</span>'
            f'<span>{de_zahl(len(zeilen))} Positionen in LV-Reihenfolge · {de_zahl(mit)} mit Fund</span>'
            f'<span class="lv-mono">OZ {h(zeilen[-1]["oz"])}</span></figcaption></figure>')


def lv_karte(zeilen, funde):
    inhalt = lv_karte_html(zeilen, funde)
    if inhalt:
        st.html(inhalt)


def fund_zeile_html(f, rechts=""):
    """Zeile einer Fundliste wie eine LV-Zeile: OZ-Spalte in Monospace, Titel, Stufe und Kategorie, rechts Status."""
    oz = ", ".join(p["oz"] for p in f["positionen"])
    ton = KATEGORIE_TON.get(f["kategorie"], "neutral")
    kat = "" if f["kategorie"] == STUFEN.get(f["stufe"]) else f' · {h(f["kategorie"])}'
    return (f'<div class="lv-zeile"><span class="lv-zeile-oz lv-mono">{h(oz)}</span>'
            f'<div class="lv-zeile-text"><div class="lv-zeile-titel">{h(f["titel"])}</div>'
            f'<div class="lv-zeile-meta"><span class="lv-punkt lv-punkt--{ton}" aria-hidden="true"></span>'
            f'{h(STUFEN.get(f["stufe"], ""))}{kat}</div></div>'
            f'<div class="lv-zeile-rechts">{rechts}</div></div>')


def klickbare_zeile(schluessel, inhalt_html, beschriftung, on_click=None, args=(), aktiv=False):
    """Ganze Zeile klickbar: unsichtbarer Streamlit-Knopf über dem HTML (Tastatur und Screenreader nutzen den Knopf)."""
    sauber = re.sub(r"[^A-Za-z0-9_-]", "_", str(schluessel))
    with st.container(key=f"lvrow-{'aktiv-' if aktiv else ''}{sauber}"):
        st.html(inhalt_html)
        return st.button(beschriftung, key=f"lvhit-{sauber}", on_click=on_click, args=args)


def panel(schluessel):
    """Rechter Detailbereich (Belegfokus); Aufruf mit `with`."""
    return st.container(key=f"lvpanel-{re.sub(r'[^A-Za-z0-9_-]', '_', str(schluessel))}")


def karte(schluessel):
    return st.container(key=f"lvkarte-{re.sub(r'[^A-Za-z0-9_-]', '_', str(schluessel))}")


def beleg(text, quelle="", oz="", pruefung=None):
    """Der Beleg als Ausschnitt einer LV-Seite: Papier, OZ am Rand, Text in Serifen, Textmarker auf den Fachangaben."""
    st.html('<figure class="lv-beleg">'
            + (f'<span class="lv-beleg-oz lv-mono">OZ {h(oz)}</span>' if oz else "")
            + f'<blockquote>{beleg_html(text, pruefung)}</blockquote>'
            + (f'<figcaption>{h(quelle)}</figcaption>' if quelle else "") + "</figure>")


def hinweis(text, ton="neutral"):
    st.html(f'<div class="lv-hinweis lv-hinweis--{_ton(ton)}">{h(text)}</div>')


def leer(titel, text):
    st.html(f'<div class="lv-leer"><div class="lv-leer-titel">{h(titel)}</div><p>{h(text)}</p></div>')


def schritte(liste):
    """Nummerierte Schritte (echte Reihenfolge) als Folge mit Haarlinien: [(Titel, Text), …]."""
    st.html('<ol class="lv-schritte">' + "".join(
        f'<li><span class="lv-schritt-nr lv-mono">{i:02d}</span><div class="lv-schritt-titel">{h(t)}</div>'
        f'<p>{h(x)}</p></li>' for i, (t, x) in enumerate(liste, 1)) + "</ol>")


STUFEN_TEXT = {1: ("Nachweisbare Fehler und Widersprüche im LV", "Kurztext DN 150, Langtext DN 200"),
               2: ("Angaben, die die Kalkulation beeinflussen", "Pauschale, Bedarfsposition, fehlende Menge"),
               3: ("Mögliches Nachtragspotenzial oder möglicher Streitpunkt in der Ausführung",
                   "Entsorgung oder Vorhaltung nicht beschrieben"),
               4: ("Unklare oder vage Formulierungen", "„nach Erfordernis“, „gleichwertig“ ohne Kriterien")}


def stufen_erklaerung():
    """Die vier Stufen als kurze Tabelle: Stufe, was geprüft wird, Beispiel. Reihenfolge = Arbeitsreihenfolge."""
    st.html('<table class="lv-stufen"><thead><tr><th>Stufe</th><th>Was geprüft wird</th><th>Beispiel</th></tr></thead>'
            "<tbody>" + "".join(
                f'<tr><td><span class="lv-mono lv-stufe-nr">{s}</span>{h(n)}</td><td>{h(STUFEN_TEXT[s][0])}</td>'
                f'<td class="lv-stufe-bsp">{h(STUFEN_TEXT[s][1])}</td></tr>' for s, n in STUFEN.items())
            + "</tbody></table>")


def beispiel_beleg_html():
    """Vorschau auf der Startseite: ein Fund, wie das Tool ihn zeigt – aus einem erfundenen LV (Team F4), gekennzeichnet."""
    return ('<figure class="lv-beispiel"><div class="lv-beispiel-kopf"><span class="lv-mono">01.0010</span>'
            '<span>Nennweite (DN) im Kurztext ≠ Langtext</span>' + chip("möglicher Widerspruch", "bernstein") + "</div>"
            '<div class="lv-beleg lv-beleg--gross"><span class="lv-beleg-oz lv-mono">Kurztext</span>'
            f'<blockquote>{beleg_html("Druckrohr PE-HD DN 150", 1)}</blockquote></div>'
            '<div class="lv-beleg lv-beleg--gross"><span class="lv-beleg-oz lv-mono">Langtext</span>'
            f'<blockquote>{beleg_html("Druckrohr PE-HD DN 200 liefern und im Rohrgraben verlegen.", 1)}</blockquote></div>'
            '<div class="lv-beispiel-fuss"><span>Rückfrage an den Auftraggeber · Entwurf</span>'
            '<span class="lv-mono">Beispiel aus einem erfundenen LV</span></div></figure>')


BEISPIEL_BLATT = [   # erfundenes LV (Team F4); Fälle wie im Demo-LV: je ein Fund je Stufe
    ("01.0010", "Druckrohr PE-HD DN 150", "Druckrohr PE-HD DN 200 liefern und im Rohrgraben verlegen.", "20,000", "m",
     "bernstein", "Stufe 1 · möglicher Widerspruch · Nennweite (DN) im Kurztext ≠ Langtext"),
    ("01.0020", "Fundament Beton C25/30", "Ortbeton C30/37 für Einzelfundament herstellen.", "5,000", "m3",
     "bernstein", "Stufe 1 · möglicher Widerspruch · Betonfestigkeitsklasse im Kurztext ≠ Langtext"),
    ("01.0030", "Boden laden und entsorgen", "Aushub laden, Entsorgungsweg nach Wahl des AN.", "120,000", "m3",
     "bernstein", "Stufe 3 · Risikohinweis · Entsorgung, Boden"),
    ("01.0040", "Wasserhaltung", "Wasserhaltung nach Erfordernis für die gesamte Bauzeit.", "1,000", "psch",
     "neutral", "Stufe 4 · Unklarheit · Vage Formulierung"),
    ("01.0050", "Schachtabdeckung reinigen", "Schachtabdeckung reinigen und gangbar machen.", "4,000", "St", None, ""),
]
BEISPIEL_MARKIERT = ("DN 150", "DN 200", "C25/30", "C30/37")   # nur was die Aussage trägt (Nr. 1 DN, Nr. 2 Beton)


def _markiere(text, woerter):
    roh = h(text)
    for w in woerter:
        roh = roh.replace(h(w), f"<mark>{h(w)}</mark>")
    return roh


def lv_blatt_html():
    """Startseite: ein LV-Blatt, auf dem ein Prüfer gearbeitet hat – OZ-Spalte, Text, Menge, Textmarker und Randnotizen.
    Erfundenes Beispiel (Team F4), als solches gekennzeichnet; zeigt, was das Tool mit einem echten LV macht."""
    zeilen = "".join(
        f'<div class="lv-blatt-zeile"><span class="lv-blatt-oz lv-mono">{oz}</span>'
        f'<div class="lv-blatt-text"><div class="lv-blatt-kurz">{_markiere(kurz, BEISPIEL_MARKIERT)}</div>'
        f'<div class="lv-blatt-lang">{_markiere(lang, BEISPIEL_MARKIERT)}</div></div>'
        f'<span class="lv-blatt-menge lv-mono">{menge} {einheit}</span>'
        + (f'<span class="lv-blatt-notiz lv-blatt-notiz--{ton}"><span class="lv-punkt lv-punkt--{ton}"></span>'
           f'{h(notiz)}</span>' if ton else '<span class="lv-blatt-notiz"></span>')
        + "</div>" for oz, kurz, lang, menge, einheit, ton, notiz in BEISPIEL_BLATT)
    return ('<figure class="lv-blatt" aria-label="Beispiel: geprüftes LV-Blatt aus einem erfundenen LV">'
            '<div class="lv-blatt-kopf"><span>Leistungsverzeichnis · Titel 01 Erdarbeiten und Leitungsbau</span>'
            '<span class="lv-mono">Seite 3</span></div>'
            f'<div class="lv-blatt-spalten"><span>OZ</span><span>Leistung</span><span>Menge</span><span>Prüfvermerk</span></div>'
            f'{zeilen}<figcaption>Beispiel aus einem erfundenen LV · 4 Funde in 5 Positionen, jeder mit wörtlichem Beleg'
            '</figcaption></figure>')


def positionsblatt_html(z, funde_anzahl):
    """Die gewählte Position als Papierblatt: OZ und Abschnitt, Kurz- und Langtext wörtlich, Menge, EP, GP laut LV."""
    def zahl(x, stellen):
        if x is None or x != x:
            return "–"
        return f"{x:,.{stellen}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    menge = zahl(z.get("menge"), 3) + (f' {h(z["einheit"])}' if z.get("einheit") and z.get("menge") is not None else "")
    seite = f' · Seite {h(z["seite"])}' if z.get("seite") else ""
    return (f'<article class="lv-pblatt"><div class="lv-pblatt-kopf"><span class="lv-mono">OZ {h(z["oz"])}</span>'
            f'<span>{h((z.get("titel") or "").split(" > ")[-1])}{seite}</span></div>'
            f'<h3 class="lv-pblatt-kurz">{h(z.get("kurztext")) or "–"}</h3>'
            f'<div class="lv-pblatt-lang">{h(z.get("langtext")) or "–"}</div>'
            f'<dl class="lv-pblatt-werte"><div><dt>Menge</dt><dd class="lv-mono">{menge}</dd></div>'
            f'<div><dt>EP laut LV</dt><dd class="lv-mono">{zahl(z.get("ep"), 2)}</dd></div>'
            f'<div><dt>GP laut LV</dt><dd class="lv-mono">{zahl(z.get("gp"), 2)}</dd></div>'
            f'<div><dt>Funde</dt><dd class="lv-mono">{de_zahl(funde_anzahl)}</dd></div></dl></article>')


# --------------------------------------------------------------------------- Rahmen (Seitenleiste, Statusleiste)

def seitenleiste(gruppen, lv=None):
    """gruppen: [(Gruppenname, [st.Page, …]), …]; lv: {"name", "format", "positionen", "funde"} oder None."""
    with st.sidebar:
        st.html('<div class="lv-marke"><div class="lv-marke-name">LV-Prüfassistent</div>'
                '<div class="lv-marke-zeile">Jeder Fund mit Beleg</div></div>')
        for name, seiten in gruppen:
            st.html(f'<div class="lv-nav-gruppe">{h(name)}</div>')
            for seite in seiten:
                st.page_link(seite)
        with st.container(key="lvkarte-aktuelles-lv"):
            if lv:
                st.html('<div class="lv-lvkarte"><div class="lv-lvkarte-label">Aktuelles LV</div>'
                        f'<div class="lv-lvkarte-name">{h(Path(lv["name"]).name)}</div>'
                        f'<div class="lv-lvkarte-meta">{h(lv.get("format") or "–")} · '
                        f'{de_zahl(lv.get("positionen"))} Positionen'
                        + (f' · {de_zahl(lv["funde"])} Funde' if lv.get("funde") is not None else "")
                        + "</div></div>")
            else:
                st.html('<div class="lv-lvkarte"><div class="lv-lvkarte-label">Aktuelles LV</div>'
                        '<div class="lv-lvkarte-name">Noch kein LV geladen</div>'
                        '<div class="lv-lvkarte-meta">Auf der Startseite hochladen</div></div>')


def statusleiste(bereich, seite, lv_geladen):
    zustand = ("Analyse verfügbar", "neutral") if lv_geladen else ("Noch kein LV geladen", "neutral")   # Grün nur „bestätigt“
    st.html(f'<div class="lv-statusleiste"><div class="lv-brotkrumen">{h(bereich)} <span aria-hidden="true">/</span> '
            f'<b>{h(seite)}</b></div><div><span class="lv-punkt lv-punkt--{zustand[1]}" aria-hidden="true">'
            f'</span>{h(zustand[0])}</div></div>')


# --------------------------------------------------------------------------- CSS

def css():
    """CSS-Variablen je Modus; color-scheme kommt aus dem aktiven Theme, light-dark() wählt den Wert."""
    paare = ";".join(f"--lv-{k.replace('_', '-')}:light-dark({FARBEN['light'][k]},{FARBEN['dark'][k]})"
                     for k in FARBEN["dark"])
    return f"""<style>
:root {{ {paare}; --lv-serif:{SERIF}; --lv-mono-f:{MONO}; --lv-kurve:cubic-bezier(0.22, 1, 0.36, 1); }}
[data-testid="stApp"] {{ background: var(--lv-grund); }}
[data-testid="stApp"] p, [data-testid="stApp"] li {{ font-feature-settings: "tnum" 1; }}
[data-testid="stHeader"] {{ background: transparent; }}
[data-testid="stMainBlockContainer"] {{ max-width: 1440px; padding: 16px 40px 96px; }}
[data-testid="stSidebar"] {{ background: var(--lv-leiste); border-right: 1px solid var(--lv-rand); }}
[data-testid="stSidebarUserContent"] {{ padding: 8px 16px 24px; }}
[data-testid="stSidebarNav"] {{ display: none; }}

.lv-mono {{ font-family: var(--lv-mono-f); font-variant-numeric: tabular-nums; letter-spacing: 0; }}
.lv-marke {{ padding: 4px 8px 20px; border-bottom: 1px solid var(--lv-rand); margin-bottom: 8px; }}
.lv-marke-name {{ font-family: var(--lv-serif); font-size: 20px; font-weight: 500; color: var(--lv-text); line-height: 1.2; }}
.lv-marke-zeile {{ font-size: 13px; color: var(--lv-text3); margin-top: 4px; }}
.lv-nav-gruppe {{ font-size: 12px; font-weight: 500; color: var(--lv-text3); margin: 20px 8px 4px; }}
[data-testid="stSidebar"] [data-testid="stPageLink"] {{ margin: 0; }}
[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] {{ border-radius: 8px; padding: 6px 8px; min-height: 32px;
  transition: background-color 150ms var(--lv-kurve); }}
[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] p {{ color: var(--lv-text2); font-size: 14px;
  white-space: normal !important; overflow: visible !important; text-overflow: clip !important; line-height: 1.35; }}
[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] {{ height: auto !important; align-items: flex-start; }}
[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] * {{ overflow: visible; text-overflow: clip; }}
[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"]:hover {{ background: var(--lv-flaeche2); }}
[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"][aria-current="page"] {{ background: var(--lv-erhoben);
  box-shadow: inset 0 0 0 1px var(--lv-rand); }}
[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"][aria-current="page"] p {{ color: var(--lv-text); font-weight: 500; }}
.st-key-lvkarte-aktuelles-lv {{ margin-top: 24px; }}
.lv-lvkarte {{ border-top: 1px solid var(--lv-rand); padding: 16px 8px 0; }}
.lv-lvkarte-label {{ font-size: 12px; color: var(--lv-text3); }}
.lv-lvkarte-name {{ color: var(--lv-text); font-size: 14px; font-weight: 500; margin-top: 4px; overflow-wrap: anywhere; }}
.lv-lvkarte-meta {{ color: var(--lv-text2); font-size: 12px; margin-top: 4px; }}

.lv-statusleiste {{ display: flex; justify-content: space-between; gap: 16px; align-items: center; font-size: 13px;
  color: var(--lv-text3); padding: 0 0 12px; border-bottom: 1px solid var(--lv-rand); margin-bottom: 24px; }}
.lv-brotkrumen b {{ color: var(--lv-text2); font-weight: 500; }}
.lv-punkt {{ display: inline-block; width: 7px; height: 7px; border-radius: 50%; margin-right: 8px; vertical-align: 1px;
  background: var(--lv-neutral-balken); flex: none; }}
.lv-punkt--rot {{ background: var(--lv-rot-balken); }} .lv-punkt--bernstein {{ background: var(--lv-bernstein-balken); }}
.lv-punkt--gruen {{ background: var(--lv-gruen-balken); }} .lv-punkt--neutral {{ background: var(--lv-neutral-balken); }}
.lv-punkt--akzent {{ background: var(--lv-akzent); }}

.lv-kopf {{ margin: 0 0 32px; }}
.lv-eyebrow {{ font-size: 13px; color: var(--lv-text3); margin-bottom: 8px; }}
.lv-titel {{ font-family: var(--lv-serif); font-size: clamp(30px, 3vw, 40px); line-height: 1.12; font-weight: 500;
  letter-spacing: -0.015em; color: var(--lv-text); margin: 0; padding: 0; text-wrap: balance; }}
.lv-untertitel {{ color: var(--lv-text2); font-size: 15px; margin: 12px 0 0; max-width: 72ch; line-height: 1.55; }}
.lv-kkopf {{ margin: 0 0 20px; }}
.lv-ktitel {{ font-family: var(--lv-serif); font-size: 26px; font-weight: 500; line-height: 1.2; color: var(--lv-text);
  margin: 0; padding: 0; }}
.lv-kmeta {{ color: var(--lv-text2); font-size: 13px; margin: 6px 0 0; overflow-wrap: anywhere; }}
.lv-kennzeile {{ display: flex; flex-wrap: wrap; gap: 4px 0; color: var(--lv-text2); font-size: 13px; margin: 4px 0 12px;
  border-top: 1px solid var(--lv-rand); border-bottom: 1px solid var(--lv-rand); padding: 8px 0; }}
.lv-kennzeile > span {{ padding: 0 16px; border-left: 1px solid var(--lv-rand); }}
.lv-kennzeile > span:first-child {{ padding-left: 0; border-left: 0; }}
.lv-kennzeile-wert {{ color: var(--lv-text); font-weight: 500; font-variant-numeric: tabular-nums; }}
.lv-abschnitt {{ display: flex; justify-content: space-between; align-items: baseline; gap: 16px; margin: 8px 0 12px; }}
.lv-abschnitt h2 {{ font-family: var(--lv-serif); font-size: 21px; font-weight: 500; color: var(--lv-text); margin: 0;
  padding: 0; letter-spacing: -0.005em; }}
.lv-abschnitt-rechts {{ color: var(--lv-text3); font-size: 13px; }}
.lv-label {{ font-size: 12px; font-weight: 500; color: var(--lv-text3); margin: 20px 0 8px; }}
.lv-meta {{ color: var(--lv-text2); font-size: 13px; }}
.lv-text {{ color: var(--lv-text2); line-height: 1.6; font-size: 14px; max-width: 70ch; }}

.lv-kennzahlen {{ display: grid; border-top: 1px solid var(--lv-rand); border-bottom: 1px solid var(--lv-rand); margin: 0 0 28px; }}
.lv-kz {{ padding: 14px 24px 14px 0; min-width: 0; }}
.lv-kz + .lv-kz {{ padding-left: 24px; border-left: 1px solid var(--lv-rand); }}
.lv-kz-titel {{ color: var(--lv-text2); font-size: 13px; }}
.lv-kz-wert {{ font-size: 28px; font-weight: 500; line-height: 1; margin-top: 8px; font-variant-numeric: tabular-nums; }}
.lv-kz:first-child .lv-kz-wert {{ font-family: var(--lv-serif); font-size: 36px; font-weight: 400; }}
.lv-kz-hinweis {{ color: var(--lv-text3); font-size: 12px; margin-top: 8px; line-height: 1.4; }}
.lv-ton--text {{ color: var(--lv-text); }} .lv-ton--rot {{ color: var(--lv-rot); }} .lv-ton--bernstein {{ color: var(--lv-bernstein); }}
.lv-ton--gruen {{ color: var(--lv-gruen); }} .lv-ton--neutral {{ color: var(--lv-neutral); }} .lv-ton--akzent {{ color: var(--lv-akzent); }}
@media (max-width: 1100px) {{ .lv-kennzahlen {{ grid-template-columns: repeat(2, minmax(0, 1fr)) !important; }}
  .lv-kz:nth-child(3) {{ border-left: 0; padding-left: 0; }} .lv-kz:nth-child(n+3) {{ border-top: 1px solid var(--lv-rand); }} }}

.lv-chip {{ display: inline-flex; align-items: center; border-radius: 6px; padding: 3px 8px; font-size: 12px;
  font-weight: 500; color: var(--lv-text2); border: 1px solid var(--lv-rand); white-space: nowrap; background: transparent; }}
.lv-chip .lv-punkt {{ width: 6px; height: 6px; margin-right: 6px; vertical-align: 0; }}

.lv-zeile {{ display: grid; grid-template-columns: 104px minmax(0, 1fr) auto; gap: 16px; align-items: center;
  padding: 12px 12px; min-height: 64px; }}
.lv-zeile-oz {{ color: var(--lv-text3); font-size: 13px; align-self: start; padding-top: 2px; overflow-wrap: anywhere; }}
.lv-zeile-titel {{ color: var(--lv-text); font-weight: 500; font-size: 15px; line-height: 1.35; }}
.lv-zeile-meta {{ color: var(--lv-text2); font-size: 13px; margin-top: 4px; display: flex; align-items: center; }}
[class*="st-key-lvrow-"] {{ position: relative; border-bottom: 1px solid var(--lv-rand); border-radius: 0;
  transition: background-color 150ms var(--lv-kurve); }}
[class*="st-key-lvrow-"]:hover {{ background: var(--lv-flaeche); }}
[class*="st-key-lvrow-aktiv-"] {{ background: var(--lv-erhoben) !important; box-shadow: inset 0 0 0 1px var(--lv-rand-stark);
  border-radius: 8px; }}
[class*="st-key-lvrow-"] [class*="st-key-lvhit-"] {{ position: absolute; inset: 0; z-index: 2; margin: 0; }}
[class*="st-key-lvhit-"] button {{ width: 100%; height: 100%; opacity: 0; cursor: pointer; }}
[class*="st-key-lvrow-"]:has(button:focus-visible) {{ outline: 2px solid var(--lv-akzent); outline-offset: 2px; }}

[class*="st-key-lvpanel-"] {{ background: var(--lv-flaeche); border: 1px solid var(--lv-rand); border-radius: 16px;
  padding: 24px; }}
[class*="st-key-lvkarte-"]:not(.st-key-lvkarte-aktuelles-lv) {{ background: var(--lv-flaeche); border: 1px solid var(--lv-rand);
  border-radius: 16px; padding: 24px; }}
.lv-panel-kopf {{ display: flex; justify-content: space-between; align-items: flex-start; gap: 8px 12px; margin-bottom: 8px;
  flex-wrap: wrap; }}
.lv-panel-kopf .lv-panel-titel {{ flex: 1 1 14rem; min-width: 0; overflow-wrap: anywhere; }}
.lv-ort, .lv-meta, .lv-zeile-titel, .lv-untertitel, .lv-lvkarte-name {{ overflow-wrap: anywhere; min-width: 0; }}
[class*="st-key-lvpanel-"] {{ min-width: 0; overflow: hidden; }}
[class*="st-key-lvpanel-"] [data-testid="stHorizontalBlock"] {{ flex-wrap: wrap; gap: 8px; }}
[class*="st-key-lvpanel-"] [data-testid="stColumn"] {{ min-width: 9rem; }}
[class*="st-key-lvpanel-"] button p {{ white-space: normal; }}
@media (max-width: 1280px) {{
  .st-key-pf_filter [data-testid="stHorizontalBlock"] {{ flex-wrap: wrap; row-gap: 8px; }}
  .st-key-pf_filter [data-testid="stColumn"] {{ flex: 1 1 calc(50% - 16px) !important; min-width: calc(50% - 16px) !important; }}
  .st-key-pos_filter [data-testid="stHorizontalBlock"] {{ flex-wrap: wrap; row-gap: 8px; }}
  .st-key-pos_filter [data-testid="stColumn"] {{ flex: 1 1 calc(33% - 16px) !important; min-width: calc(33% - 16px) !important; }}
  .lv-zeile {{ grid-template-columns: 88px minmax(0, 1fr); }}
  .lv-zeile-rechts {{ grid-column: 2; }}
}}
.lv-panel-titel {{ font-family: var(--lv-serif); font-size: 24px; font-weight: 500; color: var(--lv-text); line-height: 1.2; }}
[class*="st-key-lv_ki_"] {{ border: 1px dashed var(--lv-rand-stark); border-radius: 10px; padding: 12px 16px; margin: 12px 0; }}
[class*="st-key-lv_erf_"] {{ border: 1px solid var(--lv-rand); background: var(--lv-flaeche2); border-radius: 10px;
  padding: 12px 16px; margin: 12px 0; }}

.lv-beleg {{ position: relative; margin: 0 0 8px; background: var(--lv-papier); border: 1px solid var(--lv-papier-rand);
  border-radius: 4px; padding: 14px 20px 14px 20px; box-shadow: 0 1px 0 var(--lv-papier-rand); }}
.lv-beleg-oz {{ display: block; font-size: 12px; color: var(--lv-papier-meta); margin-bottom: 6px;
  padding-bottom: 6px; border-bottom: 1px solid var(--lv-papier-rand); }}
.lv-beleg blockquote {{ margin: 0; padding: 0; border: 0; color: var(--lv-papier-text); font-family: var(--lv-serif);
  font-size: 16px; line-height: 1.6; white-space: pre-wrap; overflow-wrap: anywhere; }}
.lv-beleg mark {{ background: var(--lv-markierung); color: var(--lv-markierung-text); padding: 0 3px; border-radius: 2px;
  -webkit-box-decoration-break: clone; box-decoration-break: clone; }}
.lv-beleg figcaption {{ color: var(--lv-papier-meta); font-size: 12px; margin-top: 8px; font-family: var(--lv-mono-f); }}

.lv-karte {{ margin: 0 0 40px; }}
.lv-karte-striche {{ display: grid; grid-template-columns: repeat(var(--n), minmax(0, 1fr)); gap: 1px; height: 56px;
  align-items: end; padding: 12px 0; border-top: 1px solid var(--lv-rand); border-bottom: 1px solid var(--lv-rand); }}
.lv-strich {{ display: block; height: 30%; background: var(--lv-rand-stark); border-radius: 1px; }}
.lv-strich--rot {{ height: 100%; background: var(--lv-rot-balken); }}
.lv-strich--bernstein {{ height: 72%; background: var(--lv-bernstein-balken); }}
.lv-strich--neutral {{ height: 52%; background: var(--lv-neutral); }}
.lv-karte figcaption {{ display: flex; justify-content: space-between; gap: 16px; color: var(--lv-text3); font-size: 12px;
  margin-top: 8px; }}

.lv-beleg-status {{ display: flex; align-items: center; }}
.lv-beleg-status--gruen {{ color: var(--lv-gruen); }} .lv-beleg-status--bernstein {{ color: var(--lv-bernstein); }}
.lv-karte {{ position: relative; }}
.lv-karte-marken {{ position: relative; height: 20px; margin-top: 4px; }}
.lv-karte-marke {{ position: absolute; top: 0; transform: translateX(-1px); padding-left: 4px; border-left: 1px solid var(--lv-rand-stark);
  font-size: 11px; color: var(--lv-text3); line-height: 16px; }}

/* Textmarker: zieht einmal über die Stelle; ohne Animation (oder bei reduzierter Bewegung) sofort vollständig sichtbar */
.lv-beleg mark, .lv-blatt mark {{ background-image: linear-gradient(var(--lv-markierung), var(--lv-markierung));
  background-color: transparent; background-repeat: no-repeat; background-size: 100% 100%;
  animation: lv-marker 520ms var(--lv-kurve); }}
@keyframes lv-marker {{ from {{ background-size: 8% 100%; }} to {{ background-size: 100% 100%; }} }}

.lv-blatt {{ margin: 0; background: var(--lv-papier); color: var(--lv-papier-text); border-radius: 4px;
  border: 1px solid var(--lv-papier-rand); padding: 20px 24px 16px; box-shadow: 0 24px 48px -24px rgba(0, 0, 0, 0.55); }}
.lv-blatt-kopf {{ display: flex; justify-content: space-between; gap: 12px; font-size: 12px; color: var(--lv-papier-meta);
  padding-bottom: 10px; border-bottom: 2px solid var(--lv-papier-text); }}
.lv-blatt-spalten, .lv-blatt-zeile {{ display: grid; grid-template-columns: 64px minmax(0, 1fr) 84px 150px; gap: 12px; }}
.lv-blatt-spalten {{ font-size: 11px; color: var(--lv-papier-meta); padding: 8px 0 6px; border-bottom: 1px solid var(--lv-papier-rand); }}
.lv-blatt-zeile {{ padding: 10px 0; border-bottom: 1px solid var(--lv-papier-rand); align-items: start; }}
.lv-blatt-oz {{ font-size: 12px; color: var(--lv-papier-meta); padding-top: 2px; }}
.lv-blatt-kurz {{ font-family: var(--lv-serif); font-size: 15px; line-height: 1.35; }}
.lv-blatt-lang {{ font-family: var(--lv-serif); font-size: 13px; line-height: 1.45; color: #4A4238; margin-top: 2px; }}
.lv-blatt-menge {{ font-size: 12px; text-align: right; padding-top: 2px; }}
.lv-blatt-notiz {{ font-size: 11.5px; line-height: 1.35; color: var(--lv-papier-meta); padding: 2px 0 0 10px;
  border-left: 1px solid var(--lv-papier-rand); display: flex; align-items: flex-start; }}
.lv-blatt-notiz .lv-punkt {{ margin-top: 4px; }}
.lv-blatt-notiz--rot {{ color: #9E2A22; }} .lv-blatt-notiz--bernstein {{ color: #7A4E00; }} .lv-blatt-notiz--neutral {{ color: #4F4F4F; }}
.lv-blatt mark {{ color: var(--lv-papier-text); padding: 0 2px; border-radius: 2px; }}
.lv-blatt figcaption {{ font-size: 12px; color: var(--lv-papier-meta); margin-top: 12px; font-family: var(--lv-mono-f); }}

.lv-pblatt {{ background: var(--lv-papier); color: var(--lv-papier-text); border: 1px solid var(--lv-papier-rand);
  border-radius: 4px; padding: 20px 24px; box-shadow: 0 1px 0 var(--lv-papier-rand); }}
.lv-pblatt-kopf {{ display: flex; justify-content: space-between; gap: 12px; font-size: 12px; color: var(--lv-papier-meta);
  padding-bottom: 8px; border-bottom: 1px solid var(--lv-papier-rand); }}
.lv-pblatt-kurz {{ font-family: var(--lv-serif); font-size: 22px; font-weight: 500; line-height: 1.3; margin: 14px 0 8px;
  padding: 0; color: var(--lv-papier-text); }}
.lv-pblatt-lang {{ font-family: var(--lv-serif); font-size: 15px; line-height: 1.6; color: #3E372E; white-space: pre-wrap;
  max-height: 22rem; overflow-y: auto; }}
.lv-pblatt-werte {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); margin: 16px 0 0; padding-top: 12px;
  border-top: 2px solid var(--lv-papier-text); }}
.lv-pblatt-werte dt {{ font-size: 11px; color: var(--lv-papier-meta); }}
.lv-pblatt-werte dd {{ margin: 4px 0 0; font-size: 14px; }}

.lv-fortschritt {{ margin: 4px 0 16px; }}
.lv-fortschritt-kopf {{ display: flex; justify-content: space-between; color: var(--lv-text2); font-size: 13px; margin-bottom: 8px; }}
.lv-zahl {{ color: var(--lv-text); font-weight: 500; font-variant-numeric: tabular-nums; }}
.lv-balken {{ height: 6px; background: var(--lv-flaeche2); border-radius: 3px; overflow: hidden; }}
.lv-balken-fuell {{ height: 100%; border-radius: 3px; }}
.lv-fuell--gruen {{ background: var(--lv-gruen-balken); }} .lv-fuell--akzent {{ background: var(--lv-akzent); }}
.lv-fuell--neutral {{ background: var(--lv-neutral-balken); }} .lv-fuell--bernstein {{ background: var(--lv-bernstein-balken); }}
.lv-fuell--rot {{ background: var(--lv-rot-balken); }}
.lv-fortschritt-hinweis {{ color: var(--lv-text3); font-size: 12px; margin-top: 8px; }}

.lv-verteilung {{ padding: 0; }}
.lv-verteilung .lv-label {{ margin-top: 0; }}
.lv-vt-zeile {{ display: grid; grid-template-columns: minmax(10rem, 15rem) 1fr 48px; gap: 12px; align-items: center;
  min-height: 32px; border-bottom: 1px solid var(--lv-rand); }}
.lv-vt-name {{ color: var(--lv-text2); font-size: 13px; display: flex; align-items: center; }}
.lv-vt-spur {{ height: 4px; background: var(--lv-flaeche2); border-radius: 2px; overflow: hidden; }}
.lv-vt-balken {{ display: block; height: 100%; border-radius: 2px; }}
.lv-vt-zahl {{ text-align: right; color: var(--lv-text); font-size: 13px; font-variant-numeric: tabular-nums; }}

.lv-hinweis {{ border-radius: 8px; padding: 12px 16px; font-size: 14px; line-height: 1.5; border: 1px solid var(--lv-rand);
  margin: 0 0 12px; }}
.lv-hinweis--neutral {{ background: var(--lv-flaeche); color: var(--lv-text2); }}
.lv-hinweis--bernstein {{ background: var(--lv-bernstein-weich); color: var(--lv-bernstein); border-color: transparent; }}
.lv-hinweis--rot {{ background: var(--lv-rot-weich); color: var(--lv-rot); border-color: transparent; }}
.lv-leer {{ border: 1px dashed var(--lv-rand-stark); border-radius: 12px; padding: 32px 24px; text-align: center; }}
.lv-leer-titel {{ font-family: var(--lv-serif); color: var(--lv-text); font-size: 20px; }}
.lv-leer p {{ color: var(--lv-text2); margin: 8px auto 0; max-width: 55ch; font-size: 14px; }}

.lv-schritte {{ list-style: none; padding: 0; margin: 0 0 48px; display: grid; grid-template-columns: repeat(3, minmax(0, 1fr));
  border-top: 1px solid var(--lv-rand); }}
.lv-schritte li {{ margin: 0; padding: 20px 24px 4px 0; }}
.lv-schritte li + li {{ padding-left: 24px; border-left: 1px solid var(--lv-rand); }}
.lv-schritt-nr {{ color: var(--lv-text3); font-size: 12px; }}
.lv-schritt-titel {{ color: var(--lv-text); font-family: var(--lv-serif); font-size: 19px; margin-top: 8px; }}
.lv-schritte p {{ color: var(--lv-text2); margin: 8px 0 0; font-size: 14px; line-height: 1.55; }}
@media (max-width: 1100px) {{ .lv-schritte {{ grid-template-columns: 1fr; }}
  .lv-schritte li + li {{ border-left: 0; padding-left: 0; border-top: 1px solid var(--lv-rand); }} }}
.lv-stufen {{ width: 100%; border-collapse: collapse; margin: 0 0 48px; font-size: 14px; }}
.lv-stufen th {{ text-align: left; font-weight: 500; font-size: 12px; color: var(--lv-text3); padding: 0 16px 8px 0;
  border-bottom: 1px solid var(--lv-rand); }}
.lv-stufen td {{ padding: 12px 16px 12px 0; border-bottom: 1px solid var(--lv-rand); color: var(--lv-text2); vertical-align: top; }}
.lv-stufen td:first-child {{ color: var(--lv-text); font-weight: 500; white-space: nowrap; }}
.lv-stufe-nr {{ color: var(--lv-text3); margin-right: 12px; font-weight: 400; }}
.lv-stufe-bsp {{ font-family: var(--lv-serif); color: var(--lv-text2); }}

.lv-beispiel {{ margin: 0; background: var(--lv-flaeche); border: 1px solid var(--lv-rand); border-radius: 16px; padding: 20px; }}
.lv-beispiel-kopf {{ display: flex; gap: 12px; align-items: center; color: var(--lv-text); font-weight: 500; font-size: 14px;
  margin-bottom: 16px; flex-wrap: wrap; }}
.lv-beispiel-kopf .lv-mono {{ color: var(--lv-text3); font-weight: 400; font-size: 13px; }}
.lv-beispiel-kopf .lv-chip {{ margin-left: auto; }}
.lv-beleg--gross blockquote {{ font-size: 19px; }}
.lv-beispiel-fuss {{ display: flex; justify-content: space-between; gap: 12px; color: var(--lv-text3); font-size: 12px;
  margin-top: 16px; flex-wrap: wrap; }}
.lv-liste {{ margin: 4px 0 0; padding-left: 18px; color: var(--lv-text2); line-height: 1.6; font-size: 14px; }}
.lv-liste li {{ margin: 6px 0; }} .lv-liste b {{ color: var(--lv-text); font-weight: 500; }}
.lv-grenzen {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0 32px; color: var(--lv-text2);
  font-size: 14px; line-height: 1.55; border-top: 1px solid var(--lv-rand); }}
.lv-grenzen > div {{ padding: 14px 0; border-bottom: 1px solid var(--lv-rand); }}
.lv-grenzen b {{ color: var(--lv-text); font-weight: 500; }}
@media (max-width: 1100px) {{ .lv-grenzen {{ grid-template-columns: 1fr; }} }}
.lv-begriffe {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 0 32px; border-top: 1px solid var(--lv-rand);
  margin-bottom: 48px; }}
.lv-begriffe > div {{ padding: 16px 0; border-bottom: 1px solid var(--lv-rand); }}
.lv-begriffe b {{ color: var(--lv-text); font-weight: 500; font-family: var(--lv-serif); font-size: 17px; }}
.lv-begriffe p {{ color: var(--lv-text2); font-size: 14px; line-height: 1.55; margin: 6px 0 0; }}
@media (max-width: 1100px) {{ .lv-begriffe {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }} }}
.lv-farben {{ display: grid; gap: 8px; margin-bottom: 48px; }}
.lv-farben > div {{ display: flex; gap: 16px; align-items: center; color: var(--lv-text2); font-size: 14px; }}
.lv-farben .lv-chip {{ min-width: 13rem; }}

[data-testid="stFileUploaderDropzone"] {{ background: var(--lv-flaeche); border: 1px dashed var(--lv-rand-stark);
  border-radius: 12px; padding: 24px; }}
[data-testid="stBaseButton-primary"] {{ background: var(--lv-akzent-fl); color: var(--lv-akzent-text); border: 0;
  font-weight: 500; border-radius: 8px; box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.12); }}
[data-testid="stBaseButton-primary"]:hover {{ opacity: 0.9; }}
[data-testid="stBaseButton-secondary"] {{ background: var(--lv-erhoben); border: 1px solid var(--lv-rand); border-radius: 8px; }}
[data-testid="stBaseButton-secondary"]:hover {{ border-color: var(--lv-rand-stark); }}
[data-testid="stBaseButton-primary"]:active, [data-testid="stBaseButton-secondary"]:active {{ transform: scale(0.98); }}
[data-testid="stBaseButton-primary"], [data-testid="stBaseButton-secondary"] {{
  transition: background-color 150ms var(--lv-kurve), border-color 150ms var(--lv-kurve), opacity 150ms var(--lv-kurve),
  transform 120ms var(--lv-kurve); }}
[data-testid="stExpander"] details {{ border-color: var(--lv-rand); border-radius: 10px; background: transparent; }}
[data-testid="stSegmentedControl"] button {{ font-weight: 500; }}
/* Aktives Segment der Status-Auswahl (trägt aria-checked="true", kein eigenes data-testid): Text in Primärfarbe */
.st-key-pf_status_zeile button[aria-checked="true"] {{ background: var(--lv-erhoben) !important; color: var(--lv-text) !important;
  border-color: var(--lv-rand-stark) !important; }}
.st-key-pf_status_zeile button[aria-checked="true"] * {{ color: var(--lv-text) !important; }}
.st-key-pf_status_zeile {{ margin-bottom: 4px; }}
.st-key-pf_status_zeile [data-testid="stSegmentedControl"] {{ flex-wrap: wrap; }}
.st-key-pos_filter [data-testid="stWidgetLabel"] p, .st-key-pos_filter label p {{ white-space: normal; }}
:is(button, a, input, [role="button"], [tabindex="0"]):focus-visible {{ outline: 2px solid var(--lv-akzent); outline-offset: 2px; }}
@media (prefers-reduced-motion: reduce) {{ * {{ transition: none !important; animation: none !important; }} }}
</style>"""


def aktiver_modus():
    """„dark“ oder „light“ aus dem aktiven Streamlit-Theme (st.context.theme.type); None, wenn unbekannt."""
    try:
        modus = st.context.theme.type
    except Exception:
        return None
    return modus if modus in ("dark", "light") else None


def stil_einbinden():
    if not os.environ.get(OHNE_CSS):
        modus = aktiver_modus()
        # Rückfall (Team, Auflage 8): color-scheme aus dem aktiven Theme, damit light-dark() den richtigen Wert wählt,
        # auch wenn Streamlit color-scheme nicht selbst setzt.
        schema = f"<style>:root {{ color-scheme: {modus}; }}</style>" if modus else ""
        st.markdown(css() + schema, unsafe_allow_html=True)
