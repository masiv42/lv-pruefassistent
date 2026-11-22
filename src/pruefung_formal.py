"""
pruefung_formal.py - Prüfungen Nr. 3–6 aus input/pruefkatalog.md (P2) und der
gemeinsame Einstieg für alle Prüfungen (alle_pruefungen).

Vorgaben des Teams (Chat 21.11.2026; „Prio“ heißt seit B1a „Stufe“, F1):
  Nr. 3 Menge oder Einheit fehlt  nachweisbarer Fehler, Stufe 1
        Menge None = fehlt; Menge 0 = eigener Hinweis "Menge 0" (Risikohinweis, Stufe 2, Rang 2: F2);
        Einheit fehlt = not einheit (None und "" bedeuten "keine Einheit").
        Auftrags-LV (Austauschphase 86) mit Menge 0 und leerer Einheit: Unklarheit, Stufe 4, „vormerken“
        (Team, 21.11.2026, F1 B1b); in Ausschreibungs-LVs bleibt „Einheit fehlt“ in Stufe 1.
        Bedarfsposition (Nr. 5) mit Menge 0: kein eigener Fund „Menge 0“, sondern Feldwert „Menge: 0“ im
        Nr.-5-Fund (Team, 21.11.2026, F2 B1b).
  Nr. 4 OZ doppelt im selben LV   nachweisbarer Fehler, Stufe 1
        ein Fund mit allen betroffenen Positionen, Belege = deren Kurztexte.
  Nr. 5 Bedarfsposition           Risikohinweis, Stufe 2
        Beleg = Textvermerk wörtlich ("Bedarfsposition", "Nur Einh.-Pr." …);
        bei GAEB XML das Kennzeichen <Provis> ("Kennzeichen in der Datei").
  Nr. 6 Pauschale                 Risikohinweis, Stufe 2; Beleg = Einheit "psch".
  Dateien nur mit Preisen (kein Kurztext, z. B. StBALV23040.D84): keine Prüfung.
  Fundliste nach Stufe, dann Rang in Stufe, dann OZ (F1, Team 21.11.2026).

Zitate stehen in `belege`, Feldwerte und Kennzeichen in `feldbelege`
(docs/data-contracts.md). Jeder Fund zu einer Position hat den Kurztext als
wörtliches Zitat; Positionen ohne Kurztext ergeben bei Nr. 3, 5, 6 keinen Fund (R5).

Bekannte Grenze Nr. 5: Bei PDF steht „Nur Einh.-Pr.“ in der Mengenzeile; diese
Zeile gibt der Parser nicht aus. Solche Positionen werden nur gemeldet, wenn ein
anderer Beleg vorhanden ist (Vermerk „*** Bedarfsposition …“ oder Text).

Aufruf (aus der Projektwurzel, uv-Befehl siehe AGENTS.md):
  python src/pruefung_formal.py <datei> [<datei> ...] [--out funde.json]
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

from lv_parser import parse
from pruefung_widerspruch import (pruefe as pruefe_widerspruch, normalisiere_oz, normalisiere_leerzeichen,
                                  PRIORITAET_IN_STUFE)

FEHLER, UNKLARHEIT, RISIKO = "nachweisbarer Fehler", "Unklarheit", "Risikohinweis"
FELDWERT, KENNZEICHEN = "Feldwert", "Kennzeichen in der Datei"
LEER = "(leer)"

# Kategorie und Stufe laut input/pruefkatalog.md und Team (Chat 21.11.2026; früher „Prio“, F1)
KATALOG = {3: (FEHLER, 1), 4: (FEHLER, 1), 5: (RISIKO, 2), 6: (RISIKO, 2)}
# "Menge 0" bei vorhandener Einheit (Team, Chat 21.11.2026, E1); Stufe 2 Kalkulationsrisiko (Team, 21.11.2026, F2)
MENGE_0 = (RISIKO, 2)
MENGE_0_TEXT = "Menge 0: Die Position geht nicht in die Angebotssumme ein, die Ausführungsmenge ist offen."
# Auftrags-LV (Austauschphase 86) mit Menge 0 und leerer Einheit (Team, 21.11.2026, F1 B1b)
AUFTRAG_OHNE_ME = (UNKLARHEIT, 4)
AUFTRAG_OHNE_ME_TITEL = "Ohne Menge und Einheit (Auftrags-LV)"
AUFTRAG_OHNE_ME_TEXT = ("Position im Auftrags-LV ohne Menge und Einheit – Abrechnungsgrundlage klären. "
                        "Empfehlung laut Prüfkatalog: vormerken.")
# Datei-Hinweis für Austauschphase 86 (Team, Chat 21.11.2026, E2); kein Fund wird unterdrückt
HINWEIS_PHASE_86 = ("Auftrags-LV (Austauschphase 86), kein Ausschreibungs-LV. "
                    "Nachtragspositionen enthalten oft nur einen Einheitspreis ohne Menge.")
EMPFEHLUNG = {3: "klärende Rückfrage", 4: "klärende Rückfrage", 5: "Risiko einpreisen", 6: "Risiko einpreisen"}

VERMERK_RE = re.compile(
    r"\b(?:Bedarfsposition|Eventualposition)\w*|\bnur\s*Einh\.?\s*-?\s*Pr\.?|\bnur\s+Einheitspreis\w*", re.I)
PROVIS_RE = re.compile(r"Bedarfsposition ?([^;]*)")   # art_roh bei GAEB XML: "Bedarfsposition <Provis-Text>"


def _txt(x):
    return x if isinstance(x, str) else ""


def _leer(x):
    return x is None or (isinstance(x, float) and pd.isna(x)) or not x


def _seite(x):
    return None if x is None or pd.isna(x) else int(x)


def _zahl(x):
    return f"{x:g}".replace(".", ",")


def nur_preise(df):
    """True, wenn das LV Positionen hat, aber keine davon einen Kurztext (reine Preisdatei)."""
    pos = df[df.typ == "Position"]
    return len(pos) > 0 and not any(_txt(k).strip() for k in pos.kurztext)


def oz_sortkey(oz):
    """Sortierschlüssel nach normalisierter OZ: Zahlen numerisch, sonst als Text."""
    return [(0, int(p), "") if p.isdigit() else (1, 0, p) for p in normalisiere_oz(oz).split(".")]


def sortiere(funde):
    """Nach Stufe, dann Rang in Stufe, dann OZ (erste Position), dann Prüfungs-Nr. (F1)."""
    return sorted(funde, key=lambda f: (f["stufe"], f["prioritaet_in_stufe"], oz_sortkey(f["positionen"][0]["oz"]),
                                        f["pruefung"]))


def _position(r):
    return {"datei": r.datei, "oz": r.oz, "seite": _seite(r.seite)}


def datei_hinweis(datei):
    """Hinweis zur ganzen Datei oder None. Austauschphase 86 (.D86/.X86): Auftrags-LV."""
    return HINWEIS_PHASE_86 if Path(datei).suffix.lower() in (".d86", ".x86") else None


def _neu(nr, r, titel, belege, feldbelege, begruendung, kategorie=None, prio=None, text=None):
    kat, pr = KATALOG[nr]
    kategorie, prio = kategorie or kat, prio or pr
    if nr == 3 and (kategorie, prio) == MENGE_0:
        quelle = "laut Team 21.11.2026 (F2)"
    elif nr == 3 and (kategorie, prio) == AUFTRAG_OHNE_ME:
        quelle = "laut Team 21.11.2026 (F1, B1b)"
    else:
        quelle = f"laut input/pruefkatalog.md, Nr. {nr}"
    return {
        "id": f"{nr}|{r.datei}|{normalisiere_oz(r.oz)}",
        "pruefung": nr,
        "kategorie": kategorie,
        "titel": titel,
        "positionen": [_position(r)],
        "belege": belege,
        "feldbelege": feldbelege,
        "begruendung": text or f"{begruendung} Empfehlung laut Prüfkatalog: {EMPFEHLUNG[nr]}.",
        "stufe": prio,
        "stufe_begruendung": f"Stufe {prio} {quelle}",
        "prioritaet_in_stufe": PRIORITAET_IN_STUFE[(nr, prio)],
        "rueckfrage": None,
        "status": "offen",
    }


def _sammeln(funde, f):
    """Höchstens ein Fund je Prüfung, Datei und normalisierter OZ (doppelte OZ: Positionen zusammen)."""
    alt = funde.get(f["id"])
    if alt is None:
        funde[f["id"]] = f
        return
    alt["positionen"] += f["positionen"]
    alt["belege"] += [b for b in f["belege"] if b not in alt["belege"]]
    alt["feldbelege"] += [b for b in f["feldbelege"] if b not in alt["feldbelege"]]


def _nr3(r, kurz):
    m_fehlt = r.menge is None or pd.isna(r.menge)
    m_null = not m_fehlt and r.menge == 0
    e_fehlt = _leer(r.einheit)
    if not (m_fehlt or m_null or e_fehlt):
        return None
    feld = []
    if m_fehlt:
        feld.append({"art": FELDWERT, "text": f"Menge: {LEER}"})
    if m_null:
        feld.append({"art": FELDWERT, "text": "Menge: 0"})
    if e_fehlt:
        feld.append({"art": FELDWERT, "text": f"Einheit: {LEER}"})
    if m_null and e_fehlt and datei_hinweis(r.datei) == HINWEIS_PHASE_86:      # F1 (B1b): Auftrags-LV
        kat, prio = AUFTRAG_OHNE_ME
        return _neu(3, r, AUFTRAG_OHNE_ME_TITEL, [kurz], feld, "", kat, prio, text=AUFTRAG_OHNE_ME_TEXT)
    if m_fehlt or e_fehlt:
        fehlt = [x for x, ja in (("Menge", m_fehlt), ("Einheit", e_fehlt)) if ja]
        titel = " und ".join(fehlt) + (" fehlen" if len(fehlt) == 2 else " fehlt")
        grund = f"Das Feld {' und das Feld '.join(fehlt)} {'sind' if len(fehlt) == 2 else 'ist'} leer."
        if m_null:
            titel += " (Menge 0)"
            grund += " Die Menge ist 0."
        return _neu(3, r, titel, [kurz], feld, grund)
    kat, prio = MENGE_0
    return _neu(3, r, "Menge 0", [kurz], feld, "", kat, prio, text=MENGE_0_TEXT)


def _nr5(r, kurz, lang):
    zitate, kennz = [], []
    art_roh = _txt(r.art_roh)
    if r.format == "GAEB XML":
        for m in PROVIS_RE.finditer(art_roh):
            v = m.group(1).strip()
            kennz.append({"art": KENNZEICHEN, "text": f"<Provis>{v}</Provis>" if v else "<Provis>"})
    elif r.format == "PDF" and re.search(r"bedarfsposition|eventualposition", art_roh, re.I):
        zitate.append(normalisiere_leerzeichen(art_roh))
    for t in (kurz, lang):
        for m in VERMERK_RE.finditer(t):
            z = normalisiere_leerzeichen(m.group())
            if z not in zitate:
                zitate.append(z)
    if not (zitate or kennz):
        return None
    nachweis = [f"„{z}“" for z in zitate] + [k["text"] for k in kennz]
    belege = [kurz] + [z for z in zitate if z != kurz]
    return _neu(5, r, "Bedarfsposition", belege, kennz,
                f"Vermerk bzw. Kennzeichen für Bedarfs-/Eventualposition oder nur Einheitspreis: "
                f"{', '.join(nachweis)}.")


def _nr6(r, kurz):
    if r.einheit != "psch":
        return None
    roh = _txt(r.einheit_roh).strip() or r.einheit
    return _neu(6, r, "Pauschale (psch)", [kurz], [{"art": FELDWERT, "text": f"Einheit: {roh}"}],
                f"Die Position wird pauschal abgerechnet (Einheit „{roh}“).")


def _nr4(pos):
    funde = []
    norm = pos.oz.map(normalisiere_oz)
    for n_oz in [k for k, v in Counter(norm).items() if v > 1]:
        gruppe = pos[norm == n_oz]
        erste = next(gruppe.itertuples())
        kurztexte = []
        for r in gruppe.itertuples():
            k = normalisiere_leerzeichen(_txt(r.kurztext))
            if k and k not in kurztexte:
                kurztexte.append(k)
        f = _neu(4, erste, "OZ doppelt im selben LV", kurztexte,
                 [{"art": FELDWERT, "text": f"OZ: {r.oz}"} for r in gruppe.itertuples()],
                 f"Die OZ {n_oz} kommt {len(gruppe)}-mal vor.")
        f["positionen"] = [_position(r) for r in gruppe.itertuples()]
        funde.append(f)
    return funde


def pruefe_formal(df):
    """Prüfungen Nr. 3–6 auf einer Tabelle aus parse(). Reine Preisdateien: keine Funde."""
    if nur_preise(df):
        return []
    pos = df[df.typ == "Position"]
    funde = {}
    for r in pos.itertuples():
        kurz = normalisiere_leerzeichen(_txt(r.kurztext))
        if not kurz:
            continue                                   # ohne Kurztext kein wörtlicher Beleg (R5)
        lang = _txt(r.langtext)
        f3, f5 = _nr3(r, kurz), _nr5(r, kurz, lang)
        if f3 and f5 and f3["titel"] == "Menge 0":    # F2 (B1b): Bedarfsposition mit Menge 0 = ein Fund
            f5["feldbelege"].append({"art": FELDWERT, "text": "Menge: 0"})
            f5["begruendung"] += " Die Menge ist 0."
            f3 = None
        for f in (f3, f5, _nr6(r, kurz)):
            if f:
                _sammeln(funde, f)
    for f in _nr4(pos):
        funde[f["id"]] = f
    return list(funde.values())


def alle_pruefungen(df, quelle=None):
    """Prüfungen Nr. 1–19, sortiert nach Stufe, Rang in Stufe und OZ. `quelle`: Pfad der Originaldatei; bei PDF und
    GAEB 90 Pflicht (Belege am Original). Reine Preisdateien: nur Nr. 17 Rechenprüfung (B1e).
    Nr. 7–14, 18 (pruefung_hinweise), 15/16 (pruefung_struktur), 19 (pruefung_vollstaendigkeit): Sitzung B2, integriert
    21.11.2026 (B2-Integration). Ränge aus der zentralen Tabelle PRIORITAET_IN_STUFE (Team 21:20)."""
    from pruefung_rechnung import pruefe_rechnung     # spät importiert: die Module importieren pruefung_formal
    from pruefung_hinweise import pruefe_hinweise
    from pruefung_struktur import pruefe_struktur
    from pruefung_vollstaendigkeit import pruefe_vollstaendigkeit
    f17 = pruefe_rechnung(df)[1]
    if nur_preise(df):
        return sortiere(f17)
    f16 = pruefe_widerspruch(df, quelle) + pruefe_formal(df)
    return sortiere(f16 + f17 + pruefe_hinweise(df, quelle, f16) + pruefe_struktur(df, quelle, f16)
                    + pruefe_vollstaendigkeit(df, quelle))


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Prüfungen Nr. 1–6")
    ap.add_argument("dateien", nargs="+")
    ap.add_argument("--out", help="Funde als JSON in diese Datei (nie in data/raw/)")
    a = ap.parse_args()
    alle = []
    for d in a.dateien:
        df = parse(d)
        if nur_preise(df):
            print(f"{Path(d).name}: nur Preise, keine Prüfung", file=sys.stderr)
            continue
        f = alle_pruefungen(df, d)
        zahl = Counter(x["pruefung"] for x in f)
        print(f"{Path(d).name}: {len(f)} Funde " + str(dict(sorted(zahl.items()))), file=sys.stderr)
        alle += f
    text = json.dumps(alle, ensure_ascii=False, indent=2)
    if a.out:
        if Path(a.out).resolve().is_relative_to(Path("data/raw").resolve()):
            sys.exit("--out darf nicht in data/raw/ liegen")
        Path(a.out).write_text(text + "\n", encoding="utf-8")
        print("gespeichert:", a.out, file=sys.stderr)
    else:
        print(text)
