# Pause and resume replays with Ctrl + ]

Ctrl + ] toggles replay playback between paused and running.

## Reproduce the patch

Run the [patch builder](../README.md#build-a-patched-game-file) with `replay-pause`.

## Implementation

The input hook at `0x0063F1B9` tests scan code `0x1B` with Ctrl. It changes `.rppvar` only on the initial key event in replay mode. The game-loop hook at `0x006325D5` uses the pause state, and the replay setup hook clears it. On a non-US keyboard, use the physical key associated with that scan code.

The table identifies the corresponding changed byte ranges. The builder supplies any shared code and data sections.

| File offset | Preferred VA | Original bytes | Replacement bytes |
|---|---|---|---|
| `0x002325D5` | `0x006325D5` | `84 db a1 88 43 de 00 74 1a` | `e9 7d ba 8f 00 90 90 90 90` |
| `0x0023F1B9` | `0x0063F1B9` | `66 8b 46 02 a8 02` | `e9 42 ee 8e 00 90` |
| `0x0037F66B` | `0x0077F66B` | `b8 63 34 b9` | `e9 6e ea 7a` |

## Verify in ROTWK

Play a replay, press Ctrl + ], confirm that simulation time stops, then press it again and check that playback resumes from the same position. Hold the hotkey, try it in a live match, and open another replay to check reset behavior.

[Back to the patch index](../README.md#feature-index)
