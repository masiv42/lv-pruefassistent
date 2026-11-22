"""
pruefstand.py - Prüfstand einer Prüfung (L24, Leitplanke E14, Team 21.11.2026).

Nennt, womit ein LV geprüft wurde: Git-Commit des Tools, Bibliotheksversionen (mit Abgleich gegen
die festgelegten Versionen), Prompt-Version der KI-Gegenprüfung und SHA-256 der geprüften Datei.
App (Kopfbereich) und Risikobericht (Blatt „Übersicht“) zeigen denselben Prüfstand.
"""
import hashlib
import importlib.metadata as md
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Festgelegte Versionen (Team, 21.11.2026, B0b 7b; docs/decisions.md); Python 3.12
FEST = {"pdfplumber": "0.11.11", "pandas": "3.1.1", "lxml": "6.1.3", "openpyxl": "3.1.5",
        "streamlit": "1.67.0", "openai": "3.57.0", "anthropic": "2.12.0"}


def git_commit():
    """Stand des Tools, z. B. „7993e3c“ oder „7993e3c-dirty“ bei lokalen Änderungen."""
    try:
        r = subprocess.run(["git", "-C", str(ROOT), "describe", "--always", "--dirty", "--abbrev=7"],
                           capture_output=True, text=True, timeout=5)
        return r.stdout.strip() or "unbekannt"
    except (OSError, subprocess.SubprocessError):
        return "unbekannt"


def installiert(paket):
    try:
        return md.version(paket)
    except md.PackageNotFoundError:
        return None


def versionen():
    """Text wie „pdfplumber 0.11.11 · pandas 3.1.1 …“; Abweichungen von FEST mit „(fest: …)“,
    nicht installierte Pakete mit „nicht installiert“."""
    teile = []
    for p, fest in FEST.items():
        v = installiert(p)
        if v is None:
            teile.append(f"{p} nicht installiert")
        elif v != fest:
            teile.append(f"{p} {v} (fest: {fest})")
        else:
            teile.append(f"{p} {v}")
    return " · ".join(teile)


def abweichend():
    """Installierte Pakete, deren Version von FEST abweicht."""
    return [p for p, fest in FEST.items() if installiert(p) not in (None, fest)]


def prompt_version():
    try:
        from ki_pruefung import PROMPT_VERSION          # spät importiert: ki_pruefung importiert bericht
        return PROMPT_VERSION
    except Exception:                                    # ohne KI-Pakete läuft die Regelprüfung weiter
        return "unbekannt"


def erstellen(daten, commit=None):
    """Prüfstand für die Datei-Bytes `daten`."""
    return {
        "commit": commit or git_commit(),
        "versionen": versionen(),
        "prompt_version": prompt_version(),
        "sha256": hashlib.sha256(daten).hexdigest(),
    }


ZEILEN = [("Git-Commit des Tools", "commit"), ("Bibliotheksversionen", "versionen"),
          ("Prompt-Version (KI)", "prompt_version"), ("SHA-256 der geprüften Datei", "sha256")]


def zeilen(stand):
    """(Bezeichnung, Wert) für App und Bericht, immer in derselben Reihenfolge."""
    return [(name, stand[k]) for name, k in ZEILEN]
