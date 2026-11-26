# 08. MoneyCost for all SpecialPower command types

`MoneyCost` sets the resource cost of using a named `SpecialPower`. It applies to targetless and targeted powers, mount and dismount, spellbook casts, and remote command-center powers. An omitted or zero cost lets the power run for free. Science purchase points and unit sacrifices still follow their own rules.

## Set a price in INI

Follow the button's `SpecialPower` reference and the ability module's `SpecialPowerTemplate` reference to the named template. Add `MoneyCost` inside that template in `data/ini/specialpower.ini` or in the include that defines it.

For example, add the cost to the existing block in `data/ini/specialpower.ini` to charge 100 for each use of the shared mount and dismount command.

```ini
SpecialPower SpecialAbilityToggleMounted
    Enum = SPECIAL_TOGGLE_MOUNTED
    ReloadTime = 2000
    MoneyCost = 100
End
```

A hero that uses this shared template pays 100 for either direction once the example is applied. To price one hero, clone the template and point that hero's button and all associated behaviors to the clone. To charge different prices by direction, use separate templates and expose the corresponding command for each mount state.

For Fell Strength, add `MoneyCost = 500` to `SpecialAbilityNecroFellStrength` and retain its existing `UnitCost = 3`, `UnitCostDeathType`, and target rules. Test with both a valid target and enough eligible horde members.

## Lothlórien seal

Open `data/ini/includes/specialpower.inc`. In `SpecialPower SpecialAbilitySaatdesgoldenenWaldes`, add `MoneyCost = 150` and retain the existing reload, targeting, and placement fields. The fortress button `Command_SpecialAbilitySaatdesgoldenenWaldes` already references this template. The tooltip displays the price in the standard coin row, using the same localized cost label as the Mallorn Tree.

At 0–149 resources, test both the button and its hotkey. With 150 resources, choose a valid location and check that the treasury decreases by 150 once. If the balance drops below 150 after the cursor opens, the order should be rejected when placed. To opt into construction-site checking for the seal, follow [03. Construction site checks](phantom-structure-check.md) and enable the option on the seal's template.

## Thranduil's paid abilities

This example uses the hero template `ElvenThranduil_mod` in `data/ini/object/goodfaction/units/elven/thranduil.ini`. Its regular and Gift command sets are `ElvenThranduilCommandSetPaid` and `ElvenThranduilCommandSetPaidGift`. The command sets, buttons, templates, and OCL entries go in the corresponding files under `data/ini/includes/`. Use the equivalent source definitions if your data uses different names.

| Action | CommandButton | SpecialPower | Cost |
| --- | --- | --- | ---: |
| Thorn of Vengeance. Mount Thranduil and choose an enemy. | `Command_ThranduilPaidArrow` | `SpecialAbilityThranduilPaidArrow` | 300 |
| Area heal. Choose an area within range. | `Command_ThranduilPaidHeal` | `SpecialAbilityThranduilPaidHeal` | 400 |
| Army buff. Affects nearby Mirkwood troops. | `Command_ThranduilPaidArmyBuff` | `SpecialAbilityThranduilPaidArmyBuff` | 500 |
| Summon troops at a chosen location. | `Command_ThranduilPaidSummon` | `SpecialAbilityThranduilPaidSummon` | 1,000 |
| Summon troops, Gift variant. | `Command_ThranduilPaidSummonGift` | `SpecialAbilityThranduilPaidSummonGift` | 1,000 |

Clone `SpecialAbilityThornVengeance` and `SpecialAbilityTheodenGloriousCharge` from `data/ini/specialpower.ini`. Clone `SpecialAbilityDieSpeereDsterwalds` and `SpecialAbilityDieSpeereDsterwaldsUp` from `data/ini/includes/specialpower.inc`. Rename the copies using the table, add `MoneyCost` to each, and link each copy from its command button and every associated hero behavior. Clone the two command sets so each uses the matching paid summon variant.

For level-one availability, set `StartsPaused = No` in `ModuleTag_ThornArrow`, `ModuleTag_TheodenGloriousChargeUpdate`, `ModuleTag_OCLSpecialPower`, and `ModuleTag_OCLSpecialPower1`. Remove the corresponding level enablers along with `ModuleTag_ThornArrowAutoAbility`, `ThornOfVengeanceAI`, and the arrow button's `AutoAbility` field. In the buff behavior, set `UpdateModuleStartsAttack = No` and remove the old `ModuleTag_GloriousChargeAnimation` update. Clone `OCL_SpawnMirkwoddSpearmenEgg` and `OCL_SpawnMirkwoddSpearmenUpEgg` as `OCL_ThranduilPaidSummon` and `OCL_ThranduilPaidSummonGift`. Keep the summon payloads and remove `RequiredUpgrades = Upgrade_Level_2` from the copies.

The heal uses `Command = SPECIAL_POWER` and `Options = NEED_TARGET_POS`. Its template defines the cost.

```ini
SpecialPower SpecialAbilityThranduilPaidHeal
    Enum = SPECIAL_SPELL_BOOK_HEAL
    MoneyCost = 400
    ReloadTime = 90000
    RadiusCursorRadius = 120
    Flags = LIMIT_DISTANCE
    MaxCastRange = 250
End
```

The hero's heal module references that template and controls its effects.

```ini
Behavior = PlayerHealSpecialPower ModuleTag_ReinigungOCLSpecialPower
    SpecialPowerTemplate = SpecialAbilityThranduilPaidHeal
    StartsPaused = No
    UpdateModuleStartsAttack = No
    HealAmount = 0.50
    HealAsPercent = Yes
    HealAffects = INFANTRY CAVALRY HERO MONSTER
    HealRadius = 120
    HealFX = FX_SpellHealUnitHealBuff
End
```

### Charge only Thranduil for mounting and dismounting

1. Copy `SpecialAbilityToggleMounted` into `data/ini/includes/specialpower.inc` under the name `SpecialAbilityThranduilPaidMount`. Retain its enum and reload time, and add `MoneyCost = 100`.
2. In `data/ini/includes/commandbutton.inc`, clone `Command_ThranduilToggleMounted` as `Command_ThranduilPaidToggleMounted` and point its `SpecialPower` to the new template. Put the cloned button in slot 2 of both paid command sets in `data/ini/includes/commandset.inc`.
3. In `ElvenThranduil_mod`, update `SpecialPowerTemplate` in `ModuleTag_HorseToggleStarter` and `ModuleTag_HorseToggle`. Update `OnTriggerRechargeSpecialPower` in the starter to the same new template. Keep the existing timing, animation, and mount conditions.

## Arwen's 500-resource swordsmen

Arwen's example uses the native production queue. Its price belongs to the horde's `BuildCost`.

1. In `data/ini/object/goodfaction/hordes/imladris/imladrishordes.ini`, derive `BruchtalSchwertkmpferHorde_ArwenReinforcement` from `BruchtalSchwertkmpferHorde`. Set `BuildCost = 500`, `BuildTime = 1.0`, and `EquivalentTo = BruchtalSchwertkmpferHorde`. It inherits the five-member payload.
2. In `data/ini/includes/commandbutton.inc`, clone `Command_ConstructBruchtalSchwertkmpferHorde` as `Command_ArwenSummonSwordsmen500`. Keep `Command = UNIT_BUILD` and set `Object = BruchtalSchwertkmpferHorde_ArwenReinforcement`.
3. Put the button at slot 6 of `ElvenArwenmodCommandSet` in `data/ini/includes/commandset.inc`. In `data/ini/object/goodfaction/units/imladris/imladrisarwen.ini`, keep the hero's `ProductionUpdate` and add the exit behavior below to `ImladrisArwen`. Add the child horde to `IMLADRIS_TROOPS_SYSTEM` in `data/ini/includes/experiencelevels.inc` to retain rank progression.

```ini
Behavior = QueueProductionExitUpdate ModuleTag_ArwenReinforcementExit
    UnitCreatePoint = X:55.0 Y:0.0 Z:0.0
    NaturalRallyPoint = X:85.0 Y:0.0 Z:0.0
    ExitDelay = 0
    NoExitPath = Yes
End
```

Recruit Arwen in an Imladris skirmish and use her normal command panel. Allow enough command points for the horde. At 500 resources the queue should produce five swordsmen beside her.

## Engine implementation

The cost field is a signed integer at `SpecialPowerTemplate + 0x8C`. The parser uses the native integer parser at `0x0042EC5E`. Expand the template from `0x8C` to `0x90` at every allocation site, zero the new field in the constructor, copy it when a template is cloned, and redirect both parser-table pointers at `0x007B1ABE` and `0x007B2325`. The constructor, copy routine, and parser table retain the existing construction-site flag at `+0x88`. The addresses below apply to the executable documented in [01](filtered-horde-respawn-behavior.md).

| Entry points | Purpose |
| --- | --- |
| `0x0068E658`, `0x0068E72F`, `0x0068E792`, `0x0068E7EA` | Charge in the four `Object::doSpecialPower` dispatchers, after native validation and module resolution. |
| `0x007B1DCB` | Check affordability in the store while preserving readiness and science checks. |
| `0x0082D612`, `0x0082D967`, `0x0082DFFD` | Check affordability during self, object, and location targeting. |
| `0x0094343B`, `0x0075CC3E`, `0x0094053F` | Check button availability and click paths. |
| `0x00808675` | Route positive `MoneyCost` values through the native coin row. |
| `0x007B17EF` | Spend the controlling player's money through the native resource routine. |

The shared dispatch reads the final template after overrides. If a paid command synchronously delegates to another unit using the same player's template, the delegated call reuses the charge. When porting to a build that already charges in individual effect handlers, restore the native bytes at those sites before using the shared charge. The earlier debit sites were the weapon handler at `0x008962A3`, OCL at `0x008C75F8`, player heal at `0x008CC4E2`, and army buff at `0x008980C7`. The base build below already uses the native bytes at all four sites. The final charge is made when the engine accepts the cast, before the effect handler runs. Interrupting preparation after that point leaves the charge in effect.

## Build the final game.dat

Complete [10. Building the base engine patches](negative-experience.md#building-the-base-engine-patches) to produce `inspection/next/phase2_patched.dat`. Use that intermediary and the same pinned pySAGE checkout. The new build adds the shared ability price and installs the [wall movement fallback](wall-climbing.md#engine-fallback) and the [live construction-status correction](phantom-structure-check.md#live-construction-status-correction).

Save the following listings at the given paths and run these commands from the build directory.

```bash
PYTHONPATH=inspection/pysage-reference python3 inspection/next/build_money_cost.py inspection/next/phase2_patched.dat game.dat
printf '%s  %s\n' 05712460c7676500fc9255ffc18aaacda6d8b9ff4b62e22f9f283a9fa15718c5 game.dat | sha256sum -c -
```

<details>
<summary><code>inspection/next/money_cast.s</code></summary>

```asm
.intel_syntax noprefix
.code32
.section .text

.equ resolve_template, 0x688d3c
.equ get_controlling_player, 0x68b678
.equ get_local_player, 0x6a8839
.equ prepare_cast, 0x68cb85
.equ withdraw, 0x7b17ef
.equ balance, 0x94
.equ player_money, 0x90
.equ score_keeper, 0x3dc
.equ template_id, 0x14
.equ money_cost, 0x8c

# EAX = player, EDX = template id. Return the matching active record in ECX.
# Each record lives within the synchronous native dispatch that owns it.
find_active:
    mov ecx, [active_charge]
.Lfind:
    test ecx, ecx
    jz .Lfind_done
    cmp [ecx+4], eax
    jne .Lnext
    cmp [ecx+8], edx
    je .Lfind_done
.Lnext:
    mov ecx, [ecx]
    jmp .Lfind
.Lfind_done:
    ret

# ECX = template, EDI = caster, EDX = empty local record. A paid activation
# goes through this point after native target checks and module resolution.
begin_activation:
    push ebx
    push esi
    mov esi, edx
    test ecx, ecx
    jz .Lbegin_allow
    call resolve_template
    mov ebx, eax
    cmp dword ptr [ebx+money_cost], 0
    jle .Lbegin_allow
    mov ecx, edi
    call get_controlling_player
    test eax, eax
    jz .Lbegin_refuse
    mov edx, [ebx+template_id]
    call find_active
    test ecx, ecx
    jnz .Lbegin_allow
    mov ecx, [ebx+money_cost]
    cmp [eax+balance], ecx
    jb .Lbegin_refuse
    mov ebx, [active_charge]
    mov [esi], ebx
    mov [esi+4], eax
    mov [esi+8], edx
    lea edx, [eax+score_keeper]
    push 0
    push edx
    push ecx
    lea ecx, [eax+player_money]
    call withdraw
    mov [active_charge], esi
.Lbegin_allow:
    mov eax, 1
    jmp .Lbegin_done
.Lbegin_refuse:
    xor eax, eax
.Lbegin_done:
    pop esi
    pop ebx
    ret

.macro dispatch entry, next, slot, arity, first=0xc, second=0x10
.global \entry
\entry:
    sub esp, 12
    mov dword ptr [esp+4], 0
    mov edx, esp
    mov ecx, [ebp+8]
    call begin_activation
    test eax, eax
    jz .Ldone\@
    mov ecx, edi
    call prepare_cast
    .if \arity == 3
    push dword ptr [ebp+0x14]
    .endif
    .if \arity >= 2
    push dword ptr [ebp+\second]
    .endif
    push dword ptr [ebp+\first]
    mov ecx, esi
    mov eax, [esi]
    call [eax+\slot]
    cmp dword ptr [esp+4], 0
    je .Ldone\@
    mov edx, [esp]
    mov [active_charge], edx
.Ldone\@:
    add esp, 12
    jmp \next
.endm

dispatch cast_self,        0x68e669, 0x28, 1
dispatch cast_with_object, 0x68e743, 0x2c, 2
dispatch cast_at_position, 0x68e7a6, 0x30, 2
dispatch cast_at_object,   0x68e801, 0x34, 3

# Keep the native readiness, science and activation-condition checks.
# A horde can delegate its paid activation to a member in the same call.
.global store_affordability
store_affordability:
    mov ebx, eax
    mov ecx, esi
    call resolve_template
    cmp dword ptr [eax+money_cost], 0
    jle .Lstore_stock
    test ebx, ebx
    jz .Lstore_refuse
    push dword ptr [eax+money_cost]
    mov edx, [eax+template_id]
    mov eax, ebx
    call find_active
    pop edx
    test ecx, ecx
    jnz .Lstore_stock
    cmp [ebx+balance], edx
    jb .Lstore_refuse
.Lstore_stock:
    lea eax, [ebp-0x18]
    jmp 0x7b1dd0
.Lstore_refuse:
    jmp 0x7b1e36

# ECX = template, EDX = caster. EAX is a boolean. Pure UI/targeting check.
can_afford:
    push edx
    call get_money_cost
    pop ecx
    test eax, eax
    jz .Lcan_pay
    test ecx, ecx
    jz .Lcannot_pay
    push eax
    call get_controlling_player
    pop edx
    jmp check_player
.Lcan_pay:
    mov eax, 1
    ret
.Lcannot_pay:
    xor eax, eax
    ret

# EAX = player, EDX = positive cost.
check_player:
    test eax, eax
    jz .Lcannot_pay
    cmp [eax+balance], edx
    setae al
    movzx eax, al
    ret

.global validate_self, validate_object
validate_self:
    mov ecx, edi
    mov edx, ebx
    call can_afford
    test eax, eax
    jz .Lself_no
    push ebx
    mov ecx, esi
    call 0x82c366
    jmp 0x82d61a
.Lself_no:
    jmp 0x82d6bc

validate_object:
    mov ecx, edi
    mov edx, ebx
    call can_afford
    test eax, eax
    jz .Lobject_no
    push edi
    mov ecx, ebx
    call 0x68c26d
    jmp 0x82d96f
.Lobject_no:
    xor eax, eax
    jmp 0x82dc10

# EAX = command type, ESI = button, EBX = selected object (if any).
# Spellbook and remote command center clicks can start with an empty selection.
.global click_extra
click_extra:
    cmp eax, 0x25
    je .Ltoggle
    cmp eax, 0x26
    je .Lplayer_command
    cmp eax, 0x20
    jne .Lclick_stock
.Lplayer_command:
    mov ecx, [esi+0x44]
    call get_money_cost
    test eax, eax
    jz .Lclick_stock
    mov ecx, [0xde4928]
    test ecx, ecx
    jz .Lclick_no
    push eax
    call get_local_player
    pop edx
    call check_player
    jmp .Lcheck_click
.Ltoggle:
    test ebx, ebx
    jz .Lclick_stock
    mov ecx, [esi+0x44]
    mov edx, ebx
    call can_afford
.Lcheck_click:
    test eax, eax
    jz .Lclick_no
.Lclick_stock:
    cmp byte ptr [ebp+0xb], 0
    je .Lclick_continue
    jmp 0x940545
.Lclick_continue:
    jmp 0x94054f
.Lclick_no:
    jmp 0x940485

# Reuse the price row and localized coin label used by building and unit costs.
.global tooltip_price
tooltip_price:
    cmp ecx, 0x18
    je .Ltooltip_power
    cmp ecx, 0x20
    je .Ltooltip_power
    cmp ecx, 0x25
    je .Ltooltip_power
    cmp ecx, 0x26
    jne .Ltooltip_done
.Ltooltip_power:
    push eax
    push ecx
    mov ecx, [eax+0x44]
    call get_money_cost
    mov edx, eax
    pop ecx
    pop eax
    test edx, edx
    jz .Ltooltip_unpriced
    push edx
    jmp 0x8083a9
.Ltooltip_unpriced:
    cmp ecx, 0x18
    je .Ltooltip_stock
.Ltooltip_done:
    jmp 0x8086aa
.Ltooltip_stock:
    jmp 0x80867a


# Extend the constructor and copy routine while keeping the phantom flag.
.global init_money_cost, copy_money_cost
init_money_cost:
    mov [esi+0x84], ebx
    mov [esi+0x88], ebx
    mov [esi+money_cost], ebx
    jmp 0x7b2013

copy_money_cost:
    mov eax, [ebp+0x88]
    mov [ebx+0x88], eax
    mov eax, [ebp+money_cost]
    mov [ebx+money_cost], eax
    mov eax, ebx
    pop esi
    pop ebp
    pop ebx
    ret 4

# ECX = template. Read the final override and normalize missing or negative prices to zero.
get_money_cost:
    xor eax, eax
    test ecx, ecx
    jz .Lprice_read
    call resolve_template
    mov eax, [eax+money_cost]
    test eax, eax
    jns .Lprice_read
    xor eax, eax
.Lprice_read:
    ret

# Preserve the resolved template in EAX for the stock control bar.
.global control_bar_cost
control_bar_cost:
    call resolve_template
    mov edx, [eax+money_cost]
    test edx, edx
    jle .Lbar_continue
    push eax
    push edx
    mov ecx, ebx
    call get_controlling_player
    pop edx
    call check_player
    test eax, eax
    pop eax
    jz .Lbar_refuse
.Lbar_continue:
    jmp 0x943440
.Lbar_refuse:
    jmp 0x9438c8

# Normal special-power clicks and hotkeys also use this readiness function.
.global click_gate
click_gate:
    cmp dword ptr [ecx+0x14], 0x18
    jne .Lnormal_click_stock
    mov edx, [esp+4]
    push ecx
    mov ecx, [ecx+0x44]
    call can_afford
    pop ecx
    test eax, eax
    jz .Lnormal_click_refused
.Lnormal_click_stock:
    push esi
    push edi
    mov edi, [esp+0xc]
    jmp 0x75cc44
.Lnormal_click_refused:
    ret 4

.global location_gate
location_gate:
    push edi
    mov edx, esi
    mov ecx, [ebp+0x14]
    call can_afford
    test eax, eax
    jz .Llocation_refused
    mov ecx, [ebp+0x14]
    call resolve_template
    jmp 0x82e006
.Llocation_refused:
    jmp 0x82e23f

# Quick horde movement falls back to assigning the final formation destination
# after a rejected step and a failed local path. Let enrolled wall climbers
# wait for the native portal/path update instead of skipping the obstacle.
.global wall_path_fallback
wall_path_fallback:
    mov esi, [ebp-0xc]
    mov eax, [ebx+4]
    test byte ptr [eax+0x11f], 1
    jz .Ldefault_goal
    mov eax, [esi+0x1f0]
    test eax, eax
    jz .Ldefault_goal
    mov eax, [eax+4]
    cmp byte ptr [eax+0x150], 0
    jne .Lretry_next_tick
.Ldefault_goal:
    add esi, 0x200
    jmp 0x66cce1
.Lretry_next_tick:
    jmp 0x66d166

.balign 4
active_charge:
    .long 0
```

</details>

<details>
<summary><code>inspection/next/build_money_cost.py</code></summary>

```python
from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
from struct import pack, unpack
from subprocess import check_output, run
from tempfile import TemporaryDirectory

from sage_patch.patches.special_powers.special_power_upgrade_filters import (
    SPECIAL_POWER_TEMPLATE_NEW_SITES,
)
from sage_patch.utils import allocate_section, apply_byte_patch, file_offset, find_section, jmp_rel32


BASE_SHA256 = '6d4e28c916c0c9ff3e634971b60137d3d8f8b9d3c13b26b80bdfca9638558ae5'
HOOKS = (
    (0x7b200d, 'e9ee3f7e0090', 'init_money_cost'),
    (0x7b1f53, 'e9b9407e00909090', 'copy_money_cost'),
    (0x68e658, '8bcfe826e5ffffff750c8b068bceff5028', 'cast_self'),
    (0x68e72f, '8bcfe84fe4ffffff75108b06ff750c8bceff502c', 'cast_with_object'),
    (0x68e792, '8bcfe8ece3ffffff75108b06ff750c8bceff5030', 'cast_at_position'),
    (0x68e7ea, '8bcfe894e3ffffff75148b06ff75108bceff750cff5034', 'cast_at_object'),
    (0x7b1dcb, '8bd88d45e8', 'store_affordability'),
    (0x82d612, '538bcee84cedffff', 'validate_self'),
    (0x82d967, '578bcbe8fee8e5ff', 'validate_object'),
    (0x82dffd, '8b4d1457e836ade5ff', 'location_gate'),
    (0x94343b, 'e8fc58d4ff', 'control_bar_cost'),
    (0x75cc3e, '56578b7c240c', 'click_gate'),
    (0x94053f, '807d0b00740a', 'click_extra'),
    (0x808675, '83f9187530', 'tooltip_price'),
    (0x66ccd8, '8b75f481c600020000', 'wall_path_fallback'),
)
TABLE_REFERENCES = (0x7b1abe, 0x7b2325)


def patch_executable(source):
    if sha256(source).hexdigest() != BASE_SHA256:
        raise ValueError('Use the matching phase2_patched.dat from the base engine build.')
    game = bytearray(source)

    def read(address, size):
        offset = file_offset(game, address)
        return bytes(game[offset:offset+size])

    def patch(address, expected, new, label):
        apply_byte_patch(game, file_offset(game, address), bytes.fromhex(expected), new, label)

    old_pointer = read(TABLE_REFERENCES[0], 4)
    old_table, = unpack('<I', old_pointer)
    rows = read(old_table, 26 * 16)
    if read(old_table + len(rows), 16) != bytes(16):
        raise ValueError('Unexpected SpecialPower parser table length.')

    symbols = {}
    assembly = Path(__file__).resolve().with_name('money_cast.s')
    with TemporaryDirectory() as directory:
        work = Path(directory)
        obj, elf, raw = (work / name for name in ('patch.o', 'patch.elf', 'patch.bin'))
        run(['as', '--32', '-o', obj, assembly], check=True)

        def section(address):
            run(['ld', '-m', 'elf_i386', '-e', '0', '-Ttext', hex(address), '-o', elf, obj], check=True)
            run(['objcopy', '-O', 'binary', '-j', '.text', elf, raw], check=True)
            for row in check_output(['nm', '--defined-only', elf], text=True).splitlines():
                value, _, name = row.split()
                symbols[name] = int(value, 16)
            code = raw.read_bytes()
            code += bytes(-len(code) % 4)
            symbols['power_parse_table'] = address + len(code)
            field_name = symbols['power_parse_table'] + len(rows) + 32
            entry = pack('<4I', field_name, 0x42ec5e, 0, 0x8c)
            return code + rows + entry + bytes(16) + b'MoneyCost\0'

        allocate_section(game, '.paycast', section, 0xe0000060)

    for address, _ in SPECIAL_POWER_TEMPLATE_NEW_SITES:
        patch(address, '688c000000', b'\x68' + pack('<I', 0x90), 'template allocation')
    for address in TABLE_REFERENCES:
        patch(address, old_pointer.hex(), pack('<I', symbols['power_parse_table']), 'parser table')
    for address, expected, name in HOOKS:
        patch(address, expected, jmp_rel32(address, symbols[name], len(bytes.fromhex(expected))), name)

    # Skip destroyed objects and retain the pending and phantom construction status tests.
    phantom_section, _, _ = find_section(game, '.pwrxtra')
    patch(phantom_section + 0xdb, 'f68358040000017448', bytes.fromhex('f68394000000017548'),
          'live construction status')
    return game


def main():
    parser = ArgumentParser()
    parser.add_argument('input_executable', type=Path)
    parser.add_argument('output_executable', type=Path)
    args = parser.parse_args()
    result = patch_executable(args.input_executable.read_bytes())
    args.output_executable.write_bytes(result)
    print(sha256(result).hexdigest(), args.output_executable)


if __name__ == '__main__':
    main()
```

</details>

## In-game verification

| Test | Expected behavior |
| --- | --- |
| Mount and dismount with 99, 100, and 101 resources after applying the example | At 99 the command is unavailable. At 100 or 101, a valid toggle spends 100 once. |
| Seal and Thranduil's powers just below and at their listed prices | The localized coin row shows the configured price. A valid use spends the listed cost once. |
| A targeted power with an invalid target or with insufficient funds | The command is rejected before the effect starts. |
| Two casts with only enough money for the first | Only the first valid cast spends resources. Test with different casters to avoid cooldown masking the result. |
| A paid cast delegated from a horde to an individual member | The cast results in one debit. |
| A spellbook power with both a science cost and a resource cost | Unlock it with the existing science points. Each accepted use spends the configured resources. |
| A power with `MoneyCost = 0` or with the field omitted | It follows the original resource behavior. |

The engine hooks were verified by emulating all four dispatchers, the affordability and tooltip hooks, and a delegated cast. Mount transitions, placement cursors, and the actual tooltip appearance still need confirmation in ROTWK.
