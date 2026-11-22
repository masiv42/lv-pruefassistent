"""
test_status_ablage.py - Tests für src/status_ablage.py (L19, Leitplanke E12 (4)).

Prüft, dass LV_FINDINGS_DIR die Ablage in einen Temp-Ordner umlenkt, dass ohne die Variable
data/findings/ gilt und dass data/raw/ abgewiesen wird. Schreibt nur in Temp-Ordner.
Aufruf aus der Projektwurzel (uv-Befehl siehe AGENTS.md):
  python src/test_status_ablage.py
Exit-Code 0 = alle Tests bestanden.
"""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import status_ablage as S                                         # noqa: E402

ergebnisse = []


def check(name, ok, detail=""):
    ergebnisse.append(ok)
    print(f"{'OK    ' if ok else 'FEHLER'} {name}" + (f" – {detail}" if detail and not ok else ""))


def main():
    alt = os.environ.pop(S.UMGEBUNG, None)
    projekt_vorher = sorted(p.name for p in S.STANDARD.iterdir()) if S.STANDARD.exists() else []
    try:
        check("Ohne LV_FINDINGS_DIR: Ablage in data/findings/ (unverändert)",
              S.status_pfad("x.X83") == (S.STANDARD / "x.X83.json").resolve())
        check("L32: Anzeige ohne Variable „Projektablage (data/findings)“", S.ablage_name() == "Projektablage (data/findings)")
        with tempfile.TemporaryDirectory() as tmp:
            os.environ[S.UMGEBUNG] = tmp
            pfad = S.status_pfad("test.X83")
            check("Mit LV_FINDINGS_DIR: Ablage im Temp-Ordner", pfad.parent == Path(tmp).resolve(), str(pfad))
            check("L32: Anzeige mit Variable „Temp-Ablage (Agent)“, kein Pfad", S.ablage_name() == "Temp-Ablage (Agent)"
                  and tmp not in S.ablage_name())
            funde = [{"id": "1|test.X83|1.1", "status": "bestätigt"}]
            S.speichere("test.X83", funde)
            check("Speichern und Laden über den Temp-Ordner", S.lade_status("test.X83") == {"1|test.X83|1.1": "bestätigt"})
            check("Datei liegt im Temp-Ordner", (Path(tmp) / "test.X83.json").exists())
            os.environ[S.UMGEBUNG] = str(S.RAW)
            try:
                S.status_pfad("test.X83")
                check("data/raw/ als Ablage wird abgewiesen", False)
            except RuntimeError:
                check("data/raw/ als Ablage wird abgewiesen", True)
        os.environ.pop(S.UMGEBUNG, None)
        projekt_nachher = sorted(p.name for p in S.STANDARD.iterdir()) if S.STANDARD.exists() else []
        check("data/findings/ des Projekts unverändert", projekt_vorher == projekt_nachher,
              f"{projekt_vorher} → {projekt_nachher}")
    finally:
        os.environ.pop(S.UMGEBUNG, None)
        if alt is not None:
            os.environ[S.UMGEBUNG] = alt
    print(f"\n{sum(ergebnisse)}/{len(ergebnisse)} Tests bestanden")
    return 0 if all(ergebnisse) else 1


if __name__ == "__main__":
    sys.exit(main())
