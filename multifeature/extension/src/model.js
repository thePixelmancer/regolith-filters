const JSON5 = require('json5');
const momoa = require('@humanwhocodes/momoa');

const FORMAT_VERSION = '1.21.90';

// Where each feature type references other features.
const PORTS = {
  'minecraft:feature_rules': [{ path: ['description', 'places_feature'], kind: 'single' }],
  'minecraft:aggregate_feature': [{ path: ['features'], kind: 'list' }],
  'minecraft:sequence_feature': [{ path: ['features'], kind: 'list' }],
  'minecraft:weighted_random_feature': [{ path: ['features'], kind: 'weighted' }],
  'minecraft:conditional_list': [{ path: ['conditional_features'], kind: 'conditional' }],
  'minecraft:height_difference_filter_feature': [{ path: ['places_feature'], kind: 'single' }],
  'minecraft:scatter_feature': [{ path: ['places_feature'], kind: 'single' }],
  'minecraft:search_feature': [{ path: ['places_feature'], kind: 'single' }],
  'minecraft:snap_to_surface_feature': [{ path: ['feature_to_snap'], kind: 'single' }],
  'minecraft:surface_relative_threshold_feature': [{ path: ['feature_to_place'], kind: 'single' }],
  'minecraft:vegetation_patch_feature': [{ path: ['vegetation_feature'], kind: 'single' }],
  'minecraft:tree_feature': [
    { path: ['fallen_trunk', 'log_decoration_feature'], kind: 'single' },
    { path: ['poplar_trunk', 'log_decoration_feature'], kind: 'single' },
  ],
};

const xzExtent = { distribution: 'uniform', extent: [0, 15] };
const TEMPLATES = [
  {
    type: 'minecraft:feature_rules', name: 'rule', label: 'Feature rule', category: 'rule', suffix: 'feature_rule',
    body: id => ({
      description: { identifier: id, places_feature: '' },
      conditions: {
        placement_pass: 'surface_pass',
        'minecraft:biome_filter': [{ test: 'has_biome_tag', operator: '==', value: 'overworld' }],
      },
      distribution: { iterations: 1, x: xzExtent, y: 'query.heightmap(variable.worldx, variable.worldz)', z: xzExtent },
    }),
  },
  {
    type: 'minecraft:aggregate_feature', name: 'aggregate', label: 'Aggregate', category: 'container',
    body: id => ({ description: { identifier: id }, features: [], early_out: 'none' }),
  },
  {
    type: 'minecraft:sequence_feature', name: 'sequence', label: 'Sequence', category: 'container',
    body: id => ({ description: { identifier: id }, features: [] }),
  },
  {
    type: 'minecraft:weighted_random_feature', name: 'weighted_random', label: 'Weighted random', category: 'container',
    body: id => ({ description: { identifier: id }, features: [] }),
  },
  {
    type: 'minecraft:conditional_list', name: 'conditional_list', label: 'Conditional list', category: 'container',
    body: id => ({ description: { identifier: id }, conditional_features: [] }),
  },
  {
    type: 'minecraft:scatter_feature', name: 'scatter', label: 'Scatter', category: 'modifier',
    body: id => ({
      description: { identifier: id }, places_feature: '',
      distribution: { iterations: 1, x: xzExtent, y: 0, z: xzExtent },
    }),
  },
  {
    type: 'minecraft:search_feature', name: 'search', label: 'Search', category: 'modifier',
    body: id => ({
      description: { identifier: id }, places_feature: '',
      search_volume: { min: [0, -4, 0], max: [0, 4, 0] }, search_axis: '-y', required_successes: 1,
    }),
  },
  {
    type: 'minecraft:snap_to_surface_feature', name: 'snap_to_surface', label: 'Snap to surface', category: 'modifier',
    body: id => ({ description: { identifier: id }, feature_to_snap: '', vertical_search_range: 5, surface: 'floor' }),
  },
  {
    type: 'minecraft:surface_relative_threshold_feature', name: 'surface_threshold', label: 'Surface threshold', category: 'modifier',
    body: id => ({ description: { identifier: id }, feature_to_place: '', minimum_distance_below_surface: 0 }),
  },
  {
    type: 'minecraft:height_difference_filter_feature', name: 'height_filter', label: 'Height difference filter', category: 'modifier',
    body: id => ({ description: { identifier: id }, places_feature: '', search_radius: 4, max_allowed_upward_height_diff: 2 }),
  },
  {
    type: 'minecraft:vegetation_patch_feature', name: 'vegetation_patch', label: 'Vegetation patch', category: 'modifier',
    body: id => ({
      description: { identifier: id },
      replaceable_blocks: ['minecraft:dirt', 'minecraft:grass_block'],
      ground_block: 'minecraft:moss_block', vegetation_feature: '', surface: 'floor',
      depth: 1, vertical_range: 5, vegetation_chance: 0.3, horizontal_radius: 4,
    }),
  },
  {
    type: 'minecraft:single_block_feature', name: 'single_block', label: 'Single block', category: 'leaf',
    body: id => ({
      description: { identifier: id }, places_block: 'minecraft:stone',
      enforce_placement_rules: false, enforce_survivability_rules: false,
    }),
  },
];

function describeTemplates() {
  return TEMPLATES.map(({ type, label, category }) => ({ type, label, category }));
}

function portsFor(type) {
  return (Object.hasOwn(PORTS, type) ? PORTS[type] : []).map(port => ({ ...port, label: port.path.join('.') }));
}

// ---------------------------------------------------------------------------------- //
// Syntax tree helpers
// ---------------------------------------------------------------------------------- //
function member(node, key) {
  if (!node || node.type !== 'Object') return undefined;
  return [...node.members].reverse().find(item => (item.name.name ?? item.name.value) === key);
}

function property(node, key) {
  const found = member(node, key);
  return found && found.value;
}

function atPath(node, path) {
  for (const key of path) node = property(node, key);
  return node;
}

function edit(start, end, text) {
  return { start, end, text };
}

function itemsOf(container) {
  return container.type === 'Array' ? container.elements.map(element => element.value) : container.members;
}

function commaAfter(ast, node, container) {
  return ast.tokens.find(token => token.type === 'Comma' &&
    token.range[0] >= node.range[1] && token.range[1] < container.range[1]);
}

function commaBefore(ast, node, container) {
  return ast.tokens.filter(token => token.type === 'Comma' &&
    token.range[1] <= node.range[0] && token.range[0] > container.range[0]).pop();
}

function indentAt(text, offset) {
  const lineStart = text.lastIndexOf('\n', offset - 1) + 1;
  return /^[ \t]*/.exec(text.slice(lineStart))[0];
}

function reindent(itemText, indent) {
  return itemText.split('\n').map((line, i) => (i === 0 ? line : indent + line)).join('\n');
}

// Inserts an item at the end of an array or object while keeping existing text intact.
function append(document, container, itemText) {
  const { text, ast } = document;
  const items = itemsOf(container);
  const last = items[items.length - 1];
  const multiline = text.slice(container.range[0], container.range[1]).includes('\n');
  const closeIndent = indentAt(text, container.range[0]);
  if (!last) {
    if (!multiline && !itemText.includes('\n')) return [edit(container.range[0] + 1, container.range[0] + 1, itemText)];
    const indent = `${closeIndent}  `;
    return [edit(container.range[0] + 1, container.range[0] + 1, `\n${indent}${reindent(itemText, indent)}\n${closeIndent}`)];
  }
  const trailing = commaAfter(ast, last, container);
  if (!multiline && !itemText.includes('\n')) {
    return trailing ? [edit(trailing.range[1], trailing.range[1], ` ${itemText},`)] : [edit(last.range[1], last.range[1], `, ${itemText}`)];
  }
  const indent = indentAt(text, last.range[0]);
  const body = `\n${indent}${reindent(itemText, indent)}`;
  return trailing ? [edit(trailing.range[1], trailing.range[1], `${body},`)] : [edit(last.range[1], last.range[1], `,${body}`)];
}

// Removes an item and exactly one adjoining comma, leaving comments untouched.
function removal(document, container, item) {
  const { text, ast } = document;
  const next = commaAfter(ast, item, container);
  if (next) {
    let end = next.range[1];
    while (end < text.length && /\s/.test(text[end])) end++;
    return [edit(item.range[0], end, '')];
  }
  const previous = commaBefore(ast, item, container);
  let start = item.range[0];
  while (start > 0 && /\s/.test(text[start - 1])) start--;
  if (previous && text.slice(previous.range[1], start).trim() === '' && start >= previous.range[1]) {
    return [edit(previous.range[0], item.range[1], '')];
  }
  return [edit(start, item.range[1], ''), ...(previous ? [edit(previous.range[0], previous.range[1], '')] : [])];
}

// ---------------------------------------------------------------------------------- //
// Reading
// ---------------------------------------------------------------------------------- //
function collectRefs(typeNode, ports) {
  const refs = [];
  const nodes = [];
  ports.forEach((port, portIndex) => {
    const refNode = atPath(typeNode, port.path);
    if (!refNode) return;
    if (port.kind === 'single') {
      if (refNode.type === 'String' && refNode.value) {
        refs.push({ target: refNode.value, label: port.label, portIndex, itemIndex: null });
        nodes.push(refNode);
      }
      return;
    }
    if (refNode.type !== 'Array') return;
    refNode.elements.forEach((element, itemIndex) => {
      const value = element.value;
      let targetNode = value;
      const extra = {};
      if (port.kind === 'weighted') {
        targetNode = value.type === 'Array' ? value.elements[0]?.value : undefined;
        const weight = value.type === 'Array' ? value.elements[1]?.value : undefined;
        if (weight && weight.type === 'Number') extra.weight = weight.value;
      } else if (port.kind === 'conditional') {
        targetNode = property(value, 'feature');
        const condition = property(value, 'condition');
        if (condition && condition.type === 'String') extra.condition = condition.value;
      }
      if (targetNode && targetNode.type === 'String' && targetNode.value) {
        refs.push({ target: targetNode.value, label: `${port.label}[${itemIndex}]`, portIndex, itemIndex, ...extra });
        nodes.push(targetNode);
      }
    });
  });
  return { refs, nodes };
}

function readDocument(text) {
  if (!text.trim()) return { text, ast: null, nodes: [], features: [], refNodes: [] };
  const value = JSON5.parse(text);
  if (!Array.isArray(value) && (!value || typeof value !== 'object')) {
    throw new Error('Expected a feature object or an array of feature objects.');
  }
  const ast = momoa.parse(text, { mode: 'json5', ranges: true, tokens: true });
  const values = Array.isArray(value) ? value : [value];
  const nodes = ast.body.type === 'Array' ? ast.body.elements.map(element => element.value) : [ast.body];
  const refNodes = [];
  const features = values.map((entry, index) => {
    if (!entry || typeof entry !== 'object' || Array.isArray(entry)) {
      throw new Error(`Feature ${index + 1} must be an object.`);
    }
    const types = Object.keys(entry).filter(key => key !== 'format_version');
    const type = types.length === 1 ? types[0] : '';
    const body = type && entry[type];
    const id = body && typeof body === 'object' && body.description && body.description.identifier;
    const ports = type ? portsFor(type) : [];
    const { refs, nodes: found } = collectRefs(type ? property(nodes[index], type) : undefined, ports);
    refNodes.push(found);
    return {
      index, type, id: typeof id === 'string' ? id : '',
      formatVersion: typeof entry.format_version === 'string' ? entry.format_version : '',
      raw: text.slice(...nodes[index].range), refs, ports,
    };
  });
  return { text, ast, features, nodes, refNodes };
}

// ---------------------------------------------------------------------------------- //
// Editing. Every function returns a list of { start, end, text } edits against the
// current text, or throws an Error whose message is safe to show to the user.
// ---------------------------------------------------------------------------------- //
function validateFeature(raw) {
  const parsed = readDocument(raw);
  if (!parsed.ast || parsed.ast.body.type !== 'Object') throw new Error('A feature must be an object.');
  const value = JSON5.parse(raw);
  const keys = Object.keys(value);
  if (!Object.hasOwn(value, 'format_version') || keys.length !== 2) {
    throw new Error('A feature must contain format_version and exactly one feature type.');
  }
  const body = value[keys.find(key => key !== 'format_version')];
  if (!body || typeof body !== 'object' || Array.isArray(body) ||
      typeof body.description?.identifier !== 'string' || !body.description.identifier.trim()) {
    throw new Error('A feature needs a description.identifier.');
  }
}

function addFeature(document, raw) {
  validateFeature(raw);
  if (!document.ast) return [edit(0, document.text.length, `[\n  ${reindent(raw, '  ')}\n]\n`)];
  if (document.ast.body.type === 'Array') return append(document, document.ast.body, raw);
  const root = document.ast.body;
  return [edit(root.range[0], root.range[0], '[\n'), edit(root.range[1], root.range[1], `,\n${raw}\n]`)];
}

function replaceFeature(document, index, raw, base) {
  const node = document.nodes[index];
  if (!node) throw new Error('Feature no longer exists.');
  if (base !== undefined && document.features[index].raw !== base) {
    throw new Error('This feature changed in the file after you started editing. Reload it and try again.');
  }
  validateFeature(raw);
  return [edit(node.range[0], node.range[1], raw)];
}

function deleteFeature(document, index) {
  const node = document.nodes[index];
  if (!node) throw new Error('Feature no longer exists.');
  if (document.ast.body.type !== 'Array') return [edit(node.range[0], node.range[1], '[]')];
  return removal(document, document.ast.body, node);
}

function locate(document, index, portIndex) {
  const feature = document.features[index];
  const port = feature && feature.ports[portIndex];
  if (!port) throw new Error('This feature has no supported connection field.');
  const body = property(document.nodes[index], feature.type);
  if (!body || body.type !== 'Object') throw new Error('Feature data must be an object.');
  const parentPath = port.path.slice(0, -1);
  const parent = atPath(body, parentPath);
  if (!parent || parent.type !== 'Object') {
    throw new Error(`Add a "${parentPath.join('.')}" object to this feature before connecting it.`);
  }
  const key = port.path[port.path.length - 1];
  return { feature, port, parent, key, existing: property(parent, key) };
}

function listEntry(existing, itemIndex, label) {
  const element = existing.type === 'Array' && existing.elements[itemIndex];
  if (!element) throw new Error(`${label}[${itemIndex}] no longer exists.`);
  return element.value;
}

function connect(document, index, target, portIndex = 0, itemIndex = null) {
  if (typeof target !== 'string' || !target.trim()) throw new Error('Enter a feature identifier.');
  target = target.trim();
  const { feature, port, parent, key, existing } = locate(document, index, portIndex);
  if (feature.id && target === feature.id) throw new Error('A feature cannot place itself.');
  const value = JSON.stringify(target);
  if (port.kind === 'single') {
    if (!existing) return append(document, parent, `${JSON.stringify(key)}: ${value}`);
    if (existing.type !== 'String') throw new Error(`${port.label} must be a string.`);
    return [edit(existing.range[0], existing.range[1], value)];
  }
  const item = port.kind === 'weighted' ? `[${value}, 1]` : port.kind === 'conditional' ? `{ "feature": ${value} }` : value;
  if (!existing) return append(document, parent, `${JSON.stringify(key)}: [${item}]`);
  if (existing.type !== 'Array') throw new Error(`${port.label} must be an array.`);
  if (itemIndex === null || itemIndex === undefined) return append(document, existing, item);
  const entry = listEntry(existing, itemIndex, port.label);
  if (port.kind === 'list') return [edit(entry.range[0], entry.range[1], value)];
  if (port.kind === 'weighted') {
    const first = entry.type === 'Array' && entry.elements[0]?.value;
    if (!first) throw new Error('Weighted entries must look like ["feature", weight].');
    return [edit(first.range[0], first.range[1], value)];
  }
  const feat = property(entry, 'feature');
  if (feat) return [edit(feat.range[0], feat.range[1], value)];
  if (entry.type !== 'Object') throw new Error('Conditional entries must be objects.');
  return append(document, entry, `"feature": ${value}`);
}

function disconnect(document, index, portIndex = 0, itemIndex = null) {
  const { port, parent, key, existing } = locate(document, index, portIndex);
  if (!existing) return [];
  if (port.kind === 'single') return removal(document, parent, member(parent, key));
  return removal(document, existing, listEntry(existing, itemIndex, port.label));
}

function setWeight(document, index, portIndex, itemIndex, weight) {
  const number = Number(weight);
  if (weight === '' || weight === null || !Number.isFinite(number) || number < 0) {
    throw new Error('Weight must be a number that is 0 or more.');
  }
  const { existing, port } = locate(document, index, portIndex);
  const entry = listEntry(existing || {}, itemIndex, port.label);
  if (entry.type !== 'Array') throw new Error('Weighted entries must look like ["feature", weight].');
  const current = entry.elements[1]?.value;
  return current ? [edit(current.range[0], current.range[1], String(number))] : append(document, entry, String(number));
}

function setCondition(document, index, portIndex, itemIndex, condition) {
  const { existing, port } = locate(document, index, portIndex);
  const entry = listEntry(existing || {}, itemIndex, port.label);
  if (entry.type !== 'Object') throw new Error('Conditional entries must be objects.');
  const text = String(condition ?? '').trim();
  const found = member(entry, 'condition');
  if (!text) return found ? removal(document, entry, found) : [];
  if (found) return [edit(found.value.range[0], found.value.range[1], JSON.stringify(text))];
  return append(document, entry, `"condition": ${JSON.stringify(text)}`);
}

function setFormatVersion(document, index, value) {
  const node = property(document.nodes[index], 'format_version');
  if (!node || node.type !== 'String') throw new Error('This feature has no format_version string to edit.');
  value = String(value).trim();
  if (!/^(\d+\.\d+\.\d+|beta)$/.test(value)) throw new Error('Format version must look like 1.21.90.');
  return [edit(node.range[0], node.range[1], JSON.stringify(value))];
}

function renameFeature(document, index, newId) {
  const feature = document.features[index];
  if (!feature) throw new Error('Feature no longer exists.');
  newId = String(newId ?? '').trim();
  if (!newId) throw new Error('An identifier cannot be empty.');
  if (/[\s"'\\]/.test(newId)) throw new Error('Identifiers cannot contain spaces, quotes or backslashes.');
  if (feature.type === 'minecraft:feature_rules' && /[/\\:*?"<>|]/.test(newId.split(':').slice(1).join(':') || newId)) {
    throw new Error('Feature rule names become file names and cannot contain / \\ : * ? " < > |.');
  }
  if (document.features.some(other => other !== feature && other.id === newId)) {
    throw new Error(`${newId} is already used by another feature in this file.`);
  }
  const node = atPath(property(document.nodes[index], feature.type), ['description', 'identifier']);
  if (!node || node.type !== 'String') throw new Error('This feature has no description.identifier to rename.');
  if (newId === feature.id) return [];
  const edits = [edit(node.range[0], node.range[1], JSON.stringify(newId))];
  const unique = feature.id && document.features.filter(other => other.id === feature.id).length === 1;
  if (unique) {
    for (const nodes of document.refNodes) {
      for (const ref of nodes) if (ref.value === feature.id) edits.push(edit(ref.range[0], ref.range[1], JSON.stringify(newId)));
    }
  }
  return edits;
}

// ---------------------------------------------------------------------------------- //
// Creating features from templates
// ---------------------------------------------------------------------------------- //
function stringify(value, level = 0) {
  const pad = '  '.repeat(level + 1);
  const close = '  '.repeat(level);
  if (Array.isArray(value)) {
    if (value.every(item => item === null || typeof item !== 'object')) return JSON.stringify(value).replace(/,/g, ', ');
    return `[\n${value.map(item => pad + stringify(item, level + 1)).join(',\n')}\n${close}]`;
  }
  if (value && typeof value === 'object') {
    const entries = Object.entries(value);
    if (!entries.length) return '{}';
    return `{\n${entries.map(([key, item]) => `${pad}${JSON.stringify(key)}: ${stringify(item, level + 1)}`).join(',\n')}\n${close}}`;
  }
  return JSON.stringify(value);
}

function createFeature(document, type, options = {}) {
  const template = TEMPLATES.find(item => item.type === type);
  if (!template) throw new Error('Unknown feature type.');
  const ids = new Set(document.features.map(feature => feature.id));
  let id = typeof options.id === 'string' ? options.id.trim() : '';
  if (id) {
    if (ids.has(id)) throw new Error(`${id} already exists in this file.`);
    if (/[\s"'\\]/.test(id)) throw new Error('Identifiers cannot contain spaces, quotes or backslashes.');
  } else {
    const source = document.features[options.from?.index]?.id || document.features.find(feature => feature.id.includes(':'))?.id || '';
    const namespace = source.includes(':') ? source.split(':')[0] : 'example';
    for (let n = 1; ids.has(id = `${namespace}:new_${template.name}_${n}.${template.suffix || 'feature'}`); n++);
  }
  const raw = stringify({ format_version: FORMAT_VERSION, [type]: template.body(id) });
  const edits = addFeature(document, raw);
  if (options.from) {
    const { index, portIndex, itemIndex } = options.from;
    edits.push(...connect(document, index, id, portIndex, itemIndex));
  }
  return { edits, id };
}

module.exports = {
  PORTS, TEMPLATES, describeTemplates, readDocument, addFeature, replaceFeature, deleteFeature,
  connect, disconnect, setWeight, setCondition, setFormatVersion, renameFeature, createFeature,
};
