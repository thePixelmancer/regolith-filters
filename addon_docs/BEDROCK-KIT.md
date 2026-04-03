# bedrock-kit — API Reference

`bedrock-kit` is a TypeScript library for reading and navigating Minecraft Bedrock Edition addon files. It works in both Node.js and browsers.

---

## Loading

```ts
import { AddOn } from "bedrock-kit";

// Node.js — reads BP and RP directories from disk
const addon = await AddOn.fromDisk("./behavior_pack", "./resource_pack");
const addon = await AddOn.fromDisk("./behavior_pack"); // RP is optional

// Browser — pass File[] arrays from folder pickers
const addon = await AddOn.fromFiles(bpFiles, rpFiles);
```

---

## Top-Level Collections

All collections on `addon` are `AssetCollection<T>` — a typed, iterable map wrapper.

| Property | Type | Contents |
|---|---|---|
| `addon.items` | `AssetCollection<Item>` | BP item definitions |
| `addon.blocks` | `AssetCollection<Block>` | BP block definitions |
| `addon.entities` | `AssetCollection<Entity>` | Unified BP+RP entity views |
| `addon.recipes` | `AssetCollection<Recipe>` | BP recipe files |
| `addon.lootTables` | `AssetCollection<LootTable>` | BP loot table files |
| `addon.trading` | `AssetCollection<TradingTable>` | BP villager trading tables |
| `addon.biomes` | `AssetCollection<Biome>` | Unified BP+RP biome views |
| `addon.animations` | `AssetCollection<Animation>` | RP animation definitions |
| `addon.animationControllers` | `AssetCollection<AnimationController>` | RP animation controllers |
| `addon.renderControllers` | `AssetCollection<RenderController>` | RP render controllers |
| `addon.particles` | `AssetCollection<Particle>` | RP particle effects |
| `addon.geometries` | `AssetCollection<GeometryModel>` | RP geometry models |
| `addon.attachables` | `AssetCollection<Attachable>` | RP attachable definitions |
| `addon.features` | `AssetCollection<Feature>` | BP world generation features |
| `addon.featureRules` | `AssetCollection<FeatureRule>` | BP feature placement rules |
| `addon.fogs` | `AssetCollection<Fog>` | RP fog definitions |
| `addon.textures` | `AssetCollection<Texture>` | RP texture files (Node.js only) |
| `addon.sounds` | `SoundDefinitionsFile \| undefined` | RP `sound_definitions.json` |
| `addon.music` | `MusicDefinitionsFile \| undefined` | RP `music_definitions.json` |
| `addon.bpManifest` | `ManifestFile \| undefined` | BP `manifest.json` |
| `addon.rpManifest` | `ManifestFile \| undefined` | RP `manifest.json` |
| `addon.languages` | `{ get(lang?): LangFile \| undefined }` | Localization files |

---

## AssetCollection\<T\>

All top-level collections share the same interface.

```ts
// Lookup
collection.get("minecraft:zombie")   // T | undefined
collection.has("minecraft:zombie")   // boolean
collection.size                      // number

// Iteration
collection.all()                     // T[]
collection.keys()                    // IterableIterator<string>
collection.values()                  // IterableIterator<T>
collection.entries()                 // IterableIterator<[string, T]>
for (const x of collection) { }
[...collection]

// Functional helpers
collection.filter(fn)                // AssetCollection<T>
collection.map(fn)                   // U[]
collection.find(fn)                  // T | undefined
collection.some(fn)                  // boolean
collection.every(fn)                 // boolean
collection.reduce(fn, init)          // U
collection.groupBy(fn)               // Record<K, T[]>
```

Collections are keyed by the asset's `id`:
- Most assets: namespaced identifier, e.g. `"minecraft:zombie"`
- Recipes: `description.identifier` from the JSON (falls back to filename without extension)
- Loot tables: relative file path from BP root, e.g. `"loot_tables/entities/zombie.json"`
- Trading tables: filename, e.g. `"economy_trade_table.json"`

---

## Item

```ts
const item = addon.items.get("mypack:copper_spear"); // Item | undefined

item.id              // "mypack:copper_spear"
item.displayName     // "Copper Spear" — en_US lang lookup, falls back to id
item.texture         // Texture | undefined — resolved from item_texture.json
item.attachable      // Attachable | undefined
item.recipes         // Recipe[] — recipes whose result is this item
item.entities        // Entity[] — entities that can drop this item via loot tables
item.droppedByBlocks // Block[] — blocks that drop this item via loot table
item.data            // Record<string, unknown> — raw JSON
item.filePath        // absolute path to the BP item file
item.docstrings      // CommentBlock[] — JSDoc blocks parsed from the source file
```

---

## Block

```ts
const block = addon.blocks.get("mypack:coal_ore"); // Block | undefined

block.id          // "mypack:coal_ore"
block.displayName // "Coal Ore" — tries tile.*, block.*, item.*, entity.* lang keys
block.texture     // Texture | undefined — resolved from terrain_texture.json
block.lootTable   // LootTable | undefined
block.soundEvents // SoundEventBinding[]
block.data        // Record<string, unknown>
block.filePath    // absolute path
block.docstrings  // CommentBlock[]
```

---

## Entity

`Entity` is a logical grouping — not itself file-backed. Raw data lives on `.behavior` and `.resource`.

```ts
const entity = addon.entities.get("minecraft:zombie"); // Entity | undefined

entity.id           // "minecraft:zombie"
entity.displayName  // "Zombie"
entity.behavior     // BehaviorEntity | undefined  (BP file)
entity.resource     // ResourceEntity | undefined  (RP file)
entity.spawnRule    // SpawnRule | undefined
entity.lootTables   // LootTable[]
entity.soundEvents  // SoundEventBinding[] — BP + RP merged, BP takes precedence
entity.docstrings   // CommentBlock[] — from behavior, falls back to resource
```

### BehaviorEntity

```ts
entity.behavior.id              // "minecraft:zombie"
entity.behavior.displayName     // "Zombie"
entity.behavior.lootTables      // LootTable[]
entity.behavior.spawnRule       // SpawnRule | undefined
entity.behavior.soundEvents     // SoundEventBinding[]
entity.behavior.entity          // Entity | undefined — back-link to unified view
entity.behavior.resource        // ResourceEntity | undefined — cross-link
entity.behavior.data            // raw BP entity JSON
entity.behavior.filePath        // absolute path to BP entity file
entity.behavior.docstrings      // CommentBlock[]
```

### ResourceEntity

```ts
entity.resource.id                    // "minecraft:zombie"
entity.resource.displayName           // "Zombie"
entity.resource.textures              // Record<string, Texture> — shortname → Texture
entity.resource.animations            // Array<{ shortname: string; animation: Animation }>
entity.resource.animationControllers  // Array<{ shortname: string; controller: AnimationController }>
entity.resource.renderControllers     // RenderController[]
entity.resource.particles             // Array<{ shortname: string; particle: Particle }>
entity.resource.soundEvents           // SoundEventBinding[]
entity.resource.animationShortnames   // Record<string, string> — shortname → full id
entity.resource.particleShortnames    // Record<string, string>
entity.resource.soundShortnames       // Record<string, string>
entity.resource.renderControllerIds   // string[]
entity.resource.entity                // Entity | undefined — back-link to unified view
entity.resource.behavior              // BehaviorEntity | undefined — cross-link
entity.resource.data                  // raw RP entity JSON
entity.resource.filePath              // absolute path to RP entity file
entity.resource.docstrings            // CommentBlock[]
```

---

## Recipe

Keyed by `description.identifier` (falls back to filename without extension).

```ts
const recipe = addon.recipes.get("mypack:copper_spear"); // Recipe | undefined

recipe.id           // "mypack:copper_spear"
recipe.type         // "shaped" | "shapeless" | "furnace" | "brewing_mix" | "brewing_container" | "unknown"
recipe.result       // ItemStack | undefined
recipe.item         // Item | undefined — shortcut for recipe.result?.item
recipe.ingredients  // (Item | Tag)[] — flat, empty slots excluded

recipe.resolveShape()      // Ingredient[][] | undefined  — 2D grid, null for empty slots
recipe.resolveShapeless()  // ShapelessIngredient[] | undefined
recipe.resolveFurnace()    // FurnaceResolved | undefined
recipe.resolveBrewing()    // BrewingResolved | undefined
recipe.usesItem(id)        // boolean

// Preferred access: item.recipes
const recipes = addon.items.get("mypack:copper_spear")?.recipes;
```

### ItemStack

```ts
const stack = recipe.result;
stack.id    // "mypack:copper_spear"
stack.count // number
stack.item  // Item | undefined  (undefined for vanilla/unknown items)
```

---

## LootTable

Keyed by relative path from BP root (e.g. `"loot_tables/entities/zombie.json"`).

```ts
const table = addon.lootTables.get("loot_tables/entities/zombie.json");

table.id              // "loot_tables/entities/zombie.json"
table.itemIds         // string[] — all item ids that can drop
table.items           // Item[] — resolved addon items (vanilla excluded)
table.sourceEntities  // Entity[] — entities referencing this table
table.sourceBlocks    // Block[] — blocks referencing this table
table.data            // raw JSON
table.filePath        // absolute path
table.docstrings      // CommentBlock[]
```

---

## SpawnRule

```ts
const rule = entity.spawnRule; // SpawnRule | undefined

rule.id        // "minecraft:zombie"
rule.biomeTags // string[] — deduplicated values from biome_filter conditions
rule.entity    // Entity | undefined — back-link to unified entity
rule.data      // raw JSON
rule.filePath  // absolute path
rule.docstrings // CommentBlock[]
```

---

## Biome

`Biome` is a logical grouping — not itself file-backed. Raw data lives on `.behavior` and `.resource`.

```ts
const biome = addon.biomes.get("mypack:maple_forest"); // Biome | undefined

biome.id               // "mypack:maple_forest"
biome.behavior         // BehaviorBiome | undefined  (BP file)
biome.resource         // ClientBiome | undefined    (RP file)
biome.entities         // Entity[] — entities with spawn rules for this biome
biome.musicDefinition  // MusicDefinitionEntry | undefined
biome.fog              // Fog | undefined — shortcut for biome.resource?.fog
biome.ambientSounds    // SoundEventBinding[] — shortcut for biome.resource?.ambientSounds
biome.docstrings       // CommentBlock[] — from behavior, falls back to resource
```

### BehaviorBiome

```ts
biome.behavior.id               // "mypack:maple_forest"
biome.behavior.entities         // Entity[] — matching spawn rules
biome.behavior.musicDefinition  // MusicDefinitionEntry | undefined
biome.behavior.biome            // Biome | undefined — back-link to unified view
biome.behavior.data             // raw BP biome JSON
biome.behavior.filePath         // absolute path
biome.behavior.docstrings       // CommentBlock[]
```

### ClientBiome

```ts
biome.resource.id            // "mypack:maple_forest"
biome.resource.fog           // Fog | undefined — resolved Fog object
biome.resource.ambientSounds // SoundEventBinding[]
biome.resource.biome         // Biome | undefined — back-link to unified view
biome.resource.data          // raw RP client biome JSON — access skyColor, foliageColor, waterColor etc. via data
biome.resource.filePath      // absolute path
biome.resource.docstrings    // CommentBlock[]
```

---

## Texture

Keyed by relative path without extension (e.g. `"textures/blocks/maple_log"`).
Only populated in Node.js (disk) mode — empty in browser mode.

```ts
const tex = addon.textures.get("textures/blocks/maple_log"); // Texture | undefined

tex.id          // "textures/blocks/maple_log"
tex.filePath    // absolute path to PNG/TGA

// PBR companion textures (resolved from <name>.texture_set.json)
tex.textureSet  // Record<string, unknown> | undefined — raw texture_set data
tex.normal      // Texture | undefined — normal map
tex.heightmap   // Texture | undefined — heightmap (alternative to normal)
tex.mer         // Texture | undefined — metalness/emissive/roughness

tex.getPixelData() // Buffer | undefined — raw file bytes (Node.js only)

// Reverse lookups (lazy, O(1) via shared index)
tex.usedByBlocks    // Block[]
tex.usedByItems     // Item[]
tex.usedByEntities  // Entity[] — includes spawn egg textures
```

---

## Fog

```ts
const fog = addon.fogs.get("mypack:maple_forest_fog"); // Fog | undefined

fog.id         // "mypack:maple_forest_fog"
fog.data       // raw fog settings JSON
fog.filePath   // absolute path to RP fogs file
fog.docstrings // CommentBlock[]
```

---

## Feature & FeatureRule

```ts
const feature = addon.features.get("mypack:maple_tree"); // Feature | undefined

feature.id                   // "mypack:maple_tree"
feature.featureType          // full JSON root key, e.g. "minecraft:tree_feature"
feature.placedByFeatureRules // FeatureRule[] — rules that place this feature
feature.data                 // raw JSON
feature.filePath             // absolute path
feature.docstrings           // CommentBlock[]

const rule = addon.featureRules.get("mypack:maple_tree_rule"); // FeatureRule | undefined

rule.id              // "mypack:maple_tree_rule"
rule.placesFeatureId // string | undefined — raw feature ID
rule.placesFeature   // Feature | undefined — resolved Feature object
rule.data            // raw JSON — access placementPass, conditions etc. via data
rule.filePath        // absolute path
rule.docstrings      // CommentBlock[]
```

---

## Sounds

```ts
// sound_definitions.json
const entry = addon.sounds?.get("mob.zombie.say"); // SoundDefinitionEntry | undefined

entry.id    // "mob.zombie.say"
entry.files // SoundFile[] — parsed audio file entries
entry.data  // raw entry data — access category, stream, volume etc. via data

addon.sounds?.all()  // SoundDefinitionEntry[]
addon.sounds?.ids    // string[]
addon.sounds?.size   // number

// SoundFile shape
file.name            // string — e.g. "sounds/mob/zombie/say1"
file.volume          // number | undefined
file.pitch           // number | undefined
file.weight          // number | undefined
file.is3D            // boolean | undefined
file.stream          // boolean | undefined
file.loadOnLowMemory // boolean | undefined

// music_definitions.json
const music = addon.music?.get("bamboo_jungle"); // MusicDefinitionEntry | undefined

music.id        // "bamboo_jungle"
music.eventName // string — e.g. "music.overworld.bamboo_jungle"
music.data      // raw entry data — access min_delay, max_delay etc. via data

addon.music?.all()
addon.music?.ids   // string[]
addon.music?.size  // number
```

### SoundEventBinding

Returned by `entity.soundEvents`, `block.soundEvents`, `biome.resource.ambientSounds`.

```ts
binding.event        // string — e.g. "step", "hurt", "ambient"
binding.definitionId // string — maps to a sound_definitions.json key
binding.volume       // number
binding.pitch        // number
```

---

## Visuals

### Animation / AnimationController

```ts
const anim = addon.animations.get("animation.zombie.walk");
anim.id        // "animation.zombie.walk"
anim.data      // raw animation data
anim.filePath
anim.docstrings

const ctrl = addon.animationControllers.get("controller.animation.zombie.general");
ctrl.id    // "controller.animation.zombie.general"
ctrl.data  // raw controller data — access states, initial_state etc. via data
```

### RenderController

```ts
const rc = addon.renderControllers.get("controller.render.zombie");
rc.id    // "controller.render.zombie"
rc.data  // raw controller data — access geometry, textures, materials via data
```

### Particle

```ts
const particle = addon.particles.get("minecraft:smoke_particle");
particle.id       // "minecraft:smoke_particle"
particle.texture  // Texture | undefined — resolved from basic_render_parameters.texture
particle.data     // raw particle data — access components, emitter settings via data
```

### GeometryModel

```ts
const geo = addon.geometries.get("geometry.humanoid");
geo.id    // "geometry.humanoid"
geo.data  // raw geometry data — access bones, textureWidth, textureHeight via data
```

### Attachable

```ts
const att = addon.attachables.get("mypack:copper_spear");
att.id       // "mypack:copper_spear"
att.textures // Record<string, Texture> — shortname → resolved Texture
att.data     // raw attachable data — access materials, geometry via data
```

---

## Languages

```ts
const en = addon.languages.get("en_US"); // LangFile | undefined
en?.get("item.minecraft.stick.name")     // "Stick" | key if not found
```

---

## Manifests

```ts
addon.bpManifest?.data   // raw manifest JSON
addon.rpManifest?.data
```

---

## File Path Lookup

```ts
// Untyped
const asset = addon.getAssetByPath("entities/zombie.json"); // Asset | undefined

// Typed — returns undefined if found but wrong type
const entity = addon.getAssetByPath("entities/zombie.json", BehaviorEntity);
const recipe = addon.getAssetByPath("recipes/copper_spear.json", Recipe);
const item   = addon.getAssetByPath("items/copper_spear.json", Item);
```

Matching is case-insensitive and suffix-based. For BP entity files the linked `ResourceEntity` is also reachable via the same path.

---

## Asset Base Class

All file-backed classes extend `Asset`:

```ts
asset.filePath    // absolute path (empty string in browser mode)
asset.data        // Record<string, unknown> — raw parsed JSON
asset.docstrings  // CommentBlock[] — JSDoc blocks parsed from the source file
```

`Entity` and `Biome` do **not** extend `Asset` — they are logical view nodes with no backing file.

---

## TradingTable

```ts
const table = addon.trading.get("economy_trade_table.json");
table.id      // filename
table.tiers   // TradeTier[]

// tier.trades   → Trade[]
// trade.gives   → TradeItem[]
// trade.wants   → TradeItem[]
```

---

## Tag

Used in recipe ingredients when the ingredient is a tag rather than a specific item.

```ts
ingredient instanceof Tag  // true
ingredient.id              // "minecraft:planks"
```
