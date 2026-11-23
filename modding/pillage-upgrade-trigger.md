# Add upgrade triggers to PillageModule

PillageModule can require upgrades before a unit receives resources for eligible hits. A zero base amount can be used with a later pillage amount modifier.

## Reproduce the patch

Run the [patch builder](../README.md#build-a-patched-game-file) with `pillage`.

## Implementation

The parser at `.combat+0x24` extends the original fields with `TriggeredBy` and `RequiresAllTriggers`. The runtime checks upgrade masks from the unit and relevant owners before counting a qualifying damage event. The amount helper can combine `PillageAmount` with the existing `DAMAGE_STRUCTURE_BOUNTY_ADD` modifier (attribute ID `0x16`) for eligible structure targets. The helper uses the enlarged mask routines, so the patch builder includes `upgrade-limit`.

The table identifies the corresponding changed byte ranges. The builder supplies any shared code and data sections.

| File offset | Preferred VA | Original bytes | Replacement bytes |
|---|---|---|---|
| `0x002535B9` | `0x006535B9` | `b2 0a 11` | `52 8a 8e` |
| `0x002535E3` | `0x006535E3` | `b8 68 c0` | `24 c0 f3` |
| `0x002535F9` | `0x006535F9` | `6a 14 e8 e0 c0 dd ff` | `e9 02 8a 8e 00 90 90` |
| `0x004882AE` | `0x008882AE` | `ff 47 08 8b 47 08` | `e9 d1 3d 6b 00 90` |
| `0x004882D4` | `0x008882D4` | `f0 8b 49 08` | `ec 90 90 90` |

Example using the existing PillageModule syntax. Define the named upgrade in your mod and grant it to the test unit. Use the mod's existing attribute-modifier syntax for a positive `DAMAGE_STRUCTURE_BOUNTY_ADD` bonus if the base amount is zero.

```ini
Behavior = PillageModule ModuleTag_UpgradePillage
    PillageAmount = 0
    NumDamageEventsPerPillage = 1
    PillageFilter = NONE +STRUCTURE
    TriggeredBy = Upgrade_MyPillage
    RequiresAllTriggers = Yes
End
```

## Verify in ROTWK

Use a swordsman and a target that matches `PillageFilter`. Check resource totals before the upgrade and after granting it. With base amount zero, verify that zero creates no floating reward and that an active positive DAMAGE_STRUCTURE_BOUNTY_ADD modifier pays on the configured hit count. Test an excluded target and a unit with a nonzero base amount.

[Back to the patch index](../README.md#feature-index)
