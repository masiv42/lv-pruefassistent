"""
test_ki_client.py - Tests für den Groq-Zweig der KI-Gegenprüfung (src/ki_client.py, P4) ohne API.

Ein Fake ersetzt das openai-SDK (OpenAI-kompatibler Groq-Endpunkt). Kein echter Key.
Aufruf aus der Projektwurzel (uv-Befehl siehe README.md):
  python src/test_ki_client.py
"""
import json
import sys
import tempfile
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import httpx2
import openai

import ki_client as C
import ki_pruefung as K

PLATZHALTER = "nur-ein-platzhalter-kein-key"
MODELL = "openai/gpt-oss-120b"
URL = "https://api.groq.com/openai/v1/chat/completions"
ergebnisse = []


def check(name, ok, detail=""):
    ergebnisse.append(ok)
    print(f"{'OK    ' if ok else 'FEHLER'} {name}" + (f" – {detail}" if detail and not ok else ""))


def fehler_429(retry_after="1"):
    r = httpx2.Response(429, headers={"retry-after": retry_after}, request=httpx2.Request("POST", URL))
    return openai.RateLimitError("rate limit", response=r, body=None)


def antwort_json(einordnung="echter Widerspruch", zk="Rohr DN 125", zl="Rohr DN 100", frage="Welche Nennweite gilt?"):
    return json.dumps({"einordnung": einordnung, "begruendung": "Werte widersprechen sich.",
                       "zitat_kurztext": zk, "zitat_langtext": zl, "rueckfrage": frage}, ensure_ascii=False)


class FakeOpenAI:
    """Wie openai.OpenAI: .chat.completions.create(**kw) und .models.list()."""

    def __init__(self, folge):
        self.folge = list(folge)          # Strings (Antworttext), (Text, finish_reason) oder Exceptions
        self.aufrufe = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))
        self.models = SimpleNamespace(list=lambda: SimpleNamespace(data=[SimpleNamespace(id=MODELL)]))

    def _create(self, **kw):
        self.aufrufe.append(kw)
        x = self.folge.pop(0)
        if isinstance(x, Exception):
            raise x
        text, fin = (x, "stop") if isinstance(x, str) else x
        return SimpleNamespace(
            choices=[SimpleNamespace(finish_reason=fin, message=SimpleNamespace(content=text, refusal=None))],
            usage=SimpleNamespace(prompt_tokens=900, completion_tokens=150, prompt_tokens_details=None),
            model=MODELL)


def fund(oz):
    return {"id": f"1|t.X83|{oz}", "pruefung": 1, "positionen": [{"datei": "t.X83", "oz": oz, "seite": None}],
            "belege": ["Rohr DN 125"], "feldbelege": []}


def texte_fuer(*fs):
    return {f["id"]: [{"oz": f["positionen"][0]["oz"], "kurztext": f"Rohr DN 125 Pos {f['positionen'][0]['oz']}",
                       "langtext": f"Rohr DN 100 aus Stahl, Pos {f['positionen'][0]['oz']}"}] for f in fs}


def konfig():
    return K.KiKonfig(MODELL, PLATZHALTER, "groq")


def lauf(funde, folge, tmp, **kw):
    sdk = FakeOpenAI(folge)
    schlaf = []
    client = C.GroqClient(sdk=sdk, schlafen=schlaf.append)
    meldungen = []
    erg, stat = K.gegenpruefung(funde, texte_fuer(*funde), konfig(), client=client,
                                cache_dir=Path(tmp) / "cache", log_datei=Path(tmp) / "log.jsonl",
                                fortschritt=lambda i, n, fid, t: meldungen.append((i, n, t)), **kw)
    return erg, stat, sdk, schlaf, meldungen


def test_parameter():
    with tempfile.TemporaryDirectory() as tmp:
        erg, stat, sdk, _, meld = lauf([fund("1.1")], [antwort_json(zk="Pos 1.1", zl="Pos 1.1")], tmp)
        kw = sdk.aufrufe[0]
        rf = kw["response_format"]
        check("Groq: temperature 0, fester seed, reasoning_effort low",
              kw["temperature"] == 0 and kw["seed"] == C.SEED and kw["reasoning_effort"] == "low")
        check("Groq: response_format json_schema strict mit Schema aus B4 (Enum der Einordnungen)",
              rf["type"] == "json_schema" and rf["json_schema"]["strict"] is True
              and rf["json_schema"]["schema"]["properties"]["einordnung"]["enum"] == K.EINORDNUNGEN
              and rf["json_schema"]["schema"]["additionalProperties"] is False
              and sorted(rf["json_schema"]["schema"]["required"]) == sorted(K.FELDER))
        check("Groq: Systemprompt und nur der Positionstext",
              kw["messages"][0] == {"role": "system", "content": K.SYSTEM_PROMPT}
              and kw["messages"][1]["role"] == "user" and len(kw["messages"]) == 2)
        check("Groq: keine von Groq nicht unterstützten Felder (logprobs, logit_bias, n, name)",
              not ({"logprobs", "logit_bias", "top_logprobs", "n"} & set(kw))
              and all("name" not in m for m in kw["messages"]))
        check("Groq: include_reasoning aus, Antwortlänge begrenzt",
              kw["extra_body"] == {"include_reasoning": False} and kw["max_completion_tokens"] == C.GROQ_MAX_TOKENS)
        k = erg["1|t.X83|1.1"]
        check("Groq: gültige Antwort, Anbieter und Modell im Ergebnis",
              k["status"] == K.STATUS_GUELTIG and k["anbieter"] == "groq" and k["modell"] == MODELL)
        check("Fortschritt: „Fund 1 von 1“ gemeldet", (1, 1, "läuft") in meld)
        log = [json.loads(z) for z in (Path(tmp) / "log.jsonl").read_text(encoding="utf-8").splitlines()]
        check("Log: Anbieter, Tokens und Dauer, keine Kosten bei Groq",
              log[0]["anbieter"] == "groq" and log[0]["usage"]["input_tokens"] == 900
              and log[0]["usage"]["output_tokens"] == 150 and "dauer_s" in log[0] and log[0]["kosten_usd"] == 0)
        check("Statistik: Tokens summiert, Kosten 0 bei Groq",
              stat["input_tokens"] == 900 and stat["output_tokens"] == 150 and stat["kosten_usd"] == 0.0)
        tok, anf = K.verbrauch_heute("groq", Path(tmp) / "log.jsonl", date.today())
        check("Tagesverbrauch aus dem Log: 1.050 Tokens, 1 Anfrage", tok == 1050 and anf == 1)
        sdk2 = FakeOpenAI([])
        erg2, stat2 = K.gegenpruefung([fund("1.1")], texte_fuer(fund("1.1")), konfig(),
                                      client=C.GroqClient(sdk=sdk2), cache_dir=Path(tmp) / "cache",
                                      log_datei=Path(tmp) / "log.jsonl")
        check("Zweiter Lauf: 0 Aufrufe, gleiches Ergebnis aus dem Cache",
              not sdk2.aufrufe and stat2["aufrufe"] == 0 and erg2["1|t.X83|1.1"]["einordnung"] == k["einordnung"])
        cache = list((Path(tmp) / "cache").iterdir())[0].read_text()
        check("Cache: Anbieter und Modell im Eintrag, kein Key",
              '"anbieter": "groq"' in cache and MODELL in cache and PLATZHALTER not in cache)
        check("Cache-Schlüssel hängt am Anbieter",
              K.cache_schluessel("groq", MODELL, "x") != K.cache_schluessel("anthropic", MODELL, "x"))


def test_429_und_technik():
    with tempfile.TemporaryDirectory() as tmp:
        erg, stat, sdk, schlaf, meld = lauf([fund("2.1")], [fehler_429("3"), fehler_429("2"),
                                                            antwort_json(zk="Pos 2.1", zl="Pos 2.1")], tmp)
        check("429: Wartezeit aus retry-after eingehalten (3 s, 2 s), dann Erfolg",
              schlaf == [3.0, 2.0] and erg["1|t.X83|2.1"]["status"] == K.STATUS_GUELTIG and len(sdk.aufrufe) == 3)
        check("429: Wartezeit in der Anzeige gemeldet", any("warte 3 s" in t for _, _, t in meld))
        check("429: Wartezeit in der Statistik", stat["wartezeit_s"] == 5.0)
    with tempfile.TemporaryDirectory() as tmp:
        funde = [fund("3.1"), fund("3.2")]
        erg, stat, sdk, schlaf, _ = lauf(funde, [fehler_429("1")] * 4, tmp)
        check("429 nach 3 Wiederholungen: technischer Fehler, Lauf bricht ab",
              len(sdk.aufrufe) == 4 and schlaf == [1.0, 1.0, 1.0] and erg == {} and stat["nicht_geprueft"] == 2
              and "Limit" in stat["meldung"])
        check("Technischer Fehler wird nicht gecacht", not (Path(tmp) / "cache").exists())
        erg, stat, sdk, _, _ = lauf(funde, [antwort_json(zk="Pos 3.1", zl="Pos 3.1"),
                                            antwort_json(zk="Pos 3.2", zl="Pos 3.2")], tmp)
        check("Nächster Klick versucht die Funde neu", len(sdk.aufrufe) == 2 and len(erg) == 2)
    with tempfile.TemporaryDirectory() as tmp:
        erg, stat, sdk, schlaf, _ = lauf([fund("4.1")], [fehler_429("3600")], tmp)
        check("Sehr lange Wartezeit (z. B. Tageslimit): sofort abbrechen statt warten",
              schlaf == [] and len(sdk.aufrufe) == 1 and stat["nicht_geprueft"] == 1)
    with tempfile.TemporaryDirectory() as tmp:
        zeit = openai.APITimeoutError(request=httpx2.Request("POST", URL))
        erg, stat, sdk, _, _ = lauf([fund("5.1"), fund("5.2")], [zeit, antwort_json(zk="Pos 5.2", zl="Pos 5.2")], tmp)
        check("Zeitüberschreitung: Fund ohne Ergebnis, nicht gecacht, nächster Fund läuft weiter",
              "1|t.X83|5.1" not in erg and erg["1|t.X83|5.2"]["status"] == K.STATUS_GUELTIG
              and stat["nicht_geprueft"] == 1 and any("Zeitüberschreitung" in x for x in stat["technische_fehler"]))
        check("Zeitlimit 60 s je Aufruf", C.ZEITLIMIT_S == 60)


def test_modellantworten():
    with tempfile.TemporaryDirectory() as tmp:
        erg, _, _, _, _ = lauf([fund("6.1")], [("", "content_filter")], tmp)
        check("Ablehnung: „KI-Antwort abgelehnt“, wird mit Status gecacht",
              erg["1|t.X83|6.1"]["status"] == "KI-Antwort abgelehnt" and (Path(tmp) / "cache").exists())
        erg, stat, _, _, _ = lauf([fund("6.2")], [('{"einordnung": "echter', "length"), ('{"kaputt', "length")], tmp)
        check("Abgeschnittene Antwort zweimal: „KI-Antwort unlesbar“, mit Status gecacht",
              erg["1|t.X83|6.2"]["status"] == K.STATUS_UNLESBAR and stat["aufrufe"] == 2)
        erg, _, _, _, _ = lauf([fund("6.3")], [antwort_json(zl="Rohr DN 100 aus Edelstahl")], tmp)
        check("Zitat nicht im Text: verworfen (gleiche Prüfkette wie bei Anthropic)",
              erg["1|t.X83|6.3"]["status"] == K.STATUS_ZITAT)
        sdk = FakeOpenAI([])
        check("/models: Modellliste über den Client", C.GroqClient(sdk=sdk).modelle() == [MODELL])


def test_konfig():
    with tempfile.TemporaryDirectory() as tmp:
        env = Path(tmp) / ".env"
        env.write_text(f"KI_ANBIETER=groq\nKI_MODELL={MODELL}\nGROQ_API_KEY={PLATZHALTER}\n", encoding="utf-8")
        k = K.lade_konfig(env)
        check("Konfig: Anbieter groq, Modell, Key gesetzt, nicht in repr",
              k.anbieter == "groq" and k.modell == MODELL and k.aktiv and PLATZHALTER not in repr(k))
        c = k.client()
        check("Client: GroqClient mit Groq-Endpunkt, Zeitlimit 60 s, ohne SDK-Wiederholungen",
              isinstance(c, C.GroqClient) and str(c._sdk.base_url).rstrip("/") == C.GROQ_BASE_URL
              and c._sdk.max_retries == 0)
        check("KI-Status nennt Anbieter und Modell", K.ki_status(k) == f"KI an: groq / {MODELL}, Prompt P4-v2")
        env.write_text(f"KI_ANBIETER=groq\nKI_MODELL={MODELL}\nANTHROPIC_API_KEY={PLATZHALTER}\n", encoding="utf-8")
        check("Groq ohne GROQ_API_KEY: KI aus", K.lade_konfig(env).aktiv is False)
        check("Ausweichmodell aus (Team 21.11.2026)", C.FALLBACKS is None)
        check("Denkaufwand je Client einstellbar (Vortest A/B)",
              k.client(reasoning_effort="medium").reasoning_effort == "medium" and k.client().reasoning_effort == C.GROQ_REASONING)
        check("Cache-Schlüssel hängt am Denkaufwand", K.denkaufwand("groq") == C.GROQ_REASONING)


if __name__ == "__main__":
    test_parameter()
    test_429_und_technik()
    test_modellantworten()
    test_konfig()
    print(f"\n{sum(ergebnisse)} von {len(ergebnisse)} Tests bestanden")
    sys.exit(0 if all(ergebnisse) else 1)
