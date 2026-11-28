from hashlib import sha256
from pathlib import Path
from struct import pack
from subprocess import check_output, run

from sage_patch.utils import allocate_section, apply_byte_patch, call_rel32, file_offset, jmp_rel32, read_bytes

HERE = Path(__file__).resolve().parent
BASE_HASH = 'b77bdca8345ee1a702544df7a15ba5b96b6b58c09370fa4e0d80ffc4fe182d44'
GAME = 'game.dat'

HOOKS = (
    (0x6c1d23, '0bc1894608', 'on_destroy_game_window', jmp_rel32),
    (0xf4cb61, 'a1acd1f400', 'check_display_controls', jmp_rel32),
    (0xf4c5d4, 'a174d1f400', 'cursor_clipping_guard', jmp_rel32),
    (0xf4c665, 'e88d6c0000', 'clip_resize_window', call_rel32),
    (0xf4cfd0, 'e87ff9ffff', 'apply_resized_window', call_rel32),
    (0xf4d013, 'e88af6ffff', 'window_resize_message', call_rel32),
)
WINDOW_STYLE = 0x10ca0000
RESIZABLE_FRAME = 0x00040000
STYLE_SITES = (0xf5806d, 0xf580bc, 0xf58391)

NATIVE = {
    'native_control_update_next': 0xf4cb66,
    'native_destroy_next': 0x6c1d28,
    'native_apply_clip_next': 0xf4c5d9,
    'native_restore_window': 0xf4c1ce,
    'apply_cursor': 0xf4c5d4,
    'release_cursor': 0xf4c0f3,
    'stock_cursor_event': 0xf4c6a2,
    'stock_window_clip': 0xf532f7,
    'stock_apply_pending_mode': 0xf4c954,
}


def patch_game(stock, work):
    assert sha256(stock).hexdigest() == BASE_HASH
    image = bytearray(stock)
    for vtable in (0xbddbb8, 0xc158c0):
        assert read_bytes(stock, vtable + 0x8c, 4) == pack('<I', 0x6c1cfc)
    cfile, asfile, elf, raw, layout = [work / name for name in ('resize.o', 'hooks.o', 'resize.elf', 'resize.bin', 'resize.ld')]
    run(['gcc', '-m32', '-Os', '-std=c11', '-ffreestanding', '-fno-pic', '-fno-pie',
         '-fno-stack-protector', '-fno-asynchronous-unwind-tables', '-fno-unwind-tables',
         '-fno-ident', '-msse2', '-mfpmath=sse', '-mpreferred-stack-boundary=2',
         '-mincoming-stack-boundary=2', '-Wall', '-Wextra', '-Werror',
         '-c', HERE / 'resize.c', '-o', cfile], check=True)
    run(['as', '--32', HERE / 'hooks.s', '-o', asfile], check=True)
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
             '-o', elf, cfile, asfile], check=True)
        for line in check_output(['nm', '--defined-only', elf], text=True).splitlines():
            addr, _, label = line.split()
            symbols[label] = int(addr, 16)
        run(['objcopy', '-O', 'binary', '-j', '.patch', elf, raw], check=True)
        return raw.read_bytes()

    allocate_section(image, '.wndsize', payload, 0xe0000060)
    for site, old, name, branch in HOOKS:
        before = bytes.fromhex(old)
        apply_byte_patch(image, file_offset(image, site), before, branch(site, symbols[name]), name)
    for site in STYLE_SITES:
        apply_byte_patch(image, file_offset(image, site), pack('<I', WINDOW_STYLE),
                         pack('<I', WINDOW_STYLE | RESIZABLE_FRAME), 'Use a resizable window frame')
    return bytes(image), symbols
