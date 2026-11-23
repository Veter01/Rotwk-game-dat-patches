# Add filtering to horde member respawn

The new FilteredHordeRespawnBehavior module lets a horde restrict which members it replaces.

## Reproduce the patch

Run the [patch builder](README.md#build-a-patched-game-file) with `unit-modules`.

## Implementation

The module registration at `0x0065A93F` leads to `.wmfeat+0x000`. The parser table at `0x00F3A454` exposes `Radius`, `RespawnDelay`, `ObjectFilter` and `RespawnFXList`. At `0x00888012` the runtime dispatches this module to the filtered path and checks the horde and member conditions before scheduling a replacement.

The table identifies the corresponding changed byte ranges. The builder supplies any shared code and data sections.

| File offset | Preferred VA | Original bytes | Replacement bytes |
|---|---|---|---|
| `0x0025A940` | `0x0065A940` | `ba c7 ff ff` | `bc f6 8d 00` |
| `0x00488012` | `0x00888012` | `8b 47 74 8b 3b 89 45 e8` | `e9 82 22 6b 00 90 90 90` |

Example inside the horde object. Replace `MyEligibleMember` with the unit template in your mod.

```ini
Behavior = FilteredHordeRespawnBehavior ModuleTag_FilteredRespawn
    Radius = 100
    RespawnDelay = 5000
    ObjectFilter = NONE +MyEligibleMember
End
```

Tune the delay in game and carry over any effects from the existing horde configuration.

## Verify in ROTWK

Create a mixed horde with one template in the filter and one outside it. Kill a member of each type in a controlled test. After the configured delay, check that only the eligible member is replaced. Repeat with the whole horde dead and with a normal respawn module as a control.

[Back to the patch index](README.md#feature-index)
