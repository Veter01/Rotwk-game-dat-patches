# Restore mouse-edge scrolling in windowed mode

Window borders, the title bar, display scaling, and the taskbar make desktop coordinates different from viewport coordinates. Use the client rectangle for both edge detection and cursor clipping. The final fixed-frame build uses the same edge calculation at scroll start and while the camera is moving.

1. Read the current cursor position and the game window's client rectangle. Convert both corners of the rectangle to screen coordinates with `ClientToScreen`. Check that the game is the foreground window and that the cursor is inside the client.
2. Treat the first and last three client pixels on each axis as edge zones. When the client extends past a monitor's usable area, also consider the visible work-area boundary. Skip a monitor seam where an adjacent work area continues inside the same client rectangle.
3. Start the engine's normal type-`3` edge-scroll state. The frame code applies the original scroll speed factors and passes the resulting horizontal and vertical delta to the game's existing camera path. Drag scrolling and keyboard scrolling retain their original commands.
4. When cursor clipping is enabled, pass the client rectangle to the clipping helper. On a single display the helper intersects it with the usable work area when needed. Reapply clipping after the window moves.
5. Use the camera frame callback to start an edge scroll when the pointer is already at the edge and Windows sends no new mouse movement. Keep the native HUD, tactical view, and mouse-state checks. In the fixed-frame build, the edge helper defers while a display switch is in progress. A cached options-owner pointer can outlive the screen and is therefore unsuitable as an input gate.

| Reference address | Role |
| --- | --- |
| `0x0083AF66` | Mouse event hook for starting and stopping edge scrolling. |
| `0x0083B47E` | Camera frame hook for checking the pointer when it is stationary. |
| `0x0083B53E` | Edge-scroll tick and movement delta. |
| `0x00F5130C` | Legacy viewport guard. Windowed mode delegates to the client-edge helper. |
| `0x00F4C665` | Cursor clipping call site. |

The first patch is in [navigation_camera](../modding/src/display_and_commands/patches/navigation_camera/build.py). The follow-up hooks are in [match_display](../modding/src/display_and_commands/patches/match_display/build.py), and [fixed_window](../modding/src/display_and_commands/patches/fixed_window/build.py) connects the final fixed-size window to client clipping and client-edge detection.

## Windows check

Start a match in windowed mode. Move the pointer to the inner left, right, top, and bottom edges in turn. Test a corner and hold the pointer still at an edge. The view should stop moving when the pointer returns to the middle or the game loses focus. Repeat with clipping enabled and disabled, after moving the window, and after opening and closing Options. Test arrows and mouse drag scrolling separately. The emulation checks exercised the camera update and edge deltas. Windows input and monitor behavior require a live check.
