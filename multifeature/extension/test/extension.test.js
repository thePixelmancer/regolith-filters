const test = require('node:test');
const assert = require('node:assert/strict');
const Module = require('node:module');

// Loads the real extension code against a minimal fake of the VS Code API.
function setup(text) {
  let provider, documentChanged, receive;
  const messages = [];
  const document = {
    uri: { toString: () => 'file:test.multifeature.json' },
    version: 1,
    text,
    getText() { return this.text; },
    positionAt(offset) { return offset; },
  };
  class WorkspaceEdit {
    constructor() { this.edits = []; }
    replace(uri, range, replacement) { this.edits.push({ range, text: replacement }); }
  }
  const vscode = {
    Uri: { joinPath: (...parts) => parts.join('/') },
    Range: class { constructor(start, end) { this.start = start; this.end = end; } },
    WorkspaceEdit,
    window: { registerCustomEditorProvider: (type, registered) => { provider = registered; return {}; } },
    commands: { registerCommand: () => ({}), executeCommand: async () => {} },
    workspace: {
      onDidChangeTextDocument: callback => { documentChanged = callback; return { dispose() {} }; },
      applyEdit: async change => {
        // Simulate VS Code taking a moment, so overlapping messages would interleave if not queued.
        await new Promise(resolve => setTimeout(resolve, 5));
        for (const edit of [...change.edits].sort((a, b) => b.range.start - a.range.start)) {
          document.text = document.text.slice(0, edit.range.start) + edit.text + document.text.slice(edit.range.end);
        }
        document.version++;
        documentChanged({ document });
        return true;
      },
    },
  };
  const originalLoad = Module._load;
  try {
    Module._load = function (request, ...args) {
      return request === 'vscode' ? vscode : originalLoad.call(this, request, ...args);
    };
    delete require.cache[require.resolve('../src/extension')];
    require('../src/extension').activate({ extensionUri: 'extension', subscriptions: [] });
  } finally {
    Module._load = originalLoad;
  }
  const panel = {
    webview: {
      cspSource: 'test',
      asWebviewUri: uri => uri,
      postMessage: message => messages.push(message),
      onDidReceiveMessage: callback => { receive = callback; },
    },
    onDidDispose() {},
  };
  provider.resolveCustomTextEditor(document, panel);
  return { document, messages, receive: message => receive(message), html: () => panel.webview.html };
}

const aggregate = `[{format_version:'1', 'minecraft:aggregate_feature': {description:{identifier:'x'}, features:[]}}]`;
const lastDocument = messages => messages.findLast(message => message.type === 'document');

test('webview page loads only its own script and style with a nonce-based policy', () => {
  const { html } = setup(aggregate);
  const page = html();
  assert.match(page, /script-src 'nonce-[^']+'/);
  assert.doesNotMatch(page, /unsafe-inline|unsafe-eval/);
  assert.match(page, /editor\.js/);
});

test('graph edits are applied to the live document and stale edits are rejected', async () => {
  const { document, messages, receive } = setup(aggregate);
  await receive({ type: 'ready' });
  assert.equal(lastDocument(messages).features[0].id, 'x');
  assert.ok(lastDocument(messages).templates.length > 5);
  await receive({ type: 'connect', version: 1, index: 0, target: 'external:feature', portIndex: 0 });
  assert.match(document.text, /external:feature/);
  assert.equal(lastDocument(messages).features[0].refs[0].target, 'external:feature');
  const updated = document.text;
  await receive({ type: 'delete', version: 1, index: 0 });
  assert.equal(document.text, updated);
  assert.match(messages.at(-1).message, /file changed/i);
});

test('messages that arrive together are applied one at a time', async () => {
  const { document, messages, receive } = setup(aggregate);
  await receive({ type: 'ready' });
  const first = receive({ type: 'connect', version: 1, index: 0, target: 'one', portIndex: 0 });
  const second = receive({ type: 'connect', version: 1, index: 0, target: 'two', portIndex: 0 });
  await Promise.all([first, second]);
  assert.match(document.text, /one/);
  assert.doesNotMatch(document.text, /two/);
  assert.equal(messages.filter(message => message.type === 'error').length, 1);
});

test('creating a feature from a connection reports its identifier back to the editor', async () => {
  const { document, messages, receive } = setup(aggregate);
  await receive({ type: 'ready' });
  await receive({ type: 'create', version: 1, template: 'minecraft:scatter_feature', from: { index: 0, portIndex: 0, itemIndex: null } });
  const created = messages.find(message => message.type === 'created');
  assert.ok(created && created.id);
  const features = lastDocument(messages).features;
  assert.equal(features.length, 2);
  assert.equal(features[0].refs[0].target, created.id);
  assert.equal(features[1].id, created.id);
  assert.ok(document.text.includes(created.id));
});

test('invalid files report a syntax error instead of failing, and replace checks the original text', async () => {
  const { document, messages, receive } = setup('[ {oops');
  await receive({ type: 'ready' });
  assert.equal(messages.at(-1).type, 'invalid');
  document.text = aggregate;
  document.version++;
  await receive({ type: 'ready' });
  const feature = lastDocument(messages).features[0];
  const raw = feature.raw.replace("'x'", "'y'");
  await receive({ type: 'replace', index: 0, raw, base: 'not the current text' });
  assert.match(messages.at(-1).message, /changed in the file/);
  await receive({ type: 'replace', index: 0, raw, base: feature.raw });
  assert.equal(lastDocument(messages).features[0].id, 'y');
});
