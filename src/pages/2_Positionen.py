"""
2_Positionen.py - Positions-Explorer (Sitzung UI, Team 22.11.2026).

Zeigt alle Positionen des auf der Hauptseite geprüften LV aus st.session_state:
  st.session_state["lv_uebersicht"]  Funde und Kennzahlen (vorhanden seit B2-Integration)
  st.session_state["lv_positionen"] = {"lv_name", "format", "zeilen": info["tabelle"], "daten": bytes}  (Vorschlag UI)
Die Seite prüft nichts, rechnet keine Beträge und setzt keinen Status: Jede Zahl ist ein Feld der Parser-Ausgabe oder eine
Zählung der Funde. Ein Fund mit mehreren Positionen steht bei jeder davon und zählt in der Fundzahl einmal.
"""
import hashlib
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))     # src/ für die Projektmodule
from bericht import STUFEN, beleg_pruefung, lade_s2               # noqa: E402
from pruefung_formal import oz_sortkey, sortiere                  # noqa: E402
import ui_stil                                                    # noqa: E402
import lv_sitzung                                                 # noqa: E402

KENNZEICHNUNG = "Daten aus der automatischen Auswertung (Parser)"
LEER = "Noch kein LV geprüft. Bitte auf der Seite „LV-Prüfung“ ein LV hochladen; die Positionen erscheinen danach hier."
FEHLT = "Die Positionsdaten dieses LV liegen nicht vor. Bitte das LV auf der Seite „LV-Prüfung“ erneut hochladen."
SORTIERUNG = ("OZ", "Höchste Stufe", "Anzahl Funde", "GP laut LV")
SPALTEN = ["OZ", "Titel", "Kurztext", "Menge", "Einheit", "EP", "GP", "Funde", "Höchste Stufe"]


# --------------------------------------------------------------------------- Daten

def zuordnen(zeilen, funde):
    """Hängt jeder Zeile ihre Funde an. Eine doppelte OZ führt zu mehreren Zeilen; der Fund steht bei jeder davon."""
    je_oz = {}
    for f in sortiere(list(funde)):
        for oz in dict.fromkeys(p["oz"] for p in f["positionen"]):
            je_oz.setdefault(oz, []).append(f)
    aus = []
    for i, z in enumerate(zeilen):
        eigene = je_oz.get(z["oz"], [])
        aus.append({**z, "zeile": i, "funde": eigene,
                    "hoechste_stufe": min((f["stufe"] for f in eigene), default=None)})
    return aus


def fund_ids(zeilen):
    return {f["id"] for z in zeilen for f in z["funde"]}


def abschnitte(zeilen):
    return list(dict.fromkeys(z["titel"] for z in zeilen if z["titel"]))


def filtere(zeilen, suche="", titel=(), stufen=(), nur_mit_fund=False):
    worte = suche.casefold().split()
    aus = []
    for z in zeilen:
        if titel and z["titel"] not in titel:
            continue
        if nur_mit_fund and not z["funde"]:
            continue
        if stufen and not any(f["stufe"] in stufen for f in z["funde"]):
            continue
        heuhaufen = " ".join((z["oz"], z["titel"], z["kurztext"], z["langtext"])).casefold()
        if all(w in heuhaufen for w in worte):
            aus.append(z)
    return aus


def sortierte(zeilen, art="OZ"):
    nach_oz = sorted(zeilen, key=lambda z: (oz_sortkey(z["oz"]), z["zeile"]))
    if art == "Höchste Stufe":          # Stufe 1 zuerst, Positionen ohne Fund zuletzt
        return sorted(nach_oz, key=lambda z: (z["hoechste_stufe"] is None, z["hoechste_stufe"] or 0))
    if art == "Anzahl Funde":
        return sorted(nach_oz, key=lambda z: -len(z["funde"]))
    if art == "GP laut LV":             # leere Preise zuletzt, nie als 0
        return sorted(nach_oz, key=lambda z: (z["gp"] is None, -(z["gp"] or 0)))
    return nach_oz


def tabelle(zeilen):
    return pd.DataFrame([{
        "OZ": z["oz"], "Titel": z["titel"], "Kurztext": z["kurztext"], "Menge": z["menge"], "Einheit": z["einheit"],
        "EP": z["ep"], "GP": z["gp"], "Funde": len(z["funde"]),
        "Höchste Stufe": ui_stil.stufe_name(z["hoechste_stufe"]) if z["hoechste_stufe"] else "",
    } for z in zeilen], columns=SPALTEN).astype({"Menge": "Float64", "EP": "Float64", "GP": "Float64"})


def _de(wert, stellen):
    if wert is None or wert != wert:
        return "–"
    return f"{wert:,.{stellen}f}".replace(",", "X").replace(".", ",").replace("X", ".")


# --------------------------------------------------------------------------- Ansicht

def detail(z, pruef):
    st.subheader(f"OZ {ui_stil.md_text(z['oz'])}", anchor=False)
    if z["titel"]:
        st.caption(ui_stil.md_text(z["titel"]))
    einheit = f" {z['einheit']}" if z["einheit"] else ""
    ui_stil.kacheln([ui_stil.Kachel("Menge", _de(z["menge"], 3) + (einheit if z["menge"] is not None else ""), "laut LV"),
                     ui_stil.Kachel("EP", _de(z["ep"], 2), "laut LV"),
                     ui_stil.Kachel("GP", _de(z["gp"], 2), "laut LV"),
                     ui_stil.Kachel("Funde", ui_stil.de_zahl(len(z["funde"])),
                                    f"Seite {z['seite']}" if z["seite"] else "")])
    links, rechts = st.columns(2, gap="large")
    with links:
        st.markdown("**Kurztext**")
        ui_stil.textblock(z["kurztext"])
        st.markdown("**Langtext**")
        ui_stil.textblock(z["langtext"])
    with rechts:
        st.markdown(f"**Funde dieser Position ({len(z['funde'])})**")
        if not z["funde"]:
            st.caption("Kein Fund der Prüfungen Nr. 1–19. Das heißt nicht, dass die Position ohne Fehler oder Risiken ist.")
        for f in z["funde"]:
            with st.container(border=True):
                st.markdown(ui_stil.abzeichen_fund(f, pruef.get(f["id"])))
                st.markdown(f"**Nr. {f['pruefung']} {ui_stil.md_text(f['titel'])}**")
                for b in f["belege"]:
                    ui_stil.beleg(b)
                for fb in f.get("feldbelege", []):
                    st.caption(f"{ui_stil.md_text(fb['art'])}: {ui_stil.md_text(fb['text'])}")
                st.markdown(ui_stil.md_text(f["begruendung"]))
                if f.get("rueckfrage"):
                    st.caption(f"Mögliche Rückfrage: {ui_stil.md_text(f['rueckfrage'])}")
                if st.button("Fund öffnen", key=f"fund-oeffnen-{f['id']}-{z['zeile']}",
                             help="Öffnet den Fund auf der Seite „LV-Prüfung“ (Status setzen, KI-Vorschlag)."):
                    lv_sitzung.fokus_setzen(fund_id=f["id"])     # A3 (UI2)
                    st.switch_page("app.py")
        if z["funde"]:
            st.caption("Status setzen und KI-Vorschläge ansehen: Seite „LV-Prüfung“.")


def seite():
    st.set_page_config(page_title="Positionen · LV-Prüfassistent", layout="wide")
    ui_stil.stil_einbinden()
    ui_stil.navigation()
    e = st.session_state.get("lv_uebersicht")
    p = st.session_state.get("lv_positionen")
    if not e:
        ui_stil.kopf("Positionen", "Noch kein LV geladen")
        st.info(LEER)
        return
    if not p or p.get("lv_name") != e["lv_name"] or p.get("zeilen") is None:
        ui_stil.kopf("Positionen", ui_stil.kontext_lv(e))
        st.warning(FEHLT)
        return

    funde = e.get("funde") or []
    zeilen = zuordnen(p["zeilen"], funde)
    mit_fund = sum(bool(z["funde"]) for z in zeilen)
    ui_stil.kopf("Positionen", ui_stil.kontext_lv(e))
    st.caption(KENNZEICHNUNG)

    # A3 (UI2): Filter überstehen den Seitenwechsel; ein Sprung zur OZ setzt die Filter dieser Seite zurück
    ziel_oz = lv_sitzung.fokus_nehmen("oz")
    if ziel_oz is not None:
        for k, w in (("pos_suche", ""), ("pos_titel", []), ("pos_stufe", []), ("pos_nur_fund", False)):
            st.session_state[k] = w
        treffer = [z["zeile"] for z in zeilen if z["oz"] == ziel_oz]
        if treffer:
            st.session_state["pos_wahl"] = treffer[0]
        st.session_state["pos_ziel"] = (ziel_oz, len(treffer))
    lv_sitzung.filter_vorbereiten("pos_suche", "")
    lv_sitzung.filter_vorbereiten("pos_titel", [], abschnitte(zeilen))
    lv_sitzung.filter_vorbereiten("pos_stufe", [], list(STUFEN))
    lv_sitzung.filter_vorbereiten("pos_sortierung", SORTIERUNG[0], SORTIERUNG)
    lv_sitzung.filter_vorbereiten("pos_nur_fund", False)
    a, b = st.columns(2)
    suche = a.text_input("Suche", placeholder="OZ, Titel, Kurz- oder Langtext", key="pos_suche")
    titel = b.multiselect("Titel / Abschnitt", abschnitte(zeilen), key="pos_titel", placeholder="Alle Abschnitte")
    c, d, g = st.columns([2, 2, 1], vertical_alignment="bottom")
    stufen = c.multiselect("Stufe", list(STUFEN), key="pos_stufe", format_func=ui_stil.stufe_name, placeholder="Alle Stufen")
    art = d.selectbox("Sortierung", SORTIERUNG, key="pos_sortierung")
    nur = g.toggle("Nur mit Fund", key="pos_nur_fund")
    lv_sitzung.filter_merken("pos_suche", "pos_titel", "pos_stufe", "pos_sortierung", "pos_nur_fund")
    ziel = st.session_state.pop("pos_ziel", None)
    if ziel:
        st.caption(f"Sprung zur OZ {ui_stil.md_text(ziel[0])}: Filter dieser Seite zurückgesetzt."
                   + (f" Die OZ kommt {ziel[1]}-mal vor; alle Zeilen stehen in der Auswahl „Position öffnen“."
                      if ziel[1] > 1 else "")
                   + (" Die OZ steht in keiner Position dieses LV." if ziel[1] == 0 else ""))

    sichtbar = sortierte(filtere(zeilen, suche, titel, stufen, nur), art)
    ui_stil.kacheln([ui_stil.Kachel("Positionen", ui_stil.de_zahl(len(zeilen)), "im LV"),
                     ui_stil.Kachel("Mit Fund", ui_stil.de_zahl(mit_fund), "Positionen"),
                     ui_stil.Kachel("Funde", ui_stil.de_zahl(len(fund_ids(zeilen))), "Hinweise zur Klärung"),
                     ui_stil.Kachel("Angezeigt", ui_stil.de_zahl(len(sichtbar)), "Positionen nach Filter")])
    mehrfach = sum(z_n > 1 for z_n in (len({x["oz"] for x in f["positionen"]}) for f in funde))
    if mehrfach:
        st.caption(f"{ui_stil.de_zahl(mehrfach)} Funde betreffen mehrere Positionen. Sie stehen bei jeder dieser "
                   "Positionen und zählen in der Fundzahl einmal.")
    if not sichtbar:
        st.info("Keine Position passt zum Filter.")
        return

    df = tabelle(sichtbar)
    stil = df.style.format({"Menge": lambda x: "" if pd.isna(x) else _de(x, 3),
                            "EP": lambda x: "" if pd.isna(x) else _de(x, 2),
                            "GP": lambda x: "" if pd.isna(x) else _de(x, 2)})
    schluessel = hashlib.sha256("|".join(str(z["zeile"]) for z in sichtbar).encode()).hexdigest()[:12]
    ereignis = st.dataframe(
        stil, key=f"pos_tabelle_{schluessel}", on_select="rerun", selection_mode="single-row", hide_index=True,
        width="stretch", height=min(44 + 35 * len(sichtbar), 460), placeholder="–",
        column_config={"OZ": st.column_config.TextColumn(width=84, pinned=True),
                       "Titel": st.column_config.TextColumn(width=170),
                       "Kurztext": st.column_config.TextColumn(width=300),
                       "Menge": st.column_config.NumberColumn(width=78),
                       "Einheit": st.column_config.TextColumn(width=62),
                       "EP": st.column_config.NumberColumn(width=78),
                       "GP": st.column_config.NumberColumn(width=92),
                       "Funde": st.column_config.NumberColumn(width=58),
                       "Höchste Stufe": st.column_config.TextColumn(width=214)})

    gezeigt = [z["zeile"] for z in sichtbar]
    auswahl = (schluessel, tuple(ereignis.selection.rows))
    if auswahl != st.session_state.get("pos_tabelle_letzte"):
        st.session_state["pos_tabelle_letzte"] = auswahl
        if auswahl[1]:
            st.session_state["pos_wahl"] = sichtbar[auswahl[1][0]]["zeile"]
    lv_sitzung.filter_vorbereiten("pos_wahl", gezeigt[0], gezeigt)
    nach_zeile = {z["zeile"]: z for z in zeilen}
    anzahl_oz = {}
    for z in zeilen:
        anzahl_oz[z["oz"]] = anzahl_oz.get(z["oz"], 0) + 1
    wahl = st.selectbox("Position öffnen", gezeigt, key="pos_wahl",
                        format_func=lambda i: f"OZ {nach_zeile[i]['oz']}"
                        + (f" (OZ doppelt, {anzahl_oz[nach_zeile[i]['oz']]}×)" if anzahl_oz[nach_zeile[i]['oz']] > 1 else "")
                        + f" – {nach_zeile[i]['kurztext'][:90]}")
    lv_sitzung.filter_merken("pos_wahl")
    st.divider()
    s2, _ = lade_s2()
    pruef = {f["id"]: beleg_pruefung(f, s2) for f in nach_zeile[wahl]["funde"]}
    detail(nach_zeile[wahl], pruef)


if __name__ == "__main__":
    seite()
