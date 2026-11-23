# Options pages and editable controls

Compared `options.big` from the original and modified inputs. Both movies have 35 root frames. The modified movie increases its character table from 294 to 363 slots, replaces `Options.apt` and `Options.const`, and adds eight text geometry files. The texture atlases and `Options.dat` match the original.

## Pages and callbacks

| Page | Visible content clip | Game callback |
|---|---|---|
| Graphics | `FrameLeft` | `ETPage0` |
| Screen | `ScreenPage` | `ETPage1` |
| Sound | `FrameMiddle` | `ETPage2` |
| Hotkeys | `HotkeysPage` | `ETPage3` |
| Network | `FrameRight` | `ETPage4` |
| Advanced | Advanced settings screen | `ETPage9` |

`ETSelectPage` switches which content clip is visible, updates the selected item in `Navigation`, and sends the matching page callback through `GameCode`. `ETSyncSoundTips` updates the sound-page help. The `NativeGadgets` sprite contains the controls that expose options to the engine.

New controls include `Options::ETFrameRate`, `Options::ETMouseSensitivity`, and `Options::ETDelayFix`. The 14 added `Options::ETKey...` controls are listed by action and default key in the [reference menu table](../interface/configurable-base-hotkeys.md#default-bindings-shown-in-the-reference-menu). `Options::ETKeyBuildPath` is the control shown as Select Matching Units and `Options::ETKeyTacticalMenu` is shown as Planning Mode in that menu. The root action code also sends `ETBegin`, `ETCancel`, and `ETReset` for settings state. The [matching engine patches](../interface/configurable-base-hotkeys.md) handle the values and actual game commands.

## Edit

Open [Options.xml](source/options/Options.xml) and search for a control name. Keep its `Options::` name intact if you are only moving it. The matching named label or border can have its own placement. Update the associated `$ET...` labels through the game's localization resources. The mesh files numbered 332–335 and 354–357 contain the new menu shapes. Follow the [build instructions](README.md#edit-and-rebuild) to compile the XML and constant table together.

## Verify

Open all five settings pages and Advanced Settings. Change a hotkey, resolution, frame-rate choice, and network delay setting in a matched game build. Verify Apply, Cancel, and Reset, and confirm a saved hotkey after restarting. The original archive used for comparison has SHA-256 `cebf8f5d5ba648dcc081b818bbdaac9465a4e8005803a2847b5eb75a4a953ea5`.

[Back to the APT index](README.md)
