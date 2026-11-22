"""
0_Uebersicht.py - Block B8a: Übersichtsseite (Sitzung B2, Team 21.11.2026, 21:20). Streamlit-Seite unter src/pages/.

Liest die Ergebnisse der Hauptseite aus st.session_state (Schlüssel = Vorschlag für Sitzung B1, siehe
docs/uebergabe_sitzung_B2.md „Integrations-Vorschlag“):
  st.session_state["lv_uebersicht"] = {
      "lv_name": str,                  # Dateiname ohne Pfad
      "format": str, "positionen": int, "nur_preise": bool,
      "abdeckung": [ {pruefung, name, pruefbar, gesamt, gruende} ],   # pruefabdeckung.abdeckung(df)
      "funde": [ Fund nach docs/data-contracts.md ],
      "kurztexte": {oz: Kurztext},     # aus parse()
      "gp": {oz: GP oder None},        # aus parse(); nur bepreiste LVs haben Werte > 0
      "ki_aktiv": bool,
  }
  st.session_state["lv_downloads"] = [ {"label", "daten" (bytes oder Funktion ohne Argumente, UI2), "dateiname", "mime"} ]   (optional)
Doktrin: nichts ausblenden (alle Stufen und Prüfungen, auch mit 0), keine Zahl ohne Quelle (jede Zahl ist eine
Zählung der Funde dieser Datei), keine Preisbewertung (nur Summe GP laut LV, ausdrücklich „kein Risikobetrag“,
R11, E9), Kategorie und Stufe wie im Fund, Beleg wörtlich (R5), KI-Hinweis nach E13. Keine Dateipfade.
"""
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))     # src/ für die Projektmodule
from pruefung_formal import sortiere                              # noqa: E402
import ui_stil                                                    # noqa: E402
import lv_sitzung                                                 # noqa: E402

STUFEN = {1: "Fehlerprüfung", 2: "Kalkulationsrisiko", 3: "mögliches Nachtragspotenzial", 4: "Unklarheit"}
BALKEN = "#7C8BA3"                                                # neutral: Stufen tragen keine Warnfarbe (R6)
POSITIONSWERT = "Positionswert laut LV (Summe GP) – kein Risikobetrag"
KI_HINWEIS = ("KI-Vorschläge entwarnen nie: Sie ändern weder Stufe, Rang, Sortierung noch Hervorhebung eines "
              "Regel-Funds (E13). Einordnungen wie „anderes Bauteil“ stehen erst in der Detailansicht, mit Warnhinweis.")
LEER = "Noch kein LV geprüft. Bitte auf der Hauptseite ein LV hochladen; die Übersicht erscheint danach hier."


def stufe_name(s):
    return f"{s} – {STUFEN[s]}"


def kachel_zahlen(funde):
    return {s: sum(f["stufe"] == s for f in funde) for s in STUFEN}


def zuerst(funde, n=5):
    return sortiere(list(funde))[:n]


def positionswert(funde, gp):
    """Summe GP der Positionen mit Fund je Stufe (jede Position je Stufe einmal) oder None, wenn unbepreist."""
    if not any((v or 0) > 0 for v in gp.values()):
        return None
    out = {}
    for s in STUFEN:
        ozs = {p["oz"] for f in funde if f["stufe"] == s for p in f["positionen"]}
        out[s] = sum((gp.get(o) or 0) for o in ozs)
    return out


def diagramm_daten(funde):
    zeilen = {}
    for f in funde:
        k = (f["pruefung"], f["titel"].split(" (")[0], f["stufe"])
        zeilen[k] = zeilen.get(k, 0) + 1
    return pd.DataFrame([{"Prüfung": f"Nr. {nr} {t}", "Nr": nr, "Stufe": stufe_name(s), "Funde": n}
                         for (nr, t, s), n in sorted(zeilen.items())])


def _eur(x):
    return f"{x:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def seite():
    ui_stil.stil_einbinden()
    ui_stil.navigation()
    e = st.session_state.get("lv_uebersicht")
    if not e:
        ui_stil.kopf("Übersicht", "Noch kein LV geladen")
        st.info(LEER)
        return
    funde = e.get("funde") or []
    ui_stil.kopf("Übersicht", f"{ui_stil.kontext_lv(e)} · {ui_stil.de_zahl(len(funde))} Funde")
    if e.get("nur_preise"):
        st.warning("Datei enthält nur Preise, bitte das LV mit Texten hochladen.")
    ui_stil.kacheln(ui_stil.kacheln_lv(e)[:4])
    if ui_stil.abdeckung_hinweis(e.get("abdeckung") or []):
        st.caption(ui_stil.abdeckung_hinweis(e["abdeckung"]))

    st.subheader("Funde je Stufe")
    zahlen = kachel_zahlen(funde)
    werte = positionswert(funde, e.get("gp") or {})
    for s, spalte in zip(STUFEN, st.columns(4)):
        with spalte:
            st.metric(stufe_name(s), zahlen[s], border=True)
            if werte is not None:
                st.caption(f"{POSITIONSWERT}: {_eur(werte[s])}")
    if werte is not None:
        st.caption("Eine Position mit Funden in mehreren Stufen zählt in jeder dieser Stufen.")

    st.subheader("Zuerst ansehen")
    st.caption("Die ersten 5 Funde in der Sortierung Stufe, Rang in Stufe, OZ.")
    kurz = e.get("kurztexte") or {}
    for i_f, f in enumerate(zuerst(funde)):
        p = f["positionen"][0]
        with st.container(border=True):
            st.markdown(f"{ui_stil.abzeichen_stufe(f['stufe'])} {ui_stil.abzeichen_kategorie(f['kategorie'])}")
            st.markdown(f"**Nr. {f['pruefung']} {ui_stil.md_text(f['titel'])}** · "
                        f"OZ {', '.join(ui_stil.md_text(x['oz']) for x in f['positionen'])}")
            st.write(f"Kurztext: {ui_stil.md_text(kurz.get(p['oz'], '')) or '–'}")       # R5: wörtlich (UI2)
            for b in f["belege"]:
                st.markdown("> " + ui_stil.md_text(b.replace("\n", " ")))
            k1, k2, _ = st.columns([1, 1, 3])                          # A3 (UI2): Dashboard → Fund / Position
            if k1.button("Fund öffnen", key=f"ue-fund-{i_f}", width="stretch"):
                lv_sitzung.fokus_setzen(fund_id=f["id"])
                st.switch_page("pages/funde.py")
            if k2.button("Zur Position", key=f"ue-pos-{i_f}", width="stretch"):
                lv_sitzung.fokus_setzen(oz=p["oz"])
                st.switch_page("pages/2_Positionen.py")

    st.subheader("Funde je Prüfung")
    daten = diagramm_daten(funde)
    if daten.empty:
        st.write("Keine Funde.")
    else:
        import altair as alt
        basis = alt.Chart(daten)
        balken = basis.mark_bar(color=BALKEN, cornerRadiusEnd=3, size=14).encode(
            x=alt.X("sum(Funde):Q", title="Funde", axis=alt.Axis(tickMinStep=1, grid=False)),
            y=alt.Y("Prüfung:N", sort=alt.SortField("Nr"), title=None, axis=alt.Axis(labelLimit=320)),
            tooltip=["Prüfung", "Stufe", "Funde"])
        # UI2 (Auflage 7): ein neutraler Ton, Zahl je Prüfung am Balkenende in Textfarbe (nicht in Balkenfarbe)
        summe = daten.groupby(["Prüfung", "Nr"], as_index=False)["Funde"].sum()
        summe["Zahl"] = summe["Funde"].map(ui_stil.de_zahl)          # deutsche Schreibweise (1.234)
        zahl = alt.Chart(summe).mark_text(align="left", dx=4, fontSize=12, color=ui_stil.textfarbe()).encode(
            x=alt.X("Funde:Q"), y=alt.Y("Prüfung:N", sort=alt.SortField("Nr")), text="Zahl:N")
        st.altair_chart(balken + zahl, width="stretch")

    if e.get("ki_aktiv"):
        st.info(KI_HINWEIS)
    else:
        st.caption(KI_HINWEIS)

    st.subheader("Downloads")
    downloads = st.session_state.get("lv_downloads") or []
    if not downloads:
        st.caption("Risikobericht und Bieterfragen stehen auf der Hauptseite zum Download bereit.")
    for i, d in enumerate(downloads):
        st.download_button(d["label"], data=d["daten"], file_name=d["dateiname"], mime=d.get("mime"), key=f"dl_{i}")


if __name__ == "__main__":
    seite()
