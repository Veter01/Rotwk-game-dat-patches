# Fit the window and keep display controls valid

In windowed mode the selected resolution describes the client area. The title bar, borders, DPI, and taskbar consume additional space. Fitting the complete window inside the monitor's work area keeps the bottom options actions reachable.

## Fit the window around the client

1. Read the active monitor's work area. Calculate the frame overhead for the selected window style. Use `GetDpiForWindow` and `AdjustWindowRectExForDpi` when available, with `AdjustWindowRect` as the fallback.
2. Subtract the frame dimensions from the work area. If the requested client is larger than either limit, fit it proportionally. Center the outer window and measure the resulting client rectangle after placement.
3. Use the measured size for the renderer. Keep the user's preferred resolution separately so the fitted window does not become the requested exclusive fullscreen resolution when switching modes.
4. For a windowed resolution change sent through the game's queued settings path, capture the old style and bounds before moving the window. Restore them if the renderer rejects the requested change. Refresh cursor clipping after either outcome.

| Reference address | Hook |
| --- | --- |
| `0x00F4C35C` | Fit windowed geometry inside the monitor work area. |
| `0x00F4C47A` | Store the measured client dimensions. |
| `0x00F4CA0C` | Preserve the preferred resolution across windowed and borderless modes. |
| `0x00645E8B` | Apply a queued windowed resolution change with rollback. |

See [window_fit.c](../modding/src/display_and_commands/patches/window_fit/window_fit.c) and [the window-fit build script](../modding/src/display_and_commands/patches/window_fit/build.py).

## Fix callbacks after a layout rebuild

A display change can rebuild the options layout and invalidate the cached mode combo. The captured crash reached the stale gadget's virtual dispatch at `0x00715E12`. The patch clears references to the mode, clipping, and resolution controls when the engine destroys them at `0x006C1D23). It also checks that cached controls are still in the live window-manager tree before updating them at `0x00F4CB61`. Live controls still receive the normal state update. See [resize.c](../modding/src/display_and_commands/patches/window_lifetime/resize.c) and [hooks.s](../modding/src/display_and_commands/patches/window_lifetime/hooks.s).

## Restore the fixed frame

An intermediate test added `WS_THICKFRAME` and processed window sizing messages. The final build restores the fixed-size style `0x10CA0000` at the three window-style sites `0x00F5806D`, `0x00F580BC`, and `0x00F58391`. The frame update calls the match-aware mode handler directly, and the window procedure resumes its regular cursor event handler. This removes resize-triggered renderer resets. The fixed window still moves by its title bar, and its dimensions can be set through the resolution option where the game allows it. The control lifetime hooks stay active. See [fixed_window](../modding/src/display_and_commands/patches/fixed_window/build.py).

## Windows check

Use a resolution near the desktop size in windowed mode. Verify that Apply, Cancel, and Defaults are reachable at the bottom of Options. Repeat with display scaling and a visible taskbar. Check that moving the window updates clipping, the frame cannot be stretched, and switching modes outside a match still refreshes the options controls.
