# Select and group buildings

The selection path accepts eligible structures for group operations, including matching building selection.

## Reproduce the patch

Run the [patch builder](README.md#build-a-patched-game-file) with `structure-selection`.

## Implementation

The hooks at `0x00625696`, `0x006A286A` and `0x006A2955` route structure eligibility through `.bldgrp` and `.padsel`. The grouping helper tests ownership, building status and the selected template or build-plot context where the command calls for matching. `.bldext`, `.bldcan` and `.bldlvl` keep the command-panel state consistent during grouped operations. The verified scope is matching-building selection and control groups. Global selection across mixed building types remains unverified.

The table identifies the corresponding changed byte ranges. The builder supplies any shared code and data sections.

| File offset | Preferred VA | Original bytes | Replacement bytes |
|---|---|---|---|
| `0x00225697` | `0x00625697` | `25 e1 06` | `85 49 8b` |
| `0x002A286B` | `0x006A286B` | `53 ad 09` | `a9 b7 83` |
| `0x002A2956` | `0x006A2956` | `66 0e ff ff` | `e6 b6 83 00` |
| `0x0031ED96` | `0x0071ED96` | `84 db 89 45 ec 74 08` | `e9 d7 b3 7b 00 90 90` |
| `0x00530E22` | `0x00930E22` | `0f f6 00` | `f5 c1 5a` |
| `0x00540975` | `0x00940975` | `8b 0d 98 63 de 00` | `e9 a0 c7 59 00 90` |
| `0x00541BFD` | `0x00941BFD` | `34 e8 ff ff` | `13 b4 59 00` |

## Verify in ROTWK

Select a production building and use the game's select-matching action. Confirm multiple eligible buildings can be selected and registered to a control group. Try a second building type, constructions in progress and enemy structures to check the intended eligibility boundaries.

[Back to the patch index](README.md#feature-index)
