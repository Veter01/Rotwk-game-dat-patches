# Apply RATE_OF_FIRE to ranged and melee weapon timing

The existing RATE_OF_FIRE modifier affects more of the weapon timing used by ranged and melee attacks.

## Reproduce the patch

Run the [patch builder](../README.md#build-a-patched-game-file) with `rate-of-fire`.

## Implementation

The helper at `.combat+0x210` reads attribute `0x15` and uses `1.0` for invalid multipliers. The delay helper divides a positive delay by that multiplier, rounds up and clamps the result. The hooks cover weapon delay calculation, attack-cycle timing, reload and secondary timing paths. Apply the existing `RATE_OF_FIRE` attribute modifier to the attacking object using the mod's normal upgrade, aura or ability mechanism.

The table identifies the corresponding changed byte ranges. The builder supplies any shared code and data sections.

| File offset | Preferred VA | Original bytes | Replacement bytes |
|---|---|---|---|
| `0x002CA830` | `0x006CA830` | `e8 8b f8 ff ff` | `e9 2f 1b 87 00` |
| `0x002CAA78` | `0x006CAA78` | `8b 41 04 8b 80 44 01 00 00` | `e9 18 18 87 00 90 90 90 90` |
| `0x002CDD6E` | `0x006CDD6E` | `f3 0f 2c c0 03 46 58` | `e9 0f e5 86 00 90 90` |
| `0x002CE8F8` | `0x006CE8F8` | `e8 c3 b7 ff ff` | `e9 55 da 86 00` |
| `0x002CE962` | `0x006CE962` | `1c` | `20` |
| `0x002CE9C1` | `0x006CE9C1` | `8b 86 44 01 00 00` | `e9 e4 d8 86 00 90` |
| `0x002CE9F3` | `0x006CE9F3` | `8b 0d 2c 41 de 00 03 41 40 03 86 44 01 00 00` | `e9 c8 d8 86 00 90 90 90 90 90 90 90 90 90 90` |
| `0x002CEF72` | `0x006CEF72` | `24` | `28` |
| `0x002CEFD7` | `0x006CEFD7` | `8b 80 44 01 00 00` | `e9 fd d2 86 00 90` |
| `0x002CF030` | `0x006CF030` | `f3 0f 11 45 f8 74 10 6a 01 57 8d 45 f8 50 6a 15 8b ce e8 e6 d7 fb ff` | `e9 b6 d2 86 00 90 90 90 90 90 90 90 90 90 90 90 90 90 90 90 90 90 90` |
| `0x002CF05A` | `0x006CF05A` | `57 8b cb 89 45 fc` | `e9 a2 d2 86 00 90` |
| `0x002CF145` | `0x006CF145` | `8b 44 10 08 89 45 fc` | `e9 d7 d1 86 00 90 90` |
| `0x002CF300` | `0x006CF300` | `8b 43 04 89 73 28 8b 80 44 01 00 00` | `e9 32 d0 86 00 90 90 90 90 90 90 90` |

## Verify in ROTWK

Give both an infantry archer and a swordsman the same known positive RATE_OF_FIRE modifier. Measure intervals between arrows or hit events against an identical control, including several reload cycles. Check that 100% retains baseline timing and that the modifier expires cleanly. Compare simulation frames under both render FPS modes.

[Back to the patch index](../README.md#feature-index)
