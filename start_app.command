#!/bin/sh
# start_app.command - B8d (Sitzung UI2, Team 22.11.2026): Doppelklick im Finder startet den LV-Prüfassistenten.
# Läuft aus dem Ordner dieser Datei (kein fester Pfad). Ohne .env im Projektordner arbeitet die App mit „KI aus“;
# es wird nichts heruntergeladen außer den festen Bibliotheksversionen über uv (AGENTS.md, E14).
# Die App ist nur auf diesem Rechner erreichbar (localhost), ohne Nutzungsstatistik an Streamlit.
cd "$(dirname "$0")" || exit 1

if ! command -v uv >/dev/null 2>&1; then
    echo "uv ist nicht installiert. Anleitung: https://docs.astral.sh/uv/getting-started/installation/"
    echo "Taste Enter schließt dieses Fenster."
    read -r _
    exit 1
fi

echo "LV-Prüfassistent startet. Der Browser öffnet sich gleich; Beenden mit Ctrl+C oder durch Schließen des Fensters."
exec uv run --no-project --python 3.12 \
    --with streamlit==1.67.0 --with pdfplumber==0.11.11 --with lxml==6.1.3 --with pandas==3.1.1 \
    --with openpyxl==3.1.5 --with anthropic==2.12.0 --with openai==3.57.0 \
    streamlit run src/app.py --server.address localhost --browser.gatherUsageStats false
