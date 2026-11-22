"""
3_Nachtrag_und_Streitpunkte.py - M2b (Team, 22.11.2026, 01:25). Sicht auf vorhandene Regel-Funde (src/nachtrag_streit.py).
Liest die Ergebnisse der Hauptseite aus st.session_state["lv_uebersicht"]. Einfache Streamlit-Bausteine; das Design
übernimmt die Sitzung UI (UI2: Kopf, Navigation und Stil aus src/ui_stil.py; Logik unverändert).
"""
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bericht import PRUEFUNGEN                                     # noqa: E402
from nachtrag_streit import ABSCHNITTE, HINWEIS, KEINE, SEITENTITEL, SPALTEN, zaehlung, zeilen   # noqa: E402
import ui_stil                                                     # noqa: E402

LEER = ("Noch kein LV geprüft. Bitte auf der Hauptseite „LV-Prüfung“ ein LV hochladen; die Sicht erscheint danach "
        "hier.")

# R7 (Team 22.11.2026, Block B3): Anzeige „Mögliches Nachtragspotenzial“; SEITENTITEL bleibt (Blattname im Export, Tests)
ANZEIGE_TITEL = "Mögliches Nachtragspotenzial und mögliche Streitpunkte"


def hinweis_oben():
    """Im neuen Design der neutrale Hinweis-Baustein, sonst st.info (gleicher Wortlaut)."""
    if ui_stil.neues_design():
        import oberflaeche
        oberflaeche.hinweis(HINWEIS)
    else:
        st.info(HINWEIS)


SPALTEN_BREITE = {"Nr.": 48, "Abschnitt": 220, "OZ": 96, "Kurztext": 260, "Beleg (wörtlich aus dem LV)": 360,
                  "Prüfung": 200, "Kategorie": 150, "Stufe": 170, "Handlungsempfehlung": 160,
                  "Bieterfrage (Entwurf)": 360, "Status": 110, "Fund-ID": 220}

st.set_page_config(page_title="Mögliches Nachtragspotenzial · LV-Prüfassistent", layout="wide")
ui_stil.stil_einbinden()
ui_stil.navigation()
e = st.session_state.get("lv_uebersicht")
if not e:
    ui_stil.kopf(ANZEIGE_TITEL if ui_stil.neues_design() else SEITENTITEL, "Noch kein LV geladen")
    hinweis_oben()
    st.write(LEER)
    st.stop()

funde = e.get("funde") or []
kurz = e.get("kurztexte") or {}
ui_stil.kopf(ANZEIGE_TITEL if ui_stil.neues_design() else SEITENTITEL,
             f"{Path(e['lv_name']).name} · {ui_stil.de_zahl(e['positionen'])} Positionen")
hinweis_oben()
st.markdown("Sicht auf die vorhandenen Regel-Funde, jeder mit wörtlichem Beleg.")
st.caption("Die Zahlen sind Zählungen je LV. KI-Vorschläge ändern diese Liste nicht; sie stehen in der Detailansicht und "
           "im Blatt „KI-Vorschläge“. Export: Blatt „Nachtrag und Streitpunkte“ im Risikobericht.")
zahlen, alle = zaehlung(funde), zeilen(funde, kurz.get)
for spalte, (k, a) in zip(st.columns(len(ABSCHNITTE)), ABSCHNITTE.items()):
    spalte.metric(a["titel"], zahlen[k]["gesamt"], border=True)
for k, a in ABSCHNITTE.items():
    st.subheader(a["titel"])
    st.caption(a["erklaerung"])
    st.caption(" · ".join(f"Nr. {nr} {PRUEFUNGEN[nr]}: {n}" for nr, n in zahlen[k]["je_pruefung"].items()))
    liste = [{s: z[s] for s in SPALTEN if s != "Abschnitt"} for z in alle if z["Abschnitt"] == a["titel"]]
    if liste:
        st.dataframe(liste, hide_index=True, width="stretch",          # B3: Spaltenbreiten statt Abschneiden
                     column_config={s: st.column_config.TextColumn(width=w) for s, w in SPALTEN_BREITE.items()
                                    if s != "Abschnitt"})
    else:
        st.write(KEINE)
