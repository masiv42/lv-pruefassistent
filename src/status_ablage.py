"""
status_ablage.py - Ablage der Status (offen / bestätigt / verworfen / Rückfrage stellen) je LV.

Standard: data/findings/<datei>.json im Projekt. Status dort stammen nur von Menschen
(Leitplanke E12 (4)). Tests und Browser-Prüfungen durch Agenten setzen die Umgebungsvariable
LV_FINDINGS_DIR auf einen Temp-Ordner (Team, 21.11.2026, L19); ohne die Variable bleibt alles
wie bisher. In data/raw/ wird nie geschrieben.
"""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
STANDARD = ROOT / "data" / "findings"
UMGEBUNG = "LV_FINDINGS_DIR"


def ordner():
    """Ablageordner: LV_FINDINGS_DIR, sonst data/findings/ des Projekts."""
    wert = os.environ.get(UMGEBUNG, "").strip()
    return Path(wert).expanduser().resolve() if wert else STANDARD


def ablage_name():
    """Kurze Anzeige der Ablage in der App, ohne lokalen Pfad (L32)."""
    return "Temp-Ablage (Agent)" if os.environ.get(UMGEBUNG, "").strip() else "Projektablage (data/findings)"


def status_pfad(datei):
    pfad = (ordner() / f"{Path(datei).name}.json").resolve()
    if pfad.is_relative_to(RAW.resolve()):          # Rohdaten nie anfassen
        raise RuntimeError("Statusdatei darf nicht in data/raw/ liegen")
    return pfad


def lade_status(datei):
    pfad = status_pfad(datei)
    if not pfad.exists():
        return {}
    return {f["id"]: f["status"] for f in json.loads(pfad.read_text(encoding="utf-8"))}


def speichere(datei, funde):
    pfad = status_pfad(datei)
    pfad.parent.mkdir(parents=True, exist_ok=True)
    pfad.write_text(json.dumps(funde, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
