# Keep resource workers out of the builder hotkey

The common builder hotkey cycles through construction units. Workers assigned to resource buildings are filtered through the builder-specific eligibility checks.

## Reproduce the patch

Run the [patch builder](README.md#build-a-patched-game-file) with `input`.

## Implementation

The filter in `.keydef+0x2C3` checks the unit's owner, active drawable and object state. `.wmfeat+0xA56` also requires the candidate's command set to contain the build action with command ID `0x35`. The helper scans up to 64 command slots, which is why the input bundle includes the matching command-set layout.

The table identifies the corresponding changed byte ranges. The builder supplies any shared code and data sections.

| File offset | Preferred VA | Original bytes | Replacement bytes |
|---|---|---|---|
| `0x0041FAAB` | `0x0081FAAB` | `83 fe 5c 0f 85 b8 0c 00 00` | `e9 50 85 71 00 90 90 90 90` |

## Verify in ROTWK

Train builders, create workers at a lumber mill and a quarry, then repeatedly cycle builders. Check that the resource workers are skipped and the normal construction units still cycle. Also check a custom construction unit using its intended command set.

[Back to the patch index](README.md#feature-index)
