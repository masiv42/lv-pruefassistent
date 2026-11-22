"""
test_seite_zuschlag.py - Tests für src/seite_zuschlag.py (Block B6a, Sitzung B2). Nur erfundene Zahlen; kein
Server-Start (Agenten starten die App nicht, Team 18:50); AppTest im Prozess als Zusatz (B2-F13). Aufruf aus src/:  python test_seite_zuschlag.py
"""
import ast
import sys
from decimal import Decimal
from pathlib import Path

from seite_zuschlag import rechne, what_if, dez, KOSTENARTEN, HINWEIS

ergebnisse = []


def check(name, ok, detail=""):
    ergebnisse.append(ok)
    print(f"{'OK    ' if ok else 'FEHLER'} {name}" + (f" – {detail}" if detail and not ok else ""))


EK = {"Lohn": "20", "Stoffe": "30,50", "Geräte": 5}                     # erfundene Werte
ZU = {"Lohn": {"BGK": 10, "AGK": 8, "W+G": 5}, "Stoffe": {"BGK": 5, "AGK": 5, "W+G": 5}, "Geräte": {"AGK": 10}}

r = rechne(EK, ZU, 12)
# von Hand: 20 × 1,23 = 24,6; 30,5 × 1,15 = 35,075; 5 × 1,10 = 5,5; Summe 65,175 → 65,18; GP 65,18 × 12 = 782,16
check("EP von Hand nachgerechnet (65,175 → 65,18, kaufmännisch gerundet)", r["ep"] == Decimal("65.18"), str(r["ep"]))
check("GP = gerundeter EP × Menge", r["gp"] == Decimal("782.16"), str(r["gp"]))
check("Rechenweg zeigt jeden Schritt", any("Lohn: Zuschlag = BGK 10 % + AGK 8 % + W+G 5 % = 23 %" in s
                                           for s in r["schritte"]) and r["schritte"][-1].startswith("GP = EP × Menge")
      and any("65,175" in s and "65,18 €" in s for s in r["schritte"]), str(r["schritte"]))
check("Kostenarten ohne Eingabe erscheinen nicht im Rechenweg", not any(s.startswith("Nachunternehmer")
                                                                         for s in r["schritte"]))
check("ohne Eingaben: alles 0 (keine Vorbelegung)", rechne({}, {}, 0)["ep"] == 0 and rechne({}, {}, 0)["gp"] == 0)
check("Rundung 0,005 → 0,01 (ROUND_HALF_UP)", rechne({"Lohn": "0.005"}, {}, 1)["ep"] == Decimal("0.01"))
for name, args in [("negative Menge", (EK, ZU, -1)), ("negative Einzelkosten", ({"Lohn": -1}, {}, 1)),
                   ("negativer Zuschlag", ({"Lohn": 1}, {"Lohn": {"BGK": -5}}, 1)), ("Text statt Zahl", ({"Lohn": "abc"}, {}, 1))]:
    try:
        rechne(*args)
        check(f"Fehler bei {name}", False)
    except ValueError:
        check(f"Fehler bei {name}", True)
w = what_if(EK, ZU, 12, {"Stoffe": 12})
# Stoffe 30,5 × 1,12 = 34,16; × 1,15 = 39,284; Summe 24,6 + 39,284 + 5,5 = 69,384 → 69,38; Diff EP 4,20; GP 832,56 − 782,16 = 50,40
check("What-if Stoffe +12 %: EP 69,38, Differenz EP 4,20, GP 50,40",
      w["variante"]["ep"] == Decimal("69.38") and w["diff_ep"] == Decimal("4.20") and w["diff_gp"] == Decimal("50.40"),
      f"{w['variante']['ep']} {w['diff_ep']} {w['diff_gp']}")
check("What-if-Rechenweg zeigt die Änderung", any("30,5 € × (1 + 12 / 100) = 34,16 €" in s for s in w["schritte"]),
      str(w["schritte"]))
w2 = what_if(EK, ZU, 12, neue_einzelkosten={"Stoffe": "28"})
check("Alternative: neue Einzelkosten Stoffe 28 € → EP 62,30", w2["variante"]["ep"] == Decimal("62.30"),
      str(w2["variante"]["ep"]))
check("Basis bleibt unverändert", w["basis"]["ep"] == r["ep"] and EK["Stoffe"] == "30,50")
check("Doppellauf gleich (E14)", rechne(EK, ZU, 12) == r and what_if(EK, ZU, 12, {"Stoffe": 12}) == w)
check("dez akzeptiert Komma", dez("12,5") == Decimal("12.5"))
quelle = Path(__file__).with_name("seite_zuschlag.py").read_text(encoding="utf-8")
baum = ast.parse(quelle)
texte = " ".join(n.value for n in ast.walk(baum) if isinstance(n, ast.Constant) and isinstance(n.value, str))
check("keine Preisvorschläge im Text (E9): nur Hinweis „schlägt keine … vor“",
      "Vorschlag" not in texte.replace("Vorschlag `src/pages", "") and "empfohlen" not in texte.lower(), "")
check("keine Vorbelegung außer 0 in der Seite", all(
    not (isinstance(k, ast.keyword) and k.arg == "value" and isinstance(k.value, ast.Constant) and k.value.value != 0.0)
    for k in ast.walk(baum)))
check("Hinweis E9 vorhanden", "schlägt keine Zuschläge oder Preise" in HINWEIS)
check("Streamlit wird beim Import nicht geladen", "streamlit" not in sys.modules)
# Zusätzlicher Test (Team 19:55, B2-F13): Seite im Prozess mit streamlit.testing (kein Port, kein Browser, schreibt
# nichts). Nur, wenn streamlit installiert ist (uv … --with streamlit==1.67.0); sonst als ÜBERSPRUNGEN gemeldet.
try:
    from streamlit.testing.v1 import AppTest
except ImportError:
    print("ÜBERSPRUNGEN AppTest (streamlit nicht installiert)")
else:
    at = AppTest.from_file(str(Path(__file__).with_name("seite_zuschlag.py"))).run(timeout=60)
    check("AppTest: Seite läuft ohne Ausnahme, Startwerte 0,00 €", not at.exception
          and [m.value for m in at.metric] == ["0,00 €", "0,00 €"], str([m.value for m in at.metric]))
    at.number_input[0].set_value(12.0)
    at.number_input[1].set_value(20.0)
    for i, v in ((2, 10.0), (3, 8.0), (4, 5.0)):
        at.number_input[i].set_value(v)
    at.run(timeout=60)
    check("AppTest: Menge 12, Lohn 20 €, Zuschläge 10/8/5 % → EP 24,60 €, GP 295,20 €",
          not at.exception and [m.value for m in at.metric] == ["24,60 €", "295,20 €"], str([m.value for m in at.metric]))
print(f"\n{sum(ergebnisse)}/{len(ergebnisse)} Tests bestanden")
sys.exit(0 if all(ergebnisse) else 1)
