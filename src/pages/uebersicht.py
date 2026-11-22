"""
pages/uebersicht.py - Start und Entscheidungsübersicht (Sitzung UI2, Block UI3, Team-Entwurf „Entscheidungsübersicht“).

Ohne LV: Startseite, die in einem Satz erklärt, was das Tool tut, das LV entgegennimmt und den Ablauf zeigt.
Mit LV: „Was muss vor der Angebotsabgabe geklärt werden?“ – Kennzahlen, „Zuerst klären“ (Sortierung Stufe, Rang, OZ wie
im Risikobericht), Belegfokus des gewählten Funds, Fortschritt der menschlichen Entscheidungen, Export.
Jede Zahl ist eine Zählung des aktuellen LV (R11). Status setzt nur der Mensch auf der Seite „Funde prüfen“ (A4, E12).
"""
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))     # src/
import lv_daten                                                   # noqa: E402
import lv_sitzung                                                 # noqa: E402
import oberflaeche as ui                                          # noqa: E402
from pruefung_formal import sortiere, datei_hinweis               # noqa: E402
from bericht import NUR_PREISE_TEXT                               # noqa: E402

FUNDE_SEITE = "pages/funde.py"
POSITIONEN_SEITE = "pages/2_Positionen.py"
LEITFRAGE = "Was muss vor der Angebotsabgabe geklärt werden?"
AUSWAHL = "ue_auswahl"


SPRUNG = "ue_sprung"


def _zu_fund(fid):
    lv_sitzung.fokus_setzen(fund_id=fid)
    st.session_state[SPRUNG] = FUNDE_SEITE


def _zu_position(oz):
    lv_sitzung.fokus_setzen(oz=oz)
    st.session_state[SPRUNG] = POSITIONEN_SEITE


def _waehlen(fid):
    st.session_state[AUSWAHL] = fid


def upload_bereich(titel="LV hochladen"):
    with ui.karte("upload"):
        st.html(f'<div class="lv-label" style="margin-top:0">{ui.h(titel)}</div>'
                '<p class="lv-text">GAEB XML (.x83, .x84 …), GAEB 90 (.d83, .d84 …), PDF oder Excel. Die Datei bleibt '
                'auf diesem Rechner; geprüft wird nur, was im LV steht.</p>')
        lv_sitzung.upload_feld("LV-Datei auswählen oder hierher ziehen")


def start():
    links, rechts = st.columns([0.92, 1.08], gap="large", vertical_alignment="center")
    with links:
        ui.seitenkopf(LEITFRAGE, "Der LV-Prüfassistent liest Ihr Leistungsverzeichnis, prüft jede Position mit 19 festen "
                      "Regeln und zeigt jeden Fund mit dem wörtlichen Beleg aus dem Original. Sie entscheiden – das Tool "
                      "benennt, es urteilt nicht.", eyebrow="LV-Prüfung vor der Angebotsabgabe")
        lv_sitzung.upload_feld("LV hochladen · GAEB XML, GAEB 90, PDF oder Excel")
        st.caption("Die Datei bleibt auf diesem Rechner. Geprüft wird nur, was im LV steht.")
    with rechts:
        st.html(ui.lv_blatt_html())
    ui.abschnitt("So arbeiten Sie damit")
    ui.schritte([("LV hochladen", "GAEB, PDF oder Excel. Die Prüfung startet direkt nach dem Hochladen."),
                 ("Funde mit Beleg prüfen", "Jeder Fund zeigt die betroffene Position und das wörtliche Zitat aus dem LV."),
                 ("Entscheiden und exportieren", "Bestätigen, verwerfen oder Rückfrage stellen. Der Risikobericht "
                  "enthält alles mit Beleg.")])
    ui.abschnitt("Was geprüft wird", "Reihenfolge = Arbeitsreihenfolge")
    ui.stufen_erklaerung()
    ui.abschnitt("Was das Tool nicht tut")
    st.html('<div class="lv-grenzen">'
            '<div><b>Keine Preise.</b> Es ermittelt und schlägt keine Preise vor; Zuschläge rechnen Sie selbst.</div>'
            '<div><b>Keine Rechtsaussage.</b> Funde sind Hinweise zur Klärung, kein Urteil über Ansprüche.</div>'
            '<div><b>Keine Vollständigkeitsgarantie.</b> Geprüft wird mit 19 Regeln; ohne Fund heißt nicht fehlerfrei.</div>'
            '<div><b>KI nur als Vorschlag.</b> KI-Hinweise sind getrennt gekennzeichnet und ändern nie einen Fund.</div>'
            '</div>')


def excel_zuordnung(stand):
    from excel_import import spalten_vorschlag, FELDER, PFLICHT, KENNZEICHNUNG
    ui.seitenkopf("Spalten zuordnen", "Bei Excel-Dateien sagen Sie einmal, welche Spalte was enthält. Danach startet "
                  "die Prüfung.", eyebrow="Excel-Import")
    ui.hinweis(KENNZEICHNUNG)
    akt = stand["akt"]
    kopf = lv_daten.excel_kopf(stand["daten"])
    vorschlag = spalten_vorschlag(kopf)
    zuordnung = {}
    with ui.karte("excel"):
        spalten = st.columns(2)
        for i, feld in enumerate(FELDER):
            gemerkt = akt["zuordnung"].get(feld, vorschlag.get(feld))
            wahl = spalten[i % 2].selectbox(feld + (" (Pflicht)" if feld in PFLICHT else ""), ["–"] + kopf,
                                            key=f"ue_map_{feld}", index=(kopf.index(gemerkt) + 1) if gemerkt in kopf else 0)
            if wahl != "–":
                zuordnung[feld] = wahl
    if st.button("Prüfung starten", type="primary", disabled=not all(f in zuordnung for f in PFLICHT)):
        akt["zuordnung"] = dict(zuordnung)
        st.rerun()
    if not all(f in zuordnung for f in PFLICHT):
        st.caption("Bitte mindestens OZ und Kurztext zuordnen.")


def uebersicht(stand):
    info, funde = stand["info"], stand["funde"]
    zeit = info["zeitpunkt"].strftime("%d.%m.%Y, %H:%M") if info.get("zeitpunkt") else "–"
    kopf_l, kopf_r = st.columns([3, 1.15], vertical_alignment="center")
    with kopf_l:                                                     # B1: Leitfrage nur ohne LV; mit LV kompakter Kopf
        ui.kompaktkopf("Entscheidungsübersicht", f"{Path(stand['name']).name} · {info['format']} · "
                       f"{ui.de_zahl(info['positionen'])} Positionen geprüft · Stand {zeit}")
    downloads = lv_daten.downloads(stand["name"], funde, stand["texte"], info, lv_daten.ki_cache(stand))
    with kopf_r:
        d = downloads[0]
        st.download_button("Risikobericht exportieren", data=d["daten"], file_name=d["dateiname"], mime=d["mime"],
                           type="primary", width="stretch", key="ue_dl_bericht")
    if info["nur_preise"]:
        ui.hinweis(f"{Path(stand['name']).name}: {NUR_PREISE_TEXT}", "bernstein")
    if datei_hinweis(stand["name"]):
        ui.hinweis(datei_hinweis(stand["name"]))

    pruef, s2_stand = lv_daten.beleg_stand(funde)
    bestaetigt_auto = sum(v == "geprüft" for v in pruef.values())
    abgleich = lv_daten.beleg_abgleich_vorhanden(funde)              # nur Dateien des Datensatzes haben einen Abgleich
    stufe1 = sum(f["stufe"] == 1 for f in funde)
    fehler_n = sum(f["stufe"] == 1 and f["kategorie"] == "nachweisbarer Fehler" for f in funde)
    entwuerfe = sum(bool(f.get("rueckfrage")) for f in funde)
    offen_n = sum(f["status"] in ("offen", "Rückfrage stellen") for f in funde)
    ui.kennzahlen([
        ui.Kennzahl("Noch zu klären", ui.de_zahl(offen_n), f"von {ui.de_zahl(len(funde))} Funden in "
                    f"{ui.de_zahl(ui.positionen_mit_fund(info.get('tabelle'), funde))} von "
                    f"{ui.de_zahl(info['positionen'])} Positionen"),
        ui.Kennzahl("Fehlerprüfung", ui.de_zahl(stufe1), "Funde der Stufe 1 · davon "
                    + ui.anzahl_wort(fehler_n, "nachweisbarer Fehler", "nachweisbare Fehler")),                       # Stufen neutral; Rot nur für die Kategorie (R6)
        ui.Kennzahl("Mit Rückfrage-Entwurf", ui.de_zahl(entwuerfe), "Entwurf, vor Versand prüfen",
                    "bernstein" if entwuerfe else "text"),
        ui.Kennzahl("Beleg am Original bestätigt", ui.de_prozent(bestaetigt_auto, len(funde)) if abgleich else "–",
                    "automatischer Abgleich, ersetzt nicht Ihre Prüfung" if abgleich
                    else "für diese Datei kein automatischer Abgleich – Belege selbst prüfen",
                    "gruen" if abgleich and bestaetigt_auto else "text"),
    ])
    if not funde:
        ui.leer("Keine Funde für die Prüfungen Nr. 1–19",
                "Das heißt nicht, dass das LV ohne Fehler oder Risiken ist; geprüft wurden nur diese Prüfungen.")
        return

    offen = [f for f in sortiere(list(funde)) if f["status"] in ("offen", "Rückfrage stellen")]
    liste = offen[:7]
    links, rechts = st.columns([1.3, 1], gap="large")
    with links:
        ui.abschnitt("Zuerst klären", "nach Stufe · Rang · OZ")
        if not liste:
            ui.leer("Alle Funde entschieden", "Jeder Fund ist bestätigt oder verworfen. Der Risikobericht enthält "
                    "Ihre Entscheidungen mit Beleg.")
        auswahl = st.session_state.get(AUSWAHL)
        if liste and auswahl not in {f["id"] for f in liste}:
            auswahl = liste[0]["id"]
        for f in liste:
            rechts_html = ui.chip_status(f["status"]) if f["status"] != "offen" else ui.chip("Beleg prüfen", "text")
            ui.klickbare_zeile(f"ue-{f['id']}", ui.fund_zeile_html(f, rechts_html), f"Fund ansehen: {f['titel']}",
                               on_click=_waehlen, args=(f["id"],), aktiv=f["id"] == auswahl)
        if len(offen) > len(liste):
            st.caption(f"{ui.de_zahl(len(offen) - len(liste))} weitere offene Funde auf „Funde prüfen“.")
        if st.button(f"Alle {ui.de_zahl(len(funde))} Funde prüfen", key="ue_alle"):
            st.switch_page(FUNDE_SEITE)
    with rechts:
        f = next((x for x in funde if x["id"] == auswahl), None) if liste else None
        if f is not None:
            belegfokus(f, pruef.get(f["id"]), stand)

    ui.abschnitt("Wo im LV die Funde liegen", "jede Position ein Strich · Farbe = Kategorie des Funds mit der höchsten Stufe")
    ui.lv_karte(info.get("tabelle") or [], funde)
    ui.abschnitt("Verteilung der Funde", "alle Funde dieses LV")
    v1, v2 = st.columns(2, gap="large")
    with v1:
        ui.verteilung("Nach Stufe", [(f"{s} – {n}", sum(f["stufe"] == s for f in funde), "neutral")
                                     for s, n in ui.STUFEN.items()])
    with v2:
        ui.verteilung("Nach Kategorie", [(k, sum(f["kategorie"] == k for f in funde), ton)
                                         for k, ton in ui.KATEGORIE_TON.items()])
    ui.abschnitt("Fortschritt")
    z = lv_daten.status_zaehlung(funde)
    entschieden = z["bestätigt"] + z["verworfen"] + z["Rückfrage stellen"]
    a, b, c = st.columns([1.1, 1.1, 1], gap="large")
    with a:
        ui.fortschritt("Ihre Entscheidungen", entschieden, len(funde), "akzent",
                       f"bestätigt {ui.de_zahl(z['bestätigt'])} · verworfen {ui.de_zahl(z['verworfen'])} · "
                       f"Rückfrage {ui.de_zahl(z['Rückfrage stellen'])} – nur durch Sie")
    with b:
        if abgleich:
            ui.fortschritt("Beleg automatisch am Original bestätigt", bestaetigt_auto, len(funde), "gruen",
                           f"Stand {s2_stand or '–'}; nicht bestätigt heißt: noch nicht abgeglichen, keine Entwarnung")
        else:
            ui.hinweis("Automatischer Belegabgleich: für diese Datei nicht vorhanden (er liegt nur für die Dateien des "
                       "Datensatzes vor). Jeder Beleg ist wörtlich aus dem LV; prüfen Sie ihn im Original.")
    with c:
        with ui.karte("export"):
            st.html('<div class="lv-text" style="margin:0 0 .6rem">Der Excel-Bericht enthält alle Funde mit Beleg, '
                    'Ihre Entscheidungen und die Bieterfragen als Entwurf.</div>')
            d = downloads[1]
            st.download_button("Bieterfragen (Entwurf)", data=d["daten"], file_name=d["dateiname"], mime=d["mime"],
                               width="stretch", key="ue_dl_fragen")


def belegfokus(f, beleg_pruefung, stand):
    oz = ", ".join(p["oz"] for p in f["positionen"])
    with ui.panel(f"ue-{f['id']}"):
        st.html(f'<div class="lv-panel-kopf"><div class="lv-panel-titel">{ui.h(f["titel"])}</div>'
                f'{ui.chip_kategorie(f["kategorie"])}</div>'
                f'<div class="lv-meta"><span class="lv-mono">OZ {ui.h(oz)}</span> · Stufe {f["stufe"]} – '
                f'{ui.h(ui.STUFEN.get(f["stufe"], ""))} · Prüfung Nr. {f["pruefung"]}</div>'
                + ui.beleg_label_html(beleg_pruefung))           # A2: Kennzeichnung nach echtem Beleg-Status
        for b in f["belege"]:
            ui.beleg(b, oz=f["positionen"][0]["oz"], pruefung=f["pruefung"])
        for fb in f.get("feldbelege", []):
            st.html(f'<div class="lv-meta">{ui.h(fb["art"])}: <span class="lv-mono">{ui.h(fb["text"])}</span></div>')
        st.html(f'<div class="lv-label">Warum relevant</div><div class="lv-text">{ui.h(f["begruendung"])}</div>')
        if f.get("rueckfrage"):
            with st.expander("Bieterfrage (Entwurf)"):
                st.html(f'<div class="lv-text">{ui.h(f["rueckfrage"])}</div>')
                st.caption("Entwurf aus der Regelprüfung – vor dem Versand prüfen und anpassen.")
        a, b = st.columns(2)
        a.button("Fund bearbeiten", key=f"ue-bearb-{f['id']}", type="primary", width="stretch",
                 on_click=_zu_fund, args=(f["id"],))
        b.button("Zur Position", key=f"ue-pos-{f['id']}", width="stretch",
                 on_click=_zu_position, args=(f["positionen"][0]["oz"],))
    sprung = st.session_state.pop(SPRUNG, None)          # Klick auf „Fund bearbeiten“ / „Zur Position“
    if sprung:
        st.switch_page(sprung)


st.set_page_config(page_title="Übersicht · LV-Prüfassistent", layout="wide")
_stand = lv_daten.lade()
if _stand and _stand["zustand"] == "ok":
    lv_daten.kompatibel_ablegen(_stand)                            # auch ohne Lauf des Routers (direkt nach dem Upload)
lv_daten.router_abgleichen(_stand)                                 # Seitenleiste nach dem Upload sofort aktuell
if _stand is None:
    start()
elif _stand["zustand"] == "zuordnung":
    excel_zuordnung(_stand)
elif _stand["zustand"] == "fehler":
    ui.seitenkopf("Datei kann nicht gelesen werden", _stand["meldung"], eyebrow="LV hochladen")
    upload_bereich("Andere Datei hochladen")
else:
    uebersicht(_stand)
    lv_sitzung.upload_feld("Anderes LV hochladen (GAEB XML, GAEB 90, PDF oder Excel)")
