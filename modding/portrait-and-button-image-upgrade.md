# Change a portrait and button image without transforming the unit

The PortraitUpgrade module can substitute the UI art on an existing unit when its upgrade is active.

## Reproduce the patch

Run the [patch builder](../README.md#build-a-patched-game-file) with `unit-modules`.

## Implementation

The module registers through `0x0065A93F`. `Portrait` and `ButtonImage` are the added fields in its parser table at `0x00F3A424`. The portrait and button-image readers consult the active override at `.wmfeat+0x111` and `.wmfeat+0x12F`. The selection panel hooks at `0x0092D052` and `0x0092D144` support refreshing the displayed art. Use mapped image names already defined in the mod.

The table identifies the corresponding changed byte ranges. The builder supplies any shared code and data sections.

| File offset | Preferred VA | Original bytes | Replacement bytes |
|---|---|---|---|
| `0x0025A940` | `0x0065A940` | `ba c7 ff ff` | `bc f6 8d 00` |
| `0x00294F06` | `0x00694F06` | `56 8b f1 e8 ea fc ff ff` | `e9 06 52 8a 00 90 90 90` |
| `0x0033D0BA` | `0x0073D0BA` | `83 7c 24 04` | `e9 70 d0 7f` |
| `0x0052D052` | `0x0092D052` | `80 7e 5e 01 0f 84 71 01 00 00` | `e9 4c d1 60 00 90 90 90 90 90` |
| `0x0052D144` | `0x0092D144` | `89 46 4c 8b 46 0c` | `e9 a2 d0 60 00 90` |

Add the module to the unit object and grant the named upgrade through the normal upgrade path.

```ini
Behavior = PortraitUpgrade ModuleTag_AlternateArt
    TriggeredBy = Upgrade_MyAlternateArt
    Portrait = MyAlternatePortrait
    ButtonImage = MyAlternateButton
End
```

## Verify in ROTWK

Select a hero before and after granting the test upgrade. Check the portrait, button icon, unit model, form, stats and abilities. Reselect the hero and check both images again.

[Back to the patch index](../README.md#feature-index)
