from hashlib import sha256
from pathlib import Path
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[2]
work = ROOT / "build" / "harvest"
source = (ROOT / "inputs" / "game.dat").read_bytes()
assert sha256(source).hexdigest() == "bad61adac79fa2e1919d65387196913610685b5c0b05b6219e4872e6dd49f3f5"
game = bytearray(source)
source_dir = Path(__file__).resolve().parent
obj = work / "dispatch.o"
binary = work / "dispatch.bin"
subprocess.run(["as", "--32", "-o", str(obj), str(source_dir / "dispatch.s")], check=True)
symbols = {
    "worker_module_data": 0xF4F097, "nearest_supply_source": 0x8FAA51,
    "issue_dock": 0x66C609, "finish_harvest_order": 0x897F00,
    "finish_power": 0x897F25, "resume_tree_search": 0x897EE9,
}
subprocess.run([
    "ld", "-m", "elf_i386", "-Ttext=0xf4f770", "--oformat", "binary",
    "-e", "harvest_dispatch_v2",
    *(f"--defsym={name}={address:#x}" for name, address in symbols.items()),
    "-o", str(binary), str(obj),
], check=True)
dispatch = binary.read_bytes()
big = work / "____enrth_data_ArnorAutoHarvest.big"
assert sha256(big.read_bytes()).hexdigest() == "fd79742a7e2ebf2be88db9e433b8a827bdf01d5aea260e169de246b3611de669"

pe, = struct.unpack_from("<I", game, 0x3c)
assert game[pe:pe + 4] == b"PE\0\0"
count, = struct.unpack_from("<H", game, pe + 6)
optional_header_size, = struct.unpack_from("<H", game, pe + 20)
optional_header = pe + 24
assert struct.unpack_from("<H", game, optional_header)[0] == 0x10b
image_base, = struct.unpack_from("<I", game, optional_header + 28)
section_table = optional_header + optional_header_size
sections = {
    game[p:p + 8].rstrip(b"\0").decode(): p
    for p in range(section_table, section_table + count * 40, 40)
}

text_header = sections[".text"]
harvest_header = sections[".harvest"]
text_size, text_rva, text_raw_size, text_raw_offset = struct.unpack_from("<4I", game, text_header + 8)
harvest_size, harvest_rva, harvest_raw_size, harvest_raw_offset = struct.unpack_from("<4I", game, harvest_header + 8)

hook_va = 0x897ee4
hook_offset = text_raw_offset + hook_va - (image_base + text_rva)
dispatch_va = 0xf4f770
dispatch_relative = dispatch_va - (image_base + harvest_rva)
dispatch_offset = harvest_raw_offset + dispatch_relative
dispatch_end = dispatch_offset + len(dispatch)
new_harvest_size = dispatch_relative + len(dispatch)
assert text_raw_offset <= hook_offset < hook_offset + 5 <= text_raw_offset + min(text_size, text_raw_size)
assert game[hook_offset:hook_offset + 5] == bytes.fromhex("8d45e05057")
assert harvest_size <= dispatch_relative < new_harvest_size <= harvest_raw_size
assert not any(game[dispatch_offset:dispatch_end])
assert not any(game[harvest_raw_offset + harvest_size:harvest_raw_offset + harvest_raw_size])

game[hook_offset:hook_offset + 5] = b"\xe9" + struct.pack("<i", dispatch_va - hook_va - 5)
game[dispatch_offset:dispatch_end] = dispatch
struct.pack_into("<I", game, harvest_header + 8, new_harvest_size)

assert len(game) == len(source)
for start, stop in (
    (0, harvest_header + 8),
    (harvest_header + 12, hook_offset),
    (hook_offset + 5, dispatch_offset),
    (dispatch_end, len(source)),
):
    assert game[start:stop] == source[start:stop]

(work / "game.dat").write_bytes(game)
