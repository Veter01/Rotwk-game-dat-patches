from hashlib import sha256
import json
from pathlib import Path
from struct import pack, pack_into, unpack_from
import subprocess

from sage_patch.utils import allocate_section, call_rel32, file_offset, jmp_rel32

ROOT = Path(__file__).resolve().parents[2]
work = ROOT / "build" / "shared-army"
source_path = ROOT / "build" / "harvest" / "game.dat"
game = bytearray(source_path.read_bytes())
assert sha256(game).hexdigest() == "46abb4a13baefa097a00f18c27d230e827a256712904b8b42ae5d92070c9a7b2"

symbols = {
    "player_relationship": 0x6ADBEB,
    "object_owner": 0x68B678,
    "nth_player": 0x6A844E,
    "donation_continue": 0x77CFB5,
    "donation_done": 0x77CFE6,
    "reset_original": 0x808A43,
    "original_status_hook": 0xEDB01C,
    "apt_scope": 0x8155D9,
    "apt_row_name": 0x815563,
    "format_ansi": 0x437A90,
    "free_ansi": 0x435D50,
    "apt_invoke": 0x62282A,
    "append_int": 0x7111E5,
    "power_continue": 0x77A4B3,
    "power_use_selection": 0x77A4D6,
    "attack_move_resume": 0x69626B,
    "ai_state": 0x660AC1,
    "ui_get_player": 0x6A8839,
    "check_upgrade_cost": 0x66F492,
    "construction_continue": 0x77B06C,
    "voice_event_preflight": 0x8E00C2,
    "audio_owner_index": 0x6DB566,
    "edge_scroll_continue": 0x83AF6B,
    "edge_scroll_skip": 0x83AFD1,
    "edge_scroll_update": 0x83B51B,
    "edge_scroll_stop": 0x83AA62,
    "edge_scroll_idle": 0x83B92C,
    "stock_rule_name": 0xF4E1FF,
}
labels = {}

def build_module(base):
    obj = work / "shared_army.o"
    elf = work / "shared_army.elf"
    binary = work / "shared_army.bin"
    subprocess.run(["as", "--32", "-o", str(obj), str(Path(__file__).with_name("shared_army.s"))], check=True)
    subprocess.run(["ld", "-m", "elf_i386", f"-Ttext={base:#x}", "-e", "local_control",
                    *(f"--defsym={k}={v:#x}" for k, v in symbols.items()),
                    "-o", str(elf), str(obj)], check=True)
    subprocess.run(["objcopy", "-O", "binary", "-j", ".text", str(elf), str(binary)], check=True)
    for line in subprocess.check_output(["nm", "-n", str(elf)], text=True).splitlines():
        address, symbol_type, name = line.split()
        if symbol_type.upper() == "T":
            labels[name] = int(address, 16)
    return binary.read_bytes()

characteristics = 0xE0000060
va = allocate_section(game, ".armyshr", build_module, characteristics)
assert va == labels["grants"]

patches = (
    (0x76ED2D, "e846c9f1ff", call_rel32(0x76ED2D, labels["order_owner"])),
    (0x68B749, "a12849de00", jmp_rel32(0x68B749, labels["local_control"], 5)),
    (0x77CFB0, "ff378b4d08", jmp_rel32(0x77CFB0, labels["on_donation"], 5)),
    (0x77A4A8, "395d087429", jmp_rel32(0x77A4A8, labels["explicit_power"], 5)),
    (0x915E00, "e917525c00", jmp_rel32(0x915E00, labels["on_status_row"], 5)),
    (0xC4F12C, "438a8000", labels["on_reset"].to_bytes(4, "little")),
    (0x696266, "b8c28ab800", jmp_rel32(0x696266, labels["on_attack_move"], 5)),
    # EVA feedback and the private targeting decal.
    (0x8E0055, "e81eb6daff8bc8e851a7dcff",
     call_rel32(0x8E0055, labels["local_control"]) + b"\x90" * 7),
    (0x6A0837, "e83caefeff", call_rel32(0x6A0837, labels["authorized_ui_owner"])),
    # Builder sidebar shows the selected constructor's commands.
    (0x92F2C8, "e86c95d7ff", call_rel32(0x92F2C8, labels["builder_panel_player"])),
    (0x77B064, "8b4704b900400000", jmp_rel32(0x77B064, labels["authorize_construction"], 8)),
    (0x9409B8, "e8bbacd4ff", call_rel32(0x9409B8, labels["authorized_ui_owner"])),
    (0x77B1C1, "e8b204f1ff", call_rel32(0x77B1C1, labels["upgrade_order_owner"])),
    # Native mobile object upgrade paths (including Angmar's summon purchase).
    (0x940DB7, "e8bca8d4ff", call_rel32(0x940DB7, labels["authorized_ui_owner"])),
    (0x940DFB, "e878a8d4ff", call_rel32(0x940DFB, labels["authorized_ui_owner"])),
    (0x940E86, "e8eda7d4ff", call_rel32(0x940E86, labels["authorized_ui_owner"])),
    (0x77A858, "e81b0ef1ff", call_rel32(0x77A858, labels["upgrade_order_owner"])),
    (0x940E45, "e848e6d2ff", call_rel32(0x940E45, labels["upgrade_affordability"])),
    (0x94310F, "e87ec3d2ff", call_rel32(0x94310F, labels["upgrade_affordability"])),
    # The preview uses the local player. The actual order uses its sender.
    (0x8332C0, "e8b383e5ff3b4508752e",
     call_rel32(0x8332C0, labels["formation_preview_access"]) + bytes.fromhex("84c090742e")),
    (0x83323E, "e83584e5ff3b450c751f",
     call_rel32(0x83323E, labels["formation_order_access"]) + bytes.fromhex("84c090741f")),
    # Positional order and selection voices use the audio visibility check.
    (0x8E00BC, "8b0dfc42de00", jmp_rel32(0x8E00BC, labels["mark_voice_feedback"], 6)),
    (0x45341B, "e846812800", call_rel32(0x45341B, labels["voice_listener_index"])),
    (0x83AF66, "38592c7566", jmp_rel32(0x83AF66, labels["borderless_edge_scroll"], 5)),
    (0x83B515, "ff152009bd00", jmp_rel32(0x83B515, labels["edge_scroll_tick"], 6)),
    # Normalize the Random Teams checkbox after reading new-lobby preferences.
    (0x85085F, "59595f5ec20400", jmp_rel32(0x85085F, labels["new_lobby_rule_defaults"], 7)),
    # Insert Shared Army Control before the existing Clan Game entry.
    (0x960A40, "b8dce2f400", b"\xb8" + labels["rts_checkboxes"].to_bytes(4, "little")),
    (0x960A70, "6a04", b"\x6a\x05"),
    (0x960B14, "e9e6d65e00", jmp_rel32(0x960B14, labels["share_rule_label"], 5)),
    (0x897B45, "e871e66a00", call_rel32(0x897B45, labels["set_weather_effect_color"])),
    (0x71A0CF, "e850ffffff", call_rel32(0x71A0CF, labels["expire_weather_effect_color"])),
    (0x492F80, "2d00000001", call_rel32(0x492F80, labels["tint_weather_vertices"])),
    (0x493A3C, "2d00000001", call_rel32(0x493A3C, labels["tint_weather_vertices"])),
    (0x5F448D, "8b8994000000", jmp_rel32(0x5F448D, labels["tint_weather_particle"], 6)),
    (0x600A0E, "b8708dbf00", b"\xb8" + pack("<I", labels["weather_field_table"])),
    (0x6012BE, "68708dbf00", b"\x68" + pack("<I", labels["weather_field_table"])),
    (0x6010C1, "885e54c746641e000000", jmp_rel32(0x6010C1, labels["initialize_weather_settings"], 10)),
    (0x600E1B, "8a4554884354", bytes.fromhex("8b4554894354")),
)
source_copy = source_path.read_bytes()
state_offset = file_offset(game, symbols["ai_state"])
assert game[state_offset:state_offset+8] == bytes.fromhex("8b41308b400485c0")
for address, original, patch in patches:
    expected = bytes.fromhex(original)
    offset = file_offset(game, address)
    assert source_copy[offset:offset+len(expected)] == expected
    assert game[offset:offset+len(expected)] == expected
    assert len(patch) == len(expected)
    game[offset:offset+len(patch)] = patch

stock_weather_fields = file_offset(game, 0xBF8D70)
weather_fields = file_offset(game, labels["weather_field_table"])
assert game[stock_weather_fields + 0x1f0:stock_weather_fields + 0x200] == bytes(16)
game[weather_fields:weather_fields + 0x1f0] = game[stock_weather_fields:stock_weather_fields + 0x1f0]
pack_into("<IIII", game, weather_fields + 0x1f0, labels["weather_field_name"],
          labels["parse_map_weather_tint"], 0, 0x55)
assert game[weather_fields + 0x200:weather_fields + 0x210] == bytes(16)

(work / "game.dat").write_bytes(game)
(work / "labels.json").write_text(json.dumps({**symbols, **labels}, indent=2))
print(f"Patched {len(patches)} verified hooks, section {va:#x}, {len(game):,} bytes")
