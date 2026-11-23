# Offer 30 FPS and 60 FPS in Options

The frame-rate setting exposes 30 FPS and 60 FPS.

## Reproduce the patch

Run the [patch builder](../README.md#build-a-patched-game-file) with `input`.

## Implementation

The settings record `Options::ETFrameRate` starts at 60 in `.wmkeys`. The localized labels are `APT:ETFPS30` and `APT:ETFPS60`. Two drawing sites call `.fpsdraw`, which throttles drawing for the 30 FPS setting and delegates directly for 60 FPS. This patch concerns rendering. The observed game logic, networking and replay behavior should be checked separately when porting.

The table identifies the corresponding changed byte ranges. The builder supplies any shared code and data sections.

| File offset | Preferred VA | Original bytes | Replacement bytes |
|---|---|---|---|
| `0x00248861` | `0x00648861` | `8b 0d 18 44 de 00 8b 01 ff 50 30` | `e8 9a 37 8e 00 90 90 90 90 90 90` |
| `0x002488BD` | `0x006488BD` | `8b 0d 18 44 de 00 8b 01 ff 50 30` | `e8 3e 37 8e 00 90 90 90 90 90 90` |

## Verify in ROTWK

Measure rendered FPS with both choices under a light workload, then restart and confirm that the last setting persists. Check that match timers move at the same rate at both settings and that replay playback remains stable.

[Back to the patch index](../README.md#feature-index)
