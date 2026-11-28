from collections import deque
from pathlib import Path
from struct import pack, unpack_from
from xml.etree import ElementTree as ET
from zipfile import ZipFile, ZIP_DEFLATED

import unicorn as u
from unicorn.x86_const import *
from sage_apt.aptfile import apt_bytes_to_xml


def members(data):
    count, = unpack_from('>I', data, 8)
    pos = 16
    result = {}
    for _ in range(count):
        start, length = unpack_from('>II', data, pos)
        end = data.index(0, pos+8)
        result[data[pos+8:end].decode('ascii')] = data[start:start+length]
        pos = end+1
    return result


ROOT = Path(__file__).resolve().parents[2]
work = ROOT / "build" / "shared-army"
game = (work/'game.dat').read_bytes()
new = members((work/'playertribute.big').read_bytes())
root = ET.fromstring(apt_bytes_to_xml(new['PlayerTribute.apt'], new['PlayerTribute.const']))
labels = {
    root.find("./edittext[@id='96']/ettext").get('text').encode('ascii'): ('Заблокировать', 'Block'),
    root.find("./edittext[@id='101']/ettext").get('text').encode('ascii'): ('Управление армией', 'Army Control'),
}
assert set(labels) == {b'$ETBlock', b'$ShareArmy'}

cpu = u.Uc(u.UC_ARCH_X86, u.UC_MODE_32)
pe, = unpack_from('<I', game, 0x3c)
sections, = unpack_from('<H', game, pe+6)
optional_size, = unpack_from('<H', game, pe+20)
optional = pe+24
base, = unpack_from('<I', game, optional+28)
image_size, = unpack_from('<I', game, optional+56)
cpu.mem_map(base, image_size)
for index in range(sections):
    header = optional+optional_size+40*index
    _, rva, size, offset = unpack_from('<4I', game, header+8)
    if size and offset:
        cpu.mem_write(base+rva, game[offset:offset+size])
scratch = 0x2000000
cpu.mem_map(scratch, 0x10000)
cpu.mem_map(0, 0x1000)
sp = scratch+0xe000
frame = sp+0x100
heap = scratch+0x1000


def allocate(data):
    global heap
    ptr = heap
    cpu.mem_write(ptr,data)
    heap += (len(data)+3) & ~3
    return ptr


def dw(addr):
    return int.from_bytes(cpu.mem_read(addr,4),'little')


def put(addr,*words):
    cpu.mem_write(addr,pack('<'+'I'*len(words),*words))


def read_z(addr,width=1):
    output = bytearray()
    while (symbol := bytes(cpu.mem_read(addr+len(output),width))) != bytes(width):
        output.extend(symbol)
    return bytes(output)


def ansi(text):
    return allocate(bytes(8)+text+b'\0')


def wide(text):
    return allocate(bytes(8)+text.encode('utf-16le')+b'\0\0')


def arg(n):
    return dw(cpu.reg_read(UC_X86_REG_ESP)+4+4*n)


def hook(addr,callback):
    cpu.hook_add(u.UC_HOOK_CODE,lambda *_: callback(),begin=addr,end=addr)


def stub(addr,callback,clean=0):
    cpu.mem_write(addr,b'\xc3' if not clean else b'\xc2'+pack('<H',clean))
    hook(addr,callback)


def eax(value):
    cpu.reg_write(UC_X86_REG_EAX,value & 0xffffffff)


def find_colon():
    s = read_z(arg(0))
    assert arg(1) == ord(':')
    eax(arg(0)+s.index(b':') if b':' in s else 0)


def compare_insensitive():
    a,b = read_z(arg(0)).lower(),read_z(arg(1)).lower()
    eax((a>b)-(a<b))


def format_label():
    value = read_z(arg(1)) % read_z(arg(2))
    assert value in (b'APT:ETBlock', b'APT:ShareArmy')
    put(arg(0),ansi(value))


def format_missing():
    fmt = read_z(arg(1),2).decode('utf-16le').replace('%hs','%s')
    put(arg(0),wide(fmt % read_z(arg(2)).decode('ascii')))


def copy_ref():
    target = cpu.reg_read(UC_X86_REG_ECX)
    put(target,dw(arg(0)))
    eax(target)


put(0xbd061c,scratch+0x100)
put(0xbd051c,scratch+0x110)
stub(scratch+0x100,find_colon)
stub(scratch+0x110,compare_insensitive)
stub(0x437a90,format_label)
stub(0xadf750,format_missing)
stub(0x42f6e0,lambda: eax(allocate(bytes(arg(0)))))
stub(0x436a90,copy_ref,4)
stub(0x436990,copy_ref,4)
stub(0x4367b0,lambda: None)
native_fallbacks = []
hook(0x6e7ad0,lambda: native_fallbacks.append(True))
trace = deque(maxlen=32)
cpu.hook_add(u.UC_HOOK_BLOCK, lambda uc, addr, *_: trace.append(hex(addr)))
cpu.hook_add(u.UC_HOOK_MEM_INVALID, lambda cpu, access, addr, *_: print(
    hex(cpu.reg_read(UC_X86_REG_EIP)), hex(addr), access, list(trace)))


def lookup_table(name, text):
    key = allocate(pack('<I',ansi(name)))
    localized = allocate(pack('<II',0,wide(text)))
    pairs = allocate(pack('<II',key,localized))
    return allocate(pack('<III',1,0,pairs))


def expect_lookup(primary, secondary, expected, present, label=None):
    text_manager = allocate(bytes(0x44))
    put(text_manager,0xc1b470)
    put(text_manager+0x2c,primary,secondary)
    put(0xde4b04,text_manager)
    cpu.mem_write(frame-0x40,bytes(0x60))
    cpu.reg_write(UC_X86_REG_EBP,frame)
    cpu.reg_write(UC_X86_REG_ESP,sp)
    old_fallbacks = len(native_fallbacks)
    if label:
        cpu.reg_write(UC_X86_REG_ESI,allocate(bytes(0x40)))
        cpu.reg_write(UC_X86_REG_ECX,ord('$'))
        eax(ansi(label))
        cpu.emu_start(0x4aa577,0x4aa5cf,count=100000)
        assert cpu.reg_read(UC_X86_REG_EIP) == 0x4aa5cf
        text_result = dw(cpu.reg_read(UC_X86_REG_EAX))
    else:
        output = allocate(bytes(4))
        put(sp,0x9868c9,output,8)
        cpu.emu_start(0x960b14,0x9868c9,count=100000)
        assert cpu.reg_read(UC_X86_REG_EIP) == 0x9868c9
        text_result = dw(output)
    assert (len(native_fallbacks)==old_fallbacks) == present
    assert read_z(text_result+8,2).decode('utf-16le') == expected


for label, (russian, english) in {**labels, None: ('Совместное управление войсками', 'Shared Army Control')}.items():
    key = b'APT:' + label[1:] if label else b'RULE:ShareArmy'
    expect_lookup(0, 0, f"MISSING: '{key.decode()}'", False, label)
    expect_lookup(lookup_table(key, russian), 0, russian, True, label)
    expect_lookup(0, lookup_table(key, english), english, True, label)
print("Verified all three labels through native GameText translation and missing-key paths.")
