"""
demo_lv.py - Block B7: Demo-LV als Kopie eines Originals mit je einem eingebauten Fall pro Prüfung (Sitzung B2,
Team 21.11.2026, 18:50). data/raw wird nur gelesen; die Kopie entsteht in einem anderen Ordner (Vorschlag `demo/`,
nicht im Repo, wie data/raw: die Kopie enthält Originaltext).

Vorlage: GAEB-[PROJEKT_004].X83 (50 Positionen, GAEB DA XML 3.2). Die Vorlage bleibt bis auf zwei neue Abschnitte
unverändert:
  98  „Demo B7: Zulage am Abschnittsanfang“                       Nr. 15
  99  „Demo B7: eingebaute Fälle“                                 Nr. 1–14, 16–19
Jeder eingebaute Text ist erfunden und als Demo erkennbar (Abschnittstitel). FAELLE nennt je Prüfung die OZ, an der
der Fall steht; der Test (src/test_demo_lv.py) prüft, dass jede Prüfung dort anschlägt. Nr. 17 (Rechenprüfung,
Block B1e, noch kein Modul): Menge 10 × EP 5,00 = 50,00, im LV steht GP 60,00.
Gleiche Vorlage und gleicher Code ergeben dieselbe Datei (Bytes), E14.

Aufruf (aus der Projektwurzel): python src/demo_lv.py <data/raw> <zielordner>
"""
import copy
import hashlib
import json
import sys
from pathlib import Path

from lxml import etree

VORLAGE = "GAEB-[PROJEKT_004].X83"
ZIEL = "Demo-LV_B7_[PROJEKT_004].X83"
NS = "http://www.gaeb.de/GAEB_DA_XML/DA83/3.2"

# (RNoPart, Kurztext, Langtext, Menge, Einheit, Extras) – Extras: provis, psch, bild, up/it
POS_99 = [
    ("0001", "Druckrohr PE-HD DN 150", "Druckrohr PE-HD DN 200 liefern und im Rohrgraben verlegen.", "20", "m", {}),
    ("0002", "Fundament Beton C25/30", "Ortbeton C30/37 für Einzelfundament herstellen.", "5", "m3", {}),
    ("0003", "Schachtabdeckung reinigen", "Schachtabdeckung reinigen und gangbar machen.", None, "St", {}),
    ("0004", "Leitung spülen", "Leitung nach Fertigstellung spülen.", "1", "St", {}),
    ("0004", "Leitung prüfen", "Druckprüfung der Leitung durchführen.", "1", "St", {}),
    ("0005", "Fels lösen", "Fels der Felsklasse 7 lösen und laden.", "10", "m3", {"provis": "WithoutTotal"}),
    ("0006", "Wasserhaltung Demo", "Wasserhaltung für die gesamte Bauzeit, Abrechnung nach Aufwand.", "1", "psch",
     {"psch": True}),
    ("0007", "Schieber DN 100", "Absperrschieber DN 100, Fabrikat VAG oder gleichwertig, liefern und einbauen.",
     "2", "St", {}),
    ("0008", "Anschluss Bestand", "Anschluss an die bestehende Leitung DN 150 herstellen.", "1", "St", {}),
    ("0009", "Bauschutt laden", "Bauschutt laden, abfahren und fachgerecht entsorgen.", "3", "t", {}),
    ("0010", "Bauzaun", "Bauzaun aufstellen, vorhalten, ggf. umsetzen und wieder abbauen.", "200", "mWo", {}),
    ("0011", "wie vor, jedoch Bauzaun H 2,5 m", "wie vor, jedoch Bauzaun H 2,5 m.", "50", "mWo", {}),
    ("0012", "Facharbeiter", "Stundenlohnarbeiten durch Facharbeiter auf Anordnung der Bauleitung.", "10", "h", {}),
    ("0013", "Anschlussstück Sonderform", "Anschlussstück in Sonderform nach Skizze herstellen.", "1", "St",
     {"bild": True}),
    ("0014", "Rinnenplatte 30 cm", "Rinnenplatte aus Beton, 30 cm breit, in Mörtelbett verlegen.", "10", "m", {}),
    ("0015", "Randstreifen ansäen", "Randstreifen mit Regelsaatgut ansäen.", "40", "m2", {}),
    ("0016", "Rinnenplatte 30 cm", "Rinnenplatte aus Beton, 30 cm breit, in Mörtelbett verlegen.", "25", "m", {}),
    ("0017", "Bordstein setzen", "Bordstein aus Beton auf Betonfundament setzen.", "10", "m", {"up": "5.00", "it": "60.00"}),
    ("0018", "Pflaster aufnehmen", "Pflaster aufnehmen und seitlich lagern.", "1", "m2", {}),
]
POS_98 = [
    ("0001", "Zulage Felsklasse 7", "Zulage für das Lösen von Fels der Klasse 7.", "5", "m3", {}),
    ("0002", "Fels lösen Klasse 7", "Fels der Klasse 7 lösen, laden und abfahren.", "5", "m3", {}),
]
FAELLE = {1: "99.0001", 2: "99.0002", 3: "99.0003", 4: "99.0004", 5: "99.0005", 6: "99.0006", 7: "99.0007",
          8: "99.0008", 9: "99.0009", 10: "99.0010", 11: "99.0010", 12: "99.0011", 13: "99.0012", 14: "99.0013",
          15: "98.0001", 16: "99.0014", 17: "99.0017", 18: "99.0018", 19: "99.0002"}


def _e(tag, parent=None, text=None, **attr):
    el = etree.SubElement(parent, f"{{{NS}}}{tag}", **attr) if parent is not None else etree.Element(f"{{{NS}}}{tag}", **attr)
    if text is not None:
        el.text = text
    return el


def _text(parent, tag, text):
    t = _e(tag, parent)
    p = _e("p", t)
    _e("span", p, text)
    return t


def _item(itemlist, nummer, rno, kurz, lang, menge, einheit, extra):
    it = _e("Item", itemlist, ID=f"demo{nummer}_{rno}_{len(itemlist)}", RNoPart=rno)
    if extra.get("provis"):
        _e("Provis", it, extra["provis"])
    if extra.get("psch"):
        _e("LumpSumItem", it, "Yes")
    if menge is not None:
        _e("Qty", it, f"{float(menge):.3f}")
    _e("QU", it, einheit)
    if extra.get("up"):
        _e("UP", it, extra["up"])
        _e("IT", it, extra["it"])
    desc = _e("Description", it)
    ct = _e("CompleteText", desc)
    det = _e("DetailTxt", ct)
    t = _text(det, "Text", lang)
    if extra.get("bild"):
        _e("image", t[0], Name="demo_skizze.png")
    ol = _e("OutlTxt", _e("OutlineText", ct))
    _text(ol, "TextOutlTxt", kurz)
    return it


def _abschnitt(body, rno, titel, positionen):
    ctgy = _e("BoQCtgy", body, ID=f"demo{rno}", RNoPart=rno)
    lbl = _e("LblTx", ctgy)
    _e("span", _e("p", lbl), titel)
    il = _e("Itemlist", _e("BoQBody", ctgy))
    for rno_pos, kurz, lang, menge, einheit, extra in positionen:
        _item(il, rno, rno_pos, kurz, lang, menge, einheit, extra)


def erzeuge(raw_ordner, ziel_ordner):
    """Schreibt die Demo-Datei und demo_faelle.json; Rückgabe Pfad der Demo-Datei. Ziel nie in data/raw."""
    quelle = Path(raw_ordner) / VORLAGE
    ziel_ordner = Path(ziel_ordner)
    if ziel_ordner.resolve().is_relative_to(Path(raw_ordner).resolve()):
        raise ValueError("Ziel darf nicht in data/raw liegen (E11)")
    baum = etree.parse(str(quelle), etree.XMLParser(huge_tree=True, remove_blank_text=False))
    root = copy.deepcopy(baum.getroot())
    body = root.find(f".//{{{NS}}}BoQ/{{{NS}}}BoQBody")
    _abschnitt(body, "98", "Demo B7: Zulage am Abschnittsanfang", POS_98)
    _abschnitt(body, "99", "Demo B7: eingebaute Fälle", POS_99)
    ziel_ordner.mkdir(parents=True, exist_ok=True)
    pfad = ziel_ordner / ZIEL
    pfad.write_bytes(etree.tostring(root, xml_declaration=True, encoding="UTF-8"))
    (ziel_ordner / "demo_faelle.json").write_text(json.dumps(
        {"datei": ZIEL, "vorlage": VORLAGE, "vorlage_sha256": hashlib.sha256(quelle.read_bytes()).hexdigest(),
         "faelle": {str(k): v for k, v in FAELLE.items()}}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return pfad


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("Aufruf: python src/demo_lv.py <data/raw> <zielordner>")
    print("geschrieben:", erzeuge(sys.argv[1], sys.argv[2]))
