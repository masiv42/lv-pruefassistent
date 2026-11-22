"""
test_ki_pruefung.py - Tests für die KI-Gegenprüfung (src/ki_pruefung.py, P4) ohne API-Kosten.

Ein Fake-Client ersetzt das SDK. Kein echter Key: die Tests verwenden nur einen Platzhalter.
Cache, Log, Goldstandard- und Etiketten-Testdateien liegen in einem Temp-Ordner, nicht in data/.
Aufruf aus der Projektwurzel (uv-Befehl siehe README.md):
  python src/test_ki_pruefung.py data/raw
"""
import copy
import io
import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

from openpyxl import load_workbook

import ki_pruefung as K
from bericht import pruefe_lv, risikobericht, r7_verstoesse, SPALTEN

D = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/raw")
PLATZHALTER_KEY = "nur-ein-platzhalter-kein-key"
MODELL = "claude-sonnet-5-5"
ergebnisse = []


def check(name, ok, detail=""):
    ergebnisse.append(ok)
    print(f"{'OK    ' if ok else 'FEHLER'} {name}" + (f" – {detail}" if detail and not ok else ""))


class FakeClient:
    """Wie anthropic.Anthropic: .beta.messages.create(**kw) liefert vorbereitete Antworten."""

    def __init__(self, antworten):
        self.antworten = list(antworten)
        self.aufrufe = []
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._create))

    def _create(self, **kw):
        self.aufrufe.append(kw)
        a = self.antworten.pop(0)
        text, stop = (a, "end_turn") if isinstance(a, str) else a
        return SimpleNamespace(
            content=[SimpleNamespace(type="thinking", thinking=""), SimpleNamespace(type="text", text=text)],
            usage=SimpleNamespace(input_tokens=1000, output_tokens=200, cache_creation_input_tokens=0,
                                  cache_read_input_tokens=800),
            stop_reason=stop, model=MODELL)


def antwort(einordnung="echter Widerspruch", zk="Rohr DN 125", zl="Rohr DN 100", grund="Werte widersprechen sich.",
            frage="Welche Nennweite gilt?"):
    return json.dumps({"einordnung": einordnung, "begruendung": grund, "zitat_kurztext": zk,
                       "zitat_langtext": zl, "rueckfrage": frage}, ensure_ascii=False)


def fund(oz, nr=1):
    return {"id": f"{nr}|t.X83|{oz}", "pruefung": nr, "kategorie": "möglicher Widerspruch",
            "titel": "Nennweite (DN) im Kurztext ≠ Langtext", "positionen": [{"datei": "t.X83", "oz": oz, "seite": None}],
            "belege": ["Rohr DN 125", "Rohr DN 100"], "feldbelege": [], "begruendung": "Kurztext nennt DN 125, "
            "Langtext nennt DN 100; kein Wert stimmt überein.", "stufe": 1, "stufe_begruendung": "", "prioritaet_in_stufe": 4,
            "rueckfrage": None, "status": "offen"}


def texte_fuer(*funde_):
    return {f["id"]: [{"oz": f["positionen"][0]["oz"], "kurztext": f"Rohr DN 125 Pos {f['positionen'][0]['oz']}",
                       "langtext": f"Rohr DN 100 aus Stahl, Pos {f['positionen'][0]['oz']}"}] for f in funde_}


def lauf(funde, texte, antworten, tmp, **kw):
    client = FakeClient(antworten)
    erg, stat = K.gegenpruefung(funde, texte, K.KiKonfig(MODELL, PLATZHALTER_KEY), client=client,
                                cache_dir=Path(tmp) / "cache", log_datei=Path(tmp) / "log.jsonl", **kw)
    return erg, stat, client


def test_kette():
    with tempfile.TemporaryDirectory() as tmp:
        f = fund("1.1"); texte = texte_fuer(f); vorher = copy.deepcopy(f)
        erg, stat, c = lauf([f], texte, [antwort()], tmp)
        k = erg[f["id"]]
        check("Gültige Antwort: Status gültig, Einordnung übernommen, 1 Aufruf",
              k["status"] == K.STATUS_GUELTIG and k["einordnung"] == "echter Widerspruch" and stat["aufrufe"] == 1)
        check("Regel-Fund bleibt unverändert (KI ändert nichts)", f == vorher)
        kw = c.aufrufe[0]
        check("Anfrage: Modell aus Konfig, Effort medium, kein temperature/top_p/top_k/tool_choice",
              kw["model"] == MODELL and kw["output_config"] == {"effort": "medium"}
              and not ({"temperature", "top_p", "top_k", "tool_choice", "tools"} & set(kw)))
        check("Anfrage: Systemprompt mit Prompt-Cache, Nachricht = nur Positionstext",
              kw["system"][0]["text"] == K.SYSTEM_PROMPT and kw["system"][0]["cache_control"] == {"type": "ephemeral"}
              and kw["messages"] == [{"role": "user", "content": K.positionstext(f, texte)}])
        log = [json.loads(z) for z in (Path(tmp) / "log.jsonl").read_text(encoding="utf-8").splitlines()]
        check("Log: usage je Aufruf in ki_log.jsonl", len(log) == 1 and log[0]["usage"]["input_tokens"] == 1000
              and log[0]["usage"]["cache_read_input_tokens"] == 800 and log[0]["ergebnis"] == K.STATUS_GUELTIG)
        alles = (Path(tmp) / "log.jsonl").read_text() + "".join(p.read_text() for p in (Path(tmp) / "cache").iterdir())
        check("Kein Key in Log oder Cache", PLATZHALTER_KEY not in alles)
        check("Kosten: 1000 ein, 800 Cache gelesen, 200 aus = 0,00408 $",
              abs(stat["kosten_usd"] - (1000 * 2 + 800 * 0.1 + 200 * 10) / 1e6) < 1e-12, str(stat["kosten_usd"]))
        # zweiter Lauf: 0 Aufrufe, gleiches Ergebnis (B10)
        erg2, stat2, c2 = lauf([f], texte, [], tmp)
        check("Cache-Treffer: 0 Aufrufe, gleiches Ergebnis",
              stat2["aufrufe"] == 0 and not c2.aufrufe and stat2["cache_treffer"] == 1
              and {k: v for k, v in erg2[f["id"]].items() if k != "quelle"}
              == {k: v for k, v in k.items() if k != "quelle"} and erg2[f["id"]]["quelle"] == "Cache")

    with tempfile.TemporaryDirectory() as tmp:
        f = fund("1.2"); texte = texte_fuer(f)
        erg, _, _ = lauf([f], texte, [antwort(zl="Rohr DN 100 aus Edelstahl")], tmp)
        k = erg[f["id"]]
        check("Zitat nicht im Original: verworfen, kein Inhalt übernommen",
              k["status"] == K.STATUS_ZITAT and k["einordnung"] == "" and k["begruendung"] == "")
        erg, stat, _ = lauf([fund("1.3")], texte_fuer(fund("1.3")), ["kein JSON {", antwort()], tmp)
        check("Kaputtes JSON: einmal neu gefragt, dann gültig (2 Aufrufe)",
              erg["1|t.X83|1.3"]["status"] == K.STATUS_GUELTIG and stat["aufrufe"] == 2)
        erg, stat, _ = lauf([fund("1.4")], texte_fuer(fund("1.4")), ["{\"einordnung\": 1}", "```json\nkaputt\n```"], tmp)
        check("Kaputtes JSON zweimal: „KI-Antwort unlesbar“ (2 Aufrufe)",
              erg["1|t.X83|1.4"]["status"] == K.STATUS_UNLESBAR and stat["aufrufe"] == 2)
        erg, _, _ = lauf([fund("1.5")], texte_fuer(fund("1.5")),
                         [antwort(grund="Der Bieter ist berechtigt, einen Nachtrag zu stellen.")], tmp)
        check("R7-Treffer in der Begründung: verworfen", erg["1|t.X83|1.5"]["status"] == K.STATUS_R7)
        erg, _, _ = lauf([fund("1.6")], texte_fuer(fund("1.6")), [antwort(frage="Ist das durchsetzbar?")], tmp)
        check("R7-Treffer in der Rückfrage: verworfen", erg["1|t.X83|1.6"]["status"] == K.STATUS_R7)
        erg, stat, _ = lauf([fund("1.7")], texte_fuer(fund("1.7")),
                            [antwort("anderes Bauteil"), antwort("anderes Bauteil", frage="")], tmp)
        check("Rückfrage bei „anderes Bauteil“ ist unvollständig: neu gefragt, dann gültig",
              erg["1|t.X83|1.7"]["status"] == K.STATUS_GUELTIG and erg["1|t.X83|1.7"]["rueckfrage"] == ""
              and stat["aufrufe"] == 2)
        erg, _, _ = lauf([fund("1.8")], texte_fuer(fund("1.8")), [("", "refusal")], tmp)
        check("Ablehnung (refusal): Status gemeldet, kein Inhalt", erg["1|t.X83|1.8"]["status"] == K.STATUS_ABGELEHNT)
        erg, _, _ = lauf([fund("1.9")], texte_fuer(fund("1.9")),
                         [antwort(einordnung="vielleicht"), antwort(einordnung="vielleicht")], tmp)
        check("Unbekannte Einordnung: unlesbar", erg["1|t.X83|1.9"]["status"] == K.STATUS_UNLESBAR)


def test_deckel_und_key():
    with tempfile.TemporaryDirectory() as tmp:
        funde = [fund(f"2.{i}") for i in range(1, 4)]
        texte = texte_fuer(*funde)
        erg, stat, c = lauf(funde, texte, [antwort(zk=f"Pos 2.{i}", zl=f"Pos 2.{i}") for i in range(1, 4)], tmp,
                            max_aufrufe=2)
        check("Deckel: höchstens 2 Aufrufe, 1 Fund nicht geprüft, Meldung",
              len(c.aufrufe) == 2 and stat["nicht_geprueft"] == 1 and "höchstens 2" in stat["meldung"]
              and len(erg) == 2, json.dumps(stat))
        check("Deckel-Standard ist 50", K.MAX_AUFRUFE == 50)
        env = Path(tmp) / ".env"
        env.write_text("KI_MODELL=claude-sonnet-5-5\n", encoding="utf-8")
        konf = K.lade_konfig(env)
        c = FakeClient([])
        erg, stat = K.gegenpruefung(funde, texte, konf, client=c, cache_dir=Path(tmp) / "c2",
                                    log_datei=Path(tmp) / "l2.jsonl")
        check("Kein Key: „KI aus (kein API-Key)“, kein Aufruf",
              K.ki_status(konf) == K.KI_AUS and stat["meldung"] == K.KI_AUS and not c.aufrufe and erg == {})
        env.write_text(f"KI_MODELL=claude-sonnet-5-5\nANTHROPIC_API_KEY={PLATZHALTER_KEY}\n", encoding="utf-8")
        konf = K.lade_konfig(env)
        check("Konfig aus .env: Modell gelesen, Key nicht in repr/str",
              konf.modell == MODELL and konf.aktiv and PLATZHALTER_KEY not in repr(konf) + str(konf))
        check("SDK-Client: höchstens 3 Wiederholungen bei 429/529", konf.client().max_retries == 3)
        check("Ohne .env: KI aus", K.lade_konfig(Path(tmp) / "fehlt.env").aktiv is False)


def test_echte_daten():
    n = "8209.003_Leistungsverzeichnis_leer.X83"
    funde, texte, info = pruefe_lv(D / n)
    vorher = copy.deepcopy(funde)
    k12 = K.ki_funde(funde)
    check("Nur Funde Nr. 1/2 gehen an die KI", all(f["pruefung"] in (1, 2) for f in k12) and len(k12) == 2)
    t = K.positionstext(k12[0], texte)
    check("Positionstext: Regelwerte, Kurz- und Langtext der Position",
          "Regelwerte: Kurztext nennt DN125; Langtext nennt DN100" in t and "Edelstahl-Rohr DN 125" in t, t[:120])
    andere = [x for f in funde if f["id"] != k12[0]["id"] for x in f["belege"]]
    check("Positionstext enthält keine anderen Positionen", not any(b in t for b in andere if len(b) > 15))
    with tempfile.TemporaryDirectory() as tmp:
        zk, zl = "Edelstahl-Rohr DN 125", "Edelstahlrohr DN 100, bis PN 16"
        antworten = [antwort(zk=zk, zl=zl, frage="Gilt DN 100 oder DN 125?"),
                     antwort("anderes Bauteil", zk="Losflansch DN 125, PN 10", zl="Losflansch, DN 100, PN 10", frage="")]
        erg, stat, _ = lauf(funde, texte, antworten, tmp)
        check("Echte Datei: KI-Funde 2, Regel-Funde unverändert (Anzahl, Reihenfolge, Inhalt)",
              len(erg) == 2 and funde == vorher, json.dumps(stat))
        wb = load_workbook(io.BytesIO(risikobericht(n, funde, texte, info, ki=erg, commit="test")))
        zeilen = [[c.value for c in r] for r in wb["Funde"].iter_rows()]
        kopf = zeilen[0]
        check("Export: neue KI-Spalten vorhanden",
              all(s in kopf for s in ["KI-Einordnung", "KI-Begründung", "KI-Zitat geprüft", "Rückfrage-Entwurf (KI)",
                                      "KI-Modell", "Prompt-Version"]))
        ki_e = {z[kopf.index("Fund-ID")]: z[kopf.index("KI-Einordnung")] for z in zeilen[1:]}
        check("Export: KI-Einordnung als „KI-Vorschlag“ gekennzeichnet, Nr. 3–6 leer",
              ki_e["1|8209.003_Leistungsverzeichnis_leer.X83|5.1.4"] == "KI-Vorschlag: echter Widerspruch"
              and all(v is None for i, v in ki_e.items() if not i.startswith(("1|", "2|"))))
        texte_alle = [c for z in zeilen for c in z if isinstance(c, str)]
        check("Export: R7 auch auf KI-Texte angewendet", not r7_verstoesse(texte_alle))
        erg_r7, _, _ = lauf(funde, texte, [antwort(zk=zk, zl=zl, grund="Ein Anspruch besteht."),
                                           antwort("anderes Bauteil", zk="Losflansch DN 125, PN 10",
                                                   zl="Losflansch, DN 100, PN 10", frage="")],
                            Path(tmp) / "neu")
        wb = load_workbook(io.BytesIO(risikobericht(n, funde, texte, info, ki=erg_r7, commit="test")))
        texte_alle = [c.value for r in wb["Funde"].iter_rows() for c in r if isinstance(c.value, str)]
        check("Export: verworfener KI-Text (R7) erscheint nicht, nur der Status",
              not r7_verstoesse(texte_alle) and K.STATUS_R7 in texte_alle)


def test_systemprompt_ohne_datensatz():
    treffer = []
    for n in ["8209.003_Leistungsverzeichnis_leer.X83", "[NUMMER_001]_leer.X83", "Leistungsverzeichnis.pdf",
              "LV_00_Roh_und_Erdauarbeiten.pdf", "501-24-01_GAEB-XML_sas.x83"]:
        funde, texte, _ = pruefe_lv(D / n)
        for f in K.ki_funde(funde):
            for b in f["belege"]:
                if len(b) > 12 and b in K.SYSTEM_PROMPT:
                    treffer.append(b)
            if f["positionen"][0]["oz"] in K.SYSTEM_PROMPT:
                treffer.append(f["positionen"][0]["oz"])
    check("B5: Systemprompt enthält keine Positionen oder OZ aus dem Datensatz", not treffer, str(treffer[:3]))
    check("B5: Prompt-Version P4-v2, R7 und R9 im Systemprompt",
          K.PROMPT_VERSION == "P4-v2" and "Anspruch" in K.SYSTEM_PROMPT and "[PERSON_" in K.SYSTEM_PROMPT)
    check("P4-v2 eingefroren: Prüfsumme passt, Änderung nur mit neuer Version", K.prompt_eingefroren())
    check("P4-v2: „anderes Bauteil“ nur bei benanntem Bauteil, Bauteile in der Begründung, im Zweifel „unklar“",
          "ausdrücklich einem anderen, benannten Bauteil" in K.SYSTEM_PROMPT
          and "zu welchem Bauteil jeder der beiden Werte gehört" in K.SYSTEM_PROMPT
          and 'Im Zweifel wähle "unklar"' in K.SYSTEM_PROMPT)
    vortest = json.loads((Path(__file__).resolve().parent.parent / "data/qa/ki_vortest.json").read_text(encoding="utf-8"))
    check("Vortest-Fälle stehen nicht im Systemprompt",
          not any(c["kurztext"] in K.SYSTEM_PROMPT or c["langtext"][:40] in K.SYSTEM_PROMPT for c in vortest["faelle"]))


def test_messung():
    with tempfile.TemporaryDirectory() as tmp:
        g = Path(tmp) / "gold.json"
        g.write_text(json.dumps({"eintraege": [
            {"fund_id": "a", "einordnung": "echter Widerspruch", "zaehlt": True},
            {"fund_id": "b", "einordnung": "anderes Bauteil", "zaehlt": True},
            {"fund_id": "c", "einordnung": "echter Widerspruch", "zaehlt": True},
            {"fund_id": "d", "einordnung": "offen", "zaehlt": False}]}), encoding="utf-8")
        erg = {"a": {"status": K.STATUS_GUELTIG, "einordnung": "echter Widerspruch"},
               "b": {"status": K.STATUS_GUELTIG, "einordnung": "unklar"},
               "c": {"status": K.STATUS_ZITAT, "einordnung": ""},
               "d": {"status": K.STATUS_GUELTIG, "einordnung": "unklar"}}
        z = {r["fund_id"]: r["urteil"] for r in K.messung(erg, g)}
        check("Messung: Treffer, Abweichung, verworfen; „offen“ zählt nicht",
              z == {"a": "Treffer", "b": "Abweichung", "c": "verworfen"}, str(z))
    gold = json.loads(K.GOLD_DATEI.read_text(encoding="utf-8"))
    check("Goldstandard: jeder zählende Eintrag hat eine Quelle, Einordnung aus der Liste",
          all(e["quelle"] and e["einordnung"] in K.EINORDNUNGEN for e in gold["eintraege"] if e["zaehlt"])
          and all(e["einordnung"] in ("offen", "strittig") for e in gold["eintraege"] if not e["zaehlt"]))
    check("Goldstandard: strittige Einträge tragen beide Einordnungen mit Quelle",
          all((len(e.get("einordnungen", [])) == 2 and all(x["quelle"] for x in e["einordnungen"]))
              or (e.get("einordnung_person_b") and e.get("quelle_person_b") and e["quelle"])
              for e in gold["eintraege"] if e.get("strittig")))


def test_messung_gruppen():
    with tempfile.TemporaryDirectory() as tmp:
        g = Path(tmp) / "gold.json"
        g.write_text(json.dumps({"eintraege": [
            {"fund_id": "a", "einordnung": "echter Widerspruch", "zaehlt": True, "regel_fund": True},
            {"fund_id": "a2", "einordnung": "echter Widerspruch", "zaehlt": True, "regel_fund": True},
            {"fund_id": "b", "einordnung": "anderes Bauteil", "zaehlt": True, "regel_fund": True},
            {"fund_id": "c", "einordnung": "Bereichs- oder Mehrfachangabe", "zaehlt": True},
            {"fund_id": "e", "einordnung": "echter Widerspruch", "zaehlt": True},
            {"fund_id": "u", "einordnung": "unklar", "zaehlt": True},
            {"fund_id": "z", "einordnung": "anderes Bauteil", "zaehlt": True, "regel_fund": False},
            {"fund_id": "s1", "einordnung": "echter Widerspruch", "zaehlt": True, "quelle": "T2", "strittig": True,
             "einordnung_person_b": "unklar", "quelle_person_b": "Person B"},
            {"fund_id": "s2", "einordnung": "strittig", "zaehlt": False, "strittig": True,
             "einordnungen": [{"einordnung": "echter Widerspruch", "quelle": "T2"},
                              {"einordnung": "unklar", "quelle": "Person B"}]}]}), encoding="utf-8")
        gv = lambda e: {"status": K.STATUS_GUELTIG, "einordnung": e}
        erg = {"a": gv("echter Widerspruch"), "a2": gv("echter Widerspruch"), "b": gv("echter Widerspruch"),
               "c": gv("anderes Bauteil"), "e": gv("unklar"), "u": gv("echter Widerspruch"), "z": gv("anderes Bauteil"),
               "s1": gv("echter Widerspruch"), "s2": gv("unklar")}
        zeilen = K.messung(erg, g)
        gr = {z["fund_id"]: z["gruppe"] for z in zeilen}
        check("Messung: Gruppen regel / zusatz / strittig",
              gr == {"a": "regel", "a2": "regel", "b": "regel", "c": "regel", "e": "regel", "u": "regel", "z": "zusatz",
                     "s1": "strittig", "s2": "strittig"}, str(gr))
        check("Messung: strittige Zeilen nennen beide Einordnungen, Urteil „strittig“",
              all(z["urteil"] == "strittig" and z["gold"] == "echter Widerspruch / unklar"
                  for z in zeilen if z["gruppe"] == "strittig"))
        a = K.auswertung(zeilen, {"a": "P1", "a2": "P1"})
        r = a["regel"]["je_fund"]
        check("Matrix grob: anderes Bauteil und Bereich = Fehlalarm; „unklar“ (Gold oder KI) getrennt, nicht bewertet",
              r["grob"]["treffer"] == 3 and r["grob"]["bewertet"] == 4 and r["grob"]["ki_unklar"] == 1
              and r["grob"]["gold_unklar"] == 1
              and r["grob"]["matrix"]["Fehlalarm"] == {"echt": 1, "Fehlalarm": 1}, str(r["grob"]))
        check("Matrix fein: 4 Klassen („unklar“ ist eine Klasse), Treffer nur bei gleicher Klasse",
              r["fein"]["treffer"] == 2 and r["fein"]["bewertet"] == 6, str(r["fein"]))
        check("Je Position: gleiche Position in zwei Dateien zählt einmal",
              a["regel"]["je_position"]["fein"]["gesamt"] == 5 and a["regel"]["positionen"] == 5)
        check("Zusatzfälle getrennt, strittige nicht in der Trefferquote",
              a["zusatz"]["je_fund"]["fein"]["gesamt"] == 1 and len(a["strittig"]) == 2
              and r["fein"]["gesamt"] == 6)
        z2 = K.messung(dict(erg, a2=gv("anderes Bauteil")), g)
        _, un = K.je_position([z for z in z2 if z["gruppe"] == "regel"], {"a": "P1", "a2": "P1"})
        check("Je Position: abweichende KI-Ergebnisse derselben Position = „uneinheitlich“", len(un) == 1)


def test_zusatzfaelle():
    funde, texte = K.zusatzfaelle(D)
    ids = [f["id"] for f in funde]
    soll = [f"1|501-24-01_GAEB-XML_sas.x83|{oz}" for oz in K.ZUSATZ_OZ]
    regel, _, _ = pruefe_lv(D / K.ZUSATZ_DATEI)
    check("Zusatzfälle: genau die 3 Fehlalarme 02.05.0005/0007/0009, nicht unter den Regel-Funden",
          ids == soll and not set(ids) & {f["id"] for f in regel}, str(ids))
    gold = {e["fund_id"]: e for e in json.loads(K.GOLD_DATEI.read_text(encoding="utf-8"))["eintraege"]}
    check("Zusatzfälle stehen im Goldstandard mit regel_fund=false",
          all(gold[i]["regel_fund"] is False and gold[i]["zaehlt"] for i in ids))
    t = K.positionstext(funde[0], texte)
    check("Zusatzfälle: Positionstext wie bei Regel-Funden (Regelwerte, Kurz- und Langtext)",
          t.startswith("Prüfung: Nennweite (DN)\nRegelwerte: Kurztext nennt DN1200") and "Rückstauverschluss" in t)


def test_etiketten():
    import etiketten as E
    from openpyxl import Workbook
    with tempfile.TemporaryDirectory() as tmp:
        g = Path(tmp) / "gold.json"
        g.write_text(json.dumps({"eintraege": [
            {"fund_id": "T2a", "einordnung": "echter Widerspruch", "zaehlt": True, "quelle": "T2"},
            {"fund_id": "T2b", "einordnung": "echter Widerspruch", "zaehlt": True, "quelle": "T2"},
            {"fund_id": "x1", "einordnung": "offen", "zaehlt": False, "quelle": "keine"},
            {"fund_id": "x2", "einordnung": "offen", "zaehlt": False, "quelle": "keine"},
            {"fund_id": "y1", "einordnung": "offen", "zaehlt": False, "quelle": "keine"},
            {"fund_id": "y2", "einordnung": "offen", "zaehlt": False, "quelle": "keine"},
            {"fund_id": "w1", "einordnung": "offen", "zaehlt": False, "quelle": "keine"}]}), encoding="utf-8")
        wb = Workbook(); ws = wb.active; ws.title = "Etiketten"
        ws.append(E.SPALTEN)
        hw = lambda i: f"gleiche Position wie Positiv-Test aus T2 ({i}; dort im Goldstandard „echter Widerspruch“) – bitte am Original bestätigen"
        ws.append(["a.pdf", "1.1", 1, "k", "DN 100", "DN 80", "echter Widerspruch", "", hw("T2a"), "x1\nx2"])
        ws.append(["a.pdf", "1.2", 1, "k", "DN 100", "DN 80", "unklar", "", hw("T2b"), "y1\ny2"])
        ws.append(["a.pdf", "1.3", 1, "k", "DN 100", "DN 80", "anderes Bauteil", "", "", "w1"])
        x = Path(tmp) / "e.xlsx"; wb.save(x)
        b = E.uebernehmen(x, g, herkunft="Test")
        neu = {e["fund_id"]: e for e in json.loads(g.read_text(encoding="utf-8"))["eintraege"]}
        check("Etiketten: neue Einordnungen mit Quelle Person B, zählend",
              sorted(b["neu"]) == ["w1", "x1", "x2"] and neu["w1"]["einordnung"] == "anderes Bauteil"
              and neu["w1"]["quelle"] == E.QUELLE_B and neu["w1"]["zaehlt"])
        check("Etiketten: gleiche Einordnung wie T2 → T2 bestätigt, nichts überschrieben",
              b["bestaetigt"] == ["1.1"] and neu["T2a"]["quelle"] == "T2" and neu["T2a"]["bestaetigt_durch"] == E.QUELLE_B)
        check("Etiketten: Abweichung von T2 → strittig, T2-Eintrag bleibt, beide Einordnungen mit Quelle",
              len(b["strittig"]) == 1 and neu["T2b"]["einordnung"] == "echter Widerspruch" and neu["T2b"]["zaehlt"]
              and neu["T2b"]["strittig"] and neu["T2b"]["einordnung_person_b"] == "unklar"
              and neu["y1"]["einordnung"] == "strittig" and not neu["y1"]["zaehlt"]
              and [e["einordnung"] for e in neu["y1"]["einordnungen"]] == ["echter Widerspruch", "unklar"])
        try:
            E.uebernehmen(x, g)
            zweimal = False
        except ValueError:
            zweimal = True
        check("Etiketten: zweites Übernehmen wird abgelehnt", zweimal)
        ws.cell(row=4, column=7, value="falsch")
        ws.cell(row=4, column=10, value="gibtsnicht")
        x2 = Path(tmp) / "f.xlsx"; wb.save(x2)
        g2 = Path(tmp) / "gold2.json"
        g2.write_text(json.dumps({"eintraege": [{"fund_id": "x1", "einordnung": "offen", "zaehlt": False}]}), encoding="utf-8")
        vorher = g2.read_text(encoding="utf-8")
        try:
            E.uebernehmen(x2, g2)
            abgelehnt = False
        except ValueError:
            abgelehnt = True
        check("Etiketten: ungültige Werte oder unbekannte Fund-IDs → nichts geändert",
              abgelehnt and g2.read_text(encoding="utf-8") == vorher)


def test_vortest_vergleich():
    import ki_vortest as V
    l1 = {"varianten": {"A": {"faelle": [{"id": "V1", "ki": "echter Widerspruch", "status": K.STATUS_GUELTIG},
                                         {"id": "V2", "ki": "unklar", "status": K.STATUS_GUELTIG}]}}}
    l2 = {"varianten": {"A": {"faelle": [{"id": "V1", "soll": "echter Widerspruch", "ki": "unklar", "status": K.STATUS_GUELTIG},
                                         {"id": "V2", "soll": "unklar", "ki": "unklar", "status": K.STATUS_GUELTIG}]}}}
    check("Stabilitätscheck: gewechselte Fälle werden erkannt", V.vergleich(l1, l2)["gewechselt"] == ["V1"])


if __name__ == "__main__":
    test_kette()
    test_deckel_und_key()
    test_echte_daten()
    test_systemprompt_ohne_datensatz()
    test_messung()
    test_messung_gruppen()
    test_zusatzfaelle()
    test_etiketten()
    test_vortest_vergleich()
    print(f"\n{sum(ergebnisse)} von {len(ergebnisse)} Tests bestanden")
    sys.exit(0 if all(ergebnisse) else 1)
