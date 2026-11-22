"""
lv_parser.py - liest Leistungsverzeichnisse (LV) aus GAEB XML, GAEB 90 und PDF
und bringt alle in dieselbe Tabelle.

Benutzung im Terminal:
    python lv_parser.py "LV-Ausdruck-[PROJEKT_004].pdf"
    python lv_parser.py "GAEB-[PROJEKT_004].X83" --out ergebnis.xlsx

Benutzung im Code:
    from lv_parser import parse
    df = parse("datei.X83")          # pandas DataFrame, eine Zeile pro Titel/Position

Benötigt: pip install pdfplumber lxml pandas openpyxl

Eigenschaften:
- Wiederholbar: gleiche Datei -> exakt gleiche Tabelle (keine KI, kein Zufall).
- Jede Zeile hat eine Fundstelle (Datei, Seite bei PDF), damit Befunde zuordenbar sind.
"""
import re
import sys
import hashlib
from collections import Counter
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Gemeinsames Datenmodell
# ---------------------------------------------------------------------------
COLUMNS = [
    "datei", "format", "seite", "typ", "oz", "titel", "kurztext", "langtext",
    "menge", "einheit", "einheit_roh", "ep", "gp", "art", "art_roh",
]

UNIT_MAP = {
    "m2": "m²", "m²": "m²", "qm": "m²",
    "m3": "m³", "m³": "m³", "cbm": "m³",
    "st": "St", "stk": "St", "stck": "St", "stück": "St", "stk.": "St", "st.": "St",
    "h": "h", "std": "h", "std.": "h", "stunde": "h",
    "t": "t", "to": "t",
    "psch": "psch", "pschl": "psch", "pausch": "psch", "pauschal": "psch", "pau": "psch",   # „pau“: B1p3 (L53)
    "m": "m", "lfm": "m", "lfdm": "m", "m.": "m", "mt": "Mt",
    "jahr": "Jahr", "jahre": "Jahr", "monat": "Mt", "monate": "Mt", "woche": "Wo", "wochen": "Wo",
    "tag": "d", "tage": "d", "stunden": "h",
}


def norm_unit(u):
    if u is None:
        return ""
    u = u.strip()
    return UNIT_MAP.get(u.lower(), u)


def de_number(s):
    """'3.200,000' -> 3200.0 ; '1' -> 1.0 ; '' -> None"""
    if s is None or s == "":
        return None
    s = s.strip().replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def art_from(kurz, lang, einheit, extra=""):
    """Positionsart aus Text/Einheit ableiten (für alle Formate gleich)."""
    t = f"{extra} {kurz} {lang}".lower()
    arten = []
    if "bedarfsposition" in t or "eventualposition" in t or "nur einh" in t:
        arten.append("Bedarf")
    if "wahlposition" in t or "alternativposition" in t:
        arten.append("Wahl")
    if re.match(r"\s*(zulage|zul\.|zuschlag|mehrpreis)", (kurz or "").lower()):
        arten.append("Zulage")
    if einheit == "psch":
        arten.append("Pauschal")
    if einheit == "h" or "stundenlohn" in t:
        arten.append("Stundenlohn")
    if re.match(r"\s*(wie vor|leistung wie position)", (kurz or "").lower()):
        arten.append("Verweis")
    return ", ".join(arten) if arten else "Normal"


def make_row(**kw):
    row = {c: None for c in COLUMNS}
    row.update(kw)
    return row


# ---------------------------------------------------------------------------
# GAEB DA XML (.X81 .X83 .X84 .X86 ...)
# ---------------------------------------------------------------------------
def parse_gaeb_xml(path):
    from lxml import etree

    def ln(el):
        return etree.QName(el).localname if isinstance(el.tag, str) else ""

    def child(el, name):
        if el is None:
            return None
        for c in el:
            if ln(c) == name:
                return c
        return None

    def text_of(el):
        if el is None:
            return ""
        # eingebettete Bilder (base64) nicht als Text lesen
        parts = el.xpath('.//text()[not(ancestor::*[local-name()="image" or local-name()="Image"])]')
        if el.text and not parts:
            parts = [el.text]
        t = " ".join(x.strip() for x in parts if x.strip())
        return re.sub(r"\s+", " ", t).strip()

    def has_image(el):
        return el is not None and bool(el.xpath('.//*[local-name()="image" or local-name()="Image"]'))

    root = etree.parse(str(path), etree.XMLParser(huge_tree=True, recover=True)).getroot()
    fmt = "GAEB XML"
    rows = []

    def walk(body, prefix, titles):
        for node in body:
            name = ln(node)
            if name == "BoQCtgy":
                rno = node.get("RNoPart", "")
                lbl = text_of(child(node, "LblTx"))
                oz = ".".join(prefix + [rno])
                rows.append(make_row(datei=Path(path).name, format=fmt, typ="Titel", oz=oz,
                                     titel=" > ".join(titles), kurztext=lbl[:200], langtext=lbl))
                sub = child(node, "BoQBody")
                if sub is not None:
                    walk(sub, prefix + [rno], titles + [lbl[:80]])
            elif name == "Itemlist":
                for it in node:
                    if ln(it) == "Item":
                        rows.append(item_row(it, prefix, titles))

    def item_row(it, prefix, titles):
        oz = ".".join(prefix + [it.get("RNoPart", "")])
        if it.get("RNoIndex"):
            oz += it.get("RNoIndex")
        desc = child(it, "Description")
        ct = child(desc, "CompleteText")
        kurz = text_of(child(child(ct, "OutlineText"), "OutlTxt")) if ct is not None else ""
        lang = text_of(child(ct, "DetailTxt")) if ct is not None else ""
        if not kurz and ct is not None:
            kurz = lang[:120]
        qu_raw = text_of(child(it, "QU"))
        qu = norm_unit(qu_raw)
        qty = text_of(child(it, "Qty"))
        up = text_of(child(it, "UP"))
        gp = text_of(child(it, "IT"))
        flags = []
        if has_image(desc):
            flags.append("enthält Bild/Skizze")
        prov = child(it, "Provis")
        if prov is not None:
            flags.append("Bedarfsposition " + text_of(prov))
        if child(it, "ALNGroupNo") is not None:
            flags.append("Wahlposition/ALN " + text_of(child(it, "ALNGroupNo")) + "-" + text_of(child(it, "ALNSerNo")))
        if child(it, "LumpSumItem") is not None:
            flags.append("Pauschal")
        if child(it, "HourIt") is not None:
            flags.append("Stundenlohn")
        # B1p3 (Team, 22.11.2026, F1): Unterbeschreibungen (SubDescr) gehören zur Position
        for sd in it:
            if ln(sd) == "SubDescr":
                sct = child(child(sd, "Description"), "CompleteText")
                teile = [text_of(child(child(sct, "OutlineText"), "OutlTxt")), text_of(child(sct, "DetailTxt"))]
                lang = " ".join(t for t in [lang] + teile if t)
        art = art_from(kurz, lang, qu, " ".join(flags))
        if any(f.startswith("Wahlposition") for f in flags) and "Wahl" not in art:
            art = ("Wahl, " + art) if art != "Normal" else "Wahl"
        return make_row(datei=Path(path).name, format=fmt, typ="Position", oz=oz,
                        titel=" > ".join(titles), kurztext=kurz, langtext=lang,
                        menge=float(qty) if qty else None, einheit=qu, einheit_roh=qu_raw,
                        ep=float(up) if up else None, gp=float(gp) if gp else None,
                        art=art, art_roh="; ".join(flags))

    for boq in root.iter():
        if isinstance(boq.tag, str) and ln(boq) == "BoQ":
            body = child(boq, "BoQBody")
            if body is not None:
                walk(body, [], [])
    return rows


# ---------------------------------------------------------------------------
# GAEB 90 (.D81 .D83 .D84 .D86 ...): Textdatei mit festen 80-Zeichen-Zeilen
# ---------------------------------------------------------------------------
def _decode_gaeb90(b):
    best = None
    for enc in ("cp850", "cp1252"):
        t = b.decode(enc, errors="replace")
        score = sum(t.count(c) for c in "äöüÄÖÜß") - 5 * t.count("�")
        if best is None or score > best[0]:
            best = (score, t)
    return best[1]


POSITIONSSAETZE = {f"{n}" for n in range(21, 31)}    # GAEB 90: Sätze einer Position (B1p2)


def parse_gaeb90(path):
    fmt = "GAEB 90"
    t = _decode_gaeb90(Path(path).read_bytes())
    lines = [l for l in t.replace("\r\n", "\n").split("\n") if l]
    rows, cur, titles, ctx = [], None, {}, None
    mask = None
    for l in lines:
        if l.startswith("00"):
            mm = re.search(r"([1-9]+P+I?)", l[50:74])
            mask = mm.group(1) if mm else None
            break

    def clean_oz(raw):
        if mask and len(mask) <= len(raw):
            parts, i = [], 0
            while i < len(mask):
                j = i
                while j < len(mask) and mask[j] == mask[i]:
                    j += 1
                seg = raw[i:j].strip()
                if mask[i] == "I":
                    if seg and parts:
                        parts[-1] += seg
                elif seg:
                    parts.append(seg)
                i = j
            return ".".join(parts)
        return re.sub(r"\s+", ".", raw.strip())

    def title_path(oz_raw):
        parts = clean_oz(oz_raw).split(".")
        out = []
        for i in range(1, len(parts)):
            key = ".".join(parts[:i])
            if key in titles:
                out.append(titles[key][:80])
        return " > ".join(out)

    for l in lines:
        ra = l[:2]
        if ra not in POSITIONSSAETZE:
            # B1p2 (Team 21.11.2026, B2-L1): Zu einer Position gehören nur die Sätze 21–30 (Satz 24, 28, 30 stehen
            # innerhalb von Positionen). Jeder andere Satz (11/12 Bereich, 20 Vorbemerkung, 31/32 Bereichsende, 99 …)
            # beendet die Position; folgende Sätze 25/26 gehören nicht mehr zu ihr (R5: Text nur aus der Position).
            cur = None
        if ra == "11":
            ctx = clean_oz(l[2:11])
            titles.setdefault(ctx, "")
        elif ra == "12" and ctx is not None:
            titles[ctx] = (titles[ctx] + " " + l[2:72].strip()).strip()
        elif ra == "21":
            cur = make_row(datei=Path(path).name, format=fmt, typ="Position", oz=clean_oz(l[2:11]),
                           kurztext="", langtext="", einheit_roh=l[34:38].strip(),
                           art_roh=l[11:14])
            cur["_ozraw"] = l[2:11]
            q = l[23:34].strip()
            cur["menge"] = int(q) / 1000 if q.isdigit() else None
            cur["einheit"] = norm_unit(cur["einheit_roh"])
            rows.append(cur)
        elif ra == "23":
            if cur is None or cur.get("_ozraw") != l[2:11]:
                cur = make_row(datei=Path(path).name, format=fmt, typ="Position", oz=clean_oz(l[2:11]),
                               kurztext="", langtext="", art_roh="")
                cur["_ozraw"] = l[2:11]
                rows.append(cur)
            toks = l[11:72].split()
            if cur.get("menge") is None and len(toks) >= 3 and toks[2].isdigit():
                cur["menge"] = int(toks[2]) / 1000
            if len(toks) >= 2 and toks[0].isdigit() and toks[1].isdigit():
                cur["gp"] = int(toks[1]) / 100
                q = cur.get("menge") or 0
                # EP hat je nach Programm 2 oder 3 Nachkommastellen: die passende wählen
                cands = [(abs(int(toks[0]) / 10 ** d * q - cur["gp"]), d) for d in (2, 3)]
                d = min(cands)[1] if q else (3 if len(toks[0]) >= 11 else 2)
                cur["ep"] = int(toks[0]) / 10 ** d
        elif ra == "25" and cur is not None:
            cur["kurztext"] = (cur["kurztext"] + " " + l[2:72].strip()).strip()
        elif ra == "26" and cur is not None:
            cur["langtext"] = (cur["langtext"] + " " + l[2:72].strip()).strip()

    title_rows = [make_row(datei=Path(path).name, format=fmt, typ="Titel", oz=k, titel="",
                           kurztext=v, langtext=v) for k, v in titles.items()]
    for r in rows:
        r["titel"] = title_path(r.pop("_ozraw"))
        r["art"] = art_from(r["kurztext"], r["langtext"], r["einheit"])
    # Titel vor ihre Positionen sortieren (stabil, nach OZ-Teilen)
    allrows = title_rows + rows

    def key(r):
        return [int(p) if p.isdigit() else 0 for p in (r["oz"] or "").split(".")] + [0 if r["typ"] == "Titel" else 1]
    allrows.sort(key=key)
    return allrows


# ---------------------------------------------------------------------------
# PDF: Textzeilen mit Layout lesen, dann OZ-, Text- und Mengenzeilen erkennen
# ---------------------------------------------------------------------------
# B1p3 (Team, 22.11.2026, F2): OZ mit leerer Ebene „1.2..2“ (LV_13_ELT.pdf) ist eine OZ; sie bleibt wie gedruckt.
OZ_RE = re.compile(r"^(?P<ind> *)(?P<oz>(?:\d{1,4}[a-z]?(?:\.{1,2}\d{1,4}){0,5}|(?:\.\d{1,4}){1,5})\.?)(?= |$) *(?P<rest>.*)$")
TITLE_WORD_RE = re.compile(r"^ *(?:Bereich|Abschnitt|Titel|Los|Unterabschnitt) +(?P<oz>\d{1,4}(?:\.\d{1,4}){0,5}\.?) +(?P<rest>.*)$")
NUM = r"(?:\d{1,3}(?:\.\d{3})+|\d+)(?:,\d{1,4})?"
QTY_RE = re.compile(r"^ *(?P<qty>" + NUM + r") +(?P<unit>[A-Za-zÄÖÜäöüß²³][A-Za-zÄÖÜäöüß²³0-9/]{0,7}\.?)(?: +(?P<rest>.*))?$")
# B1p3: Mengenzeile ohne Einheit – Menge mit 3 Nachkommastellen, danach nur die Punktefelder für EP und GP
QTY_OHNE_EINHEIT_RE = re.compile(r"^ *(?P<qty>(?:\d{1,3}(?:\.\d{3})+|\d+),\d{3}) +(?P<rest>\.{5,}(?: +\.{5,})*) *$")
PRICE_RE = re.compile(r"\d{1,3}(?:\.\d{3})*,\d{2,3}\b")
NOISE_RE = re.compile(
    r"Übertrag|Seite *:? *\d|Seite \d+ von|Druckdatum|in EUR *$|Gesamtsumme|MWSt|^ *Summe\b|"
    r"Alle Einzelbeträge|Gesamtbetrag *:|^ *(OZ|Pos|Ordnungszahl|Nr\.|Pos-Nr)\b.*(Menge|Leistungsbeschreibung|Einheit)|"
    r"^ *Nr\.\) *$|Netto *:")
TITLE_PREFIX_RE = re.compile(r"^(?:LV|Titel|Bereich|Los|Abschnitt)\s+", re.I)
# B1p (Team, 21.11.2026, F3): Schlussteil eines LV bzw. Zusammenstellung beendet den Text der Position;
# alle Zeilen bis zur nächsten OZ gehören nicht mehr zur Position (R5: Beleg nur aus dem Text der Position).
STOP_RE = re.compile(
    r"^\s*(?:Gesamt)?[Zz]usammenstellung(?:\s+(?:Bereich|Abschnitt|Titel|Los)\b.*)?\s*$|"
    r"^\s*Zuzüglich der gesetzlichen Mehrwertsteuer\b|^\s*Das LV besteht aus den Seiten\b")
KOPF_ZEILEN = 12        # B1p: Kopfbereich je Seite für die Kopfzeilen-Erkennung kurzer PDFs (2–3 Seiten)
# B1p3 (Team, 22.11.2026, F1): Hinter der letzten Mengenzeile gehört nur eine Unterbeschreibung zur Position.
# Sie beginnt mit „Unterbeschreibung N:“ und endet an der Einleitung der Folgeposition (GAEB: SubDescr im Item).
UNTER_START_RE = re.compile(r"^Unterbeschreibung \d+:$")
UNTER_ENDE_RE = re.compile(r"^(?:Gemäß\b.*\b\d+:|Leitbeschreibung:|\*\*\*.*)$")


def _is_date(oz):
    p = oz.rstrip(".").split(".")
    return len(p) == 3 and len(p[2]) == 4 and p[2][:2] in ("19", "20") and p[0].isdigit() and p[1].isdigit() \
        and int(p[0]) <= 31 and int(p[1]) <= 12


UNIT_OK_RE = re.compile(
    r"^(?:m|m2|m²|m3|m³|qm|cbm|lfm|lfdm|st|stk|stck|stück|psch|pschl|pausch|h|std|t|to|kg|g|l|km|cm|mm|"
    r"kw|kwh|mt|mon|monate?|wo|wochen?|d|tage?|jahre?|jhr|stunden?|satz|paar|pkt|stg|e|einh|vb|ltr|pau|set)"
    r"(?:wo|d|mt|tag|mon)?\.?$", re.I)


def _qty_line(line):
    """Gibt (menge, einheit_roh, ep, gp, rest) zurück, wenn die Zeile eine Mengenzeile ist."""
    ohne = QTY_OHNE_EINHEIT_RE.match(line)
    if ohne:
        return de_number(ohne.group("qty")), "", None, None, ohne.group("rest")   # B1p3: Einheit fehlt im Original
    m = QTY_RE.match(line)
    if not m:
        return None
    rest = (m.group("rest") or "").strip()
    qty = m.group("qty")
    unit = m.group("unit")
    if not UNIT_OK_RE.match(unit):
        return None
    # Rest darf nur Preisfelder enthalten: Punkte, Preise, EP/GP, "Nur Einh.-Pr."
    leftover = re.sub(r"\.{2,}|…|\d{1,3}(?:\.\d{3})*,\d{2,3}|\bEP\b|\bGP\b|Nur\s*Einh\.?\s*-?\s*Pr\.?|[\s*:.\-'|]", "", rest)
    pricey = rest != "" and leftover == ""
    three_dec = bool(re.search(r",\d{3}$", qty))
    if not (pricey or (rest == "" and three_dec)):
        return None
    prices = PRICE_RE.findall(rest)
    ep = de_number(prices[0]) if len(prices) >= 2 else None
    gp = de_number(prices[-1]) if len(prices) >= 2 else (de_number(prices[0]) if len(prices) == 1 else None)
    return de_number(qty), unit, ep, gp, rest


def _schrift(chars):
    """Häufigste Schrift (ohne Subset-Präfix „ABCDEF+“) einer Zeichenfolge oder None."""
    c = Counter(ch.get("fontname", "").split("+")[-1] for ch in chars if ch.get("text", "").strip())
    return c.most_common(1)[0][0] if c else None


def _schriften(fp, zeilen):
    """B1p: Schrift je Layout-Zeile als (ganze Zeile, Zeile ohne erstes Wort), zugeordnet über den Text ohne
    Leerraum (pdfplumber extract_text_lines, gleiche Seite, Reihenfolge wie auf der Seite). Zeilen mit
    Anonymisierungs-Platzhalter („[PERSON_033]“, R9) sind im Datensatz als ganze Zeile in einer anderen Schrift
    neu gesetzt; ihre Schrift sagt nichts über Kurz- oder Langtext und gilt als unbekannt (None)."""
    tl = [(re.sub(r"\s", "", x["text"]), x) for x in fp.extract_text_lines(layout=False, x_tolerance=1.5)]
    frei, out = [True] * len(tl), []
    for z in zeilen:
        k = re.sub(r"\s", "", z)
        if "[" in z:
            out.append((None, None))
            continue
        j = next((i for i, (kk, _) in enumerate(tl) if frei[i] and kk == k), None)
        if j is None:
            out.append((None, None))
            continue
        frei[j] = False
        chars = [c for c in tl[j][1]["chars"] if c.get("text", "").strip()]
        erstes = len(z.split()[0]) if z.split() else 0
        rest = chars[erstes:] if len(z.split()) > 1 else chars
        out.append((_schrift(chars), _schrift(rest)))
    return out


def _pdf_zeilen(path):
    """Zeilen des PDF als (Seite, Zeile, Schrift ganze Zeile, Schrift ohne erstes Wort), ohne Kopf-/Fußzeilen."""
    import pdfplumber
    pages, fonts = [], []
    with pdfplumber.open(str(path)) as pdf:
        for p in pdf.pages:
            # Leerzeichen-Zeichen entfernen: manche PDFs legen sie doppelt über die Ziffern
            # ("8 5,000" statt "85,000"). Wörter werden dann über die Abstände getrennt.
            fp = p.filter(lambda o: not (o.get("object_type") == "char" and o.get("text", "").isspace()))
            txt = fp.extract_text(layout=True, x_tolerance=1.5) or ""
            zeilen = [l.rstrip() for l in txt.split("\n") if l.strip()]
            pages.append(zeilen)
            fonts.append(_schriften(fp, zeilen))
    # Kopf-/Fußzeilen: Zeilen, die auf vielen Seiten gleich vorkommen
    # (Mengenzeilen und OZ-Zeilen sind nie Kopf-/Fußzeilen, auch wenn sie ähnlich aussehen)
    def protected(l):
        return _qty_line(l) is not None or OZ_RE.match(l) is not None

    def key_of(l):
        return re.sub(r"\d", "#", re.sub(r"\s+", " ", l.strip()))

    normed = [set(key_of(l) for l in pg if not protected(l)) for pg in pages]
    cnt = Counter(x for s in normed for x in s)
    n = len(pages)
    boiler = {k for k, v in cnt.items() if n >= 4 and v >= max(3, 0.4 * n)}
    if 2 <= n < 4:
        # B1p: kurze PDFs (2–3 Seiten) – Kopfzeilen = Zeilen, die im Kopfbereich jeder Seite gleich stehen
        # (z. B. Firma, Tel./Fax, „Projekt: …“, „LV: …“ in LV_01, LV_15, LV_15a)
        koepfe = [set(key_of(l) for l in pg[:KOPF_ZEILEN] if not protected(l)) for pg in pages]
        boiler |= set.intersection(*koepfe)
    out = []
    for i, (pg, fs) in enumerate(zip(pages, fonts), start=1):
        for l, (f, f_rest) in zip(pg, fs):
            if not protected(l) and (key_of(l) in boiler or NOISE_RE.search(l)):
                continue
            out.append((i, l, f, f_rest))
    return out


def _pdf_lines(path):
    """Zeilen des PDF als (Seite, Zeile), ohne Kopf-/Fußzeilen (wie bisher; Schrift siehe _pdf_zeilen)."""
    return [(i, l) for i, l, _, _ in _pdf_zeilen(path)]


def _oz_candidates(lines):
    """Einrückungen, an denen OZ-ähnliche Zeilen stehen."""
    inds = Counter()
    for _, l in lines:
        m = OZ_RE.match(l)
        if m and "." in m.group("oz") and not _is_date(m.group("oz")) and m.group("rest"):
            inds[len(m.group("ind"))] += 1
    return inds


def _choose_oz_col(lines):
    """Die OZ-Spalte ist die Einrückung, bei der die meisten Blöcke eine Mengenzeile haben."""
    best = (-1, 0)
    for ind in sorted(_oz_candidates(lines)):
        blocks_with_qty, in_block, has_q = 0, False, False
        for _, l in lines:
            m = OZ_RE.match(l)
            if m and "." in m.group("oz") and not _is_date(m.group("oz")) and abs(len(m.group("ind")) - ind) <= 2:
                if in_block and has_q:
                    blocks_with_qty += 1
                in_block, has_q = True, _qty_line(m.group("rest")) is not None
            elif in_block and _qty_line(l):
                has_q = True
        if in_block and has_q:
            blocks_with_qty += 1
        if blocks_with_qty > best[0]:
            best = (blocks_with_qty, ind)
    return best[1]


def _bis_positionsgrenze(zeilen):
    """B1p3: Zeilen eines Blocks ohne fremden Text hinter der letzten Mengenzeile. Unterbeschreibungen bleiben
    (ohne die Zeile „Unterbeschreibung N:“, die im GAEB-Original nur eine Nummer ist)."""
    letzte = max((i for i, z in enumerate(zeilen) if _qty_line(z["t"])), default=None)
    if letzte is None:
        return zeilen
    aus, in_unter = list(zeilen[:letzte + 1]), False
    for z in zeilen[letzte + 1:]:
        if UNTER_START_RE.match(z["t"]):
            in_unter = True
        elif UNTER_ENDE_RE.match(z["t"]):
            in_unter = False
        elif in_unter:
            aus.append(z)
    return aus


def _textschrift(blocks):
    """B1p: häufigste Schrift der Textzeilen in Positionsblöcken (= Schrift des Langtexts)."""
    c = Counter(z["font"] for b in blocks for z in b["lines"] if z["font"] and not _qty_line(z["t"]))
    return c.most_common(1)[0][0] if c else None


def _kurztextschrift(blocks):
    """B1p: häufigste Schrift der Kurztext-Zeilen (Text der OZ-Zeilen) – gilt für Kurztexte mit Platzhalter."""
    c = Counter(b["font"] for b in blocks if b["font"] and b["first"] and not b.get("inline"))
    return c.most_common(1)[0][0] if c else None


def parse_pdf(path):
    """PDF-Zweig. B1p (Team, 21.11.2026, F3; R5): Langtext nur aus dem Text der Position –
    - Schlussteil/Zusammenstellung (STOP_RE) beendet den Text der Position bis zur nächsten OZ;
    - Kopfzeilen kurzer PDFs (2–3 Seiten) werden wie Kopf-/Fußzeilen entfernt (_pdf_zeilen);
    - Menge in der OZ-Zeile (Angebots-Ausdruck, Fall A): nur eingerückte Zeilen gehören zur Position, sie
      bilden den (umbrochenen) Kurztext; ein Langtext wird in diesem Layout nicht gedruckt; Zeilen auf Höhe
      der OZ-Spalte (Fußzeilen, „Hinweistext …“, „Zusammenstellung …“) beenden den Text der Position;
    - sonst: Zeilen direkt nach der Kurztext-Zeile in derselben Schrift wie der Kurztext gehören zum
      Kurztext (Umbruch), aber nur, wenn sich diese Schrift von der Langtext-Schrift des Dokuments
      unterscheidet (z. B. Leistungsverzeichnis.pdf: Kurztext F1, Langtext F2).
    """
    fmt = "PDF"
    lines = _pdf_zeilen(path)

    oz_col = _choose_oz_col([(pg, l) for pg, l, _, _ in lines])

    blocks = []  # jeder Block = eine OZ mit ihren Zeilen
    cur = None
    seen_oz_lines = set()
    for page, l, font, font_rest in lines:
        m = OZ_RE.match(l)
        tw = TITLE_WORD_RE.match(l)
        single_ok = m and ("." in m.group("oz") or re.match(r"[A-Za-zÄÖÜ]", m.group("rest") or ""))
        if m and single_ok and not _is_date(m.group("oz")) and abs(len(m.group("ind")) - oz_col) <= 2:
            sig = re.sub(r"\s+", " ", l.strip())
            if sig in seen_oz_lines:
                continue  # gleiche OZ-Zeile schon gesehen = Titel-Kopfzeile, die auf jeder Seite wiederkommt
            seen_oz_lines.add(sig)
            rest = m.group("rest").strip()
            inline = bool(rest) and _qty_line(rest) is not None
            cur = {"oz": m.group("oz").rstrip("."), "page": page, "first": rest, "lines": [],
                   "font": font_rest, "inline": inline, "stop": False}
            blocks.append(cur)
        elif tw:
            cur = {"oz": tw.group("oz").rstrip("."), "page": page, "first": tw.group("rest").strip(),
                   "lines": [], "title_word": True, "font": font_rest, "inline": False, "stop": False}
            blocks.append(cur)
        elif cur is not None and not cur["stop"]:
            einzug = len(l) - len(l.lstrip())
            if STOP_RE.match(l) or (cur["inline"] and einzug <= oz_col + 2):
                cur["stop"] = True                 # B1p: kein Text der Position mehr bis zur nächsten OZ
                continue
            cur["lines"].append({"t": l.strip(), "font": font})

    textschrift, kurzschrift = _textschrift(blocks), _kurztextschrift(blocks)
    rows = []
    title_text = {}
    for b in blocks:
        first = b["first"]
        qty = None
        # Fall A: Menge steht direkt in der OZ-Zeile (Angebots-Ausdrucke)
        inline = _qty_line(first) if first else None
        text_lines = []                            # (Text, Schrift)
        if inline:
            qty = inline
            first = ""
        inline_found = inline is not None
        for z in (b["lines"] if inline_found else _bis_positionsgrenze(b["lines"])):
            l = z["t"]
            q = _qty_line(l) if not inline_found else None
            if q:
                qty = q  # die letzte Mengenzeile im Block gilt (Zahlen im Langtext stehen davor)
            elif not re.fullmatch(r"[.…' ]+|Angeb\. ?Fabrikat.*|Angebotenes Fabrikat:?", l):
                text_lines.append((l, z["font"]))
        marker = ""
        kfont = b["font"]
        if first.startswith("***"):
            marker = first.strip("* ")
            first, kfont = text_lines.pop(0) if text_lines else ("", None)
        if inline_found and text_lines:
            # B1p Fall A: eingerückter Text = (umbrochener) Kurztext, kein Langtext gedruckt
            first = " ".join(t for t, _ in text_lines)
            text_lines = []
        elif first:
            # B1p: umbrochene Kurztext-Zeilen – gleiche Schrift wie der Kurztext, andere als der Langtext; nicht
            # bei Zeilen mit Platzhalter (Schrift unbekannt) und nicht bei Überschriften („Hinweis:“, „Hinweis für
            # …“). Hat die Kurztext-Zeile selbst einen Platzhalter, gilt die übliche Kurztext-Schrift des Dokuments.
            kfont = kfont or (kurzschrift if "[" in first else None)
            while (kfont and kfont != textschrift and text_lines and text_lines[0][1] == kfont
                   and not text_lines[0][0].endswith(":") and not re.match(r"Hinweis\b", text_lines[0][0])):
                first += " " + text_lines.pop(0)[0]
        text_lines = [t for t, _ in text_lines]
        if qty is None or b.get("title_word"):
            name = TITLE_PREFIX_RE.sub("", first).strip()
            title_text[b["oz"]] = name
            rows.append(make_row(datei=Path(path).name, format=fmt, seite=b["page"], typ="Titel", oz=b["oz"],
                                 kurztext=name, langtext=" ".join([name] + text_lines).strip()))
            continue
        menge, unit_raw, ep, gp, rest = qty
        kurz = first if first else (text_lines[0] if text_lines else "")
        lang = " ".join(([first] if first else []) + text_lines).strip()
        unit = norm_unit(unit_raw)
        rows.append(make_row(datei=Path(path).name, format=fmt, seite=b["page"], typ="Position", oz=b["oz"],
                             kurztext=kurz, langtext=lang, menge=menge, einheit=unit, einheit_roh=unit_raw,
                             ep=ep, gp=gp, art=art_from(kurz, lang + " " + rest, unit, marker), art_roh=marker))

    # Titelpfad setzen; Titel ohne eigene Positionen (z. B. Gliederung der Vertragsbedingungen) weglassen
    pos_oz = [r["oz"] for r in rows if r["typ"] == "Position"]
    keep = []
    for r in rows:
        if r["typ"] == "Titel":
            if not any(p.startswith(r["oz"] + ".") for p in pos_oz):
                continue
        parts = r["oz"].split(".")
        path_titles = [title_text[".".join(parts[:i])] for i in range(1, len(parts)) if ".".join(parts[:i]) in title_text]
        r["titel"] = " > ".join(t[:80] for t in path_titles)
        keep.append(r)
    return keep


# ---------------------------------------------------------------------------
# Einstieg
# ---------------------------------------------------------------------------
def detect_format(path):
    suf = Path(path).suffix.lower()
    head = Path(path).read_bytes()[:400]
    if suf == ".pdf" or head.startswith(b"%PDF"):
        return "PDF"
    if b"<GAEB" in head or b"<?xml" in head or re.fullmatch(r"\.x\d\d", suf):
        return "GAEB XML"
    if re.fullmatch(r"\.d\d\d", suf) or head[:2] in (b"00", b"T0"):
        return "GAEB 90"
    raise ValueError(f"Unbekanntes Format: {path}")


def parse(path):
    """Liest eine LV-Datei und gibt eine Tabelle (pandas DataFrame) zurück."""
    fmt = detect_format(path)
    rows = {"PDF": parse_pdf, "GAEB XML": parse_gaeb_xml, "GAEB 90": parse_gaeb90}[fmt](path)
    df = pd.DataFrame(rows, columns=COLUMNS)
    return df


def fingerprint(df):
    """Prüfsumme der Tabelle: gleiche Datei muss immer denselben Wert liefern."""
    return hashlib.sha256(df.to_csv(index=False).encode("utf-8")).hexdigest()[:16]


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="LV-Datei (GAEB XML, GAEB 90, PDF) in eine Tabelle umwandeln")
    ap.add_argument("datei")
    ap.add_argument("--out", help="Ausgabe als .xlsx oder .csv (Standard: <datei>_parsed.xlsx)")
    a = ap.parse_args()
    df = parse(a.datei)
    pos = df[df.typ == "Position"]
    print(f"{a.datei}: {detect_format(a.datei)} | {len(pos)} Positionen, {len(df) - len(pos)} Titel | Prüfsumme {fingerprint(df)}")
    print(pos["einheit"].value_counts().head(10).to_string())
    out = a.out or str(Path(a.datei).with_suffix("")) + "_parsed.xlsx"
    if out.endswith(".csv"):
        df.to_csv(out, index=False, encoding="utf-8-sig")
    else:
        df.to_excel(out, index=False, sheet_name="LV")
    print("gespeichert:", out)
