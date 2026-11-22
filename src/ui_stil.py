"""
ui_stil.py - Design-System der App (Sitzung UI, Team 22.11.2026), abgestimmt auf streamlit==1.67.0.

Eine Stelle für eigenes CSS und die Darstellungs-Helfer: Kopfbereich, Kennzahl-Kacheln, Abzeichen, Belegblock,
Navigation. Die Farben stehen nur in .streamlit/config.toml; das CSS liest sie von dort und wählt sie über
`light-dark()` passend zum aktiven Streamlit-Theme.

Farbsemantik (R6): Rot nur „nachweisbarer Fehler“; Bernstein „möglicher Widerspruch“ und „Risikohinweis“;
„Unklarheit“ und Stufen neutral; Grün nur für erledigte Status. KI-Vorschläge bleiben getrennt und nie grün (E13).
Der Helfer rechnet nichts Fachliches: Jede Zahl ist eine Zählung der übergebenen Funde oder ein Wert aus `info`.

Ohne CSS (LV_UI_OHNE_CSS=1) bleibt alles nutzbar: Inhalte sind natives Streamlit oder semantisches HTML.
"""
import html
import os
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path

import streamlit as st
from streamlit.errors import StreamlitAPIException

import pruefabdeckung
from bericht import STUFEN

CONFIG = Path(__file__).resolve().parent.parent / ".streamlit" / "config.toml"
OHNE_CSS = "LV_UI_OHNE_CSS"

KATEGORIE_FARBE = {"nachweisbarer Fehler": "red", "möglicher Widerspruch": "orange", "Risikohinweis": "orange",
                   "Unklarheit": "gray"}
STATUS_FARBE = {"offen": "gray", "bestätigt": "green", "verworfen": "gray", "Rückfrage stellen": "gray"}   # Blau nur Bedienung (Auftrag Abschnitt 9)
BELEG_ABZEICHEN = {"geprüft": ("green", "Beleg am Original geprüft"),
                   "ungeprüft": ("gray", "Beleg noch nicht am Original geprüft"),
                   "nicht im Original": ("orange", "Beleg nicht wörtlich im Original")}
SEITEN = (("app.py", "LV-Prüfung"), ("pages/0_Uebersicht.py", "Übersicht"), ("pages/2_Positionen.py", "Positionen"),
          ("pages/3_Nachtrag_und_Streitpunkte.py", "Nachtragspotenzial und Streitpunkte"),   # M2b (UI2)
          ("pages/1_Zuschlag_und_What-if.py", "Zuschlag und What-if"))


# --------------------------------------------------------------------------- Text und Zahlen

def de_zahl(n):
    """Ganze Zahl mit Tausenderpunkt."""
    return f"{n:,}".replace(",", ".")


def md_text(text):
    """Text aus dem LV oder ein Dateiname für Markdown: wird wörtlich angezeigt (z. B. „[ORT_024] LV.D86“)."""
    return re.sub(r"([\\`*_{}\[\]<>$:~#|])", r"\\\1", str(text))


def _html_text(text):
    return html.escape(str(text), quote=True).replace("\r\n", "\n").replace("\n", "<br>")


# --------------------------------------------------------------------------- Abzeichen

def _abzeichen(farbe, text):
    return f":{farbe}-badge[{text}]"


def stufe_name(stufe):
    return f"{stufe} – {STUFEN[stufe]}"


def abzeichen_stufe(stufe):
    """Stufe immer neutral und mit Namen."""
    return _abzeichen("gray", stufe_name(stufe))


def abzeichen_kategorie(kategorie):
    return _abzeichen(KATEGORIE_FARBE.get(kategorie, "gray"), kategorie)


def abzeichen_status(status):
    return _abzeichen(STATUS_FARBE.get(status, "gray"), status)


def abzeichen_status_zahl(status, anzahl):
    """Status mit Anzahl für den Kopf, z. B. „offen 12“."""
    return _abzeichen(STATUS_FARBE.get(status, "gray"), f"{status} {de_zahl(anzahl)}")


def abzeichen_beleg(pruefung):
    farbe, text = BELEG_ABZEICHEN.get(pruefung, ("gray", str(pruefung)))
    return _abzeichen(farbe, text)


def abzeichen_ki():
    """KI-Vorschläge sind neutral gekennzeichnet und nie grün (E13)."""
    return _abzeichen("gray", "KI-Vorschlag")


def abzeichen_fund(fund, beleg=None):
    """Stufe, Kategorie, Status und optional Beleg-Status als eine Markdown-Zeile."""
    teile = [abzeichen_stufe(fund["stufe"]), abzeichen_kategorie(fund["kategorie"]), abzeichen_status(fund["status"])]
    if beleg is not None:
        teile.append(abzeichen_beleg(beleg))
    return " ".join(teile)


# --------------------------------------------------------------------------- Kopfbereich und Kacheln

@dataclass(frozen=True)
class Kachel:
    bezeichnung: str
    wert: str
    hinweis: str = ""


def kopf(titel, kontext="", status=()):
    """Einheitlicher Kopf: Seitentitel, Kontext (wird wörtlich angezeigt), Status-Abzeichen (Markdown)."""
    with st.container(key="lv_kopf"):
        st.title(titel, anchor=False)
        if kontext:
            st.caption(md_text(kontext))
        if status:
            st.markdown(" ".join(status))


def kontext_lv(e):
    """„Datei · Format · 249 Positionen“ aus dem Session-Eintrag; nur der Dateiname, nie ein Pfad."""
    return f"{Path(e['lv_name']).name} · {e['format']} · {de_zahl(e['positionen'])} Positionen"


def kacheln_html(liste):
    zellen = []
    for k in liste:
        hinweis = f'<dd class="lv-kennzahl-hinweis">{_html_text(k.hinweis)}</dd>' if k.hinweis else ""
        zellen.append(f'<div class="lv-kennzahl"><dt>{_html_text(k.bezeichnung)}</dt>'
                      f'<dd class="lv-kennzahl-wert">{_html_text(k.wert)}</dd>{hinweis}</div>')
    return f'<dl class="lv-kennzahlen">{"".join(zellen)}</dl>'


def kacheln(liste):
    st.html(kacheln_html(liste))


def abdeckung_hinweis(abdeckung):
    """Eingeschränkte Prüfungen, gleichlautende zusammengefasst; leer, wenn alle Positionen prüfbar sind."""
    gruppen = {}
    for a in pruefabdeckung.eingeschraenkt(abdeckung):
        gruppen.setdefault(pruefabdeckung.text(a), []).append(str(a["pruefung"]))
    if not gruppen:
        return ""
    return ("**Prüfabdeckung:** " + " · ".join(f"Nr. {', '.join(n)} {t}" for t, n in gruppen.items())
            + ". Ein Hinweis, kein Fund wird unterdrückt.")


def kacheln_lv(e):
    """Acht Kacheln aus dem Session-Eintrag `lv_uebersicht`: nur Zählungen und Angaben aus der Prüfung."""
    funde = e.get("funde") or []
    abdeckung = e.get("abdeckung") or []
    regulaer = [a for a in abdeckung if not a.get("text")]
    if regulaer:
        voll = len(regulaer) - len(pruefabdeckung.eingeschraenkt(abdeckung))
        k_abdeckung = Kachel("Prüfabdeckung", f"{voll} von {len(regulaer)}", "Prüfungen in allen Positionen prüfbar")
    else:
        k_abdeckung = Kachel("Prüfabdeckung", "–", "keine Positionstexte in dieser Datei")
    rechnung = next((a for a in abdeckung if a["pruefung"] == 17), None)
    if rechnung is None:
        k_rechnung = Kachel("Rechenprüfung", "–", "nicht durchgeführt")
    elif not rechnung.get("pruefbar"):             # „0 Abweichungen“ ohne Rechnung sähe wie eine Entwarnung aus
        k_rechnung = Kachel("Rechenprüfung", "–", "keine Position mit Menge, EP und GP")
    else:
        teile = pruefabdeckung.text(rechnung).removeprefix("Rechenprüfung: ").split(", ", 1)
        k_rechnung = Kachel("Rechenprüfung", teile[-1], teile[0] if len(teile) == 2 else "")
    zahl = {s: sum(f["stufe"] == s for f in funde) for s in STUFEN}
    return [Kachel("Positionen", de_zahl(e["positionen"]), "laut Parser"),
            Kachel("Funde", de_zahl(len(funde)), "Hinweise zur Klärung"),
            k_abdeckung, k_rechnung] + [Kachel(stufe_name(s), de_zahl(zahl[s]), "Funde") for s in STUFEN]


# --------------------------------------------------------------------------- Belege und KI

def beleg_html(text):
    return f'<blockquote class="lv-beleg">{_html_text(text)}</blockquote>'


def beleg(text):
    """Wörtliches Zitat ohne Markdown-Verarbeitung, damit es Zeichen für Zeichen stehen bleibt (R5)."""
    st.html(beleg_html(text))


def textblock(text):
    """Kurz- oder Langtext der Position, wörtlich und mit Zeilenumbrüchen."""
    st.html(f'<div class="lv-text">{_html_text(text) if text else "–"}</div>')


def erfahrung_bereich(schluessel):
    """Bereich „Erfahrung“ (M2c): frühere menschliche Entscheidungen, neutral und nur Anzeige; Aufruf mit `with`.
    Nie grün, nie entwarnend: die Einordnung des Regel-Funds bleibt unverändert."""
    return st.container(border=True, key=f"lv_erf_{re.sub(r'[^A-Za-z0-9_-]', '_', str(schluessel))}")


def abzeichen_erfahrung():
    return _abzeichen("gray", "Erfahrung: frühere Entscheidung eines Menschen")


def entscheidung_bereich(schluessel):
    """Bereich „Entscheidung“: Begründung und Statusknöpfe gehören sichtbar zusammen; Aufruf mit `with`."""
    return st.container(border=True, key=f"lv_ents_{re.sub(r'[^A-Za-z0-9_-]', '_', str(schluessel))}")


def ki_bereich(schluessel):
    """Eigener, gestrichelt umrandeter Bereich für KI-Vorschläge (E13); Aufruf mit `with`."""
    return st.container(border=True, key=f"lv_ki_{re.sub(r'[^A-Za-z0-9_-]', '_', str(schluessel))}")


# --------------------------------------------------------------------------- Navigation

def navigation():
    """Einheitliche Navigation mit fachlichen Namen. Sind die Seiten nicht registriert (z. B. AppTest einer Einzelseite),
    bleibt die Standard-Navigation von Streamlit."""
    if not all((Path(__file__).resolve().parent / pfad).exists() for pfad, _ in SEITEN):
        return False
    with st.sidebar:
        try:
            for pfad, name in SEITEN:
                st.page_link(pfad, label=name)
        except StreamlitAPIException:
            return False
    if not os.environ.get(OHNE_CSS):
        st.markdown('<style>[data-testid="stSidebarNav"]{display:none}</style>', unsafe_allow_html=True)
    return True


# --------------------------------------------------------------------------- CSS

SYSTEMFARBEN = {"textColor": "CanvasText", "grayTextColor": "GrayText", "borderColor": "GrayText",
                "backgroundColor": "Canvas", "secondaryBackgroundColor": "Canvas", "primaryColor": "LinkText",
                "blueBackgroundColor": "Mark", "blueTextColor": "MarkText"}


def _farbe(theme, name):
    """`light-dark(hell, dunkel)` aus .streamlit/config.toml; folgt dem aktiven Streamlit-Theme.
    Fehlen die Abschnitte [theme.light]/[theme.dark], gelten Systemfarben: lesbar in beiden Modi."""
    hell, dunkel = theme.get("light", {}).get(name), theme.get("dark", {}).get(name)
    return f"light-dark({hell}, {dunkel})" if hell and dunkel else SYSTEMFARBEN[name]


def textfarbe():
    """Textfarbe des aktiven Themes für Diagrammbeschriftungen (Vega zeichnet ohne CSS). Quelle: config.toml;
    Modus aus st.context.theme.type, ohne Angabe die dunkle Variante (Dark-first)."""
    theme = tomllib.loads(CONFIG.read_text(encoding="utf-8")).get("theme", {})
    try:
        modus = st.context.theme.type or "dark"
    except Exception:                                  # z. B. außerhalb eines Laufs
        modus = "dark"
    return theme.get(modus, {}).get("textColor") or theme.get("dark", {}).get("textColor") or "#808080"


def css():
    theme = tomllib.loads(CONFIG.read_text(encoding="utf-8")).get("theme", {})
    f = lambda name: _farbe(theme, name)
    return f"""<style>
[data-testid="stApp"] {{
  --lv-text: {f("textColor")}; --lv-text-2: {f("grayTextColor")}; --lv-rand: {f("borderColor")};
  --lv-flaeche: {f("backgroundColor")}; --lv-flaeche-2: {f("secondaryBackgroundColor")};
  --lv-akzent: {f("primaryColor")}; --lv-markierung: {f("blueBackgroundColor")};
  --lv-markierung-text: {f("blueTextColor")};
}}
[data-testid="stElementContainer"]:has(> [data-testid="stMarkdown"] style) {{ display: none; }}
[data-testid="stMainBlockContainer"] {{
  max-width: 90rem; padding: 3.75rem clamp(1rem, 3vw, 2.5rem) 4rem;
}}
[data-testid="stHeading"] h1, [data-testid="stHeading"] h2, [data-testid="stHeading"] h3 {{
  letter-spacing: -0.012em; text-wrap: balance; padding-block: 0.15rem;
}}
.st-key-lv_kopf {{
  gap: 0.5rem; padding-bottom: 1rem; margin-bottom: 0.5rem; border-bottom: 1px solid var(--lv-rand);
}}
.st-key-lv_kopf [data-testid="stHeading"] h1 {{ line-height: 1.3; padding-block: 0 0.1rem; }}
.st-key-lv_kopf [data-testid="stCaptionContainer"] p {{ color: var(--lv-text-2); font-size: 0.9rem; }}

[data-testid="stApp"] dl.lv-kennzahlen {{
  display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 1px; margin: 0; padding: 0;
  background: var(--lv-rand); border: 1px solid var(--lv-rand); border-radius: 8px; overflow: hidden;
}}
.lv-kennzahl {{ background: var(--lv-flaeche); padding: 0.75rem 1rem 0.8rem; min-width: 0; }}
.lv-kennzahl dt {{ color: var(--lv-text-2); font-size: 0.8rem; font-weight: 500; line-height: 1.3; }}
.lv-kennzahl dd {{ margin: 0; }}
.lv-kennzahl .lv-kennzahl-wert {{
  color: var(--lv-text); font-size: 1.3rem; font-weight: 620; line-height: 1.35; margin-top: 0.2rem;
  font-variant-numeric: tabular-nums; overflow-wrap: anywhere;
}}
.lv-kennzahl .lv-kennzahl-hinweis {{ color: var(--lv-text-2); font-size: 0.76rem; line-height: 1.3; }}
@media (max-width: 52rem) {{
  [data-testid="stApp"] dl.lv-kennzahlen {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
}}

.lv-beleg {{
  margin: 0; padding: 0.65rem 0.85rem; max-width: 75ch; color: var(--lv-text); background: var(--lv-flaeche-2);
  border: 1px solid var(--lv-rand); border-radius: 6px; font-size: 0.95rem; line-height: 1.55;
  overflow-wrap: anywhere;
}}
.lv-text {{
  max-width: 75ch; max-height: 24rem; overflow-y: auto; color: var(--lv-text); font-size: 0.93rem; line-height: 1.55;
  overflow-wrap: anywhere;
}}
.lv-beleg mark {{ color: var(--lv-markierung-text); background: var(--lv-markierung); border-radius: 2px; padding: 0 2px; }}
[class*="st-key-lv_ki_"] {{ border-style: dashed !important; }}
[class*="st-key-lv_erf_"] {{ background: var(--lv-flaeche); }}
[class*="st-key-lv_ents_"] {{ border-color: var(--lv-rand-stark, var(--lv-rand)) !important; }}

[data-baseweb="tag"] {{
  background-color: var(--lv-markierung) !important; color: var(--lv-markierung-text) !important;
  border-radius: 4px !important;
}}
[data-baseweb="tag"] :is(span, svg) {{ color: inherit !important; fill: currentColor; }}
[data-testid="stMetric"] {{ padding: 0.75rem 1rem; border-radius: 8px; }}
[data-testid="stMetricLabel"], [data-testid="stMetricLabel"] * {{
  white-space: normal !important; overflow: visible !important; text-overflow: clip !important;
}}
[data-testid="stMetricLabel"] p {{ color: var(--lv-text-2); font-size: 0.8rem; font-weight: 500; line-height: 1.3; }}
[data-testid="stMetricValue"] {{ font-size: 1.3rem; font-weight: 620; }}
[data-testid="stMetricValue"], [data-testid="stDataFrame"] {{ font-variant-numeric: tabular-nums; }}
[data-testid="stBaseButton-primary"], [data-testid="stBaseButton-secondary"], [data-testid="stPageLink-NavLink"] {{
  transition: background-color 150ms ease-out, border-color 150ms ease-out, color 150ms ease-out;
}}
:is(button, a, input, [role="button"], [tabindex="0"]):focus-visible {{
  outline: 2px solid var(--lv-akzent); outline-offset: 1px;
}}
@media (prefers-reduced-motion: reduce) {{ * {{ transition: none !important; }} }}
</style>"""


def stil_einbinden():
    """Bindet das CSS ein (je Seite einmal aufrufen). LV_UI_OHNE_CSS=1 lässt es weg (Prüfung der Nutzbarkeit)."""
    if not os.environ.get(OHNE_CSS):
        st.markdown(css(), unsafe_allow_html=True)
