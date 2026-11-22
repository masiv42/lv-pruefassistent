"""
pruefung_rechnung.py - Prüfung Nr. 17 Rechenprüfung Menge × EP ≠ GP (Block B1e, Team 21.11.2026).

Nachgerechnet wird jede Position mit Menge, EP und GP aus parse(), auch in reinen Preisdateien (D84). Keine
Preisbewertung und keine eigenen Preise (E9): verglichen wird nur, ob das Produkt Menge × EP zum gedruckten GP passt.

Toleranz (Prüflogik, B1e): 0,01 € + |Menge| × 0,0005 €. Der GP ist auf Cent gerundet (≤ 0,005 €); der EP ist
höchstens mit 3 Nachkommastellen gedruckt (≤ 0,0005 € je Einheit). Nur eine Abweichung darüber lässt sich nicht
durch die Rundung der gedruckten Werte erklären – dann ist es ein nachweisbarer Fehler (Stufe 1, Rang 1).
Erhebung 21.11.2026: 1.242 Positionen in 5 Dateien, größte Abweichung 0,0018 € (Angebot AN24-0305 2.3.40).

Beleg (R5): Menge, EP und GP als Feldwerte der Position, dazu der Kurztext, falls vorhanden.
"""
import pandas as pd

from pruefung_widerspruch import normalisiere_oz, normalisiere_leerzeichen, PRIORITAET_IN_STUFE

NR = 17
TITEL = "Rechenprüfung Menge × EP ≠ GP"
KATEGORIE = "nachweisbarer Fehler"
STUFE = 1
FELDWERT = "Feldwert"
TOLERANZ_GRUND, TOLERANZ_JE_EINHEIT = 0.01, 0.0005


def toleranz(menge):
    return TOLERANZ_GRUND + abs(menge) * TOLERANZ_JE_EINHEIT


def de(x, stellen):
    """Zahl im deutschen Format mit Tausenderpunkt, z. B. 6803.4 -> „6.803,40“."""
    return f"{x:,.{stellen}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def de_ep(x):
    """EP mit 2 Nachkommastellen, bei Bedarf 3 (wie im LV gedruckt)."""
    return de(x, 3) if round(x, 2) != round(x, 3) else de(x, 2)


def _da(x):
    return x is not None and not (isinstance(x, float) and pd.isna(x))


def _seite(x):
    return None if x is None or pd.isna(x) else int(x)


def nachrechenbar(df):
    """Positionen mit Menge, EP und GP."""
    pos = df[df.typ == "Position"]
    return pos[pos.menge.notna() & pos.ep.notna() & pos.gp.notna()]


def pruefe_rechnung(df):
    """(Anzahl nachgerechneter Positionen, Funde Nr. 17) für eine Tabelle aus parse()."""
    n = nachrechenbar(df)
    funde = {}
    for r in n.itertuples():
        soll = r.menge * r.ep
        d = abs(soll - r.gp)
        tol = toleranz(r.menge)
        if d <= tol:
            continue
        kurz = normalisiere_leerzeichen(r.kurztext if isinstance(r.kurztext, str) else "")
        einheit = r.einheit_roh if isinstance(r.einheit_roh, str) and r.einheit_roh.strip() else (r.einheit or "")
        fid = f"{NR}|{r.datei}|{normalisiere_oz(r.oz)}"
        if fid in funde:
            continue
        funde[fid] = {
            "id": fid,
            "pruefung": NR,
            "kategorie": KATEGORIE,
            "titel": TITEL,
            "positionen": [{"datei": r.datei, "oz": r.oz, "seite": _seite(r.seite)}],
            "belege": [kurz] if kurz else [],
            "feldbelege": [{"art": FELDWERT, "text": f"Menge: {de(r.menge, 3)} {einheit}".rstrip()},
                           {"art": FELDWERT, "text": f"EP: {de_ep(r.ep)}"},
                           {"art": FELDWERT, "text": f"GP: {de(r.gp, 2)}"}],
            "begruendung": (f"Menge × EP = {de(soll, 2)} €, im LV steht GP {de(r.gp, 2)} €; Abweichung {de(d, 2)} € "
                            f"(Toleranz {de(tol, 2)} € aus der Rundung der gedruckten Werte). "
                            f"Empfehlung laut Prüfkatalog: klärende Rückfrage."),
            "stufe": STUFE,
            "stufe_begruendung": f"Stufe {STUFE} laut Team 21.11.2026 (B1e, Rangtabelle 21:20)",
            "prioritaet_in_stufe": PRIORITAET_IN_STUFE[(NR, STUFE)],
            "rueckfrage": None,
            "status": "offen",
        }
    return len(n), list(funde.values())


def abdeckung_eintrag(df):
    """Eintrag für die Prüfabdeckung: „Rechenprüfung: N Positionen nachgerechnet, K Abweichungen“ (auch bei 0)."""
    pos = df[df.typ == "Position"]
    n, funde = pruefe_rechnung(df)
    gruende = [("ohne Menge, EP oder GP (unbepreist)", len(pos) - n)] if len(pos) - n else []
    return {"pruefung": NR, "name": TITEL, "pruefbar": n, "gesamt": len(pos), "gruende": gruende,
            "text": f"Rechenprüfung: {n} Positionen nachgerechnet, {len(funde)} Abweichungen"}
