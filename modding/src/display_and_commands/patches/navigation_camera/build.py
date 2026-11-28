from hashlib import sha256
from pathlib import Path
from struct import pack_into, unpack_from
from subprocess import check_output, run
from xml.etree import ElementTree as ET

from sage_apt.aptfile import CHAR_SIG, MOVIE, PLACEOBJECT, SPRITE, apt_bytes_to_xml
from sage_patch.utils import allocate_section, apply_byte_patch, call_rel32, file_offset, jmp_rel32, read_bytes

HERE = Path(__file__).resolve().parent
GAME = 'game.dat'
OPTIONS = 'apt/options.big'
GAME_HASH = '947a02859ea7791fcc6f12bdf1da71a09a165c840275ea54e8e4ed66ddb91240'
HOOKS = (
    (0x83af66, 'e977637100', 'edge_event'),
    (0x83b53e, '8b0d1844de00', 'edge_tick'),
)
CLIP_CALL_SITE = 0xf4c665
NATIVE = {
    'original_edge_event': 0xf512e2,
    'start_edge_scroll': 0x83afc8,
    'stop_edge_scroll': 0x83af9e,
    'finish_mouse_event': 0x83afd1,
    'stop_edge_tick': 0xf51315,
    'apply_edge_scroll': 0x83b851,
    'original_viewport_tick': 0x83b544,
}
NAVIGATION = (
    (17, 363, 'Tab5', 392, 332),
    (18, 335, 'Selected5', 392, 332),
    (19, 364, None, 404, 344),
    (20, 370, 'Tab6', 332, 392),
    (21, 335, 'Selected6', 332, 392),
    (22, 371, None, 344, 404),
)


def patch_game(stock, work):
    assert sha256(stock).hexdigest() == GAME_HASH
    assert read_bytes(stock, 0xf512e2, 11).hex() == '38592c0f84809c8eff5051'
    assert read_bytes(stock, 0xf51315, 7).hex() == '89f1e846978eff'
    image = bytearray(stock)
    native, hooks, elf, raw, layout = [work / name for name in ('edges.o', 'hooks.o', 'edges.elf', 'edges.bin', 'edges.ld')]
    run(['gcc', '-m32', '-Os', '-std=c11', '-ffreestanding', '-fno-pic', '-fno-pie',
         '-fno-stack-protector', '-fno-asynchronous-unwind-tables', '-fno-unwind-tables',
         '-fno-ident', '-msse2', '-mfpmath=sse', '-mpreferred-stack-boundary=2',
         '-mincoming-stack-boundary=2', '-Wall', '-Wextra', '-Werror',
         '-c', HERE / 'edges.c', '-o', native], check=True)
    run(['as', '--32', HERE / 'hooks.s', '-o', hooks], check=True)
    layout.write_text('''
SECTIONS {
    . = PATCH_ADDRESS;
    .patch : { *(.text*) *(.rodata*) *(.data*) *(.bss*) BYTE(0) }
    /DISCARD/ : { *(.note*) *(.comment*) }
}
''')
    symbols = {}

    def payload(address):
        definitions = {'PATCH_ADDRESS': address, **NATIVE}
        run(['ld', '-m', 'elf_i386', '--no-warn-rwx-segments', '-z', 'noexecstack',
             '-T', layout, *[f'--defsym={name}={value:#x}' for name, value in definitions.items()],
             '-o', elf, native, hooks], check=True)
        for line in check_output(['nm', '--defined-only', elf], text=True).splitlines():
            value, _, name = line.split()
            symbols[name] = int(value, 16)
        run(['objcopy', '-O', 'binary', '-j', '.patch', elf, raw], check=True)
        return raw.read_bytes()

    allocate_section(image, '.wndedge', payload, 0xe0000060)
    for site, old, name in HOOKS:
        before = bytes.fromhex(old)
        apply_byte_patch(image, file_offset(image, site), before,
                         jmp_rel32(site, symbols[name], len(before)), name)
    apply_byte_patch(image, file_offset(image, CLIP_CALL_SITE), bytes.fromhex('ff15cc08bd00'),
                     call_rel32(CLIP_CALL_SITE, symbols['clip_window_cursor']) + b'\x90',
                     'Use the reachable viewport when cursor clipping is enabled')
    return bytes(image), symbols


def big_entries(blob):
    assert blob[:4] == b'BIGF' and unpack_from('<I', blob, 4)[0] == len(blob)
    cursor = 16
    result = {}
    for _ in range(unpack_from('>I', blob, 8)[0]):
        offset, size = unpack_from('>II', blob, cursor)
        end = blob.index(0, cursor + 8)
        name = blob[cursor + 8:end].decode('ascii')
        assert name not in result and offset + size <= len(blob)
        result[name] = offset, size
        cursor = end + 1
    return result


def patch_options(blob):
    entries = big_entries(blob)
    start, length = entries['Options.apt']
    apt = bytearray(blob[start:start+length])
    start_const, length_const = entries['Options.const']
    const = blob[start_const:start_const+length_const]
    before = ET.fromstring(apt_bytes_to_xml(bytes(apt), const))
    navigation = [place for place in before.findall('.//placeobject') if place.find('poname[@name="Navigation"]') is not None]
    assert len(navigation) == 1
    sprite_id = int(navigation[0].get('character'))

    movie = unpack_from('<I', const, 0x14)[0]
    assert unpack_from('<II', apt, movie) == (MOVIE, CHAR_SIG)
    count, character_table = unpack_from('<II', apt, movie + 20)
    assert 0 < sprite_id < count
    sprite = unpack_from('<I', apt, character_table + sprite_id * 4)[0]
    kind, signature, frames, frame_table = unpack_from('<IIII', apt, sprite)
    assert kind == SPRITE and signature == CHAR_SIG and frames == 1
    item_count, item_table = unpack_from('<II', apt, frame_table)
    placements = {}
    for index in range(item_count):
        item = unpack_from('<I', apt, item_table + 4 * index)[0]
        item_type = unpack_from('<I', apt, item)[0]
        if item_type == PLACEOBJECT:
            depth = unpack_from('<i', apt, item + 8)[0]
            assert depth not in placements
            placements[depth] = item

    frame = before.find(f'./sprite[@id="{sprite_id}"]/frames/frame[@id="0"]')
    for depth, character, name, previous_y, new_y in NAVIGATION:
        item = placements[depth]
        assert unpack_from('<i', apt, item + 12)[0] == character
        assert unpack_from('<f', apt, item + 36)[0] == previous_y
        clip = frame.find(f'placeobject[@depth="{depth}"]')
        named = clip.find('poname')
        assert (named.get('name') if named is not None else None) == name
        pack_into('<f', apt, item + 36, new_y)
        clip.set('ty', str(new_y))

    after = ET.fromstring(apt_bytes_to_xml(bytes(apt), const))
    assert ET.tostring(before) == ET.tostring(after)
    return blob[:start] + apt + blob[start+length:]
