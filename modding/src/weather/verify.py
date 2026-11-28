import re
import struct
import unicorn as u
from unicorn.x86_const import (
    UC_X86_REG_EAX, UC_X86_REG_EBP, UC_X86_REG_EBX,
    UC_X86_REG_ECX, UC_X86_REG_EIP, UC_X86_REG_ESP,
)

from build import BEHAVIOR, ROOT, SPELLS, packed


game = (ROOT / "build" / "shared-army" / "game.dat").read_bytes()
pe, = struct.unpack_from("<I", game, 0x3c)
count, = struct.unpack_from("<H", game, pe + 6)
opt_size, = struct.unpack_from("<H", game, pe + 20)
base, = struct.unpack_from("<I", game, pe + 24 + 28)
size_image, = struct.unpack_from("<I", game, pe + 24 + 56)
cpu = u.Uc(u.UC_ARCH_X86, u.UC_MODE_32)
cpu.mem_map(0, 0x1000)
cpu.mem_map(base, size_image)
for section in range(count):
    _, rva, size, offset = struct.unpack_from("<4I", game, pe + 24 + opt_size + section * 40 + 8)
    if size and offset:
        cpu.mem_write(base + rva, game[offset:offset + size])

arena = 0x2000000
cpu.mem_map(arena, 0x10000)
stack, exit_addr = arena + 0xff00, arena + 0x100
module, weather_state, fields, io_ptr = [arena + offset for offset in (0x1000, 0x2000, 0x3000, 0x4000)]
weather_ids = {b"SUNNY": 4, b"RAINY": 2, b"CLOUDYRAINY": 3}


def get(addr):
    return int.from_bytes(cpu.mem_read(addr, 4), "little")


def put(addr, *words):
    cpu.mem_write(addr, struct.pack("<" + "I" * len(words), *words))


def text(addr):
    return bytes(cpu.mem_read(addr, 64)).split(b"\0", 1)[0].decode("ascii")


def hook(address, routine):
    return cpu.hook_add(u.UC_HOOK_CODE, lambda *_: routine(), begin=address, end=address)


def sub_return(result=0, arguments=0):
    esp = cpu.reg_read(UC_X86_REG_ESP)
    cpu.reg_write(UC_X86_REG_EAX, result)
    cpu.reg_write(UC_X86_REG_EIP, get(esp))
    cpu.reg_write(UC_X86_REG_ESP, esp + 4 + 4 * arguments)


def argument(index):
    return get(cpu.reg_read(UC_X86_REG_ESP) + 4 * (index + 1))


def run(address, args=(), stop=exit_addr, **regs):
    put(stack, exit_addr, *args)
    cpu.reg_write(UC_X86_REG_ESP, stack)
    for register, value in regs.items():
        cpu.reg_write(globals()["UC_X86_REG_" + register], value)
    cpu.emu_start(address, stop, count=2000)
    assert cpu.reg_read(UC_X86_REG_EIP) == stop
    return cpu.reg_read(UC_X86_REG_EAX)


def find_field(name):
    for index in range(get(fields + 0x80)):
        table = get(fields + index * 4)
        while get(table):
            if text(get(table)) == name:
                return get(table + 4), get(table + 12)
            table += 16
    raise AssertionError(name)


def next_token():
    sub_return(next(token_addresses), 1)


def compare_token():
    sub_return(int(text(argument(0)) != text(argument(1))))


def parse_int():
    put(argument(2), int(text(argument(0))))
    sub_return(1)


put(0xbd051c, arena + 0x200)
put(0xbd05e8, arena + 0x300)
hook(arena + 0x200, compare_token)
hook(arena + 0x300, parse_int)
hook(0x42dc9f, next_token)
hook(0x719dee, sub_return)
hook(0x71a04f, sub_return)
hook(0x71a13d, lambda: sub_return(arguments=6))
put(0xde772c, weather_state)
put(0xde46a8, io_ptr)

for path, powers in SPELLS.items():
    for block in BEHAVIOR.finditer(packed[path]):
        power = re.search(rb"(?m)^[ \t]*SpecialPowerTemplate[ \t]*=[ \t]*(\w+)", block[0])
        if not power or power[1] not in powers:
            continue
        factor, = re.findall(rb"(?m)^[ \t]*DarkeningFactor[ \t]*=[ \t]*([^\r\n]+)", block[0])
        expected_mode = weather_ids[powers[power[1]][1]]
        put(fields + 0x80, 0)
        # The OCL factory registers the shared table, followed by its own fields.
        registry = 0x8c7b0b if block[1] == b"OCLSpecialPower" else 0x89699b
        run(registry, (fields,))
        parser, field_offset = find_field("DarkeningFactor")
        for offset in range(0, 0xa0, 4):
            put(module + offset, 0)
        values = re.findall(rb"([RGB]):(\d+)", factor)
        tokens = [part for pair in values for part in pair]
        token_addresses = iter(arena + 0x500 + i * 0x80 for i in range(len(tokens)))
        for i, token in enumerate(tokens):
            cpu.mem_write(arena + 0x500 + i * 0x80, token + b"\0")
        run(parser, (io_ptr, 0, module + field_offset, 0))
        red, green, blue = (int(value) for _, value in values)
        assert bytes(cpu.mem_read(module + 0x2c, 4)) == bytes((0, red, green, blue))
        assert cpu.mem_read(module + 0x69, 1)[0] == 1
        cpu.mem_write(module + 0x2c, b"\x01")
        put(module + 0x30, 1800)
        put(module + 0x64, expected_mode)
        put(weather_state + 0x10, 0)
        run(0x897adf, stop=0x897d14, EBX=module, EBP=arena+0xfe00)
        assert get(weather_state + 0x10) == expected_mode
        assert get(weather_state + 0x28) == 1800
        assert get(0xf4629c) == (1 << (23 + expected_mode)) | (blue << 16) | (green << 8) | red
        if expected_mode != 4:
            run(0x492f80, stop=0x492f85, EAX=0x00ffffff)
            assert cpu.reg_read(UC_X86_REG_EAX) == 0xff000000 | red << 16 | green << 8 | blue
        print(power[1].decode(), "registered, parsed and used the RGB from the packed INI")
