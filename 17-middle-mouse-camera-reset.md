# Restore camera reset on a middle mouse click

A short middle mouse click reaches camera reset while a drag can still control the camera.

## Reproduce the patch

Run the [patch builder](README.md#build-a-patched-game-file) with `input`.

## Implementation

The `.camfix` pointer handlers record initial coordinates and a timestamp. The reset path tests a 350 ms window and drag movement against a five-pixel threshold in each axis. It uses the host timer via the existing import slot at `0x00BD0920`. The input settings code also supplies the `APT:ETKeyMiddleButton` display label.

The table identifies the corresponding changed byte ranges. The builder supplies any shared code and data sections.

| File offset | Preferred VA | Original bytes | Replacement bytes |
|---|---|---|---|
| `0x0043AD3D` | `0x0083AD3D` | `8b 46 30 2b 46 28 88 5e 39 79 02 f7 …` (60 bytes) | `e9 be c2 6f 00 90 90 90 90 90 90 90 …` (60 bytes) |
| `0x0043ADE6` | `0x0083ADE6` | `8b 0d 88 43 de 00 8b 01 ff 50 7c` | `ff 15 20 09 bd 00 90 90 90 90 90` |
| `0x0043AEA3` | `0x0083AEA3` | `8b 08 89 4e 30 8b 40 04 89 46 34 eb 59` | `e9 81 c1 6f 00 90 90 90 90 90 90 90 90` |

## Verify in ROTWK

Change the camera angle or zoom, then click and release the middle mouse button promptly with little movement. Check camera reset. Drag with the button held and repeat with a longer press to check that those gestures use the intended paths.

[Back to the patch index](README.md#feature-index)
