from hashlib import sha256
import json
from pathlib import Path
from struct import pack
import subprocess

from sage_patch.utils import allocate_section, file_offset


ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / "build" / "help"
TABLE = 0xF3D3A8


def build(original):
    assert sha256(original).hexdigest() == "600afcae2ff784d09d758e05f5db65d89620b1bf05b8d9d1d5535b919ec7e19f"
    game = bytearray(original)
    labels = {}
    offset = file_offset(original, TABLE)
    existing_commands = original[offset:offset + 10 * 8]

    def assemble(base):
        obj, elf, payload = [WORK / f"help.{ext}" for ext in ("o", "elf", "bin")]
        subprocess.run(["as", "--32", "-o", str(obj), str(Path(__file__).with_name("help.s"))], check=True)
        subprocess.run(["ld", "-m", "elf_i386", f"-Ttext={base:#x}", "-e", "select_help_page",
                        "-o", str(elf), str(obj)], check=True)
        subprocess.run(["objcopy", "-O", "binary", "-j", ".text", str(elf), str(payload)], check=True)
        for line in subprocess.check_output(["nm", "-n", str(elf)], text=True).splitlines():
            address, kind, name = line.split()
            if kind.lower() == "t":
                labels[name] = int(address, 16)
        result = bytearray(payload.read_bytes())
        result.extend(bytes(-len(result) % 4))
        labels["options_commands"] = base + len(result)
        result.extend(existing_commands)
        # Strings follow the expanded fixed-size table.
        page_name = b"AptOptions::ETPage6\0"
        link_name = b"AptOptions::ETOpenHelp\0"
        strings_address = labels["options_commands"] + len(existing_commands) + 16
        result.extend(pack("<II", strings_address, labels["select_help_page"]))
        result.extend(pack("<II", strings_address + len(page_name), labels["open_help_link"]))
        result.extend(page_name + link_name)
        return bytes(result)

    allocate_section(game, ".opthelp", assemble, 0x60000020)
    address = labels["options_commands"]
    for location, expected, updated in (
        (0xf237d8, pack("<I", TABLE + 4), pack("<I", address + 4)),
        (0xf237f2, pack("<I", TABLE), pack("<I", address)),
        (0xf23823, b"\x0a", b"\x0c"),
    ):
        offset = file_offset(game, location)
        assert game[offset:offset + len(expected)] == expected
        game[offset:offset + len(updated)] = updated
    return bytes(game), labels


if __name__ == "__main__":
    game, labels = build((WORK.parent / "shared-army" / "game.dat").read_bytes())
    (WORK / "game.dat").write_bytes(game)
    (WORK / "labels.json").write_text(json.dumps(labels, indent=2))
    print(f"Game with Help: {len(game):,} bytes")
