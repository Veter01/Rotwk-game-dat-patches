from hashlib import sha256
from pathlib import Path
from subprocess import check_output, run

from sage_patch.utils import allocate_section, apply_byte_patch, call_rel32, file_offset, jmp_rel32

HERE = Path(__file__).resolve().parent
BASE_HASH = '65215ab414a9395d90488e3594efdf0bb738b7dcf978b5af34d52dbb0c628555'
GAME = 'game.dat'

HOOKS = (
    (0x83b47e, '807e380057', 'poll_camera', jmp_rel32),
    (0xf533a2, 'e85cfdffff', 'window_scroll_edges', call_rel32),
    (0xf5326b, 'e893feffff', 'window_scroll_edges', call_rel32),
    (0xf5130c, 'e825000000', 'legacy_scroll_guard', call_rel32),
    (0xf4c893, 'a37cd1f400', 'select_mode', jmp_rel32),
    (0xf4cc47, '8d65f85b5e5de958f8ffff', 'sync_mode', jmp_rel32),
    (0xf4cc95, 'a1acd1f400', 'read_reset_mode', jmp_rel32),
    (0xf4ce5a, 'a1acd1f400', 'read_save_mode', jmp_rel32),
    (0xf4c8b0, '8b1580d1f400', 'cancel_mode', jmp_rel32),
    (0xf59232, 'e81d37ffff', 'apply_allowed_display_mode', call_rel32),
)

NATIVE = {
    'moving_window': 0xf59538,
    'stock_window_edges': 0xf53103,
    'stock_cursor_in_window': 0xf51336,
    'stock_apply_pending_mode': 0xf4c954,
    'native_camera_frame': 0x83b483,
    'native_select_return': 0xf4c898,
    'native_sync_resolution': 0xf4c4aa,
    'native_reset_test': 0xf4cc9a,
    'native_save_test': 0xf4ce5f,
    'native_cancel_mode': 0xf4c8b6,
    'native_cancel_return': 0xf4c8d9,
}


def patch_game(stock, work):
    assert sha256(stock).hexdigest() == BASE_HASH
    image = bytearray(stock)
    cfile, asfile, elf, raw, layout = [work / name for name in
                                       ('window.o', 'hooks.o', 'window.elf', 'window.bin', 'window.ld')]
    run(['gcc', '-m32', '-Os', '-std=c11', '-ffreestanding', '-fno-pic', '-fno-pie',
         '-fno-stack-protector', '-fno-asynchronous-unwind-tables', '-fno-unwind-tables',
         '-fno-ident', '-msse2', '-mfpmath=sse', '-mpreferred-stack-boundary=2',
         '-mincoming-stack-boundary=2', '-Wall', '-Wextra', '-Werror',
         '-c', HERE / 'window.c', '-o', cfile], check=True)
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

    allocate_section(image, '.wndplay', payload, 0x60000020)
    for site, old, name, branch in HOOKS:
        before = bytes.fromhex(old)
        encoded = branch(site, symbols[name])
        apply_byte_patch(image, file_offset(image, site), before,
                         encoded.ljust(len(before), b'\x90'), name)
    return bytes(image), symbols
