# Fix the tooltip crash seen while training troops

The crash was reproduced in the early command-bar patch when building or training units exposed a tooltip with missing requirements. On that path the native tooltip code had already reused `ESI` for an inner string. The custom price hook treated it as the original descriptor and obtained an invalid command button. The recorded exception was a read access violation at address `0x19`.

1. At `0x0080814D`, save the real `CommandButton*` while the tooltip descriptor is still in `ESI`. The descriptor's button pointer is at `[ESI + 0x0C]`.
2. Use `[EBP - 0x50]` in this particular tooltip frame to carry the pointer to the hook at `0x00808390`. When porting, check that both hook sites share the frame and that no native instruction overwrites the chosen slot before the price hook.
3. Pass the saved button together with the upgrade, player, and unit arguments to the price helper. Keep `[EBP - 0x54]` for the maximum price. After the helper returns, the pointer is dead and `[EBP - 0x50]` can carry the minimum price for the suffix hook at `0x008083C7`.
4. Let the engine draw its usual cost prefix. Add the maximum only when it exceeds the minimum. For a non-upgrade, an ineligible group, or a missing selection, preserve the normal price path.

The complete hooks are `remember_tooltip_button`, `tooltip_price`, and `tooltip_suffix` in `src/display_and_commands/patches/commands/hooks.s`. The build includes this corrected version of the tooltip patch.

## Reproduce and verify

For a live check, hover a recruitment or upgrade button with an unmet requirement, then queue troops. Repeat with a valid single price and a mixed-selection range. In development, replaying the recorded x86 frame produced the invalid read on the early patch. With the saved pointer, the same path reached the stock price formatter with a 500-resource test price. Crash dumps are unnecessary for building the fix.
