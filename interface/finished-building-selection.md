# 11. Exclude unfinished buildings from matching selection

Double-clicking a finished building or pressing `E` with one selected adds finished buildings of the same type. Confirmed construction sites and buildings still under construction are skipped. A site selected with a single click stays selected so the player can cancel construction. While that site is the only selection, it cannot start a search for matching buildings.

## INI configuration

The fix lives in `game.dat`. It uses the existing `STRUCTURE` flag from each building template's `KindOf` and reads the live construction status from the object. Apply the patch with your existing INI files and key bindings.

## Engine changes

Double-clicking calls the screen search through `0x009403ED`. The matching hotkey enters at `0x0069B9C8`, which tries the screen first and can fall back to the whole map. Both use the same region search at `0x006A43FE`.

| Hook address | Expected bytes | Change |
| --- | --- | --- |
| `0x006A4467` | `8B 46 04 89 45 F0` | Skip unfinished structures when collecting the template types from the current selection. Resume at `0x006A446D` for eligible objects or advance the loop at `0x006A44FE`. |
| `0x006A2955` | `E8 E6 B6 83 00` | Reject unfinished structures during the scan. Eligible candidates continue through the existing matching and selectability check at `0x00EDE040`. |

Both hooks use the same test. Reject an object only if its template carries `STRUCTURE` and it either has `UNDER_CONSTRUCTION` or has both `PENDING_CONSTRUCTION` and `PHANTOM_STRUCTURE`. The two pending flags cover a confirmed site while the builder is still walking to it.

| Flag | Address | Mask |
| --- | --- | --- |
| `STRUCTURE` | `[template + 0x108]`, where the template pointer is at `[object + 0x04]` | `0x80` |
| `UNDER_CONSTRUCTION` | `[object + 0x94]` | `0x04` |
| `PENDING_CONSTRUCTION` | `[object + 0x9E]` | `0x80` |
| `PHANTOM_STRUCTURE` | `[object + 0x9F]` | `0x01` |

## Build the patched game.dat

Use a compatible ROTWK 2.01.2614.37001 executable with the existing matching-building support. The first row below is the output of [08. Build the final game.dat](../modding/special-power-money-cost.md#build-the-final-gamedat). The second row covers the other verified input layout. Both columns are SHA-256 checksums.

| Input `game.dat` | Patched executable |
| --- | --- |
| `05712460c7676500fc9255ffc18aaacda6d8b9ff4b62e22f9f283a9fa15718c5` | `b6ecd8f5f0a86b3e232311599e078f437bd9bee0dc6c4bcd42fbed2521815a1a` |
| `ea4702bb41d135e500078c337a5764374950c17c50d88b1bfeb4a1ecf6ba2faf` | `3af4062d360b0662b596666260a9e698a7397140cd77eb689914bcf39fc1590a` |

Save the two listings below as `inspection/next/selection.s` and `inspection/next/patch_selection.py`. Use Python 3, GNU binutils with i386 support, and the [same pinned pySAGE checkout](https://github.com/ClementJ18/pySAGE/tree/0a1f1b5d71b1b080008a7e9fff6f997601ec5a7f) at `inspection/pysage-reference`. Run these commands from the build directory.

```bash
sha256sum game.dat
PYTHONPATH=inspection/pysage-reference python3 inspection/next/patch_selection.py game.dat game_with_selection.dat
sha256sum game_with_selection.dat
```

The script assembles the handlers in a new PE section named `.builtSel` and calculates each relative branch from its actual address. It checks the input digest and the bytes at both hook sites before writing a separate output file. To test the result, close the game and use the output as `game.dat` in a test installation.

<details>
<summary><code>inspection/next/selection.s</code></summary>

```asm
.intel_syntax noprefix
.code32
.section .text

# ECX = Object. Building orders set the pending flag before construction starts.
is_unfinished_structure:
    mov eax, [ecx+0x4]
    test byte ptr [eax+0x108], 0x80  # KindOf STRUCTURE
    jz .Lfinished
    test byte ptr [ecx+0x94], 0x04   # UNDER_CONSTRUCTION
    jnz .Lunfinished
    test byte ptr [ecx+0x9e], 0x80   # PENDING_CONSTRUCTION
    jz .Lfinished
    test byte ptr [ecx+0x9f], 0x01   # PHANTOM_STRUCTURE
    jnz .Lunfinished
.Lfinished:
    xor eax, eax
    ret
.Lunfinished:
    mov eax, 1
    ret

# The matching callback uses this call to check each candidate object.
.global check_candidate
check_candidate:
    call is_unfinished_structure
    test eax, eax
    jz .Lnative_candidate
    xor eax, eax
    ret
.Lnative_candidate:
    jmp 0xede040

# The matching search builds its type list from the current selection. A site
# selected by an ordinary click stays selected but cannot start a type search.
.global check_seed
check_seed:
    mov ecx, esi
    call is_unfinished_structure
    test eax, eax
    jnz .Lnext_seed
    mov eax, [esi+0x4]
    mov [ebp-0x10], eax
    jmp 0x6a446d
.Lnext_seed:
    jmp 0x6a44fe
```

</details>

<details>
<summary><code>inspection/next/patch_selection.py</code></summary>

```python
from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
from subprocess import check_output, run
from tempfile import TemporaryDirectory

from sage_patch.utils import allocate_section, apply_byte_patch, call_rel32, file_offset, jmp_rel32


HERE = Path(__file__).resolve().parent
COMPATIBLE_INPUTS = {
    '05712460c7676500fc9255ffc18aaacda6d8b9ff4b62e22f9f283a9fa15718c5',
    'ea4702bb41d135e500078c337a5764374950c17c50d88b1bfeb4a1ecf6ba2faf',
}
CANDIDATE = 0x6a2955
SEED = 0x6a4467


def patch_game(previous):
    if sha256(previous).hexdigest() not in COMPATIBLE_INPUTS:
        raise ValueError('Unexpected input game.dat. Compare its SHA-256 to the guide.')
    game = bytearray(previous)
    symbols = {}
    with TemporaryDirectory() as directory:
        work = Path(directory)
        obj, elf, raw = (work / name for name in ('selection.o', 'selection.elf', 'selection.bin'))
        run(['as', '--32', '-o', obj, HERE / 'selection.s'], check=True)

        def make_section(address):
            run(['ld', '-m', 'elf_i386', '-e', '0', '-Ttext', hex(address), '-o', elf, obj], check=True)
            run(['objcopy', '-O', 'binary', '-j', '.text', elf, raw], check=True)
            for row in check_output(['nm', '-g', '--defined-only', elf], text=True).splitlines():
                address, _, name = row.split()
                symbols[name] = int(address, 16)
            return raw.read_bytes()

        allocate_section(game, '.builtSel', make_section, 0x60000060)

    apply_byte_patch(game, file_offset(game, CANDIDATE), bytes.fromhex('e8e6b68300'),
                     call_rel32(CANDIDATE, symbols['check_candidate']), 'matching candidate')
    expected = bytes.fromhex('8b46048945f0')
    apply_byte_patch(game, file_offset(game, SEED), expected,
                     jmp_rel32(SEED, symbols['check_seed'], len(expected)), 'matching source')
    return game


def main():
    parser = ArgumentParser()
    parser.add_argument('input_executable', type=Path)
    parser.add_argument('output_executable', type=Path)
    args = parser.parse_args()

    if args.input_executable.resolve() == args.output_executable.resolve():
        parser.error('Choose a separate output file.')

    patched = patch_game(args.input_executable.read_bytes())
    args.output_executable.write_bytes(patched)
    print(sha256(patched).hexdigest(), args.output_executable)


if __name__ == '__main__':
    main()
```

</details>

## In-game verification

| Test | Expected result |
| --- | --- |
| Place two finished buildings of the same type beside a third under active construction. Double-click a finished one. | Both finished buildings are selected. |
| Single-click a finished one and press `E`. Test with another matching building off-screen to exercise the map fallback when there are no new matches on-screen. | The search adds only finished buildings of the matching type. |
| Repeat while a builder is travelling to the confirmed third site, then again after construction finishes. | The site is skipped while pending, then becomes eligible once it is finished. |
| Single-click a site and try `E` or double-click with that site as the only selection. | The site remains selected and the selection does not expand. |
| Select matching infantry using the same controls. | The existing unit selection rules apply. |

Machine-code tests exercised both input dispatchers, the template and candidate filters, and the existing single-object selectability path. The behavior still needs confirmation in a running match.
