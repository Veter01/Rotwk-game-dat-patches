from hashlib import sha256
from pathlib import Path
from subprocess import check_output, run

from patches.labels import build as labels
from sage_patch.utils import allocate_section, apply_byte_patch, call_rel32, file_offset

HERE = Path(__file__).resolve().parent
BASE_HASH = 'fccc1895029e8f21cf6ff5cc488787ee17047c3ef271f07c14722e599a1b3172'
GAME = 'game.dat'
PLAYERS = 'apt/playertribute.big'
HOOKS = (
    (0xf4c7f3, 'e810faffff', 'configure_startup_window'),
    (0xf4ca56, 'e8adf7ffff', 'configure_live_window'),
)
# The source gradient is MenuExport's CH_TabGradient: sprite 258 uses shape 257,
# spanning exactly 256 APT units. The prior layout enlarged the data tab by 26.
GRADIENT_WIDTH = 256.0


def patch_players(blob):
    movie = labels.edit_movie(blob, 'PlayerTribute')
    imports = [node for node in movie.xml.iter() if node.get('name') == 'CH_TabGradient']
    assert len(imports) == 1 and imports[0].attrib == {
        'name': 'CH_TabGradient', 'movie': 'MenuExport', 'character': '64'
    }
    movie.place(69, 0, 4, 64, rotm00=labels.shift(labels.EXTRA_WIDTH / GRADIENT_WIDTH))
    return labels.patch_big(blob, {'PlayerTribute.apt': movie.finish()})


def patch_game(stock, work):
    assert sha256(stock).hexdigest() == BASE_HASH
    image = bytearray(stock)
    cfile, asfile, elf, raw, layout = [work / name for name in
                                       ('fullscreen.o', 'hooks.o', 'fullscreen.elf',
                                        'fullscreen.bin', 'fullscreen.ld')]
    run(['gcc', '-m32', '-Os', '-std=c11', '-ffreestanding', '-fno-pic', '-fno-pie',
         '-fno-stack-protector', '-fno-asynchronous-unwind-tables', '-fno-unwind-tables',
         '-fno-ident', '-mpreferred-stack-boundary=2', '-mincoming-stack-boundary=2',
         '-Wall', '-Wextra', '-Werror', '-c', HERE / 'fullscreen.c', '-o', cfile], check=True)
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
        run(['ld', '-m', 'elf_i386', '--no-warn-rwx-segments', '-z', 'noexecstack',
             '-T', layout, f'--defsym=PATCH_ADDRESS={address:#x}',
             '--defsym=native_configure_window=0xf4c208',
             '-o', elf, cfile, asfile], check=True)
        for line in check_output(['nm', '--defined-only', elf], text=True).splitlines():
            addr, _, label = line.split()
            symbols[label] = int(addr, 16)
        run(['objcopy', '-O', 'binary', '-j', '.patch', elf, raw], check=True)
        return raw.read_bytes()

    allocate_section(image, '.fullscr', payload, 0x60000020)
    for site, old, name in HOOKS:
        apply_byte_patch(image, file_offset(image, site), bytes.fromhex(old),
                         call_rel32(site, symbols[name]), name)

    # This format check is called only when preparing an exclusive swap chain.
    # Pass bWindowed=FALSE before allowing an alpha back buffer on this display.
    apply_byte_patch(image, file_offset(image, 0x5213d9), b'\x6a\x01', b'\x6a\x00',
                     'Check the exclusive back-buffer format')
    return bytes(image), symbols
