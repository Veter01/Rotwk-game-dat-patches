# Restore the builder selection click

The builder selection action plays the Palantír interface click.

## Reproduce the patch

Run the [patch builder](README.md#build-a-patched-game-file) with `input`.

## Implementation

The selection notification at `0x0092DB1F` enters `.hotkeys+0x4D6`. It calls the audio event helper at `0x00815772` with `Gui_PalantirCommandButtonClick` and then resumes the selection flow. The alternate builder path at `0x0069E17D` now plays the same event. The event is a UI click. Individual builder voice lines use the game's normal audio data.

The table identifies the corresponding changed byte ranges. The builder supplies any shared code and data sections.

| File offset | Preferred VA | Original bytes | Replacement bytes |
|---|---|---|---|
| `0x0029E17D` | `0x0069E17D` | `8b 0d 7c 44 de 00 8b 01 83 c6 38 56 ff 50 54` | `68 18 c4 c8 00 e8 eb 75 17 00 83 c4 04 90 90` |
| `0x0052DB1F` | `0x0092DB1F` | `80 7d 08 00 5b 75 26` | `e9 b2 a9 60 00 90 90` |

## Verify in ROTWK

Enable Sound Effects, select a builder from the builder control and cycle with its hotkey. Listen for one click per successful selection. Confirm that selection still succeeds with Sound Effects disabled.

[Back to the patch index](README.md#feature-index)
