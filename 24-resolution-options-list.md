# Add missing entries to the resolution settings

Expose the expanded mode list in the in-game Options screen.

## Reproduce the patch

Run the [patch builder](README.md#build-a-patched-game-file) with `input display-modes`.

## Implementation

The display-mode bundle supplies the broader engine list through `.ressort`. The Options layer uses `Options::Resolution` and `APT:ETResolution` for its control and label, consuming the list from the engine. This is the UI part of the change documented in [the display-mode guide](23-display-mode-support.md).

The table identifies the corresponding changed byte ranges. The builder supplies any shared code and data sections.

| File offset | Preferred VA | Original bytes | Replacement bytes |
|---|---|---|---|
| `0x000451CE` | `0x004451CE` | `55 8b ec 51 53` | `e9 2d ce ad 00` |
| `0x00239FEF` | `0x00639FEF` | `8b 0d 7c 44 de 00` | `e9 87 90 8e 00 90` |
| `0x005204D9` | `0x009204D9` | `8d 4d cc e8 6b 22 e9 ff` | `e9 49 2b 60 00 90 90 90` |
| `0x00520602` | `0x00920602` | `0f 85 89 01 00 00` | `e9 f9 29 60 00 90` |
| `0x005212BA` | `0x009212BA` | `33 c9 89 5d c8` | `e9 08 1e 60 00` |

## Verify in ROTWK

Open Graphics settings and compare the resolution choices with your display-mode list. Select a newly available mode, apply it, close and reopen Options, and verify the saved resolution after a restart.

[Back to the patch index](README.md#feature-index)
