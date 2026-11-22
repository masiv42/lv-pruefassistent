"""
pages/funde.py - „Funde prüfen“: Arbeitswarteschlange und Belegfokus (Sitzung UI2, Block UI3 „Redesign“, Team 22.11.2026).

Links die Funde in der Arbeitsreihenfolge Stufe → Rang in Stufe → OZ (sortiere(), unverändert), gruppiert nach Stufe, mit
Filtern Status, Stufe, Kategorie und Suche. Rechts der gewählte Fund: wörtlicher Beleg (bei PDF auch als Bild der
Originalseite), Einordnung, Bieterfrage (Entwurf), KI-Vorschlag getrennt und nie entwarnend (E13), frühere menschliche
Entscheidungen (M2c) und die Entscheidung selbst – Status setzt nur der Mensch, gespeichert wie bisher (status_ablage).
Bis UI3-1 stand dieser Inhalt in src/app.py; Logik unverändert übernommen (setze_status, KI, B5, Vergleichspreise).
"""
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))     # src/
from pruefung_formal import sortiere, datei_hinweis                       # noqa: E402
from bericht import (lade_s2, beleg_pruefung, NUR_PREISE_TEXT, ki_warnhinweis, STUFEN, RANG,   # noqa: E402
                     ABDECKUNG_HINWEIS, PRUEFER)
from status_ablage import speichere, ablage_name                          # noqa: E402
import pruefstand                                                          # noqa: E402
import pruefabdeckung                                                      # noqa: E402
import ki_b5                                                               # noqa: E402
import ki_blatt                                                            # noqa: E402
import erfahrung                                                           # noqa: E402
import lv_sitzung                                                          # noqa: E402
import lv_daten                                                            # noqa: E402
import belegbild                                                           # noqa: E402
import oberflaeche as ui                                                   # noqa: E402
from ki_pruefung import (lade_konfig, ki_status, aus_cache, verbrauch_heute,   # noqa: E402
                         ki_funde, gegenpruefung, PREISE, MAX_AUFRUFE, GROQ_LIMITS)

ROOT = Path(__file__).resolve().parents[2]
STATUS = ["offen", "bestätigt", "verworfen", "Rückfrage stellen"]
STATUS_FILTER = {"Offen": ("offen",), "Rückfrage": ("Rückfrage stellen",), "Bestätigt": ("bestätigt",),
                 "Verworfen": ("verworfen",), "Alle": tuple(STATUS)}
HINWEIS_S2 = "Beleg noch nicht am Original geprüft."
GEPRUEFT = "Beleg am Original geprüft"
NICHT_IM_ORIGINAL = "Beleg steht so nicht wörtlich im Original"
SEITE_LISTE = 40                                                  # Zeilen je „Mehr anzeigen“


@st.cache_data(show_spinner="Vergleichspreise werden gelesen …")
def preisquellen_datensatz():
    """Bepreiste Dateien des Datensatzes (nur lesen, E11); D84 ohne Text nicht verknüpft (B2-F14, B2-L9)."""
    from vergleichspreise import preisquellen
    raw = ROOT / "data" / "raw"
    namen = ["Abgabe LV.pdf", "Angebot AN24-0305.pdf", "StBALV23040.D86", "[ORT_024] LV24069.D86"]
    return preisquellen([raw / n for n in namen if (raw / n).exists()])


def bericht_button(name, funde, texte, info, ki=None):
    """Download des Risikoberichts (immer alle Funde, unabhängig vom Filter) und der Bieterfragen (Entwurf)."""
    liste = lv_daten.downloads(name, funde, texte, info, ki)
    st.session_state["lv_downloads"] = liste
    spalten = st.columns(len(liste))
    for s, d in zip(spalten, liste):
        s.download_button(d["label"], data=d["daten"], file_name=d["dateiname"], mime=d["mime"], width="stretch")


def setze_status(schluessel, fid, status):
    eintrag = st.session_state[schluessel]
    for f in eintrag["funde"]:
        if f["id"] == fid:
            f["status"] = status
            geaendert = f
    speichere(eintrag["datei"], eintrag["funde"])
    # M2c: nur diese menschliche Aktion schreibt in die Erfahrungsdatenbank; ein Fehler dort ändert den Status nicht
    begr = st.session_state.get(f"begr-{fid}") or lv_sitzung.begruendung(fid)      # B8e: Text übersteht Seitenwechsel
    if not erfahrung.status_geaendert(geaendert, status, eintrag["datei"], begr):
        st.session_state["erfahrung_fehler"] = True


def _waehlen(fid):
    st.session_state["pf_fund"] = fid


def _mehr():
    st.session_state["pf_anzahl"] = st.session_state.get("pf_anzahl", SEITE_LISTE) + SEITE_LISTE


# --------------------------------------------------------------------------- Ansicht

st.set_page_config(page_title="Funde prüfen · LV-Prüfassistent", layout="wide")
stand = lv_daten.lade()
if stand and stand["zustand"] == "ok":
    lv_daten.kompatibel_ablegen(stand)
lv_daten.router_abgleichen(stand)
if stand is None or stand["zustand"] != "ok":
    ui.seitenkopf("Funde prüfen", "Hier prüfen Sie Fund für Fund mit Beleg und entscheiden.", eyebrow="Prüfung")
    if stand and stand["zustand"] == "zuordnung":
        ui.hinweis("Bei dieser Excel-Datei fehlt noch die Spalten-Zuordnung. Bitte auf der Startseite zuordnen.")
    elif stand and stand["zustand"] == "fehler":
        ui.hinweis(f"Datei kann nicht gelesen werden: {stand['meldung']}", "bernstein")
    else:
        ui.leer("Noch kein LV geladen", "Laden Sie auf der Startseite ein LV hoch. Danach erscheinen hier alle Funde "
                "in der Reihenfolge, in der Sie sie klären sollten.")
    if st.button("Zur Startseite", type="primary"):
        st.switch_page("pages/uebersicht.py")
    lv_sitzung.upload_feld("Ein LV hochladen (GAEB XML, GAEB 90, PDF oder Excel)")
    st.stop()

lv_name, daten, aktuell = stand["name"], stand["daten"], stand["akt"]
info, texte, schluessel = stand["info"], stand["texte"], stand["schluessel"]
funde = stand["funde"]
konfig = lade_konfig()
ki = aus_cache(funde, texte, konfig)
z = lv_daten.status_zaehlung(funde)

ui.seitenkopf("Funde prüfen", f"{Path(lv_name).name} · {ui.de_zahl(len(funde))} Funde · offen {ui.de_zahl(z['offen'])} · "
              f"Rückfrage {ui.de_zahl(z['Rückfrage stellen'])} · bestätigt {ui.de_zahl(z['bestätigt'])} · "
              f"verworfen {ui.de_zahl(z['verworfen'])}", eyebrow="Arbeitsreihenfolge: Stufe → Rang → OZ")
if info["nur_preise"]:
    ui.hinweis(f"{Path(lv_name).name}: {NUR_PREISE_TEXT}", "bernstein")
if datei_hinweis(lv_name):                       # Hinweis zur Datei, unterdrückt keinen Fund
    ui.hinweis(datei_hinweis(lv_name))
if not funde:
    ui.leer("Keine Funde für die Prüfungen Nr. 1–19", "Das heißt nicht, dass das LV ohne Fehler oder Risiken ist; "
            "geprüft wurden nur diese Prüfungen.")

s2, s2_stand = lade_s2()
pruef = {f["id"]: beleg_pruefung(f, s2) for f in funde}

if funde:
    # Filter (A3: überstehen den Seitenwechsel; ein Sprung macht den Ziel-Fund sichtbar)
    k_opt = sorted({f["kategorie"] for f in funde})
    s_opt = sorted({f["stufe"] for f in funde})
    ziel = lv_sitzung.fokus_nehmen("fund_id")
    if ziel is not None:
        st.session_state["pf_kat"], st.session_state["pf_stufe"] = list(k_opt), list(s_opt)
        st.session_state["pf_status"], st.session_state["pf_suche"] = "Alle", ""
        st.session_state["pf_fund"] = ziel
    lv_sitzung.filter_vorbereiten("pf_status", "Offen", list(STATUS_FILTER))
    lv_sitzung.filter_vorbereiten("pf_kat", list(k_opt), k_opt)
    lv_sitzung.filter_vorbereiten("pf_stufe", list(s_opt), s_opt)
    lv_sitzung.filter_vorbereiten("pf_suche", "")
    with st.container(key="pf_status_zeile"):                       # 1: Status in eigener Zeile, alle Optionen sichtbar
        status_wahl = st.segmented_control("Status", list(STATUS_FILTER), key="pf_status") or "Alle"
    f2, f3, f4 = st.container(key="pf_filter").columns([1.1, 1.3, 1.2], vertical_alignment="bottom")
    s_wahl = f2.multiselect("Stufe", s_opt, key="pf_stufe", format_func=lambda s: f"{s} – {STUFEN[s]}",
                            placeholder="Alle Stufen")
    k_wahl = f3.multiselect("Kategorie", k_opt, key="pf_kat", placeholder="Alle Kategorien")
    suche = f4.text_input("Suche", key="pf_suche", placeholder="OZ, Titel oder Fund-ID")
    lv_sitzung.filter_merken("pf_status", "pf_kat", "pf_stufe", "pf_suche")
    worte = suche.casefold().split()
    sichtbar = sortiere([f for f in funde if f["status"] in STATUS_FILTER[status_wahl]
                         and f["kategorie"] in k_wahl and f["stufe"] in s_wahl
                         and all(w in " ".join([f["id"], f["titel"], *(p["oz"] for p in f["positionen"])]).casefold()
                                 for w in worte)])
    # Der gewählte Fund bleibt nach einer Entscheidung offen (auch wenn er den Status-Filter nicht mehr erfüllt)
    passend = {f["id"] for f in funde if f["kategorie"] in k_wahl and f["stufe"] in s_wahl}
    if st.session_state.get("pf_fund") not in passend:
        st.session_state["pf_fund"] = sichtbar[0]["id"] if sichtbar else None
    naechster = next((x["id"] for x in sichtbar if x["status"] == "offen" and x["id"] != st.session_state["pf_fund"]),
                     None)

    links, rechts = st.columns([1.12, 1], gap="large")
    with links:
        st.caption(f"{ui.de_zahl(len(sichtbar))} von {ui.de_zahl(len(funde))} Funden, sortiert nach Stufe, dann {RANG}, "
                   "dann OZ")
        if not sichtbar:
            ui.leer("Kein Fund passt zum Filter", "Filter oben ändern, z. B. Status „Alle“.")
        anzahl = st.session_state.get("pf_anzahl", SEITE_LISTE)
        gezeigt = sichtbar[:anzahl]
        for s in sorted({f["stufe"] for f in gezeigt}):
            in_s = [f for f in gezeigt if f["stufe"] == s]
            gesamt_s = sum(f["stufe"] == s for f in sichtbar)
            ui.abschnitt(f"Stufe {s} · {STUFEN[s]}", f"{ui.de_zahl(gesamt_s)} Funde")
            for f in in_s:
                rechts_html = ui.chip_status(f["status"])
                ui.klickbare_zeile(f"pf-{f['id']}", ui.fund_zeile_html(f, rechts_html),
                                   f"Fund öffnen: OZ {f['positionen'][0]['oz']} – {f['titel']} ({f['status']})",
                                   on_click=_waehlen, args=(f["id"],), aktiv=f["id"] == st.session_state["pf_fund"])
        if len(sichtbar) > len(gezeigt):
            st.button(f"Weitere {ui.de_zahl(min(SEITE_LISTE, len(sichtbar) - len(gezeigt)))} anzeigen "
                      f"({ui.de_zahl(len(sichtbar) - len(gezeigt))} verbleibend)", on_click=_mehr, key="pf_mehr")

    f = next((x for x in funde if x["id"] == st.session_state.get("pf_fund")), None)
    with rechts:
        if f is None:
            ui.leer("Kein Fund gewählt", "Links einen Fund anklicken.")
        else:
            with ui.panel(f"pf-{f['id']}"):
                st.html(f'<div class="lv-label" style="margin-top:0">Belegfokus</div>'
                        f'<div class="lv-panel-kopf"><div class="lv-panel-titel">{ui.h(f["titel"])}</div>'
                        f'{ui.chip_kategorie(f["kategorie"])}</div>'
                        f'<div style="display:flex;gap:.4rem;flex-wrap:wrap;margin:.3rem 0 .5rem">'
                        f'{ui.chip_stufe(f["stufe"])}{ui.chip_status(f["status"])}</div>'
                        f'<div class="lv-meta">Prüfung Nr. {f["pruefung"]} · Prüfer: '
                        f'{ui.h(PRUEFER.get(f["pruefung"], "–"))} · {ui.h(RANG)}: {ui.h(f["prioritaet_in_stufe"])}</div>')
                for i_p, p in enumerate(f["positionen"]):
                    ort = f"{p['datei']} · OZ {p['oz']}" + (f" · Seite {p['seite']}" if p["seite"] is not None else "")
                    st.html(f'<div class="lv-meta lv-mono lv-ort">{ui.h(ort)}</div>')   # A4: bricht um, keine Spalten
                    if st.button("Zur Position", key=f"zur-pos-{f['id']}-{i_p}",
                                 help="Öffnet die Position mit allen ihren Funden; Filter hier bleiben erhalten."):
                        lv_sitzung.fokus_setzen(oz=p["oz"])             # A3 (UI2)
                        st.switch_page("pages/2_Positionen.py")
                st.html(ui.beleg_label_html(pruef[f["id"]]))      # A2: Kennzeichnung nach echtem Beleg-Status
                for b in f["belege"]:
                    ui.beleg(b, oz=f["positionen"][0]["oz"], pruefung=f["pruefung"])
                if lv_name.lower().endswith(".pdf"):                 # B8b (UI2): Beleg am Original als Bild, nur auf Klick
                    for i_p, p in enumerate(f["positionen"]):
                        if p["seite"] is not None and f["belege"]:
                            belegbild.anzeigen(daten, aktuell["sha"], int(p["seite"]), f["belege"], f"{f['id']}-{i_p}")
                for fb in f.get("feldbelege", []):              # kein Zitat: Feldwert oder Kennzeichen
                    st.html(f'<div class="lv-meta">{ui.h(fb["art"])}: <span class="lv-mono">{ui.h(fb["text"])}</span></div>')
                if pruef[f["id"]] == "nicht im Original":
                    st.caption("Der Fund geht zurück an die Prüflogik.")
                if ui.belegstand_text(pruef[f["id"]], s2_stand):        # 7: nur bei echtem Abgleich, Datum deutsch
                    st.caption(ui.belegstand_text(pruef[f["id"]], s2_stand))
                st.html(f'<div class="lv-label">Einordnung</div><div class="lv-text">{ui.h(f["begruendung"])}</div>')
                if f["rueckfrage"]:
                    with st.expander("Bieterfrage (Entwurf)"):
                        st.html(f'<div class="lv-text">{ui.h(f["rueckfrage"])}</div>')
                        st.caption("Mögliche Rückfrage an den Auftraggeber – Entwurf, vor dem Versand prüfen.")
                if f["pruefung"] in (1, 2):                        # KI-Gegenprüfung: nur Vorschlag, Fund bleibt
                    k = ki.get(f["id"])
                    with st.container(key=f"lv_ki_{f['id'].replace('|', '_').replace('.', '_')}"):
                        st.html(ui.chip("KI-Vorschlag", "neutral"))
                        if k is None:
                            st.caption("KI-Gegenprüfung: noch nicht durchgeführt")
                        elif not k["einordnung"]:
                            st.caption(f"KI-Gegenprüfung: {k['status']}. Der Regel-Fund bleibt unverändert.")
                        else:
                            st.markdown(f"**KI-Vorschlag:** {ui.md_text(k['einordnung'])}")
                            if ki_warnhinweis(k):                   # B0b.6 / E13
                                st.warning(ki_warnhinweis(k))
                            st.markdown(f"**Begründung (KI):** {ui.md_text(k['begruendung'])}")
                            st.markdown(f"**Zitat-Status:** {ui.md_text(k['zitat_status'])} – „{ui.md_text(k['zitat_kurztext'])}“ / "
                                        f"„{ui.md_text(k['zitat_langtext'])}“")
                            if k["rueckfrage"]:
                                st.markdown(f"**Rückfrage-Entwurf (KI):** {ui.md_text(k['rueckfrage'])}")
                        if k is not None:
                            st.caption(f"{k['modell']} · Prompt {k['prompt_version']} · aus {k['quelle']}. "
                                       "Die Entscheidung trifft die kalkulierende Person.")
                frueher = erfahrung.fruehere(f, lv_name)       # M2c: nur Anzeige, ändert keinen Fund (entwarnt nie)
                if frueher:
                    with st.container(key=f"lv_erf_{f['id'].replace('|', '_').replace('.', '_')}"):
                        st.html(ui.chip("Erfahrung: frühere Entscheidung eines Menschen", "neutral"))
                        st.caption(erfahrung.KENNZEICHNUNG)
                        for e_ in frueher:
                            st.text(erfahrung.anzeige(e_))
                st.html('<div class="lv-label">Ihre Entscheidung</div>')
                lv_sitzung.begruendung_feld(f["id"], "Begründung (optional, wird mit der Entscheidung gespeichert)")
                if st.session_state.pop("erfahrung_fehler", False):
                    st.warning("Status gespeichert, die Erfahrungsdatenbank konnte aber nicht geschrieben werden.")
                b1, b2 = st.columns(2)
                b1.button("Bestätigen", key=f"ok-{f['id']}", disabled=f["status"] == "bestätigt", type="primary",
                          on_click=setze_status, args=(schluessel, f["id"], "bestätigt"), width="stretch")
                b2.button("Rückfrage stellen", key=f"frage-{f['id']}", disabled=f["status"] == "Rückfrage stellen",
                          on_click=setze_status, args=(schluessel, f["id"], "Rückfrage stellen"), width="stretch")
                b3, b4 = st.columns(2)
                b3.button("Verwerfen", key=f"nein-{f['id']}", disabled=f["status"] == "verworfen",
                          on_click=setze_status, args=(schluessel, f["id"], "verworfen"), width="stretch")
                b4.button("Zurück auf offen", key=f"offen-{f['id']}", disabled=f["status"] == "offen",
                          on_click=setze_status, args=(schluessel, f["id"], "offen"), width="stretch")
                if naechster and f["status"] != "offen":
                    st.button("Nächster offener Fund →", key="pf_naechster", on_click=_waehlen, args=(naechster,),
                              width="stretch")
                st.html(f'<div class="lv-meta">Status wird gespeichert in: {ui.h(ablage_name())} · Fund-ID '   # 3: neutral
                        f'<span class="lv-mono">{ui.h(f["id"])}</span></div>')
            with st.expander("Vergleichspreise (bepreiste Dateien des Datensatzes)"):     # B6b, B2-Integration
                from vergleichspreise import vergleichspreise, HINWEIS as VP_HINWEIS
                st.caption(VP_HINWEIS)
                treffer = []
                for p in f["positionen"]:
                    treffer += vergleichspreise(info["kurztexte"].get(p["oz"], ""), info["einheiten"].get(p["oz"], ""),
                                                preisquellen_datensatz(), ohne=(lv_name, p["oz"]))
                if not treffer:
                    st.write("Keine Position mit gleichem Kurztext bzw. allen Wörtern und gleicher Einheit gefunden.")
                for t_ in treffer:
                    st.write(f"{t_['trefferart']}: {t_['quelle']} – „{t_['kurztext']}“")
            for t in texte[f["id"]]:
                with st.expander(f"Position {t['oz']}: Kurz- und Langtext (Parser-Ausgabe)"):
                    st.markdown("**Kurztext**")
                    st.text(t["kurztext"])
                    st.markdown("**Langtext**")
                    st.text(t["langtext"])

# --------------------------------------------------------------------------- Prüfstand, KI, Export, anderes LV

ui.abschnitt("Prüfstand, KI und Export")


def rechenpruefung_zeile(info):
    """B1e: „Rechenprüfung: N Positionen nachgerechnet, K Abweichungen“ – immer, auch bei 0."""
    e = next((x for x in info.get("abdeckung") or [] if x["pruefung"] == 17), None)
    if e is not None:
        st.caption(f"**{e['text']}** (Menge × EP gegen GP, Rundung der gedruckten Werte berücksichtigt)")


stand_p = info["pruefstand"]                         # L24: womit geprüft wurde (auch im Risikobericht)
rechenpruefung_zeile(info)                           # Nr. 17 (B1e)
abdeckung = info.get("abdeckung") or []
eng = pruefabdeckung.eingeschraenkt(abdeckung)
if eng:                                             # gleichlautende Einträge zusammengefasst (19 Prüfungen)
    gruppen = {}
    for e in eng:
        gruppen.setdefault(pruefabdeckung.text(e), []).append(str(e["pruefung"]))
    st.caption("Prüfabdeckung: " + " · ".join(f"Nr. {', '.join(n)} {txt}" for txt, n in gruppen.items())
               + ". Ein Hinweis, kein Fund wird unterdrückt.")
with st.expander("Prüfstand und Prüfabdeckung je Prüfung", expanded=False):
    st.caption(f"Prüfstand: Commit {stand_p['commit']} · Prompt {stand_p['prompt_version']} · "
               f"SHA-256 {stand_p['sha256'][:12]}… (vollständig im Risikobericht)")
    for name, wert in pruefstand.zeilen(stand_p):
        st.markdown(f"**{name}:** `{wert}`")
    st.divider()
    st.caption(f"Prüfabdeckung {ABDECKUNG_HINWEIS}.")
    for e in abdeckung:
        st.markdown(f"**Nr. {e['pruefung']} ({e['name']}):** {pruefabdeckung.text(e)}")
if pruefstand.abweichend():
    st.warning(f"Bibliotheksversionen weichen von den festgelegten ab: {', '.join(pruefstand.abweichend())} "
               "(Leitplanke E14).")

# KI-Gegenprüfung (P4): nur auf Knopfdruck; Ergebnisse aus dem Cache kosten keinen Aufruf
offen_ki = [f_ for f_ in ki_funde(funde) if f_["id"] not in ki]
if ki_funde(funde):
    with st.expander("KI-Gegenprüfung (nur Vorschlag, ändert keinen Fund)"):
        st.caption(ki_status(konfig))
        if konfig.anbieter == "groq":
            tok, anf = verbrauch_heute("groq")
            de = lambda n: f"{n:,}".replace(",", ".")       # Tausenderpunkt
            st.caption(f"Groq heute: {de(tok)} von {de(GROQ_LIMITS['tokens_tag'])} Tokens, {de(anf)} von "
                       f"{de(GROQ_LIMITS['anfragen_tag'])} Anfragen (laut data/qa/ki_log.jsonl; "
                       f"maßgeblich ist der Limits-Tab in der Groq-Console)")
        if st.button(f"KI-Gegenprüfung starten ({len(offen_ki)} Funde)",
                     disabled=not (konfig.aktiv and konfig.modell and offen_ki)):
            anzeige = st.empty()
            _, stat = gegenpruefung(funde, texte, konfig,
                                    fortschritt=lambda i, n, fid, t: anzeige.info(f"Fund {i} von {n} ({fid}): {t}"))
            anzeige.empty()
            st.session_state[f"ki-stat-{schluessel}"] = stat
            st.rerun()
        stat = st.session_state.get(f"ki-stat-{schluessel}")
        if stat:
            text = (f"Letzter KI-Lauf: {stat['aufrufe']} API-Aufrufe (höchstens {MAX_AUFRUFE}), "
                    f"{stat['cache_treffer']} aus dem Cache · Tokens ein {stat['input_tokens']}, "
                    f"aus {stat['output_tokens']} · Dauer {stat['dauer_s']:.1f} s, Wartezeit {stat['wartezeit_s']:.0f} s")
            if stat["anbieter"] == "anthropic":
                text += (f" · geschätzte Kosten {stat['kosten_usd']:.4f} $ ({PREISE['input']:g} $ / "
                         f"{PREISE['output']:g} $ pro Mio. Tokens; Quelle: platform.claude.com, Stand 21.11.2026)")
            st.caption(text)
            if stat["meldung"]:
                st.warning(stat["meldung"])

# B5: KI-Prüfungen Tippfehler und Widerspruch zwischen Positionen – nur KI-Vorschlag, getrennt von den Regel-Funden
# (E13: ändert keinen Fund, keine Sortierung, keinen Filter); nur auf Knopfdruck, höchstens MAX_AUFRUFE je Klick.
B5_NAMEN = {"tippfehler": "Tippfehler", "widerspruch": "Widerspruch zwischen Positionen"}
if any(info["b5"].values()):
    with st.expander("KI-Prüfungen (B5): Tippfehler, Widerspruch zwischen Positionen – nur KI-Vorschlag"):
        st.caption(f"{ki_status(konfig).split(', Prompt')[0]} · Prompt-Versionen {ki_b5.VERSION['tippfehler']} / "
                   f"{ki_b5.VERSION['widerspruch']} · Messung an 32 erfundenen Fällen: data/qa/b5_messung.json. "
                   "KI-Vorschläge verändern keinen Regel-Fund; bitte jeden Vorschlag am Text prüfen.")
        for pr, name in B5_NAMEN.items():
            gruppen = info["b5"][pr]
            if not gruppen:
                continue
            einheit = "Positionen" if pr == "tippfehler" else "Positionspaare (Regel-Vorauswahl)"
            if st.button(f"KI: {name} prüfen ({len(gruppen)} {einheit}, höchstens {MAX_AUFRUFE} Aufrufe je Klick)",
                         key=f"b5-{pr}-{schluessel}", disabled=not (konfig.aktiv and konfig.modell)):
                anzeige = st.empty()
                _, st5 = ki_b5.pruefe(pr, gruppen, konfig,
                                      fortschritt=lambda i, n: anzeige.info(f"{name}: {i} von {n}"))
                anzeige.empty()
                st.session_state[f"b5-stat-{pr}-{schluessel}"] = st5
            erg5, cst = ki_b5.pruefe(pr, gruppen, konfig, max_aufrufe=0)      # nur Cache, kein Aufruf
            alle5 = ki_b5.vorschlaege(pr, erg5)
            vor = [v for v in alle5 if ki_blatt.unbedenklich(v)]      # L59: gleicher Filter wie im Risikobericht
            st5 = st.session_state.get(f"b5-stat-{pr}-{schluessel}")
            st.markdown(f"**{name}:** {cst['cache_treffer']} von {len(gruppen)} geprüft, {len(vor)} KI-Vorschläge"
                        + (f", {len(alle5) - len(vor)} wegen auffälligem KI-Text nicht übernommen"
                           if len(alle5) != len(vor) else ""))
            if st5:
                st.caption(f"Letzter Klick: {st5['aufrufe']} API-Aufrufe, {st5['cache_treffer']} aus dem Cache")
                if st5["meldung"]:
                    st.warning(st5["meldung"])
            for v in vor:
                a = v["antwort"]
                if pr == "tippfehler":
                    st.markdown(f"- OZ {v['positionen'][0]}: „{a['zitat']}“ → vermutlich „{a['korrektur']}“ "
                                f"(KI-Vorschlag, {v['kategorie_vorschlag']}, Stufe {v['stufe_vorschlag']}, "
                                f"{v['empfehlung']}; Quelle {v['quelle']}, {v['modell']})")
                else:
                    st.markdown(f"- OZ {a['oz_a']} „{a['zitat_a']}“ ↔ OZ {a['oz_b']} „{a['zitat_b']}“: "
                                f"{a['begruendung']} Rückfrage-Entwurf: {a['rueckfrage']} (KI-Vorschlag, "
                                f"{v['kategorie_vorschlag']}, Stufe {v['stufe_vorschlag']}; Quelle {v['quelle']}, "
                                f"{v['modell']})")

st.session_state["lv_uebersicht"]["ki_aktiv"] = konfig.aktiv
bericht_button(lv_name, funde, texte, info, ki)   # alle Funde mit Entscheidung aus der App; Bieterfragen
lv_sitzung.upload_feld("Ein LV hochladen (GAEB XML, GAEB 90, PDF oder Excel)")
