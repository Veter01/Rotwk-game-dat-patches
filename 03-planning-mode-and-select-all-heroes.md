# Add Planning Mode and Select All Heroes hotkeys

Expose Planning Mode and Select All Heroes as configurable in-game actions.

## Reproduce the patch

Run the [patch builder](README.md#build-a-patched-game-file) with `input`.

## Implementation

The settings records use `Options::ETKeyTacticalMenu` for Planning Mode and `Options::ETKeySelectAllHeroes` for hero selection. The two meta entries are `0x99` and `0xAB`. The latter is routed by `.hotkeys+0x510` and uses the normal hero-selection screen object. The name `ETKeyTacticalMenu` is the internal setting name used by this build.

The table identifies the corresponding changed byte ranges. The builder supplies any shared code and data sections.

| File offset | Preferred VA | Original bytes | Replacement bytes |
|---|---|---|---|
| `0x0041F983` | `0x0081F983` | `ba 82 00 00` | `e9 88 8b 71` |
| `0x0052C8C4` | `0x0092C8C4` | `55 8b ec 83 ec 14` | `e9 eb e2 60 00 90` |
| `0x0052CA55` | `0x0092CA55` | `8b 7d f0 c6 45 fc 00` | `e9 78 e1 60 00 90 90` |
| `0x0052CDB1` | `0x0092CDB1` | `8b 49 08 e8 0b fb ff ff` | `eb 06 90 90 90 90 90 90` |

Use the matching Options interface and language strings from the target mod. The original in-game button for selecting heroes is a separate entry point.

## Verify in ROTWK

Bind an unused key to each action. Toggle Planning Mode twice, then select all heroes with two living heroes at different locations. Save the bindings, restart the game and repeat. Test the former default separately with a custom binding.

[Back to the patch index](README.md#feature-index)
