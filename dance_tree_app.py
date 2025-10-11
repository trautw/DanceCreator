"""
DanceTreeApp - ein kleines Flask-Backend für die HTML5-GUI.

Beschreibung:
 - Liefert die HTML-Seite (templates/index.html)
 - Stellt statische Dateien unter /static bereit (style.css, app.js)
 - Bietet einen einfachen API-Endpunkt /tree, der eine JSON-Datei (aus ./Figures)
   einliest und als flache Liste von Knoten mit id/parent_id zurückgibt.

Anleitung:
1. Kopiere diese Ordnerstruktur in dein Projekt oder nutze sie standalone:
    DanceTreeApp/
    ├── dance_tree_app.py
    ├── templates/
    │   └── index.html
    ├── static/
    │   ├── style.css
    │   └── app.js
    └── Figures/         <-- JSON-Dateien hier ablegen (z. B. HLReelAD.json)

2. Abhängigkeiten installieren:
    pip install flask

3. Starten:
    python dance_tree_app.py

4. Öffne im Browser:
    http://127.0.0.1:5000

Hinweis:
 - Die GUI zeigt links die Figurenliste und rechts die Baumstruktur.
 - Die mittlere Tanzfläche ist ein Platzhalter (keine Drag&Drop-Funktionalität).
 - Diese Datei ist ausführlich kommentiert; passe die Parserlogik im Bereich `build_tree_from_json`
   an, falls deine JSON-Struktur stärker von den Beispielen abweicht.
"""

from flask import Flask, jsonify, request, render_template, send_from_directory
import json
import os
from itertools import count
from typing import Any, Dict, List, Optional

app = Flask(__name__, template_folder="templates", static_folder="static")

# Ordner, in dem der Benutzer seine JSON-Files ablegen soll
FIGURES_DIR = os.path.join(os.path.dirname(__file__), "Figures")

def build_tree_from_json(data: Any) -> List[Dict[str, Any]]:
    """
    Konvertiert eine geladene JSON-Struktur in eine flache Liste von Knoten.
    Jeder Knoten ist ein Dict mit:
      - id: eindeutige Nummer
      - parent_id: id des Elternknotens oder None
      - name: Anzeigetext
      - type: 'root'|'complex'|'simple'|'step'|'unknown'
      - meta: zusätzliches Metadaten-Dict (z. B. 'anchor')

    Die Funktion versucht mehrere übliche Formate zu erkennen:
      - Top-Level-Dict mit 'FigureList'
      - Einfache Figuren-Formen wie [[x,y], ["Name", ...]]
      - Listen von Unterfiguren (sequenziell/parallel)
    """
    id_gen = count(1)
    nodes: List[Dict[str, Any]] = []

    def new_node(name: str, parent: Optional[int], node_type: str, meta: Optional[Dict]=None) -> int:
        nid = next(id_gen)
        nodes.append({
            "id": nid,
            "parent_id": parent,
            "name": name,
            "type": node_type,
            "meta": meta or {}
        })
        return nid

    def parse_item(item: Any, parent: Optional[int]) -> None:
        # None => nichts tun
        if item is None:
            return

        # bereits ein Dict (möglicherweise komplex)
        if isinstance(item, dict):
            name = item.get("Name") or item.get("name") or "Figure"
            nid = new_node(name, parent, "complex", {k:v for k,v in item.items() if k != "FigureList"})
            # Nur noch FigureList wird unterstützt
            if "FigureList" in item:
                parse_item(item["FigureList"], nid)
            return

        # Listen: mehrere Varianten möglich
        if isinstance(item, list):
            # Variante: [mode, [subfigures...]] z. B. ['s', [...]] oder ['sequential', [...]]
            if len(item) == 2 and isinstance(item[0], str) and isinstance(item[1], list):
                mode = item[0]
                name = f"Complex ({mode})"
                nid = new_node(name, parent, "complex", {"mode": mode})
                for sub in item[1]:
                    parse_item(sub, nid)
                return

            # Variante: [[x,y], ["Name", ...]]  (simple figure with anchor and name)
            if (len(item) == 2 and isinstance(item[0], list)
                and (isinstance(item[1], list) or isinstance(item[1], str))):
                anchor = item[0]
                if isinstance(item[1], list):
                    name = item[1][0] if item[1] else "Figure"
                    addons = item[1][1:] if len(item[1]) > 1 else []
                else:
                    name = item[1]
                    addons = []
                new_node(name, parent, "simple", {"anchor": anchor, "addons": addons})
                return

            # Fallback: liste von Unterelementen -> rekursiv verarbeiten
            for sub in item:
                parse_item(sub, parent)
            return

        # Sonst: primitive Werte in einen Leaf-Knoten verwandeln
        new_node(str(item), parent, "unknown", {"raw": item})

    # Root-Knoten anlegen
    root_name = "Dance"
    if isinstance(data, dict):
        root_name = data.get("Name", root_name)
    root_id = new_node(root_name, None, "root", {})

    # Bevorzugt FigureList, falls vorhanden
    if isinstance(data, dict) and "FigureList" in data:
        parse_item(data["FigureList"], root_id)
    else:
        # sonst versuche die ganze Datei als komplexe Struktur zu parsen
        parse_item(data, root_id)

    return nodes

@app.route("/")
def index():
    """
    Liefert die Hauptseite (templates/index.html).
    """
    return render_template("index.html")

@app.route("/tree")
def tree():
    """
    API-Endpunkt:
      GET /tree?file=FILENAME

    Liest die angegebene JSON-Datei aus dem FIGURES_DIR oder verwendet eine Standarddatei
    (HLReelAD.json). Gibt eine JSON-Liste von Knoten zurück.
    Ist keine Datei vorhanden oder leer, wird ein Root-Knoten (type='root') erzeugt.
    """
    fname = request.args.get("file") or "HLReelAD.json"
    candidates = [
        fname,
        os.path.join(FIGURES_DIR, fname),
        os.path.join(os.path.dirname(__file__), fname)
    ]
    data = None
    for c in candidates:
        if os.path.isfile(c):
            with open(c, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except Exception:
                    data = None
            break

    if data is None:
        # Keine Datei gefunden oder Datei leer/fehlerhaft: Root-Knoten erzeugen
        nodes = [{
            "id": 1,
            "parent_id": None,
            "name": "Dance (leer)",
            "type": "root",
            "meta": {}
        }]
        return jsonify(nodes)

    nodes = build_tree_from_json(data)
    # Falls build_tree_from_json keine Knoten liefert, Root-Knoten erzeugen
    if not nodes:
        nodes = [{
            "id": 1,
            "parent_id": None,
            "name": "Dance (leer)",
            "type": "root",
            "meta": {}
        }]
    return jsonify(nodes)

@app.route('/figures')
def figures():
    """
    Liefert eine Liste aller Figuren im Figures-Verzeichnis.
    Für jede Figur werden Name, Typ (simple/complex) und Beschreibung extrahiert.
    Nur noch FigureList wird für komplexe Figuren akzeptiert.
    """
    result = []
    for fname in sorted(os.listdir(FIGURES_DIR)):
        if not fname.endswith('.json'):
            continue
        fpath = os.path.join(FIGURES_DIR, fname)
        try:
            with open(fpath, encoding='utf-8') as f:
                data = json.load(f)
            # Name extrahieren
            name = data.get('Name') or data.get('name') or fname[:-5]
            # Beschreibung extrahieren
            desc = data.get('Desc') or data.get('desc') or ''
            # Typ bestimmen: simple, complex, unknown
            if 'FigureList' in data:
                ftype = 'complex'
            elif 'Addons' in data or 'addons' in data:
                ftype = 'simple'
            else:
                # Heuristik: Wenn es ein Feld gibt, das eine Liste von Figuren enthält
                if any(isinstance(v, list) and v and isinstance(v[0], dict) for v in data.values()):
                    ftype = 'complex'
                else:
                    ftype = 'simple'
            result.append({
                'name': name,
                'type': ftype,
                'desc': desc,
                'filename': fname
            })
        except Exception as e:
            # Fehlerhafte Datei überspringen
            continue
    return jsonify(result)

if __name__ == "__main__":
    # Sicherstellen, dass das Figures-Verzeichnis existiert
    os.makedirs(FIGURES_DIR, exist_ok=True)
    print("Starte DanceTreeApp (Flask). Lege JSON-Dateien in das Verzeichnis 'Figures'.")
    app.run(debug=True)
