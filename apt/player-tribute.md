# Per-player chat mute button

Compared `playertribute.big` from the original and modified inputs. The modified movie adds a `ChatMute` sprite to two player-row templates. The name fields at character IDs 20 and 46 are narrowed by 15 stage units to make room. The patched archives change the movie and constant table and add seven button meshes. The original texture atlas and image map are reused.

## Button and game callbacks

Sprite 90 defines the control and sprite 89 holds its state frames. The `_pending`, `_audible`, `_muted`, and `_disabled` labels represent its display states. Buttons 87 and 88 run `ToggleChat`. That function sends the row identity to the engine through `GameCodeNoPrefix` using the `cmt=` argument. `RefreshChat` requests the row's current state with `cmq=`. The `ChatMuteRevision` value lets visible rows request a fresh state after a toggle. The [chat mute engine patch](../multiplayer/mute-player-messages.md) returns the state to `SetMuteState` and handles actual message filtering.

## Edit

Open [PlayerTribute.xml](source/playertribute/PlayerTribute.xml) and search for `poname name="ChatMute"` to find the two placements. To move the control, change their `tx` and `ty` values. The shapes in `PlayerTribute_geometry` define the pending and button graphics. Keep the control name and state labels in sync with the engine hooks.

## Verify

Join a multiplayer match, open the player list, and mute one player while leaving another audible. Verify the icon changes, only the selected player's messages are suppressed, and unmuting restores new messages. Reopen or scroll the player list and verify the state follows the correct player. The original archive used for comparison has SHA-256 `fb4792c9cdf5e25c7ae4d0b8eb4250463ee439547f802edec211d2a95d89214f`.

[Back to the APT index](README.md)
