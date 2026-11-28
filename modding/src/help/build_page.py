from copy import deepcopy
from pathlib import Path
from xml.etree import ElementTree as ET

from apt_big import member_bytes, read_index, replace_members
from sage_apt.aptfile import apt_bytes_to_xml, xml_bytes_to_apt


ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / "build" / "help"
APT = b"Options.apt"
CONST = b"Options.const"
HELP_PAGE = 6


def build(archive):
    entries, header = read_index(archive)
    original_apt, original_const = (member_bytes(archive, entries[name]) for name in (APT, CONST))
    root = ET.fromstring(apt_bytes_to_xml(original_apt, original_const))
    original = deepcopy(root)

    def character(number):
        return root.find(f"*[@id='{number}']")

    def frame(number, index=0):
        return character(number).find(f"frames/frame[@id='{index}']")

    def clone(number, new_number):
        child = deepcopy(character(number))
        child.set("id", str(new_number))
        root.append(child)
        return child

    def place(frame_node, depth, character_id, x, y, name=None, scale_x=1):
        placement = ET.SubElement(
            frame_node, "placeobject", depth=str(depth), character=str(character_id),
            rotm00=str(scale_x), rotm01="0", rotm10="0", rotm11="1", tx=str(x), ty=str(y),
            red="255", green="255", blue="255", alpha="255", ratio="0", clipdepth="-1", unknown="0",
        )
        flags = "HasCharacter|HasMatrix"
        if name:
            flags += "|HasName"
        ET.SubElement(placement, "poflags", value=flags)
        if name:
            ET.SubElement(placement, "poname", name=name)
        return placement

    def commands(xml):
        return list(ET.fromstring(f"<body>{xml}</body>"))

    def localized(character_id, new_id, key, **style):
        item = clone(character_id, new_id)
        item.attrib.update(style)
        item.find("ettext").set("text", f"${key}")
        return item

    # Copy the existing tab skin and keep the original page numbers.
    tab = clone(363, 370)
    tab.find("buttonactions/buttonaction/pushbyte").set("val", str(HELP_PAGE))
    localized(364, 371, "ETHelp")
    navigation = frame(347)
    for depth in (17, 18, 19):
        other = navigation.find(f"placeobject[@depth='{depth}']")
        other.set("ty", str(int(other.get("ty")) + 60))
    place(navigation, 20, 370, 0, 332, "Tab6")
    place(navigation, 21, 335, 0, 332, "Selected6")
    place(navigation, 22, 371, 14, 344)

    # The help page has one wrapped text field and a button in the normal menu style.
    localized(365, 372, "ETHelp")
    localized(366, 373, "ETHelpText", right="550", bottom="285",
              red="235", green="240", blue="243", alpha="255", multiline="1", wordwrap="1")
    localized(364, 374, "ETHelpLink", right="257", alignment="2",
              red="187", green="222", blue="236", alpha="255")
    link = clone(363, 375)
    link_action = link.find("buttonactions/buttonaction")
    # GameCode(ETOpenHelp, "1") sends a fixed token. The URL is looked up natively.
    link_action[:] = commands("""
        <pushstring str="1"/>
        <pushstring str="ETOpenHelp"/>
        <pushbyte val="2"/>
        <getstringvar str="_root"/>
        <pushstring str="GameCode"/>
        <noarg action="82"/>
        <pop/>
        <end/>
    """)
    page = ET.SubElement(root, "sprite", id="376")
    content = ET.SubElement(ET.SubElement(page, "frames"), "frame", id="0")
    ET.SubElement(content, "action").extend(commands("""
        <pushthis/>
        <pushstring str="_visible"/>
        <pushfalse/>
        <setmember/>
        <end/>
    """))
    place(content, 1, 372, 0, 0)
    place(content, 2, 373, 40, 54)
    place(content, 3, 375, 40, 370, "OpenHelp", scale_x=1.5)
    place(content, 4, 374, 50, 382)
    place(frame(175), 1700, 376, 206, -30, "HelpPage")
    # The advanced graphics frame removes the other page clips as well.
    frame(175, 19).insert(0, ET.Element("removeobject", depth="1700"))

    select_page = root.find(".//definefunction[@name='ETSelectPage']/body")
    select_page[:0] = commands("""
        <getstringvar str="_root"/>
        <pushstring str="Main"/>
        <getmember/>
        <pushstring str="HelpPage"/>
        <getmember/>
        <pushstring str="_visible"/>
        <getstringvar str="page"/>
        <pushbyte val="6"/>
        <newequals/>
        <setmember/>
        <getstringvar str="_root"/>
        <pushstring str="Main"/>
        <getmember/>
        <pushstring str="Navigation"/>
        <getmember/>
        <pushstring str="Selected6"/>
        <getmember/>
        <pushstring str="_visible"/>
        <getstringvar str="page"/>
        <pushbyte val="6"/>
        <newequals/>
        <setmember/>
    """)
    select_page[-5:-5] = commands("""
        <getstringvar str="page"/>
        <pushbyte val="6"/>
        <newequals/>
        <logicalnot/>
        <branchiftrue target="HelpPageDone"/>
        <pushstring str="ETPage6"/>
        <pushbyte val="1"/>
        <getstringvar str="_root"/>
        <pushstring str="GameCode"/>
        <noarg action="82"/>
        <pop/>
        <pushzero anchor="HelpPageDone"/>
        <pop/>
    """)

    apt, const = xml_bytes_to_apt(ET.tostring(root, encoding="utf-8"))
    actual = ET.fromstring(apt_bytes_to_xml(apt, const))
    for old in original:
        if old.tag == "movieclip" or (old.tag == "sprite" and old.get("id") in ("175", "347")):
            continue
        current = next(child for child in actual if child.tag == old.tag and child.get("id") == old.get("id"))
        ET.indent(old)
        ET.indent(current)
        assert ET.tostring(old).strip() == ET.tostring(current).strip(), old.attrib
    result = replace_members(archive, entries, header, {APT: apt, CONST: const})
    new_entries, _ = read_index(result)
    assert new_entries.keys() == entries.keys()
    assert all(member_bytes(result, new_entries[name]) == member_bytes(archive, entries[name])
               for name in entries.keys() - {APT, CONST})
    return result, actual


if __name__ == "__main__":
    big, tree = build((ROOT / "inputs" / "options.big").read_bytes())
    ET.indent(tree)
    (WORK / "Options-help.xml").write_bytes(ET.tostring(tree, encoding="utf-8"))
    (WORK / "options-page.big").write_bytes(big)
    print(f"Options with Help: {len(big):,} bytes")
