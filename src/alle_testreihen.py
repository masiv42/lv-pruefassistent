"""
alle_testreihen.py - alle Testreihen laut AGENTS.md parallel (Team, 22.11.2026, 00:45).

Jede Reihe schreibt in eine eigene Logdatei; am Ende stehen Ergebnis, Laufzeit je Reihe und die Gesamtzeit in
<log-ordner>/zusammenfassung.tsv. Doppellauf und Durchlauf laufen mit. Am besten auf einem sauberen Checkout starten,
weil der Stand im Doppellauf und im Bericht sonst „-dirty“ zeigt.

Aufruf aus der Projektwurzel (uv-Befehl siehe AGENTS.md, zusätzlich --with streamlit==1.67.0 --with anthropic==2.12.0
--with openai==3.57.0):
  python src/alle_testreihen.py <log-ordner außerhalb von data/raw> [--jobs 7]
Exit-Code 0 = alle Reihen grün.
"""
import argparse
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REIHEN = [(n, ".", ["src/" + d] + a) for n, d, a in (
    ("validate_parser", "validate_parser.py", ["data/raw"]),
    ("pruefung", "test_pruefung.py", ["data/raw", "--stufe2"]),
    ("pruefung_formal", "test_pruefung_formal.py", ["data/raw"]),
    ("bericht", "test_bericht.py", ["data/raw"]),
    ("ki_client", "test_ki_client.py", []),
    ("ki_pruefung", "test_ki_pruefung.py", ["data/raw"]),
    ("status_ablage", "test_status_ablage.py", []),
    ("auswertung_v2", "test_auswertung_v2.py", []),
    ("pruefstand", "test_pruefstand.py", []),
    ("pruefabdeckung", "test_pruefabdeckung.py", ["data/raw"]),
    ("parser_pdf", "test_parser_pdf.py", ["data/raw"]),
    ("parser_gaeb90", "test_parser_gaeb90.py", ["data/raw"]),
    ("regel_dn", "test_regel_dn.py", []),
    ("ki_b5", "test_ki_b5.py", []),
    ("ki_blatt", "test_ki_blatt.py", []),
    ("nachtrag_streit", "test_nachtrag_streit.py", ["data/raw"]),
    ("erfahrung", "test_erfahrung.py", []),
    ("skeptiker_s2", "test_skeptiker_s2.py", ["data/raw"]),
    ("ui_sitzung", "test_ui_sitzung.py", []),
    ("ui_start", "test_ui_start.py", []),
    ("pruefung_rechnung", "test_pruefung_rechnung.py", ["data/raw"]),
    ("doppellauf", "test_reproduzierbarkeit.py", ["data/raw"]),
)] + [(n, "src", [d] + a) for n, d, a in (
    ("hinweise", "test_pruefung_hinweise.py", ["../data/raw"]),
    ("struktur", "test_pruefung_struktur.py", ["../data/raw"]),
    ("vollstaendigkeit", "test_pruefung_vollstaendigkeit.py", ["../data/raw"]),
    ("excel_import", "test_excel_import.py", ["../data/raw"]),
    ("seite_zuschlag", "test_seite_zuschlag.py", []),
    ("vergleichspreise", "test_vergleichspreise.py", ["../data/raw"]),
    ("demo_lv", "test_demo_lv.py", ["../data/raw"]),
    ("bieterfragen", "test_bieterfragen.py", ["../data/raw"]),
    ("rueckblick", "test_rueckblick.py", ["../data/raw"]),
    ("seite_uebersicht", "test_seite_uebersicht.py", []),
    ("durchlauf", "test_durchlauf.py", ["../data/raw"]),
    ("ui_stil", "test_ui_stil.py", []),
    ("ui_theme", "test_ui_theme.py", []),
    ("ui_positionen", "test_ui_positionen.py", ["../data/raw"]),
)]


def lauf(reihe, logs):
    name, ordner, befehl = reihe
    start = time.monotonic()
    with open(logs / f"{name}.log", "w", encoding="utf-8") as log:
        code = subprocess.run([sys.executable] + befehl, cwd=ROOT / ordner, stdout=log, stderr=subprocess.STDOUT).returncode
    text = [z for z in (logs / f"{name}.log").read_text(encoding="utf-8", errors="replace").splitlines() if z.strip()]
    return name, code, time.monotonic() - start, (text[-1].strip()[:90] if text else "")


def main():
    ap = argparse.ArgumentParser(description="Alle Testreihen parallel")
    ap.add_argument("logs", type=Path)
    ap.add_argument("--jobs", type=int, default=7)
    a = ap.parse_args()
    logs = a.logs.resolve()
    if (ROOT / "data" / "raw").resolve() in [logs, *logs.parents]:
        sys.exit("Log-Ordner darf nicht in data/raw liegen")
    logs.mkdir(parents=True, exist_ok=True)
    start = time.monotonic()
    erg = []
    with ThreadPoolExecutor(a.jobs) as pool:
        for f in as_completed([pool.submit(lauf, r, logs) for r in REIHEN]):
            erg.append(f.result())
            print(f"{'OK    ' if erg[-1][1] == 0 else 'FEHLER'} {erg[-1][0]} ({erg[-1][2]:.0f} s): {erg[-1][3]}", flush=True)
    gesamt = time.monotonic() - start
    summe = sum(e[2] for e in erg)
    rot = sorted(e[0] for e in erg if e[1] != 0)
    zeilen = [f"{n}\texit={c}\t{t:.0f}s\t{z}" for n, c, t, z in sorted(erg)]
    zeilen.append(f"GESAMT\t{len(erg) - len(rot)}/{len(erg)} grün\t{gesamt:.0f}s parallel\t{summe:.0f}s nacheinander")
    (logs / "zusammenfassung.tsv").write_text("\n".join(zeilen) + "\n", encoding="utf-8")
    print(zeilen[-1].replace("\t", " | "))
    if rot:
        print("nicht grün:", ", ".join(rot))
    return 1 if rot else 0


if __name__ == "__main__":
    sys.exit(main())
