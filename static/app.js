// Minimal port of the tkinter UI to a web app.
// Data model: a root array `figures` containing the Dance root.

const api = {
  list: () => fetch('/api/list').then(r=>r.json()),
  load: (filename) => fetch(`/api/load?filename=${encodeURIComponent(filename)}`).then(r=>r.json()),
  save: (data, filename) => fetch(`/api/save?filename=${encodeURIComponent(filename)}`, {
    method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(data)
  }).then(r=>r.json())
}

let figures = [];

function makeDanceRoot() {
  return { type: 'complex', name: 'Dance', Anchor: [0,0], mode: 'sequential', figures: [] };
}

// Init
window.addEventListener('load', async ()=>{
  const canvas = document.getElementById('canvas');
  document.getElementById('btnAddSimple').onclick = ()=>addSimple(figures[0]);
  document.getElementById('btnAddComplex').onclick = ()=>addComplex(figures[0]);
  document.getElementById('btnSave').onclick = saveCurrent;
  document.getElementById('btnLoad').onclick = loadFromSelect;

  // load file list
  refreshFileList();

  // initial model
  figures = [makeDanceRoot()];
  render();

  // global click to dismiss context menus
  document.addEventListener('click', ()=>closeContextMenu());
});

async function refreshFileList(){
  const list = document.getElementById('fileList');
  try{
    const files = await api.list();
    list.innerHTML = '';
    files.forEach(f=>{
      const o = document.createElement('option'); o.value = f; o.textContent = f;
      list.appendChild(o);
    })
  }catch(e){ console.warn('Could not list files', e) }
}

function render(){
  const canvas = document.getElementById('canvas');
  canvas.innerHTML = '';
  figures.forEach((fig, idx)=>{
    const el = renderFigure(fig, null, idx);
    canvas.appendChild(el);
  })
}

function renderFigure(fig, parent, index, parentFigures){
  const el = document.createElement('div');
  el.className = 'box ' + (fig.type === 'simple' ? 'simple' : 'complex');
  el.dataset.index = index;
  el.dataset.type = fig.type;
  el.style.width = 'fit-content';
  el.style.minWidth = '80px';
  el.style.minHeight = '40px';
  el.style.position = 'relative';
  el.style.boxSizing = 'border-box';
  // Kontextmenü: immer tiefste Figur treffen
  el.addEventListener('contextmenu', (ev)=>{
    ev.preventDefault();
    ev.stopPropagation();
    openContextMenu(ev.clientX, ev.clientY, fig, parent);
  });
  el.ondblclick = ()=>{ editFigureName(fig); };
  // Drag & Drop: Drag-Quelle speichern
  el.draggable = true;
  el.ondragstart = (ev)=>{
    window._dragged = { figure: fig, parent, index, parentFigures };
    ev.dataTransfer.setData('text/plain', 'dance-figure');
  };
  // Titel
  const title = document.createElement('div'); title.className='title'; title.textContent = fig.name || '(unnamed)';
  el.appendChild(title);
  // Für komplexe Figuren: Subfiguren + Drop-Zonen
  if(fig.type === 'complex'){
    const mode = document.createElement('div'); mode.textContent = `Mode: ${fig.mode}`; mode.style.fontSize='12px'; el.appendChild(mode);
    const sub = document.createElement('div');
    sub.className = fig.mode === 'sequential' ? 'container-row' : 'container-col';
    sub.style.padding = '6px';
    el.appendChild(sub);

    // Drop-Zone am Anfang
    sub.appendChild(makeDropZone(fig, 0));
    (fig.figures||[]).forEach((subfig, i)=>{
      const childEl = renderFigure(subfig, fig, i, fig.figures);
      sub.appendChild(childEl);
      // Drop-Zone nach jedem Kind
      sub.appendChild(makeDropZone(fig, i+1));
    });
  }
  return el;
}

function makeDropZone(targetFig, insertIdx){
  const dz = document.createElement('div');
  dz.className = 'drop-zone';
  dz.style.height = '12px';
  dz.style.margin = '2px 0';
  dz.ondragover = (ev)=>{ ev.preventDefault(); dz.style.background='#3b82f6'; };
  dz.ondragleave = ()=>{ dz.style.background=''; };
  dz.ondrop = (ev)=>{
    ev.preventDefault(); dz.style.background='';
    const dragged = window._dragged;
    if(!dragged) return;
    // Nur innerhalb komplexer Figuren erlaubt
    if(!targetFig.figures) targetFig.figures = [];
    // Entferne aus altem Parent
    if(dragged.parent && dragged.parent.figures){
      const idx = dragged.parent.figures.indexOf(dragged.figure);
      if(idx>=0) dragged.parent.figures.splice(idx,1);
    } else if(dragged.parentFigures) {
      const idx = dragged.parentFigures.indexOf(dragged.figure);
      if(idx>=0) dragged.parentFigures.splice(idx,1);
    }
    // Füge an neuer Position ein
    targetFig.figures.splice(insertIdx,0,dragged.figure);
    window._dragged = null;
    render();
  };
  return dz;
}

function openContextMenu(x,y,fig,parent){
  closeContextMenu();
  const menu = document.createElement('div'); menu.className='context-menu'; menu.style.left = x + 'px'; menu.style.top = y + 'px';
  const addBtn = (label, cb) => { const b = document.createElement('button'); b.textContent = label; b.onclick = (ev)=>{ ev.stopPropagation(); cb(); closeContextMenu(); }; menu.appendChild(b); };
  addBtn('Info', ()=>showInfo(fig));
  addBtn('Edit Name', ()=>editFigureName(fig));
  if(fig.type !== 'complex' || fig.name !== 'Dance') addBtn('Remove', ()=>removeFigure(fig, parent));
  if(fig.type === 'complex'){
    addBtn('Change Mode', ()=>changeModeDialog(fig));
    addBtn('Add Simple', ()=>addSimple(fig));
    addBtn('Add Complex', ()=>addComplex(fig));
  }
  addBtn('Save', ()=>saveFigureDialog(fig));
  addBtn('Load into', ()=>loadIntoDialog(fig));
  document.body.appendChild(menu);
}
function closeContextMenu(){ document.querySelectorAll('.context-menu').forEach(c=>c.remove()); }

function showInfo(fig){
  alert(JSON.stringify(fig, null, 2));
}

function editFigureName(fig){
  const name = prompt('Figure name:', fig.name||'');
  if(name !== null){ fig.name = name; render(); }
}

function removeFigure(fig, parent){
  if(!parent){ const idx = figures.indexOf(fig); if(idx>=0) figures.splice(idx,1); }
  else{ const idx = parent.figures.indexOf(fig); if(idx>=0) parent.figures.splice(idx,1); }
  render();
}

function changeModeDialog(fig){
  const mode = prompt('Mode (sequential/parallel):', fig.mode||'sequential');
  if(mode === 'sequential' || mode === 'parallel'){ fig.mode = mode; render(); }
}

function addSimple(parent){
  const name = prompt('Simple figure name:');
  if(!name) return;
  const f = { type: 'simple', name, Anchor:[1,1], _Addons: [] };
  parent.figures = parent.figures || [];
  parent.figures.push(f);
  render();
}
function addComplex(parent){
  const name = prompt('Complex figure name:');
  if(!name) return;
  const f = { type: 'complex', name, Anchor:[1,1], mode:'sequential', figures: [] };
  parent.figures = parent.figures || [];
  parent.figures.push(f);
  render();
}

function saveFigureDialog(fig){
  const filename = prompt('Save filename:', fig.name || 'figure');
  if(!filename) return;
  const data = serializeFigure(fig);
  api.save(data, filename).then(res=>{
    if(res.error) alert('Save error: '+res.error); else { alert('Saved as '+res.filename); refreshFileList(); }
  }).catch(e=>alert('Save failed: '+e));
}

function serializeFigure(fig){
  if(fig.type === 'simple'){
    return { Version: 1, Name: fig.name, Anchor: fig.Anchor || [1,1], Addons: (fig._Addons||[]).map(a=>a.name||'') };
  }
  return { Version: 3, Name: fig.name, Desc: fig.desc||'', Anchor: fig.Anchor||[0,0], FigureList: buildFigureList(fig) };
}

function buildFigureList(fig){
  if(fig.type === 'simple'){
    return [[fig.Anchor?.[0]||1, fig.Anchor?.[1]||1], [fig.name||'', (fig._Addons || []).map(a=>a.name||'')]];
  }else{
    const mode = fig.mode === 'sequential' ? 's' : 'p';
    const sub = (fig.figures||[]).map(buildFigureList);
    return [mode, sub];
  }
}

function loadFromSelect(){
  const sel = document.getElementById('fileList');
  if(!sel.value) return alert('No file selected');
  api.load(sel.value).then(data=>{
    try{
      const parsed = deserializeRoot(data);
      figures = [parsed];
      render();
    }catch(e){ alert('Load/parse error: '+e); }
  }).catch(e=>alert('Load failed: '+e));
}

function saveCurrent(){
  const root = figures[0];
  const filename = prompt('Save dance as:', root.name || 'Dance');
  if(!filename) return;
  const data = serializeFigure(root);
  api.save(data, filename).then(res=>{ if(res.error) alert('Save error: '+res.error); else { alert('Saved: '+res.filename); refreshFileList(); } }).catch(e=>alert(e));
}

function deserializeRoot(data){
  function parse(fl){
    if(Array.isArray(fl) && fl.length === 2 && Array.isArray(fl[0]) && Array.isArray(fl[1]) && typeof fl[1][0] === 'string'){
      const name = fl[1][0]; const anchor = fl[0]; const addons = fl[1][1] || [];
      return { type:'simple', name, Anchor: anchor, _Addons: addons.map(a=>({type:'simple', name:a})) };
    }
    if(Array.isArray(fl) && fl.length === 2 && typeof fl[0] === 'string' && (fl[0] === 's' || fl[0] === 'p')){
      const mode = fl[0] === 's' ? 'sequential' : 'parallel';
      const node = { type:'complex', name:'', Anchor:[0,0], mode, figures: [] };
      node.figures = (fl[1]||[]).map(parse);
      return node;
    }
    throw new Error('Unknown FigureList format');
  }

  if(data.FigureList){
    const root = { type:'complex', name: data.Name || 'Dance', Anchor: data.Anchor || [0,0], mode: 'sequential', figures: [] };
    const parsed = parse(data.FigureList);
    if(parsed.type === 'complex') root.figures = parsed.figures; else root.figures = [parsed];
    return root;
  }
  if(data.Name && !data.FigureList) return { type:'simple', name:data.Name, Anchor: data.Anchor || [0,0] };
  throw new Error('Unsupported file format');
}

function loadIntoDialog(fig){
  const sel = document.getElementById('fileList');
  const filename = sel.value;
  if(!filename) return alert('Select a file in the dropdown to load into this figure.');
  api.load(filename).then(data=>{
    try{
      const parsed = deserializeRoot(data);
      if(parsed.type === 'complex'){
        fig.figures = fig.figures || [];
        fig.figures.push(...parsed.figures);
      }else{
        fig.figures = fig.figures || [];
        fig.figures.push(parsed);
      }
      render();
    }catch(e){ alert('Load/parse error: '+e); }
  }).catch(e=>alert('Load failed: '+e));
}