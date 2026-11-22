"""
ki_pruefung.py - KI-Gegenprüfung der Funde Nr. 1 und 2 (P4).

Grundsatz (Team, Chat 21.11.2026): Die KI schlägt vor, der Code prüft, der Kalkulator
entscheidet. Die KI löscht, versteckt, verschiebt und ändert keinen Regel-Fund; dieses
Modul liest Funde nur und gibt KI-Vorschläge getrennt zurück. Prüfungen 3–6 bleiben Regeln.

- Zugang: KI_ANBIETER, KI_MODELL und der Key (GROQ_API_KEY bzw. ANTHROPIC_API_KEY) aus .env;
  der Key wird nie ausgegeben, geloggt oder gespeichert. Ohne Key: „KI aus (kein API-Key)“.
  Anbieter-Anbindung: src/ki_client.py.
- Aufruf nur auf Knopfdruck; gesendet werden nur Kurztext, Langtext und die beiden
  Regelwerte der Position. Aufrufe nacheinander, höchstens 50 je Lauf.
- Prüfkette je Antwort: 1. JSON lesbar und vollständig (sonst einmal neu fragen, dann
  „KI-Antwort unlesbar“), 2. beide Zitate wörtlich im Text (Leerraum zusammengefasst),
  3. R7-Begriffe in Begründung und Rückfrage.
- Cache in data/ki_cache/ (Schlüssel: sha256 aus Anbieter, Modell, Denkaufwand, Prompt-Version,
  Systemprompt, Positionstext): echte Modellantworten mit ihrem Status, auch verworfene und
  unlesbare; technische Fehler nicht (Team, 21.11.2026). Tokens und Dauer je Aufruf in
  data/qa/ki_log.jsonl.

Aufruf (aus der Projektwurzel, uv-Befehl siehe README.md):
  python src/ki_pruefung.py data/raw            # alle Funde Nr. 1/2 der lesbaren Dateien
"""
import hashlib
import json
import sys
from datetime import datetime, date
from pathlib import Path

from pruefung_widerspruch import PATTERNS, werte, normalisiere_leerzeichen, beleg_im_text
from bericht import r7_verstoesse
import ki_client
from ki_client import TechnischerFehler, als_client, GroqClient

ROOT = Path(__file__).resolve().parent.parent
ENV_DATEI = ROOT / ".env"
CACHE_DIR = ROOT / "data" / "ki_cache"
LOG_DATEI = ROOT / "data" / "qa" / "ki_log.jsonl"

PROMPT_VERSION = "P4-v2"
# Prüfsumme des eingefrorenen Systemprompts P4-v2 (Team, 21.11.2026: Änderung nur mit neuer Version)
PROMPT_SHA256 = "27bbf1be6ab4f9e20dbf0589254f1b0f01b9e198558942c98467b8d34e42b2c2"
# Nur zum Lesen des Caches, wenn .env fehlt (Demo ohne Internet); Team 21.11.2026: Groq
STANDARD_ANBIETER, STANDARD_MODELL = "groq", "openai/gpt-oss-120b"
EINORDNUNGEN = ["echter Widerspruch", "anderes Bauteil", "Bereichs- oder Mehrfachangabe", "unklar"]
MIT_RUECKFRAGE = {"echter Widerspruch", "unklar"}
FELDER = ["einordnung", "begruendung", "zitat_kurztext", "zitat_langtext", "rueckfrage"]
MAX_AUFRUFE = 50              # je Lauf (Klick)
SDK_WIEDERHOLUNGEN = 3        # Anthropic: SDK wiederholt 429/5xx mit Wartezeit, höchstens 3-mal
# Groq Free Tier, openai/gpt-oss-120b: console.groq.com/docs/rate-limits (abgerufen 21.11.2026);
# maßgeblich ist der Limits-Tab in der Console
GROQ_LIMITS = {"anfragen_min": 30, "anfragen_tag": 1000, "tokens_min": 8000, "tokens_tag": 200_000}
# Preise Claude Sonnet 5.5 in $ pro Mio. Tokens (nur Anbieter anthropic); Quelle: platform.claude.com,
# about-claude/pricing, Stand 21.11.2026. Groq (Free Tier): keine Kosten, die App zeigt Tokens.
PREISE = {"input": 2.0, "output": 10.0, "cache_write": 2.5, "cache_read": 0.10}

STATUS_GUELTIG = "KI-Vorschlag gültig"
STATUS_UNLESBAR = "KI-Antwort unlesbar"
STATUS_ZITAT = "KI-Vorschlag verworfen: Zitat nicht im Original"
STATUS_R7 = "KI-Vorschlag verworfen: R7"
STATUS_ABGELEHNT = "KI-Antwort abgelehnt"
KI_AUS = "KI aus (kein API-Key)"

SYSTEM_PROMPT_V1 = """Du prüfst einzelne Positionen aus Leistungsverzeichnissen (LV) für eine kalkulierende Person eines ausführenden Unternehmens. Eine Regel hat gemeldet, dass Kurztext und Langtext einer Position unterschiedliche Werte nennen: entweder Nennweiten (DN) oder Betonfestigkeitsklassen (z. B. C25/30). Du ordnest ein, was dieser Unterschied wahrscheinlich bedeutet. Du entscheidest nichts; die Entscheidung trifft die kalkulierende Person.

Wähle genau eine Einordnung:
- "echter Widerspruch": Kurztext und Langtext beschreiben denselben Gegenstand mit unterschiedlichen Werten.
- "anderes Bauteil": Der abweichende Wert gehört zu einem anderen Teil der Leistung, zum Beispiel zu einem Anschluss, Formstück, Flansch, Abzweig oder Zubehör, nicht zum Hauptgegenstand der Position.
- "Bereichs- oder Mehrfachangabe": Ein Text nennt einen Bereich oder mehrere zulässige Werte, erkennbar zum Beispiel an "bis", "von ... bis", ">", "<" oder "/", und der andere Wert passt zu diesem Bereich oder dieser Aufzählung.
- "unklar": Der Text reicht nicht aus, um sicher einzuordnen.

Regeln:
1. Zitiere wörtlich. "zitat_kurztext" ist ein zusammenhängender Ausschnitt aus dem Kurztext, "zitat_langtext" ein zusammenhängender Ausschnitt aus dem Langtext, jeweils mit dem betroffenen Wert. Nichts umformulieren, nichts auslassen, keine Auslassungszeichen, keine Anführungszeichen hinzufügen.
2. "begruendung": höchstens zwei Sätze, sachlich, auf Deutsch.
3. "rueckfrage": nur bei "echter Widerspruch" oder "unklar" eine kurze, neutrale Frage des Bieters an den Auftraggeber zur Klärung; bei den anderen Einordnungen ein leerer Text "".
4. Keine Aussagen zu Ansprüchen, Vergütung, Haftung oder Vertragsauslegung. Verwende nicht die Wörter "Anspruch", "berechtigt" und "durchsetzbar" und verweise auf keine Paragraphen.
5. Platzhalter in eckigen Klammern wie [PERSON_...], [NUMMER_...], [FIRMA_...] oder [ORT_...] stammen aus der Anonymisierung. Sie sind keine Fehler und kein Grund für eine Einordnung.
6. Nimm nichts an, was nicht im Text steht.

Antworte ausschließlich mit einem JSON-Objekt ohne weiteren Text, genau mit diesen Feldern:
{"einordnung": "...", "begruendung": "...", "zitat_kurztext": "...", "zitat_langtext": "...", "rueckfrage": "..."}"""

# P4-v2 (Team, 21.11.2026): „anderes Bauteil“ nur bei ausdrücklich benanntem Bauteil, Bauteile in der
# Begründung nennen, im Zweifel „unklar“. Eingefroren: Änderung nur mit neuer Version und neuer Messung.
SYSTEM_PROMPT = """Du prüfst einzelne Positionen aus Leistungsverzeichnissen (LV) für eine kalkulierende Person eines ausführenden Unternehmens. Eine Regel hat gemeldet, dass Kurztext und Langtext einer Position unterschiedliche Werte nennen: entweder Nennweiten (DN) oder Betonfestigkeitsklassen (z. B. C25/30). Du ordnest ein, was dieser Unterschied wahrscheinlich bedeutet. Du entscheidest nichts; die Entscheidung trifft die kalkulierende Person.

Wähle genau eine Einordnung:
- "echter Widerspruch": Kurztext und Langtext beschreiben denselben Gegenstand mit unterschiedlichen Werten.
- "anderes Bauteil": nur, wenn der abweichende Wert im Text ausdrücklich einem anderen, benannten Bauteil zugeordnet ist, zum Beispiel "Anschlussflansch DN 100". Zubehör ohne eigenen Wert, zum Beispiel "mit Steckmuffe" oder "inkl. Dichtung", macht den Wert nicht zu einem anderen Bauteil.
- "Bereichs- oder Mehrfachangabe": Ein Text nennt einen Bereich oder mehrere zulässige Werte, erkennbar zum Beispiel an "bis", "von ... bis", ">", "<" oder "/", und der andere Wert passt zu diesem Bereich oder dieser Aufzählung.
- "unklar": Der Text reicht nicht aus, um sicher einzuordnen.

Im Zweifel wähle "unklar", niemals "anderes Bauteil" raten. Grund: Wird ein echter Fehler als "anderes Bauteil" eingeordnet, verwirft die kalkulierende Person ihn womöglich; das ist für sie teurer als eine Rückfrage.

Regeln:
1. Zitiere wörtlich. "zitat_kurztext" ist ein zusammenhängender Ausschnitt aus dem Kurztext, "zitat_langtext" ein zusammenhängender Ausschnitt aus dem Langtext, jeweils mit dem betroffenen Wert. Nichts umformulieren, nichts auslassen, keine Auslassungszeichen, keine Anführungszeichen hinzufügen.
2. "begruendung": höchstens zwei Sätze, sachlich, auf Deutsch. Nenne darin, zu welchem Bauteil jeder der beiden Werte gehört.
3. "rueckfrage": nur bei "echter Widerspruch" oder "unklar" eine kurze, neutrale Frage des Bieters an den Auftraggeber zur Klärung; bei den anderen Einordnungen ein leerer Text "".
4. Keine Aussagen zu Ansprüchen, Vergütung, Haftung oder Vertragsauslegung. Verwende nicht die Wörter "Anspruch", "berechtigt" und "durchsetzbar" und verweise auf keine Paragraphen.
5. Platzhalter in eckigen Klammern wie [PERSON_...], [NUMMER_...], [FIRMA_...] oder [ORT_...] stammen aus der Anonymisierung. Sie sind keine Fehler und kein Grund für eine Einordnung.
6. Nimm nichts an, was nicht im Text steht.

Antworte ausschließlich mit einem JSON-Objekt ohne weiteren Text, genau mit diesen Feldern:
{"einordnung": "...", "begruendung": "...", "zitat_kurztext": "...", "zitat_langtext": "...", "rueckfrage": "..."}"""

PRUEFUNG_NAME = {1: "Nennweite (DN)", 2: "Betonfestigkeitsklasse"}


# --------------------------------------------------------------------------- Zugang

class KiKonfig:
    """Anbieter, Modell und Key aus .env. Der Key erscheint in keiner Ausgabe (repr/str)."""

    def __init__(self, modell=None, key=None, anbieter="anthropic"):
        self.modell = modell
        self.anbieter = anbieter
        self._key = key

    @property
    def aktiv(self):
        return bool(self._key)

    def __repr__(self):
        return f"KiKonfig(anbieter={self.anbieter!r}, modell={self.modell!r}, key={'gesetzt' if self._key else 'fehlt'})"

    __str__ = __repr__

    def client(self, reasoning_effort=None):
        """SDK-Client des Anbieters (der Key bleibt im Client)."""
        if self.anbieter == "groq":
            return GroqClient(key=self._key, reasoning_effort=reasoning_effort)
        import anthropic
        return anthropic.Anthropic(api_key=self._key, max_retries=SDK_WIEDERHOLUNGEN)


def lade_konfig(pfad=ENV_DATEI):
    """Liest KI_ANBIETER, KI_MODELL und den passenden Key aus der .env (Zeilen KEY=WERT)."""
    env = {}
    if Path(pfad).exists():
        for zeile in Path(pfad).read_text(encoding="utf-8").splitlines():
            zeile = zeile.strip()
            if not zeile or zeile.startswith("#") or "=" not in zeile:
                continue
            k, v = zeile.split("=", 1)
            env[k.strip().removeprefix("export ").strip().upper()] = v.strip().strip('"').strip("'")  # KI_Anbieter = KI_ANBIETER
    anbieter = (env.get("KI_ANBIETER") or ("anthropic" if env.get("ANTHROPIC_API_KEY") else STANDARD_ANBIETER)).lower()
    key = env.get("GROQ_API_KEY") if anbieter == "groq" else env.get("ANTHROPIC_API_KEY")
    return KiKonfig(env.get("KI_MODELL") or None, key or None, anbieter)


def cache_ziel(konfig):
    """(Anbieter, Modell) für den Cache-Schlüssel; ohne .env die vom Team festgelegten Werte."""
    if konfig.modell:
        return konfig.anbieter, konfig.modell
    return STANDARD_ANBIETER, STANDARD_MODELL


def ki_status(konfig):
    return (f"KI an: {konfig.anbieter} / {konfig.modell}, Prompt {PROMPT_VERSION}"
            if konfig.aktiv and konfig.modell else KI_AUS)


# --------------------------------------------------------------------------- Anfrage

def regelwerte(f, kurz, lang):
    """Die beiden Regelwerte wie in Prüfung Nr. 1/2 (Kurztext-Anfang im Langtext abgeschnitten)."""
    pat = PATTERNS[f["pruefung"]]
    rest = lang[len(kurz):] if lang.startswith(kurz) else lang
    return sorted(werte(pat, kurz)), sorted(werte(pat, rest))


def positionstext(f, texte):
    """Inhalt der Nutzernachricht: nur Kurztext, Langtext und die Regelwerte der Position."""
    t = texte[f["id"]][0]
    kurz, lang = t["kurztext"], t["langtext"]
    wk, wl = regelwerte(f, kurz, lang)
    return (f"Prüfung: {PRUEFUNG_NAME[f['pruefung']]}\n"
            f"Regelwerte: Kurztext nennt {', '.join(wk)}; Langtext nennt {', '.join(wl)}\n\n"
            f"Kurztext:\n<<<\n{normalisiere_leerzeichen(kurz)}\n>>>\n\n"
            f"Langtext:\n<<<\n{normalisiere_leerzeichen(lang)}\n>>>")


def prompt_eingefroren():
    """True, wenn der Systemprompt zur eingefrorenen Version passt."""
    return hashlib.sha256(SYSTEM_PROMPT.encode("utf-8")).hexdigest() == PROMPT_SHA256


def denkaufwand(anbieter):
    return ki_client.GROQ_REASONING if anbieter == "groq" else ki_client.ANTHROPIC_EFFORT


def cache_schluessel(anbieter, modell, text):
    roh = json.dumps([anbieter, modell, denkaufwand(anbieter), PROMPT_VERSION, SYSTEM_PROMPT, text],
                     ensure_ascii=False)
    return hashlib.sha256(roh.encode("utf-8")).hexdigest()


def kosten(usage, anbieter="anthropic"):
    """Geschätzte Kosten in $ (nur Anthropic; Groq Free Tier: 0)."""
    if anbieter != "anthropic":
        return 0.0
    return (usage["input_tokens"] * PREISE["input"] + usage["output_tokens"] * PREISE["output"]
            + usage["cache_creation_input_tokens"] * PREISE["cache_write"]
            + usage["cache_read_input_tokens"] * PREISE["cache_read"]) / 1_000_000


# --------------------------------------------------------------------------- Prüfkette

def lies_json(text):
    """Schritt 1: JSON lesbar und vollständig? Gibt dict oder None zurück."""
    s = (text or "").strip()
    a, e = s.find("{"), s.rfind("}")
    if a < 0 or e < a:
        return None
    try:
        d = json.loads(s[a:e + 1])
    except json.JSONDecodeError:
        return None
    if not isinstance(d, dict) or any(not isinstance(d.get(k), str) for k in FELDER):
        return None
    if d["einordnung"] not in EINORDNUNGEN or not d["begruendung"].strip():
        return None
    if d["einordnung"] not in MIT_RUECKFRAGE and d["rueckfrage"].strip():
        return None
    return {k: d[k] for k in FELDER}


def bewerte(antworttext, kurz, lang, stop_reason=None):
    """Prüfkette 1–3 für eine Antwort. Gibt (status, vorschlag oder None) zurück."""
    if stop_reason == "refusal":
        return STATUS_ABGELEHNT, None
    d = lies_json(antworttext)
    if d is None:
        return STATUS_UNLESBAR, None
    if not (beleg_im_text(d["zitat_kurztext"], kurz) and beleg_im_text(d["zitat_langtext"], lang)):
        return STATUS_ZITAT, d
    if r7_verstoesse([d["begruendung"], d["rueckfrage"]]):
        return STATUS_R7, d
    return STATUS_GUELTIG, d


def ergebnis(status, d, modell, quelle, anbieter=None):
    """KI-Ergebnis je Fund. Inhalt nur, wenn gültig; sonst nur der Status."""
    gueltig = status == STATUS_GUELTIG
    return {
        "status": status,
        "einordnung": d["einordnung"] if gueltig else "",
        "begruendung": d["begruendung"] if gueltig else "",
        "rueckfrage": d["rueckfrage"] if gueltig else "",
        "zitat_kurztext": d["zitat_kurztext"] if gueltig else "",
        "zitat_langtext": d["zitat_langtext"] if gueltig else "",
        "zitat_status": ("beide Zitate im Text gefunden" if gueltig
                         else "Zitat nicht im Text" if status == STATUS_ZITAT
                         else "–"),
        "anbieter": anbieter,
        "modell": modell,
        "prompt_version": PROMPT_VERSION,
        "quelle": quelle,                       # "Cache" oder "API"
        "verworfen_vorschlag": d if status in (STATUS_ZITAT, STATUS_R7) else None,   # nur für den Bericht
    }


# --------------------------------------------------------------------------- Cache, Log

def _cache_pfad(schluessel, cache_dir):
    return Path(cache_dir) / f"{schluessel}.json"


def lies_cache(schluessel, cache_dir=CACHE_DIR):
    p = _cache_pfad(schluessel, cache_dir)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def schreibe_cache(schluessel, eintrag, cache_dir=CACHE_DIR):
    Path(cache_dir).mkdir(parents=True, exist_ok=True)
    _cache_pfad(schluessel, cache_dir).write_text(json.dumps(eintrag, ensure_ascii=False, indent=2) + "\n",
                                                  encoding="utf-8")


def schreibe_log(zeile, log_datei=LOG_DATEI):
    Path(log_datei).parent.mkdir(parents=True, exist_ok=True)
    with open(log_datei, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(zeile, ensure_ascii=False) + "\n")


def verbrauch_heute(anbieter="groq", log_datei=LOG_DATEI, heute=None):
    """Heute verbrauchte Tokens und Anfragen laut Log (lokales Datum)."""
    heute = (heute or date.today()).isoformat()
    tokens = anfragen = 0
    p = Path(log_datei)
    if p.exists():
        for z in p.read_text(encoding="utf-8").splitlines():
            e = json.loads(z)
            if e.get("anbieter") == anbieter and str(e.get("zeit", "")).startswith(heute) and e.get("usage"):
                tokens += e["usage"]["input_tokens"] + e["usage"]["output_tokens"]
                anfragen += 1
    return tokens, anfragen


def ki_funde(funde):
    """Nur Funde Nr. 1 und 2 werden gegengeprüft."""
    return [f for f in funde if f["pruefung"] in (1, 2)]


def aus_cache(funde, texte, konfig, cache_dir=CACHE_DIR):
    """KI-Ergebnisse, die schon im Cache liegen (kein API-Aufruf). Prüfkette läuft neu."""
    anbieter, modell = cache_ziel(konfig)
    erg = {}
    for f in ki_funde(funde):
        c = lies_cache(cache_schluessel(anbieter, modell, positionstext(f, texte)), cache_dir)
        if c is None:
            continue
        t = texte[f["id"]][0]
        status, d = bewerte(c["antwort_text"], t["kurztext"], t["langtext"], c.get("stop_reason"))
        erg[f["id"]] = ergebnis(status, d, c.get("modell_antwort") or modell, "Cache", anbieter)
    return erg


def gegenpruefung(funde, texte, konfig, client=None, max_aufrufe=MAX_AUFRUFE,
                  cache_dir=CACHE_DIR, log_datei=LOG_DATEI, fortschritt=None):
    """KI-Gegenprüfung für alle Funde Nr. 1/2, nacheinander. Regel-Funde bleiben unverändert.
    `fortschritt(i, n, fund_id, text)` meldet „Fund i von n“ und Wartezeiten.
    Gibt (ergebnisse je Fund-ID, statistik) zurück."""
    stat = {"anbieter": konfig.anbieter, "modell": konfig.modell, "aufrufe": 0, "cache_treffer": 0,
            "input_tokens": 0, "output_tokens": 0, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0,
            "kosten_usd": 0.0, "dauer_s": 0.0, "wartezeit_s": 0.0, "technische_fehler": [],
            "nicht_geprueft": 0, "meldung": ""}
    erg = {}
    if not konfig.aktiv or not konfig.modell:
        stat["meldung"] = KI_AUS
        return erg, stat
    if not prompt_eingefroren():
        raise RuntimeError(f"Systemprompt weicht von {PROMPT_VERSION} ab: neue Version und neue Messung nötig")
    ki = als_client(client if client is not None else konfig.client(), konfig.anbieter)
    liste = ki_funde(funde)
    abbruch = None
    for i, f in enumerate(liste, start=1):
        if abbruch:
            stat["nicht_geprueft"] += 1
            continue
        if fortschritt:
            fortschritt(i, len(liste), f["id"], "läuft")
        text = positionstext(f, texte)
        schluessel = cache_schluessel(konfig.anbieter, konfig.modell, text)
        t = texte[f["id"]][0]
        c = lies_cache(schluessel, cache_dir)
        if c is not None:
            stat["cache_treffer"] += 1
            status, d = bewerte(c["antwort_text"], t["kurztext"], t["langtext"], c.get("stop_reason"))
            erg[f["id"]] = ergebnis(status, d, c.get("modell_antwort") or konfig.modell, "Cache", konfig.anbieter)
            continue
        status, d, antwort, versuch = None, None, None, 0
        while versuch < 2:                                  # einmal neu fragen bei unlesbarer Antwort
            if stat["aufrufe"] >= max_aufrufe:
                abbruch = f"höchstens {max_aufrufe} API-Aufrufe je Lauf"
                break
            versuch += 1
            stat["aufrufe"] += 1
            warte = (lambda s, i=i: fortschritt(i, len(liste), f["id"], f"warte {s:.0f} s (Limit)")) if fortschritt else None
            zeit = datetime.now().astimezone().isoformat(timespec="seconds")
            try:
                antwort = ki.anfrage(konfig.modell, SYSTEM_PROMPT, text, EINORDNUNGEN, warte)
            except TechnischerFehler as e:
                stat["technische_fehler"].append(f"{f['id']}: {e.art}")
                stat["wartezeit_s"] += e.wartezeit_s
                schreibe_log({"zeit": zeit, "fund_id": f["id"], "anbieter": konfig.anbieter, "modell": konfig.modell,
                              "prompt_version": PROMPT_VERSION, "versuch": versuch, "usage": None,
                              "wartezeit_s": round(e.wartezeit_s, 1), "ergebnis": f"technischer Fehler: {e.art}"},
                             log_datei)
                if e.art.startswith("429"):
                    abbruch = f"Limit erreicht ({e.art})"
                antwort, status = None, None
                break
            for k, v in antwort.usage.items():
                stat[k] += v
            stat["kosten_usd"] += kosten(antwort.usage, konfig.anbieter)
            stat["dauer_s"] += antwort.dauer_s
            stat["wartezeit_s"] += antwort.wartezeit_s
            status, d = bewerte(antwort.text, t["kurztext"], t["langtext"], antwort.stop_reason)
            schreibe_log({"zeit": zeit, "fund_id": f["id"], "anbieter": konfig.anbieter, "modell": konfig.modell,
                          "modell_antwort": antwort.modell, "prompt_version": PROMPT_VERSION, "versuch": versuch,
                          "stop_reason": antwort.stop_reason, "usage": antwort.usage,
                          "dauer_s": round(antwort.dauer_s, 2), "wartezeit_s": round(antwort.wartezeit_s, 1),
                          "kosten_usd": round(kosten(antwort.usage, konfig.anbieter), 6), "ergebnis": status},
                         log_datei)
            if status != STATUS_UNLESBAR:
                break
        if antwort is None or status is None or (status == STATUS_UNLESBAR and versuch < 2):
            stat["nicht_geprueft"] += 1                     # kein Modell-Ergebnis: nicht cachen
            continue
        schreibe_cache(schluessel, {"fund_id": f["id"], "anbieter": konfig.anbieter, "modell": konfig.modell,
                                    "modell_antwort": antwort.modell, "prompt_version": PROMPT_VERSION,
                                    "positionstext": text, "antwort_text": antwort.text,
                                    "stop_reason": antwort.stop_reason, "status": status,
                                    "erstellt": datetime.now().astimezone().isoformat(timespec="seconds")},
                       cache_dir)
        erg[f["id"]] = ergebnis(status, d, antwort.modell, "API", konfig.anbieter)
    if stat["nicht_geprueft"]:
        grund = abbruch or "technische Fehler"
        stat["meldung"] = f"Abbruch bzw. Lücke: {grund}; {stat['nicht_geprueft']} Funde nicht geprüft (nächster Klick versucht sie neu)."
    return erg, stat


# --------------------------------------------------------------------------- Messung (B9)

GOLD_DATEI = ROOT / "data" / "qa" / "ki_goldstandard.json"
GROB = {"echter Widerspruch": "echt", "anderes Bauteil": "Fehlalarm", "Bereichs- oder Mehrfachangabe": "Fehlalarm",
        "unklar": "unklar"}
# Zusatzfälle (Team, 21.11.2026): die 3 bestätigten Fehlalarme, die der DN-Filter schon aussortiert
ZUSATZ_DATEI = "501-24-01_GAEB-XML_sas.x83"
ZUSATZ_OZ = ("2.5.5", "2.5.7", "2.5.9")
ZUSATZ_TITEL = "Zusatzfälle, vom DN-Filter bereits aussortiert"


def zusatzfaelle(rohdaten=ROOT / "data" / "raw"):
    """Die 3 Fehlalarme 501-24-01 02.05.0005/0007/0009 so, wie Prüfung Nr. 1 sie ohne DN-Filter melden
    würde (Kurztext und Langtext nennen DN-Werte, kein Wert stimmt überein). Nur für die Messung;
    die App zeigt sie nicht. Gibt (funde, texte) zurück."""
    from lv_parser import parse
    from pruefung_widerspruch import normalisiere_oz
    df = parse(Path(rohdaten) / ZUSATZ_DATEI)
    funde, texte = [], {}
    for row in df[df.typ == "Position"].itertuples():
        oz = normalisiere_oz(row.oz)
        if oz not in ZUSATZ_OZ:
            continue
        kurz = row.kurztext if isinstance(row.kurztext, str) else ""
        lang = row.langtext if isinstance(row.langtext, str) else ""
        rest = lang[len(kurz):] if lang.startswith(kurz) else lang
        k, l = werte(PATTERNS[1], kurz), werte(PATTERNS[1], rest)
        if not (k and l) or (k & l):
            continue
        fid = f"1|{row.datei}|{oz}"
        funde.append({"id": fid, "pruefung": 1, "positionen": [{"datei": row.datei, "oz": row.oz, "seite": None}]})
        texte[fid] = [{"oz": row.oz, "kurztext": kurz, "langtext": lang}]
    return funde, texte


def messung(ergebnisse, gold_datei=GOLD_DATEI):
    """Zeilen KI gegen Goldstandard: Einträge mit zaehlt=true und strittige Einträge.
    gruppe: „regel“ (Regel-Fund), „zusatz“ (kein Regel-Fund, ZUSATZ_TITEL), „strittig“ (getrennt,
    nicht in der Trefferquote)."""
    gold = json.loads(Path(gold_datei).read_text(encoding="utf-8"))
    zeilen = []
    for g in gold["eintraege"]:
        strittig = bool(g.get("strittig"))
        if not (g.get("zaehlt") or strittig):
            continue
        k = ergebnisse.get(g["fund_id"])
        if k is None:
            urteil, ki = "nicht geprüft", "–"
        elif k["status"] != STATUS_GUELTIG:
            urteil, ki = "verworfen", k["status"]
        else:
            ki = k["einordnung"]
            urteil = "Treffer" if ki == g["einordnung"] else "Abweichung"
        if strittig:
            einordnungen = g.get("einordnungen") or [{"einordnung": g["einordnung"], "quelle": g["quelle"]},
                                                     {"einordnung": g["einordnung_person_b"],
                                                      "quelle": g["quelle_person_b"]}]
            gold_text = " / ".join(e["einordnung"] for e in einordnungen)
            urteil = "strittig" if urteil in ("Treffer", "Abweichung") else urteil
        else:
            gold_text = g["einordnung"]
        gruppe = "strittig" if strittig else ("regel" if g.get("regel_fund", True) else "zusatz")
        zeilen.append({"fund_id": g["fund_id"], "gold": gold_text, "ki": ki, "urteil": urteil, "gruppe": gruppe})
    return zeilen


def _klasse(z, grob):
    """KI-Spalte der Matrix: Einordnung (fein oder grob) bzw. „verworfen“ / „nicht geprüft“."""
    if z["urteil"] in ("verworfen", "nicht geprüft"):
        return z["urteil"]
    return GROB[z["ki"]] if grob else z["ki"]


def matrix(zeilen, grob=False):
    """Zählmatrix Goldstandard (Zeile) × KI (Spalte). Treffer: gleiche Klasse.
    grob: nur „echt“ gegen „Fehlalarm“ (anderes Bauteil + Bereichsangabe); „unklar“ im Goldstandard
    oder bei der KI steht getrennt und zählt weder als Treffer noch als Abweichung.
    fein: alle 4 Klassen, „unklar“ ist eine Klasse. Verworfene und nicht geprüfte stehen immer getrennt."""
    m = {}
    for z in zeilen:
        g = GROB[z["gold"]] if grob else z["gold"]
        k = _klasse(z, grob)
        m.setdefault(g, {}).setdefault(k, 0)
        m[g][k] += 1

    def bewertbar(z):
        k = _klasse(z, grob)
        return k not in ("verworfen", "nicht geprüft") and not (grob and "unklar" in (k, GROB[z["gold"]]))
    bewertet = [z for z in zeilen if bewertbar(z)]
    treffer = sum((GROB[z["gold"]] if grob else z["gold"]) == _klasse(z, grob) for z in bewertet)
    return {"matrix": m, "treffer": treffer, "bewertet": len(bewertet), "gesamt": len(zeilen),
            "ki_unklar": sum(z["urteil"] not in ("verworfen", "nicht geprüft") and z["ki"] == "unklar" for z in zeilen),
            "gold_unklar": sum(z["gold"] == "unklar" for z in zeilen),
            "verworfen": sum(z["urteil"] == "verworfen" for z in zeilen),
            "nicht_geprueft": sum(z["urteil"] == "nicht geprüft" for z in zeilen)}


def je_position(zeilen, schluessel):
    """Dedupliziert: eine Zeile je Position (schluessel: fund_id → Positionsschlüssel). Uneinheitliche
    KI-Ergebnisse derselben Position werden als „uneinheitlich“ gemeldet, nicht gezählt."""
    gr = {}
    for z in zeilen:
        gr.setdefault((z["gruppe"], schluessel.get(z["fund_id"], z["fund_id"])), []).append(z)
    aus, uneinheitlich = [], []
    for (gruppe, pos), zs in sorted(gr.items(), key=lambda kv: str(kv[0])):
        if len({(z["gold"], z["ki"], z["urteil"]) for z in zs}) == 1:
            aus.append(dict(zs[0], fund_id=zs[0]["fund_id"], anzahl=len(zs)))
        else:
            uneinheitlich.append({"position": str(pos), "zeilen": zs})
    return aus, uneinheitlich


def auswertung(zeilen, schluessel):
    """Messtabellen (Schritt 4): je Gruppe „regel“ und „zusatz“ grob (echt / Fehlalarm) und fein (4 Klassen),
    je Fund und dedupliziert je Position; strittige Positionen getrennt."""
    aus = {"strittig": [z for z in zeilen if z["gruppe"] == "strittig"]}
    for gruppe in ("regel", "zusatz"):
        zs = [z for z in zeilen if z["gruppe"] == gruppe]
        pos, uneinheitlich = je_position(zs, schluessel)
        aus[gruppe] = {"je_fund": {"grob": matrix(zs, grob=True), "fein": matrix(zs)},
                       "je_position": {"grob": matrix(pos, grob=True), "fein": matrix(pos)},
                       "positionen": len(pos) + len(uneinheitlich), "uneinheitlich": uneinheitlich}
    return aus


if __name__ == "__main__":
    from bericht import pruefe_lv
    from pruefung_widerspruch import normalisiere_oz
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    d = Path(args[0]) if args else ROOT / "data" / "raw"
    ausgabe = next((Path(a.split("=", 1)[1]) for a in sys.argv[1:] if a.startswith("--ausgabe=")),
                   ROOT / "data" / "qa" / "ki_messung.json")
    konfig = lade_konfig()
    print(ki_status(konfig))
    alle_funde, alle_texte = [], {}
    for p in sorted(d.iterdir()):
        try:
            funde, texte, _ = pruefe_lv(p)
        except ValueError:
            continue
        alle_funde += ki_funde(funde)
        alle_texte.update(texte)
    fp = lambda i, n, fid, t: print(f"  Fund {i} von {n}: {fid} – {t}", flush=True)
    print(f"Funde Nr. 1/2: {len(alle_funde)}")
    erg, stat = gegenpruefung(alle_funde, alle_texte, konfig, fortschritt=fp)
    print("Regel-Funde:", json.dumps(stat, ensure_ascii=False))
    z_funde, z_texte = zusatzfaelle(d)                  # getrennter Messaufruf, nicht in der App
    print(f"{ZUSATZ_TITEL}: {len(z_funde)}")
    z_erg, z_stat = gegenpruefung(z_funde, z_texte, konfig, fortschritt=fp)
    print("Zusatzfälle:", json.dumps(z_stat, ensure_ascii=False))
    texte_alle = {**alle_texte, **z_texte}
    schluessel = {}
    for f in alle_funde + z_funde:
        t = texte_alle[f["id"]][0]
        wk, wl = regelwerte(f, t["kurztext"], t["langtext"])
        schluessel[f["id"]] = f"{normalisiere_oz(f['positionen'][0]['oz'])} {'/'.join(wk)} | {'/'.join(wl)}"
    zeilen = messung({**erg, **z_erg})
    doc = {"zeit": datetime.now().astimezone().isoformat(timespec="seconds"), "anbieter": konfig.anbieter,
           "modell": konfig.modell, "prompt_version": PROMPT_VERSION, "denkaufwand": denkaufwand(konfig.anbieter),
           "statistik": {"regel": stat, "zusatz": z_stat}, "zeilen": zeilen,
           "auswertung": auswertung(zeilen, schluessel), "positionen": schluessel,
           "ergebnisse": {fid: dict(k, gruppe="zusatz" if fid in z_erg else "regel")
                          for fid, k in {**erg, **z_erg}.items()}}
    ausgabe.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Messung: {ausgabe}")
    for z in zeilen:
        print(" ", z)
