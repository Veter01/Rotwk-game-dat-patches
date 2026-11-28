from hashlib import sha256
from pathlib import Path
from subprocess import check_output, run

from sage_patch.utils import allocate_section, apply_byte_patch, file_offset, jmp_rel32, read_bytes

HERE = Path(__file__).resolve().parent
BASE_HASH = '8e96c2eca02ceab762e7caf5e797ac51d6749564a7af2b7a3e2b93f32cb9fdc6'
GAME = 'game.dat'

HOOKS = (
    (0xf4c35c, '31c0895db88945b0', 'fit_configure_window'),
    (0xf4c47a, '8b458c8b7d9c', 'configure_client_size'),
    (0xf4ca0c, '833d84d1f400018945a07410', 'keep_preferred_resolution'),
    (0xf4c7d1, '83fb02774e', 'initial_window_mode'),
    (0x645e8b, 'ff575884c0', 'apply_queued_resolution'),
)

NATIVE = {
    'configure_failed': 0xf4c384,
    'apply_window_geometry': 0xf4c3dd,
    'store_client_size': 0xf4c480,
    'update_preferred': 0xf4ca18,
    'use_preferred': 0xf4ca28,
    'configure_initial_mode': 0xf4c7d6,
    'commit_initial_mode': 0xf4c824,
    'resolution_result': 0x645e90,
    'original_configure': 0xf4c208,
    'original_restore': 0xf4c1ce,
    'apply_cursor': 0xf4c5d4,
}


def patch_game(stock, work):
    assert sha256(stock).hexdigest() == BASE_HASH
    assert read_bytes(stock, NATIVE['original_configure'], 6).hex() == '5589e5575653'
    assert read_bytes(stock, NATIVE['store_client_size'], 2).hex() == '8918'
    image = bytearray(stock)
    cfile, asfile, elf, raw, layout = [work / name for name in ('fit.o', 'hooks.o', 'fit.elf', 'fit.bin', 'fit.ld')]
    run(['gcc', '-m32', '-Os', '-std=c11', '-ffreestanding', '-fno-pic', '-fno-pie',
         '-fno-stack-protector', '-fno-asynchronous-unwind-tables', '-fno-unwind-tables',
         '-fno-ident', '-msse2', '-mfpmath=sse', '-mpreferred-stack-boundary=2',
         '-mincoming-stack-boundary=2', '-Wall', '-Wextra', '-Werror',
         '-c', HERE / 'window_fit.c', '-o', cfile], check=True)
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

    allocate_section(image, '.wndfit', payload, 0xe0000060)
    for site, old, name in HOOKS:
        before = bytes.fromhex(old)
        apply_byte_patch(image, file_offset(image, site), before,
                         jmp_rel32(site, symbols[name], len(before)), name)
    return bytes(image), symbols
