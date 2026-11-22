"""
pages/hilfe.py - „So funktioniert’s“ (Sitzung UI2, Block UI3): Ablauf, Begriffe und Grenzen in einfacher Sprache.
Nur Erklärtext; keine Zahl, die nicht aus dem Prüfkatalog oder dem aktuellen LV stammt.
"""
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))     # src/
import oberflaeche as ui                                          # noqa: E402

st.set_page_config(page_title="So funktioniert’s · LV-Prüfassistent", layout="wide")
ui.seitenkopf("So funktioniert’s", "In drei Schritten vom Leistungsverzeichnis zu einer belegten Liste der Punkte, die "
              "Sie vor der Abgabe klären sollten.", eyebrow="Hilfe")
ui.schritte([("LV hochladen", "Auf der Startseite: GAEB XML, GAEB 90, PDF oder Excel (mit Spalten-Zuordnung)."),
             ("Funde mit Beleg prüfen", "„Zuerst klären“ zeigt die wichtigsten Funde. Jeder hat ein wörtliches Zitat "
              "aus dem LV; bei PDF auch die Originalseite als Bild."),
             ("Entscheiden und exportieren", "Auf „Funde prüfen“ bestätigen, verwerfen oder Rückfrage stellen. Unter "
              "„Berichte & Export“ liegt der Risikobericht.")])
ui.abschnitt("Begriffe")
st.html('<div class="lv-begriffe">'
        '<div><b>Position, OZ</b><p>Eine Leistung im LV mit ihrer Ordnungszahl, z. B. „01.02.0030“.</p></div>'
        '<div><b>Fund</b><p>Eine Stelle, die eine Prüfregel gefunden hat – ein Hinweis zur Klärung, kein Urteil.</p></div>'
        '<div><b>Beleg</b><p>Das wörtliche Zitat aus dem LV, auf dem der Fund beruht. Ohne Beleg kein Fund.</p></div>'
        '<div><b>Kategorie</b><p>nachweisbarer Fehler · möglicher Widerspruch · Unklarheit · Risikohinweis.</p></div>'
        '<div><b>Stufe und Rang</b><p>Arbeitsreihenfolge: Stufe 1 zuerst; innerhalb einer Stufe der Rang.</p></div>'
        '<div><b>KI-Vorschlag</b><p>Optionaler Zweitblick einer KI, getrennt gekennzeichnet. Er ändert nie einen Fund '
        'und entwarnt nie.</p></div></div>')
ui.abschnitt("Die vier Stufen")
ui.stufen_erklaerung()
ui.abschnitt("Farben")
st.html('<div class="lv-farben">'
        f'<div>{ui.chip("nachweisbarer Fehler", "rot")}<span>Rot nur für nachweisbare Fehler.</span></div>'
        f'<div>{ui.chip("möglicher Widerspruch", "bernstein")}<span>Bernstein für Widersprüche und Risikohinweise.</span></div>'
        f'<div>{ui.chip("Unklarheit", "neutral")}<span>Neutral für Unklarheiten, Stufen und KI-Vorschläge.</span></div>'
        f'<div>{ui.chip("bestätigt", "gruen")}<span>Grün nur für Ihre Bestätigung bzw. einen bestätigten Beleg.</span></div>'
        '</div>')
ui.abschnitt("Grenzen")
st.html('<div class="lv-grenzen">'
        '<div><b>Keine Preise.</b> Das Tool ermittelt keine Preise; Vergleichspreise stammen nur aus bepreisten Dateien '
        'des Datensatzes, immer mit Quelle.</div>'
        '<div><b>Keine Rechtsaussage.</b> „Mögliches Nachtragspotenzial“ ist ein Hinweis, keine Bewertung.</div>'
        '<div><b>Keine Vollständigkeitsgarantie.</b> Kein Fund heißt nicht, dass die Position fehlerfrei ist.</div>'
        '<div><b>Sie entscheiden.</b> Status setzt nur ein Mensch; die Ablage liegt je LV auf diesem Rechner.</div>'
        '</div>')
