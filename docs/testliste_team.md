# Testliste für das Team – echte Dateien in der App (Port 8501)

Stand: 21.11.2026, 23:05, main nach der B2-Integration. Geschrieben von Sitzung B1, weil die Testliste von Sitzung B2
nicht im Repo lag. Der Agenten-Browser kann die echten PDFs (rund 400 KB) nicht hochladen; diese Prüfung macht das
Team. Jeder gemeldete Fehler wird als Fehlschlag (docs/fehlschlaege.md) mit Ursache eingetragen und behoben.

**Bitte melden:** Datei, Schritt, was zu sehen war (Bildschirmfoto oder Text), was erwartet war.

## A. Grundablauf (je eine Datei pro Format)

| Nr | Datei (aus data/raw, nur hochladen, nicht speichern) | Prüfen |
|---|---|---|
| A1 | LV_00_Roh_und_Erdauarbeiten.pdf (PDF) | Kopfzeile: 269 Positionen, 132 Funde; „Rechenprüfung: 0 Positionen nachgerechnet, 0 Abweichungen“; Stufe 1 offen, Stufen 2–4 aufklappbar mit Anzahl |
| A2 | 8209.003_Leistungsverzeichnis_leer.X83 (GAEB XML) | Funde Nr. 1 zu 05.01.4 und 05.01.46 in Stufe 1; Detailansicht mit Belegen aus Kurz- und Langtext |
| A3 | StBALV23040.D86 (GAEB 90, Auftrags-LV) | Hinweis „Auftrags-LV (Austauschphase 86)“; „Rechenprüfung: 249 Positionen nachgerechnet, 0 Abweichungen“; Bieterfragen-Datei enthält „Auftrags-LV – keine Bieterfragen“ |
| A4 | Angebot AN24-0305.D84 (reine Preisdatei) | Hinweis „Datei enthält nur Preise …“; „Rechenprüfung: 274 Positionen nachgerechnet, 0 Abweichungen“; kein Absturz |
| A5 | Angebot AN24-0305.pdf | Prüfabdeckung „Nr. 1, 2, 16 prüfbar in 0 von 274 …“ (das Angebot druckt nur Kurztexte) |
| A6 | eine eigene Excel-Datei (falls vorhanden) | Hinweis „ohne Orga-Beispiel getestet“; Spalten-Zuordnung; ohne OZ/Kurztext klare Meldung |

## B. Funktionen

| Nr | Schritt | Erwartung |
|---|---|---|
| B1 | Fund bestätigen, verwerfen, „Rückfrage stellen“, zurück auf offen | Status wechselt; „Status wird gespeichert in: Projektablage (data/findings)“ |
| B2 | Risikobericht herunterladen, in Excel/Numbers öffnen (**nicht nach data/raw speichern**) | Blätter Übersicht, Funde, Legende, Nachtrag und Streitpunkte, KI-Vorschläge; Überschriften lesbar; Spalten Nr., Stufe (Text), Prüfer, Menge/Einheit/EP/GP |
| B3 | Bieterfragen (Entwurf) herunterladen | nur Funde mit Empfehlung „Rückfrage“; Hinweis „Entwurf … vor dem Versand prüfen“ |
| B4 | Seite „Uebersicht“ in der Seitenleiste | Funde je Stufe, „Zuerst ansehen“, Diagramm, Downloads |
| B5 | Seite „Zuschlag und What-if“ | alle Eingaben 0; eigene Werte ergeben EP/GP mit Rechenweg |
| B6 | Detailansicht → „Vergleichspreise“ aufklappen (z. B. Leistungsverzeichnis.pdf, „Buschwerk entfernen …“) | Treffer mit Quelle (Datei, OZ, EP), keine Bewertung |
| B7 | KI-Gegenprüfung (nur auf Knopfdruck, Nr. 1/2) | „KI-Hinweis im Detail“ bzw. „KI-Vorschlag …“; Stufe und Reihenfolge ändern sich nicht |
| B8 | Demo-LV `demo/Demo-LV_B7_[PROJEKT_004].X83` | je Prüfung Nr. 1–19 ein Fund (Fälle in `demo/demo_faelle.json`); KI-Vorschläge aus dem Cache |

## C. Bekannte Grenzen (kein Fehler, nicht melden)

- LV-Positionen.docx wird nicht gelesen.
- Spezifikationen und Vorbemerkungen außerhalb von Positionen werden nicht geprüft (L55, seit B1p2/B1p3 in allen Formaten gleich).
- Die Übersichtsseite zeigt „Positionswert laut LV (Summe GP) – kein Risikobetrag“ (bitte trotzdem bewerten, E9/R11).
