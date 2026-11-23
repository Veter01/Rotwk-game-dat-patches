# Extend lobby faction IDs to 127

The lobby patch extends faction ID handling for builds with more than the previous 14 factions.

## Reproduce the patch

Run the [patch builder](../README.md#build-a-patched-game-file) with `factions`.

## Implementation

The wrappers at `.lobfac+0x00` and `.lobfac+0x25` extend lobby faction serialization and decoding. Two write sites and two read sites use the wrappers. The reader initializes an absent extension byte to `0x80` before accepting a supplied byte. Keep the sender and receiver changes together. Declare the additional factions in the mod's existing faction data and update the lobby assets if they contain a fixed list.

The table identifies the corresponding changed byte ranges. The builder supplies any shared code and data sections.

| File offset | Preferred VA | Original bytes | Replacement bytes |
|---|---|---|---|
| `0x0044AB5F` | `0x0084AB5F` | `d4 f9 ff ff` | `9d e4 68 00` |
| `0x0044AC0D` | `0x0084AC0D` | `26 f9 ff ff` | `ef e3 68 00` |
| `0x0044B474` | `0x0084B474` | `41 84 12` | `ad db 68` |
| `0x0044B76B` | `0x0084B76B` | `4a 81 12` | `b6 d8 68` |

## Verify in ROTWK

Use matched clients. Create a lobby with factions on both sides of the old boundary, select IDs near the upper limit and verify that both clients show and spawn the same faction after starting. Also test Random and spectator slots. This binary comparison establishes the transport changes. The full roster capacity still needs an end-to-end test with the target mod.

[Back to the patch index](../README.md#feature-index)
