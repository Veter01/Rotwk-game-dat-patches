# Allow mounted special abilities at zero locomotor speed

ToggleMountedSpecialAbilityUpdate can run when the selected locomotor set has zero speed.

## Reproduce the patch

Run the [patch builder](../README.md#build-a-patched-game-file) with `mount-at-zero-speed`.

## Implementation

The branch at `0x008B1FFE` enters `.wmfeat+0x940`. The original floating-point status check is retained. The new path also reads the locomotor state and permits its zero-speed case through the existing continuation at `0x008B2003`. Range, cooldown and the underlying command setup still come from the hero definition.

The table identifies the corresponding changed byte ranges. The builder supplies any shared code and data sections.

| File offset | Preferred VA | Original bytes | Replacement bytes |
|---|---|---|---|
| `0x004B1FFE` | `0x008B1FFE` | `f6 c4 44 7b 21` | `e9 3d 89 68 00` |

## Verify in ROTWK

Use an existing `ToggleMountedSpecialAbilityUpdate` ability with a stationary LocomotorSet. Trigger it while stationary. Repeat while mobile and confirm that cooldown and the command's other prerequisites still apply.

[Back to the patch index](../README.md#feature-index)
