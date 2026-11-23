# Allow War of the Ring multiplayer with more than two participants

The War of the Ring changes remove the old two-participant setup restriction on the patched path.

## Reproduce the patch

Run the [patch builder](README.md#build-a-patched-game-file) with `wotr`.

## Implementation

The setup edits around `0x0083C529`, `0x0083C547` and `0x00841787` bypass older slot and scenario gates. The `.wotrobs` helpers enumerate up to eight slots and handle tactical participants and observers. Use the multiplayer setup and matching scenario data described in [the eight-player guide](27-wotr-eight-player-support.md). The scenario and game session still define the number of usable seats.

The table identifies the corresponding changed byte ranges. The builder supplies any shared code and data sections.

| File offset | Preferred VA | Original bytes | Replacement bytes |
|---|---|---|---|
| `0x00227C41` | `0x00627C41` | `89 45 e0 89 5d e8` | `e8 75 15 90 00 90` |
| `0x00227C6E` | `0x00627C6E` | `39 5e 18 89 5d fc` | `e8 b5 15 90 00 90` |
| `0x00227CC1` | `0x00627CC1` | `8b 45 e8 83 c0 02` | `e8 df 15 90 00 90` |
| `0x00227CEB` | `0x00627CEB` | `8d 45 e4 8d 4e 34` | `e8 88 15 90 00 90` |
| `0x00227E20` | `0x00627E20` | `8b 46 18 85 c0` | `e8 2c 14 90 00` |
| `0x0043C529` | `0x0083C529` | `39 7d 84 7e 04` | `eb 07 90 90 90` |
| `0x0043C547` | `0x0083C547` | `c6 45 0b 00` | `90 90 90 90` |
| `0x00441787` | `0x00841787` | `74` | `eb` |

## Verify in ROTWK

Use three matched clients first. Confirm that they can enter one campaign, advance turns and join the same tactical battle. Add further clients or AI slots incrementally with an eight-slot scenario and verify observer and reconnect behavior.

[Back to the patch index](README.md#feature-index)
