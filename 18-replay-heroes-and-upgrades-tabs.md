# Open Heroes and Upgrades tabs in replays

Observers can open supported command-panel submenus during replay playback.

## Reproduce the patch

Run the [patch builder](README.md#build-a-patched-game-file) with `replay-tabs`.

## Implementation

At `0x00941BD2`, the command filter calls `.obscmd`. Menu-switch actions `0x37` and `0x38` take the observer-compatible path. Other commands continue through the original validation function at `0x006A87F5`. The tabs displayed depend on the command set and observer UI for the selected player's faction.

The table identifies the corresponding changed byte ranges. The builder supplies any shared code and data sections.

| File offset | Preferred VA | Original bytes | Replacement bytes |
|---|---|---|---|
| `0x00541BD3` | `0x00941BD3` | `1e 6c d6 ff` | `29 64 59 00` |

## Verify in ROTWK

Open a replay and select a faction structure with Heroes and Upgrades tabs. Open each submenu and return to the main panel. Check that no purchase or research action fires in playback.

[Back to the patch index](README.md#feature-index)
