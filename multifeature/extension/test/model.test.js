const test = require('node:test');
const assert = require('node:assert/strict');
const JSON5 = require('json5');
const model = require('../src/model');

function apply(text, edits) {
  for (const edit of [...edits].sort((a, b) => b.start - a.start)) {
    text = text.slice(0, edit.start) + edit.text + text.slice(edit.end);
  }
  return text;
}

const read = text => model.readDocument(text);
const targets = feature => feature.refs.map(ref => ref.target);

const source = `[
  // Keep the rule comment
  {format_version:'1.21.0', 'minecraft:feature_rules': {
    description: {identifier: 'example:rule', places_feature: 'example:aggregate'}
  }},
  {format_version:'1.21.0', 'minecraft:aggregate_feature': {
    description: {identifier: 'example:aggregate'},
    features: ['example:one', /* keep */ 'example:two',],
  }},
  {format_version:'1.21.0', 'minecraft:weighted_random_feature': {
    description: {identifier: 'example:weighted'}, features: [['example:one', 5]]
  }},
  {format_version:'1.21.0', 'minecraft:conditional_list': {
    description: {identifier: 'example:conditional'}, conditional_features: [{feature:'example:two', condition:'true'}]
  }},
  {format_version:'1.21.0', 'minecraft:tree_feature': {
    description: {identifier: 'example:tree'},
    fallen_trunk: {log_decoration_feature: 'example:external'}
  }}
]`;

test('discovers rule, branching, weighted, conditional and nested tree references', () => {
  const { features } = read(source);
  assert.deepEqual(features.map(targets), [
    ['example:aggregate'], ['example:one', 'example:two'], ['example:one'], ['example:two'], ['example:external'],
  ]);
  assert.equal(features[2].refs[0].weight, 5);
  assert.equal(features[3].refs[0].condition, 'true');
  assert.equal(features[4].refs[0].label, 'fallen_trunk.log_decoration_feature');
});

test('connecting updates only the field and retains JSON5 comments', () => {
  let text = apply(source, model.connect(read(source), 0, 'example:other'));
  text = apply(text, model.connect(read(text), 1, 'example:three'));
  text = apply(text, model.connect(read(text), 2, 'example:three'));
  text = apply(text, model.connect(read(text), 3, 'example:three'));
  const { features } = read(text);
  assert.equal(features[0].refs[0].target, 'example:other');
  assert.deepEqual(targets(features[1]), ['example:one', 'example:two', 'example:three']);
  assert.deepEqual(features[2].refs.map(ref => [ref.target, ref.weight]), [['example:one', 5], ['example:three', 1]]);
  assert.equal(features[3].refs[1].target, 'example:three');
  assert.match(text, /\/\/ Keep the rule comment/);
  assert.match(text, /\/\* keep \*\//);
});

test('connecting an existing entry retargets it in place', () => {
  let text = apply(source, model.connect(read(source), 1, 'example:swapped', 0, 1));
  text = apply(text, model.connect(read(text), 2, 'example:swapped', 0, 0));
  text = apply(text, model.connect(read(text), 3, 'example:swapped', 0, 0));
  const { features } = read(text);
  assert.deepEqual(targets(features[1]), ['example:one', 'example:swapped']);
  assert.deepEqual(features[2].refs.map(ref => [ref.target, ref.weight]), [['example:swapped', 5]]);
  assert.equal(features[3].refs[0].condition, 'true');
  assert.throws(() => model.connect(read(source), 0, 'example:rule'), /cannot place itself/);
});

test('adds missing connection fields and rejects wrong shapes', () => {
  const text = `[{format_version:'1', 'minecraft:scatter_feature': {description:{identifier:'x'}}}]`;
  const changed = apply(text, model.connect(read(text), 0, 'outside:x'));
  assert.equal(read(changed).features[0].refs[0].target, 'outside:x');
  const bad = `[{format_version:'1', 'minecraft:aggregate_feature': {description:{identifier:'x'}, features:42}}]`;
  assert.throws(() => model.connect(read(bad), 0, 'outside:x'), /must be an array/);
  const badSingle = `[{format_version:'1', 'minecraft:scatter_feature': {description:{identifier:'x'}, places_feature:{custom:1}}}]`;
  assert.throws(() => model.connect(read(badSingle), 0, 'outside:x'), /must be a string/);
  const tree = `[{format_version:'1', 'minecraft:tree_feature': {description:{identifier:'x'}}}]`;
  assert.throws(() => model.connect(read(tree), 0, 'outside:x'), /fallen_trunk/);
});

test('disconnecting removes only the chosen entry', () => {
  let text = apply(source, model.disconnect(read(source), 1, 0, 0));
  assert.deepEqual(targets(read(text).features[1]), ['example:two']);
  assert.match(text, /\/\* keep \*\//);
  text = apply(text, model.disconnect(read(text), 1, 0, 0));
  assert.deepEqual(targets(read(text).features[1]), []);
  text = apply(text, model.disconnect(read(text), 0, 0, null));
  assert.deepEqual(targets(read(text).features[0]), []);
  assert.equal(read(text).features.length, 5);
  text = apply(text, model.disconnect(read(text), 2, 0, 0));
  assert.deepEqual(targets(read(text).features[2]), []);
});

test('weights and conditions can be edited, added and cleared', () => {
  let text = apply(source, model.setWeight(read(source), 2, 0, 0, '12.5'));
  assert.equal(read(text).features[2].refs[0].weight, 12.5);
  assert.throws(() => model.setWeight(read(source), 2, 0, 0, '-1'), /Weight/);
  assert.throws(() => model.setWeight(read(source), 2, 0, 0, ''), /Weight/);
  text = apply(source, model.setCondition(read(source), 3, 0, 0, 'query.is_day'));
  assert.equal(read(text).features[3].refs[0].condition, 'query.is_day');
  text = apply(text, model.setCondition(read(text), 3, 0, 0, ''));
  assert.equal(read(text).features[3].refs[0].condition, undefined);
  text = apply(text, model.setCondition(read(text), 3, 0, 0, 'v.x > 1'));
  assert.equal(read(text).features[3].refs[0].condition, 'v.x > 1');
});

test('renaming updates the identifier and every reference to it', () => {
  const text = apply(source, model.renameFeature(read(source), 1, 'example:renamed'));
  const { features } = read(text);
  assert.equal(features[1].id, 'example:renamed');
  assert.equal(features[0].refs[0].target, 'example:renamed');
  assert.throws(() => model.renameFeature(read(source), 1, 'example:rule'), /already used/);
  assert.throws(() => model.renameFeature(read(source), 1, 'has space'), /spaces/);
  assert.throws(() => model.renameFeature(read(source), 0, 'example:bad/name'), /file names/);
  assert.deepEqual(model.renameFeature(read(source), 1, 'example:aggregate'), []);
});

test('format version can be changed', () => {
  const text = apply(source, model.setFormatVersion(read(source), 0, '1.21.90'));
  assert.equal(read(text).features[0].formatVersion, '1.21.90');
  assert.throws(() => model.setFormatVersion(read(source), 0, 'nope'), /Format version/);
});

test('adding to an object wraps it without removing surrounding comments', () => {
  const original = `// before\n{format_version:'1', 'minecraft:scatter_feature': {description:{identifier:'x'}}} // after\n`;
  const added = `{format_version:'1', 'minecraft:scatter_feature': {description:{identifier:'y'}}}`;
  const text = apply(original, model.addFeature(read(original), added));
  assert.equal(read(text).features.length, 2);
  assert.match(text, /\/\/ before/);
  assert.match(text, /\/\/ after/);
});

test('empty and whitespace-only files are valid empty graphs and accept new features', () => {
  for (const original of ['', '  \n', '[]']) {
    const document = read(original);
    assert.deepEqual(document.features, []);
    const { edits, id } = model.createFeature(document, 'minecraft:scatter_feature');
    const next = read(apply(original, edits));
    assert.equal(next.features.length, 1);
    assert.equal(next.features[0].id, id);
  }
});

test('deleting first, last and only features leaves valid JSON5 and comments', () => {
  for (const index of [0, 2, 4]) {
    const text = apply(source, model.deleteFeature(read(source), index));
    assert.equal(read(text).features.length, 4);
    assert.match(text, /\/\/ Keep the rule comment/);
  }
  const single = `{format_version:'1', 'minecraft:scatter_feature': {description:{identifier:'x'}}}`;
  assert.deepEqual(read(apply(single, model.deleteFeature(read(single), 0))).features, []);
});

test('replacing a feature preserves other nodes and rejects invalid or stale input', () => {
  const replacement = `{format_version:'1', 'minecraft:scatter_feature': {description:{identifier:'new'}}}`;
  const text = apply(source, model.replaceFeature(read(source), 0, replacement));
  assert.equal(read(text).features[0].id, 'new');
  assert.match(text, /\/\/ Keep the rule comment/);
  assert.throws(() => model.replaceFeature(read(source), 0, '[]'), /must be an object/);
  assert.throws(() => model.addFeature(read(source), '{format_version:"1", "minecraft:foo":{}}'), /description.identifier/);
  assert.throws(() => model.addFeature(read(source), '{"minecraft:foo":{description:{identifier:"x"}}}'), /format_version/);
  assert.throws(() => model.replaceFeature(read(source), 0, replacement, 'not the current text'), /changed in the file/);
  assert.doesNotThrow(() => model.replaceFeature(read(source), 0, replacement, read(source).features[0].raw));
  assert.throws(() => read('{oops:'), /./);
});

test('every template creates a valid feature, and the output stays valid after repeated edits', () => {
  let text = '[]';
  for (const template of model.TEMPLATES) {
    const { edits, id } = model.createFeature(read(text), template.type);
    text = apply(text, edits);
    const feature = read(text).features.at(-1);
    assert.equal(feature.id, id);
    assert.equal(feature.type, template.type);
    assert.doesNotThrow(() => JSON5.parse(text));
  }
  assert.equal(read(text).features.length, model.TEMPLATES.length);
  assert.equal(new Set(read(text).features.map(feature => feature.id)).size, model.TEMPLATES.length);
});

test('creating then deleting the last feature restores the original text', () => {
  const original = `[\n  {"format_version":"1.21.90","minecraft:aggregate_feature":{"description":{"identifier":"mod:root"},"features":[]}}\n]`;
  const created = apply(original, model.createFeature(read(original), 'minecraft:single_block_feature').edits);
  assert.equal(read(created).features.length, 2);
  assert.equal(apply(created, model.deleteFeature(read(created), 1)), original);
  const connected = apply(original, model.connect(read(original), 0, 'mod:a'));
  assert.equal(apply(connected, model.disconnect(read(connected), 0, 0, 0)), original);
});

test('creating from a connection adds the feature and connects it in one edit', () => {
  const start = `[{"format_version":"1.21.90","minecraft:aggregate_feature":{"description":{"identifier":"mod:root"},"features":[]}}]`;
  const { edits, id } = model.createFeature(read(start), 'minecraft:scatter_feature', { from: { index: 0, portIndex: 0, itemIndex: null } });
  const next = read(apply(start, edits));
  assert.equal(next.features.length, 2);
  assert.match(id, /^mod:new_scatter_1/);
  assert.deepEqual(targets(next.features[0]), [id]);
  const again = model.createFeature(next, 'minecraft:scatter_feature', { id: 'mod:given' });
  assert.equal(again.id, 'mod:given');
  assert.throws(() => model.createFeature(next, 'minecraft:scatter_feature', { id: id }), /already exists/);
  assert.throws(() => model.createFeature(next, 'minecraft:nope'), /Unknown/);
});
