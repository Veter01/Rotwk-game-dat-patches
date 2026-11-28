# Match player-list and rule label sizes

This change updates `apt/playertribute.big` and `apt/mpgamesetup.big`. It keeps the language-pack lookup keys and edits the placement, bounds, and shared row text field in the APT movies.

## Player list headings and background

1. Decode `PlayerTribute.apt` with `PlayerTribute.const`. In the Data tab, use `$HeaderTeam` (EditText `56`) as the reference. It uses font ID `14`, centered alignment, and a height of `14`. Set `$ETBlock` (`96`) and `$ShareArmy` (`101`) to the same height and set their horizontal placement scale in sprite `61` to `1.0`.
2. Widen the Data table by `26` APT units and shift its placements left by `13` to keep it centered. Move the headers and row controls to their updated column centers. Update the APT shape bounds as well as the X coordinates in the geometry records.

| Shape and geometry ID | Piece that needs to follow the new width |
| --- | --- |
| 57 | Header and row background shape. |
| 59 | Grid and its interior column separators. |
| 62 | Table backing. |
| 65 | Status-tab frame. |

3. Stretch the header gradient placement in sprite `61`. Also stretch the separate imported gray gradient `MenuExport.CH_TabGradient` in sprite `69`, frame `0`, depth `4`, character `64`. The imported shape is `256` APT units wide, so add `26 / 256` to its X scale. Leaving this placement at its original scale leaves the right end of the Data tab black. The same imported symbol also appears in sprite `77` for the other tab. Change only the placement in sprite `69`.

See [the player-list geometry patch](../modding/src/display_and_commands/patches/labels/build.py) and [the later gradient correction](../modding/src/display_and_commands/patches/fullscreen/build.py).

## Allow Players To Transfer Their Armies To Allies

In `MpGameSetup.apt`, the repeated checkbox rows use sprite `9` and its named `RuleText` field, EditText `8`. It already has the reference text height of `14`. Increase the field's right bound to `480` APT units. The long label then fits in the same row text field as the other rules, with room for its normal font size. The fix is in `patch_rules` in [the label build script](../modding/src/display_and_commands/patches/labels/build.py).

When replacing a BIG member that changed length, write the new data at the end, update the member offset and length, and update the archive length. Validate the member table and compare unaffected member contents after the edit.

## Windows check

In Players → Data, compare Block and Shared Control with Player and Team. Check that the gray background reaches the right border and that the row controls still line up with their headers. Open the other tab to check its background. In the game setup Rules tab, compare the player-transfer label with Random Teams and Allow Ring Heroes. Repeat in each language you ship.
