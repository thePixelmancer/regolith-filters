# MultiFeature Editor

A node editor for `.multifeature.json` files. Every feature in the file is a
node, and a line from one node to another means "this feature places that
feature". It reads and writes the same JSON5 the filter accepts, including
comments and trailing commas, and only touches the text it needs to change.

## Run it

1. Open this `extension` folder in VS Code and run `npm install` in its terminal.
2. Press **F5**. A second window (the Extension Development Host) opens with
   other installed extensions disabled; your normal window is unaffected.
3. In that window, open a `.multifeature.json` file, such as
   [test/decoration.multifeature.json](test/decoration.multifeature.json), and
   click the graph icon in the editor title bar. You can also right-click the
   file in the Explorer and choose **MultiFeature: Open Graph Editor**, or use
   **Reopen Editor With... > MultiFeature Graph**.
4. To start from scratch, run **MultiFeature: Create File** from the Command
   Palette.

Edits are normal text edits: they show up in the text editor, mark the file as
modified, and work with undo and redo. Use **Open as text** to switch back.

## Editing

| To do this | Do this |
| --- | --- |
| Add a feature | **+ Add feature**, then pick a type |
| Connect two features | Drag from a dot on the right of a node onto another node |
| Create and connect in one step | Drag from a dot and drop on empty space, then pick a type |
| Re-point a connection | Drag from its (filled) dot to a different node |
| Remove a connection | Click the line and press **Delete**, or use **Remove** in the side panel |
| Delete a feature | Select the node and press **Delete** |
| Rename a feature | Edit **Identifier** in the side panel. References in the file are updated |
| Change weights or conditions | Side panel, under **Connections** |
| Edit everything else | **Feature JSON5** in the side panel, then **Apply changes** |
| Move, pan, zoom | Drag a node, drag the background, scroll. **Fit** and **Auto layout** tidy up |

Colors show the kind of feature: orange for feature rules, purple for lists that
branch (aggregate, sequence, weighted random, conditional list), blue for
modifiers, and green for blocks.

Lists that can branch, such as aggregate, have an extra empty row at the bottom;
drag from its dot to add another connection.

## Behavior to know about

- A dashed node is an identifier that is referenced but not defined in this
  file (for example a vanilla feature, or one in another file). Other files are
  not loaded. **Create feature...** on a dashed node defines it here.
- If the file has a syntax error, the last valid graph stays visible but is
  read-only until the error is fixed in the text editor.
- Features with a missing or duplicated identifier get a warning. A duplicated
  identifier cannot be used as a connection target.
- Node positions are remembered while the editor is open but are not written to
  the file.
- If the file changes underneath an unapplied JSON5 draft, **Apply changes** is
  disabled until you use **Reload from file**, so a draft never overwrites newer
  text.
- Applying a JSON5 draft requires `format_version`, exactly one feature type,
  and `description.identifier`, the same rules the filter enforces.

## Supported connections

Feature rules (`places_feature`), aggregate, sequence, weighted random,
conditional list, height difference filter, scatter, search, snap to surface,
surface relative threshold, vegetation patch, and the log decoration feature
inside tree trunks. Other feature types still appear as nodes and can be edited
as JSON5, but their references are not drawn. Tree connections need the
relevant trunk object (`fallen_trunk` or `poplar_trunk`) to exist first.

New features use format version `1.21.90`. The editor does not validate feature
contents against Minecraft's schemas; use the schema from the filter's
documentation for that.

## Development

```
npm install
npm test
```

The tests cover the text-editing model, including comment and formatting
preservation, and the extension host against a fake VS Code API.
