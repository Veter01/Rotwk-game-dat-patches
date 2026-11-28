# Apply discounts and display mixed upgrade prices

The command bar must resolve the upgrade separately for each selected unit. A button name or price cached from one representative can be wrong for another unit, especially when command sets change between upgrade stages.

## Use the upgrade fields

`DiscountGroup` is an optional string on a `CostModifierUpgrade` behavior with `UpgradeDiscount = Yes`. Differently named carriers can use the same ladder when the group name, the full `Percentage` vector, and the full `ApplyToTheseUpgrades` list match. Distinct groups contribute separately to the applicable total.

```ini
Behavior = CostModifierUpgrade ModuleTag_ForgeDiscount
    TriggeredBy = Upgrade_ForgeEnabled
    UpgradeDiscount = Yes
    DiscountGroup = ForgeDiscount
    Percentage = 0% -10% -20%
    ApplyToTheseUpgrades = Upgrade_ExampleBlades
End
```

The example uses placeholder upgrade names. Use your mod's existing definitions. For a branch with two distinct upgrade templates, set `MultiSelectGroup = 2` on both relevant `OBJECT_UPGRADE` command buttons and use the same command slot. Alternatively, if separate buttons refer to the very same upgrade template, the patched merge recognizes the shared template directly. Prices come from the upgrade definitions and discount rules. The game patch registers the new fields. An editor with its own parser needs the corresponding editor support before it can read INI data that uses them.

## Implement the pricing and purchase paths

1. Apply pySAGE's `PlayerUpgradeDiscountPatch`, `CostModifierUpgradeGroupsPatch`, and `MultiSelectGroupPatch` in that order. The bundled builder fingerprints the existing wrapper at `0x00942733` and its native fallback before adapting the pySAGE anchor.
2. For `Type = PLAYER`, a module must explicitly list the upgrade in `ApplyToTheseUpgrades`. `NoUpgradeDiscount = Yes` still opts out of the upgrade discount. At `0x0066F2FF`, combine the existing object-template-derived price with the applicable upgrade discount. The multiplier is `1 + sum_of_applicable_upgrade_discount_fractions`. Truncate to an integer, with a lower bound of zero.
3. Scan the unit's own command set for the clicked button or a button with the same upgrade template. Keep the first matching nonzero `MultiSelectGroup` as a fallback. Preserve the eligibility checks for each unit, including existing ownership of the upgrade and its prerequisites. For a mixed selection the shared action can be offered if at least one eligible unit can afford its upgrade.
4. Use the engine's `UpgradeTemplate::calcCostToBuild` at `0x0066F2C8` with that unit and its owner to compute each eligible price. Display the lowest and highest prices as a range if they differ. Display one price when all match. Keep the original building-upgrade path and its separate availability wrapper. The command stream and native purchase path handle the actual transaction.

The command source (`src/display_and_commands/patches/commands/commands.c`) includes the per-unit eligibility, range, and affordability checks. Read the [tooltip fix](training-crash-tooltip-pointer.md) before porting the price hook. [Upstream discount groups](https://github.com/ClementJ18/pySAGE/blob/10e069500929452ad96c3896bc04eb71e025dfb8/sage_patch/docs/cost-modifier-upgrade-groups.md) · [Upstream player upgrade discounts](https://github.com/ClementJ18/pySAGE/blob/10e069500929452ad96c3896bc04eb71e025dfb8/sage_patch/docs/player-upgrade-discount.md)

## Windows check

Prepare an upgrade with two effective prices, for example 180 and 320 resources. Select both eligible unit types and check that the shared label shows the range. With enough resources for only the cheaper upgrade, check that the affordable unit starts its own upgrade and the charge matches its calculated price. Also test a single unit, equal prices, a locked upgrade, a building upgrade, a named PLAYER discount, and the no-discount flag.
