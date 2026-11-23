# Create and import larger WorldBuilder maps

The patch raises the maximum New and Resize map dimensions from 600 × 600 to 2000 × 2000. The heightmap TGA importer accepts up to 2000 pixels per axis, up from 1024.

## Apply

From the directory that contains the [patcher](patch_worldbuilder.py) and its [data file](patch-data.json), run

```powershell
py -3 .\patch_worldbuilder.py .\worldbuilder.exe .\worldbuilder-maps.exe --patch map
```

The map mode also sets the [large address flag](large-address-space.md). The default `full` mode installs the map changes together with the expanded Player List.

## Implementation

| Path | Change |
|---|---|
| New and Resize dialogs | Change the six limit operands at raw offsets `0x176512`, `0x17652E`, `0x176C6C`, `0x176CB7`, `0x177228`, and `0x1773D8` from `0x0258` to `0x07D0`. |
| Heightmap import | Change the two operands at `0x2A93BA` and `0x2A93C9` from `0x0400` to `0x07D0`. |
| Terrain texture resolution | The hook at preferred VA `0x00771F48` enters `.wbtex` and caps the flat texture resolution parameter at 8 above 2304 terrain chunks and at 4 above 6400 chunks. This reduces memory use on large maps at the cost of terrain texture detail. |
| TGA texture decoding | Hooks at `0x007709CF`, `0x00770A2C`, `0x00770B68`, and `0x00770F83` change temporary strip allocation. The helper allocates `width × 64 × 4` bytes per strip, uses a second strip when a normal map is present, and releases the allocation after decoding. |

Keep the section layout and allocation hooks together when porting this patch. The [patch data](patch-data.json) contains the original and replacement bytes for the supported build.

## Verify

Create, save, and reopen a 2000 × 2000 map. Resize a smaller map to that limit and import a square TGA heightmap at the new limit. Pan across textured terrain and check for missing tiles or decoding failures. Try one dimension above the limit to verify that the dialog rejects it.

[Back to the WorldBuilder index](README.md)
