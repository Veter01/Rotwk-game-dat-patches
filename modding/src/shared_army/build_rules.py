from hashlib import sha256
from pathlib import Path
from struct import pack, pack_into, unpack_from
import sys
import xml.etree.ElementTree as ET

from sage_apt.aptfile import apt_bytes_to_xml

from apt_big import member_bytes, read_index, replace_members

APT = b"MpGameSetup.apt"
CONSTANTS = b"MpGameSetup.const"


def u32(data, offset):
    return unpack_from("<I", data, offset)[0]


def extend_rules(apt, constants):
    result = bytearray(apt)
    characters = u32(apt, u32(constants, 20) + 24)

    def append(payload):
        result.extend(bytes(-len(result) % 4))
        offset = len(result)
        result.extend(payload)
        return offset

    new_name = append(b"4\x00")
    for character, new_depth, spacing in ((10, 17, 33), (189, 25, 34)):
        sprite = u32(apt, characters + 4 * character)
        assert u32(apt, sprite) == 5
        frame = u32(apt, sprite + 12)
        count, array = unpack_from("<II", apt, frame)
        controls = list(unpack_from(f"<{count}I", apt, array))
        for control in controls:
            if u32(apt, control) != 3:
                continue
            name = u32(apt, control + 52)
            if name and apt[name:name + 2] == b"3\x00":
                break
        else:
            raise ValueError(f"Checkbox 3 was not found in sprite {character}")
        assert all(u32(apt, at) != 3 or u32(apt, at + 8) != new_depth for at in controls)
        template = bytearray(apt[control:control + 64])
        y = unpack_from("<f", template, 36)[0]
        pack_into("<I", template, 8, new_depth)
        pack_into("<f", template, 36, y + spacing)
        pack_into("<I", template, 52, new_name)
        controls.append(append(template))
        pack_into("<II", result, frame, len(controls), append(pack(f"<{len(controls)}I", *controls)))
    xml = ET.fromstring(apt_bytes_to_xml(bytes(result), constants))
    for character in (10, 189):
        frame = xml.find(f"sprite[@id='{character}']/frames/frame[@id='0']")
        assert [node.get("name") for node in frame.findall("placeobject/poname")].count("4") == 1
    return bytes(result)


def main(source, output):
    original = source.read_bytes()
    assert sha256(original).hexdigest() == "fa0d60542bcd7d83f9ba24230cfeec2dd2d087b35fec8ce568467231164490db"
    entries, end = read_index(original)
    apt, constants = (member_bytes(original, entries[name]) for name in (APT, CONSTANTS))
    result = replace_members(original, entries, end, {APT: extend_rules(apt, constants)})
    patched, _ = read_index(result)
    assert patched.keys() == entries.keys()
    for name in entries.keys() - {APT}:
        assert member_bytes(result, patched[name]) == member_bytes(original, entries[name])
    output.write_bytes(result)


if __name__ == "__main__":
    main(*(Path(value) for value in sys.argv[1:]))
