# ROTWK WorldBuilder patches

These guides cover the 32-bit WorldBuilder executable for *The Rise of the Witch-king*. Use your own copy of `worldbuilder.exe`. The patcher verifies the original file before writing a new executable.

| Guide | What it covers |
|---|---|
| [Startup license dialog](startup-license-dialog.md) | Use WorldBuilder's built-in marker file after accepting the license terms. |
| [Large address space](large-address-space.md) | Enable up to 4 GiB of user-mode virtual address space on 64-bit Windows. |
| [Large maps](large-maps.md) | Create, resize, and import maps up to 2000 × 2000. |
| [AI factions in Player List](ai-factions-in-player-list.md) | Expand the editor's record storage for up to 100 AI faction entries within the full roster. |

## Build the patched editor

Save [patch_worldbuilder.py](patch_worldbuilder.py) and [patch-data.json](patch-data.json) in the same directory. Run the command from that directory with your original executable. Python 3.8 or later is sufficient. On macOS or Linux, use `python3` in place of `py -3`.

```powershell
py -3 .\patch_worldbuilder.py .\worldbuilder.exe .\worldbuilder-patched.exe
```

Use `--patch memory` for the address-space flag alone or `--patch map` for the map changes and the address-space flag. The default `full` mode also expands Player List. Each mode starts from the same original build.

| File | SHA-256 |
|---|---|
| Original input | `3fdae1d2dd3fc2c44cd53e4617acc3b8992b4eec0938b9abb213714c197280d7` |
| Full patched output | `ca1344a41302b3bc98facb5a97bb9358943a3f79bbbc530a3952e5e185522dd6` |

Close WorldBuilder and keep a backup of the installed executable. Copy the patched file into the editor's directory and name it `worldbuilder.exe`. For the startup dialog setting, follow its separate guide. The full patch reproduces the reference executable byte for byte. The feature guides include Windows smoke tests for the editor and any relevant game data.

[Back to the game.dat patch index](../README.md#feature-index)
