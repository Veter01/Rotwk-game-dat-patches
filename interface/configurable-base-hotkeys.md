# Add and repair the basic configurable hotkeys

The shared Options input layer registers configurable controls and routes them through the engine's normal command dispatch.

## Reproduce the patch

Run the [patch builder](../README.md#build-a-patched-game-file) with `input`.

## Implementation

The `.optui` hooks integrate settings load, lookup and save. `.wmkeys` contains the option records and `.keycmd`, `.keydef` and `.hotkeys` handle matching, defaults and runtime routing. The table includes camera turn, zoom, camera reset, builder selection, Stop, Attack Move, the build-path or select-matching action, spellbook, Sell, map-wide selection and hero selection. The menu and runtime input handlers are a shared bundle with the other controls and settings in these guides.

The table identifies the corresponding changed byte ranges. The builder supplies any shared code and data sections.

| File offset | Preferred VA | Original bytes | Replacement bytes |
|---|---|---|---|
| `0x001DA8F0` | `0x005DA8F0` | `a1 38 36 de 00 8b 70 0c eb 6c` | `e9 dc 01 96 00 e9 c7 d7 95 00` |
| `0x001DA910` | `0x005DA910` | `85 7e 14 74 4f` | `e9 eb e6 95 00` |
| `0x001DA982` | `0x005DA982` | `8b 0d 98 63 de 00` | `e9 6f 01 96 00 90` |
| `0x001ED37A` | `0x005ED37A` | `55 8b ec 83 7d 10 00` | `e9 14 5d 93 00 90 90` |
| `0x00412C89` | `0x00812C89` | `55 8b ec 83 ec 1c` | `e9 a8 53 72 00 90` |
| `0x00412EDA` | `0x00812EDA` | `83 7f 04 01 75 70` | `e9 88 51 72 00 90` |
| `0x005204D9` | `0x009204D9` | `8d 4d cc e8 6b 22 e9 ff` | `e9 49 2b 60 00 90 90 90` |
| `0x00520602` | `0x00920602` | `0f 85 89 01 00 00` | `e9 f9 29 60 00 90` |
| `0x005212BA` | `0x009212BA` | `33 c9 89 5d c8` | `e9 08 1e 60 00` |
| `0x0059106B` | `0x0099106B` | `8b 01 ff 50 7c 85 c0 74 2a` | `e9 10 85 5a 00 90 90 90 90` |

The menu references `APT:ETHotkeys`, `APT:ETKeyDefault` and `APT:ETKeyDefaultSuffix`. Keep the associated strings and the target UI's hotkey rows together when porting.

## Verify in ROTWK

Assign distinctive keys, apply, restart the game and test every action in a skirmish. Rebind a command to a key used elsewhere and inspect the conflict behavior. Restore defaults and retest mouse and keyboard input.

[Back to the patch index](../README.md#feature-index)
