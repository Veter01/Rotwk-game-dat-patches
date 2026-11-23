# Show recorded match chat in replays

Chat seen or sent by the recording client can be embedded in the replay and shown during playback.

## Reproduce the patch

Run the [patch builder](README.md#build-a-patched-game-file) with `replay-chat`.

## Implementation

The live chat path feeds `.rpchat`. The writer adds a custom replay record of type `0x07D4`. The playback hooks recognize the `RCT1` marker and rebuild the text using the stored frame and sender information. The capture code checks the recipient mask and has a bounded text buffer. The resulting replay carries the messages that the recording client was able to capture. Replays made before the patch have no added chat records.

The table identifies the corresponding changed byte ranges. The builder supplies any shared code and data sections.

| File offset | Preferred VA | Original bytes | Replacement bytes |
|---|---|---|---|
| `0x002D7AA5` | `0x006D7AA5` | `d3 a0 d6 ff` | `87 03 80 00` |
| `0x0037DCFC` | `0x0077DCFC` | `83 7d ec 1d 74 15` | `e9 af a0 75 00 90` |
| `0x0037DE0F` | `0x0077DE0F` | `83 7d ec 1d 74 09` | `e9 bc 9f 75 00 90` |
| `0x0037F7B7` | `0x0077F7B7` | `83 c4 40 8b ce` | `e9 44 86 75 00` |
| `0x0038419D` | `0x0078419D` | `b8 d2 38 b9` | `e9 ae 3a 75` |
| `0x004D55A1` | `0x008D55A1` | `85 ff 75 3a e8 a0 df ff ff` | `e9 9a 23 60 00 90 90 90 90` |
| `0x004D5662` | `0x008D5662` | `37 eb ea ff` | `1e 23 60 00` |
| `0x005177DD` | `0x009177DD` | `b8 ed 94 ba` | `e9 be 06 5c` |
| `0x005179DE` | `0x009179DE` | `39 3d 68 7d de 00 75 08` | `e9 5d 04 5c 00 90 90 90` |

The supplied binary implements automatic capture and playback hooks. The guide covers the automatic replay chat behavior in this build. For general replay format background, see [pySAGE's replay documentation](https://github.com/ClementJ18/pySAGE/blob/master/sage_replay/README.md).

## Verify in ROTWK

Record a new match with public and team messages and varied text. Copy just the replay to a second installation with the patch. Check who can see each message and at what replay time. Include a control replay made before the patch. Check the target viewer and build before sharing a replay containing chat.

[Back to the patch index](README.md#feature-index)
