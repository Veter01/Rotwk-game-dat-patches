# Enforce the construction limit

The placement limit includes relevant structures already under construction.

## Reproduce the patch

Run the [patch builder](README.md#build-a-patched-game-file) with `construction-limit`.

## Implementation

At `0x0079406F` the limit check passes the callback in `.bldcap` to the existing object enumeration. The wrapper invokes the original counting function, then checks construction state flags and the template match before adding a qualifying pending structure. Keep the original counter and the additional state filters when adapting the callback.

The table identifies the corresponding changed byte ranges. The builder supplies any shared code and data sections.

| File offset | Preferred VA | Original bytes | Replacement bytes |
|---|---|---|---|
| `0x00394070` | `0x00794070` | `12 3d 79` | `00 10 f2` |

## Verify in ROTWK

Set a small construction limit on a test building. Place blueprints up to the limit and attempt one more before any finish. Cancel one, verify that a new slot is available, then repeat with completed buildings, multiple builders and another player.

[Back to the patch index](README.md#feature-index)
