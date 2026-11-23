# Keep units moving when switching to Defensive Stance

Switching stance preserves movement on the eligible AI update path.

## Reproduce the patch

Run the [patch builder](../README.md#build-a-patched-game-file) with `stances`.

## Implementation

At `0x00862161` the stance handler jumps to `.stancem`. The helper checks the AI update component and its state byte and calls the existing virtual predicate before choosing whether to run the original stop path. Other stance rules are handled by the game as before.

The table identifies the corresponding changed byte ranges. The builder supplies any shared code and data sections.

| File offset | Preferred VA | Original bytes | Replacement bytes |
|---|---|---|---|
| `0x00462161` | `0x00862161` | `8b 9b 60 02 00 00 85 db 74 0a` | `e9 9a 1e 6d 00 90 90 90 90 90` |

## Verify in ROTWK

Issue a move order to a unit or horde, then switch to Defensive Stance during movement. Confirm it continues toward the destination. Also test a queued route, an idle unit and an explicit Stop command.

[Back to the patch index](../README.md#feature-index)
