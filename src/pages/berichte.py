"""
pages/berichte.py - Berichte und Export (Sitzung UI2, Block UI3): die vorhandenen Exporte gebündelt und erklärt.
Dieselben Dateien wie bisher (lv_daten.downloads → bericht.risikobericht, bieterfragen); erzeugt erst beim Klick.
"""
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))     # src/
import lv_daten                                                   # noqa: E402
import oberflaeche as ui                                          # noqa: E402

st.set_page_config(page_title="Berichte & Export · LV-Prüfassistent", layout="wide")
ui.seitenkopf("Berichte & Export", "Alles, was Sie für die Angebotsabgabe weitergeben, als Excel – mit Beleg, Prüfstand "
              "und Ihren Entscheidungen.", eyebrow="Auswertung")
stand = lv_daten.lade()
if not stand or stand["zustand"] != "ok":
    ui.leer("Noch kein LV geprüft", "Laden Sie auf der Startseite ein LV hoch; danach stehen hier der Risikobericht "
            "und die Bieterfragen (Entwurf) bereit.")
    if st.button("Zur Startseite", type="primary"):
        st.switch_page("pages/uebersicht.py")
    st.stop()

funde = stand["funde"]
z = lv_daten.status_zaehlung(funde)
dl = lv_daten.downloads(stand["name"], funde, stand["texte"], stand["info"], lv_daten.ki_cache(stand))
links, rechts = st.columns(2, gap="large")
with links:
    with ui.karte("bericht"):
        st.html('<div class="lv-panel-titel">Risikobericht (.xlsx)</div>'
                '<ul class="lv-liste"><li>alle Funde mit Kategorie, Stufe, Rang und wörtlichem Beleg</li>'
                '<li>Ihre Entscheidungen (bestätigt, verworfen, Rückfrage) und Begründungen</li>'
                '<li>Prüfstand (Commit, Prüfsumme der Datei) und Prüfabdeckung je Prüfung</li>'
                '<li>Blätter „Nachtrag und Streitpunkte“ und „KI-Vorschläge“ (getrennt, mit Warnhinweis)</li></ul>')
        st.html(f'<div class="lv-meta" style="margin:.5rem 0 .8rem">{ui.de_zahl(len(funde))} Funde · entschieden '
                f'{ui.de_zahl(len(funde) - z["offen"])} · offen {ui.de_zahl(z["offen"])}</div>')
        st.download_button(dl[0]["label"], data=dl[0]["daten"], file_name=dl[0]["dateiname"], mime=dl[0]["mime"],
                           type="primary", width="stretch", key="be_bericht")
with rechts:
    with ui.karte("fragen"):
        st.html('<div class="lv-panel-titel">Bieterfragen (Entwurf, .xlsx)</div>'
                '<ul class="lv-liste"><li>je Fund mit Rückfrage-Entwurf eine Frage an den Auftraggeber</li>'
                '<li>mit OZ und Beleg, damit die Frage nachvollziehbar bleibt</li>'
                '<li>ein Entwurf: vor dem Versand prüfen und anpassen</li></ul>')
        st.html(f'<div class="lv-meta" style="margin:.5rem 0 .8rem">{ui.de_zahl(sum(bool(f.get("rueckfrage")) for f in funde))}'
                ' Funde mit Rückfrage-Entwurf</div>')
        st.download_button(dl[1]["label"], data=dl[1]["daten"], file_name=dl[1]["dateiname"], mime=dl[1]["mime"],
                           width="stretch", key="be_fragen")
ui.hinweis("Die Exporte enthalten den Stand dieser Sitzung. Ein Fund ohne Entscheidung bleibt „offen“; das ist keine "
           "Entwarnung.")
