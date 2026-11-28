from pathlib import Path
import json
from struct import pack, unpack_from
import unicorn as u
from unicorn.x86_const import *

ROOT = Path(__file__).resolve().parents[2]
work = ROOT / "build" / "shared-army"
labels = json.loads((work / "labels.json").read_text())
bin_data = (work / "game.dat").read_bytes()
pe, = unpack_from("<I", bin_data, 0x3c)
count, = unpack_from("<H", bin_data, pe + 6)
opt_size, = unpack_from("<H", bin_data, pe + 20)
base, = unpack_from("<I", bin_data, pe + 24 + 28)
size_image, = unpack_from("<I", bin_data, pe + 24 + 56)

cpu = u.Uc(u.UC_ARCH_X86, u.UC_MODE_32)
cpu.mem_map(base, size_image)
table = pe + 24 + opt_size
for section in range(count):
    _, rva, size, offset = unpack_from("<4I", bin_data, table + section * 40 + 8)
    if size and offset:
        cpu.mem_write(base + rva, bin_data[offset:offset+size])

cpu.mem_map(0x2000000, 0x20000)
arena = 0x2000000
stack = arena + 0x1f000
exit_address = arena + 0x100
roster, message, template, obj, team_instance, node = (
    arena + n for n in (0x1000, 0x2000, 0x3000, 0x4000, 0x5000, 0x5100)
)
player = {n: arena + 0x6000 + n * 0x1000 for n in (1, 2, 3, 10)}
team = {n: arena + 0xc000 + n * 0x100 for n in player}
allies = {(1, 2), (2, 1), (1, 10), (10, 1), (2, 10), (10, 2)}

def put(addr, *words):
    cpu.mem_write(addr, pack("<" + "I" * len(words), *words))

def get(addr):
    return int.from_bytes(cpu.mem_read(addr, 4), "little")

def text(addr):
    return bytes(cpu.mem_read(addr, 96)).split(b"\0", 1)[0].decode("ascii")

put(0xDE4928, roster)
for index, address in player.items():
    put(roster + 0x18 + index * 4, address)
    put(address + 0x54, index)
    put(address + 0x30c, team[index])
put(obj + 4, template)
put(obj + 0x260, 1)
put(obj + 0x31c, team_instance)
put(team_instance + 0x30, node)
put(node + 8, player[1])
put(roster + 0x10, player[1])
game_info = arena + 0x1d000
put(0xDE412C, arena + 0x13000)
put(0xDE8930, game_info)
put(arena + 0x13000 + 0x110, 2)
put(game_info + 0x5c, 0xffffffff)
put(game_info + 0x80, 1)
recorded = []
return_value = 0
last_stop = ""
invalid_objects = False

def hook_func(pc, fn):
    def on_call(machine, address, size, user_data):
        fn()
    cpu.hook_add(u.UC_HOOK_CODE, on_call, begin=pc, end=pc)

def stack_arguments(count):
    esp = cpu.reg_read(UC_X86_REG_ESP)
    return [get(esp+4+i*4) for i in range(count)]

def substitute(result, num_args):
    esp = cpu.reg_read(UC_X86_REG_ESP)
    cpu.reg_write(UC_X86_REG_EAX, result)
    cpu.reg_write(UC_X86_REG_EIP, get(esp))
    cpu.reg_write(UC_X86_REG_ESP, esp + 4 + num_args * 4)

def relationship():
    owner = get(cpu.reg_read(UC_X86_REG_ECX)+0x54)
    target_team, = stack_arguments(1)
    target = next(n for n, pointer in team.items() if pointer == target_team)
    substitute(2 if (owner, target) in allies or owner == target else 0, 1)

hook_func(labels["player_relationship"], relationship)

def stop_at(label):
    global last_stop
    last_stop = label
    cpu.emu_stop()

for name in ("donation_done", "power_continue", "power_use_selection", "reset_original", "original_status_hook"):
    hook_func(labels[name], lambda name=name: stop_at(name))

def donation_original():
    # The original call frame has sender/target/amount on the native stack.
    assert stack_arguments(3) == [1, 2, 73]
    stop_at("normal_donation")
hook_func(0x6264e1, donation_original)

def run(address, args=(), **regs):
    global last_stop
    last_stop = ""
    for name in ("EAX","EBX","ECX","EDX","ESI","EDI","EBP"):
        cpu.reg_write(globals()["UC_X86_REG_"+name], regs.get(name, 0))
    cpu.reg_write(UC_X86_REG_EFLAGS, 2)
    cpu.reg_write(UC_X86_REG_ESP, stack)
    put(stack, exit_address, *args)
    cpu.emu_start(address, exit_address, count=2000)
    assert last_stop or cpu.reg_read(UC_X86_REG_EIP) == exit_address
    return cpu.reg_read(UC_X86_REG_EAX)

def grant(owner, recipient):
    return bool(get(labels["grants"]+4*owner) & (1<<recipient))

tag = 0x53480000
frame_ptr = stack + 0x200
msg_args = message + 0x84

def receive(sender, recipient, enable=True, *, claimed=None, amount=0, tagged=True, kind=0):
    put(message + 0x14, sender, 3, msg_args)
    payload = (tag | (int(enable)<<8) | recipient) if tagged else recipient
    for i, value in enumerate((sender if claimed is None else claimed, payload, amount)):
        off = msg_args + i*32
        put(off+4, 0 if i == 2 else off+32, value)
        put(off+0x18, kind if i == 1 else 0)
    put(frame_ptr-0x14, player.get(sender, 0))
    run(0x77CF91, EBP=frame_ptr, ESI=message)
    assert last_stop == ("donation_done" if tagged else "normal_donation")

def local(unit, viewer):
    put(roster+0x10, player[viewer])
    return run(0x68B749, ECX=unit)

assert local(obj, 1) == 1
assert local(obj, 2) == 0
put(game_info + 0x80, 0)
receive(1, 2)
assert not grant(1, 2)
put(game_info + 0x80, 1)
receive(1, 2)
assert grant(1, 2) and not grant(2, 1) and not grant(1, 10)
assert local(obj, 1) == local(obj, 2) == 1 and local(obj, 3) == local(obj, 10) == 0

def check_filter(issuer, allowed):
    # Execute the real AIGroup loop with a single selected object. Hook only the remove method.
    group, sentinel, entry = arena+0xf000, arena+0xf100, arena+0xf200
    put(group+4, sentinel)
    put(sentinel, entry)
    put(entry, sentinel, sentinel, obj)
    seen = []
    def remove():
        seen.append(stack_arguments(1)[0])
        substitute(1, 1)
    h = cpu.hook_add(u.UC_HOOK_CODE, lambda *_: remove(), begin=0x76ec79, end=0x76ec79)
    try:
        assert run(0x76ED16, (player[issuer],), ECX=group) & 255 == int(not allowed)
        assert seen == ([] if allowed else [obj])
    finally:
        cpu.hook_del(h)

check_filter(1, True)
check_filter(2, True)
check_filter(3, False)
receive(1, 2)  # Idempotent grant
assert grant(1, 2)
put(template+0x108, 0x80)  # Structures remain owner-only
assert local(obj, 2) == 0 and local(obj, 1) == 1
check_filter(2, False)
put(template+0x108, 0)

def power(issuer, allowed):
    put(frame_ptr+8, obj)
    put(frame_ptr-0x14, player[issuer])
    run(0x77A4A8, EBP=frame_ptr)
    assert last_stop == ("power_continue" if allowed else "donation_done")

power(2, True)
receive(1, 2, enable=False)
assert not grant(1, 2) and local(obj, 2) == 0
check_filter(2, False)
power(2, False)
power(1, True)
receive(2, 10, claimed=1)
assert not grant(2, 10) and not grant(1, 10)
receive(1, 3)
receive(1, 1)
receive(1, 250)
receive(1, 2, amount=5)
receive(1, 2, kind=4)
assert not any(grant(1, i) for i in (1, 2, 3, 10))
receive(1, 2, tagged=False, amount=73)
receive(1, 10)
assert grant(1, 10) and local(obj, 10) == 1
allies.remove((10, 1))
assert local(obj, 10) == 0
allies.add((10, 1))
cpu.mem_write(player[10]+0x754, b"\x01")
assert local(obj, 10) == 0
cpu.mem_write(player[10]+0x754, b"\x00")
run(get(0xC4F12C), ECX=arena + 0x1800)
assert last_stop == "reset_original"
assert not any(cpu.mem_read(labels["grants"], labels["state_end"] - labels["grants"]))

# Exercise the compiled APT dispatch boundary, message writer, and visual sync.
apt, status, arg, stream = (arena+n for n in (0xd000, 0xe000, 0xe800, 0xf000))
put(roster + 0x10, player[1])
put(status+0x6c, 2)
put(status+0x74, player[1])
put(status+0x80, player[2])
put(0xDE3F0C, apt)
put(0xDE6398, stream)
put(stream, stream + 0x100)
put(stream + 0x148, arena + 0x200)
string_obj = arena + 0x12000

def append_message():
    assert stack_arguments(1) == [0x466]
    recorded.append([])
    substitute(message, 1)

def append_int():
    recorded[-1] += stack_arguments(1)
    substitute(0, 1)

def format_ansi():
    out, fmt, row = stack_arguments(3)
    assert text(fmt) == "%s.ShareArmy" and text(row) == "RowPath"
    put(out, string_obj)
    cpu.mem_write(string_obj+8, b"RowPath.ShareArmy\x00")
    substitute(0, 0)

def apt_invoke():
    movie_id, path, method, argc, state, *_ = stack_arguments(9)
    assert movie_id == 2 and text(path) == "RowPath.ShareArmy" and text(method) == "SetShareState"
    assert argc == 1
    visual.append(text(state))
    substitute(0, 9)

visual = []
hook_func(arena + 0x200, append_message)
hook_func(labels["append_int"], append_int)
hook_func(labels["apt_scope"], lambda: substitute(2, 0))
hook_func(labels["apt_row_name"], lambda: substitute(stack_arguments(1)[0], 0))
hook_func(labels["format_ansi"], format_ansi)
hook_func(labels["free_ansi"], lambda: substitute(0, 0))
hook_func(labels["apt_invoke"], apt_invoke)

def ui(command, row):
    cpu.mem_write(arg, f"{command}={row}&name=RowPath".encode()+b"\x00")
    run(0x915e00, (arg,), ECX=status)
    if command[:2] == "sc":
        assert cpu.reg_read(UC_X86_REG_ESP) == stack+8

ui("scq", 0)
ui("scg", 0)
ui("scr", 0)
ui("scq", 1)
assert visual == ["_hidden", "_hidden", "_hidden", "_audible"] and not recorded
put(game_info+0x80, 0)
ui("scq", 1)
ui("scg", 1)
assert visual[-2:] == ["_hidden", "_hidden"] and not recorded
put(game_info+0x80, 1)
ui("scg", 1)
assert recorded == [[1, tag|0x100|2, 0]] and not grant(1, 2)
receive(1, 2)
ui("scq", 1)
assert visual[-1] == "_muted"
ui("scr", 1)
assert recorded == [[1, tag|0x100|2, 0], [1, tag|2, 0]]
receive(1, 2, enable=False)
ui("scq", 1)
assert visual[-1] == "_audible"
ui("cmt", 1)
assert last_stop == "original_status_hook"

# An allied AI's checkbox uses the same synchronized grant and is clickable.
put(player[2]+0x5c, 1)
ui("scq", 1)
assert visual[-1] == "_audible"
ui("scg", 1)
assert recorded[-1] == [1, tag|0x100|2, 0] and not grant(1, 2)
receive(1, 2)
assert grant(1, 2)
ui("scq", 1)
assert visual[-1] == "_muted"

# Drive the actual attack-move hook, object ownership, and idle-state reader.
# The fixture observes orders at the original method's continuation.
logic, vanguard, vanguard_team, vanguard_node, vanguard_ai, support_ai, ai_machine, ai_state, goal = (
    arena+n for n in (0x13000, 0x14000, 0x15000, 0x15100, 0x16000,
                      0x17000, 0x17500, 0x17600, 0x18000)
)
put(0xDE412C, logic)
put(logic+0x40, 100)
put(logic+0xac, vanguard)
put(vanguard+0x8c, obj)
put(vanguard+0x31c, vanguard_team)
put(vanguard_team+0x30, vanguard_node)
put(vanguard_node+8, player[2])
put(vanguard_ai+8, vanguard)
put(vanguard+0x260, vanguard_ai)
put(support_ai+8, obj)
put(obj+0x260, support_ai)
put(support_ai+0x30, ai_machine)
put(ai_machine+4, ai_state)
put(ai_state+4, 0)
put(template+0x108, 0x0a)
cpu.mem_write(vanguard+0x38, pack("<3f", 100, 100, 0))
cpu.mem_write(obj+0x38, pack("<3f", 200, 200, 0))
cpu.mem_write(goal, pack("<3f", 503, 602, 0))

issued = []

def original_attack_move():
    coord, shots, source = stack_arguments(3)
    assert cpu.reg_read(UC_X86_REG_EAX) == 0xB88AC2
    issued.append((cpu.reg_read(UC_X86_REG_ECX), unpack_from("<3f", cpu.mem_read(coord, 12)), shots, source))
    substitute(0, 3)

hook_func(labels["attack_move_resume"], original_attack_move)

def attack(frame, source=0, who=vanguard_ai):
    put(logic+0x40, frame)
    issued.clear()
    run(0x696266, (goal, 22, source), ECX=who+0x20)
    assert cpu.reg_read(UC_X86_REG_ESP) == stack+16
    assert issued[-1] == (who+0x20, (503, 602, 0), 22, source)
    return issued[:-1]

assert attack(100) == [(support_ai+0x20, (503, 602, 0), 0x7FFFFFFF, 0)]
assert attack(101) == []
assert attack(160, who=support_ai) == []
put(ai_state+4, 4)
assert attack(160) == []
put(ai_state+4, 0)
cpu.mem_write(obj+0x38, pack("<3f", 2000, 2000, 0))
assert attack(220) == []
cpu.mem_write(obj+0x38, pack("<3f", 200, 200, 0))
put(template+0x108, 0x8a)
assert attack(280) == []
put(template+0x108, 0x0a)
assert attack(340, source=2) == []
assert attack(340) == [(support_ai+0x20, (503, 602, 0), 0x7FFFFFFF, 0)]
ui("scr", 1)
assert recorded[-1] == [1, tag|2, 0]
receive(1, 2, enable=False)
assert not grant(1, 2)
assert local(obj, 1) == 1 and attack(500) == []
ui("scq", 1)
assert visual[-1] == "_audible"

# An enemy AI stays unavailable even if a request bypasses the grey box.
put(status+0x80, player[3])
put(player[3]+0x5c, 1)
old_command_count = len(recorded)
ui("scq", 1)
ui("scg", 1)
receive(1, 3)
assert visual[-2:] == ["_disabled", "_disabled"] and len(recorded) == old_command_count
assert not grant(1, 3)
receive(1, 2)
receive(10, 2)
assert get(labels["ai_grantors"] + 2*4) == (1 << 1) | (1 << 10)
receive(1, 2, enable=False)
assert not grant(1, 2) and grant(10, 2)
assert get(labels["ai_recipients"]) == 1 << 2 and attack(540) == []
run(get(0xC4F12C), ECX=arena+0x1800)
assert last_stop == "reset_original"
assert not any(cpu.mem_read(labels["grants"], labels["state_end"] - labels["grants"]))
print("Verified clickable allied AI, human grants, enemy exclusion, AI support orders, user ownership, revoke, and reset.")

# Exercise the exact client gates in the final binary. Stop where the original
# render/command paths diverge, before they need a live window or audio device.
for address, marker in {
    0x8E0065: "play_voice",
    0x8E0067: "skip_voice",
    0x6A083C: "radius_owner",
    0x732E46: "draw_radius",
    0x732EF5: "hide_radius",
    0x92F2D1: "show_builder",
    0x92F302: "hide_builder",
    0x940DC4: "send_upgrade",
    0x941ABB: "ignore_upgrade",
    0x77A866: "cancel_upgrade",
    0x77B1CF: "cancel_construction",
    0x77B06C: "place_construction",
}.items():
    hook_func(address, lambda marker=marker: stop_at(marker))

observer_view = 0
hook_func(labels["ui_get_player"], lambda: substitute(observer_view or get(roster+0x10), 0))
affordability = []

def engine_upgrade_cost():
    payer, upgrade, unit, warn = stack_arguments(4)
    affordability.append((payer, upgrade, unit, warn))
    assert cpu.reg_read(UC_X86_REG_ECX) == 0x61234
    substitute(int(get(payer+0x94) >= 300), 4)

hook_func(labels["check_upgrade_cost"], engine_upgrade_cost)
put(player[1]+0x94, 750)
put(player[2]+0x94, 10)
put(player[2]+0x5c, 0)
put(template+0x108, 0x4008)

def check_client(viewer, allowed, payer):
    put(roster+0x10, player[viewer])
    run(0x8E0055, ECX=obj)
    assert last_stop == ("play_voice" if allowed else "skip_voice")
    radius_player = run(0x6A0837, ECX=obj)
    run(0x732E32, EDI=radius_player)
    assert last_stop == ("draw_radius" if allowed else "hide_radius")
    run(0x92F2B5, EDI=obj)
    assert last_stop == ("show_builder" if allowed else "hide_builder")
    assert cpu.reg_read(UC_X86_REG_EBX) == player[1]
    run(0x940DB7, ECX=obj, EDI=player[viewer])
    assert last_stop == ("send_upgrade" if allowed else "ignore_upgrade")
    assert run(labels["upgrade_affordability"], (player[viewer], template, obj, 1),
               ECX=0x61234) == int(get(player[payer]+0x94) >= 300)
    assert affordability[-1] == (player[payer], template, obj, 1)
    assert cpu.reg_read(UC_X86_REG_ESP) == stack+20

def check_simulation(issuer, allowed):
    put(frame_ptr-0x14, player[issuer])
    run(0x77B064, EBP=frame_ptr, EDI=obj, EDX=player[1])
    assert last_stop == ("place_construction" if allowed else "donation_done")
    assert cpu.reg_read(UC_X86_REG_EDX) == player[1]
    if allowed:
        assert cpu.reg_read(UC_X86_REG_EAX) == template
        assert cpu.reg_read(UC_X86_REG_ECX) == 0x4000
    run(0x77A858, EBP=frame_ptr, ECX=obj)
    assert last_stop == ("cancel_upgrade" if allowed else "donation_done")
    run(0x77B1C1, EBP=frame_ptr, ECX=obj)
    assert last_stop == ("cancel_construction" if allowed else "donation_done")

check_client(1, True, 1)
check_client(2, False, 2)
receive(1, 2)
check_client(2, True, 1)
check_client(3, False, 3)
check_simulation(1, True)
check_simulation(2, True)
check_simulation(3, False)
put(player[1]+0x94, 10)
put(player[2]+0x94, 750)
check_client(2, True, 1)
put(template+0x108, 0x80)
check_client(2, False, 2)
put(template+0x108, 0x4008)
receive(1, 2, enable=False)
check_client(2, False, 2)
check_simulation(2, False)
observer_view = player[1]
run(0x92F2B5, EDI=obj)
assert last_stop == "show_builder"
print("Verified EVA, targeting decal, construction panel, owner-funded upgrades, build and cancel permissions.")

# Execute both formation eligibility loops. Stub the engine's object filter
# and list library individually so the test observes exactly what each admits.
formation = arena+0x19000
formation_vector, slots, formation_group, group_head, group_entry, formation_result, result_head = (
    formation+n for n in (0x100, 0x200, 0x300, 0x400, 0x500, 0x600, 0x700)
)
put(obj+0x74, 123)
put(formation_vector, slots, slots+4)
put(slots, obj)
put(formation_group, group_head)
put(group_head, group_entry)
put(group_entry, group_head, group_head, obj)
put(formation_result, result_head)
for pointer in player.values():
    put(pointer+0x750, formation_vector)

def clear_formation_result():
    assert cpu.reg_read(UC_X86_REG_ECX) == formation_result
    put(result_head, result_head)
    substitute(0, 0)

def formation_filter():
    unit, issuer = stack_arguments(2)
    assert cpu.reg_read(UC_X86_REG_ECX) == formation+0x20
    assert unit == obj
    filter_calls.append(issuer)
    substitute(int(filter_accepts), 2)

def append_formation_result(expected):
    assert cpu.reg_read(UC_X86_REG_ECX) == formation_result
    value, = stack_arguments(1)
    assert get(value) == expected
    put(result_head, group_entry)
    substitute(0, 1)

hook_func(0x6652E4, clear_formation_result)
hook_func(0x5EA918, clear_formation_result)
hook_func(0x8DB060, lambda: substitute(formation_vector, 0))
hook_func(0x7640C1, formation_filter)
hook_func(0x6A253A, lambda: append_formation_result(123))
hook_func(0x5EB775, lambda: append_formation_result(obj))
filter_calls = []
filter_accepts = True

def check_formation(issuer, admitted, runs_filter=True):
    filter_calls.clear()
    assert run(0x833282, (player[issuer], formation_result), ECX=formation) & 255 == admitted
    assert run(0x83320B, (formation_group, player[issuer], formation_result), ECX=formation) & 255 == admitted
    assert filter_calls == ([player[issuer]]*2 if runs_filter else [])

observer_view = 0
put(roster+0x10, player[3])  # Simulation must use the sender, not this client.
check_formation(1, True)
check_formation(2, False, False)
receive(1, 2)
check_formation(2, True)
check_formation(3, False, False)
filter_accepts = False
check_formation(2, False)
filter_accepts = True
put(template+0x108, 0x80)
check_formation(2, False, False)
put(template+0x108, 0x4008)
receive(1, 2, enable=False)
check_formation(2, False, False)
print("Verified both formation loops for ownership, active grants, revocation and native eligibility.")

# Follow actual feedback event submission and the native sound visibility
# decision, including stock lookups of positional sound owners.
audio, audio_vtable, voice, voice_info = (arena+n for n in (0x1a000, 0x1a200, 0x1a400, 0x1a600))
primary_voice = frame_ptr-0x2e8
secondary_voice = frame_ptr-0x370
put(0xDE42FC, audio)
put(audio, audio_vtable)
put(audio_vtable+0x7c, arena+0x300)
put(audio_vtable+0x64, arena+0x310)
put(voice+0x24, obj)

admitted_voice_events = []

def voice_preflight():
    assert stack_arguments(1) == [primary_voice]
    substitute(1, 1)

def submit_voice():
    event, = stack_arguments(1)
    assert get(event+0x34) == 123 and get(event+0x38) == 2
    admitted_voice_events.append(event)
    substitute(0, 1)

def feedback_object_lookup():
    assert stack_arguments(1) == [123]
    substitute(obj, 1)

hook_func(arena+0x300, voice_preflight)
hook_func(arena+0x310, submit_voice)
hook_func(0x8E0126, lambda: stop_at("voice_events_submitted"))
hook_func(0x449681, feedback_object_lookup)
hook_func(0x45343F, lambda: stop_at("audio_visibility_decided"))
put(voice_info+0x48, 0x20)  # PLAYER visibility without ALLIES.

def check_voice(viewer, audible):
    put(roster+0x10, player[viewer])
    admitted_voice_events.clear()
    for event in (primary_voice, secondary_voice):
        put(event+0x38, 6)
        put(event+0x6c, 0xffffffff)
    run(0x8E00BC, EBP=frame_ptr, ESI=voice)
    assert last_stop == "voice_events_submitted"
    assert admitted_voice_events == [primary_voice, secondary_voice]
    for event in admitted_voice_events:
        run(0x45341B, ECX=event, ESI=voice_info, EDI=player[viewer])
        assert last_stop == "audio_visibility_decided"
        assert cpu.reg_read(UC_X86_REG_EBX) & 0xff == audible

check_voice(1, True)
check_voice(2, False)
receive(1, 2)
check_voice(2, True)
check_voice(3, False)
put(template+0x108, 0x80)
check_voice(2, False)
put(template+0x108, 0x4008)
receive(1, 2, enable=False)
check_voice(2, False)
print("Verified positional voice events keep their source and pass PLAYER visibility for the active controller.")

# Follow the original mouse-movement path to its three-pixel edge check.
display, camera = arena+0x1b000, arena+0x1b500
hwnd = 0x1234
foreground_window = hwnd
put(0xDC3C64, hwnd)
put(0xBD0850, arena+0x320)
hook_func(arena+0x320, lambda: substitute(foreground_window, 0))
hook_func(0x83AFD1, lambda: stop_at("skip_edge_scroll"))
physical_pointer = 0, 0

def cursor_position():
    put(stack_arguments(1)[0], *[v & 0xffffffff for v in physical_pointer])
    substitute(1, 1)

def screen_to_client():
    assert stack_arguments(2)[0] == hwnd
    substitute(1, 2)

def client_rectangle():
    hwnd_arg, address = stack_arguments(2)
    assert hwnd_arg == hwnd
    put(address, 0, 0, 1920, 1080)
    substitute(1, 2)

for iat, fn, entry in ((0xBD081C, cursor_position, 0x340),
                       (0xBD0890, screen_to_client, 0x350),
                       (0xBD08B8, client_rectangle, 0x360)):
    put(iat, arena+entry)
    hook_func(arena+entry, fn)

def start_edge_scroll():
    assert stack_arguments(1) == [3]
    assert cpu.reg_read(UC_X86_REG_ECX) == camera
    stop_at("start_edge_scroll")

hook_func(0x83A9BD, start_edge_scroll)

def check_edge(mode, windowed, x, y, start, ui_blocked=False, pointer=None):
    global physical_pointer
    physical_pointer = (x, y) if pointer is None else pointer
    put(0xF4D184, mode)
    put(display+0x2c, windowed)
    put(frame_ptr-0x14, 1920)
    put(camera+0x14, x, y)
    run(0x83AF66, ECX=display, EBP=frame_ptr, ESI=camera, EDI=1080, EAX=ui_blocked)
    assert last_stop == ("start_edge_scroll" if start else "skip_edge_scroll")

for x, y in ((0, 500), (1919, 500), (960, 0), (960, 1079)):
    check_edge(1, True, x, y, True)
    check_edge(2, True, x, y, True)
check_edge(1, True, 960, 540, False)
check_edge(1, True, 0, 500, False, ui_blocked=True)
check_edge(2, True, 0, 500, False, pointer=(-1, 500))
check_edge(0, False, 0, 500, True)
foreground_window = 0x4321
check_edge(1, True, 0, 500, False)
def stop_edge_scroll():
    assert cpu.reg_read(UC_X86_REG_ECX) == camera
    substitute(0, 0)
hook_func(0x83aa62, stop_edge_scroll)
hook_func(0x83b92c, lambda: stop_at("edge_lost_focus"))
hook_func(0x83b51b, lambda: stop_at("edge_timer"))
put(0xBD0920, arena+0x390)
hook_func(arena+0x390, lambda: substitute(1000, 0))

put(0xF4D184, 2)
foreground_window = hwnd
physical_pointer = 0, 500
run(0x83b515, EBP=frame_ptr, ESI=camera)
assert last_stop == "edge_timer"
physical_pointer = -1, 500
run(0x83b515, EBP=frame_ptr, ESI=camera)
assert last_stop == "edge_lost_focus"
assert get(frame_ptr-0x0c) == 0
foreground_window = 0x4321
physical_pointer = 0, 500
run(0x83b515, EBP=frame_ptr, ESI=camera)
assert last_stop == "edge_lost_focus"
print("Verified all four edges in windowed and borderless modes, UI guards and focus loss.")

# Both multiplayer host paths use this reader before copying the rules into
# the lobby. Exercise its native defaults and saved-settings branches.
preferences, rules_lobby, rules_controller, preferences_tree, rule_record, saved_rule_text = (
    arena+n for n in (0x1c000, 0x1c400, 0x1c800, 0x1cc00, 0x1cc40, 0x1cd00)
)
put(preferences+4, preferences_tree)
put(rule_record+0x14, saved_rule_text)
put(0xBD0628, arena+0x330)
put(0xDE4364, display)
has_saved_rules = False

def find_rules_key():
    assert cpu.reg_read(UC_X86_REG_ECX) == preferences
    assert text(stack_arguments(1)[0]) == "Rules"
    substitute(preferences+0x18, 1)

def find_saved_rules():
    assert cpu.reg_read(UC_X86_REG_ECX) == preferences+4
    assert stack_arguments(1) == [preferences+0x18]
    substitute(rule_record if has_saved_rules else preferences_tree, 1)

def atoi():
    words = text(stack_arguments(1)[0]).split()
    substitute(int(words[0]) & 0xffffffff if words else 0, 0)

def clear_rule_slots():
    dest, fill, size = stack_arguments(3)
    assert dest in (rules_lobby+0x60, arena+0x1d080) and size == 40
    cpu.mem_write(dest, bytes([fill])*size)
    substitute(dest, 0)

hook_func(0x8501D3, find_rules_key)
hook_func(0x456726, find_saved_rules)
hook_func(0xA3CF28, clear_rule_slots)
hook_func(arena+0x330, atoi)

def read_new_lobby_rules(game_kind):
    put(preferences+0x14, game_kind)
    found = run(0x850815, (rules_lobby+0x60,), ECX=preferences, EDI=0x45678, ESI=0x12345)
    assert found & 0xff == has_saved_rules
    assert cpu.reg_read(UC_X86_REG_EDI) == 0x45678
    assert cpu.reg_read(UC_X86_REG_ESI) == 0x12345
    assert cpu.reg_read(UC_X86_REG_ESP) == stack+8
    return unpack_from("<10i", cpu.mem_read(rules_lobby+0x60, 40))

assert read_new_lobby_rules(0)[8] == read_new_lobby_rules(0)[9] == 0
has_saved_rules = True
saved_rules = (1, 0, 1, -1, 2, 0, -1, 0, -1, 1)
cpu.mem_write(saved_rule_text+8, b"1 0 1 -1 2 0 -1 0 -1 1\x00")
assert read_new_lobby_rules(1) == saved_rules
assert read_new_lobby_rules(0) == (*saved_rules[:8], 0, 0)
put(rules_lobby+0x64, 0)  # Normal RTS rules, without the incompatible mode flag.
assert run(0xF4E017, (rules_controller, rules_lobby)) == 0
put(rules_lobby+0x84, 1)  # Value submitted by the host after clicking the checkbox.
assert run(0xF4E017, (rules_controller, rules_lobby)) == 1
put(rules_lobby+0x84, 0)
assert run(0xF4E017, (rules_controller, rules_lobby)) == 0
print("Verified Random Teams defaults with and without saved rules, and the live opt-in.")

# Native Rules defaults and all supported match handoff routes.
defaults = arena+0x1d080
run(0x960A74, (0, defaults))
assert unpack_from("<10i", cpu.mem_read(defaults, 40)) == (1, 0, 1, 100, 1000, -1, -1, -1, 0, 0)
assert run(0x960A5D, (0,)) == 5
rs = run(0x960A2B, (0,))
assert [get(get(rs+4*i)) for i in range(5)] == [0, 2, 9, 8, 1]
put(0xDE7D6C, game_info)
put(game_info+0x5c, 0)
network, network_vt = arena+0x1d200, arena+0x1d280
put(0xDE4394, network)
put(network, network_vt)
put(network_vt+0xe0, arena+0x370)
hook_func(arena+0x370, lambda: substitute(game_info, 0))
put(0xDE412C, logic)
for match_origin in range(4):
    put(logic+0x114, match_origin)
    put(0xDE892C, game_info if match_origin == 3 else 0)
    put(game_info+0x80, 0)
    assert run(labels["army_rule_enabled"]) == 0
    put(game_info+0x80, 1)
    assert run(labels["army_rule_enabled"]) == 1
    put(game_info+0x5c, 1)
    assert run(labels["army_rule_enabled"]) == 0
    put(game_info+0x5c, 0)
network_match = arena+0x1d300
put(network_match+0x5c, 0)
put(network_match+0x80, 0)
put(logic+0x114, 1)
put(0xDE892C, network_match)
assert get(game_info+0x80) == 1
assert run(labels["army_rule_enabled"]) == 0
put(network_match+0x80, 1)
assert run(labels["army_rule_enabled"]) == 1
print("Verified rule defaults, checkbox registration, and synchronized GameInfo lookup.")

# Run the actual lobby gadget handler, host callback and copy into
# the single-player GameInfo header. The native lobby leaves game type at -1.
cpu.mem_map(0, 0x1000)
skirmish_lobby = arena+0x18100
skirmish_panel = skirmish_lobby+0xd0
rule_buttons, rule_button = arena+0x18500, arena+0x18540
game_info_holder, holder_vtable = arena+0x18600, arena+0x18640
skirmish_host, host_vtable = arena+0x18680, arena+0x186c0
put(skirmish_panel, 0xC53F30)
put(skirmish_panel+0x7c, rule_buttons, rule_buttons+40)
put(skirmish_panel+0x88, 1)
cpu.mem_write(skirmish_panel+0x8c, bytes(cpu.mem_read(defaults, 40)))
put(rule_button+0x3c, 4)
put(rule_buttons+8*4, rule_button)
put(0xDE8D78, skirmish_lobby)
put(skirmish_lobby+0x58, skirmish_host, game_info_holder)
put(game_info_holder, holder_vtable)
put(game_info_holder+8, game_info)
put(holder_vtable+4, arena+0x3a0)
put(skirmish_host, host_vtable)
put(host_vtable+4, arena+0x3b0)
hook_func(arena+0x3a0, lambda: substitute(1, 1))
hook_func(arena+0x3b0, lambda: substitute(1, 0))

def copy_skirmish_rules():
    dest, source, size = stack_arguments(3)
    assert (dest, source, size) == (game_info+0x60, skirmish_panel+0x8c, 40)
    cpu.mem_write(dest, bytes(cpu.mem_read(source, size)))
    substitute(dest, 0)

hook_func(0xA3CF22, copy_skirmish_rules)
# Everything after the native copy updates lobby labels and notifications.
hook_func(0x84226a, lambda: cpu.reg_write(UC_X86_REG_EIP, 0x8423c0))

put(logic+0x110, 2, 0)
put(game_info+0x5c, 0xffffffff)
put(0xDE892C, game_info)
put(roster+0x10, player[1])
put(status+0x80, player[2])
receive(1, 2, enable=False)
assert not grant(1, 2)
for enabled in (0, 1, 0):
    put(rule_button+0x38, enabled << 2)
    assert run(0x986776, (0x4008, rule_button, 0), ECX=skirmish_panel) & 0xff == 1
    assert get(game_info+0x80) == enabled
    assert get(game_info+0x5c) == 0xffffffff
    ui("scq", 0)
    ui("scq", 1)
    assert visual[-2:] == ["_hidden", "_audible" if enabled else "_hidden"]
    receive(1, 2)
    assert grant(1, 2) == bool(enabled)
    if enabled:
        receive(1, 2, enable=False)

# A strategic or uninitialized match can use the same numerical slot.
put(game_info+0x80, 1)
put(logic+0x110, 6)
assert run(labels["army_rule_enabled"]) == 0
put(logic+0x110, 2)
put(0xDE892C, arena+0x18700)
put(arena+0x18700+0x5c, 0xffffffff)
put(arena+0x18700+0x80, 1)
assert run(labels["army_rule_enabled"]) == 0
put(0xDE892C, game_info)
put(game_info+0x5c, 1)
assert run(labels["army_rule_enabled"]) == 0
print("Verified single-player Rules checkbox drives the in-game allied row and grant with the native -1 game type.")

# Verify the actual rule-name call-site return address and GameText contract.
loc_manager, loc_vt, loc_return = arena+0x1d420, arena+0x1d480, arena+0x380
put(0xDE4B04, loc_manager)
put(loc_manager, loc_vt)
put(loc_vt+0x3c, loc_return)
def lookup_rule():
    output, key, flags = stack_arguments(3)
    assert (output, text(key), flags) == (arg, "RULE:ShareArmy", 0)
    substitute(0, 3)
hook_func(loc_return, lookup_rule)
# Start with the real CALL's arguments on the stack, then enter the patched routine.
put(stack, 0x9868c9, arg, 8)
cpu.reg_write(UC_X86_REG_ESP, stack)
cpu.emu_start(0x960b14, 0x9868c9)
assert cpu.reg_read(UC_X86_REG_EAX) == arg
print("Verified Rules UI uses GameText to resolve RULE:ShareArmy.")

# Compiled weather entry points, precalculated map colors, and stock brightness.
from math import isclose

weather = arena+0x1d520
weather_module = arena+0x1d560
particles = arena+0x1d680
fx_template = arena+0x1d900
fx_name = arena+0x1da40
fx_particle = arena+0x1da80
fx_color_pointer = arena+0x1db30
map_weather, map_override = arena+0x1db80, arena+0x1dc40
put(0xDE772C, weather)
put(0xDE3B58, map_weather)
put(map_weather+0x54, 0xffffff01)
put(map_override+0x54, 0xffffff00)
put(weather_module+0x2c, 0x82821e00)
cpu.mem_write(weather_module+0x69, b"\x01")

def finish_native_weather():
    assert cpu.reg_read(UC_X86_REG_ECX) == weather
    weather_type, _, _ = stack_arguments(3)
    put(weather+0x10, weather_type)
    substitute(0, 3)
hook_func(0x71a024, finish_native_weather)

def set_weather(weather_type):
    run(labels["set_weather_effect_color"], (weather_type, 0, 120), EBX=weather_module, ECX=weather)
    assert cpu.reg_read(UC_X86_REG_ESP) == stack+16

for point in (0x492F85, 0x493A41):
    hook_func(point, lambda: stop_at("weather_vertex_continuation"))

def vertex_color(color, location):
    value = run(location, EAX=color)
    assert last_stop == "weather_vertex_continuation"
    return value

def stub_particle_color():
    assert cpu.reg_read(UC_X86_REG_ECX) == fx_color_pointer
    substitute(fx_color_pointer, 0)
hook_func(0x5f4493, stub_particle_color)
put(fx_particle+0x3c, particles)
put(fx_particle+0x94, fx_color_pointer)
put(particles+0x198, fx_template)
put(fx_template+0x9c, fx_name)
cpu.mem_write(fx_color_pointer, pack("<3f", 0.6, 0.5, 0.2))

def check_particle(name, tinted):
    cpu.mem_write(fx_name+8, name.encode() + b"\x00")
    out = run(0x5F448D, ECX=fx_particle)
    assert (out != fx_color_pointer) == tinted
    if tinted:
        actual = unpack_from("<3f", cpu.mem_read(out, 12))
        expect = [base * tint/255 for base, tint in zip((0.6, 0.5, 0.2), (30, 130, 130))]
        assert all(isclose(a, b, rel_tol=1e-6) for a, b in zip(actual, expect))
        assert unpack_from("<3f", cpu.mem_read(fx_color_pointer, 12))[1] == 0.5

for mode in (1, 2, 3, 4):
    set_weather(mode)
    assert get(0xf4629c) == (1 << (23+mode)) | 0x82821e
    for where in (0x492f80, 0x493a3c):
        assert vertex_color(0x00808080, where) == (0xff0f4141 if mode != 4 else 0xff808080)
    check_particle("CloudBreakRaysRohan", mode == 4)
    check_particle("GildorCloudBreakRays", mode == 4)
    check_particle("SnowFlakesRainWK", mode != 4)
    check_particle("WeatherStormRain", mode != 4)
    check_particle("UnrelatedImpact", False)

run(labels["expire_weather_effect_color"], (0, 0, 0), ECX=weather)
assert get(0xf4629c) == 0
assert vertex_color(0x00ffffff, 0x492f80) == 0xffffffff
check_particle("CloudBreakRays", False)

fields = run(0x600a0e)
name, parser, flag, offset = unpack_from("<4I", cpu.mem_read(fields+0x1f0, 16))
assert (text(name), parser, flag, offset) == ("DarkeningFactor", labels["parse_map_weather_tint"], 0, 0x55)
def parse_rgb():
    _, _, dest, _ = stack_arguments(4)
    cpu.mem_write(dest, pack("<3f", 30/255, 130/255, 130/255))
    substitute(0, 0)
hook_func(0x42ef99, parse_rgb)
run(parser, (0, 0, map_weather+offset, 0))
assert bytes(cpu.mem_read(map_weather+0x54, 4)) == b"\x01\x1e\x82\x82"
assert vertex_color(0x00ffffff, 0x493a3c) == 0xff1e8282
put(map_weather+4, map_override)
assert vertex_color(0x00ffffff, 0x493a3c) == 0xffffffff
run(parser, (0, 0, map_override+offset, 0))
assert vertex_color(0x00ffffff, 0x493a3c) == 0xff1e8282
print("Verified weather parsing, both precipitation paths, RGB modulation and Cloud Break particle scoping.")
