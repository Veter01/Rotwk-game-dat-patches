# 06. Separate production modifiers

**Status:** Implemented. Machine-code tests covered four income paths and both queue types. In-game timing measurements are still pending.

## INI configuration

Define the modifier in `attributemodifier.ini` and apply it through an aura, power, or upgrade as usual.

```ini
ModifierList SplitProductionExample
    Category = SPELL
    Modifier = RESOURCE_PRODUCTION 200%
    Modifier = UNITS_PRODUCTION 50%
    Duration = 3500
End
```

| Field | Effect |
|---|---|
| `PRODUCTION` | The existing general multiplier. |
| `RESOURCE_PRODUCTION` | Resource income, including automatic deposits, income from resource buildings, and the value of delivered supplies. |
| `UNITS_PRODUCTION` | Normal unit recruitment and upgrade research in the production queue. |

The engine multiplies the general and specialized values together on the relevant path. For example, `PRODUCTION 125%` combined with `RESOURCE_PRODUCTION 200%` gives a resource income multiplier of 2.5, all else being equal. Hero recruitment and revival use a separate timer. Builder construction follows the original logic.

## Implementation

This change adapts officialNecro's `production-split` patch. It appends the two names from the specification and maps queue kinds 1 and 2 to the same `UNITS_PRODUCTION` index. Kind 3 keeps its original path. The adaptation omits the separate builder construction speed hook.

| Call site | Path |
|---|---|
| `0x0089DC44` | `AutoDepositUpdate` |
| `0x0088559E` | `TerrainResourceBehavior` |
| `0x00883C4D` | `SlaughterHordeContain` |
| `0x008A4622` | `SupplyCenterDockUpdate` |
| `0x008A1ED6` | `ProductionUpdate` queue progress |

Run the adaptation script from [10](negative-experience.md) against the pinned pySAGE commit documented there. The new tokens are appended after the original names. [production-split source](https://github.com/ClementJ18/pySAGE/blob/0a1f1b5d71b1b080008a7e9fff6f997601ec5a7f/sage_patch/patches/economy/production_split.py)

## In-game verification

1. Use a Mallorn Tree and a Lórien barracks. Measure income over several equal intervals and record the time to recruit one ordinary horde with no modifier.
2. Repeat with the modifier. The example should increase income and slow the queue. Measure the time to research one upgrade as well.
3. Repeat with one specialized modifier at a time while retaining `PRODUCTION`. For comparison, measure hero recruitment and builder construction speed.
