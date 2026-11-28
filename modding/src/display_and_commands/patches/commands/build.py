from hashlib import sha256
from pathlib import Path
from struct import unpack
from subprocess import check_output, run

from sage_patch.patches.commandbar import multi_select_group as multi
from sage_patch.patches.economy.cost_modifier_upgrade_groups import CostModifierUpgradeGroupsPatch
from sage_patch.patches.economy.player_upgrade_discount import PlayerUpgradeDiscountPatch
from sage_patch.utils import allocate_section, apply_byte_patch, file_offset, find_section, call_rel32, jmp_rel32, read_bytes

HERE = Path(__file__).resolve().parent
BASE_HASH = 'ada51c5149c40683727419f4e8a6379ac15026e31e75082babb3cb13eb90f982'

HOOKS = (
    (0x94070f, '85db7415538bce', 'group_right_click'),
    (0x9445da, 'f6431d010f84d1000000', 'seed_autocast_button'),
    (0x80814d, '8b460c8b4014', 'remember_tooltip_button'),
    (0x808390, 'ff75e48b4ddcff75e0e82a6fe6ff33ff3bc70f8e02030000', 'tooltip_price'),
    (0x8083c7, 'e9de020000', 'tooltip_suffix'),
    (0x66f2ff, 'e9f8000000', 'combine_template_discounts'),
    (0x940d49, '8b7e2485ff', 'remember_upgrade_button'),
)
CALLS = (
    (0x940e45, 'e870056100', 'group_upgrade_gate'),
    (0x9405b3, 'e87b210000', 'group_availability'),
    (0x9449d6, 'e858ddffff', 'group_availability'),
)
NATIVE = {
    'finish_click': 0x941abb,
    'refuse_click': 0x940642,
    'no_representative': 0x940728,
    'native_click': 0x940716,
    'seed_button': 0x9445e4,
    'skip_button': 0x9446b5,
    'tooltip_command_resume': 0x808153,
    'price_prefix': 0x8083a8,
    'no_price': 0x8086aa,
    'template_price_done': 0x66f3fc,
    'copy_string': 0x435f30,
    'native_building_upgrade_role': 0xf360e9,
    'upgrade_click_resume': 0x940d4e,
}


def branch_target(image, va, opcode):
    op, disp = unpack('<Bi', read_bytes(image, va, 5))
    assert op == opcode, (va, op)
    return va + 5 + disp


def patch_upgrades(image):
    # The base already has the building-upgrade availability wrapper. Check both
    # ends of its native fallback before allowing pySAGE to use the same entry.
    assert read_bytes(image, 0x942733, 5).hex() == 'e9823e5f00'
    assert read_bytes(image, 0xf367ef, 5).hex() == 'b81ec4ba00'
    assert branch_target(image, 0xf367f4, 0xe9) == 0x942738
    assert read_bytes(image, 0x942738, 5).hex() == 'e8b3a70f00'
    multi.ANCHORS[0x942733] = bytes.fromhex('e9823e5f00')

    patches = [PlayerUpgradeDiscountPatch(), CostModifierUpgradeGroupsPatch(), multi.MultiSelectGroupPatch()]
    for patch in patches:
        patch.apply(image)
    for patch in patches:
        assert not patch.verify(image), (patch.name, patch.verify(image))

    group_va = find_section(image, multi.SECTION_NAME)[0]
    refs = multi.MultiSelectGroupPatch._resolve(image)
    rows_before_new_field = len(multi.read_field_table(image, refs)) - 1
    layout = multi._layout(group_va, multi.DEFAULT_KEYWORD, rows_before_new_field)
    return {
        'discount_query': branch_target(image, 0x66f389, 0xe8),
        'upgrade_button_usable': multi.entry_points(layout.code_va, layout.flags_va)['usable'],
    }


def patch_game(engine, work):
    assert sha256(engine).hexdigest() == BASE_HASH
    image = bytearray(engine)
    functions = patch_upgrades(image)
    native, hooks, elf, raw, layout = [work / name for name in ('commands.o', 'hooks.o', 'patch.elf', 'patch.bin', 'patch.ld')]
    run(['gcc', '-m32', '-Os', '-std=c11', '-ffreestanding', '-fno-pic', '-fno-pie',
         '-fno-stack-protector', '-fno-asynchronous-unwind-tables', '-fno-unwind-tables',
         '-fno-ident', '-msse2', '-mfpmath=sse', '-mpreferred-stack-boundary=2',
         '-mincoming-stack-boundary=2', '-Wall', '-Wextra', '-Werror',
         '-c', HERE / 'commands.c', '-o', native], check=True)
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
        definitions = {'PATCH_ADDRESS': address, **NATIVE, **functions}
        run(['ld', '-m', 'elf_i386', '-z', 'noexecstack', '--no-warn-rwx-segments', '-T', layout,
             *[f'--defsym={name}={va:#x}' for name, va in definitions.items()],
             '-o', elf, native, hooks], check=True)
        for line in check_output(['nm', '--defined-only', elf], text=True).splitlines():
            value, _, name = line.split()
            symbols[name] = int(value, 16)
        run(['objcopy', '-O', 'binary', '-j', '.patch', elf, raw], check=True)
        return raw.read_bytes()

    allocate_section(image, '.groupui', payload, 0x60000060)
    for site, old, symbol in HOOKS:
        before = bytes.fromhex(old)
        apply_byte_patch(image, file_offset(image, site), before,
                         jmp_rel32(site, symbols[symbol], len(before)), symbol)
    for site, old, symbol in CALLS:
        apply_byte_patch(image, file_offset(image, site), bytes.fromhex(old),
                         call_rel32(site, symbols[symbol]), symbol)
    return bytes(image), symbols
