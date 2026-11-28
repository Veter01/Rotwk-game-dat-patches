from hashlib import sha256
from struct import pack

from sage_patch.utils import apply_byte_patch, call_rel32, file_offset

BASE_HASH = 'b311c84a9a06a2874ace18798fe2ba41b011753e9048f0d4f9ef142e74226bb7'
GAME = 'game.dat'

STYLE_SITES = (0xf5806d, 0xf580bc, 0xf58391)
FIXED_FRAME = 0x10ca0000
RESIZABLE_FRAME = 0x00040000
MODE_PUMP = 0xf5b250
CLIENT_EDGES = 0xf53103
EDGE_ENTRY = 0xf5b000

ROLLBACK = (
    (0xf4c5d4, 'e923cf0000', 'a174d1f400', 'Restore the native clipping entry'),
    (0xf4c665, 'e8a7ca0000', 'e88d6c0000', 'Clip to the game client'),
    (0xf4d013, 'e856c10000', 'e88af6ffff', 'Restore the window event handler'),
)

OLD_EDGE_ENTRY = bytes.fromhex(
    '83 3d 38 95 f5 00 00 0f 85 07 01 00 00 '
    '83 3d 88 d1 f4 00 00 0f 85 fa 00 00 00'
)


def patch_game(original):
    assert sha256(original).hexdigest() == BASE_HASH
    image = bytearray(original)

    def replace(address, old, new, name):
        apply_byte_patch(image, file_offset(image, address), old, new, name)

    for address, old, new, name in ROLLBACK:
        replace(address, bytes.fromhex(old), bytes.fromhex(new), name)

    for address in STYLE_SITES:
        replace(address, pack('<I', FIXED_FRAME | RESIZABLE_FRAME), pack('<I', FIXED_FRAME),
                'Restore the fixed window frame')

    # Keep the existing match-aware mode pump and leave the GUI lifetime fixes in place.
    replace(0xf4cfd0, call_rel32(0xf4cfd0, 0xf5921b), call_rel32(0xf4cfd0, MODE_PUMP),
            'Apply pending display modes without the window-resize updater')

    # Edge detection uses the same client rectangle as cursor clipping. A stored options
    # owner is bookkeeping and must not suppress camera movement after closing the screen.
    cmp_switching_mode = bytes.fromhex('83 3d 88 d1 f4 00 00')
    jump_if_idle = b'\x0f\x84' + pack('<i', CLIENT_EDGES - (EDGE_ENTRY + 13))
    replacement = cmp_switching_mode + jump_if_idle + b'\x31\xc0\xc3'
    replace(EDGE_ENTRY, OLD_EDGE_ENTRY, replacement.ljust(len(OLD_EDGE_ENTRY), b'\x90'),
            'Use the client rectangle for camera edges')
    return bytes(image)
