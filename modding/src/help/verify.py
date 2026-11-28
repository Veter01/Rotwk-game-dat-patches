import json
from pathlib import Path
from struct import pack, unpack_from
from xml.etree import ElementTree as ET

import unicorn as u
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_EDX, UC_X86_REG_ESP, UC_X86_REG_EIP


ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / "build" / "help"
ROOT = ET.parse(WORK / "Options-help.xml").getroot()
COMMANDS = json.loads((WORK / "labels.json").read_text())


def char(number):
    return ROOT.find(f"*[@id='{number}']")


def execute_apt(actions, root, variables=None):
    variables = {"_root": root, **(variables or {})}
    stack = []
    labels = {op.get("anchor"): index for index, op in enumerate(actions) if op.get("anchor")}
    pointer = 0
    while pointer < len(actions):
        op = actions[pointer]
        pointer += 1
        if op.tag in ("pushstring", "pushbyte"):
            stack.append(op.get("str") if op.tag == "pushstring" else int(op.get("val")))
        elif op.tag in ("pushzero", "pushone"):
            stack.append(int(op.tag == "pushone"))
        elif op.tag == "pushfalse":
            stack.append(False)
        elif op.tag == "pushthis":
            stack.append(variables["this"])
        elif op.tag == "getstringvar":
            stack.append(variables[op.get("str")])
        elif op.tag == "getmember":
            field, container = stack.pop(), stack.pop()
            stack.append(container[field])
        elif op.tag == "setmember":
            value, field, container = stack.pop(), stack.pop(), stack.pop()
            container[field] = value
        elif op.tag == "newequals":
            stack.append(stack.pop() == stack.pop())
        elif op.tag == "logicalnot":
            stack.append(not stack.pop())
        elif op.tag == "branchiftrue":
            if stack.pop():
                pointer = labels[op.get("target")]
        elif op.tag == "noarg" and op.get("action") == "82":
            method, receiver, count = stack.pop(), stack.pop(), stack.pop()
            stack.append(receiver[method](*(stack.pop() for _ in range(count))))
        elif op.tag == "pop":
            stack.pop()
        else:
            assert op.tag == "end", op.tag
    assert not stack


select = ROOT.find(".//definefunction[@name='ETSelectPage']/body")
nav = char(347).find(".//frame")
tab_y = {p.find("poname").get("name"): int(p.get("ty")) for p in nav
         if p.find("poname") is not None and p.find("poname").get("name").startswith("Tab")}
assert [name for name, _ in sorted(tab_y.items(), key=lambda item: item[1])] == [
    "Tab0", "Tab1", "Tab2", "Tab3", "Tab4", "Tab6", "Tab5"
]
page_names = ("FrameLeft", "ScreenPage", "FrameMiddle", "HotkeysPage", "FrameRight", "OtherPage", "HelpPage")
screen = {name: {} for name in (*page_names, "PanelBack", "SubTitle", "Navigation")}
screen["Navigation"].update({f"Selected{page}": {} for page in range(7)})
actions = []
root = {"Main": screen, "GameCode": lambda *args: actions.append(args),
        "ETSyncSoundTips": lambda: None}
root["ETSelectPage"] = lambda page: execute_apt(select, root, {"page": page})
for character in (336, 370, 375, 363):
    execute_apt(char(character).find(".//buttonaction"), root)
assert actions == [("ETPage0",), ("ETPage6",), ("ETOpenHelp", "1"), ("ETPage5",)]
execute_apt(char(376).find(".//action"), root, {"this": screen["HelpPage"]})
assert not screen["HelpPage"]["_visible"]
for page in (*range(7), 9):
    root["ETSelectPage"](page)
    assert [name for name in page_names if screen[name]["_visible"]] == (
        [] if page == 9 else [page_names[page]]
    )
    assert screen["Navigation"]["Selected6"]["_visible"] == (page == 6)
    assert screen["Navigation"]["_visible"] == (page != 9)
    assert actions[-1] == (f"ETPage{page}",)
assert char(373).get("multiline") == char(373).get("wordwrap") == "1"
assert tuple(char(n).find("ettext").get("text") for n in range(371, 375)) == (
    "$ETHelp", "$ETHelp", "$ETHelpText", "$ETHelpLink",
)
print("Verified all eight APT page states, tab order, and the Help button command.")

game = (WORK / "game.dat").read_bytes()
pe, = unpack_from("<I", game, 0x3c)
count, = unpack_from("<H", game, pe + 6)
optional_size, = unpack_from("<H", game, pe + 20)
base, = unpack_from("<I", game, pe + 24 + 28)
size_image, = unpack_from("<I", game, pe + 24 + 56)
cpu = u.Uc(u.UC_ARCH_X86, u.UC_MODE_32)
cpu.mem_map(0, 0x1000)
cpu.mem_map(base, size_image)
for section in range(count):
    _, rva, size, offset = unpack_from("<4I", game, pe + 24 + optional_size + section * 40 + 8)
    if size and offset:
        cpu.mem_write(base + rva, game[offset:offset + size])
arena = 0x2000000
cursor = arena + 0x1000
stack = arena + 0x3e000
stop_addr = arena + 0x700
dialog = arena + 0x100
cpu.mem_map(arena, 0x40000)


def alloc(data):
    global cursor
    address = cursor
    cpu.mem_write(address, data)
    cursor += (len(data) + 3) & ~3
    return address


def get(addr):
    return unpack_from("<I", cpu.mem_read(addr, 4))[0]


def put(addr, *words):
    cpu.mem_write(addr, pack("<" + "I" * len(words), *words))


def string(addr, wide=False):
    char_size = 2 if wide else 1
    result = bytearray()
    while value := bytes(cpu.mem_read(addr + len(result), char_size)):
        if value == b"\0" * char_size:
            break
        result.extend(value)
    return result.decode("utf-16le" if wide else "ascii")


def with_header(text, wide=False):
    return alloc(bytes(8) + (text + "\0").encode("utf-16le" if wide else "ascii"))


def arg(index):
    return get(cpu.reg_read(UC_X86_REG_ESP) + (index + 1) * 4)


def stub(addr, callback, clean=0):
    cpu.mem_write(addr, b"\xc3" if not clean else b"\xc2" + pack("<H", clean))
    cpu.hook_add(u.UC_HOOK_CODE, lambda *_: callback(), begin=addr, end=addr)


def eax(value):
    cpu.reg_write(UC_X86_REG_EAX, value & 0xffffffff)


def this():
    return cpu.reg_read(UC_X86_REG_ECX)


def run(address, args=(), ecx=0):
    cpu.reg_write(UC_X86_REG_ECX, ecx)
    cpu.reg_write(UC_X86_REG_EDX, 0)
    cpu.reg_write(UC_X86_REG_ESP, stack)
    put(stack, stop_addr, *args)
    cpu.emu_start(address, stop_addr, count=100000)
    assert cpu.reg_read(UC_X86_REG_EIP) == stop_addr
    assert cpu.reg_read(UC_X86_REG_ESP) == stack + 4


registered = {}
freed = []


def set_ansi():
    put(this(), with_header(string(arg(0))))
    eax(this())


def copy_ref():
    put(this(), get(arg(0)))
    eax(this())


def register_options():
    assert this() == dialog + 0x21c
    registered[string(get(arg(0)) + 8)] = arg(1)


def wformat():
    formatted = string(arg(1), True).replace("%hs", "%s") % string(arg(2))
    put(arg(0), with_header(formatted, True))


def compare():
    a, b = string(arg(0)).lower(), string(arg(1)).lower()
    eax((a > b) - (a < b))


stub(0x4374e0, set_ansi, 4)
stub(0x435d50, lambda: freed.append("ansi"))
stub(0x436a90, copy_ref, 4)
stub(0x436990, copy_ref, 4)
stub(0x4367b0, lambda: freed.append("wide"))
stub(0x92b062, register_options, 8)
stub(0x42f6e0, lambda: eax(alloc(bytes(arg(0)))))
stub(0xadf750, wformat)
put(0xbd051c, arena + 0xa00)
stub(arena + 0xa00, compare)
run(0xf237b8, (dialog,))
assert len(registered) == 12
assert set(registered).issuperset({
    "AptOptions::ETPage0", "AptOptions::ETPage5", "AptOptions::ETPage6", "AptOptions::ETPage9",
    "AptOptions::ETOpenHelp",
})


def dispatch(name, params=""):
    # Invoke the actual C++ member functor used by the FSCommand dispatcher.
    wrapped = alloc(pack("<I", registered[f"AptOptions::{name}"]))
    args = (0, alloc(params.encode("ascii") + b"\0"), 0)
    cpu.reg_write(UC_X86_REG_ECX, wrapped)
    cpu.reg_write(UC_X86_REG_ESP, stack)
    put(stack, stop_addr, *args)
    cpu.emu_start(0x62262d, stop_addr, count=100000)
    assert cpu.reg_read(UC_X86_REG_EIP) == stop_addr
    assert cpu.reg_read(UC_X86_REG_ESP) == stack + 16


native_visibility = []
put(0xf3b020, arena + 0x900)
stub(0x724411, lambda: None)
stub(0x71552b, lambda: native_visibility.append((this(), arg(0))), 4)
put(0xf27674, dialog)
dispatch("ETPage6")
assert get(0xf2767c) == 6
assert native_visibility == [(arena + 0x900, 1)]
print("Verified engine registration and native gadget visibility when Help is active.")


def translations(url):
    key = alloc(pack("<I", with_header("APT:ETHelpURL")))
    value = alloc(pack("<II", 0, with_header(url, True)))
    return alloc(pack("<III", 1, 0, alloc(pack("<II", key, value))))


game_text = alloc(bytes(0x44))
put(game_text, 0xc1b470)
put(0xde4b04, game_text)
window = 0x1234
put(0xdc3c64, window)
launches = []


def launch():
    assert arg(0) == window and string(arg(1), True) == "open"
    assert (arg(3), arg(4), arg(5)) == (0, 0, 1)
    launches.append(string(arg(2), True))
    eax(33)


put(0xbd07a4, arena + 0xb00)
stub(arena + 0xb00, launch, 24)

web = "https://example.com/справка?категория=игра"
browser = "HtTpS://example.org/help"
app = "myapp://open/help"
mail = "mailto:help@example.org"
for idx, url in enumerate((web, app, mail, browser)):
    put(game_text + 0x2c, translations(url) if idx % 2 == 0 else 0,
        translations(url) if idx % 2 else 0)
    dispatch("ETOpenHelp", "1")
    assert launches[-1] == url
assert launches == [web, app, mail, browser]
for url in ("", "file:///test.txt", "FiLe://test/path", "not a link", "https:", "https:///help",
            "https://?help", r"C:\test.txt", r"\\server\share", "https://example.com/a b",
            "javascript:alert(1)", "https://example.com/\nhelp"):
    put(game_text + 0x2c, translations(url), 0)
    dispatch("ETOpenHelp", "1")
    assert freed[-2:] == ["wide", "ansi"]
put(game_text + 0x2c, 0, 0)
dispatch("ETOpenHelp", "1")
put(game_text + 0x2c, translations(web), 0)
put(0xf2767c, 5)
dispatch("ETOpenHelp", "1")
put(0xf2767c, 6)
put(0xf27674, dialog + 4)
dispatch("ETOpenHelp", "1")
assert launches == [web, app, mail, browser]
print("Verified native lotr.str lookup for both language tables, exact UTF-16 ShellExecuteW arguments, and no launch on missing or invalid values.")
