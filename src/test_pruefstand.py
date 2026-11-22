"""
test_pruefstand.py - Tests für src/pruefstand.py (L24, Leitplanke E14).

Aufruf aus der Projektwurzel (uv-Befehl mit festen Versionen siehe AGENTS.md):
  python src/test_pruefstand.py
Exit-Code 0 = alle Tests bestanden. Schreibt nichts.
"""
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pruefstand as P                                              # noqa: E402

ergebnisse = []


def check(name, ok, detail=""):
    ergebnisse.append(ok)
    print(f"{'OK    ' if ok else 'FEHLER'} {name}" + (f" – {detail}" if detail and not ok else ""))


def main():
    s = P.erstellen(b"abc", commit="test")
    check("SHA-256 der Datei-Bytes", s["sha256"] == hashlib.sha256(b"abc").hexdigest())
    check("Commit übernommen", s["commit"] == "test")
    check("Prompt-Version aus src/ki_pruefung.py", s["prompt_version"] == "P4-v2", s["prompt_version"])
    check("Versionen nennen jedes festgelegte Paket", all(p in s["versionen"] for p in P.FEST), s["versionen"])
    check("Zeilen in fester Reihenfolge", [n for n, _ in P.zeilen(s)] == [
        "Git-Commit des Tools", "Bibliotheksversionen", "Prompt-Version (KI)", "SHA-256 der geprüften Datei"])
    check("Gleiche Bytes, gleicher Prüfstand (E14)", P.erstellen(b"abc", commit="x") == P.erstellen(b"abc", commit="x"))
    check("Abweichung wird mit „(fest: …)“ markiert, wenn vorhanden",
          all(f"{p} " in s["versionen"] and "(fest:" in s["versionen"] for p in P.abweichend()) or not P.abweichend(),
          str(P.abweichend()))
    print(f"INFO   installiert: {s['versionen']}")
    print(f"\n{sum(ergebnisse)}/{len(ergebnisse)} Tests bestanden")
    return 0 if all(ergebnisse) else 1


if __name__ == "__main__":
    sys.exit(main())
