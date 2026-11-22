"""
app.py - Ergebnisansicht (U1, P2).

Ein LV hochladen -> parse() -> Prüfungen Nr. 1–6 -> Fundliste (nach Stufe, Rang in Stufe, OZ; Filter
nach Kategorie und Stufe; Stufe 2 je Prüfung aufklappbar gruppiert, B1b), Prüfabdeckung im Kopf,
Belegansicht, Bestätigen/Verwerfen.
Der Status wird je LV in data/findings/<datei>.json gespeichert (nie in data/raw/); Tests und
Browser-Prüfungen durch Agenten lenken die Ablage mit LV_FINDINGS_DIR in einen Temp-Ordner
(src/status_ablage.py, L19). KI-Vorschläge entwarnen nie (Leitplanke E13).
Funde nach docs/data-contracts.md. Reine Preisdateien werden nicht geprüft.
Risikobericht als .xlsx zum Herunterladen (src/bericht.py, P3).

Start aus der Projektwurzel:
  uv run --no-project --python 3.12 --with streamlit==1.67.0 --with pdfplumber==0.11.11 --with lxml==6.1.3 \
      --with pandas==3.1.1 --with openpyxl==3.1.5 --with anthropic==2.12.0 --with openai==3.57.0 streamlit run src/app.py \
      --server.address localhost --browser.gatherUsageStats false
(nur auf diesem Rechner erreichbar, keine Nutzungsstatistik an Streamlit)
"""
import hashlib
import io
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pruefung_formal import sortiere, datei_hinweis                       # noqa: E402
from bericht import (pruefe_lv, lade_s2, beleg_pruefung, risikobericht,   # noqa: E402
                     dateiname, NUR_PREISE_TEXT, ki_liste, ki_warnhinweis, STUFEN, RANG,
                     ABDECKUNG_HINWEIS, PRUEFER)
from status_ablage import lade_status, speichere, ablage_name              # noqa: E402
import pruefstand                                                          # noqa: E402
import pruefabdeckung                                                      # noqa: E402
import ki_b5                                                                    # noqa: E402
import ki_blatt                                                                 # noqa: E402
import erfahrung                                                                # noqa: E402
import ui_stil                                                                  # noqa: E402
import lv_sitzung                                                               # noqa: E402
from ki_pruefung import (lade_konfig, ki_status, aus_cache, verbrauch_heute,   # noqa: E402
                         ki_funde, gegenpruefung, PREISE, MAX_AUFRUFE, GROQ_LIMITS)

ROOT = Path(__file__).resolve().parent.parent
STATUS = ["offen", "bestätigt", "verworfen", "Rückfrage stellen"]
HINWEIS_S2 = "Beleg noch nicht am Original geprüft."
GEPRUEFT = "Beleg am Original geprüft"
NICHT_IM_ORIGINAL = "Beleg steht so nicht wörtlich im Original"


# --------------------------------------------------------------------------- Daten

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


XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@st.cache_data(show_spinner="Vergleichspreise werden gelesen …")
def preisquellen_datensatz():
    """Bepreiste Dateien des Datensatzes (nur lesen, E11); D84 ohne Text nicht verknüpft (B2-F14, B2-L9)."""
    from vergleichspreise import preisquellen
    raw = ROOT / "data" / "raw"
    namen = ["Abgabe LV.pdf", "Angebot AN24-0305.pdf", "StBALV23040.D86", "[ORT_024] LV24069.D86"]
    return preisquellen([raw / n for n in namen if (raw / n).exists()])


def downloads(name, funde, texte, info, ki=None):
    """Risikobericht und Bieterfragen (Entwurf) als Download-Liste; auch für die Übersichtsseite (B2-Integration).
    UI2 (Auflage 6): `daten` ist eine Funktion ohne Argumente, die Streamlit erst beim Klick ausführt (eigener Thread,
    ohne session_state). Sie bekommt eine Kopie des Stands beim Anzeigen (Funde mit Status, KI-Cache), damit der Bericht
    nicht bei jedem Neulauf auf jeder Seite entsteht und trotzdem genau den angezeigten Stand enthält."""
    import copy
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


def bericht_button(name, funde, texte, info, ki=None):
    """Download des Risikoberichts (immer alle Funde, unabhängig vom Filter) und der Bieterfragen (Entwurf)."""
    liste = downloads(name, funde, texte, info, ki)
    st.session_state["lv_downloads"] = liste
    spalten = st.columns(len(liste))
    for s, d in zip(spalten, liste):
        s.download_button(d["label"], data=d["daten"], file_name=d["dateiname"], mime=d["mime"])


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


# --------------------------------------------------------------------------- Ansicht

st.set_page_config(page_title="LV-Prüfassistent", layout="wide")
ui_stil.stil_einbinden()
ui_stil.navigation()
kopf_platz = st.container()
st.caption("Prüfungen Nr. 1–19 laut Prüfkatalog (Fehler, Kalkulationsrisiken, mögliches Nachtragspotenzial, "
           "Unklarheiten). Die Funde sind Hinweise zur Klärung, keine Rechtsberatung und keine "
           "Vollständigkeitsprüfung des LV.")

# B8e (A1): das aktuelle LV liegt zentral in der Sitzung, nicht im Upload-Feld (übersteht Seitenwechsel)
aktuell = lv_sitzung.upload_feld("Ein LV hochladen (GAEB XML, GAEB 90, PDF oder Excel)")
if aktuell is None:
    with kopf_platz:
        ui_stil.kopf("LV-Prüfung", "Noch kein LV geladen")
    st.stop()

lv_name, daten = aktuell["name"], aktuell["daten"]
zuordnung = {}
if lv_name.lower().endswith((".xlsx", ".xlsm")):        # B2-Integration (B4): Excel mit Spalten-Zuordnung
    import pandas as pd
    from excel_import import spalten_vorschlag, FELDER, PFLICHT, KENNZEICHNUNG
    st.info(KENNZEICHNUNG)
    kopf = list(pd.read_excel(io.BytesIO(daten), nrows=0, engine="openpyxl").columns.astype(str))
    vorschlag = spalten_vorschlag(kopf)
    with st.expander("Spalten-Zuordnung (Excel)", expanded=not all(f in vorschlag for f in PFLICHT)):
        for feld in FELDER:
            gemerkt = aktuell["zuordnung"].get(feld, vorschlag.get(feld))      # B8e: Zuordnung übersteht Seitenwechsel
            wahl = st.selectbox(feld, ["–"] + kopf, key=f"map_{feld}",
                                index=(kopf.index(gemerkt) + 1) if gemerkt in kopf else 0)
            if wahl != "–":
                zuordnung[feld] = wahl
    aktuell["zuordnung"] = dict(zuordnung)
    if not all(f in zuordnung for f in PFLICHT):
        with kopf_platz:
            ui_stil.kopf("LV-Prüfung", lv_name)
        st.warning("Bitte mindestens OZ und Kurztext zuordnen.")
        st.stop()
try:
    funde_neu, texte, info = analysiere(lv_name, daten, tuple(sorted(zuordnung.items())))
except ValueError as e:
    with kopf_platz:
        ui_stil.kopf("LV-Prüfung", lv_name)
    st.error(f"Datei kann nicht gelesen werden: {e}")
    st.stop()
kontext_lv = ui_stil.kontext_lv({"lv_name": lv_name, "format": info["format"], "positionen": info["positionen"]})

def rechenpruefung_zeile(info):
    """B1e: „Rechenprüfung: N Positionen nachgerechnet, K Abweichungen“ – immer, auch bei 0."""
    e = next((x for x in info.get("abdeckung") or [] if x["pruefung"] == 17), None)
    if e is not None:
        st.caption(f"**{e['text']}** (Menge × EP gegen GP, Rundung der gedruckten Werte berücksichtigt)")


if info["nur_preise"]:
    st.warning(f"**{lv_name}**: {NUR_PREISE_TEXT}")
    rechenpruefung_zeile(info)
    if not funde_neu:                                # reine Preisdatei ohne Rechenfehler: nichts weiter zu zeigen
        with kopf_platz:
            ui_stil.kopf("LV-Prüfung", kontext_lv)
            ui_stil.kacheln(ui_stil.kacheln_lv({**info, "lv_name": lv_name, "funde": []}))
        bericht_button(lv_name, funde_neu, texte, info)
        st.stop()

if datei_hinweis(lv_name):                       # Hinweis zur Datei, unterdrückt keinen Fund
    st.info(datei_hinweis(lv_name))

# Status aus data/findings/ übernehmen (gleiche Fund-ID = gleicher Fund)
schluessel = lv_sitzung.status_schluessel(lv_name, daten, tuple(sorted(zuordnung.items())))   # Auflage 2
if schluessel not in st.session_state:
    gespeichert = lade_status(lv_name)
    funde = [dict(f, status=gespeichert.get(f["id"], "offen")) for f in funde_neu]
    st.session_state[schluessel] = {"datei": lv_name, "funde": funde}
funde = st.session_state[schluessel]["funde"]

zaehler = {s: sum(f["status"] == s for f in funde) for s in STATUS}
with kopf_platz:
    ui_stil.kopf("LV-Prüfung", kontext_lv, [ui_stil.abzeichen_status_zahl(s, n) for s, n in zaehler.items()])
    ui_stil.kacheln(ui_stil.kacheln_lv({**info, "lv_name": lv_name, "funde": funde}))
stand = info["pruefstand"]                         # L24: womit geprüft wurde (auch im Risikobericht)
if not info["nur_preise"]:
    rechenpruefung_zeile(info)                      # Nr. 17 (B1e)
# Prüfabdeckung je Prüfung (B1b, Nachtrag 3): Hinweis, unterdrückt keinen Fund
abdeckung = info.get("abdeckung") or []
if ui_stil.abdeckung_hinweis(abdeckung):            # gleichlautende Einträge zusammengefasst (19 Prüfungen)
    st.caption(ui_stil.abdeckung_hinweis(abdeckung))
with st.expander("Prüfstand und Prüfabdeckung je Prüfung", expanded=False):
    st.caption(f"Prüfstand: Commit {stand['commit']} · Prompt {stand['prompt_version']} · "
               f"SHA-256 {stand['sha256'][:12]}… (vollständig im Risikobericht)")
    for name, wert in pruefstand.zeilen(stand):
        st.markdown(f"**{name}:** `{wert}`")
    st.divider()
    st.caption(f"Prüfabdeckung {ABDECKUNG_HINWEIS}.")
    for e in abdeckung:
        st.markdown(f"**Nr. {e['pruefung']} ({e['name']}):** {pruefabdeckung.text(e)}")
if pruefstand.abweichend():
    st.warning(f"Bibliotheksversionen weichen von den festgelegten ab: {', '.join(pruefstand.abweichend())} "
               "(Leitplanke E14).")

# KI-Gegenprüfung (P4): nur auf Knopfdruck; Ergebnisse aus dem Cache kosten keinen Aufruf
konfig = lade_konfig()
ki = aus_cache(funde, texte, konfig)
offen_ki = [f for f in ki_funde(funde) if f["id"] not in ki]
if ki_funde(funde):
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
        ki = aus_cache(funde, texte, konfig)
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

# Übersichtsseite (src/pages/0_Uebersicht.py, Sitzung B2): Schlüssel laut Integrations-Vorschlag
st.session_state["lv_uebersicht"] = {
    "lv_name": lv_name, "format": info["format"], "positionen": info["positionen"],
    "nur_preise": info["nur_preise"], "abdeckung": info["abdeckung"], "funde": funde,
    "kurztexte": info["kurztexte"], "gp": info["gp"], "ki_aktiv": konfig.aktiv,
}
st.session_state["lv_positionen"] = {"lv_name": lv_name, "format": info["format"],
                                     "zeilen": info.get("tabelle"), "daten": daten}   # Positions-Explorer; info["tabelle"] kommt mit dem bericht.py-Vorschlag (B4)
bericht_button(lv_name, funde, texte, info, ki)   # alle Funde mit Entscheidung aus der App; Bieterfragen

if not funde:
    st.info("Keine Funde für die Prüfungen Nr. 1–19. Das heißt nicht, dass das LV ohne "
            "Fehler oder Risiken ist; geprüft wurden nur diese Prüfungen.")
    st.stop()

s2, s2_stand = lade_s2()
pruef = {f["id"]: beleg_pruefung(f, s2) for f in funde}
ungeprueft = sum(v == "ungeprüft" for v in pruef.values())
if ungeprueft:
    st.warning(f"{ungeprueft} von {len(funde)} Funden: {HINWEIS_S2} Diese Belege stammen "
               "aus der Parser-Ausgabe.")

links, rechts = st.columns([2, 3], gap="large")

with links:
    st.subheader("Fundliste")
    k_opt = sorted({f["kategorie"] for f in funde})
    s_opt = sorted({f["stufe"] for f in funde})
    fk, fs = st.columns(2)
    # A3 (UI2): Filter und Auswahl überstehen den Seitenwechsel (gemerkt je LV in lv_sitzung)
    ziel = lv_sitzung.fokus_nehmen("fund_id")
    if ziel is not None:                                # Sprung von Übersicht/Positionen: Fund sichtbar machen
        st.session_state["pf_kat"], st.session_state["pf_stufe"] = list(k_opt), list(s_opt)
        st.session_state["pf_fund"] = ziel
    lv_sitzung.filter_vorbereiten("pf_kat", list(k_opt), k_opt)
    lv_sitzung.filter_vorbereiten("pf_stufe", list(s_opt), s_opt)
    k_wahl = fk.multiselect("Kategorie", k_opt, key="pf_kat")
    s_wahl = fs.multiselect("Stufe", s_opt, key="pf_stufe", format_func=lambda s: f"{s} – {STUFEN[s]}")
    lv_sitzung.filter_merken("pf_kat", "pf_stufe")
    alle = funde
    funde = sortiere([f for f in alle if f["kategorie"] in k_wahl and f["stufe"] in s_wahl])
    st.caption(f"{len(funde)} von {len(alle)} Funden, sortiert nach Stufe, dann {RANG}, dann OZ")
    if not funde:
        st.info("Kein Fund passt zum Filter.")
        st.stop()

    def anzahl(n):
        return f"{n} Fund" if n == 1 else f"{n} Funde"

    def tabelle(liste):
        st.dataframe([{
            "OZ": x["positionen"][0]["oz"],
            "Stufe": f"{x['stufe']} – {STUFEN[x['stufe']]}",
            RANG: x["prioritaet_in_stufe"],
            "Titel": x["titel"],
            "Kategorie": x["kategorie"],
            "Status": x["status"],
            "Beleg am Original": pruef[x["id"]],
            "KI-Vorschlag": ki_liste(x, ki),           # E13: entwarnende Einordnung erst im Detail
            "Seite": x["positionen"][0]["seite"] or "",
            "Prüfung": x["pruefung"],
            "Prüfer": PRUEFER.get(x["pruefung"], ""),
        } for x in liste], hide_index=True, width="stretch")

    # Stufe 1 offen; Stufen 2–4 je Prüfung gruppiert und aufklappbar, mit Anzahl; nichts ausgeblendet
    # (B1b, B2-Integration: über 1.200 Funde Nr. 7–14, 18, 19 dürfen Stufe 1 nicht zudecken)
    for s in sorted({x["stufe"] for x in funde}):
        in_s = [x for x in funde if x["stufe"] == s]
        st.markdown(f"**Stufe {s} – {STUFEN[s]}: {anzahl(len(in_s))}**")
        if s == 1:
            tabelle(in_s)
            continue
        for nr in dict.fromkeys(x["pruefung"] for x in in_s):     # Reihenfolge wie sortiert (Rang)
            gruppe = [x for x in in_s if x["pruefung"] == nr]
            with st.expander(f"Nr. {nr} {gruppe[0]['titel']} · {RANG} {gruppe[0]['prioritaet_in_stufe']} · "
                             f"{anzahl(len(gruppe))}"):
                tabelle(gruppe)
    nach_id = {x["id"]: x for x in funde}
    lv_sitzung.filter_vorbereiten("pf_fund", funde[0]["id"], nach_id)
    wahl = st.selectbox(
        "Fund öffnen",
        list(nach_id),
        key="pf_fund",
        format_func=lambda i: f"OZ {nach_id[i]['positionen'][0]['oz']} – {nach_id[i]['titel']} "
                              f"({nach_id[i]['status']})",
    )
    lv_sitzung.filter_merken("pf_fund")

f = nach_id[wahl]
with rechts:
    st.subheader(f"Beleg – OZ {', '.join(p['oz'] for p in f['positionen'])}")
    st.markdown(ui_stil.abzeichen_fund(f, pruef[f["id"]]))
    st.caption(f"Prüfung Nr. {f['pruefung']} · Prüfer: {PRUEFER.get(f['pruefung'], '–')} · "
               f"{RANG}: {f['prioritaet_in_stufe']}")
    for i_p, p in enumerate(f["positionen"]):
        ort = f"Datei {p['datei']}, OZ {p['oz']}"
        if p["seite"] is not None:
            ort += f", Seite {p['seite']}"
        z_ort, z_knopf = st.columns([4, 1], vertical_alignment="center")
        z_ort.caption(ort)
        if z_knopf.button("Zur Position", key=f"zur-pos-{f['id']}-{i_p}",
                          help="Öffnet die Position mit allen ihren Funden; Filter hier bleiben erhalten."):
            lv_sitzung.fokus_setzen(oz=p["oz"])             # A3 (UI2)
            st.switch_page("pages/2_Positionen.py")
    st.markdown("**Belege (wörtlich aus dem LV):**")
    for b in f["belege"]:
        ui_stil.beleg(b)
    for fb in f.get("feldbelege", []):              # kein Zitat: Feldwert oder Kennzeichen
        st.markdown(f"**{fb['art']}:** `{fb['text']}`")
    st.markdown(f"**Begründung:** {f['begruendung']}")
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
    if f["rueckfrage"]:
        st.markdown(f"**Mögliche Rückfrage an den Auftraggeber:** {f['rueckfrage']}")
    if f["pruefung"] in (1, 2):                        # KI-Gegenprüfung: nur Vorschlag, Fund bleibt
        k = ki.get(f["id"])
        with ui_stil.ki_bereich(f["id"]):
            st.markdown(ui_stil.abzeichen_ki())
            if k is None:
                st.markdown("**KI-Gegenprüfung:** noch nicht durchgeführt")
            elif not k["einordnung"]:
                st.markdown(f"**KI-Gegenprüfung:** {k['status']}. Der Regel-Fund bleibt unverändert.")
            else:
                st.markdown(f"**KI-Vorschlag:** {k['einordnung']}")
                if ki_warnhinweis(k):                   # B0b.6 / E13
                    st.warning(ki_warnhinweis(k))
                st.markdown(f"**Begründung (KI):** {k['begruendung']}")
                st.markdown(f"**Zitat-Status:** {k['zitat_status']} – „{k['zitat_kurztext']}“ / "
                            f"„{k['zitat_langtext']}“")
                if k["rueckfrage"]:
                    st.markdown(f"**Rückfrage-Entwurf (KI):** {k['rueckfrage']}")
            if k is not None:
                st.caption(f"{k['modell']} · Prompt {k['prompt_version']} · aus {k['quelle']}. "
                           "Die Entscheidung trifft die kalkulierende Person.")
    if pruef[f["id"]] == "geprüft":
        st.caption(f"{GEPRUEFT} (Stand {s2_stand}). Fund-ID: `{f['id']}`")
    elif pruef[f["id"]] == "nicht im Original":
        st.warning(f"{NICHT_IM_ORIGINAL} (Stand {s2_stand}). Der Fund geht zurück an die "
                   "Prüflogik.")
        st.caption(f"Fund-ID: `{f['id']}`")
    else:
        st.caption(f"{HINWEIS_S2} Fund-ID: `{f['id']}`")

    frueher = erfahrung.fruehere(f, lv_name)       # M2c: nur Anzeige, ändert keinen Fund (entwarnt nie)
    if frueher:
        with ui_stil.erfahrung_bereich(f["id"]):                    # UI2: neutral, nur Anzeige
            st.markdown(ui_stil.abzeichen_erfahrung())
            st.caption(erfahrung.KENNZEICHNUNG)
            for e_ in frueher:
                st.text(erfahrung.anzeige(e_))
    ents = ui_stil.entscheidung_bereich(f["id"])                     # UI2: Begründung und Status zusammen
    ents.markdown("**Entscheidung** · aktueller Status: " + ui_stil.abzeichen_status(f["status"]))
    with ents:
        lv_sitzung.begruendung_feld(f["id"], "Begründung zur Entscheidung (optional, wird mit Bestätigen oder "
                                    "Verwerfen gespeichert)")             # B8e: Text übersteht Seitenwechsel
    if st.session_state.pop("erfahrung_fehler", False):
        st.warning("Status gespeichert, die Erfahrungsdatenbank konnte aber nicht geschrieben werden.")

    b1, b2, b3, b4 = ents.columns(4)
    b1.button("Bestätigen", key=f"ok-{f['id']}", disabled=f["status"] == "bestätigt",
              on_click=setze_status, args=(schluessel, f["id"], "bestätigt"), width="stretch")
    b2.button("Verwerfen", key=f"nein-{f['id']}", disabled=f["status"] == "verworfen",
              on_click=setze_status, args=(schluessel, f["id"], "verworfen"), width="stretch")
    b3.button("Rückfrage stellen", key=f"frage-{f['id']}", disabled=f["status"] == "Rückfrage stellen",
              on_click=setze_status, args=(schluessel, f["id"], "Rückfrage stellen"), width="stretch")
    b4.button("Zurück auf offen", key=f"offen-{f['id']}", disabled=f["status"] == "offen",
              on_click=setze_status, args=(schluessel, f["id"], "offen"), width="stretch")
    st.caption(f"Status wird gespeichert in: {ablage_name()}")

    for t in texte[f["id"]]:
        with st.expander(f"Position {t['oz']}: Kurz- und Langtext (Parser-Ausgabe)"):
            st.markdown("**Kurztext**")
            st.text(t["kurztext"])
            st.markdown("**Langtext**")
            st.text(t["langtext"])
