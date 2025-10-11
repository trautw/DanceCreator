/* static/app.js
   JavaScript-Frontend-Logik für die DanceTreeApp.

   Verantwortlichkeiten:
   - Lädt die Struktur vom Backend-Endpunkt /tree?file=...
   - Baut eine einfache Figurenliste (links) und eine Baumdarstellung (rechts)
   - Zeigt Statusmeldungen in der Toolbar
   - Die zentrale Tanzfläche bleibt leer (Platzhalter) — spätere Implementierung
*/

/**
 * Hilfsfunktion: holt die Tree-Daten vom Server.
 * Erwartet eine flache Node-Liste (id, parent_id, name, type, meta).
 */
async function fetchTree(filename) {
  const url = '/tree?file=' + encodeURIComponent(filename);
  const res = await fetch(url);
  if (!res.ok) {
    const err = await res.json().catch(()=>({error:res.statusText}));
    throw new Error(err.error || res.statusText || 'Fehler beim Laden');
  }
  return await res.json();
}

/**
 * Baut aus einer flachen Node-Liste eine verschachtelte Struktur.
 * Gibt das Root-Objekt zurück (das parent_id === null hat).
 */
function buildNested(nodes) {
  const map = new Map();
  nodes.forEach(n => map.set(n.id, {...n, children: []}));
  let root = null;
  map.forEach(n => {
    if (n.parent_id === null) {
      root = n;
    } else if (map.has(n.parent_id)) {
      map.get(n.parent_id).children.push(n);
    }
  });
  return root;
}

/**
 * Wandelt die flache Node-Liste in das jsTree-Format um.
 * jsTree erwartet: [{ id, parent, text, data, ... }]
 */
function toJsTreeData(nodes) {
  return nodes.map(n => ({
    id: n.id,
    parent: n.parent_id === null ? '#' : n.parent_id,
    text: n.name || ('Knoten ' + n.id),
    type: n.type || 'default',
    data: n.meta || {}
  }));
}

/**
 * Initialisiert jsTree im treeContainer mit den übergebenen Daten.
 */
function renderJsTree(nodes) {
  const treeData = toJsTreeData(nodes);
  const treeContainer = $('#treeContainer');
  treeContainer.jstree('destroy'); // Vorherigen Baum entfernen
  treeContainer.jstree({
    core: {
      data: treeData,
      check_callback: true
    },
    plugins: ['types', 'dnd', 'wholerow'],
    types: {
      default: { icon: 'jstree-icon jstree-file' },
      simple: { icon: 'jstree-icon jstree-file' },
      complex: { icon: 'jstree-icon jstree-folder' }
    }
  });
}

/**
 * Holt alle Figuren-Dateien aus /Figures und analysiert sie.
 * Erwartet ein Backend-Endpoint /figures, der eine Liste aller Figuren liefert.
 * Sortiert und trennt nach simple/complex.
 */
async function fetchAndRenderFigureList() {
  const ul = document.getElementById('figureList');
  ul.innerHTML = '<li>Lade Figuren ...</li>';
  try {
    // Hole alle Figuren-Dateinamen und deren Typen vom Backend
    const res = await fetch('/figures');
    if (!res.ok) throw new Error('Fehler beim Laden der Figurenliste');
    const figures = await res.json(); // [{name, type, desc, ...}]
    // Sortiere und trenne nach Typ
    const simple = figures.filter(f => f.type === 'simple').sort((a,b)=>a.name.localeCompare(b.name));
    const complex = figures.filter(f => f.type === 'complex').sort((a,b)=>a.name.localeCompare(b.name));
    ul.innerHTML = '';
    // Simple Figuren
    if (simple.length) {
      const h = document.createElement('li');
      h.textContent = 'Einfache Figuren:';
      h.style.fontWeight = 'bold';
      ul.appendChild(h);
      simple.forEach(f => {
        const li = document.createElement('li');
        li.textContent = f.name;
        li.title = f.desc || '';
        ul.appendChild(li);
      });
    }
    // Complexe Figuren
    if (complex.length) {
      const h = document.createElement('li');
      h.textContent = 'Komplexe Figuren:';
      h.style.fontWeight = 'bold';
      ul.appendChild(h);
      complex.forEach(f => {
        const li = document.createElement('li');
        li.textContent = f.name;
        li.title = f.desc || '';
        ul.appendChild(li);
      });
    }
    if (!simple.length && !complex.length) {
      ul.innerHTML = '<li>Keine Figuren gefunden.</li>';
    }
  } catch (err) {
    ul.innerHTML = '<li>Fehler: ' + err.message + '</li>';
  }
}

/**
 * Setzt einen kurzen Statustext in der Toolbar.
 */
function setStatus(text) {
  const el = document.getElementById('status');
  if (el) el.textContent = text;
}

/**
 * Haupt-Load-Funktion: liest den Dateinamen aus dem Input-Feld,
 * ruft fetchTree auf und füllt die Bereiche.
 */
async function loadAndRender() {
  const input = document.getElementById('fileInput');
  let fname = input.value.trim() || 'HLReelAD';
  if (!fname.endsWith('.json')) {
    fname += '.json';
  }
  setStatus('Lade ' + fname + ' ...');
  try {
    const nodes = await fetchTree(fname);
    // Figurenliste links: alle Figuren aus /Figures
    fetchAndRenderFigureList();
    // Baumstruktur rechts: jsTree
    renderJsTree(nodes || []);
    setStatus('Datei geladen: ' + fname);
  } catch (err) {
    console.error(err);
    setStatus('Fehler: ' + err.message);
    // Wenn Fehler, zeige kurze Nachricht im Tree-Container
    const treeContainer = document.getElementById('treeContainer');
    treeContainer.innerHTML = '<div style="color:crimson">Fehler: ' + err.message + '</div>';
    const ul = document.getElementById('figureList');
    ul.innerHTML = '';
  }
}

/**
 * Event-Handler: Klick auf den 'Laden'-Button
 */
document.addEventListener('DOMContentLoaded', function() {
  document.getElementById('loadButton').addEventListener('click', loadAndRender);
  // Laden beim ersten Aufruf
  loadAndRender();
});
