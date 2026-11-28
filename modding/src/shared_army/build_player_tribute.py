from copy import deepcopy
from pathlib import Path
import re
from struct import pack_into, unpack_from
import xml.etree.ElementTree as ET

from sage_apt.aptfile import apt_bytes_to_xml, xml_bytes_to_apt

ROOT = Path(__file__).resolve().parents[2]
work = ROOT / "build" / "shared-army"
archive_path = ROOT / "inputs" / "playertribute.big"
original = archive_path.read_bytes()
assert original[:4] == b"BIGF"
count, table_end = unpack_from(">2I", original, 8)
pos = 16
entries = {}
for _ in range(count):
    offset, length = unpack_from(">2I", original, pos)
    end = original.index(0, pos + 8)
    name = original[pos + 8:end].decode("ascii")
    entries[name] = (pos, original[offset:offset + length])
    pos = end + 1
assert len(entries) == count
assert pos <= table_end + 1

apt_name = "PlayerTribute.apt"
const_name = "PlayerTribute.const"
grid_name = "PlayerTribute_geometry/59.ru"
apt_original = entries[apt_name][1]
const_original = entries[const_name][1]
root = ET.fromstring(apt_bytes_to_xml(apt_original, const_original))


def char(number):
    return next(node for node in root if node.get("id") == str(number))


def frame(number, index=0):
    return char(number).find(f"frames/frame[@id='{index}']")


def placement(frame_node, **by_attribute):
    return next(child for child in frame_node.findall("placeobject")
                if all(child.get(name) == str(value) for name, value in by_attribute.items()))


def nfmt(number):
    return f"{number:.7f}".rstrip("0").rstrip(".")


def center_text(character, clip, center, width, scale=1):
    left = float(character.get("left"))
    character.set("right", nfmt(left + width))
    clip.set("rotm00", nfmt(scale))
    clip.set("tx", nfmt(center - scale * (left + width / 2)))


# Coordinates in StatusPage space. Keep the outside frame and parent menus fixed.
columns = (0, 91, 184, 222, 286, 350, 441.3)
centers = tuple((left + right) / 2 for left, right in zip(columns, columns[1:]))
outer = frame(61)
row = frame(50)
rows = frame(52, 1)
row_parent = placement(outer, character=52)
row_parent_scale = float(row_parent.get("rotm00"))
sample_row = placement(rows, character=51)
row_x = float(row_parent.get("tx")) + row_parent_scale * float(sample_row.get("tx"))
status_units = frame(51, 4)
colored_x = float(placement(status_units, character=50).get("tx"))
char(46).set("right", "102.9")
for i, character in enumerate((47, 48, 49), 1):
    span = columns[i + 1] - columns[i] - 8
    center_text(char(character), placement(row, character=character),
                (centers[i] - row_x) / row_parent_scale - colored_x, span)
for i, character in enumerate((53, 55, 56, 54)):
    span = columns[i + 1] - columns[i] - 6
    center_text(char(character), placement(outer, character=character), centers[i], span)

block_caption = placement(outer, character=96)
char(96).find("ettext").set("text", "$ETBlock")
char(96).set("height", "10")
center_text(char(96), block_caption, centers[4], 116, 0.53)
block_box = placement(status_units, character=90)
block_box.set("tx", nfmt((centers[4] - row_x) / row_parent_scale))

# Give the new button its own handlers and state. Reuse the status checkbox artwork.
ids = {87: 97, 88: 98, 89: 99, 90: 100}
for existing, new in ids.items():
    node = deepcopy(char(existing))
    node.set("id", str(new))
    for place in node.iter("placeobject"):
        child_id = int(place.get("character"))
        if child_id in ids:
            place.set("character", str(ids[child_id]))
    root.append(node)

# Wait for the roster query before showing a box. Only the disabled state
# needs the inactive artwork.
pending_frame = frame(99, 0)
pending_box = placement(pending_frame, character=95)
disabled_box = deepcopy(pending_box)
pending_frame.remove(pending_box)
disabled_frame = frame(99, 3)
assert disabled_frame.find("framelabel[@label='_disabled']") is not None
assert disabled_frame.find("removeobject[@depth='1']") is not None
disabled_frame.append(disabled_box)
hidden_frame = deepcopy(disabled_frame)
hidden_frame.set("id", "4")
hidden_frame.find("framelabel").set("label", "_hidden")
hidden_frame.remove(placement(hidden_frame, character=95))
char(99).find("frames").append(hidden_frame)

for number, handler in ((97, "GrantShareArmy"), (98, "RevokeShareArmy")):
    node = next(x for x in char(number).iter("pushstring") if x.get("str") == "ToggleChat")
    node.set("str", handler)

share_action = frame(100).find("action")
rename = {
    "SetMuteState": "SetShareState",
    "ToggleChat": "GrantShareArmy",
    "RefreshChat": "RefreshShareArmy",
    "cmt=": "scg=",
    "cmq=": "scq=",
}
for node in char(100).iter("pushstring"):
    name = node.get("str")
    if name in rename:
        node.set("str", rename[name])
functions = share_action.findall("definefunction")
grant_body = functions[1].find("body")
refresh_body = functions[2].find("body")
for body in (grant_body, refresh_body):
    callback_end = next(i for i, cmd in enumerate(body) if cmd.tag == "pop") + 1
    del body[callback_end:]

grant_index = list(share_action).index(functions[1]) - 2
revoke = [deepcopy(node) for node in list(share_action)[grant_index:grant_index + 4]]
revoke[1].set("str", "RevokeShareArmy")
revoke[2].find("body/pushstring[@str='scg=']").set("str", "scr=")
for i, node in enumerate(revoke):
    share_action.insert(grant_index + 4 + i, node)

poll = ET.fromstring("""
<body>
  <pushthis/>
  <pushstring str="ShareArmyPoll"/>
  <pushthis/>
  <getstringmember str="ShareArmyPoll"/>
  <increment/>
  <setmember/>
  <pushthis/>
  <getstringmember str="ShareArmyPoll"/>
  <pushbyte val="8"/>
  <newlessthan/>
  <branchiftrue target="L1"/>
  <pushthis/>
  <pushstring str="ShareArmyPoll"/>
  <pushzero/>
  <setmember/>
  <pushzero/>
  <pushthis/>
  <pushstring str="RefreshShareArmy"/>
  <noarg action="82"/>
  <pop/>
  <pushzero anchor="L1"/>
  <pop/>
</body>
""")
functions[3].remove(functions[3].find("body"))
functions[3].append(poll)
frame_setup = list(share_action).index(share_action.find("gotoframe"))
for i, command in enumerate(ET.fromstring(
    '<setup><pushthis/><pushstring str="ShareArmyPoll"/><pushzero/><setmember/></setup>'
)):
    share_action.insert(frame_setup + i, command)

share_box = deepcopy(block_box)
share_box.set("character", "100")
share_box.set("depth", "3")
share_box.set("tx", nfmt((centers[5] - row_x) / row_parent_scale))
share_box.find("poname").set("name", "ShareArmy")
status_units.append(share_box)

# Native APT EditText resolves $ShareArmy as APT:ShareArmy in the game text table.
# Leave room for the full missing-key label within the existing column.
caption_token = "$ShareArmy"
caption = deepcopy(char(96))
caption.set("id", "101")
caption.set("height", "10")
caption.find("ettext").set("text", caption_token)
root.append(caption)
clip = deepcopy(block_caption)
clip.attrib.update(character="101", depth="25")
center_text(caption, clip, centers[5], 130, 0.66)
outer.append(clip)

grid_clip = placement(outer, character=60)
grid_tx = float(grid_clip.get("tx"))
grid_scale = float(grid_clip.get("rotm00"))
grid_original = entries[grid_name][1].decode("ascii")
assert all(grid_original.count(x) > 0 for x in ("105.03878", "226.02586", "269.02127", "339.01379"))
coordinates = {
    old: nfmt((new - grid_tx) / grid_scale)
    for old, new in zip(("105.03878", "226.02586", "269.02127", "339.01379"), columns[1:5])
}
grid = re.sub(r"105\.03878|226\.02586|269\.02127|339\.01379",
              lambda match: coordinates[match[0]], grid_original)
new_divider = nfmt((columns[5] - grid_tx) / grid_scale)
grid += f"l {new_divider}:0:{new_divider}:229.1\r\n"

xml = ET.tostring(root, encoding="utf-8")
(work / "PlayerTribute-SharedArmy.xml").write_bytes(xml)
apt, const = xml_bytes_to_apt(xml)
decoded = ET.fromstring(apt_bytes_to_xml(apt, const))
assert len(decoded) == len(root)
assert decoded.find("sprite[@id='51']/frames/frame[@id='4']/placeobject[@character='100']/poname").get("name") == "ShareArmy"
disabled = decoded.find("sprite[@id='99']/frames/frame[@id='3']")
assert disabled.find("framelabel[@label='_disabled']") is not None
assert disabled.find("placeobject[@character='95'][@depth='1']") is not None
hidden = decoded.find("sprite[@id='99']/frames/frame[@id='4']")
assert hidden.find("framelabel[@label='_hidden']") is not None
assert hidden.find("removeobject[@depth='1']") is not None
assert hidden.find("placeobject") is None
assert decoded.find("sprite[@id='99']/frames/frame[@id='0']/placeobject") is None
assert decoded.find("shape[@id='95']") is not None
assert decoded.find("button[@id='95']") is None
decoded_outer = decoded.find("sprite[@id='61']/frames/frame[@id='0']")
assert decoded_outer.find("placeobject[@character='101'][@depth='25']") is not None
assert decoded.find("edittext[@id='101']/ettext").get("text") == caption_token
assert decoded.find("edittext[@id='96']/ettext").get("text") == "$ETBlock"
assert apt.count(caption_token.encode("ascii") + b"\0") == 1
assert "Передать управление".encode("utf-8") not in apt
assert "Заблокировать".encode("utf-8") not in apt
for token in ("scg=", "scr=", "scq=", "SetShareState"):
    assert any(node.get("str") == token for node in decoded.findall("sprite[@id='100']//pushstring"))
assert b"ChatMute\0" in apt and b"ShareArmy\0" in apt

replacements = {apt_name: apt, const_name: const, grid_name: grid.encode("ascii")}
first = table_end + 1
header = bytearray(original[:first])
data_parts = []
offset = first
for name, (entry, existing) in entries.items():
    content = replacements.get(name, existing)
    pack_into(">2I", header, entry, offset, len(content))
    data_parts.append(content)
    offset += len(content)
pack_into("<I", header, 4, offset)
output = work / "playertribute.big"
output.write_bytes(b"".join([header, *data_parts]))

packed = output.read_bytes()
assert len(packed) == offset
changed = set()
for name, (entry, existing) in entries.items():
    start, size = unpack_from(">2I", packed, entry)
    actual = packed[start:start + size]
    assert actual == replacements.get(name, existing)
    if actual != existing:
        changed.add(name)
assert changed == set(replacements)
print(f"{output.name}: verified {count} contents, localized caption, and checkbox actions")
