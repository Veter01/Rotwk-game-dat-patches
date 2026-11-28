# Toggle autocast for matching selected units

Right-clicking a shared autocast button now applies the same target state to every eligible unit in the current selection. Select multiple units and use their shared command slot. A matching unit elsewhere on the map is outside the selection.

## Set up the command data

On an existing autocast-capable button, retain the ability's target flags and set `AutoAbility = Yes` inside its `CommandButton` block. The selected units need the corresponding ability or weapon and an autocast behavior. Arrange the shared command in the same displayed slot of each unit's `CommandSet`.

Separately named `SPECIAL_POWER` buttons can share a slot when they point to the same power template and both have autocast enabled. The click handler resolves each candidate through its unit's command set and checks the resolved template, availability, and autocast state. For `FIRE_WEAPON`, the shared weapon button and weapon slot must match. Manual activation still uses the engine's multi-selection rules.

## Implement the engine behavior

1. Apply the pySAGE command-slot compatibility patch (`src/display_and_commands/patches/commands/pysage-multiselect.patch`). It updates the merge routine to recognize autocast aliases and permits an eligible autocast button to seed a group slot.
2. At `0x009445DA`, allow a `SPECIAL_POWER` or `FIRE_WEAPON` with the autocast flag to appear in the multi-selection command bar. At `0x0094070F`, send right-clicks to the group handler. Preserve the manual click path and its `OK_FOR_MULTI_SELECT` check.
3. Walk the selected units controlled by the local player. Read the matching command and its state per unit, skipping unavailable commands. If at least one eligible unit is off, choose on for the group. If every eligible unit is already on, choose off.
4. Use the native message stream for each eligible unit whose state needs to change. A power toggle uses message `0x458` and a weapon toggle uses `0x459`. Pass the original power or weapon argument followed by the unit's object ID.

The algorithm is in `src/display_and_commands/patches/commands/commands.c`. The branch targets and register handling are in `src/display_and_commands/patches/commands/hooks.s` and `src/display_and_commands/patches/commands/build.py`.

## Windows check

Select several units with a mix of on and off autocast states. The first right-click should turn matching eligible units on. The next should turn them off. Include a unit with a different ability, a unit missing a prerequisite, and an unselected unit. Confirm their states stay as configured. Compare a single-unit right-click and normal left-click with their original behavior.
