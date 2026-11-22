# Bericht B1p2 – Parser GAEB 90: Langtext nur aus dem Text der Position (B2-L1)

Stand: 21.11.2026, Branch arbeit/B1p2 (Zeitrahmen 45 min eingehalten).

**Kern-Check:** Punkte 1–6 eingehalten (Rollenkette kompakt: Scope nur GAEB-90-Zweig; Auditor: jede Fundänderung erklärt;
Kalkulator: „fremde Vorbemerkungen dürfen nicht als Beleg einer Position erscheinen“).

## Ergebnis

- Regel: Zu einer Position gehören die Sätze 21–30; jeder andere Satz beendet sie (`POSITIONSSAETZE`).
- Parser vorher/nachher (nur GAEB 90): OZ, Menge, Einheit, EP, GP unverändert; Langtexte gekürzt in
  8209.003…D83 13, Angebot AN24-0305.D84 15, StBALV23040.D86 31 (+1 Kurztext), [ORT_024] LV24069.D86 13 Positionen.
- Funde: 1.688 unverändert; geändert nur der Beleg von 13|StBALV23040.D86|6.2.1:
  „[PERSON_020]/-in sämtliche Kosten/Zuschläge Kalkulationsgrundlage“ → „… Kosten/Zuschläge“.
  Die B2-Module zitierten schon vorher nur aus dem eigenen Block (Gaeb90Bloecke).
- Skeptiker am Original: StBALV23040.D86 Satz 25 von 06.02.0001 = neuer Beleg; 8209.003…D83 01.02.5 endet mit Satz 31
  (Z. 619), danach Bereich 01.03 und „ZUSÄTZLICHE TECHNISCHE VERTRAGSBEDINGUNGEN …“ (nicht mehr im Langtext).
- Tests: neu src/test_parser_gaeb90.py 5/5 (Rohdatei-Erwartungen, erfundene Mini-Datei). Übrige Reihen, Doppellauf,
  Durchlauf: docs/uebergabe.md.
- Offen: das PDF-Gegenstück „Text hinter der Mengenzeile“ (FS2, F2).
