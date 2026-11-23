# Expose the network delay fix in Options

The Network page can enable or disable the patched multiplayer delay calculation.

## Reproduce the patch

Run the [patch builder](../README.md#build-a-patched-game-file) with `input`.

## Implementation

The UI key is `Options::ETDelayFix`. The executable uses `NetworkDelayFix` for the stored option name and `APT:ETDelayFix` for the localized label. The state byte at `0x00F352E8` starts at `1` in this build. The two network timing hooks at `0x00632535` and `0x00632A9B` switch calculation paths according to the option and session state.

The table identifies the corresponding changed byte ranges. The builder supplies any shared code and data sections.

| File offset | Preferred VA | Original bytes | Replacement bytes |
|---|---|---|---|
| `0x00232535` | `0x00632535` | `f7 3d 00 a4 ec 00` | `e9 fb 2a 90 00 90` |
| `0x00232A9B` | `0x00632A9B` | `b8 02 00 00 00 eb 19 c8` | `e9 b2 25 90 00 90 90 90` |

## Verify in ROTWK

Open Network settings, switch the option off and on and verify persistence after restarting. Test both positions in a match with the same peers and network conditions and compare order response. The effect depends on session timing and connectivity.

[Back to the patch index](../README.md#feature-index)
