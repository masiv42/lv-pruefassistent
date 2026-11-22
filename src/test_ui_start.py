"""
test_ui_start.py - B8d (Sitzung UI2, Team 22.11.2026): Startdatei start_app.command und README-Abschnitt.

Prüft ohne die App zu starten: ausführbar, kein fester Pfad und kein Benutzername, Versionen wie in AGENTS.md (E14),
nur localhost und ohne Nutzungsstatistik, Start aus dem eigenen Ordner, „KI aus“ ohne .env.
Aufruf aus der Projektwurzel: python src/test_ui_start.py
"""
import os
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
ergebnisse = []


def check(name, ok, detail=""):
    ergebnisse.append(bool(ok))
    print(("OK    " if ok else "FEHLT ") + name + ("" if ok else f"  [{detail}]"))


if __name__ == "__main__":
    start = ROOT / "start_app.command"
    text = start.read_text(encoding="utf-8") if start.exists() else ""
    check("start_app.command vorhanden", bool(text))
    check("ausführbar", start.exists() and os.access(start, os.X_OK))
    check("startet aus dem eigenen Ordner", 'cd "$(dirname "$0")"' in text)
    check("kein fester Pfad, kein Benutzername", not re.search(r"/Users/|/home/|/private/|~/", text))
    soll = re.findall(r"(\w+==[\d.]+)", (ROOT / "AGENTS.md").read_text(encoding="utf-8").split("Feste Bibliotheksversionen")[1]
                      .split("\n")[0])
    ist = set(re.findall(r"--with (\S+==[\d.]+)", text))
    check("Bibliotheksversionen wie in AGENTS.md (E14)", ist == set(soll), f"{sorted(ist)} vs {sorted(soll)}")
    check("Python 3.12", "--python 3.12" in text)
    check("nur localhost, keine Nutzungsstatistik", "--server.address localhost" in text
          and "--browser.gatherUsageStats false" in text)
    check("startet src/app.py", "streamlit run src/app.py" in text)
    check("kein Key im Skript", "API_KEY" not in text and "source" not in text)

    from ki_pruefung import lade_konfig, ki_status, KI_AUS
    leer = Path(tempfile.mkdtemp()) / ".env"                     # nicht vorhandene .env
    check("ohne .env: KI aus", ki_status(lade_konfig(leer)) == KI_AUS, ki_status(lade_konfig(leer)))

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    abschnitt = readme.split("## So startest du die App")[1].split("\n## ")[0] if "## So startest du die App" in readme else ""
    check("README: Abschnitt „So startest du die App“", bool(abschnitt))
    check("README nennt start_app.command und KI aus", "start_app.command" in abschnitt and "KI aus" in abschnitt)
    print(f"\n{sum(ergebnisse)}/{len(ergebnisse)} Tests bestanden")
    sys.exit(0 if all(ergebnisse) else 1)
