(function () {
  const vscode = acquireVsCodeApi();
  const $ = id => document.getElementById(id);
  const canvas = $('canvas'), scene = $('scene'), nodesLayer = $('nodes'), edgesLayer = $('edges');
  const inspector = $('inspector'), statusEl = $('status'), banner = $('banner'), menu = $('menu'), emptyEl = $('empty');
  const svgNS = 'http://www.w3.org/2000/svg';
  const NODE_WIDTH = 240, GAP_X = 70, GAP_Y = 24;
  const CATEGORY_COLORS = { rule: '#e08a2e', container: '#a070e0', modifier: '#3794ff', leaf: '#4cae6a' };

  const saved = vscode.getState() || {};
  let positions = saved.positions || {};
  let view = saved.view || { x: 20, y: 20, k: 1 };
  let features = [], templates = [], version = 0, invalid = null;
  let selection = null, pendingFocus = null, pendingRename = null, inspectorSignature = '';
  let graph = { nodes: [], links: [] };
  const cards = new Map();   // node key -> { el, anchors: { in, out: Map(link id -> point) } }
  const edgeEls = new Map(); // link id -> path
  const drafts = new Map();  // node key -> { base, raw }
  let persistTimer, statusTimer, busyTimer, busy = false, fitted = !!saved.view;

  // ------------------------------------------------------------------------------ //
  // Small helpers
  // ------------------------------------------------------------------------------ //
  function el(tag, text, className) {
    const node = document.createElement(tag);
    if (text !== undefined) node.textContent = text;
    if (className) node.className = className;
    return node;
  }
  function svg(tag, attrs = {}) {
    const node = document.createElementNS(svgNS, tag);
    for (const [name, value] of Object.entries(attrs)) node.setAttribute(name, value);
    return node;
  }
  function button(text, onClick, className) {
    const node = el('button', text, className);
    node.addEventListener('click', onClick);
    return node;
  }
  function persist() {
    clearTimeout(persistTimer);
    persistTimer = setTimeout(() => vscode.setState({ positions, view }), 200);
  }
  function notify(text, isError) {
    clearTimeout(statusTimer);
    statusEl.textContent = text;
    statusEl.classList.toggle('error', !!isError);
    if (isError) statusTimer = setTimeout(updateStatus, 7000);
  }
  function updateStatus() {
    statusEl.classList.remove('error');
    const count = features.length;
    statusEl.textContent = `${count} feature${count === 1 ? '' : 's'}, ${graph.links.length} connection${graph.links.length === 1 ? '' : 's'}`;
  }
  function send(type, data = {}) {
    if (invalid && type !== 'openText') {
      notify('Fix the syntax error in the text editor first.', true);
      return false;
    }
    // Edits target feature indexes from the last document the editor saw, so only one may be in flight.
    if (type !== 'openText') {
      if (busy) { notify('Still applying the previous change…', false); return false; }
      busy = true;
      clearTimeout(busyTimer);
      busyTimer = setTimeout(() => { busy = false; }, 4000);
    }
    vscode.postMessage({ type, version, ...data });
    return true;
  }
  function settle() {
    busy = false;
    clearTimeout(busyTimer);
  }
  function templateOf(type) {
    return templates.find(item => item.type === type);
  }
  function typeLabel(type) {
    return templateOf(type)?.label || (type ? type.replace(/^minecraft:/, '') : 'Invalid feature');
  }
  function isTyping(target) {
    return target && (['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName) || target.isContentEditable);
  }

  // ------------------------------------------------------------------------------ //
  // Graph model
  // ------------------------------------------------------------------------------ //
  function problemsOf(feature, counts) {
    const list = [];
    if (!feature.type) list.push('Needs format_version and exactly one feature type.');
    if (!feature.id) list.push('Missing description.identifier.');
    else if (counts.get(feature.id) > 1) list.push('Another feature uses the same identifier.');
    return list;
  }
  function buildGraph() {
    const counts = new Map();
    features.forEach(feature => { if (feature.id) counts.set(feature.id, (counts.get(feature.id) || 0) + 1); });
    const keyOf = feature => (feature.id && counts.get(feature.id) === 1 ? feature.id : `${feature.id || '?'}#${feature.index}`);
    const nodes = features.map(feature => ({ key: keyOf(feature), feature, problems: problemsOf(feature, counts) }));
    const byId = new Map(nodes.filter(node => node.key === node.feature.id).map(node => [node.feature.id, node]));
    const links = [];
    const internal = nodes.slice();
    for (const node of internal) {
      for (const ref of node.feature.refs) {
        let target = byId.get(ref.target);
        if (!target) {
          const key = `ext:${ref.target}`;
          target = nodes.find(item => item.key === key);
          if (!target) {
            target = { key, external: true, target: ref.target, ambiguous: counts.get(ref.target) > 1, referencedBy: [] };
            nodes.push(target);
          }
        }
        if (target.external && !target.referencedBy.includes(node.feature.id || '(unnamed)')) target.referencedBy.push(node.feature.id || '(unnamed)');
        links.push({ id: `${node.key}|${ref.portIndex}|${ref.itemIndex}`, from: node.key, to: target.key, ref, node });
      }
    }
    return { nodes, links };
  }

  // ------------------------------------------------------------------------------ //
  // Rendering the canvas
  // ------------------------------------------------------------------------------ //
  function render() {
    graph = buildGraph();
    nodesLayer.replaceChildren();
    cards.clear();
    for (const node of graph.nodes) cards.set(node.key, createCard(node));
    placeNodes(false);
    applyView();
    measureAnchors();
    renderEdges();
    emptyEl.hidden = graph.nodes.length > 0;
    if (selection && !selectionExists()) selection = null;
    refreshSelection();
    if (!fitted && graph.nodes.length) { fitted = true; fit(); }
  }

  function selectionExists() {
    return selection.kind === 'node' ? cards.has(selection.key) : graph.links.some(link => link.id === selection.id);
  }

  function createCard(node) {
    const card = el('div', undefined, 'node');
    card.dataset.key = node.key;
    card.tabIndex = 0;
    const head = el('div', undefined, 'head');
    head.append(el('span', undefined, 'dot in'));
    const anchors = { out: new Map() };
    if (node.external) {
      card.classList.add('external');
      head.append(el('strong', node.target), el('small', node.ambiguous ? 'Ambiguous: several features share this id' : 'Not defined in this file'));
      card.append(head);
      if (!node.ambiguous) {
        const actions = el('div', undefined, 'ext-actions');
        actions.append(button('Create feature…', event => {
          const rect = event.currentTarget.getBoundingClientRect();
          showMenu(rect.left, rect.bottom, `Create ${node.target}`, type => {
            pendingFocus = { pos: positions[node.key] };
            send('create', { template: type, id: node.target });
          });
        }, 'secondary'));
        card.append(actions);
      }
    } else {
      const feature = node.feature;
      const category = templateOf(feature.type)?.category;
      if (category) card.classList.add(`cat-${category}`);
      if (node.problems.length) card.classList.add('problem');
      const title = el('strong', feature.id || '(no identifier)');
      const subtitle = el('small', typeLabel(feature.type));
      if (node.problems.length) {
        const warn = el('span', ' ⚠', 'warn');
        subtitle.append(warn);
        card.title = node.problems.join('\n');
      }
      head.append(title, subtitle);
      card.append(head);
      const rows = el('div', undefined, 'rows');
      feature.ports.forEach((port, portIndex) => {
        const refs = feature.refs.filter(ref => ref.portIndex === portIndex);
        refs.forEach(ref => rows.append(createRow(node, port, portIndex, ref)));
        if (port.kind !== 'single' || !refs.length) rows.append(createRow(node, port, portIndex, null));
      });
      if (rows.children.length) card.append(rows);
    }
    card.addEventListener('pointerdown', event => startNodeDrag(event, node, card));
    card.addEventListener('keydown', event => {
      if (event.target === card && (event.key === 'Enter' || event.key === ' ')) {
        event.preventDefault();
        select({ kind: 'node', key: node.key });
      }
    });
    nodesLayer.append(card);
    cards.set(node.key, { el: card, anchors });
    return { el: card, anchors };
  }

  function createRow(node, port, portIndex, ref) {
    const row = el('div', undefined, `row${ref ? '' : ' empty'}`);
    let label = port.label;
    if (ref && port.kind !== 'single') {
      label = port.kind === 'weighted' ? `× ${ref.weight ?? '?'}` : port.kind === 'conditional' ? (ref.condition ? `if ${ref.condition}` : 'always') : `[${ref.itemIndex}]`;
    } else if (!ref && port.kind !== 'single') label = `+ ${port.label}`;
    const targetEl = el('span', ref ? ref.target : 'drag to connect', 'target');
    if (ref) targetEl.title = ref.target;
    row.append(el('span', label, 'label'), targetEl);
    const dot = el('span', undefined, `dot out${ref ? ' filled' : ''}`);
    dot.title = 'Drag to another feature to connect';
    row.append(dot);
    const itemIndex = ref ? ref.itemIndex : null;
    row.dataset.link = ref ? `${node.key}|${portIndex}|${itemIndex}` : '';
    dot.addEventListener('pointerdown', event => startLinkDrag(event, node, dot, portIndex, itemIndex));
    return row;
  }

  function placeNodes(force) {
    const incoming = new Set(graph.links.map(link => link.to));
    const outgoing = new Map();
    graph.links.forEach(link => outgoing.set(link.from, [...(outgoing.get(link.from) || []), link]));
    const depth = new Map(), order = [], queue = [];
    const run = () => {
      while (queue.length) {
        const key = queue.shift();
        order.push(key);
        for (const link of outgoing.get(key) || []) {
          if (!depth.has(link.to)) { depth.set(link.to, depth.get(key) + 1); queue.push(link.to); }
        }
      }
    };
    const seed = node => { if (!depth.has(node.key)) { depth.set(node.key, 0); queue.push(node.key); run(); } };
    graph.nodes.filter(node => !incoming.has(node.key)).forEach(seed);
    graph.nodes.forEach(seed);
    const columnY = new Map();
    for (const key of order) {
      const column = depth.get(key);
      const y = columnY.get(column) ?? 40;
      if (force || !positions[key]) positions[key] = { x: 40 + column * (NODE_WIDTH + GAP_X), y };
      columnY.set(column, y + cards.get(key).el.offsetHeight + GAP_Y);
    }
    for (const [key, card] of cards) {
      card.el.style.left = `${positions[key].x}px`;
      card.el.style.top = `${positions[key].y}px`;
    }
    persist();
  }

  function measureAnchors() {
    const scale = view.k;
    for (const [key, card] of cards) {
      const box = card.el.getBoundingClientRect();
      const center = dot => {
        const rect = dot.getBoundingClientRect();
        return { x: (rect.left + rect.width / 2 - box.left) / scale, y: (rect.top + rect.height / 2 - box.top) / scale };
      };
      card.anchors.in = center(card.el.querySelector('.dot.in'));
      card.anchors.out = new Map();
      card.el.querySelectorAll('.row').forEach(row => {
        if (row.dataset.link) card.anchors.out.set(row.dataset.link, center(row.querySelector('.dot.out')));
      });
      card.anchors.rows = [...card.el.querySelectorAll('.row')].map(row => ({ link: row.dataset.link, point: center(row.querySelector('.dot.out')), dot: row.querySelector('.dot.out') }));
    }
  }

  function curve(a, b) {
    const bend = Math.max(50, Math.abs(b.x - a.x) / 2);
    return `M ${a.x} ${a.y} C ${a.x + bend} ${a.y}, ${b.x - bend - 8} ${b.y}, ${b.x - 8} ${b.y}`;
  }

  function renderEdges() {
    edgesLayer.replaceChildren();
    edgeEls.clear();
    const defs = svg('defs');
    const marker = svg('marker', { id: 'arrow', viewBox: '0 0 10 10', refX: '9', refY: '5', markerWidth: '7', markerHeight: '7', orient: 'auto' });
    marker.append(svg('path', { d: 'M 0 0 L 10 5 L 0 10 z', class: 'edge-arrow' }));
    defs.append(marker);
    edgesLayer.append(defs);
    for (const link of graph.links) {
      const from = positions[link.from], to = positions[link.to];
      const fromCard = cards.get(link.from), toCard = cards.get(link.to);
      const out = fromCard && fromCard.anchors.out.get(link.id);
      if (!from || !to || !out || !toCard.anchors.in) continue;
      const a = { x: from.x + out.x, y: from.y + out.y };
      const b = { x: to.x + toCard.anchors.in.x, y: to.y + toCard.anchors.in.y };
      const d = curve(a, b);
      const title = svg('title');
      title.textContent = `${link.node.feature.id || '(unnamed)'} → ${link.ref.target} (${link.ref.label})`;
      const hit = svg('path', { d, class: 'edge-hit' });
      hit.append(title.cloneNode(true));
      const path = svg('path', { d, class: `edge${selection && selection.kind === 'edge' && selection.id === link.id ? ' selected' : ''}`, 'marker-end': 'url(#arrow)' });
      hit.addEventListener('click', () => select({ kind: 'edge', id: link.id }));
      edgesLayer.append(hit, path);
      edgeEls.set(link.id, path);
    }
  }

  function applyView() {
    scene.style.transform = `translate(${view.x}px, ${view.y}px) scale(${view.k})`;
    canvas.style.backgroundSize = `${24 * view.k}px ${24 * view.k}px`;
    canvas.style.backgroundPosition = `${view.x}px ${view.y}px`;
    persist();
  }

  function fit() {
    const rect = canvas.getBoundingClientRect();
    if (!graph.nodes.length || !rect.width) { view = { x: 20, y: 20, k: 1 }; applyView(); return; }
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    for (const [key, card] of cards) {
      const pos = positions[key];
      minX = Math.min(minX, pos.x); minY = Math.min(minY, pos.y);
      maxX = Math.max(maxX, pos.x + NODE_WIDTH); maxY = Math.max(maxY, pos.y + card.el.offsetHeight);
    }
    const k = Math.max(0.25, Math.min(1, (rect.width - 80) / (maxX - minX), (rect.height - 80) / (maxY - minY)));
    view = { k, x: Math.max(24, (rect.width - (maxX - minX) * k) / 2) - minX * k, y: Math.max(24, (rect.height - (maxY - minY) * k) / 2) - minY * k };
    applyView();
  }

  function toScene(clientX, clientY) {
    const rect = canvas.getBoundingClientRect();
    return { x: (clientX - rect.left - view.x) / view.k, y: (clientY - rect.top - view.y) / view.k };
  }

  function setPosition(key, pos) {
    positions[key] = { x: Math.max(0, pos.x), y: Math.max(0, pos.y) };
    const card = cards.get(key);
    if (card) {
      card.el.style.left = `${positions[key].x}px`;
      card.el.style.top = `${positions[key].y}px`;
      renderEdges();
    }
    persist();
  }

  // ------------------------------------------------------------------------------ //
  // Selection
  // ------------------------------------------------------------------------------ //
  function select(next) {
    selection = next;
    refreshSelection();
    renderInspector(true);
  }
  function refreshSelection() {
    for (const [key, card] of cards) card.el.classList.toggle('selected', !!selection && selection.kind === 'node' && selection.key === key);
    for (const [id, path] of edgeEls) path.classList.toggle('selected', !!selection && selection.kind === 'edge' && selection.id === id);
  }
  function deleteSelection() {
    if (!selection) return;
    if (selection.kind === 'edge') {
      const link = graph.links.find(item => item.id === selection.id);
      if (link) send('disconnect', { index: link.node.feature.index, portIndex: link.ref.portIndex, itemIndex: link.ref.itemIndex });
      selection = null;
    } else {
      const node = graph.nodes.find(item => item.key === selection.key);
      if (!node || node.external) return;
      send('delete', { index: node.feature.index });
    }
  }

  // ------------------------------------------------------------------------------ //
  // Mouse interaction: pan, zoom, move nodes, drag connections
  // ------------------------------------------------------------------------------ //
  canvas.addEventListener('pointerdown', event => {
    if (event.button !== 0 && event.button !== 1) return;
    hideMenu();
    if (event.target.closest('.node') || event.target.closest('.edge-hit')) return;
    const start = { x: event.clientX, y: event.clientY, vx: view.x, vy: view.y };
    let moved = false;
    canvas.setPointerCapture(event.pointerId);
    canvas.classList.add('panning');
    const move = e => {
      const dx = e.clientX - start.x, dy = e.clientY - start.y;
      if (!moved && Math.abs(dx) + Math.abs(dy) > 3) moved = true;
      if (moved) { view.x = start.vx + dx; view.y = start.vy + dy; applyView(); }
    };
    const up = () => {
      canvas.classList.remove('panning');
      canvas.removeEventListener('pointermove', move);
      canvas.removeEventListener('pointerup', up);
      canvas.removeEventListener('pointercancel', up);
      if (!moved) select(null);
    };
    canvas.addEventListener('pointermove', move);
    canvas.addEventListener('pointerup', up);
    canvas.addEventListener('pointercancel', up);
  });

  canvas.addEventListener('wheel', event => {
    event.preventDefault();
    const rect = canvas.getBoundingClientRect();
    const px = event.clientX - rect.left, py = event.clientY - rect.top;
    const k = Math.max(0.2, Math.min(2, view.k * Math.exp(-event.deltaY * 0.0015)));
    view.x = px - (px - view.x) * (k / view.k);
    view.y = py - (py - view.y) * (k / view.k);
    view.k = k;
    applyView();
  }, { passive: false });

  function startNodeDrag(event, node, card) {
    if (event.button !== 0 || event.target.closest('.dot.out') || event.target.closest('button')) return;
    event.stopPropagation();
    hideMenu();
    if (!selection || selection.kind !== 'node' || selection.key !== node.key) select({ kind: 'node', key: node.key });
    const start = { x: event.clientX, y: event.clientY, pos: { ...positions[node.key] } };
    card.setPointerCapture(event.pointerId);
    const move = e => {
      const dx = (e.clientX - start.x) / view.k, dy = (e.clientY - start.y) / view.k;
      setPosition(node.key, { x: start.pos.x + dx, y: start.pos.y + dy });
    };
    const up = () => {
      card.removeEventListener('pointermove', move);
      card.removeEventListener('pointerup', up);
      card.removeEventListener('pointercancel', up);
    };
    card.addEventListener('pointermove', move);
    card.addEventListener('pointerup', up);
    card.addEventListener('pointercancel', up);
  }

  function startLinkDrag(event, node, dot, portIndex, itemIndex) {
    if (event.button !== 0) return;
    event.stopPropagation();
    event.preventDefault();
    if (invalid) { notify('Fix the syntax error in the text editor first.', true); return; }
    hideMenu();
    const card = cards.get(node.key);
    const row = card.anchors.rows.find(item => item.dot === dot);
    const origin = { x: positions[node.key].x + row.point.x, y: positions[node.key].y + row.point.y };
    const temp = svg('path', { class: 'edge-temp' });
    edgesLayer.append(temp);
    dot.setPointerCapture(event.pointerId);
    dot.classList.add('active');
    canvas.classList.add('linking');
    let hover = null;
    const targetAt = e => {
      const found = document.elementFromPoint(e.clientX, e.clientY);
      return found ? found.closest('.node') : null;
    };
    const move = e => {
      const point = toScene(e.clientX, e.clientY);
      temp.setAttribute('d', `M ${origin.x} ${origin.y} C ${origin.x + 60} ${origin.y}, ${point.x - 60} ${point.y}, ${point.x} ${point.y}`);
      const under = targetAt(e);
      const key = under && under.dataset.key !== node.key ? under.dataset.key : null;
      if (key !== hover) {
        if (hover && cards.has(hover)) cards.get(hover).el.classList.remove('drop-target');
        hover = key;
        if (hover && cards.has(hover)) cards.get(hover).el.classList.add('drop-target');
      }
    };
    const up = e => {
      dot.removeEventListener('pointermove', move);
      dot.removeEventListener('pointerup', up);
      dot.removeEventListener('pointercancel', cancel);
      dot.classList.remove('active');
      canvas.classList.remove('linking');
      temp.remove();
      const dropped = hover;
      if (hover && cards.has(hover)) cards.get(hover).el.classList.remove('drop-target');
      const from = { index: node.feature.index, portIndex, itemIndex };
      const under = targetAt(e);
      if (dropped) connectTo(from, dropped);
      else if (!under && canvas.contains(document.elementFromPoint(e.clientX, e.clientY))) {
        const point = toScene(e.clientX, e.clientY);
        showMenu(e.clientX, e.clientY, 'Create and connect', type => {
          pendingFocus = { pos: point };
          send('create', { template: type, from });
        });
      }
    };
    const cancel = () => {
      dot.removeEventListener('pointermove', move);
      dot.removeEventListener('pointerup', up);
      dot.removeEventListener('pointercancel', cancel);
      dot.classList.remove('active');
      canvas.classList.remove('linking');
      temp.remove();
      if (hover && cards.has(hover)) cards.get(hover).el.classList.remove('drop-target');
    };
    dot.addEventListener('pointermove', move);
    dot.addEventListener('pointerup', up);
    dot.addEventListener('pointercancel', cancel);
    move(event);
  }

  function connectTo(from, targetKey) {
    const target = graph.nodes.find(item => item.key === targetKey);
    if (!target) return;
    const id = target.external ? target.target : target.feature.id;
    if (!target.external && target.key !== target.feature.id) {
      notify('Give the target feature a unique identifier before connecting to it.', true);
      return;
    }
    send('connect', { ...from, target: id });
  }

  // ------------------------------------------------------------------------------ //
  // Pop-up menu for choosing a feature type
  // ------------------------------------------------------------------------------ //
  function showMenu(x, y, title, onPick) {
    menu.replaceChildren(el('div', title, 'title'));
    for (const template of templates) {
      const item = el('button', undefined);
      const swatch = el('span', undefined, 'swatch');
      swatch.style.background = CATEGORY_COLORS[template.category] || '#888';
      item.append(swatch, el('span', template.label));
      item.addEventListener('click', () => { hideMenu(); onPick(template.type); });
      menu.append(item);
    }
    menu.hidden = false;
    menu.style.left = `${Math.max(4, Math.min(x, window.innerWidth - menu.offsetWidth - 8))}px`;
    menu.style.top = `${Math.max(4, Math.min(y, window.innerHeight - menu.offsetHeight - 8))}px`;
    const first = menu.querySelector('button');
    if (first) first.focus();
  }
  function hideMenu() { menu.hidden = true; }
  document.addEventListener('pointerdown', event => { if (!menu.hidden && !menu.contains(event.target)) hideMenu(); }, true);
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape') { hideMenu(); return; }
    if ((event.key === 'Delete' || event.key === 'Backspace') && !isTyping(event.target) && menu.hidden) {
      event.preventDefault();
      deleteSelection();
    }
  });

  // ------------------------------------------------------------------------------ //
  // Inspector
  // ------------------------------------------------------------------------------ //
  function renderInspector(force) {
    const signature = JSON.stringify([selection, features, invalid ? 1 : 0]);
    if (!force && signature === inspectorSignature) return;
    inspectorSignature = signature;
    const active = document.activeElement;
    const field = active && inspector.contains(active) ? active.dataset.field : null;
    const caret = field && active.selectionStart !== undefined ? [active.selectionStart, active.selectionEnd] : null;
    inspector.replaceChildren();
    const node = selection && selection.kind === 'node' ? graph.nodes.find(item => item.key === selection.key) : null;
    const link = selection && selection.kind === 'edge' ? graph.links.find(item => item.id === selection.id) : null;
    if (node && node.external) inspectExternal(node);
    else if (node) inspectFeature(node);
    else if (link) inspectLink(link);
    else inspectHelp();
    if (field) {
      const next = inspector.querySelector(`[data-field="${field}"]`);
      if (next) { next.focus(); if (caret && next.setSelectionRange) next.setSelectionRange(caret[0], caret[1]); }
    }
  }

  function inspectHelp() {
    inspector.append(el('h2', 'MultiFeature graph'));
    const list = el('ul', undefined, 'help');
    [
      'Drag a node to move it. Drag the background to pan, scroll to zoom.',
      'Drag from a dot on the right of a node onto another node to connect them.',
      'Drop a connection on empty space to create a new feature and connect it.',
      'Click a line to select it, then press Delete to remove the connection.',
      'Select a node to rename it, change its connections, or edit its JSON5.',
      'Dashed nodes are referenced but not defined in this file.',
    ].forEach(text => list.append(el('li', text)));
    inspector.append(list, el('h3', 'Feature types'));
    const legend = el('p', undefined, 'muted');
    legend.textContent = 'Orange: feature rules. Purple: lists that branch (aggregate, sequence, weighted, conditional). Blue: modifiers. Green: blocks.';
    inspector.append(legend);
    const problems = graph.nodes.filter(node => node.problems && node.problems.length);
    if (problems.length) {
      inspector.append(el('h3', 'Problems'));
      problems.forEach(node => inspector.append(el('p', `${node.feature.id || `Feature #${node.feature.index + 1}`}: ${node.problems.join(' ')}`, 'warning')));
    }
  }

  function inspectExternal(node) {
    inspector.append(el('h2', node.target), el('p', 'Not defined in this file. It may be a vanilla feature or live in another file.', 'muted'));
    inspector.append(el('h3', 'Referenced by'));
    node.referencedBy.forEach(id => inspector.append(el('p', id)));
    if (!node.ambiguous) {
      inspector.append(el('h3', 'Create it here'));
      const actions = el('div', undefined, 'actions');
      templates.forEach(template => actions.append(button(template.label, () => {
        pendingFocus = { pos: positions[node.key] };
        send('create', { template: template.type, id: node.target });
      }, 'secondary')));
      inspector.append(actions);
    }
  }

  function inspectLink(link) {
    inspector.append(el('h2', 'Connection'));
    inspector.append(el('p', `From ${link.node.feature.id || '(unnamed)'}`), el('p', `To ${link.ref.target}`), el('p', `Field ${link.ref.label}`, 'muted'));
    const actions = el('div', undefined, 'actions');
    actions.append(button('Remove connection', deleteSelection, 'danger'));
    actions.append(button('Select source', () => select({ kind: 'node', key: link.from }), 'secondary'));
    actions.append(button('Select target', () => select({ kind: 'node', key: link.to }), 'secondary'));
    inspector.append(actions);
  }

  function labelled(text, input) {
    const wrap = el('div');
    wrap.append(el('label', text), input);
    return wrap;
  }

  function inspectFeature(node) {
    const feature = node.feature;
    inspector.append(el('h2', feature.id || '(no identifier)'), el('p', typeLabel(feature.type), 'muted'));
    node.problems.forEach(problem => inspector.append(el('p', problem, 'warning')));

    const id = el('input');
    id.value = feature.id;
    id.dataset.field = 'id';
    id.addEventListener('change', () => {
      const next = id.value.trim();
      pendingRename = { from: node.key, to: next };
      if (!send('rename', { index: feature.index, id: next })) pendingRename = null;
    });
    inspector.append(labelled('Identifier (references are updated)', id));
    const fv = el('input');
    fv.value = feature.formatVersion;
    fv.dataset.field = 'fv';
    fv.addEventListener('change', () => send('formatVersion', { index: feature.index, value: fv.value }));
    inspector.append(labelled('Format version', fv));

    const ids = el('datalist');
    ids.id = 'feature-ids';
    graph.nodes.filter(item => !item.external && item.key === item.feature.id && item.key !== node.key).forEach(item => {
      const option = el('option');
      option.value = item.feature.id;
      ids.append(option);
    });
    inspector.append(ids);

    if (!feature.ports.length) {
      inspector.append(el('h3', 'Connections'), el('p', feature.type ? 'This feature does not place other features.' : 'Fix the feature type to see its connections.', 'muted'));
    }
    feature.ports.forEach((port, portIndex) => {
      inspector.append(el('h3', `Connections: ${port.label}`));
      const refs = feature.refs.filter(ref => ref.portIndex === portIndex);
      refs.forEach(ref => {
        const box = el('div', undefined, 'conn');
        const target = el('input');
        target.value = ref.target;
        target.setAttribute('list', 'feature-ids');
        target.setAttribute('aria-label', `Target of ${ref.label}`);
        target.dataset.field = `t-${portIndex}-${ref.itemIndex}`;
        target.addEventListener('change', () => send('connect', { index: feature.index, portIndex, itemIndex: ref.itemIndex, target: target.value }));
        box.append(el('div', ref.label, 'muted'), target);
        if (port.kind === 'weighted') {
          const weight = el('input', undefined, 'weight');
          weight.type = 'number'; weight.min = '0'; weight.step = 'any';
          weight.value = ref.weight ?? '';
          weight.dataset.field = `w-${portIndex}-${ref.itemIndex}`;
          weight.addEventListener('change', () => send('weight', { index: feature.index, portIndex, itemIndex: ref.itemIndex, value: weight.value }));
          const line = el('div', undefined, 'line');
          line.append(el('label', 'Weight'), weight);
          box.append(line);
        }
        if (port.kind === 'conditional') {
          const condition = el('input');
          condition.placeholder = 'Molang condition (empty = always)';
          condition.value = ref.condition ?? '';
          condition.dataset.field = `c-${portIndex}-${ref.itemIndex}`;
          condition.addEventListener('change', () => send('condition', { index: feature.index, portIndex, itemIndex: ref.itemIndex, value: condition.value }));
          box.append(labelled('Condition', condition));
        }
        const actions = el('div', undefined, 'actions');
        actions.append(button('Remove', () => send('disconnect', { index: feature.index, portIndex, itemIndex: ref.itemIndex }), 'secondary'));
        box.append(actions);
        inspector.append(box);
      });
      if (port.kind !== 'single' || !refs.length) {
        const box = el('div', undefined, 'conn');
        const input = el('input');
        input.placeholder = 'namespace:feature';
        input.setAttribute('list', 'feature-ids');
        input.setAttribute('aria-label', `New target for ${port.label}`);
        input.dataset.field = `new-${portIndex}`;
        const add = () => {
          if (!input.value.trim()) { notify('Enter a feature identifier.', true); return; }
          send('connect', { index: feature.index, portIndex, itemIndex: null, target: input.value });
        };
        input.addEventListener('keydown', event => { if (event.key === 'Enter') add(); });
        const actions = el('div', undefined, 'actions');
        actions.append(button(port.kind === 'single' ? 'Connect' : 'Add connection', add));
        box.append(input, actions);
        inspector.append(box);
      }
    });

    inspector.append(el('h3', 'Feature JSON5'));
    let draft = drafts.get(node.key);
    if (draft && draft.raw === feature.raw) draft = null;
    if (draft && draft.raw === draft.base && draft.base !== feature.raw) draft = null;
    if (!draft) { draft = { base: feature.raw, raw: feature.raw }; drafts.set(node.key, draft); }
    const conflict = draft.base !== feature.raw;
    const dirty = draft.raw !== draft.base;
    const textarea = el('textarea');
    textarea.value = draft.raw;
    textarea.spellcheck = false;
    textarea.dataset.field = 'raw';
    textarea.setAttribute('aria-label', 'Feature JSON5');
    const apply = button('Apply changes', () => {
      send('replace', { index: feature.index, raw: draft.raw, base: draft.base });
    });
    const note = el('p', undefined, 'warning');
    const refresh = () => {
      const changed = draft.raw !== draft.base;
      apply.disabled = !changed || conflict;
      note.textContent = conflict ? 'This feature changed in the file after you started editing.' : changed ? 'Edited, not applied yet.' : '';
    };
    textarea.addEventListener('input', () => { draft.raw = textarea.value; refresh(); });
    refresh();
    inspector.append(textarea, note);
    const actions = el('div', undefined, 'actions');
    actions.append(apply);
    actions.append(button(conflict ? 'Reload from file' : 'Revert', () => { drafts.delete(node.key); renderInspector(true); }, 'secondary'));
    actions.append(button('Delete feature', () => send('delete', { index: feature.index }), 'danger'));
    inspector.append(actions);
    if (dirty && !conflict) inspector.append(el('p', 'You can select other nodes; this draft is kept.', 'muted'));
  }

  // ------------------------------------------------------------------------------ //
  // Wiring
  // ------------------------------------------------------------------------------ //
  $('add').addEventListener('click', event => {
    const rect = event.currentTarget.getBoundingClientRect();
    showMenu(rect.left, rect.bottom + 2, 'Add feature', type => {
      const bounds = canvas.getBoundingClientRect();
      pendingFocus = { pos: toScene(bounds.left + bounds.width / 3, bounds.top + bounds.height / 3) };
      send('create', { template: type });
    });
  });
  $('layout').addEventListener('click', () => { positions = {}; placeNodes(true); measureAnchors(); renderEdges(); fit(); });
  $('fit').addEventListener('click', fit);
  $('text').addEventListener('click', () => send('openText'));

  function applyFocus() {
    if (!pendingFocus || !pendingFocus.id) return;
    const node = graph.nodes.find(item => !item.external && item.feature.id === pendingFocus.id);
    if (!node) return;
    const { pos } = pendingFocus;
    pendingFocus = null;
    if (pos) setPosition(node.key, { x: pos.x - 20, y: pos.y - 20 });
    select({ kind: 'node', key: node.key });
  }

  window.addEventListener('message', event => {
    const data = event.data;
    switch (data.type) {
      case 'document':
        settle();
        invalid = null;
        banner.hidden = true;
        version = data.version;
        features = data.features;
        templates = data.templates;
        if (pendingRename) {
          if (features.some(feature => feature.id === pendingRename.to) && !features.some(feature => feature.id === pendingRename.from)) {
            const { from, to } = pendingRename;
            if (positions[from]) positions[to] = positions[from];
            drafts.delete(from);
            if (selection && selection.kind === 'node' && selection.key === from) selection = { kind: 'node', key: to };
          }
          pendingRename = null;
        }
        render();
        updateStatus();
        renderInspector();
        applyFocus();
        break;
      case 'invalid':
        settle();
        invalid = data.message;
        version = data.version;
        banner.textContent = `The file has a syntax error, so the graph is read-only until it is fixed: ${data.message}`;
        banner.hidden = false;
        break;
      case 'created':
        pendingFocus = { pos: null, ...pendingFocus, id: data.id };
        applyFocus();
        break;
      case 'error':
        settle();
        pendingFocus = null;
        pendingRename = null;
        notify(data.message, true);
        renderInspector(true);
        break;
    }
  });

  vscode.postMessage({ type: 'ready' });
}());
