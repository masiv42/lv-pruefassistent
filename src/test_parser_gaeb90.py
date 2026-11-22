"""
test_parser_gaeb90.py - Tests für den GAEB-90-Zweig von src/lv_parser.py (Block B1p2, Team 21.11.2026; B2-L1, R5).

Zu einer Position gehören nur die Sätze 21–30. Die Erwartungswerte stammen aus der Rohdatei (Sätze in cp850, ohne
parse()); dazu eine erfundene Mini-Datei.
Aufruf aus der Projektwurzel (uv-Befehl siehe AGENTS.md):
  python src/test_parser_gaeb90.py data/raw
Exit-Code 0 = alle Tests bestanden. Schreibt nur in einen Temp-Ordner.
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lv_parser import parse                                        # noqa: E402

D = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/raw")
ergebnisse = []


def check(name, ok, detail=""):
    ergebnisse.append(ok)
    print(f"{'OK    ' if ok else 'FEHLER'} {name}" + (f" – {detail}" if detail and not ok else ""))


def roh(datei):
    return (D / datei).read_text(encoding="cp850").splitlines()


def pos(df, oz):
    p = df[df.typ == "Position"]
    return p[p.oz == oz].iloc[0]


def satz(z, nr, oz_ohne_leer):
    i = next(i for i, l in enumerate(z) if l.startswith("21") and l[2:11].replace(" ", "") == oz_ohne_leer)
    return i, [l for l in z[i:i + 3] if l.startswith("25")]


def main():
    # 1. StBALV23040.D86 06.02.0001: Kurztext = Satz 25 (B2-L1-Fall „… Kalkulationsgrundlage“)
    z = roh("StBALV23040.D86")
    i, s25 = satz(z, 25, "06020001")
    k = s25[0][2:72].strip()
    r = pos(parse(D / "StBALV23040.D86"), "06.02.0001")
    check("StBALV23040.D86 06.02.0001: Kurztext = Satz 25 der Rohdatei", r.kurztext == k == "[PERSON_020]/-in sämtliche Kosten/Zuschläge",
          f"{r.kurztext!r} / {k!r}")
    # 2. 8209.003…D83 01.02.5: Position endet mit Satz 31; folgender Text gehört nicht dazu
    z = roh("8209.003_Leistungsverzeichnis_leer.D83")
    i, _ = satz(z, 25, "01025")
    ende = next(j for j in range(i, len(z)) if z[j][:2] not in {str(n) for n in range(21, 31)})
    danach = " ".join(l[2:72].strip() for l in z[ende:ende + 40] if l[:2] == "26")
    r = pos(parse(D / "8209.003_Leistungsverzeichnis_leer.D83"), "01.02.5")
    check("8209.003…D83 01.02.5: Position endet an Satz 31 (Rohdatei), Text danach nicht im Langtext",
          z[ende][:2] == "31" and "ZUSÄTZLICHE TECHNISCHE VERTRAGSBEDINGUNGEN" in danach
          and "ZUSÄTZLICHE TECHNISCHE VERTRAGSBEDINGUNGEN" not in r.langtext, z[ende][:2])
    eigen = " ".join(l[2:72].strip() for l in z[i:ende] if l[:2] == "26")
    check("8209.003…D83 01.02.5: Langtext = Kurztext + eigene Sätze 26 (Rohdatei)",
          " ".join(r.langtext.split()) == " ".join(eigen.split()) or " ".join(r.langtext.split()).endswith(" ".join(eigen.split())))
    # 3. Erfundene Mini-Datei: Satz 20 (Vorbemerkung) hinter einer Position
    mini = ["00        83                                                                    000001",
            "1101       N    Titel                                                           000002",
            "12Erdarbeiten (erfunden)                                                        000003",
            "210101   1 NNN         00000010000m                                             000004",
            "25Graben ausheben (erfunden)                                                    000005",
            "26   Graben bis 1 m tief ausheben                                               000006",
            "310101                                                                          000007",
            "20                                                                              000008",
            "26   Vorbemerkung: fremder Text (erfunden)                                      000009",
            "210101   2 NNN         00000005000m                                             000010",
            "25Kies einbauen (erfunden)                                                      000011",
            "99                                                                              000012"]
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "mini.D83"
        p.write_text("\r\n".join(mini) + "\r\n", encoding="cp850")
        df = parse(p)
    pp = df[df.typ == "Position"]
    a, b = pp.iloc[0], pp.iloc[1]                      # OZ ohne Maske im Kopfsatz: Reihenfolge der Sätze 21
    check("Mini: Vorbemerkung hinter Satz 31/20 hängt nicht an der vorigen Position",
          "Vorbemerkung" not in a.langtext and a.kurztext == "Graben ausheben (erfunden)", a.langtext)
    check("Mini: nächste Position unverändert gelesen", b.kurztext == "Kies einbauen (erfunden)" and b.menge == 5.0)
    print(f"\n{sum(ergebnisse)}/{len(ergebnisse)} Tests bestanden")
    return 0 if all(ergebnisse) else 1


if __name__ == "__main__":
    sys.exit(main())
