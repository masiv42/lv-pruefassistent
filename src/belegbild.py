"""
belegbild.py - B8b / P5 (Sitzung UI2, Team 22.11.2026): Beleg am Original als Bild, nur für PDF, nur auf Klick (A5).

Das Bild entsteht aus den Bytes der hochgeladenen Originaldatei (pdfplumber rendert die Seite), nie aus parse().
Das Zitat wird auf der angegebenen Seite gesucht; Leerzeichen und Zeilenumbrüche zählen dabei nicht, weil die
Textebene des PDF sie anders setzt als die Parser-Ausgabe (AGENTS.md: „C 3 0/37“). Gefunden: Rahmen um jede Zeile des
Treffers. Nicht gefunden: kein Rahmen, sondern der Hinweis NICHT_GEFUNDEN (R5: kein Kasten ohne wörtlichen Treffer).
Keine neue Bibliothek: pdfplumber 0.11.11 bringt das Rendern mit (pypdfium2).
"""
import io
import re

import streamlit as st

NICHT_GEFUNDEN = "Zitat auf dieser Seite nicht automatisch gefunden – bitte im PDF nachsehen"
RAHMEN = (31, 95, 214)                 # Blau = Auswahl/Fokus (Auftrag Abschnitt 9), wie primaryColor hell
AUFLOESUNG = 110
MAX_PIXEL = 2400                       # längste Bildseite in Pixel (Schutz vor riesigen Seitenformaten)
MIN_AUFLOESUNG = 12                    # darunter wäre das Bild unlesbar: Hinweis statt Bild
RAND_X, RAND_Y = 24, 36                # Rand um die Rahmen beim Zuschnitt, in Punkt (Kontext über und unter dem Zitat)
ZIEL_PX = 1200                         # Bildbreite des Ausschnitts in Pixel (Schrift bei 1440 px Fensterbreite gut lesbar)
MAX_AUFLOESUNG = 300


def muster(zitat):
    """Regex, die das Zitat unabhängig von Leerraum findet (jedes Zeichen wörtlich, dazwischen beliebig Leerraum)."""
    zeichen = [c for c in str(zitat) if not c.isspace()]
    return r"\s*".join(re.escape(c) for c in zeichen) if zeichen else None


def _zeilen(treffer):
    """Rahmen je Textzeile eines Treffers (ein Treffer kann über mehrere Zeilen gehen)."""
    zeilen = {}
    for c in treffer.get("chars") or []:
        z = zeilen.setdefault(round(c["top"]), [c["x0"], c["top"], c["x1"], c["bottom"]])
        z[0], z[1], z[2], z[3] = min(z[0], c["x0"]), min(z[1], c["top"]), max(z[2], c["x1"]), max(z[3], c["bottom"])
    if not zeilen:
        return [(treffer["x0"], treffer["top"], treffer["x1"], treffer["bottom"])]
    return [tuple(z) for _, z in sorted(zeilen.items())]


def belegbild(pdf_bytes, seite, zitate, aufloesung=AUFLOESUNG):
    """Rendert Seite `seite` (1-basiert) und rahmt jedes gefundene Zitat ein.
    Wird mindestens ein Zitat gefunden, wird auf alle Rahmen dieses Funds plus Rand zugeschnitten (mehrere Zitate bleiben
    alle im Ausschnitt). Ohne Treffer: ganze Seite ohne Rahmen (der Hinweis steht in anzeigen()).
    Rückgabe {"png": bytes|None, "gefunden": [bool je Zitat], "rahmen": Anzahl, "rahmen_liste": [(x0, top, x1, bottom)],
    "ausschnitt": (x0, top, x1, bottom)|None, "fehler": str|None}."""
    import pdfplumber
    zitate = [z for z in (zitate or []) if str(z).strip()]
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            if not isinstance(seite, int) or not 1 <= seite <= len(pdf.pages):
                return {"png": None, "gefunden": [False] * len(zitate), "rahmen": 0,
                        "fehler": f"Seite {seite} gibt es in dieser PDF nicht"}
            page = pdf.pages[seite - 1]
            groesste = max(float(page.width or 0), float(page.height or 0), 1.0)      # in Punkt (1/72 Zoll)
            aufloesung = min(aufloesung, MAX_PIXEL * 72 / groesste)
            if aufloesung < MIN_AUFLOESUNG:
                return {"png": None, "gefunden": [False] * len(zitate), "rahmen": 0,
                        "fehler": f"Seite {seite} ist zu groß, um sie als Bild anzuzeigen – bitte im PDF nachsehen"}
            gefunden, rahmen = [], []
            for z in zitate:
                m = muster(z)
                treffer = page.search(m, regex=True, case=True) if m else []
                gefunden.append(bool(treffer))
                for t in treffer[:1]:                              # erster Treffer je Zitat
                    rahmen += _zeilen(t)
            ziel, ausschnitt = page, None
            if rahmen:                                             # Zuschnitt auf alle Rahmen plus Rand, innerhalb der Seite
                px0, ptop, px1, pbottom = (float(v) for v in page.bbox)
                ausschnitt = (max(px0, min(r[0] for r in rahmen) - RAND_X), max(ptop, min(r[1] for r in rahmen) - RAND_Y),
                              min(px1, max(r[2] for r in rahmen) + RAND_X),
                              min(pbottom, max(r[3] for r in rahmen) + RAND_Y))
                ziel = page.crop(ausschnitt)
                breite, hoehe = ausschnitt[2] - ausschnitt[0], ausschnitt[3] - ausschnitt[1]
                # pdfplumber rendert die ganze Seite und schneidet dann zu: Grenze der Seite gilt weiter (MAX_PIXEL je Seite)
                aufloesung = min(ZIEL_PX * 72 / max(breite, 1.0), MAX_PIXEL * 72 / max(breite, hoehe, 1.0), MAX_AUFLOESUNG,
                                 MAX_PIXEL * 72 / groesste)
            bild = ziel.to_image(resolution=aufloesung)
            for x0, top, x1, bottom in rahmen:
                bild.draw_rect((x0 - 2, top - 2, x1 + 2, bottom + 2), fill=RAHMEN + (40,), stroke=RAHMEN + (255,),
                               stroke_width=2)
            puffer = io.BytesIO()
            bild.save(puffer, format="PNG")
            return {"png": puffer.getvalue(), "gefunden": gefunden, "rahmen": len(rahmen), "rahmen_liste": rahmen,
                    "ausschnitt": ausschnitt, "fehler": None}
    except Exception as e:                                         # beschädigte Datei o. ä.: Hinweis statt Absturz
        return {"png": None, "gefunden": [False] * len(zitate), "rahmen": 0,
                "fehler": f"Seite konnte nicht gerendert werden ({type(e).__name__})"}


@st.cache_data(show_spinner="Seite wird aus dem Original gerendert …", max_entries=64)
def _belegbild_cache(sha, pdf_bytes, seite, zitate):
    return belegbild(pdf_bytes, seite, list(zitate))


def anzeigen(pdf_bytes, sha, seite, zitate, schluessel):
    """Knopf „Beleg im Original zeigen“; das Bild entsteht erst nach dem Klick (A5) und bleibt bis zum Zuklappen."""
    offen = f"belegbild-offen-{schluessel}"
    if st.button(f"Beleg im Original zeigen (Seite {seite})" if not st.session_state.get(offen)
                 else "Bild des Originals ausblenden", key=f"belegbild-{schluessel}"):
        st.session_state[offen] = not st.session_state.get(offen, False)
    if not st.session_state.get(offen):
        return None
    erg = _belegbild_cache(sha, pdf_bytes, seite, tuple(zitate))
    if erg["fehler"]:
        st.caption(erg["fehler"])
        return erg
    if not all(erg["gefunden"]):
        st.info(NICHT_GEFUNDEN)
    st.image(erg["png"], caption=(f"Ausschnitt der Originalseite {seite} · Rahmen = gefundenes Zitat" if erg.get("ausschnitt")
                                  else f"Originalseite {seite}"),
             width="stretch")
    return erg
