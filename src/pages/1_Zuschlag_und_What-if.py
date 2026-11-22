"""
Seite „Zuschlag und What-if“ (Block B6a, Sitzung B2; eingebunden in der B2-Integration, 21.11.2026).

Die Rechnung und die Seite stehen in src/seite_zuschlag.py (dort getestet, test_seite_zuschlag.py). Diese Datei macht
sie nur als Seite der App sichtbar. Alle Werte sind Eingaben des Kalkulators (E9).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from seite_zuschlag import seite                       # noqa: E402
import ui_stil                                         # noqa: E402

ui_stil.stil_einbinden()
ui_stil.navigation()
seite()
