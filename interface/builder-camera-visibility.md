# Keep the camera in place for on-screen builders

Selecting a builder preserves the current camera position when the builder is visible. The camera can still move to an off-screen builder.

## Reproduce the patch

Run the [patch builder](../README.md#build-a-patched-game-file) with `input`.

## Implementation

The camera helper at `.camfix+0x60` projects the selected object's world position through the view and checks the current viewport bounds. The visible case returns without changing the camera. The off-screen case uses the engine's normal camera centering call. The selection path around `0x0092DB1F` routes the applicable selection mode to this helper.

The table identifies the corresponding changed byte ranges. The builder supplies any shared code and data sections.

| File offset | Preferred VA | Original bytes | Replacement bytes |
|---|---|---|---|
| `0x0029E17D` | `0x0069E17D` | `8b 0d 7c 44 de 00 8b 01 83 c6 38 56 ff 50 54` | `68 18 c4 c8 00 e8 eb 75 17 00 83 c4 04 90 90` |
| `0x0052DB1F` | `0x0092DB1F` | `80 7d 08 00 5b 75 26` | `e9 b2 a9 60 00 90 90` |
| `0x0052DB80` | `0x0092DB80` | `ff 74 24 04` | `6a 01 90 90` |

## Verify in ROTWK

Select an on-screen builder and confirm that the camera stays in place. Move the camera far away and select the same builder. Verify that the camera brings the builder into view. Repeat near all four edges at two screen resolutions.

[Back to the patch index](../README.md#feature-index)
