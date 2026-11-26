# 04. AcceptanceFilter for PlayerHealSpecialPower

**Status:** Implemented. Emulation covered field parsing and filter selection. The named units and structures still need in-game verification.

## INI configuration

```ini
Behavior = PlayerHealSpecialPower ModuleTag_AragornAthelasHeal
    SpecialPowerTemplate = SpecialAbilityActivateeDummy
    HealAmount = 1500
    HealAsPercent = No
    HealAffects = HERO
    AcceptanceFilter = ANY +HERO -FornostHammer
    HealRadius = 100
    HealFX = FX_HealingHerbs
    TriggerFX = FX_HealingHerbs
End
```

When supplied, `AcceptanceFilter` determines which target types can receive healing. The module still applies its existing checks for the caster's side and allies. Existing modules that omit `AcceptanceFilter` continue to use `HealAffects`.

To exclude Azog's high ground, add the actual object template name from your mod with a `-` prefix. The exclusion list comes from the INI for that module.

## Implementation

- The ModuleData allocation at `0x00652371` grows from `0xAC` to `0xB4`. The filter handle is at `+0xAC` and the field presence flag is at `+0xB0`.
- Parsing uses the native filter parser at `0x0076392F`. Initialization sets an empty handle and the destructor releases the filter through `0x007629B0`.
- The hook at `0x008CC399` selects the `HealAffects` check at `0x0070C548` or the `AcceptanceFilter` check at `0x007640C1`. Both checks return to the shared healing path.

The `engine_patch.s` source and build instructions are in [01](filtered-horde-respawn-behavior.md). See `heal_init`, `heal_parse_filter`, `heal_filter_target`, and the `heal_fields` table.

## In-game verification

1. Set `HealAffects = STRUCTURE` and `AcceptanceFilter = ANY +HERO -FornostHammer` to make the two cases easy to distinguish.
2. Damage an ordinary hero and an allied structure. Cast so that both are within the healing radius. The hero should recover health.
3. Remove `AcceptanceFilter` and repeat with `HealAffects = STRUCTURE`. The structure should heal through the original path. Check excluded targets and an enemy hero separately.
