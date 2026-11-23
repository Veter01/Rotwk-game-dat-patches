# Extend War of the Ring from six to eight players

The engine changes make room for War of the Ring scenario slots seven and eight.

## Reproduce the patch

Run the [patch builder](../README.md#build-a-patched-game-file) with `wotr`.

## Implementation

The setup and presentation checks at `0x00840A91` and `0x0084692B` use `8` in place of `6`. `.wotrui` and `.wotrobs` handle the related slot UI and observer logic. `.wtrdisp` loads `wotr8\scenario.big` and carries scenario display adjustments. Supply the matching scenario archive with eight available combatant slots, supported teams, starting regions and the UI entries used by your mod. Populate and validate the scenario data first, then package it as `scenario.big` under the `wotr8` directory relative to the game installation. Keep its internal paths consistent with the existing War of the Ring scenario archive format. The two binary inputs contained no scenario data.

The table identifies the corresponding changed byte ranges. The builder supplies any shared code and data sections.

| File offset | Preferred VA | Original bytes | Replacement bytes |
|---|---|---|---|
| `0x003BAABE` | `0x007BAABE` | `6a 00 6a 18 68 f0 62 da 00` | `e9 3d 45 77 00 90 90 90 90` |
| `0x00440A91` | `0x00840A91` | `06` | `08` |
| `0x00441691` | `0x00841691` | `c7 04 24 31 03 84 00` | `e9 6a 69 6e 00 90 90` |
| `0x0044692B` | `0x0084692B` | `06` | `08` |
| `0x005760B4` | `0x009760B4` | `8d 45 0c 50 ff 52 38` | `e9 6b 8f 5b 00 90 90` |
| `0x005765B3` | `0x009765B3` | `8d 45 dc 50 ff 52 38` | `e9 87 8a 5b 00 90 90` |
| `0x00576BA8` | `0x00976BA8` | `8d 45 ec 50 ff 52 38` | `e9 b0 84 5b 00 90 90` |

## Verify in ROTWK

Open an eight-player scenario, populate slots seven and eight, start the campaign and advance several turns. Trigger a tactical battle involving each additional slot, then save, reload and confirm that the slots, ownership and armies persist.

[Back to the patch index](../README.md#feature-index)
