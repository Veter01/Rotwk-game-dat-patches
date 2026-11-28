from copy import deepcopy
from io import BytesIO
from pathlib import Path
from struct import pack, pack_into
from xml.etree import ElementTree as ET
import subprocess

from PIL import Image, ImageChops, ImageDraw
from apt_big import member_bytes, read_index, replace_members
from sage_apt.aptfile import apt_bytes_to_xml, xml_bytes_to_apt
from sage_apt.geometry import parse_geometry
from sage_apt.imagemap import parse_image_map


ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / "build" / "help"
ATLAS = b"art/Textures/apt_Options_1.tga"
IMAGE_MAP = b"Options.dat"
APT = b"Options.apt"
CONST = b"Options.const"
IMAGE_ID, SHAPE_ID = 377, 378
X, Y, SIZE = 952, 64, 64
ICON_BOX = X, Y, X + SIZE, Y + SIZE


def verify_available_space(atlas, entries):
    maps = parse_image_map(entries[IMAGE_MAP].decode("ascii"))
    assert not any(maps.texture_of(image) == 1 for image in maps.rects)
    sampled = Image.new("1", atlas.size)
    draw = ImageDraw.Draw(sampled)
    for path, data in entries.items():
        if not path.endswith(b".ru"):
            continue
        for fill in parse_geometry(data.decode("latin-1")):
            if fill.image_id is None or maps.texture_of(fill.image_id) != 1:
                continue
            a, b, c, d, tx, ty = fill.matrix
            for triangle in fill.triangles:
                draw.polygon(
                    [(a * x + c * y + tx, b * x + d * y + ty)
                     for x, y in zip(triangle[::2], triangle[1::2], strict=True)],
                    fill=1,
                )
    padding = 4
    bounds = X - padding, Y - padding, X + SIZE + padding, Y + SIZE + padding
    assert 0 <= bounds[0] < bounds[2] <= atlas.width
    assert 0 <= bounds[1] < bounds[3] <= atlas.height
    assert sampled.crop(bounds).getbbox() is None
    assert atlas.getchannel("A").crop(bounds).getbbox() is None


def place_in_atlas(texture, icon_data, entries):
    with Image.open(BytesIO(texture)) as atlas, Image.open(BytesIO(icon_data)) as icon:
        assert atlas.mode == icon.mode == "RGBA"
        assert atlas.size == (1024, 512) and icon.size == (SIZE, SIZE)
        assert texture[:18] == pack("<BBBHHBHHHHBB", 0, 0, 2, 0, 0, 0, 0, 0, 1024, 512, 32, 8)
        verify_available_space(atlas, entries)
        old_image = atlas.copy()
        icon = icon.copy()
    result = bytearray(texture)
    icon_rows = icon.tobytes("raw", "BGRA")
    for row in range(SIZE):
        destination = 18 + ((old_image.height - 1 - (Y + row)) * old_image.width + X) * 4
        source = row * SIZE * 4
        result[destination:destination + SIZE * 4] = icon_rows[source:source + SIZE * 4]
    with Image.open(BytesIO(result)) as packed:
        assert packed.crop(ICON_BOX).tobytes() == icon.tobytes()
        restored = packed.copy()
        restored.paste(old_image.crop(ICON_BOX), (X, Y))
        assert ImageChops.difference(restored, old_image).getbbox(alpha_only=False) is None
        packed.save(WORK / "atlas-preview.png")
    return bytes(result)


def add_icon_to_movie(apt, const):
    movie = ET.fromstring(apt_bytes_to_xml(apt, const))
    frame = movie.find("./sprite[@id='376']/frames/frame[@id='0']")
    label = movie.find("./edittext[@id='374']")
    label.attrib.update(alignment="0", right="213")
    placement = frame.find("./placeobject[@character='374']")
    placement.set("tx", "92")
    icon = deepcopy(placement)
    icon.attrib.update(depth="5", character=str(SHAPE_ID), tx="56", ty="376.5")
    frame.append(icon)
    ET.SubElement(movie, "image", id=str(IMAGE_ID), image=str(IMAGE_ID))
    ET.SubElement(movie, "shape", id=str(SHAPE_ID), geometry=str(SHAPE_ID),
                  top="0", left="0", bottom="32", right="26")
    result = xml_bytes_to_apt(ET.tostring(movie, encoding="utf-8"))
    reparsed = apt_bytes_to_xml(*result)
    assert xml_bytes_to_apt(reparsed) == result
    verified = ET.fromstring(reparsed)
    selected = verified.find("./sprite[@id='376']/frames/frame[@id='0']")
    assert [int(node.get("character")) for node in selected.findall("placeobject")] == [372, 373, 375, 374, SHAPE_ID]
    action = verified.find("./button[@id='375']/buttonactions/buttonaction")
    assert [node.get("str") for node in action.findall("pushstring")] == ["1", "ETOpenHelp", "GameCode"]
    assert b"ETOpenHelp2" not in reparsed and b"ETHelpLink2" not in reparsed
    (WORK / "Options-help.xml").write_bytes(reparsed)
    return result


def add_big_member(archive, name, data):
    index, header = read_index(archive)
    assert name not in index
    entry_size = 8 + len(name) + 1
    entry = pack(">II", len(archive) + entry_size, len(data)) + name + b"\0"
    result = bytearray(archive[:header] + entry + archive[header:] + data)
    pack_into("<I", result, 4, len(result))
    pack_into(">II", result, 8, len(index) + 1, header + entry_size)
    for offset, start, _ in index.values():
        pack_into(">I", result, offset, start + entry_size)
    return bytes(result)


def render_discord():
    svg = Path(__file__).with_name("discord.svg")
    png = WORK / "discord.png"
    subprocess.run(
        ["inkscape", str(svg), "--export-width=256", "--export-height=256", f"--export-filename={png}"],
        check=True,
    )
    with Image.open(png) as render:
        icon = render.convert("RGBA").resize((SIZE, SIZE), Image.Resampling.LANCZOS)
    assert icon.getchannel("A").getextrema() == (0, 255)
    header = pack("<BBBHHBHHHHBB", 0, 0, 2, 0, 0, 0, 0, 0, SIZE, SIZE, 32, 8)
    pixels = icon.transpose(Image.Transpose.FLIP_TOP_BOTTOM).tobytes("raw", "BGRA")
    return header + pixels + bytes(8) + b"TRUEVISION-XFILE.\0"


source = (WORK / "options-page.big").read_bytes()
discord = render_discord()
index, header = read_index(source)
entries = {name: member_bytes(source, item) for name, item in index.items()}
apt, const = add_icon_to_movie(entries[APT], entries[CONST])
assert entries[IMAGE_MAP].endswith(b"\r\n")
image_map = entries[IMAGE_MAP] + f"{IMAGE_ID}->1\r\n".encode()
parsed_map = parse_image_map(image_map.decode())
assert parsed_map.texture_of(IMAGE_ID) == 1 and parsed_map.rect_of(IMAGE_ID) is None
updated_atlas = place_in_atlas(entries[ATLAS], discord, entries)

geometry_name = f"Options_geometry/{SHAPE_ID}.ru".encode()
geometry = (
    f"c\r\ns tc:255:255:255:255:{IMAGE_ID}:{SIZE / 26:.8f}:0:0:2:{X}:{Y}\r\n"
    "t 0:32:0:0:26:0\r\n"
    "t 26:0:26:32:0:32\r\n"
).encode()
fill, = parse_geometry(geometry.decode())
assert fill.image_id == IMAGE_ID and fill.matrix[-2:] == (X, Y)
changes = {APT: apt, CONST: const, IMAGE_MAP: image_map, ATLAS: updated_atlas}
updated = replace_members(source, index, header, changes)
options = add_big_member(updated, geometry_name, geometry)
result_index, _ = read_index(options)
assert list(result_index) == list(index) + [geometry_name]
assert all(member_bytes(options, result_index[name]) == data
           for name, data in {**entries, **changes, geometry_name: geometry}.items())

(WORK / "options.big").write_bytes(options)
print(f"Packed {len(result_index)} BIG members with the Discord icon in the shared atlas.")
