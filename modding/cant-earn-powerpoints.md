# Block spellbook power-point earnings on selected units

The new KindOf flag `CANT_EARN_POWERPOINTS` suppresses spellbook power-point earnings attributed to the flagged unit.

## Reproduce the patch

Run the [patch builder](../README.md#build-a-patched-game-file) with `power-points`.

## Implementation

The KindOf lookup is relocated to `0x00F3A5C0`. The new flag occupies zero-based index `222` (bit `0x40` at template offset `+0x123`). Table users and loop bounds move with the new entry. Earnings hooks use the flag on the unit and related attacker objects in the inspected attribution paths.

The table identifies the corresponding changed byte ranges. The builder supplies any shared code and data sections.

| File offset | Preferred VA | Original bytes | Replacement bytes |
|---|---|---|---|
| `0x002AC639` | `0x006AC639` | `de` | `df` |
| `0x003079F6` | `0x007079F6` | `de` | `df` |
| `0x002AAFC3` | `0x006AAFC3` | `55 8b ec 51 53` | `e9 f1 f3 88 00` |
| `0x002AB0D0` | `0x006AB0D0` | `55 8b ec 83 7d 08 00` | `e9 02 f3 88 00 90 90` |
| `0x00453FA1` | `0x00853FA1` | `ff ea f2 ff` | `52 64 6e 00` |
| `0x004FE8C7` | `0x008FE8C7` | `d9 41 e8 ff` | `44 bb 63 00` |

Append `CANT_EARN_POWERPOINTS` to the object's existing `KindOf = …` list in its INI definition.

## Verify in ROTWK

Use the same target and repeat the encounter with an ordinary attacker and a flagged attacker. Compare spellbook progress and individual unit experience. Test both a standalone object and a horde member if the mod uses the flag in hordes.

[Back to the patch index](../README.md#feature-index)
