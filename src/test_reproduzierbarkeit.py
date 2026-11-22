"""
test_reproduzierbarkeit.py - Doppellauf-Test nach Leitplanke E14 (Team, 21.11.2026).

1. alle_pruefungen() und pruefabdeckung.abdeckung() laufen über alle Dateien in data/raw dreimal, jeweils in einem eigenen
   Prozess (verschiedene PYTHONHASHSEED), einmal in umgekehrter Dateireihenfolge. Jede Ausgabe
   geht nur in einen Temp-Ordner. Die drei JSON-Ausgaben müssen byte-gleich sein.
2. Formatvergleich je (Prüfung, OZ): dasselbe LV in verschiedenen Formaten liefert dieselben
   Regel-Funde. Bekannte Abweichungen stehen in BEKANNT, jede mit Beleg am Original
   (vom Skeptiker geprüft, 21.11.2026).

Aufruf aus der Projektwurzel (uv-Befehl siehe AGENTS.md):
  python src/test_reproduzierbarkeit.py data/raw
Exit-Code 0 = alle Tests bestanden. Nichts wird in data/ geschrieben.
"""
import json
import os
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

SRC = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC))

IGNORIERT = {".DS_Store"}                     # E11: macOS-Systemdateien (Team, 21.11.2026)

GRUPPEN = [                                   # dasselbe LV in verschiedenen Formaten (Team, 21.11.2026)
    ["8209.003_Leistungsverzeichnis_leer.X83", "8209.003_Leistungsverzeichnis_leer.D83",
     "HEM2301-2_Gesamt-LV.pdf"],
    ["[NUMMER_001]_leer.X83", "Leistungsverzeichnis_leer.pdf", "Abgabe LV.pdf"],
    ["GAEB-[PROJEKT_004].X83", "LV-Ausdruck-[PROJEKT_004].pdf"],
    ["Leistungsverzeichnis.pdf", "Angebot AN24-0305.pdf"],
]

# (Prüfung, normalisierte OZ) -> (Dateien mit Fund, Beleg am Original)
# B1p3 (22.11.2026): Die FS2-Abweichungen „Text hinter der Mengenzeile“ sind behoben und ausgetragen: Nr. 7 HEM 6.1.6, 6.4.4;
# Nr. 8 HEM 6.1.4, 6.2.1; Nr. 9 3.1.8 (Leistungsverzeichnis_leer.pdf, Abgabe LV.pdf); Nr. 10 LV-Ausdruck 4.3.
BEKANNT = {
    "GAEB-[PROJEKT_004].X83|LV-Ausdruck-[PROJEKT_004].pdf": {
        # (1, "2.9") entfällt seit B1q: „DN 800/900“ ist eine Angabe mit DN 900 (Kurztext „bis DN 900 mm“),
        # daher in keinem Format mehr ein Fund (Skeptiker am X83, Item 0009, 21.11.2026)
    },
    "8209.003_Leistungsverzeichnis_leer.X83|8209.003_Leistungsverzeichnis_leer.D83|HEM2301-2_Gesamt-LV.pdf": {
        (7, "3.5.1"): (["8209.003_Leistungsverzeichnis_leer.X83", "HEM2301-2_Gesamt-LV.pdf"],
                       "D83 Satz 26 Z. 2045: „02Bglw.)“ statt „o. glw.)“ – im GAEB-90-Original anders geschrieben; "
                       "Skeptiker Sitzung B2 (B2-Integration 21.11.2026)"),
    },
    "[NUMMER_001]_leer.X83|Leistungsverzeichnis_leer.pdf|Abgabe LV.pdf": {},
    "GAEB-[PROJEKT_004].X83|LV-Ausdruck-[PROJEKT_004].pdf": {
        **{(nr, "2.17"): (["GAEB-[PROJEKT_004].X83"],
                          "LV-Ausdruck S. 10 druckt bei 02.0017 nicht den Kurztext „Bestehende Bachverrohrung DN 600 Beton "
                          "ausbauen, entsorgen“, sondern „Bauteile, welche im Zuge Aushubarbeiten freigelegt werden …“; "
                          "Skeptiker 21.11.2026 (B2-Integration)") for nr in (8, 9)},
    },
    "Leistungsverzeichnis.pdf|Angebot AN24-0305.pdf": {
        **{(nr, oz): (["Leistungsverzeichnis.pdf"],
                      "Angebot AN24-0305.pdf druckt nur den Kurztext (z. B. S. 2 „1.1.150 … Buschwerk entfernen und "
                      "entsorgen“); der Langtext mit dem Treffer fehlt dort; Skeptiker Sitzung B2 (B2-Integration)")
           for nr, oz in ((8, "1.1.150"), (8, "4.1.300"), (8, "5.2.70"), (8, "7.1.10"), (10, "2.1.420"),
                          (10, "2.1.430"), (12, "2.2.40"), (12, "5.1.80"))},
        (1, "3.2.60"): (["Leistungsverzeichnis.pdf"],
                        "Angebot AN24-0305.pdf S. 13: nur Kurztext „Muffenschutz aus Gummi DN 300 liefern "
                        "und einbauen“, „DN 500“ fehlt; Skeptiker 21.11.2026"),
        (1, "5.3.100"): (["Leistungsverzeichnis.pdf"],
                         "Angebot AN24-0305.pdf S. 22: nur Kurztext „Wasserschieber m. HRD MDP 16, DN 100 "
                         "Kurzbaul.“; Skeptiker 21.11.2026"),
        (1, "5.3.210"): (["Leistungsverzeichnis.pdf"],
                         "Angebot AN24-0305.pdf S. 23: nur Kurztext „Profilstahlkonstruktionen aus [PERSON_115] h "
                         "bis 60 cm, bis DN 250“, der Langtext mit „bis DN 300“ (Leistungsverzeichnis.pdf S. 64) "
                         "ist nicht gedruckt; neu seit B1p; Skeptiker 21.11.2026"),
    },
}

ergebnisse = []


def check(name, ok, detail=""):
    ergebnisse.append(ok)
    print(f"{'OK    ' if ok else 'FEHLER'} {name}" + (f" – {detail}" if detail and not ok else ""))


def dateien(d):
    return sorted(p for p in Path(d).iterdir() if p.is_file() and p.name not in IGNORIERT)


def lauf(d, ziel, umgekehrt):
    """Ein Lauf: prüft alle Dateien und schreibt {datei: funde} nach `ziel` (immer nach Name sortiert,
    damit nur die Ergebnisse verglichen werden, nicht die Verarbeitungsreihenfolge)."""
    from lv_parser import parse
    from pruefung_formal import alle_pruefungen
    from pruefabdeckung import abdeckung
    if Path(ziel).resolve().is_relative_to((SRC.parent / "data").resolve()):
        sys.exit("Ausgabe darf nicht in data/ liegen")
    folge = dateien(d)[::-1] if umgekehrt else dateien(d)
    aus, abd = {}, {}
    for p in folge:
        try:
            df = parse(p)
        except Exception as e:                 # nicht lesbare Datei: Fehlertext gehört zum Ergebnis
            aus[p.name] = {"fehler": f"{type(e).__name__}: {e}"}
            continue
        aus[p.name] = alle_pruefungen(df, p)
        abd[p.name] = abdeckung(df)               # Prüfabdeckung (B1b) gehört zum Ergebnis (E14)
    text = json.dumps({"funde": {k: aus[k] for k in sorted(aus)}, "abdeckung": {k: abd[k] for k in sorted(abd)}},
                      ensure_ascii=False, indent=1)
    Path(ziel).write_text(text + "\n", encoding="utf-8")


def schluessel(funde):
    return {(f["pruefung"], f["id"].split("|")[2]) for f in funde}


def main(d):
    with tempfile.TemporaryDirectory() as tmp:
        jobs = []
        for i, umgekehrt in enumerate([False, False, True]):
            ziel = Path(tmp) / f"lauf{i + 1}.json"
            env = dict(os.environ, PYTHONHASHSEED=str(i))
            cmd = [sys.executable, __file__, "--lauf", str(d), str(ziel)] + (["--umgekehrt"] if umgekehrt else [])
            jobs.append((ziel, subprocess.Popen(cmd, env=env)))
        for ziel, p in jobs:
            check(f"Lauf {ziel.stem} beendet", p.wait() == 0)
        roh = [z.read_bytes() for z, _ in jobs]
        check("Doppellauf: drei Läufe byte-gleich (einer in umgekehrter Reihenfolge)",
              roh[0] == roh[1] == roh[2], f"Größen {[len(r) for r in roh]}")
        alle = json.loads(roh[0])["funde"]

    lesbar = {k: v for k, v in alle.items() if isinstance(v, list)}
    zahl = Counter(f["pruefung"] for v in lesbar.values() for f in v)
    print(f"INFO   {sum(zahl.values())} Funde in {len(lesbar)} lesbaren Dateien "
          f"(nicht lesbar: {sorted(set(alle) - set(lesbar)) or 'keine'}); je Prüfung {dict(sorted(zahl.items()))}")
    check("Fund-IDs je Datei eindeutig",
          all(len({f['id'] for f in v}) == len(v) for v in lesbar.values()))

    for gruppe in GRUPPEN:
        fehlt = [g for g in gruppe if g not in lesbar]
        if fehlt:
            check(f"Formatvergleich {gruppe}: alle Dateien lesbar", False, f"fehlt: {fehlt}")
            continue
        ks = {g: schluessel(lesbar[g]) for g in gruppe}
        bekannt = BEKANNT.get("|".join(gruppe), {})
        abweichend = {}
        for k in set().union(*ks.values()):
            mit = [g for g in gruppe if k in ks[g]]
            if len(mit) != len(gruppe):
                abweichend[k] = mit
        unbelegt = {k: v for k, v in abweichend.items() if k not in bekannt or bekannt[k][0] != v}
        if gruppe == ["Leistungsverzeichnis.pdf", "Angebot AN24-0305.pdf"]:
            # Angebot AN24-0305.pdf druckt nur Kurztexte (B1p: 0 von 274 mit eigenem Langtext, test_parser_pdf): Funde
            # nur im Leistungsverzeichnis stützen sich auf den Langtext (B2-Integration: alle 63 geprüft, FS2)
            nur_lv = {k for k, v in unbelegt.items() if v == ["Leistungsverzeichnis.pdf"]}
            print(f"INFO   {len(nur_lv)} Funde nur in Leistungsverzeichnis.pdf (Langtext; Angebot ohne Langtext)")
            unbelegt = {k: v for k, v in unbelegt.items() if k not in nur_lv}
        check(f"Formatvergleich {' = '.join(gruppe)}: gleiche Regel-Funde je (Prüfung, OZ)",
              not unbelegt, f"Abweichung ohne Beleg: {sorted(unbelegt.items(), key=str)}")
        weg = [k for k in bekannt if k not in abweichend]
        check(f"Formatvergleich {gruppe[0]}: jede bekannte Abweichung tritt noch auf", not weg, str(weg))
        for k, (_, beleg) in sorted(bekannt.items(), key=str):
            if k in abweichend:
                print(f"INFO   bekannte Abweichung Nr. {k[0]} OZ {k[1]}: {beleg}")

    n_ok = sum(ergebnisse)
    print(f"\n{n_ok}/{len(ergebnisse)} Tests bestanden")
    return 0 if all(ergebnisse) else 1


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--lauf":
        lauf(sys.argv[2], sys.argv[3], "--umgekehrt" in sys.argv)
        sys.exit(0)
    sys.exit(main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/raw")))
