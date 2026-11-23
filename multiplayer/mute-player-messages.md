# Mute a player's messages from the multiplayer player list

Toggle whether incoming chat from a specific player is displayed locally.

## Reproduce the patch

Run the [patch builder](../README.md#build-a-patched-game-file) with `chat-mute`.

## Implementation

The `.chatmut` section wires the player-list action through `%s.ChatMute` and updates the APT control with `SetMuteState`. Incoming chat checks the local mute state by player slot. The UI state names in this build include `_audible`, `_muted` and `_disabled`. Expose the matching target in the player-list APT for a port of this behavior.

The table identifies the corresponding changed byte ranges. The builder supplies any shared code and data sections.

| File offset | Preferred VA | Original bytes | Replacement bytes |
|---|---|---|---|
| `0x0022D232` | `0x0062D232` | `b8 3f 41 b8` | `e9 20 e0 8a` |
| `0x00426CC1` | `0x00826CC1` | `80 78 0a 00 75 42` | `e9 48 45 6b 00 90` |
| `0x004D5343` | `0x008D5343` | `56 8b c1 8b 4c 24 08` | `8b c1 8b 4c 24 04 56` |
| `0x004D55ED` | `0x008D55ED` | `80 78 0a 00 8b ce 0f 94 45 0b` | `e9 3a 5c 60 00 90 90 90 90 90` |
| `0x004D560B` | `0x008D560B` | `80 7d 0b 00 74 58` | `e9 a0 5c 60 00 90` |
| `0x00515E00` | `0x00915E00` | `b8 59 91 ba` | `e9 17 52 5c` |
| `0x005162F5` | `0x009162F5` | `b8 23 92 ba` | `e9 3d 4d 5c` |

## Verify in ROTWK

Join a match with two other players. Mute one player, send chat from both peers and check that only the other player's messages are displayed. Unmute and send new messages. On a second client verify that the first client's mute setting has no effect on its chat.

[Back to the patch index](../README.md#feature-index)
