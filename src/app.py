"""
app.py - Startdatei und Navigation des LV-Prüfassistenten (Sitzung UI2, Block UI3 „Redesign“, Team 22.11.2026).

Registriert die Seiten (st.navigation, eigene Seitenleiste mit Gruppen), bindet das Designsystem (src/oberflaeche.py)
ein und zeigt Statusleiste und Karte „Aktuelles LV“. Die Seiten liegen in src/pages/; die Prüfseite mit Status,
Erfahrung und KI steht in src/pages/funde.py.

Start aus der Projektwurzel (unverändert):
  uv run --no-project --python 3.12 --with streamlit==1.67.0 --with pdfplumber==0.11.11 --with lxml==6.1.3 \
      --with pandas==3.1.1 --with openpyxl==3.1.5 --with anthropic==2.12.0 --with openai==3.57.0 streamlit run src/app.py \
      --server.address localhost --browser.gatherUsageStats false
(nur auf diesem Rechner erreichbar, keine Nutzungsstatistik an Streamlit)
"""
import hashlib
import os
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lv_daten                                                   # noqa: E402
import lv_sitzung                                                 # noqa: E402
import oberflaeche as ui                                          # noqa: E402
import ui_stil                                                    # noqa: E402

st.set_page_config(page_title="LV-Prüfassistent", layout="wide", initial_sidebar_state="expanded")

GRUPPEN = [
    ("Prüfung", [
        st.Page("pages/uebersicht.py", title="Entscheidungsübersicht", default=True),
        st.Page("pages/funde.py", title="Funde prüfen"),
        st.Page("pages/2_Positionen.py", title="Alle Positionen"),
    ]),
    ("Auswertung", [
        st.Page("pages/3_Nachtrag_und_Streitpunkte.py", title="Mögliches Nachtragspotenzial"),
        st.Page("pages/1_Zuschlag_und_What-if.py", title="Zuschlag & What-if"),
        st.Page("pages/berichte.py", title="Berichte & Export"),
    ]),
    ("Hilfe", [
        st.Page("pages/hilfe.py", title="So funktioniert’s"),
    ]),
]

seite = st.navigation([p for _, seiten in GRUPPEN for p in seiten], position="hidden")
st.session_state[ui_stil.ROUTER] = True                          # bestehende Seiten zeichnen im neuen Design
ui.stil_einbinden()

# Nur für Bildschirmprüfungen durch Agenten mit einer erfundenen Datei (Team F4): LV_UI_VORSCHAU=<Pfad> lädt sie als
# aktuelles LV, solange keins geladen ist. Ohne die Variable ohne Wirkung.
_vorschau = os.environ.get("LV_UI_VORSCHAU", "").strip()
if _vorschau and lv_sitzung.aktuelles_lv() is None and Path(_vorschau).is_file():
    _b = Path(_vorschau).read_bytes()
    st.session_state[lv_sitzung.AKTUELL] = {"name": Path(_vorschau).name, "daten": _b,
                                            "sha": hashlib.sha256(_b).hexdigest(), "zuordnung": {}, "ersetzt": None}

stand = lv_daten.lade()                                           # dieselbe Auswertung für alle Seiten (Cache)
lv = None
if stand and stand["zustand"] == "ok":
    lv_daten.kompatibel_ablegen(stand)
    lv = {"name": stand["name"], "format": stand["info"]["format"], "positionen": stand["info"]["positionen"],
          "funde": len(stand["funde"])}
elif stand:
    lv = {"name": stand["name"], "format": "–", "positionen": None, "funde": None}
lv_daten.router_merken(stand)
ui.seitenleiste(GRUPPEN, lv)
bereich = next((name for name, seiten in GRUPPEN if any(p.url_path == seite.url_path for p in seiten)), "")
ui.statusleiste(bereich, seite.title, bool(stand and stand["zustand"] == "ok"))
seite.run()
