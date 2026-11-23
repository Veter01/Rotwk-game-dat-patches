# Support the common unload command for Battlewagons

The common unload action can process eligible units attached to transport or rider objects.

## Reproduce the patch

Run the [patch builder](../README.md#build-a-patched-game-file) with `unload`.

## Implementation

The two `.wmfeat` hooks at `0x008670D2` and `0x0087CF94` extend attachment bookkeeping and exit processing. The new path checks the transporter, the attached object's state and its parent link, then uses the existing removal path. Battlewagons and the Witch-king rely on their INI definitions for the matching attachment and unload setup.

The table identifies the corresponding changed byte ranges. The builder supplies any shared code and data sections.

| File offset | Preferred VA | Original bytes | Replacement bytes |
|---|---|---|---|
| `0x004670D2` | `0x008670D2` | `8b 46 04 83 a6 7c 02 00 00 00` | `e9 db 38 6d 00 90 90 90 90 90` |
| `0x0047CF94` | `0x0087CF94` | `8d 4e f8 8b 01 6a 02` | `e9 c6 d9 6b 00 90 90` |
| `0x00540415` | `0x00940415` | `75 13` | `90 90` |

## Verify in ROTWK

Equip a Battlewagon and the relevant Witch-king form with the intended riders or passengers. Invoke the common unload command and verify that the associated object is released exactly once. Repeat with a standard transport and with an empty transport.

[Back to the patch index](../README.md#feature-index)
