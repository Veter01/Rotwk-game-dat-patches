# Restore exclusive fullscreen and lock display mode during a match

A windowed client can end up at a size that the display adapter does not expose as an exclusive fullscreen mode. The mode combo needs both a compatible resolution and a match-state check.

## Choose an exclusive fullscreen resolution

1. Wrap the two calls to the existing window configurator at `0x00F4C7F3` during startup and `0x00F4CA56` during live changes. Its register arguments are mode in EAX, width pointer in EDX, and height pointer in ECX. Forward the original stack argument. Run the mode chooser for fullscreen mode `0`; modes `1` and `2` retain their existing borderless and windowed paths.
2. When Direct3D is active, enumerate the active adapter's modes for the applicable color depth. Keep an exact supported request. Otherwise prefer the desktop dimensions when that pair is listed, or choose the supported dimensions nearest to the desktop by total width and height difference. If Direct3D returns an empty mode list for that depth, keep the original dimensions and let the engine handle the result.
3. Before Direct3D is initialized, query the primary display with `EnumDisplaySettingsA`. Keep the supported request or use the desktop-based fallback. Pass the selected dimensions to the original window and renderer flow, keeping its existing rollback if the renderer fails.
4. At `0x005213D9`, pass `FALSE` as the windowed argument for the back-buffer format compatibility check on the exclusive path.

See `src/display_and_commands/patches/fullscreen/fullscreen.c` and the wrapper (`src/display_and_commands/patches/fullscreen/hooks.s`).

## Lock the mode combo during matches

Use the engine's existing `GameLogic` predicate at `0x00441B60`, which the native resolution save flow already uses to recognize active gameplay. Feed it the game logic singleton at `0x00DE412C`.

When the Screen page is available, enable or disable the mode combo using the native widget function at `0x007154B3`. Guard the picker change event at `0x00F4C893`, the Defaults path at `0x00F4CC95`, the saved-mode read at `0x00F4CE5A`, and the Cancel path at `0x00F4C8B0`. In the frame callback, drop any pending mode change if a match became active after the request was queued. Keep the independent cursor-clipping checkbox in the normal options flow.

See `src/display_and_commands/patches/match_display/window.c`, its hooks (`src/display_and_commands/patches/match_display/hooks.s`), and the final frame callback in the fixed-window patch (`src/display_and_commands/patches/fixed_window/build.py`).

## Windows check

In the main menu, switch among windowed, borderless, and fullscreen modes. Try fullscreen from a window whose fitted size differs from a listed display mode. Save and relaunch, then check the persisted mode. In both a skirmish and a multiplayer match, open Options → Screen. Confirm that the mode selector is disabled, Defaults and Apply leave the current mode active, and cursor clipping still responds. After leaving the match, verify that the mode combo is usable again.
