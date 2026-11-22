"""
lv_daten.py - Gemeinsame Auswertung des aktuellen LV für alle Seiten (Sitzung UI2, Block UI3, Team 22.11.2026).

Eine Quelle für alle Seiten: das aktuelle LV aus lv_sitzung (Name, Bytes, Excel-Zuordnung) → analysiere() (einmal je
Eingabe, st.cache_data) → Funde mit Status aus der bestehenden Ablage (status_ablage, Schlüssel lv-<sha> wie bisher).
Keine Prüflogik hier: pruefe_lv() aus bericht.py liefert Funde, Texte und Kennzahlen unverändert.
"""
import copy
import io
import tempfile
from datetime import datetime
from pathlib import Path

import streamlit as st

import lv_sitzung
from bericht import pruefe_lv, risikobericht, dateiname, beleg_pruefung, lade_s2
from status_ablage import lade_status

XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
STATUS = ["offen", "bestätigt", "verworfen", "Rückfrage stellen"]


@st.cache_data(show_spinner="LV wird gelesen und geprüft …")
def analysiere(name, daten, zuordnung=()):
    """Parst das hochgeladene LV in einem Temp-Ordner und prüft es. `zuordnung`: Excel-Spalten als Tupel (Cache).
    Gibt Funde (Status 'offen'), Positionstexte je Fund-ID und Kennzahlen zurück."""
    with tempfile.TemporaryDirectory() as d:
        pfad = Path(d) / Path(name).name
        pfad.write_bytes(daten)
        funde, texte, info = pruefe_lv(pfad, dict(zuordnung) or None)   # PDF: Seitentexte aus der Datei
    info["zeitpunkt"] = datetime.now().astimezone()   # Zeitpunkt der Prüfung mit Zeitzone (Bericht)
    return funde, texte, info


def ist_excel(name):
    return str(name).lower().endswith((".xlsx", ".xlsm"))


def excel_kopf(daten):
    import pandas as pd
    return list(pd.read_excel(io.BytesIO(daten), nrows=0, engine="openpyxl").columns.astype(str))


def zuordnung_vollstaendig(akt):
    from excel_import import PFLICHT
    return all(f in (akt.get("zuordnung") or {}) for f in PFLICHT)


def lade():
    """Stand des aktuellen LV für jede Seite.
    Rückgabe None (kein LV) oder dict mit "zustand": "ok" | "zuordnung" (Excel-Spalten fehlen) | "fehler"."""
    akt = lv_sitzung.aktuelles_lv()
    if akt is None:
        return None
    name, daten = akt["name"], akt["daten"]
    zuordnung = dict(akt.get("zuordnung") or {})
    if ist_excel(name) and not zuordnung_vollstaendig(akt):
        return {"zustand": "zuordnung", "name": name, "daten": daten, "akt": akt}
    try:
        funde_neu, texte, info = analysiere(name, daten, tuple(sorted(zuordnung.items())))
    except ValueError as e:
        return {"zustand": "fehler", "name": name, "meldung": str(e), "akt": akt}
    schluessel = lv_sitzung.status_schluessel(name, daten, tuple(sorted(zuordnung.items())))
    if schluessel not in st.session_state:                         # Status aus data/findings/ (gleiche Fund-ID)
        gespeichert = lade_status(name)
        st.session_state[schluessel] = {"datei": name,
                                        "funde": [dict(f, status=gespeichert.get(f["id"], "offen")) for f in funde_neu]}
    funde = st.session_state[schluessel]["funde"]
    return {"zustand": "ok", "name": name, "daten": daten, "sha": akt["sha"], "akt": akt, "info": info,
            "texte": texte, "funde": funde, "schluessel": schluessel}


def ki_cache(stand):
    """KI-Gegenprüfung nur aus dem Cache (kein API-Aufruf), wie auf der Prüfseite für den Risikobericht."""
    from ki_pruefung import lade_konfig, aus_cache
    return aus_cache(stand["funde"], stand["texte"], lade_konfig())


def status_zaehlung(funde):
    return {s: sum(f["status"] == s for f in funde) for s in STATUS}


def beleg_stand(funde):
    """Automatische Belegprüfung am Original (S2-Liste, keine menschliche Prüfung): {fund_id: geprüft|ungeprüft|…}."""
    s2, stand = lade_s2()
    return {f["id"]: beleg_pruefung(f, s2) for f in funde}, stand


def beleg_abgleich_vorhanden(funde):
    """True, wenn es für dieses LV überhaupt einen automatischen Abgleich gibt (S2 kennt nur Dateien des Datensatzes).
    Ohne Abgleich ist „0 % bestätigt“ falsch – angezeigt wird „–“ (R11, keine Entwarnung und keine Scheinzahl)."""
    s2, _ = lade_s2()
    return any(f["id"] in s2 for f in funde)


def downloads(name, funde, texte, info, ki=None):
    """Risikobericht und Bieterfragen (Entwurf); `daten` ist eine Funktion, die erst beim Klick rechnet (mit Kopie des
    angezeigten Stands). Gleiche Dateien wie bisher."""
    from bieterfragen import bieterfragen, ausgenommen, xlsx_bytes
    stand = copy.deepcopy(funde)
    ki_stand = copy.deepcopy(ki)

    def bericht():
        return risikobericht(name, stand, texte, info, zeitpunkt=info["zeitpunkt"], ki=ki_stand)

    def fragen():
        return xlsx_bytes(bieterfragen(stand), ausgenommen(stand))

    return [
        {"label": "Risikobericht herunterladen (.xlsx)", "dateiname": dateiname(name, info["zeitpunkt"]),
         "daten": bericht, "mime": XLSX},
        {"label": "Bieterfragen (Entwurf, .xlsx)", "dateiname": "Bieterfragen_" + Path(name).stem + ".xlsx",
         "daten": fragen, "mime": XLSX},
    ]


def kompatibel_ablegen(stand, ki_aktiv=False):
    """Session-Schlüssel der bestehenden Seiten (Übersicht, Positionen, Nachtrag): lv_uebersicht, lv_positionen."""
    info = stand["info"]
    st.session_state["lv_uebersicht"] = {
        "lv_name": stand["name"], "format": info["format"], "positionen": info["positionen"],
        "nur_preise": info["nur_preise"], "abdeckung": info["abdeckung"], "funde": stand["funde"],
        "kurztexte": info["kurztexte"], "gp": info["gp"], "ki_aktiv": ki_aktiv}
    st.session_state["lv_positionen"] = {"lv_name": stand["name"], "format": info["format"],
                                         "zeilen": info.get("tabelle"), "daten": stand["daten"]}


ROUTER_SHA = "_lv_router_sha"


def router_merken(stand):
    """app.py merkt sich, welches LV die Seitenleiste zeigt (sha oder None)."""
    st.session_state[ROUTER_SHA] = (stand or {}).get("sha") if stand and stand.get("zustand") == "ok" else None


def router_abgleichen(stand):
    """Hat die Seite ein anderes LV als die Seitenleiste (z. B. direkt nach dem Upload), einmal neu laufen lassen."""
    sha = stand.get("sha") if stand and stand.get("zustand") == "ok" else None
    if ROUTER_SHA in st.session_state and st.session_state[ROUTER_SHA] != sha:
        st.session_state[ROUTER_SHA] = sha
        st.rerun()
