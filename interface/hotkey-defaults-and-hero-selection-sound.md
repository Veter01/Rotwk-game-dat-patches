# ROTWK hotkey defaults and Select All Heroes sound fix

This `game.dat` patch makes **Z** the default shortcut for **Planning Mode** and ties the **Select All Heroes** confirmation sound to the active shortcut. It was built on top of the version in `ROTWK_Allied_Minimap_Colors.zip` identified by the input hash below.

## Set Z as the Planning Mode default

The engine registers Planning Mode as `TOGGLE_PLANNING_MODE` (`0x99`). The hotkeys menu uses the row `Options::ETKeyTacticalMenu`, whose current choice is stored at `0xF3B230`. A value of `0` represents **Default**.

1. At `0xF31248`, redirect the branch reached after the configured shortcuts have been checked. If Planning Mode is set to **Default** and the normalized scan code is `0x2C` (`Z`) with no modifiers, pass action `0x99` to the existing temporary `MetaMap` record builder at `0xF310C1`. This gives explicitly configured shortcuts priority and uses the game's existing keyboard layout normalization.
2. At `0xF39030`, skip the original Planning Mode key record while the choice is **Default**. The temporary record still reaches the normal dispatcher, and explicitly configured Planning Mode shortcuts go through the existing remapping logic.
3. At `0xF39215`, use the Unicode `Z` string already in the key table and pass it to the existing label formatter at `0xF39258`. The menu displays **Z (Default)** using the localized `APT:ETKeyDefaultSuffix` string.

## Route the hero-selection sound through the command

The hero bar registered a second hotkey through `NonCommand_SelectAllHeroes`. Its callback at `0x92CDB1` returns success directly, so `HotKeyManager` could play its generic confirmation sound on the old key after a rebind. The remappable **Select All Heroes** action already uses its own dispatcher entry, `0xAB`.

Jump from `0x92C13C` to `0x92C1A6` to bypass the legacy registration and resume at the original cleanup. Both the default **O** shortcut and any explicitly assigned shortcut use action `0xAB`. The dispatcher at `0xF38510` runs the hero-selection routine, and the sound path at `0xF3ABD2` plays `Gui_PalantirCommandButtonClick` once when the routine selects an eligible hero. A keypress with no eligible heroes produces no selection sound.

## Binary changes

The virtual addresses below refer to the supported 32-bit build with image base `0x00400000`. The three Planning Mode handlers occupy 98 bytes in a new executable, read-only `.hkfix` section at `0xF3E000`. The section begins at file offset `0xB22A00` and is padded to `0x200` bytes on disk. The patch also updates the PE section count, code size and image size.

| Purpose | Virtual address | File offset | Original bytes | Patched bytes |
| --- | --- | --- | --- | --- |
| Resolve the default `Z` shortcut | `0xF31248` | `0xB1E448` | `0F 84 7D 73 00 00` | `0F 84 B2 CD 00 00` |
| Skip the original Planning Mode binding on **Default** | `0xF39030` | `0xB20830` | `E9 64 F0 FF FF` | `E9 F1 4F 00 00` |
| Display `Z` in the default label | `0xF39215` | `0xB20A15` | `E9 92 F3 FF FF` | `E9 30 4E 00 00` |
| Skip the legacy hero-bar hotkey registration | `0x92C13C` | `0x52C13C` | `6A 0C E8 9D 35 B0 FF` | `E9 65 00 00 00 90 90` |

## Reproduce the patch

Extract `game.dat` from the matching `ROTWK_Allied_Minimap_Colors.zip` build. Save the script below as `patch_hotkeys.py` and run it with Python 3. It checks both SHA-256 hashes and creates a separate output file. Place the resulting `game.dat` in the mod directory with the game closed.

```bash
python3 patch_hotkeys.py game.dat patched/game.dat
```

```python
from hashlib import sha256
from pathlib import Path
from struct import pack
import sys


INPUT_SHA256 = "85a3543fe20917f82845634f8c3f9f6963c02aa1f224ed075caac16725595535"
OUTPUT_SHA256 = "f8fd6f2f4d99bcf4b93eedf8328181f982602f21f0a09932fd442840d11ce0e6"

HOOKS = (
    (0xB1E448, "0F 84 7D 73 00 00", "0F 84 B2 CD 00 00"),
    (0xB20830, "E9 64 F0 FF FF", "E9 F1 4F 00 00"),
    (0xB20A15, "E9 92 F3 FF FF", "E9 30 4E 00 00"),
    (0x52C13C, "6A 0C E8 9D 35 B0 FF", "E9 65 00 00 00 90 90"),
)

CODE = bytes.fromhex("""
    83 3D 30 B2 F3 00 00 75 18 83 FA 2C 75 13 83 7C
    24 24 00 75 0C BE 99 00 00 00 31 FF E9 A0 30 FF
    FF E9 A5 A5 FF FF 81 FE B8 77 F2 00 74 12 81 7E
    04 99 00 00 00 75 09 83 3D 30 B2 F3 00 00 74 05
    E9 54 A0 FF FF E9 1A C9 69 FF 81 FF 1C B2 F3 00
    75 0B 8B 1D 80 47 F2 00 E9 FB B1 FF FF E9 4A A5
    FF FF
""")


def main():
    if len(sys.argv) != 3:
        raise SystemExit("Usage: patch_hotkeys.py INPUT_GAME_DAT OUTPUT_GAME_DAT")

    source, output = map(Path, sys.argv[1:])
    data = bytearray(source.read_bytes())
    if sha256(data).hexdigest() != INPUT_SHA256:
        raise SystemExit("Unsupported game.dat build. Check the input SHA-256.")

    for offset, original, patched in HOOKS:
        before, after = bytes.fromhex(original), bytes.fromhex(patched)
        end = offset + len(before)
        if data[offset:end] != before:
            raise SystemExit(f"Unexpected instruction bytes at {offset:#x}.")
        data[offset:end] = after

    section_header_offset = 0x9B8
    section_header = pack(
        "<8sIIIIIIHHI",
        b".hkfix", len(CODE), 0xB3E000, 0x200, 0xB22A00,
        0, 0, 0, 0, 0x60000020,
    )
    data[section_header_offset:section_header_offset + len(section_header)] = section_header
    data[0x11E:0x120] = pack("<H", 50)        # NumberOfSections
    data[0x134:0x138] = pack("<I", 0x7DE800)  # SizeOfCode
    data[0x168:0x16C] = pack("<I", 0xB3F000)  # SizeOfImage
    data.extend(CODE.ljust(0x200, b"\x00"))

    if sha256(data).hexdigest() != OUTPUT_SHA256:
        raise SystemExit("Patched game.dat did not match the expected SHA-256.")

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as patched_file:
        patched_file.write(data)
    print(f"Created {output}\nSHA-256 {OUTPUT_SHA256}")


if __name__ == "__main__":
    main()
```

## Verification

The game’s x86 routines were exercised in an emulator. The checks covered the default `Z` binding, custom bindings with modifiers, German keyboard layout normalization, restoring defaults, the default label, and one sound event when the hero-selection routine found an eligible hero. The audio test intercepted the engine’s sound call. The full game was not run.

To verify in ROTWK, set Planning Mode to **Z (Default)** and press `Z` in a skirmish. Then recruit a hero, assign **Select All Heroes** to `Ctrl+H`, and apply the settings. Clear the selection before each keypress. `Ctrl+H` should select the hero and play one confirmation sound. `O` should produce no **Select All Heroes** feedback. Restore the default hero shortcut and check that `O` selects the hero with the same confirmation sound again.
