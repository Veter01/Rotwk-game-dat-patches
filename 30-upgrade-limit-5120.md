# Raise the upgrade ID limit from 1,152 to 5,120

The patch expands the upgrade bitset capacity from `0x480` to `0x1400` entries.

## Reproduce the patch

Run the [patch builder](README.md#build-a-patched-game-file) with `upgrade-limit`.

## Implementation

The `.upg5k` section implements expanded mask storage and access. The patch changes bounds, set/clear/test operations, copies and several consumers of the original 36-dword mask. The reference keeps the original inline object layout and uses out-of-line storage for extended masks. Changing the bound alone leaves existing mask users writing to the old representation.

The table identifies the corresponding changed byte ranges. The builder supplies any shared code and data sections.

| File offset | Preferred VA | Original bytes | Replacement bytes |
|---|---|---|---|
| `0x00046113` | `0x00446113` | `53 56 57 33 c0` | `e9 70 92 a9 00` |
| `0x00048A91` | `0x00448A91` | `8d 84 85 ec fe ff ff f7 d2 21 10` | `e9 03 6e a9 00 90 90 90 90 90 90` |
| `0x001EBD52` | `0x005EBD52` | `80 04` | `00 14` |
| `0x001EBE86` | `0x005EBE86` | `80 04` | `00 14` |
| `0x004097D6` | `0x008097D6` | `8b 44 24 04 33 d2` | `e9 0e 5c 6d 00 90` |
| `0x0040F27E` | `0x0080F27E` | `33 c0 f7 54 85 dc 40 83 f8 24 72 f6` | `e9 8d 18 6d 00 90 90 90 90 90 90 90` |
| `0x004D2837` | `0x008D2837` | `80 04` | `00 14` |
| `0x005A3E32` | `0x009A3E32` | `80 04` | `00 14` |
| `0x006081B9` | `0x00A081B9` | `80 04` | `00 14` |
| `0x00608540` | `0x00A08540` | `80 04` | `00 14` |

## Verify in ROTWK

In a disposable mod setup, put an upgrade beyond the 1,152-entry boundary and apply it to a unit. Verify that a second high-ID upgrade remains independent, then check player-level effects, save/load and multiplayer with matching clients. Exercise IDs just below and above the original boundary.

[Back to the patch index](README.md#feature-index)
