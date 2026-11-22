"""
seite_zuschlag.py - Block B6a (Meilenstein 5): Zuschlags-Rechner und What-if als eigene Streamlit-Seite
(Sitzung B2, Team 21.11.2026, 18:50). Ort: Vorschlag `src/pages/zuschlag_rechner.py` bei der Integration
(Streamlit nimmt Dateien in pages/ sofort als Seite auf; deshalb liegt sie bis zur Freigabe hier).

Leitplanken: Nur Eingaben des Kalkulators (E9, Scope D) – keine Zuschläge, Preise oder Mengen aus dem Tool, keine
Vorbelegung außer 0, keine Preisvorschläge, keine Empfehlung zu Preisverlagerungen. Jede Rechnung steht Schritt für
Schritt sichtbar da. Gerechnet wird mit Decimal; gerundet wird nur der Einheitspreis auf 2 Nachkommastellen
(kaufmännisch, ROUND_HALF_UP), der Gesamtpreis ist gerundeter EP × Menge, ebenfalls auf 2 Stellen (Rundung je
Schritt angezeigt).

Rechenweg (Zuschlagskalkulation, additiv):
  je Kostenart k (Lohn, Stoffe, Geräte, Nachunternehmer, Sonstiges):
    Zuschlagssatz z_k = BGK_k + AGK_k + W+G_k  (Prozent, Eingabe des Kalkulators)
    Anteil EP_k     = Einzelkosten_k × (1 + z_k / 100)
  EP = Σ Anteil EP_k (gerundet), GP = EP × Menge (gerundet)
What-if: Änderung je Kostenart in Prozent (z. B. Stoffe +12 %) oder neue Einzelkosten (Alternative). Gezeigt werden
beide Rechnungen und die Differenz von EP und GP. Das Tool bewertet die Varianten nicht.

Start (nur durch Menschen, nicht durch Agenten; Port laut launch.json): streamlit run src/seite_zuschlag.py
"""
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

KOSTENARTEN = ("Lohn", "Stoffe", "Geräte", "Nachunternehmer", "Sonstiges")
ZUSCHLAGSARTEN = ("BGK", "AGK", "W+G")          # Baustellengemeinkosten, Allgemeine Geschäftskosten, Wagnis und Gewinn
CENT = Decimal("0.01")
HINWEIS = ("Alle Werte sind Eingaben des Kalkulators. Das Tool rechnet nur und schlägt keine Zuschläge oder Preise "
           "vor (E9).")


def dez(x, name="Wert"):
    """Eingabe als Decimal (auch „12,5“). Fehler bei Text, der keine Zahl ist."""
    if isinstance(x, Decimal):
        return x
    try:
        return Decimal(str(x).strip().replace(" ", "").replace(",", "."))
    except (InvalidOperation, AttributeError):
        raise ValueError(f"{name}: „{x}“ ist keine Zahl")


def _eur(x):
    return f"{x:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def _zahl(x):
    s = f"{x.normalize():f}" if x == x.to_integral() else f"{x:f}".rstrip("0")
    return s.replace(".", ",")


def rechne(einzelkosten, zuschlaege, menge):
    """einzelkosten: {Kostenart: € je Einheit}; zuschlaege: {Kostenart: {BGK|AGK|W+G: %}}; menge: Zahl.
    Rückgabe {ep, gp, anteile, schritte}. Fehlende Werte zählen als 0. Negative Werte sind ein Fehler."""
    m = dez(menge, "Menge")
    if m < 0:
        raise ValueError("Menge darf nicht negativ sein")
    schritte, anteile, summe = [], {}, Decimal(0)
    for k in KOSTENARTEN:
        ek = dez(einzelkosten.get(k, 0), f"Einzelkosten {k}")
        if ek < 0:
            raise ValueError(f"Einzelkosten {k} dürfen nicht negativ sein")
        teile = {z: dez((zuschlaege.get(k) or {}).get(z, 0), f"{z} {k}") for z in ZUSCHLAGSARTEN}
        if any(v < 0 for v in teile.values()):
            raise ValueError(f"Zuschläge {k} dürfen nicht negativ sein")
        satz = sum(teile.values(), Decimal(0))
        anteil = ek * (1 + satz / 100)
        anteile[k] = anteil
        summe += anteil
        if ek or satz:
            schritte.append(f"{k}: Zuschlag = " + " + ".join(f"{z} {_zahl(teile[z])} %" for z in ZUSCHLAGSARTEN)
                            + f" = {_zahl(satz)} %; Anteil EP = {_zahl(ek)} € × (1 + {_zahl(satz)} / 100) = "
                              f"{_zahl(anteil)} €")
    ep = summe.quantize(CENT, rounding=ROUND_HALF_UP)
    schritte.append(f"EP = Summe der Anteile = {_zahl(summe)} € → gerundet {_eur(ep)}")
    gp = (ep * m).quantize(CENT, rounding=ROUND_HALF_UP)
    schritte.append(f"GP = EP × Menge = {_eur(ep)} × {_zahl(m)} = {_zahl(ep * m)} € → gerundet {_eur(gp)}")
    return {"ep": ep, "gp": gp, "anteile": anteile, "schritte": schritte}


def what_if(einzelkosten, zuschlaege, menge, aenderung_prozent=None, neue_einzelkosten=None):
    """Variante gegen Basis: Einzelkosten je Kostenart um Prozent ändern und/oder ersetzen (Alternative).
    Rückgabe {basis, variante, diff_ep, diff_gp, schritte}."""
    basis = rechne(einzelkosten, zuschlaege, menge)
    neu, schritte = {}, []
    for k in KOSTENARTEN:
        ek = dez(einzelkosten.get(k, 0), f"Einzelkosten {k}")
        if neue_einzelkosten and k in neue_einzelkosten:
            n = dez(neue_einzelkosten[k], f"Alternative {k}")
            schritte.append(f"{k}: Alternative {_zahl(ek)} € → {_zahl(n)} €")
            ek = n
        if aenderung_prozent and k in aenderung_prozent:
            p = dez(aenderung_prozent[k], f"Änderung {k}")
            n = ek * (1 + p / 100)
            schritte.append(f"{k}: {_zahl(ek)} € × (1 + {_zahl(p)} / 100) = {_zahl(n)} €")
            ek = n
        if ek < 0:
            raise ValueError(f"Variante: Einzelkosten {k} wären negativ")
        neu[k] = ek
    variante = rechne(neu, zuschlaege, menge)
    d_ep, d_gp = variante["ep"] - basis["ep"], variante["gp"] - basis["gp"]
    schritte.append(f"Differenz EP = {_eur(variante['ep'])} − {_eur(basis['ep'])} = {_eur(d_ep)}")
    schritte.append(f"Differenz GP = {_eur(variante['gp'])} − {_eur(basis['gp'])} = {_eur(d_gp)}")
    return {"basis": basis, "variante": variante, "diff_ep": d_ep, "diff_gp": d_gp, "schritte": schritte}


def seite():
    import streamlit as st
    from ui_stil import kopf
    kopf("Zuschlag und What-if", "Alle Werte sind Ihre Eingaben")
    st.info(HINWEIS)
    menge = st.number_input("Menge", min_value=0.0, value=0.0, step=1.0, format="%.3f")
    st.subheader("Einzelkosten je Einheit (€) und Zuschläge (%)")
    ek, zu = {}, {}
    for k in KOSTENARTEN:
        c = st.columns(4)
        ek[k] = c[0].number_input(f"{k} €", min_value=0.0, value=0.0, step=0.5, format="%.2f", key=f"ek_{k}")
        zu[k] = {z: c[i + 1].number_input(f"{z} % ({k})", min_value=0.0, value=0.0, step=0.5, format="%.2f",
                                           key=f"z_{z}_{k}") for i, z in enumerate(ZUSCHLAGSARTEN)}
    basis = rechne(ek, zu, menge)
    st.metric("Einheitspreis (Rechnung mit Ihren Eingaben)", _eur(basis["ep"]))
    st.metric("Gesamtpreis", _eur(basis["gp"]))
    with st.expander("Rechenweg", expanded=True):
        for s in basis["schritte"]:
            st.write(s)
    st.subheader("What-if")
    aend = {k: st.number_input(f"Änderung {k} (%)", value=0.0, step=1.0, format="%.2f", key=f"a_{k}")
            for k in KOSTENARTEN}
    w = what_if(ek, zu, menge, {k: v for k, v in aend.items() if v})
    st.write(f"Variante: EP {_eur(w['variante']['ep'])}, GP {_eur(w['variante']['gp'])}; "
             f"Differenz EP {_eur(w['diff_ep'])}, GP {_eur(w['diff_gp'])}")
    with st.expander("Rechenweg What-if"):
        for s in w["schritte"] + w["variante"]["schritte"]:
            st.write(s)


if __name__ == "__main__":
    seite()
