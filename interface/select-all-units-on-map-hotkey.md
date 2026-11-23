# Add a Select All Units on Map hotkey

Expose the existing map-wide unit selection command in the hotkey settings.

## Reproduce the patch

Run the [patch builder](../README.md#build-a-patched-game-file) with `input`.

## Implementation

The settings record at `0x00F3B1D4` uses `Options::ETKeySelectAll` and meta command `0x64`. The remapping path in `.keycmd` resolves a configured binding to the same engine action. The original selection rules still determine which owned objects qualify, including the engine's `IGNORES_SELECT_ALL` exclusion.

On a port, bind the settings row to `ETKeySelectAll` and give it a localized label in the target Options UI.

## Verify in ROTWK

Bind an unused key, place owned units on and off screen, and press it. Check enemy units and groups flagged `IGNORES_SELECT_ALL` separately. Reopen Options and confirm that the saved binding is displayed.

[Back to the patch index](../README.md#feature-index)
