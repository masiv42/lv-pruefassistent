"""
lv_sitzung.py - B8e (Sitzung UI2, Team 22.11.2026): das aktuelle LV als zentraler Session-Eintrag (A1).

Ursache des Ablauffehlers (belegt mit AppTest auf c4ad20f): Streamlit löscht den Zustand eines Widgets, sobald eine
Seite ohne dieses Widget läuft. Das Upload-Feld liefert nach einem Seitenwechsel deshalb None, die Excel-Zuordnung
(map_*) und das Begründungsfeld (begr-<fid>, M2c) verlieren ihren Wert. Hier liegen Name, Bytes, Zuordnung und die
Begründungstexte in einfachen Session-Schlüsseln, die einen Seitenwechsel überstehen.

Regeln: Nur ein neuer Upload ersetzt das aktuelle LV (sichtbar, mit „ersetzt …“). Leeren des Upload-Felds (X) oder ein
Seitenwechsel entfernt es nicht; das tut nur „Anderes LV laden“. Funde, Fund-IDs und Status bleiben unberührt: Der
Status liegt wie bisher unter lv-<sha> und wird nur über setze_status() in app.py gespeichert (A4).
"""
import hashlib

import streamlit as st

AKTUELL = "lv_aktuell"            # {name, daten, sha, zuordnung, ersetzt}
BEGRUENDUNG = "lv_begruendung"    # {fund_id: Text}
_ZAEHLER = "lv_upload_nr"         # neuer Schlüssel für ein leeres Upload-Feld nach „Anderes LV laden“


def status_schluessel(name, daten, zuordnung=()):
    """Session-Schlüssel der Funde mit Status. Ohne Excel-Zuordnung wie bisher (sha256 aus Name und Bytes); mit Zuordnung
    geht sie in den Schlüssel ein, damit nach einer geänderten Zuordnung keine alten Funde stehen bleiben (Auflage 2)."""
    roh = name.encode() + daten
    if zuordnung:
        roh += repr(tuple(sorted(dict(zuordnung).items()))).encode()
    return "lv-" + hashlib.sha256(roh).hexdigest()[:16]


def aktuelles_lv():
    return st.session_state.get(AKTUELL)


def _upload_key():
    return f"lv_upload_{st.session_state.get(_ZAEHLER, 0)}"


def _uebernehmen(key):
    up = st.session_state.get(key)
    if up is None:                      # X am Upload-Feld: das aktuelle LV bleibt
        return
    daten = up.getvalue()
    alt = st.session_state.get(AKTUELL)
    if alt and alt["name"] == up.name and alt["daten"] == daten:
        return
    st.session_state[AKTUELL] = {"name": up.name, "daten": daten, "sha": hashlib.sha256(daten).hexdigest(),
                                 "zuordnung": {}, "ersetzt": alt["name"] if alt else None}


def lv_schliessen():
    """„Anderes LV laden“: entfernt das aktuelle LV aus der Sitzung (nicht den gespeicherten Status) und zeigt ein
    leeres Upload-Feld."""
    st.session_state[AKTUELL] = None
    st.session_state[_ZAEHLER] = st.session_state.get(_ZAEHLER, 0) + 1


def upload_feld(label):
    """Upload-Feld. Ohne aktuelles LV offen; mit aktuellem LV eingeklappt unter „Anderes LV hochladen“.
    Gibt das aktuelle LV (dict) oder None zurück."""
    key = _upload_key()
    if aktuelles_lv() is None:
        st.file_uploader(label, key=key, on_change=_uebernehmen, args=(key,))
    else:
        with st.expander("Anderes LV hochladen"):
            st.file_uploader(label, key=key, on_change=_uebernehmen, args=(key,))
            st.button("Anderes LV laden", on_click=lv_schliessen,
                      help="Entfernt das aktuelle LV aus dieser Sitzung. Gespeicherte Status bleiben erhalten.")
    akt = aktuelles_lv()
    if akt and akt.get("ersetzt"):
        st.caption(f"Aktuelles LV: {akt['name']} (ersetzt {akt['ersetzt']})")
    return akt


def begruendung(fid):
    return (st.session_state.get(BEGRUENDUNG) or {}).get(fid, "")


def begruendung_feld(fid, label):
    """Begründungsfeld (M2c) mit zentral gemerktem Text (Auflage 3). Der Widget-Schlüssel bleibt begr-<fid>, damit
    setze_status() ihn wie bisher liest."""
    key = f"begr-{fid}"
    speicher = st.session_state.setdefault(BEGRUENDUNG, {})

    def merken():
        speicher[fid] = st.session_state.get(key, "")

    return st.text_input(label, key=key, value=speicher.get(fid, ""), on_change=merken)


# --------------------------------------------------------------------------- A3: Sprünge und Filter (UI2)

FOKUS = "lv_fokus"                # {"fund_id": …} oder {"oz": …}; wird von der Zielseite einmal gelesen
FILTER = "lv_filter"              # {lv-sha: {widget-key: Wert}} – Filter und Auswahl überstehen den Seitenwechsel


def fokus_setzen(**ziel):
    st.session_state[FOKUS] = dict(ziel)


def fokus_nehmen(art):
    """Gibt das Sprungziel der Art `art` ("fund_id" oder "oz") zurück und entfernt es (einmalig)."""
    ziel = st.session_state.get(FOKUS) or {}
    if art in ziel:
        st.session_state[FOKUS] = None
        return ziel[art]
    return None


def _ablage():
    akt = aktuelles_lv() or {}
    return st.session_state.setdefault(FILTER, {}).setdefault(akt.get("sha", "-"), {})


def filter_vorbereiten(key, standard, gueltig=None):
    """Setzt den Zustand eines Filter-Widgets vor seiner Erzeugung: gemerkter Wert dieses LV, sonst `standard`.
    `gueltig`: erlaubte Optionen (Listen werden darauf gekürzt, Einzelwerte sonst auf `standard` gesetzt).
    Das Widget wird danach ohne default/value/index erzeugt."""
    if key not in st.session_state:
        st.session_state[key] = _ablage().get(key, standard)
    wert = st.session_state[key]
    if gueltig is not None:
        gueltig = list(gueltig)
        if isinstance(wert, list):
            st.session_state[key] = [w for w in wert if w in gueltig]
        elif wert not in gueltig:
            st.session_state[key] = standard


def filter_merken(*keys):
    ablage = _ablage()
    for k in keys:
        if k in st.session_state:
            ablage[k] = st.session_state[k]
