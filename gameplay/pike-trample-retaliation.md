# ROTWK cavalry trample and pikeman retaliation fix

This patch restores the pikeman’s configured `CrushRevengeWeapon` when cavalry tramples a pikeman that the engine considers flanked. It applies to the exact 32-bit `game.dat` build identified below. The ROTWK 2.02 v9.6.3 patch notes describe a similar problem with rear charges. [ROTWK 2.02 patch notes](https://www.moddb.com/downloads/rotwk-patch-202-v964)

## Cause

The trample collision handler looks up the crushed unit’s revenge weapon at `0x8BFFD8`. When a weapon is present, it calls the flanking check at `0x68FB63`. If that check returns true, the original `jne` at `0x8BFFEC` jumps past the retaliation call to `0x8BFFFD`. By then the handler has already processed the crush, so the cavalry can trample the pikeman without taking its revenge damage. The result depends on the flanking check for that collision.

## Engine change

The patch redirects the decision at `0x8BFFEA` into the padding at the end of the existing `.combat` section. A non-flanked collision follows the original weapon call. For a flanked collision, the new code checks that the crusher or its horde has the `CAVALRY` flag. It then checks for the `PIKE` flag on the victim or its horde, or for a `DamageNugget` of type `SPECIALIST` in the configured revenge weapon. That last check covers pikemen whose templates omit the `PIKE` flag.

A matching collision resumes at `0x8BFFF3` with the original source, target, and weapon. The game calls its existing weapon dispatcher at `0x6CF328`, so the mod’s weapon and armor definitions still determine how much damage is dealt. Other flanked collisions branch to `0x8BFFFD` as before.

| Change | Virtual address | File offset | Bytes or size |
| --- | --- | --- | --- |
| Redirect the retaliation decision | `0x8BFFEA` | `0x4BFFEA` | `84 C0 75 0F 8B 43 74 6A 00` → `E9 89 C3 67 00 90 90 90 90` |
| Add the retaliation checks to `.combat` | `0xF3C378` | `0xB22378` | 130 bytes |
| Extend `.combat`’s `VirtualSize` | PE section header | `0x970` | `0x376` → `0x3FA` |

## Reproduce the patch

Save the script as `patch_pike_trample.py` and run it with Python 3 from the directory containing the original `game.dat`. The script checks the input and output SHA-256 hashes and writes a separate executable.

```bash
python3 patch_pike_trample.py game.dat patched/game.dat
```

```python
import hashlib
from pathlib import Path
import sys


ORIGINAL_SHA256 = "8853bde32ff0be8941b0d53fb6e4845df96df643142451abd3e995c218e0fbee"
PATCHED_SHA256 = "7c3ba893a414640dbe3b38115e8e508595fdc03589a5421a6596b0458e7df7b8"

HOOK_OFFSET = 0x4BFFEA
CODE_OFFSET = 0xB22378
VIRTUAL_SIZE_OFFSET = 0x970
ORIGINAL_HOOK = bytes.fromhex("84 C0 75 0F 8B 43 74 6A 00")
PATCHED_HOOK = bytes.fromhex("E9 89 C3 67 00 90 90 90 90")
REVENGE_CODE = bytes.fromhex("""
    84 c0 74 6f 8b 43 04 f6 80 09 01 00 00 02 75 16
    8b 83 7c 02 00 00 85 c0 74 63 8b 40 04 f6 80 09
    01 00 00 02 74 57 8b 46 04 f6 80 20 01 00 00 40
    75 41 8b 86 7c 02 00 00 85 c0 74 0c 8b 40 04 f6
    80 20 01 00 00 40 75 2b 8b 47 04 85 c0 74 2e 8b
    88 7c 01 00 00 8b 11 39 ca 74 22 8b 42 08 81 38
    78 ae c7 00 75 09 83 b8 78 01 00 00 12 74 04 8b
    12 eb e4 8b 43 74 6a 00 e9 fe 3b 98 ff e9 03 3c
    98 ff
""")


def main():
    if len(sys.argv) != 3:
        raise SystemExit("Usage: patch_pike_trample.py INPUT_GAME_DAT OUTPUT_GAME_DAT")

    source, output = map(Path, sys.argv[1:])
    data = bytearray(source.read_bytes())
    if hashlib.sha256(data).hexdigest() != ORIGINAL_SHA256:
        raise SystemExit("Unsupported game.dat build. Check the original SHA-256 above.")

    hook_end = HOOK_OFFSET + len(ORIGINAL_HOOK)
    code_end = CODE_OFFSET + len(REVENGE_CODE)
    if data[HOOK_OFFSET:hook_end] != ORIGINAL_HOOK or any(data[CODE_OFFSET:code_end]):
        raise SystemExit("The expected hook bytes or .combat padding did not match.")

    data[HOOK_OFFSET:hook_end] = PATCHED_HOOK
    data[CODE_OFFSET:code_end] = REVENGE_CODE
    data[VIRTUAL_SIZE_OFFSET:VIRTUAL_SIZE_OFFSET + 4] = (0x3FA).to_bytes(4, "little")

    if hashlib.sha256(data).hexdigest() != PATCHED_SHA256:
        raise SystemExit("The patched executable did not match the expected SHA-256.")

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as patched_file:
        patched_file.write(data)
    print(f"Created {output}\nSHA-256 {PATCHED_SHA256}")


if __name__ == "__main__":
    main()
```

## Verification

The original and patched collision paths were checked across 11 scenarios in a 32-bit x86 emulator. The checks covered the existing frontal retaliation path, the flanked pikeman bug, classification through horde flags or `SPECIALIST` damage, and cases involving ordinary infantry, a non-cavalry crusher, or a missing revenge weapon. The harness verified whether the engine would call the weapon dispatcher and which arguments it would pass. In-game verification is pending.

To verify in ROTWK, back up the installed `game.dat` and place the generated file in its place. In a skirmish, give cavalry a move order through an enemy pikeman formation from the front, side, and rear. Check rider health at the moment of impact in each pass. Repeat against ordinary infantry to compare the existing behavior.
