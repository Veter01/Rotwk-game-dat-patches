# Cycle through all hired builders

The builder hotkey can cycle through newly hired builders when the player has more than two.

## Reproduce the patch

Run the [patch builder](README.md#build-a-patched-game-file) with `input`.

## Implementation

The builder dispatch at `0x0081FAAB` routes meta command `0x5F` through `.hotkeys` to the builder scan. The fallback enumerates the player's drawable list through `.keydef+0x2C3`, tracks the currently selected builder and wraps to the first eligible one. The candidate test checks ownership, selectability and the build action. Keep the builder filtering in [the worker hotkey guide](06-builder-worker-hotkey-filter.md) when porting the traversal.

The table identifies the corresponding changed byte ranges. The builder supplies any shared code and data sections.

| File offset | Preferred VA | Original bytes | Replacement bytes |
|---|---|---|---|
| `0x0041FAAB` | `0x0081FAAB` | `83 fe 5c 0f 85 b8 0c 00 00` | `e9 50 85 71 00 90 90 90 90` |
| `0x0052DB1F` | `0x0092DB1F` | `80 7d 08 00 5b 75 26` | `e9 b2 a9 60 00 90 90` |
| `0x0052DB80` | `0x0092DB80` | `ff 74 24 04` | `6a 01 90 90` |

## Verify in ROTWK

Hire ten builders from multiple production points. Press the builder hotkey ten times and log which builder is selected each time. Check that selection wraps after all eligible builders have been visited, and repeat after hiring and losing a builder.

[Back to the patch index](README.md#feature-index)
