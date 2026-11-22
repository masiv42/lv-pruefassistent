"""
test_ui_theme.py - Prüft .streamlit/config.toml (Sitzung UI): Dark und Light vollständig, Kontrast nach WCAG, kein reines
Schwarz, Akzent Blau. Aufruf aus src/:  python test_ui_theme.py
"""
import sys
import tomllib
from pathlib import Path

CONFIG = Path(__file__).resolve().parent.parent / ".streamlit" / "config.toml"
ergebnisse = []


def check(name, ok, detail=""):
    ergebnisse.append(bool(ok))
    print(f"{'OK    ' if ok else 'FEHLER'} {name}" + (f" – {detail}" if detail and not ok else ""))


def _hell(farbe):
    h = farbe.lstrip("#")
    kanal = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    kanal = [x / 12.92 if x <= .03928 else ((x + .055) / 1.055) ** 2.4 for x in kanal]
    return .2126 * kanal[0] + .7152 * kanal[1] + .0722 * kanal[2]


def kontrast(a, b):
    x, y = sorted((_hell(a), _hell(b)), reverse=True)
    return (x + .05) / (y + .05)


if __name__ == "__main__":
    theme = tomllib.loads(CONFIG.read_text(encoding="utf-8"))["theme"]
    check("Kein festes `base`: Dark und Light bleiben wählbar", "base" not in theme)
    for modus in ("dark", "light"):
        t = theme[modus]
        check(f"{modus}: alle Farbrollen", all(f"{c}{r}" in t for c in ("red", "orange", "gray", "green", "blue")
                                               for r in ("Color", "TextColor", "BackgroundColor")))
        check(f"{modus}: kein reines Schwarz", t["backgroundColor"].lower() != "#000000")
        for vorder, hinter in (("textColor", "backgroundColor"), ("textColor", "secondaryBackgroundColor"),
                               ("grayTextColor", "backgroundColor"), ("grayTextColor", "secondaryBackgroundColor"),
                               ("linkColor", "backgroundColor")):
            w = kontrast(t[vorder], t[hinter])
            check(f"{modus}: {vorder} auf {hinter} ≥ 4,5:1", w >= 4.5, f"{w:.2f}")
        w = kontrast("#FFFFFF", t["primaryColor"])
        check(f"{modus}: Text auf Akzent ≥ 4,5:1", w >= 4.5, f"{w:.2f}")
        for c in ("red", "orange", "gray", "green", "blue"):
            w = kontrast(t[f"{c}TextColor"], t[f"{c}BackgroundColor"])
            check(f"{modus}: Abzeichen {c} ≥ 4,5:1", w >= 4.5, f"{w:.2f}")
    print(f"\n{sum(ergebnisse)}/{len(ergebnisse)} Tests bestanden")
    sys.exit(0 if all(ergebnisse) else 1)
