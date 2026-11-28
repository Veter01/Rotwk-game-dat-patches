from pathlib import Path
import re
import struct

ROOT = Path(__file__).resolve().parents[2]
work = ROOT / "build" / "harvest"
source_path = ROOT / "inputs" / "____enrth_data.big"
output_path = work / "____enrth_data_ArnorAutoHarvest.big"
source = source_path.read_bytes()
worker = r"data\ini\object\goodfaction\units\arnor\new\arnorharvester.ini"
center = r"data\ini\object\goodfaction\structures\arnor\new\stoneworkerMod.ini"
rocks = r"data\ini\object\neutral\SupplyRocks.ini"
command_sets = r"data\ini\includes\commandset.inc"


def archive_entries(data):
    assert data[:4] == b"BIGF"
    assert struct.unpack_from("<I", data, 4)[0] == len(data)
    count, index_end = struct.unpack_from(">II", data, 8)
    entries = {}
    position = 16
    expected_offset = index_end + 1
    for _ in range(count):
        offset, size = struct.unpack_from(">II", data, position)
        name_end = data.index(0, position + 8, index_end)
        name = data[position + 8:name_end].decode("cp1252")
        assert name not in entries and offset == expected_offset
        assert offset + size <= len(data)
        entries[name] = (position, offset, size)
        position = name_end + 1
        expected_offset = offset + size
    assert data[position:index_end + 1] == b"L225\x00\x00\x00\x00"
    assert expected_offset == len(data)
    return index_end + 1, entries


def replace_once(data, original, updated):
    assert data.count(original) == 1, original
    return data.replace(original, updated, 1)


def mark_stone_piles(data):
    pattern = rb"(?m)^(  KindOf = [^;\r\n]*\bSUPPLY_SOURCE)(?=[ ;\r])"
    updated, count = re.subn(pattern, rb"\1 HARVEST_STONE", data)
    assert count == len(re.findall(rb"(?m)^  Behavior = SupplyWarehouseDockUpdate\b", data)) == 33
    return updated


payload_start, entries = archive_entries(source)
source_view = memoryview(source)


def entry_data(name):
    _, offset, size = entries[name]
    return bytes(source_view[offset:offset + size])


original_worker = entry_data(worker)
worker_data, count = re.subn(
    rb"(?m)^([\t ]+)(HarvestTrees[\t ]*=[\t ]*No)([^\r\n]*)\r\n",
    rb"\1\2\3\r\n\1HarvestKindOf = HARVEST_STONE\r\n\1WarehouseKindOf = STONE_WAREHOUSE\r\n",
    original_worker,
)
assert count == 1
original_center = entry_data(center)
center_data = replace_once(
    original_center,
    b"CANNOT_BUILD_NEAR_SUPPLIES ;;AUTO_RALLYPOINT",
    b"CANNOT_BUILD_NEAR_SUPPLIES STONE_WAREHOUSE ;;AUTO_RALLYPOINT",
)
original_command_sets = entry_data(command_sets)
command_set_data = replace_once(
    original_command_sets,
    b"   ;; 1 = Command_HarvestArnor\r\n",
    b"     1   = Command_HarvestArnor\r\n",
)
edits = {
    worker: worker_data,
    center: center_data,
    rocks: mark_stone_piles(entry_data(rocks)),
    command_sets: command_set_data,
}

header = bytearray(source[:payload_start])
archive_size = len(source) + sum(len(data) - entries[name][2] for name, data in edits.items())
struct.pack_into("<I", header, 4, archive_size)
offset = payload_start
for name, (entry_position, _, size) in entries.items():
    if name in edits:
        size = len(edits[name])
    struct.pack_into(">II", header, entry_position, offset, size)
    offset += size
assert offset == archive_size

with output_path.open("wb") as stream:
    stream.write(header)
    for name, (_, offset, size) in entries.items():
        stream.write(edits[name] if name in edits else source_view[offset:offset + size])

packed = output_path.read_bytes()
packed_view = memoryview(packed)
_, packed_entries = archive_entries(packed)
assert list(entries) == list(packed_entries)
changed = set()
for name, (_, old_offset, old_size) in entries.items():
    _, new_offset, new_size = packed_entries[name]
    before = source_view[old_offset:old_offset + old_size]
    after = packed_view[new_offset:new_offset + new_size]
    if before != after:
        changed.add(name)
        assert after == edits[name], name
assert changed == set(edits)

rock_data = edits[rocks]
rock_objects = re.findall(rb"(?m)^Object (\w+)\r?\n(.*?)(?=^End\r?$)", rock_data, re.S)
assert len(rock_objects) == 34
for name, block in rock_objects:
    assert (b"HARVEST_STONE" in block) == (b"Behavior = SupplyWarehouseDockUpdate" in block)
    assert (name == b"SupplyRocksNull") == (b"HARVEST_STONE" not in block)

button_rules = entry_data(r"data\ini\commandbutton.ini")
button = re.search(rb"(?ms)^CommandButton Command_HarvestArnor\r\n(.*?)^End\b", button_rules)[1]
assert re.search(rb"(?m)^\s*SpecialPower\s*=\s*SpecialAbilityHarvest\s*$", button)
assert re.search(rb"(?m)^\s*AutoAbility\s*=\s*Yes\s*$", button)
assert b"SpecialPowerTemplate      = SpecialAbilityHarvest" in worker_data
assert b"Behavior = AutoAbilityBehavior" in worker_data
assert b"SpawnTemplateName = ArnorHarvester" in center_data
assert b"Behavior = SupplyCenterDockUpdate" in center_data
assert b"Behavior = SupplyCenterCreate" in center_data
assert b"CommandSet = ArnorHarvesterCommandSet" in worker_data
print(f"{output_path}: {archive_size:,} bytes, {len(entries)} entries, {len(changed)} edited entries")
for name in edits:
    print(name)
