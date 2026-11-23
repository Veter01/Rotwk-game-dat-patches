# Expand engine display-mode support

The display-mode enumeration can expose more modes reported by the graphics adapter.

## Reproduce the patch

Run the [patch builder](README.md#build-a-patched-game-file) with `display-modes`.

## Implementation

The conditional skips at `0x004451BB` and `0x00445229` are removed. The replacement enumerator at `0x004451CE` uses the device's mode table and orders qualifying entries by width, height and format information. Its inner loop explicitly filters widths below 800 and formats at or below 23. Availability also depends on the adapter, display and graphics backend.

The table identifies the corresponding changed byte ranges. The builder supplies any shared code and data sections.

| File offset | Preferred VA | Original bytes | Replacement bytes |
|---|---|---|---|
| `0x000451BB` | `0x004451BB` | `76 01` | `90 90` |
| `0x000451CE` | `0x004451CE` | `55 8b ec 51 53` | `e9 2d ce ad 00` |
| `0x00045229` | `0x00445229` | `76 0b` | `90 90` |

## Verify in ROTWK

Compare the enumerated modes against the same machine's available display modes. Test common widescreen, ultrawide and high-resolution entries that the adapter actually offers. Apply a mode, restart and verify the selected resolution.

[Back to the patch index](README.md#feature-index)
