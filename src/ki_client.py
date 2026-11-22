"""
ki_client.py - Schnittstelle zu den KI-Anbietern der KI-Gegenprüfung (P4).

KI_ANBIETER in der .env wählt (Team, Chat 21.11.2026):
- "groq": OpenAI-kompatibler Endpunkt https://api.groq.com/openai/v1 über das Paket `openai`.
  Parameter laut Groq-Doku (console.groq.com/docs, abgerufen 21.11.2026):
  temperature 0 (Groq setzt intern 1e-8; docs/openai), seed (best effort; docs/api-reference),
  response_format json_schema mit strict: true (für openai/gpt-oss-120b unterstützt;
  docs/structured-outputs), reasoning_effort "low" (GPT-OSS; docs/reasoning),
  include_reasoning false (GPT-OSS; docs/reasoning). Zeitlimit 60 s. Bei 429 wird die
  Wartezeit aus „retry-after“ eingehalten, höchstens 3 Wiederholungen (docs/rate-limits).
- "anthropic": wie in P4 gebaut (Paket `anthropic`, Effort „medium“ über output_config).

Technische Fehler (Zeitüberschreitung, Netzfehler, 429 nach allen Wiederholungen, andere
HTTP-Fehler) werfen TechnischerFehler; sie werden nicht gecacht und beim nächsten Klick
neu versucht. Der Key wird nie ausgegeben.
"""
import time
from dataclasses import dataclass, field

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
ZEITLIMIT_S = 60
WIEDERHOLUNGEN_429 = 3
MAX_WARTEN_S = 120            # längere retry-after-Zeiten (z. B. Tageslimit): abbrechen statt warten
SEED = 20261121
GROQ_MAX_TOKENS = 2000
GROQ_REASONING = "low"
ANTHROPIC_MAX_TOKENS = 8000
ANTHROPIC_EFFORT = "medium"
FALLBACK_BETA = "server-side-fallback-2026-07-01"
FALLBACKS = None              # Team 21.11.2026: kein Ausweichmodell; es antwortet genau KI_MODELL


class TechnischerFehler(Exception):
    """Kein Modell-Ergebnis (Zeitüberschreitung, Netz, 429, HTTP-Fehler). Nicht cachen."""

    def __init__(self, art, wartezeit_s=0.0):
        super().__init__(art)
        self.art = art
        self.wartezeit_s = wartezeit_s


@dataclass
class KiAntwort:
    text: str
    stop_reason: str                  # "end_turn", "max_tokens", "refusal" (vereinheitlicht)
    modell: str
    usage: dict = field(default_factory=dict)
    dauer_s: float = 0.0
    wartezeit_s: float = 0.0


def _usage(input_tokens=0, output_tokens=0, cache_write=0, cache_read=0):
    return {"input_tokens": int(input_tokens or 0), "output_tokens": int(output_tokens or 0),
            "cache_creation_input_tokens": int(cache_write or 0), "cache_read_input_tokens": int(cache_read or 0)}


def antwort_schema(einordnungen):
    """JSON-Schema der Antwort (B4) für strict-Modus: alle Felder required, keine weiteren."""
    return {
        "type": "object",
        "properties": {
            "einordnung": {"type": "string", "enum": list(einordnungen)},
            "begruendung": {"type": "string"},
            "zitat_kurztext": {"type": "string"},
            "zitat_langtext": {"type": "string"},
            "rueckfrage": {"type": "string"},
        },
        "required": ["einordnung", "begruendung", "zitat_kurztext", "zitat_langtext", "rueckfrage"],
        "additionalProperties": False,
    }


class GroqClient:
    """Groq über den OpenAI-kompatiblen Endpunkt. `sdk` = openai.OpenAI oder Fake."""
    anbieter = "groq"

    def __init__(self, key=None, sdk=None, schlafen=time.sleep, reasoning_effort=None):
        self.reasoning_effort = reasoning_effort or GROQ_REASONING
        if sdk is None:
            import openai
            sdk = openai.OpenAI(api_key=key, base_url=GROQ_BASE_URL, timeout=ZEITLIMIT_S, max_retries=0)
        self._sdk = sdk
        self._schlafen = schlafen

    def modelle(self):
        return [m.id for m in self._sdk.models.list().data]

    def anfrage(self, modell, system, text, einordnungen=None, warte_hinweis=None, schema=None):
        import openai
        kw = dict(
            model=modell,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": text}],
            temperature=0,
            seed=SEED,
            response_format={"type": "json_schema",
                             "json_schema": {"name": "ki_einordnung", "strict": True,
                                             "schema": schema or antwort_schema(einordnungen)}},
            reasoning_effort=self.reasoning_effort,
            max_completion_tokens=GROQ_MAX_TOKENS,
            extra_body={"include_reasoning": False},
        )
        gewartet = 0.0
        for versuch in range(WIEDERHOLUNGEN_429 + 1):
            t0 = time.monotonic()
            try:
                r = self._sdk.chat.completions.create(**kw)
            except openai.RateLimitError as e:
                warte = _retry_after(e)
                if versuch == WIEDERHOLUNGEN_429 or warte > MAX_WARTEN_S:
                    raise TechnischerFehler(f"429 (Limit), retry-after {warte:.0f} s", gewartet) from None
                if warte_hinweis:
                    warte_hinweis(warte)
                self._schlafen(warte)
                gewartet += warte
                continue
            except openai.APITimeoutError:
                raise TechnischerFehler(f"Zeitüberschreitung nach {ZEITLIMIT_S} s", gewartet) from None
            except openai.APIConnectionError:
                raise TechnischerFehler("Netzfehler", gewartet) from None
            except openai.APIStatusError as e:
                raise TechnischerFehler(f"HTTP {e.status_code}", gewartet) from None
            dauer = time.monotonic() - t0
            wahl = r.choices[0]
            msg = wahl.message
            stop = {"stop": "end_turn", "length": "max_tokens", "content_filter": "refusal"}.get(
                wahl.finish_reason, wahl.finish_reason or "")
            if getattr(msg, "refusal", None):
                stop = "refusal"
            u = r.usage
            cached = getattr(getattr(u, "prompt_tokens_details", None), "cached_tokens", 0) if u else 0
            return KiAntwort(text=msg.content or "", stop_reason=stop, modell=r.model,
                             usage=_usage(getattr(u, "prompt_tokens", 0), getattr(u, "completion_tokens", 0),
                                          0, cached),
                             dauer_s=dauer, wartezeit_s=gewartet)
        raise TechnischerFehler("429 (Limit)", gewartet)       # nicht erreichbar


def _retry_after(fehler):
    try:
        return max(0.0, float(fehler.response.headers.get("retry-after", "2")))
    except (AttributeError, TypeError, ValueError):
        return 2.0


class AnthropicClient:
    """Claude über das Paket `anthropic` (wie in P4 gebaut). `sdk` = anthropic.Anthropic oder Fake."""
    anbieter = "anthropic"

    def __init__(self, sdk):
        self._sdk = sdk

    def anfrage(self, modell, system, text, einordnungen=None, warte_hinweis=None, schema=None):
        # schema (B5) nur für Groq; Anthropic antwortet laut System-Prompt im JSON-Format.
        kw = dict(
            model=modell,
            max_tokens=ANTHROPIC_MAX_TOKENS,
            system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": text}],
            output_config={"effort": ANTHROPIC_EFFORT},
        )
        if FALLBACKS:
            kw.update(betas=[FALLBACK_BETA], fallbacks=FALLBACKS)
        t0 = time.monotonic()
        try:
            r = self._sdk.beta.messages.create(**kw)
        except Exception as e:                          # nur SDK-Fehler in technische Fehler wandeln
            import anthropic
            if isinstance(e, anthropic.APITimeoutError):
                raise TechnischerFehler("Zeitüberschreitung") from None
            if isinstance(e, anthropic.APIConnectionError):
                raise TechnischerFehler("Netzfehler") from None
            if isinstance(e, anthropic.RateLimitError):
                raise TechnischerFehler("429 (Limit)") from None
            if isinstance(e, anthropic.APIStatusError):
                raise TechnischerFehler(f"HTTP {e.status_code}") from None
            raise
        dauer = time.monotonic() - t0
        u = getattr(r, "usage", None)
        hole = lambda n: getattr(u, n, 0) if u is not None else 0
        text = "".join(getattr(b, "text", "") for b in getattr(r, "content", []) if getattr(b, "type", "") == "text")
        return KiAntwort(text=text, stop_reason=getattr(r, "stop_reason", "") or "",
                         modell=getattr(r, "model", modell),
                         usage=_usage(hole("input_tokens"), hole("output_tokens"),
                                      hole("cache_creation_input_tokens"), hole("cache_read_input_tokens")),
                         dauer_s=dauer)


def als_client(obj, anbieter):
    """Adapter wählen: fertiger Client (hat .anfrage), Anthropic-SDK/Fake (.beta) oder OpenAI-SDK/Fake (.chat)."""
    if hasattr(obj, "anfrage"):
        return obj
    if anbieter == "groq" or hasattr(obj, "chat"):
        return GroqClient(sdk=obj)
    return AnthropicClient(obj)
