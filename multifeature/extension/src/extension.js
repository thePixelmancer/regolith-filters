const vscode = require('vscode');
const crypto = require('crypto');
const model = require('./model');

const viewType = 'multifeature.graph';

function activate(context) {
  context.subscriptions.push(
    vscode.window.registerCustomEditorProvider(viewType, new GraphEditor(context), {
      webviewOptions: { retainContextWhenHidden: true },
      supportsMultipleEditorsPerDocument: true,
    }),
    vscode.commands.registerCommand('multifeature.open', async resource => {
      const uri = resource instanceof vscode.Uri ? resource : vscode.window.activeTextEditor?.document.uri;
      if (!uri) {
        vscode.window.showInformationMessage('Open a .multifeature.json file first.');
        return;
      }
      await vscode.commands.executeCommand('vscode.openWith', uri, viewType);
    }),
    vscode.commands.registerCommand('multifeature.create', async () => {
      const folder = vscode.workspace.workspaceFolders?.[0]?.uri;
      const uri = await vscode.window.showSaveDialog({
        title: 'Create MultiFeature file',
        saveLabel: 'Create',
        defaultUri: folder ? vscode.Uri.joinPath(folder, 'new.multifeature.json') : undefined,
        filters: { 'MultiFeature JSON': ['json'] },
      });
      if (!uri) return;
      if (!uri.path.toLowerCase().endsWith('.multifeature.json')) {
        vscode.window.showErrorMessage('The file name must end in .multifeature.json.');
        return;
      }
      const changes = new vscode.WorkspaceEdit();
      changes.createFile(uri, { overwrite: false, ignoreIfExists: false });
      changes.insert(uri, new vscode.Position(0, 0), '[]\n');
      try {
        if (!await vscode.workspace.applyEdit(changes)) throw new Error('Could not create the file.');
        await vscode.commands.executeCommand('vscode.openWith', uri, viewType);
      } catch (error) {
        vscode.window.showErrorMessage(`MultiFeature: ${error.message}`);
      }
    }),
  );
}

class GraphEditor {
  constructor(context) {
    this.context = context;
  }

  resolveCustomTextEditor(document, panel) {
    const webview = panel.webview;
    const media = vscode.Uri.joinPath(this.context.extensionUri, 'media');
    webview.options = { enableScripts: true, localResourceRoots: [media] };
    const script = webview.asWebviewUri(vscode.Uri.joinPath(media, 'editor.js'));
    const style = webview.asWebviewUri(vscode.Uri.joinPath(media, 'editor.css'));
    const nonce = crypto.randomBytes(16).toString('base64');
    webview.html = `<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src ${webview.cspSource}; script-src 'nonce-${nonce}';">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="stylesheet" href="${style}"><title>MultiFeature Graph</title></head>
<body>
<header>
  <button id="add" title="Add a new feature">+ Add feature</button>
  <button id="layout" class="secondary" title="Arrange all nodes automatically">Auto layout</button>
  <button id="fit" class="secondary" title="Zoom to show every node">Fit</button>
  <button id="text" class="secondary" title="Open this file in the text editor">Open as text</button>
  <span id="status" role="status"></span>
</header>
<div id="banner" hidden></div>
<main>
  <div id="canvas" tabindex="0" aria-label="Feature graph">
    <div id="scene"><svg id="edges" aria-hidden="true"></svg><div id="nodes"></div></div>
    <div id="empty" hidden>This file has no features yet. Click <b>+ Add feature</b> to start.</div>
  </div>
  <aside id="inspector"></aside>
</main>
<div id="menu" role="menu" hidden></div>
<script nonce="${nonce}" src="${script}"></script>
</body></html>`;

    const update = () => {
      try {
        const parsed = model.readDocument(document.getText());
        webview.postMessage({
          type: 'document', version: document.version, features: parsed.features, templates: model.describeTemplates(),
        });
      } catch (error) {
        webview.postMessage({ type: 'invalid', version: document.version, message: error.message });
      }
    };
    const subscription = vscode.workspace.onDidChangeTextDocument(event => {
      if (event.document.uri.toString() === document.uri.toString()) update();
    });
    panel.onDidDispose(() => subscription.dispose());

    const handle = async message => {
      if (message.type === 'ready') return update();
      if (message.type === 'openText') {
        return vscode.commands.executeCommand('vscode.openWith', document.uri, 'default');
      }
      try {
        const parsed = model.readDocument(document.getText());
        // Edits are computed from feature indexes, so they are only valid for the version the
        // webview saw. Replacing a feature is guarded separately by comparing its previous text.
        if (message.type !== 'replace' && message.version !== document.version) {
          throw new Error('The file changed while you were editing. Review the updated graph and try again.');
        }
        let edits;
        let created;
        switch (message.type) {
          case 'create': {
            const result = model.createFeature(parsed, message.template, { id: message.id, from: message.from });
            edits = result.edits;
            created = result.id;
            break;
          }
          case 'replace': edits = model.replaceFeature(parsed, message.index, message.raw, message.base); break;
          case 'delete': edits = model.deleteFeature(parsed, message.index); break;
          case 'connect': edits = model.connect(parsed, message.index, message.target, message.portIndex, message.itemIndex); break;
          case 'disconnect': edits = model.disconnect(parsed, message.index, message.portIndex, message.itemIndex); break;
          case 'weight': edits = model.setWeight(parsed, message.index, message.portIndex, message.itemIndex, message.value); break;
          case 'condition': edits = model.setCondition(parsed, message.index, message.portIndex, message.itemIndex, message.value); break;
          case 'rename': edits = model.renameFeature(parsed, message.index, message.id); break;
          case 'formatVersion': edits = model.setFormatVersion(parsed, message.index, message.value); break;
          default: throw new Error('Unknown editor action.');
        }
        if (edits.length) {
          const change = new vscode.WorkspaceEdit();
          for (const item of edits) {
            change.replace(document.uri, new vscode.Range(document.positionAt(item.start), document.positionAt(item.end)), item.text);
          }
          if (!await vscode.workspace.applyEdit(change)) throw new Error('VS Code could not apply the edit.');
        }
        update();
        if (created) webview.postMessage({ type: 'created', id: created });
      } catch (error) {
        webview.postMessage({ type: 'error', message: error.message });
      }
    };

    // Messages must run one at a time: each edit changes the document the next one targets.
    let queue = Promise.resolve();
    webview.onDidReceiveMessage(message => {
      queue = queue.then(() => handle(message)).catch(error => {
        webview.postMessage({ type: 'error', message: String(error && error.message || error) });
      });
      return queue;
    });
  }
}

module.exports = { activate };
