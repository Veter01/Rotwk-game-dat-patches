# Add map search to the lobby

Filter the lobby map list by typing part of a map name.

## Reproduce the patch

Run the [patch builder](../README.md#build-a-patched-game-file) with `map-search`.

## Implementation

The `.mapsvar` section stores the search state. The `.mapfind` hooks integrate input, list population and lifecycle reset. The patch supplies the `APT:MapSearch` localization key and includes case handling for Latin and Cyrillic characters. Add the corresponding label to the mod's `lotr.str` and verify the layout in the target lobby UI.

The table identifies the corresponding changed byte ranges. The builder supplies any shared code and data sections.

| File offset | Preferred VA | Original bytes | Replacement bytes |
|---|---|---|---|
| `0x0009FC37` | `0x0049FC37` | `8b 4d 08 e8 33 5d 27 00` | `e9 22 34 a9 00 90 90 90` |
| `0x00322745` | `0x00722745` | `55 8b ec 83 ec 18` | `e9 db 08 81 00 90` |
| `0x00440879` | `0x00840879` | `89 9e 94 03 00 00` | `e9 28 28 6f 00 90` |
| `0x00440906` | `0x00840906` | `55 8b ec 83 ec 14` | `e9 f5 26 6f 00 90` |
| `0x004465EA` | `0x008465EA` | `8b 86 f4 00 00 00` | `e9 99 ca 6e 00 90` |
| `0x004467A9` | `0x008467A9` | `d8 d4 ff ff` | `16 cd 6e 00` |

## Verify in ROTWK

Open the map picker and enter partial names in different cases. Include a localized map name if your package provides one. Backspace and clear the search, switch categories, then reopen the picker. Check that the map launched is the map selected in the filtered list.

[Back to the patch index](../README.md#feature-index)
