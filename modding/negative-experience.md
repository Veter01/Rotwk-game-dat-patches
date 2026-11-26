# 10. Removing experience, ranks, and banner carriers

**Status:** XP loss, rank effects, banner retirement, and repeatable banner purchases passed x86 emulation. A live Windows match is pending.

## INI configuration

```ini
Behavior = LevelGrantSpecialPower ModuleTag_TunnelausbauenKingsFavor2
    SpecialPowerTemplate = SpecialAbilityTunnelbesetzen
    UnpackingVariation = 2
    StartAbilityRange = 30
    Experience = -60
    RadiusEffect = 100
    AcceptanceFilter = ANY +WildMineShaft +WildMineShaft_Player +WildMineShaft_Independant ENEMIES
    LevelFX = FX_LevelUp
    UnpackTime = 0
    PreparationTime = 0
    FreezeAfterTriggerDuration = 0
End
```

This example from the specification targets an enemy Mine Shaft. To test banner carrier removal, select a horde template with configured XP thresholds and a banner carrier. Check the command button's target filter too if it restricts valid targets.

## Implementation

- `level-grant-special-power` retains the original signed `Experience` parser, accepts negative values when executing the ability, and uses the relationship specified by `AcceptanceFilter`. It still skips an amount of zero.
- `experience-level-down` recalculates rank when XP is removed, removes the rank modifiers the object has lost, and updates its upgrades. XP has a lower bound. Only `OBJECT` upgrades owned by the object are considered.
- `upgrade-module-removal` and `special-power-pause-button` revoke upgrades and refresh ability availability. Modules whose effects must be reversible need to support removal and use `Permanent = No`.
- The input `game.dat` uses `.upg5k` to store some upgrade indices separately. For indices 1088 and above, the ownership check calls this build's existing read path at `0x00EDF337`. Removal uses the matching mask update path. The build checks the original jumps at `0x00691458` and `0x008097D6` against the expected bytes.
- The hook at `0x0079DAE3` compares the actual rank before and after the change. When the rank falls below the native banner spawn requirement, the engine clears the horde's banner slot and removes its banner carrier. The branch at `0x00871950` distinguishes this removal from combat death so `BannerCarrierDestroyHordeOnDeath` does not kill the horde when it loses rank.

## Building the base engine patches

1. Complete the [first build pass in 01](filtered-horde-respawn-behavior.md). It creates `inspection/game_patched.dat`.
2. Save the two source files from [02](cloudy-darkening-factor.md) and [03](phantom-structure-check.md).
3. Check out the pinned pySAGE revision in a separate clone. The adaptation script edits files in that clone. Use a clean checkout of this commit when rebuilding from scratch.

```bash
git clone https://github.com/ClementJ18/pySAGE.git inspection/pysage-reference
git -C inspection/pysage-reference checkout --detach 0a1f1b5d71b1b080008a7e9fff6f997601ec5a7f
```

4. Save the following four files at the paths shown.

<details>
<summary><code>inspection/next/adapt_reference.py</code></summary>

```python
from pathlib import Path
from hashlib import sha256
from struct import pack
from inspect_pe import img, off

base = Path('inspection/pysage-reference/sage_patch')
assert sha256(img).hexdigest() == 'd2e8e4354c5f31376ce043a7240d34ee119c02b28d8af4af27bb153f4e605762'
remove_site = img[off(0x691458):off(0x691458)+11]
assert remove_site == bytes.fromhex('e9a0e78400909090909090')
anchors_path = base/'addresses/objects.py'
anchors = anchors_path.read_text()
old = 'c1e8058d84828c020000f7d621308b'
assert anchors.count(old) == 2
anchors = anchors.replace(old, f'c1e805{remove_site.hex()}8b')

# Preserve the existing .upg5k trampoline in the model-condition lookup.
lookup_site = img[off(0x8097d6):off(0x8097d6)+6]
assert lookup_site == bytes.fromhex('e90e5c6d0090')
prefix = '    0x008097D6: bytes.fromhex(\n        "'
old = '8b44240433d22bc1568b34088531750f4283c10483fa2472f032c05ec20400b001ebf8'
assert anchors.count(prefix + old) == 1
anchors_path.write_text(anchors.replace(prefix + old, prefix + lookup_site.hex() + old[12:]))

xp_path = base/'patches/combat/experience_level_down.py'
xp = xp_path.read_text()
first = '''    a.emit(b"\\x8b\\x42\\x38\\x0f\\xa3\\x83\\x8c\\x02\\x00\\x00")
    a.jcc(JAE, "upgrade_next")  # already absent: duplicate definitions cause only one remove
'''
second = '''    a.emit(b"\\x8b\\x42\\x38")  # eax = upgrade index
    a.emit(b"\\x3d", (0x22 * 32).to_bytes(4, "little"))
    a.jcc(JAE, "extended_upgrade_bit")
    a.emit(b"\\x0f\\xa3\\x83\\x8c\\x02\\x00\\x00")
    a.jcc(JAE, "upgrade_next")  # already absent: duplicate definitions cause only one remove
    a.jmp("remove_upgrade")
    a.label("extended_upgrade_bit")
    # The input build stores dwords >= 0x22 in a separate mask. Use the
    # read-only path from its own Object::hasUpgrade bit test.
    a.emit(b"\\x89\\xc1\\xba\\x01\\x00\\x00\\x00\\xd3\\xe2\\xc1\\xe8\\x05")
    a.emit(b"\\x52\\x6a\\x00\\x52\\x50\\x8d\\x83\\x8c\\x02\\x00\\x00\\x50")
    a.call_absolute(0x00EDF337)
    a.emit(b"\\x83\\xc4\\x10\\x5a\\x85\\xd0")
    a.jcc(JE, "upgrade_next")
    a.emit(b"\\x8b\\x17")
    a.label("remove_upgrade")
'''
assert xp.count(first) == 1
xp_path.write_text(xp.replace(first, second))

prod_path = base/'patches/economy/production_split.py'
prod = prod_path.read_text()
prod = prod.replace('''    "PRODUCTION_MONEY",\n    "PRODUCTION_UNIT",\n    "PRODUCTION_UPGRADE",\n    "PRODUCTION_CONSTRUCTION",''','''    "RESOURCE_PRODUCTION",\n    "UNITS_PRODUCTION",''')
prod = prod.replace('return TypeIndices(*(first_index + position for position in range(len(NEW_TYPES))))',
                    'return TypeIndices(first_index, first_index + 1, first_index + 1, -1)')
prod = prod.replace('    (0x0088DE6D, CALC_TIME_TO_BUILD, "construction", "DozerAIUpdate construction rate"),\n','')
prod = prod.replace('        ("construction", lambda va: _build_construction(va, zero_va, types)),\n','')
prod_path.write_text(prod)
```

</details>

<details>
<summary><code>inspection/next/apply_reference.py</code></summary>

```python
from pathlib import Path
from sage_patch import apply_patches
from sage_patch.patches import (
    ExperienceLevelDownPatch, LevelGrantSpecialPowerPatch, UpgradeModuleRemovalPatch,
    SpecialPowerPauseButtonPatch, ProductionSplitPatch,
)

stage = Path('inspection/next')
patches = (
    ProductionSplitPatch(),
    UpgradeModuleRemovalPatch(),
    ExperienceLevelDownPatch(),
    LevelGrantSpecialPowerPatch(),
    SpecialPowerPauseButtonPatch(),
)
source = Path('inspection/game_patched.dat')
applied = []
for patch in patches:
    output = stage/(patch.name+'.dat')
    try:
        apply_patches(source, [patch], output=output)
    except ValueError as error:
        print(patch.name, error)
        raise
    source = output
    applied.append(patch)
    bytecode = source.read_bytes()
    for previous in applied:
        problems = previous.verify(bytecode)
        if problems:
            raise ValueError(previous.name, problems)
    print(patch.name, 'applied and verified with all earlier patches')
(stage/'phase2_base.dat').write_bytes(source.read_bytes())
```

</details>

<details>
<summary><code>inspection/next/banner_down.s</code></summary>

```asm
.intel_syntax noprefix
.code32
.section .text

# Track a genuine rank decrease across the engine's rank setter. The setter
# can decline a rank, so compare the result with the previously stored rank.
banner_check_level_change:
    push dword ptr [esi+0x24]
    push dword ptr [edi]
    mov ecx, esi
    call 0x79d72a
    pop ecx
    cmp [esi+0x24], ecx
    jge banner_level_change_done
    push dword ptr [esi+0x24]
    mov ecx, [esi+0x34]
    call retire_horde_banner
banner_level_change_done:
    jmp 0x79daec

retire_horde_banner:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    mov ebx, ecx
    test ebx, ebx
    jz retire_done
    call 0x68c866
    test eax, eax
    jz retire_done
    mov esi, eax
    mov edx, [esi]
    cmp dword ptr [edx+0x34], 0x87370b
    jne retire_done
    mov eax, [esi-0x118]
    test eax, eax
    jz retire_done
    movzx eax, byte ptr [eax+0x27c]
    # As in the native spawn gate, rank is zero-based and must be > minimum.
    cmp [ebp+8], eax
    jg retire_done
    mov eax, [esi+0x150]
    test eax, eax
    jz retire_done
    mov ecx, dword ptr [0xde412c]
    test ecx, ecx
    jz retire_done
    push eax
    call 0x449681
    test eax, eax
    jz retire_done
    mov edi, eax
    cmp [edi+0x27c], ebx
    jne retire_done
    cmp dword ptr [retiring_banner], edi
    je retire_done
    push dword ptr [retiring_banner]
    mov dword ptr [retiring_banner], edi
    push edi
    mov ecx, esi
    call 0x87370b
    push edi
    mov ecx, dword ptr [0xde412c]
    call 0x62bbab
    pop dword ptr [retiring_banner]
retire_done:
    pop edi
    pop esi
    pop ebx
    leave
    ret 4

# Let the native handler clear its banner ID and update the spawn delay.
# A retirement by rank loss does not trigger BannerCarrierDestroyHordeOnDeath.
banner_death_choice:
    cmp dword ptr [retiring_banner], edx
    je banner_death_survive
    cmp byte ptr [edi+0x224], 0
    je banner_death_survive
    jmp 0x871959
banner_death_survive:
    jmp 0x8719b5

.balign 4
retiring_banner: .long 0
```

</details>

<details>
<summary><code>inspection/next/build_extra.py</code></summary>

```python
from pathlib import Path
from struct import pack
import subprocess

from sage_patch.patches.special_powers.special_power_upgrade_filters import SPECIAL_POWER_TEMPLATE_NEW_SITES
from sage_patch.utils import allocate_section, apply_byte_patch, call_rel32, file_offset, find_section, jmp_rel32

ROOT = Path('inspection/next')
SOURCE = ROOT/'phase2_base.dat'
PATCH = ROOT/'power_extras'
OUTPUT = ROOT/'phase2_patched.dat'
PLAIN_TABLE = 0xDA5FD8
TABLE_LENGTH = 0x180
ANCHORS = {
    0x688d3c: '8bc18b500485d274',
    0x97338f: '8b81ac000000c3',
    0x7640c1: '578bf98b4c240885c9',
    0x82d2fd: 'b816beb900e8e9fb2000',
    0x82c366: '558bec83ec0c833d404bde0000',
    0x871a14: '0fb6807c0200008b8b6c0200003941247e44',
    0x87370b: 'b892f7b900e8db971c00',
    0x62bbab: '53578b7c240c85ff',
    0x68c866: '8b895802000085c97503',
}
d = bytearray(SOURCE.read_bytes())

def read(va, size):
    p = file_offset(d,va)
    return bytes(d[p:p+size])

def expect(va, expected):
    actual = read(va,len(expected))
    assert actual == expected, f'{va:x}: {actual.hex()} != {expected.hex()}'

def apply(va, old, new):
    old = bytes.fromhex(old)
    apply_byte_patch(d,file_offset(d,va),old,new,f'{va:#010x}')

for va, old in ANCHORS.items():
    expect(va, bytes.fromhex(old))
expected_section, expected_raw, expected_size = find_section(d,'.bldcap')
expect(expected_section+0x16, bytes.fromhex('f6835804000001742580bb9e00000000791cf6839f000000017413'))

subprocess.run(['as','--32','-o',PATCH.with_suffix('.o'),PATCH.with_suffix('.s')],check=True)
symbols = {}
def build_cave(va):
    subprocess.run(['ld','-m','elf_i386','-e','0','-Ttext',hex(va),'-o',PATCH.with_suffix('.elf'),PATCH.with_suffix('.o')],check=True)
    subprocess.run(['objcopy','-O','binary','-j','.text',PATCH.with_suffix('.elf'),PATCH.with_suffix('.bin')],check=True)
    obj_code = PATCH.with_suffix('.bin').read_bytes()
    for row in subprocess.check_output(['nm',PATCH.with_suffix('.elf')],text=True).splitlines():
        addr, _type, name = row.split()
        symbols[name] = int(addr,16)
    obj_code += bytes(-len(obj_code)%4)
    table_va = va + len(obj_code)
    symbols['power_parse_table'] = table_va
    names = [b'PhantomStructureCheck\0',b'PhantomStrucrureCheck\0']
    table = read(PLAIN_TABLE,TABLE_LENGTH)
    expect(PLAIN_TABLE+TABLE_LENGTH,bytes(16))
    header_size = len(table) + (len(names)+1)*16
    text_data = bytearray()
    for name in names:
        table += pack('<4I',table_va+header_size+len(text_data),0x42e558,0,0x88)
        text_data.extend(name)
    obj_code += table + bytes(16) + bytes(text_data)
    obj_code += bytes(-len(obj_code) % 4)
    weather_table_va = va + len(obj_code)
    symbols['weather_parse_table'] = weather_table_va
    stock_weather_table = read(0xc64db0, 35 * 16)
    expect(0xc64db0 + len(stock_weather_table), bytes(16))
    name = b'DarkeningFactor\0'
    weather_row = pack('<4I', weather_table_va+len(stock_weather_table)+32,
                       symbols['weather_parse_rgb'], 0, 0x2c)
    return obj_code + stock_weather_table + weather_row + bytes(16) + name

new_va = allocate_section(d,'.pwrxtra',build_cave,0xe0000060)
assert new_va == find_section(d,'.pwrxtra')[0]

for va, _ in SPECIAL_POWER_TEMPLATE_NEW_SITES:
    apply(va,'68 88 00 00 00',b'\x68'+pack('<I',0x8c))

for va, op, dest in [
    (0x7b200d,'89 9e 84 00 00 00','power_template_init'),
    (0x7b1f53,'8b c3 5e 5d 5b c2 04 00','power_template_copy'),
    (0x719fdb,'56 8b f1 57 ff 76 14','weather_reset'),
    (0x71a3b7,'5f 5e c9 c2 04 00','weather_xfer'),
    (0x494de0,'8d 73 30 a5 a5 a5','weather_copy_rgb'),
    (0x79dae3,'ff 37 8b ce e8 3e fc ff ff','banner_check_level_change'),
    (0x871950,'80 bf 24 02 00 00 00 74 5c','banner_death_choice'),
]:
    apply(va,op,jmp_rel32(va,symbols[dest],len(bytes.fromhex(op))))
for va, op, dest in [
    (0x82e128,'e8 d0 f1 ff ff','phantom_location_gate'),
    (0x82da69,'e8 f8 e8 ff ff','phantom_object_gate'),
    (0x897b45,'e8 da 24 e8 ff','weather_cast'),
]:
    apply(va,op,call_rel32(va,symbols[dest]))
for va in (0x7b1abe,0x7b2325):
    apply(va,'d8 5f da 00',pack('<I',symbols['power_parse_table']))

apply(0x896897,'88 5e 2c',bytes.fromhex('89 5e 2c'))
apply(0x8968ff,'88 5e 68',bytes.fromhex('89 5e 68'))
apply(0x8969a2,'b0 4d c6 00',pack('<I',symbols['weather_parse_table']))
apply(0x71a2fd,'04',bytes([5]))

OUTPUT.write_bytes(d)
print(OUTPUT)
```

</details>

5. Run the commands from the working directory. They use Python 3.12 and the binutils specified in [01](filtered-horde-respawn-behavior.md).

```bash
PYTHONPATH=inspection python3 inspection/next/adapt_reference.py
PYTHONPATH=inspection/pysage-reference python3 inspection/next/apply_reference.py
printf '%s  %s\n' 9a5afb853026eec0c45a6ef918dade811eda51591942c6991d7ac6731fbe3c04 inspection/next/phase2_base.dat | sha256sum -c -
PYTHONPATH=inspection/pysage-reference python3 inspection/next/build_extra.py
printf '%s  %s\n' 6d4e28c916c0c9ff3e634971b60137d3d8f8b9d3c13b26b80bdfca9638558ae5 inspection/next/phase2_patched.dat | sha256sum -c -
```

The rebuilt executable is `inspection/next/phase2_patched.dat`. To test it, back up the current `game.dat` and replace it with the rebuilt file. Enable the desired options in the mod's INI files using the examples. The build covers seven items from the specification. See [07](wall-climbing.md), [08](special-power-money-cost.md), and [09](worker-harvest-filters.md) for wall climbing, ability costs, and worker filters.

For the engine build with generic `MoneyCost`, the wall movement fallback, and the live construction-status correction, continue with [08. Build the final game.dat](special-power-money-cost.md#build-the-final-gamedat).

## In-game verification of rank loss

1. Give a horde enough XP to cross its banner spawn threshold. Record its current rank and the upgrades tied to that rank.
2. Apply negative XP. First remove too little to change its rank, then bring it below the `BannerCarrierMinLevel` requirement. The banner carrier should disappear as the horde crosses the threshold, and the horde should survive. Check that it loses the old rank's upgrade and the ability tied to that upgrade.
3. Restore the XP. Check that the ability returns and the banner carrier spawns through the normal path. Separately test losing a banner carrier in combat and filtering an enemy target.

## Make the banner upgrade purchasable again

An `ExperienceLevel` reward and a paid training upgrade are recorded separately. Retiring the banner and removing the old rank rewards can leave the squad's paid `OBJECT` upgrade marked as complete. That completion flag blocks a second purchase, and its `LevelUpUpgrade` handler also needs to be ready to run again.

The follow-up calls the existing banner retirement code, then clears a matching training purchase when the stored rank crosses the native boundary. The spawn test is `rank > BannerCarrierMinLevel`, so a drop from rank 2 to rank 1 crosses the default boundary. The horde must have a configured list of banner carriers.

The handler checks the active, default, and alternate command sets for an `OBJECT_UPGRADE` button whose upgrade is owned by the horde. The same upgrade must appear in a `LevelUpUpgrade` trigger mask with positive `LevelsToGain` and a `LevelCap` above the banner boundary. It clears the upgrade via the engine's native `Object::removeUpgrade` path at `0x00691438`, which also resets the module through its upgrade-removal callbacks. Use a nonpermanent `LevelUpUpgrade` for repeatable training. The button keeps its normal technology requirements, price, build time, and grant behavior.

| Address in the reference input | Change |
| --- | --- |
| `0x00F462B2` | Route the genuine rank-loss branch through the existing banner retirement and the repurchase reset. Pass both the old and new rank. |
| `0x00C6E054` | Wrap `LevelUpUpgrade::loadPostProcess` so an older save can clear a stale purchase flag in a low-rank horde without a banner. On load, require that one purchase can raise the horde across the threshold. |
| `0x00EDF337` | Read the existing extended mask for upgrade indices 1088 and above. Native removal updates the same storage. |

### Test with INI

Use the signed `Experience` field shown above. To target a test horde instead of a Mine Shaft, set `AcceptanceFilter = ANY +MordorFighterHorde ENEMIES` on the test ability. If its command button has a separate target filter, allow that horde there too. The reference horde uses `Command_PurchaseMordorAufseher` to buy `Upgrade_PurchaseMordorAufseher`, with the module below.

```ini
Behavior = LevelUpUpgrade ModuleTag_BasicTraining
    TriggeredBy = Upgrade_PurchaseMordorAufseher
    LevelsToGain = 1
    LevelCap = 2
End
```

1. Research the required technology and buy the upgrade. Apply enough negative XP to demote the horde below its banner boundary.
2. Buy the upgrade again. Check the treasury, the new rank, and the banner's appearance. Repeat with a save made after demotion.
3. Lose a banner in ordinary combat and check its normal replacement behavior. Apply a smaller XP loss while the horde stays above the threshold and verify that the paid upgrade remains complete.
4. Equip another upgrade and verify that the purchase survives the demotion.

The native ownership check, upgrade removal, reactivation, completed-purchase path, and saved-state repair were exercised in x86 emulation. Confirm the UI and banner appearance in a Windows match.

### Build the banner repurchase patch

Use the reference output from [09. Worker harvest and warehouse filters](worker-harvest-filters.md#build-the-patched-gamedat), which includes the earlier banner-retirement hook from this guide. The addresses above are virtual addresses specific to that input. Save the three listings below together and use the same pinned pySAGE checkout, Python 3, GCC with i386 support, and GNU binutils.

| File | Reference SHA-256 |
| --- | --- |
| Input `game.dat` | `4d9e7bbe44766173fcb81f53cbf712da9cd4c3e74b43beec29f643d17cf97400` |
| Output with GCC 14.2.0 and GNU binutils 2.44 | `bad61adac79fa2e1919d65387196913610685b5c0b05b6219e4872e6dd49f3f5` |

```bash
PYTHONPATH=pySAGE python3 build_banner_repurchase.py game.dat game_with_banner_repurchase.dat
```

Use the output as `game.dat` for testing. The engine fix uses the current horde and purchase definitions from your data.

### Banner repurchase sources

<details>
<summary><code>banner_repurchase.c</code></summary>

```c
typedef unsigned char Byte;
typedef unsigned int MaskWord;

#define THISCALL __attribute__((thiscall))
#define AT(type, base, offset) (*(type const *)((const Byte *)(base) + (offset)))

enum {
    ObjectTemplate = 0x04,
    ObjectModules = 0x24c,
    ObjectExperienceTracker = 0x26c,
    ObjectCompletedUpgrades = 0x28c,
    HordeContainData = -0x118,
    HordeBannerId = 0x150,
    HordeBannerNameList = 0x218,
    HordeBannerMinLevel = 0x27c,
    LevelUpUpgradeVTable = 0xc6e050,
    LevelsToGain = 0x138,
    LevelCap = 0x13c,
    ObjectUpgradeCommand = 7,
    CommandSetSlots = 64,
    InlineUpgradeWords = 0x22,
    UpgradeCapacity = 0x1400
};

typedef void (THISCALL RetireBanner)(void *, int);
typedef void (THISCALL LoadPostProcess)(void *);
typedef const void *(THISCALL ReadObjectValue)(const void *);
typedef const void *(THISCALL FindCommandSet)(const void *, const void *);
typedef const void *(THISCALL FindCommandButton)(const void *, int);
typedef void (THISCALL RemoveObjectUpgrade)(void *, const void *);
typedef MaskWord (ExtendedMask)(const void *, unsigned, MaskWord, unsigned);

#define retire_banner ((RetireBanner *)0xf462c2)
#define original_load_post_process ((LoadPostProcess *)0x8b88b0)
#define get_horde ((ReadObjectValue *)0x68c866)
#define get_command_set_name ((ReadObjectValue *)0x69156b)
#define get_alternate_template ((ReadObjectValue *)0x69194e)
#define find_command_set ((FindCommandSet *)0x71efa2)
#define get_command_button ((FindCommandButton *)0x80c837)
#define remove_object_upgrade ((RemoveObjectUpgrade *)0x691438)
#define extended_mask_word ((ExtendedMask *)0xedf337)
#define command_set_store (*(const void **)0xde7744)

static const Byte *banner_horde(const void *object, int *minimum_level)
{
    if (!object)
        return 0;
    const Byte *horde = get_horde(object);
    if (!horde || AT(const MaskWord *, horde, 0)[0x34 / 4] != 0x87370b)
        return 0;
    const Byte *data = AT(const Byte *, horde, HordeContainData);
    if (!data || AT(const void *, data, HordeBannerNameList) ==
                 AT(const void *, data, HordeBannerNameList + 4))
        return 0;
    *minimum_level = data[HordeBannerMinLevel];
    return horde;
}

static int has_mask_bit(const Byte *mask, unsigned index)
{
    unsigned word = index >> 5;
    MaskWord bit = 1u << (index & 31);
    MaskWord value = word < InlineUpgradeWords
        ? ((const MaskWord *)mask)[word]
        : extended_mask_word(mask, word, bit, 0);
    return (value & bit) != 0;
}

static int starts_banner_training(const Byte *object, unsigned upgrade_index, int rank,
                                  int minimum_level, int loading)
{
    const Byte *const *modules = AT(const Byte *const *, object, ObjectModules);
    if (!modules)
        return 0;
    for (; *modules; ++modules) {
        const Byte *module = *modules;
        if (AT(MaskWord, module, 0) != LevelUpUpgradeVTable)
            continue;
        const Byte *data = AT(const Byte *, module, 4);
        if (!data)
            continue;
        int gain = AT(int, data, LevelsToGain);
        int cap = AT(int, data, LevelCap);
        if (gain <= 0 || cap <= minimum_level || (loading && gain <= minimum_level - rank))
            continue;
        if (has_mask_bit(data + 8, upgrade_index))
            return 1;
    }
    return 0;
}

static void reset_training_buttons(Byte *object, const void *set, int rank, int minimum_level, int loading)
{
    if (!set)
        return;

    for (int slot = 0; slot < CommandSetSlots; ++slot) {
        const Byte *button = get_command_button(set, slot);
        if (!button || AT(int, button, 0x14) != ObjectUpgradeCommand)
            continue;
        const Byte *upgrade = AT(const Byte *, button, 0x24);
        if (!upgrade || !AT(int, upgrade, 4))
            continue;
        unsigned index = AT(unsigned, upgrade, 0x38);
        if (index >= UpgradeCapacity || !has_mask_bit(object + ObjectCompletedUpgrades, index))
            continue;
        if (starts_banner_training(object, index, rank, minimum_level, loading))
            remove_object_upgrade(object, upgrade);
    }
}

static void reset_training_purchase(Byte *object, int rank, int minimum_level, int loading)
{
    const void *store = command_set_store;
    if (!store)
        return;
    const void *active = find_command_set(store, get_command_set_name(object));
    reset_training_buttons(object, active, rank, minimum_level, loading);

    /* Formation and temporary command sets can hide the original purchase button. */
    const Byte *template = AT(const Byte *, object, ObjectTemplate);
    const Byte *alternate = get_alternate_template(object);
    if (template) {
        const void *base_set = find_command_set(store, template + 0x70);
        if (base_set != active)
            reset_training_buttons(object, base_set, rank, minimum_level, loading);
    }
    if (alternate && alternate != template) {
        const void *alternate_set = find_command_set(store, alternate + 0x70);
        if (alternate_set != active)
            reset_training_buttons(object, alternate_set, rank, minimum_level, loading);
    }
}

void THISCALL rank_lost(void *object, int rank, int old_rank)
{
    retire_banner(object, rank);
    int minimum_level;
    if (banner_horde(object, &minimum_level) && rank <= minimum_level && old_rank > minimum_level)
        reset_training_purchase(object, rank, minimum_level, 0);
}

void THISCALL load_level_up_upgrade(void *module)
{
    original_load_post_process(module);

    Byte *object = AT(Byte *, module, 8);
    int minimum_level;
    const Byte *horde = banner_horde(object, &minimum_level);
    if (!horde || AT(unsigned, horde, HordeBannerId))
        return;
    const Byte *tracker = AT(const Byte *, object, ObjectExperienceTracker);
    if (!tracker)
        return;
    int rank = AT(int, tracker, 0x24);
    if (rank >= 0 && rank <= minimum_level)
        reset_training_purchase(object, rank, minimum_level, 1);
}
```

</details>

<details>
<summary><code>banner_repurchase.s</code></summary>

```asm
.intel_syntax noprefix
.section .text
.global on_rank_loss
.set level_change_resume, 0xf462bd

# ECX contains the rank before the setter. ESI points to the live tracker.
on_rank_loss:
    push ecx
    push dword ptr [esi+0x24]
    mov ecx, [esi+0x34]
    call rank_lost
    jmp level_change_resume

.section .note.GNU-stack,"",@progbits
```

</details>

<details>
<summary><code>build_banner_repurchase.py</code></summary>

```python
from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
from struct import pack
from subprocess import check_output, run
from tempfile import TemporaryDirectory

from sage_patch.utils import allocate_section, apply_byte_patch, file_offset, jmp_rel32, read_bytes

HERE = Path(__file__).resolve().parent
BASE_HASH = '4d9e7bbe44766173fcb81f53cbf712da9cd4c3e74b43beec29f643d17cf97400'
RANK_BRANCH = 0xf462b2
RANK_ORIGINAL = bytes.fromhex('ff76248b4e34e805000000')
LEVEL_UP_LOAD_SLOT = 0xc6e054
ORIGINAL_LOAD = 0x8b88b0


def patch_executable(stock, work):
    assert sha256(stock).hexdigest() == BASE_HASH
    assert read_bytes(stock, 0x80c8fc, 3) == bytes.fromhex('83fa40')
    assert read_bytes(stock, 0xf462ad, 5) == bytes.fromhex('394e247d0b')
    image = bytearray(stock)
    native, hooks, elf, binary, script = (work / file for file in
                                         ('purchase.o', 'hooks.o', 'purchase.elf', 'purchase.bin', 'purchase.ld'))
    run(['gcc', '-m32', '-Os', '-std=c11', '-ffreestanding', '-fno-pic', '-fno-pie',
         '-fno-stack-protector', '-fno-asynchronous-unwind-tables', '-fno-unwind-tables',
         '-fno-ident', '-mno-sse', '-mno-mmx', '-mpreferred-stack-boundary=2',
         '-mincoming-stack-boundary=2', '-Wall', '-Wextra', '-Werror',
         '-c', HERE / 'banner_repurchase.c', '-o', native], check=True)
    run(['as', '--32', HERE / 'banner_repurchase.s', '-o', hooks], check=True)
    script.write_text('''
SECTIONS {
    . = PATCH_ADDRESS;
    .patch : { *(.text*) *(.rodata*) }
    /DISCARD/ : { *(.note*) *(.comment*) }
}
''')
    symbols = {}

    def payload(address):
        run(['ld', '-m', 'elf_i386', '-z', 'noexecstack', '-T', script, '--defsym',
             f'PATCH_ADDRESS={address:#x}', '-o', elf, native, hooks], check=True)
        for row in check_output(['nm', '--defined-only', elf], text=True).splitlines():
            value, _, name = row.split()
            symbols[name] = int(value, 16)
        run(['objcopy', '-O', 'binary', '-j', '.patch', elf, binary], check=True)
        return binary.read_bytes()

    allocate_section(image, '.banbuy', payload, 0x60000020)
    apply_byte_patch(image, file_offset(image, RANK_BRANCH), RANK_ORIGINAL,
                     jmp_rel32(RANK_BRANCH, symbols['on_rank_loss'], len(RANK_ORIGINAL)), 'Banner purchase on level loss')
    apply_byte_patch(image, file_offset(image, LEVEL_UP_LOAD_SLOT),
                     pack('<I', ORIGINAL_LOAD), pack('<I', symbols['load_level_up_upgrade']),
                     'Restore banner purchase after loading')
    return bytes(image), symbols


def main():
    parser = ArgumentParser()
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    with TemporaryDirectory() as folder:
        game, _ = patch_executable(args.input.read_bytes(), Path(folder))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(game)


if __name__ == '__main__':
    main()
```

</details>

## Credits and references

- **officialNecro** provided the basis for [06](production-split.md). [production-split source](https://github.com/ClementJ18/pySAGE/blob/0a1f1b5d71b1b080008a7e9fff6f997601ec5a7f/sage_patch/patches/economy/production_split.py)
- **Ostkannit** authored the XP loss, ability effect, upgrade module removal, and button state changes. [experience-level-down](https://github.com/ClementJ18/pySAGE/blob/0a1f1b5d71b1b080008a7e9fff6f997601ec5a7f/sage_patch/docs/experience-level-down.md) · [level-grant-special-power](https://github.com/ClementJ18/pySAGE/blob/0a1f1b5d71b1b080008a7e9fff6f997601ec5a7f/sage_patch/docs/level-grant-special-power.md) · [upgrade-module-removal](https://github.com/ClementJ18/pySAGE/blob/0a1f1b5d71b1b080008a7e9fff6f997601ec5a7f/sage_patch/docs/upgrade-module-removal.md) · [special-power-pause-button](https://github.com/ClementJ18/pySAGE/blob/0a1f1b5d71b1b080008a7e9fff6f997601ec5a7f/sage_patch/docs/special-power-pause-button.md)
- Keep the MIT notice when publishing copies of the pySAGE code. The license is included in the cloned repository. [LICENSE](https://github.com/ClementJ18/pySAGE/blob/0a1f1b5d71b1b080008a7e9fff6f997601ec5a7f/LICENSE)

## Repeating the machine-code tests for the full build

The test loads the final PE32 image in an x86 emulator, runs the patched routines, and substitutes stubs for external engine calls. It covers construction site checks, weather color, production multipliers, banner carrier removal, extended upgrade indices, and compatibility between the applied patches.

<details>
<summary><code>inspection/next/test_phase2.py</code></summary>

```python
from pathlib import Path
from struct import pack, unpack

import pefile
from unicorn import Uc, UC_ARCH_X86, UC_HOOK_CODE, UC_MODE_32
from unicorn.x86_const import (
    UC_X86_REG_EAX, UC_X86_REG_EBX, UC_X86_REG_ECX, UC_X86_REG_EDX, UC_X86_REG_EBP,
    UC_X86_REG_EFLAGS, UC_X86_REG_EIP, UC_X86_REG_EDI, UC_X86_REG_ESI, UC_X86_REG_ESP
)

from sage_patch.patches.combat import experience_level_down as level_down
from sage_patch.patches.economy import production_split as production
from sage_patch.utils import file_offset, find_section
from sage_patch.patches import (
    LevelGrantSpecialPowerPatch, ExperienceLevelDownPatch, UpgradeModuleRemovalPatch,
    SpecialPowerPauseButtonPatch, ProductionSplitPatch,
)

ROOT=Path('inspection/next')
image=(ROOT/'phase2_patched.dat').read_bytes()
base=pefile.PE(data=image)
uc=Uc(UC_ARCH_X86, UC_MODE_32)
uc.mem_map(0x400000, base.OPTIONAL_HEADER.SizeOfImage)
for section in base.sections:
    uc.mem_write(0x400000 + section.VirtualAddress, section.get_data())
uc.mem_map(0x20000000,0x40000)
stop=0x20000000
stack=0x2003ffe0
aux=0x20001000

r=uc.reg_read
w=uc.reg_write
def get(address):
    return unpack('<I',uc.mem_read(address,4))[0]
def put(address,*values):
    uc.mem_write(address,pack(f'<{len(values)}I',*values))
def fp(address,*values):
    uc.mem_write(address,pack(f'<{len(values)}f',*values))
def floats(address):
    return unpack('<3f',uc.mem_read(address,12))
def getbyte(p):
    return uc.mem_read(p,1)[0]
def setbyte(p,data):
    uc.mem_write(p,bytes([data]))
def zstr(p):
    chars=bytearray()
    while (c:=getbyte(p)):
        chars.append(c)
        p+=1
    return chars.decode()

callbacks={}
def hook(engine, entry, size, extra):
    if entry in callbacks:
        callbacks[entry]()
uc.hook_add(UC_HOOK_CODE, hook)
def emu_return(pop=0,value=None):
    if value is not None: w(UC_X86_REG_EAX,value)
    esp=r(UC_X86_REG_ESP)
    w(UC_X86_REG_EIP,get(esp))
    w(UC_X86_REG_ESP,esp+4+pop)
def argument(index):
    return get(r(UC_X86_REG_ESP)+4*index)

def run(va,args=(), registers=None, cleanup=0, check_stack=True):
    for reg in (UC_X86_REG_EAX,UC_X86_REG_EBX,UC_X86_REG_ECX,UC_X86_REG_EDX,
                UC_X86_REG_EBP,UC_X86_REG_ESI,UC_X86_REG_EDI):
        w(reg, 0)
    w(UC_X86_REG_EFLAGS,0x202)
    for reg, value in (registers or {}).items(): w(reg, value)
    put(stack,stop,*args)
    w(UC_X86_REG_ESP,stack)
    uc.emu_start(va,stop,count=20000)
    assert r(UC_X86_REG_EIP)==stop
    if check_stack:
        assert r(UC_X86_REG_ESP)==stack+4+cleanup
    return r(UC_X86_REG_EAX)

def jumps_from(va):
    assert getbyte(va) in (0xe8,0xe9)
    rel,=unpack('<i',uc.mem_read(va+1,4))
    return va+5+rel

# Follow what the final binary actually points to rather than a build-map copy.
special_table=get(0x7b1abe)
assert special_table==get(0x7b2325)
assert tuple(zstr(get(special_table+i*16)) for i in (24,25)) == (
    'PhantomStructureCheck','PhantomStrucrureCheck')
assert get(special_table+26*16)==0
assert get(special_table+24*16+12)==0x88==get(special_table+25*16+12)
weather_table=get(0x8969a2)
assert zstr(get(weather_table+35*16))=='DarkeningFactor'
assert get(weather_table+35*16+12)==0x2c and get(weather_table+36*16)==0

template=aux
caster=aux+0x800
phantom=aux+0x1000
target=aux+0x1800
hero=aux+0x2000
logic=aux+0x2800
put(0xde412c,logic)
put(logic+0xac,phantom)
put(template+0x18,0x10)
fp(template+0x7c,50)
fp(phantom+0x38,30,40,500)
fp(target+0x38,0,0,0)
setbyte(phantom+0x458,1)
setbyte(phantom+0x9e,0x80)
setbyte(phantom+0x9f,1)
stock_allow=1
object_allow=0
filter_matches=1
def check_loc_stock():
    assert (argument(1),argument(2),argument(3))==(caster,target+0x38,template)
    emu_return(12,stock_allow)
def check_obj_stock():
    assert argument(1)==caster
    emu_return(4,object_allow)
def check_obj_filter():
    assert r(UC_X86_REG_ECX)==template+0x78
    assert (argument(1),argument(2))==(phantom,caster)
    emu_return(8,filter_matches)
callbacks.update({0x82d2fd:check_loc_stock,0x82c366:check_obj_stock,0x7640c1:check_obj_filter})
loc=jumps_from(0x82e128)
assert run(loc,(caster,target+0x38,template),cleanup=12)==1
setbyte(template+0x88,1)
assert run(loc,(caster,target+0x38,template),cleanup=12)==0
fp(phantom+0x3c,41)
assert run(loc,(caster,target+0x38,template),cleanup=12)==1
fp(phantom+0x3c,39)
filter_matches=0
assert run(loc,(caster,target+0x38,template),cleanup=12)==1
filter_matches=1
setbyte(phantom+0x9f,0)
assert run(loc,(caster,target+0x38,template),cleanup=12)==1
setbyte(phantom+0x9f,1)
put(template+0x18,0)
assert run(loc,(caster,target+0x38,template),cleanup=12)==1
put(template+0x18,0x10)
stock_allow=0
assert run(loc,(caster,target+0x38,template),cleanup=12)==0
object_gate=jumps_from(0x82da69)
frame=aux+0x3000
put(frame+0xc,target)
put(frame+0x14,template)
assert run(object_gate,(caster,),registers={UC_X86_REG_EBP:frame,UC_X86_REG_EBX:caster},cleanup=4)==1
object_allow=1
setbyte(template+0x88,0)
assert run(object_gate,(caster,),registers={UC_X86_REG_EBP:frame,UC_X86_REG_EBX:caster},cleanup=4)==1
print('Phantom template, filters, distance, native fallback, location and object branches passed')

# Exercise the actual callable parser stub, colour packing, weather dispatch, native float colour
# convention, fade-state register preservation, reset, and old/new save field.
module=aux+0x5000
cloud=aux+0x6000
dest=aux+0x6800
def native_rgb_parse():
    assert argument(1)==0x11 and argument(2)==0x22 and argument(4)==0x44
    fp(argument(3),30/255,130/255,255/255)
    emu_return()
callbacks[0x42ef99]=native_rgb_parse
def weather_setter():
    assert argument(1) in (0,1,2)
    assert (argument(2),argument(3))==(0,1800)
    emu_return(12,0)
callbacks[0x71a024]=weather_setter
def color_resume():
    assert (r(UC_X86_REG_EFLAGS)&0xcd5)==0x40
    assert r(UC_X86_REG_EDI)==dest+12 and r(UC_X86_REG_ESI)==cloud+0x3c
    emu_return()
callbacks[0x494de6]=color_resume
def color_test(expected,weather):
    put(cloud+0xbc,weather)
    def color_setup():
        w(UC_X86_REG_EFLAGS,0x242)
    entry=jumps_from(0x494de0)
    callbacks[entry]=color_setup
    run(entry,registers={UC_X86_REG_EBX:cloud,UC_X86_REG_EDI:dest})
    assert all(abs(a-b)<1e-6 for a,b in zip(floats(dest),expected))
    del callbacks[entry]

# Parsing must leave the adjacent existing WeatherBased flag untouched.
setbyte(module+0x2c,1)
run(get(weather_table+35*16+4),(0x11,0x22,module+0x2c,0x44))
assert get(module+0x2c)==0xff821e01 and getbyte(module+0x69)==1
fp(cloud+0x30,.125,.25,.375)
run(jumps_from(0x897b45),(1,0,1800),registers={UC_X86_REG_EBX:module},cleanup=12)
color_test((30/255,130/255,1),1)
color_test((30/255,130/255,1),0)
color_test((.125,.25,.375),2)
setbyte(module+0x69,0)
run(jumps_from(0x897b45),(1,0,1800),registers={UC_X86_REG_EBX:module},cleanup=12)
color_test((.125,.25,.375),1)
setbyte(module+0x69,1)
run(jumps_from(0x897b45),(1,0,1800),registers={UC_X86_REG_EBX:module},cleanup=12)
def reset_resume():
    assert get(r(UC_X86_REG_ESP))==0
    w(UC_X86_REG_ESP,r(UC_X86_REG_ESP)+12)
    emu_return()
callbacks[0x719fe2]=reset_resume
run(jumps_from(0x719fdb),registers={UC_X86_REG_ECX:module})
color_test((.125,.25,.375),1)
assert getbyte(0x71a2fd)==5
xfer_ptr=aux+0x7000
xfer_stub=xfer_ptr+0x200
put(xfer_ptr,xfer_ptr+0x20)
put(xfer_ptr+0x20+0x78,xfer_stub)
def xfer_tint():
    assert r(UC_X86_REG_ECX)==xfer_ptr
    put(argument(1),0x01010203)
    emu_return(4)
callbacks[xfer_stub]=xfer_tint
def xfer(version):
    registers={UC_X86_REG_EBP:stack+8,UC_X86_REG_EDI:xfer_ptr}
    def xfer_setup():
        setbyte(stack+5,version)
    entry=jumps_from(0x71a3b7)
    callbacks[entry]=xfer_setup
    run(entry,(0,0,stop,0),registers=registers,check_stack=False)
    del callbacks[entry]
xfer(5)
color_test((3/255,2/255,1/255),1)
xfer(4)
color_test((.125,.25,.375),1)
print('CLOUDY parsing, reset, uncoloured casts, fade selection and old/new save blocks passed')

# Confirm the officialNecro production algebra and the template names on the actual result.
table=production.read_table(image)
money_type=table.index_of(image,'RESOURCE_PRODUCTION')
unit_type=table.index_of(image,'UNITS_PRODUCTION')
assert money_type!=unit_type and money_type>27 and unit_type>27
assert table.index_of(image,'PRODUCTION')==13
out=aux+0x8000
slot=aux+0x8800
kinds=[]
def modifier():
    kind=argument(1)
    kinds.append(kind)
    fp(argument(2),{13: 2.0,money_type:3.0,unit_type:4.0}[kind])
    emu_return(16,1)
callbacks[0x68c82d]=modifier
args=(13,out,0,1)
for entry in (0x89dc44,0x88559e,0x883c4d,0x8a4622):
    kinds.clear()
    assert run(jumps_from(entry),args,cleanup=16)==1 and kinds==[13,money_type]
    assert floats(out)[0]==6
for queue_kind in (1,2,3):
    kinds.clear()
    put(slot+4,queue_kind)
    assert run(jumps_from(0x8a1ed6),args,registers={UC_X86_REG_EBX:slot},cleanup=16)==1
    assert kinds==([13,unit_type] if queue_kind!=3 else [13])
    assert floats(out)[0]==(8 if queue_kind!=3 else 2)
print('All four resource sites, unit and upgrade queues, and vanilla hero queue branch passed')

# Exercise rank loss with a real banner slot. Native data signals that a
# banner's death destroys its horde, which must be skipped only on retirement.
horde=aux+0xa000
horde_module=aux+0xa800
horde_data=aux+0xb400
banner=aux+0xc000
tracker=aux+0xc800
rank_ref=aux+0xc900
put(tracker+0x34,horde)
put(horde_module+4,horde_data)
put(horde_module+0x11c,0xc5b1f8)
setbyte(horde_data+0x27c,1)
setbyte(horde_data+0x224,1)
put(horde_module+0x26c,7)
put(banner+0x27c,horde)
retired=[]
def tracker_set():
    rank=argument(1)
    put(r(UC_X86_REG_ECX)+0x24,rank)
    emu_return(4)
def horde_iface():
    assert r(UC_X86_REG_ECX)==horde
    emu_return(0,horde_module+0x11c)
def object_lookup():
    assert r(UC_X86_REG_ECX)==logic and argument(1)==7
    emu_return(4,banner)
def rank_resume():
    emu_return()
def kill_horde():
    emu_return(0,7)
def let_horde_live():
    emu_return(0,0)
def remove_banner():
    assert r(UC_X86_REG_ECX)==horde_module+0x11c and argument(1)==banner
    # Feed the removal handler its live EDX and EDI, preserving the actual stack.
    w(UC_X86_REG_EDX,banner)
    w(UC_X86_REG_EDI,horde_data)
    def branch_result(value):
        w(UC_X86_REG_EDI,banner)
        emu_return(4,value)
    callbacks[0x8719b5]=lambda: branch_result(0)
    callbacks[0x871959]=lambda: branch_result(7)
    w(UC_X86_REG_EIP,0x871950)
def destroy_banner():
    assert r(UC_X86_REG_ECX)==logic and argument(1)==banner
    assert r(UC_X86_REG_EAX)==0
    retired.append(banner)
    emu_return(4)
callbacks.update({0x79d72a:tracker_set,0x68c866:horde_iface,0x449681:object_lookup,
    0x87370b:remove_banner,0x62bbab:destroy_banner,0x79daec:rank_resume})
for old,new,count in [(2,3,0),(3,2,0),(2,1,1),(1,1,1)]:
    put(tracker+0x24,old)
    put(rank_ref,new)
    run(0x79dae3,registers={UC_X86_REG_ESI:tracker,UC_X86_REG_EDI:rank_ref})
    assert len(retired)==count and get(tracker+0x24)==new
callbacks[0x8719b5]=let_horde_live
callbacks[0x871959]=kill_horde
assert run(0x871950,registers={UC_X86_REG_EDI:horde_data,UC_X86_REG_EDX:banner})==7
print('Rank crossing, banner retirement and native combat banner death branch passed')

# Every upstream patch re-verifies its generated code against the final binary;
# the single native rank-set anchor is covered independently by the tests above.
normalized=bytearray(image)
anchor=file_offset(normalized,0x79dae3)
assert getbyte(0x79dae3)==0xe9
normalized[anchor:anchor+9]=bytes.fromhex('ff378bcee83efcffff')
for patch in (ProductionSplitPatch(),UpgradeModuleRemovalPatch(), ExperienceLevelDownPatch(),
              LevelGrantSpecialPowerPatch(),SpecialPowerPauseButtonPatch()):
    assert patch.verify(normalized)==[], (patch.name,patch.verify(normalized))
print('Final image passed all five upstream structural checks with the new banner hook accounted for')

# Direct verification of the additional .upg5k lookup from the level-down cave.
level=aux+0xe000
level_upgrades=aux+0xe300
upgrade=aux+0xe400
holder=aux+0xf000
xp_va=find_section(image,level_down.SECTION_NAME)[0]
remove=level_down._assemble(xp_va).label_va('remove')
put(level+0x4c,level_upgrades,level_upgrades+4)
put(level_upgrades,upgrade)
put(upgrade+4,1)
high_id=1151
put(upgrade+0x38,high_id)
calls=[]
has_high_upgrade=True
def read_extended_mask():
    assert [argument(i) for i in range(1,5)]==[
        holder+0x28c,high_id//32,1<<(high_id%32),0,
    ]
    emu_return(0,(1<<(high_id%32)) if has_high_upgrade else 0)
def remove_upgrade():
    assert r(UC_X86_REG_ECX)==holder
    assert argument(1)==upgrade
    calls.append(upgrade)
    emu_return(4)
callbacks.update({0xedf337:read_extended_mask,0x691438:remove_upgrade})
for present,expected_count in [(True,1),(False,1)]:
    has_high_upgrade=present
    run(remove,(level,),registers={UC_X86_REG_ECX:holder},cleanup=4)
    assert len(calls)==expected_count
put(upgrade+4,0)
has_high_upgrade=True
run(remove,(level,),registers={UC_X86_REG_ECX:holder},cleanup=4)
assert len(calls)==1
print('An extended index above 1087 uses the native lookup ABI and only removes an owned OBJECT upgrade')
```

</details>

```bash
python3 -m venv .venv
.venv/bin/python -m pip install unicorn pefile
PYTHONPATH=inspection/pysage-reference .venv/bin/python inspection/next/test_phase2.py
```
