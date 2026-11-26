# 01. Replenishing hordes with FilteredHordeRespawnBehavior

**Status:** Implemented. The reproducible build also includes items 04 and 05. Machine-code tests passed. An in-game ROTWK test is still pending.

## INI configuration

```ini
Behavior = FilteredHordeRespawnBehavior ModuleTag_FilteredHordeRespawn
    Radius = 180
    RespawnDelay = 5000
    ObjectFilter = NONE +ElvenLorienPikemanHorde SAME_PLAYER
    UpgradeRequired = Upgrade_EnableHordeReplenishment
    UnitSpawnFX = FX_BannerCarrierSpawnUnit
    ReplenishAllNearbyHordes = Yes
End
```

`ObjectFilter` applies to candidate objects in the search area. This example uses the horde template `ElvenLorienPikemanHorde`. Register `Upgrade_EnableHordeReplenishment` as an `OBJECT` upgrade and grant it to the object that owns the module through `GrantUpgradeCreate`. Substitute the relevant template and FX names for your mod.

## Engine changes

| Site | Change |
|---|---|
| ModuleData allocation at `0x00F3A20F` | Increase the size from `0x3C` to `0x40`. |
| Field table at `0x00F3A251` | `UnitSpawnFX` and `RespawnFXList` share the same parser and the field at `+0x34`. `UpgradeRequired` writes to `+0x24`, which the existing upgrade check reads. |
| `ReplenishAllNearbyHordes` | The Boolean at `+0x3C` defaults to `Yes`. With `No`, the loop stops after the first **successful** replenishment, even if it encounters full hordes first. |
| Spawn result | The replenishment routine reports whether it spawned a member. If an FX is configured, it plays on that new member. |

## Build requirements

The code was tested on a modified ROTWK 2.01.2614.37001 `game.dat` containing the `.wmfeat`, `.bldcap`, and `.upg5k` sections. Addresses refer to a PE32 image with base `0x00400000`. Binaries with the same displayed version can have different bytes. For a different executable, port the offsets and expected bytes before applying the patches.

The build uses Linux x86-64, Python 3.12, GNU binutils with i386 support, and Git. Create the subdirectories in a fresh working directory and place your copy of the original executable at `inspection/game.dat`. Run all commands from that working directory.

```bash
mkdir -p inspection/next
sha256sum inspection/game.dat
```

Check the input against this SHA-256:

```text
d2e8e4354c5f31376ce043a7240d34ee119c02b28d8af4af27bb153f4e605762
```

Save the following files at the paths shown. This first build pass adds the replenishment options, the healing filter, and the fix for repeated XP awards after health reaches zero. Use the executable from your own installation as the input.

<details>
<summary><code>inspection/inspect_pe.py</code></summary>

```python
from pathlib import Path
from struct import unpack_from, pack
from sys import argv
img = Path('inspection/game.dat').read_bytes()
u16 = lambda off: unpack_from('<H',img,off)[0]
u32 = lambda off: unpack_from('<I',img,off)[0]
pe = u32(0x3c)
sections = [unpack_from('<8s6I2HI',img,i) for i in range(pe+24+u16(pe+20),pe+24+u16(pe+20)+40*u16(pe+6),40)]
def va(o):
    for _,_,rva,size,raw,*_ in sections:
        if raw <= o < raw+size:
            return rva+0x400000+o-raw
    return o
def off(a):
    for _,_,rva,size,raw,*_ in sections:
        if rva+0x400000 <= a < rva+0x400000+size:
            return a-0x400000-rva+raw
    raise ValueError(hex(a))
def zstr(a):
    try:
        o=off(a)
        v=img[o:img.index(0,o)]
        return v.decode('ascii') if 0<len(v)<90 and all(32<=n<127 for n in v) else ''
    except (ValueError,UnicodeError):
        return ''
def matches(p):
    o=0
    while (o:=img.find(p,o))!=-1:
        yield va(o)
        o+=1
def xrefs(a):
    return list(matches(pack('<I',a)))
if __name__=='__main__':
    for arg in argv[1:]:
        if arg.startswith('@'):
            a,n=(arg[1:]+':20').split(':')[:2]
            a=int(a,16)
            for addr in range(a,a+int(n,16),4):
                v=u32(off(addr))
                print(f'{addr:08x}: {v:08x} {zstr(v)}')
        elif arg.startswith('0x'):
            a=int(arg,16)
            print(arg, ' '.join(f'{x:08x}' for x in xrefs(a)))
        else:
            for a in matches(arg.encode()+b'\0'):
                if off(a)>0 and img[off(a)-1] not in (0,0xcc):
                    continue
                print(arg, f'{a:08x}', ' '.join(f'{x:08x}' for x in xrefs(a)))
```

</details>

<details>
<summary><code>inspection/engine_patch.s</code></summary>

```asm
.intel_syntax noprefix
.section .text
.code32

# Extend the data for the filtered module without moving any existing fields.
filtered_init:
    mov dword ptr [esi+0x38], 0
    mov dword ptr [esi+0x3c], 1
    jmp 0xf3a233

filtered_candidate:
    cmp dword ptr [ebx-0x24], 0xf3a578
    jne filtered_stock
    mov eax, [ebx-0x20]
    cmp dword ptr [eax+0x38], 0
    je filtered_next
    push dword ptr [eax+0x34]
    mov ecx, edi
    call 0xf3a2c7
    test eax, eax
    je filtered_next
    mov eax, [ebx-0x20]
    cmp byte ptr [eax+0x3c], 0
    jne filtered_next
    jmp 0x888065
filtered_stock:
    jmp 0xf3a2ba
filtered_next:
    jmp 0x888056

filtered_spawn_ok:
    mov eax, [esp+0x10]
    test eax, eax
    jz filtered_spawn_report
    push 0
    push esi
    push eax
    call 0x4b1b5a
    add esp, 12
filtered_spawn_report:
    mov eax, 1
    jmp filtered_spawn_return

filtered_spawn_miss:
    xor eax, eax
filtered_spawn_return:
    pop edi
    pop esi
    pop ebx
    ret 4

.balign 4
filtered_fields:
    .long 0x00be3610, 0x0042ed00, 0, 0x08  # Radius
    .long 0x00f3a4da, 0x0073a429, 0, 0x10  # RespawnDelay
    .long 0x00bf2b7c, 0x00f3a25b, 0, 0x20  # ObjectFilter
    .long 0x00c09e60, 0x0073a302, 0, 0x34  # RespawnFXList
    .long 0x00c66000, 0x0073a302, 0, 0x34  # UnitSpawnFX, alias
    .long 0x00c06988, 0x0042ee5e, 0, 0x24  # UpgradeRequired, existing update gate
    .long 0x00c65fcc, 0x0042e558, 0, 0x3c  # ReplenishAllNearbyHordes
    .long 0, 0, 0, 0

# PlayerHealSpecialPower holds a native ObjectFilter handle and an explicit presence flag.
heal_init:
    mov dword ptr [esi+0xac], -1
    mov dword ptr [esi+0xb0], 0
    pop edi
    mov eax, esi
    pop esi
    ret

heal_destroy:
    push ecx
    lea ecx, [ecx+0xac]
    call 0x7629b0
    pop ecx
    jmp 0x8cc1d7

heal_parse_filter:
    push esi
    mov esi, [esp+0x10]
    push dword ptr [esp+0x14]
    push esi
    push dword ptr [esp+0x14]
    push dword ptr [esp+0x14]
    call 0x76392f
    add esp, 16
    mov byte ptr [esi+4], 1
    pop esi
    ret

heal_filter_target:
    cmp byte ptr [edi+0xb0], 0
    jne heal_use_acceptance_filter
    lea eax, [edi+0x88]
    push eax
    mov ecx, esi
    call 0x70c548
    jmp 0x8cc3a7

heal_use_acceptance_filter:
    push dword ptr [ebx+0x08]
    push esi
    lea ecx, [edi+0xac]
    call 0x7640c1
    jmp 0x8cc3a7

.balign 4
heal_fields:
    .long 0x00c74eb4, 0x0042ed00, 0, 0x7c  # HealAmount
    .long 0x00c74ea4, 0x0042e558, 0, 0x80  # HealAsPercent
    .long 0x00c74e98, 0x006564e7, 0, 0x88  # HealAffects
    .long 0x00c74e8c, 0x0042ed00, 0, 0x84  # HealRadius
    .long 0x00c60b04, 0x0073a302, 0, 0xa4  # HealFX
    .long 0x00c74e84, 0x0073a368, 0, 0xa8  # HealOCL
    .long 0x00c73524, heal_parse_filter, 0, 0xac
    .long 0, 0, 0, 0

# A zero health delta returns early in DelayedDeathBody. Record the current
# health as the previous health so the damage processor does not re-use a
# previous hit's health loss to grant experience and power points.
delayed_death_zero_delta:
    jp delayed_death_continue
    mov eax, [esi+8]
    mov [esi+0x0c], eax
    jmp 0x8c567a
delayed_death_continue:
    jmp 0x8c5564
```

</details>

<details>
<summary><code>inspection/build_patch.py</code></summary>

```python
from hashlib import sha256
from pathlib import Path
from struct import pack, pack_into
import subprocess

from inspect_pe import img, off, pe, sections, u16, u32

scratch = Path('inspection')
section_rva = u32(pe+24+56)
section_address = 0x400000 + section_rva
assert section_rva == 0xb8f000
assert sections[-1][2] + ((sections[-1][1] + 0xfff) & ~0xfff) == section_rva
subprocess.run(['as','--32','-o',scratch/'engine_patch.o',scratch/'engine_patch.s'],check=True)
subprocess.run(['ld','-m','elf_i386','-e','0','-Ttext',hex(section_address),'-o',scratch/'engine_patch.elf',scratch/'engine_patch.o'],check=True)
subprocess.run(['objcopy','-O','binary','-j','.text',scratch/'engine_patch.elf',scratch/'engine_patch.bin'],check=True)
symbols = {row.split()[-1]:int(row.split()[0],16) for row in subprocess.check_output(['nm',scratch/'engine_patch.elf'],text=True).splitlines()}

data = bytearray(img)
edits = {}
def patch(address, original, replacement):
    original = bytes.fromhex(original)
    assert len(original) == len(replacement)
    offset = off(address)
    assert data[offset:offset+len(original)] == original, hex(address)
    data[offset:offset+len(original)] = replacement
    edits[address] = len(original)

def hook(address, original, destination):
    length = len(bytes.fromhex(original))
    target = symbols[destination]
    patch(address, original, b'\xe9'+pack('<i',target-address-5)+b'\x90'*(length-5))

def pointer(address, original, destination):
    patch(address, original, pack('<I', symbols[destination]))

patch(0xf3a20f, '3c', b'\x40')
hook(0xf3a22c, 'c7 46 38 00 00 00 00', 'filtered_init')
pointer(0xf3a251, '54 a4 f3 00', 'filtered_fields')
hook(0xf3a299, '81 7b dc 78 a5 f3 00', 'filtered_candidate')
hook(0xf3a332, '8b 44 24 10 85 c0', 'filtered_spawn_ok')
hook(0xf3a346, '5f 5e 5b c2 04 00', 'filtered_spawn_miss')

patch(0x652371, 'ac 00 00 00', pack('<I', 0xb4))
hook(0x8cc4af, '5f 8b c6 5e c3', 'heal_init')
pointer(0xc74de8, 'd7 c1 8c 00', 'heal_destroy')
pointer(0x8cc293, 'c0 4e c7 00', 'heal_fields')
hook(0x8cc399, '8d 87 88 00 00 00', 'heal_filter_target')

hook(0x8c555e, '0f 8b 16 01 00 00', 'delayed_death_zero_delta')

section = (scratch/'engine_patch.bin').read_bytes()
raw_alignment = u32(pe+24+36)
image_alignment = u32(pe+24+32)
def align(size, boundary):
    return (size+boundary-1)//boundary*boundary
raw_size = align(len(section),raw_alignment)
header = pe+24+u16(pe+20)+len(sections)*40
assert data[header:header+40] == bytes(40)
assert len(img) % raw_alignment == 0
assert len(img) == sections[-1][3] + sections[-1][4]
pack_into('<8s6I2HI',data,header,b'.modext1',len(section),section_rva,raw_size,len(img),0,0,0,0,0x60000020)
pack_into('<H',data,pe+6,len(sections)+1)
pack_into('<I',data,pe+24+4,u32(pe+24+4)+raw_size)
pack_into('<I',data,pe+24+56,section_rva+align(len(section),image_alignment))
data.extend(section.ljust(raw_size,b'\0'))
(scratch/'game_patched.dat').write_bytes(data)
print('Original',sha256(img).hexdigest())
print('Patched ',sha256(data).hexdigest())
print('Patch sites',', '.join(f'{address:x}+{count}' for address,count in edits.items()))
```

</details>

```bash
printf '%s  %s\n' d2e8e4354c5f31376ce043a7240d34ee119c02b28d8af4af27bb153f4e605762 inspection/game.dat | sha256sum -c -
python3 inspection/build_patch.py
printf '%s  %s\n' c0aa39df31adbacc76bad5cc957a4834378eb004a8a18d9babb3f18abef5eef9 inspection/game_patched.dat | sha256sum -c -
```

The script writes `inspection/game_patched.dat`. For the remaining implemented changes, save the files from [02](cloudy-darkening-factor.md) and [03](phantom-structure-check.md), then follow the [full build in 10](negative-experience.md).

## In-game verification

1. Bring two depleted hordes under the same player to the object with the module. Add a full horde nearby.
2. Grant the required upgrade. Check that `Yes` replenishes both depleted hordes in one pass and that `No` stops after the first successful replenishment.
3. Check that the FX plays on the new member. Repeat with a module owner that lacks the required upgrade and confirm that no members spawn.

## Repeating the first-pass machine-code tests

This optional test runs the patch in a Linux x86-64 process with 32-bit compatibility mode. Stubs stand in for external engine calls. The test covers replenishment and its FX, healing filter selection, and the zero-health-delta case. Save these files and build the test after completing the first pass.

<details>
<summary><code>inspection/compat_run.c</code></summary>

```c
#define _GNU_SOURCE
#include <elf.h>
#include <signal.h>
#include <ucontext.h>
#include <fcntl.h>
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>

extern int enter32(uint32_t entry, uint32_t stack);
extern void return64(void);
uintptr_t saved_sp;

static void inspect_crash(int sig, siginfo_t *info, void *ptr) {
    ucontext_t *context = ptr;
    greg_t *r = context->uc_mcontext.gregs;
    dprintf(2, "signal %d fault=%p ip=%llx sp=%llx bp=%llx eax=%llx bx=%llx cs=%llx\n",sig,info->si_addr,r[REG_RIP],r[REG_RSP],r[REG_RBP],r[REG_RAX],r[REG_RBX],r[REG_CSGSFS]);
    _exit(220);
}

int main(int argc, char **argv) {
    static char alternate[65536];
    stack_t alt = { .ss_sp=alternate, .ss_size=sizeof alternate };
    sigaltstack(&alt,0);
    struct sigaction action = {.sa_sigaction=inspect_crash,.sa_flags=SA_ONSTACK|SA_SIGINFO};
    sigaction(SIGSEGV, &action, 0);
    sigaction(SIGILL, &action, 0);
    sigaction(SIGBUS, &action, 0);
    if (argc != 2) return 200;
    int fd = open(argv[1], O_RDONLY);
    Elf32_Ehdr header;
    if (fd < 0 || read(fd, &header, sizeof header) != sizeof header) return 201;
    for (int i = 0; i < header.e_phnum; ++i) {
        Elf32_Phdr ph;
        if (pread(fd, &ph, sizeof ph, header.e_phoff + i * sizeof ph) != sizeof ph) return 202;
        if (mmap((void *)(uintptr_t)ph.p_vaddr, ph.p_memsz, PROT_READ | PROT_WRITE | PROT_EXEC,
            MAP_PRIVATE | MAP_FIXED_NOREPLACE, fd, ph.p_offset) == MAP_FAILED) return 203;
    }
    char *bridge = mmap((void *)0x3000000, 4096, PROT_READ | PROT_WRITE | PROT_EXEC,
        MAP_ANON | MAP_PRIVATE | MAP_FIXED_NOREPLACE, -1, 0);
    if (bridge == MAP_FAILED) return 204;
    const unsigned char jump[] = {0x48, 0xb8, 0,0,0,0,0,0,0,0, 0xff, 0xe0};
    memcpy(bridge, jump, sizeof jump);
    uintptr_t label = (uintptr_t)return64;
    memcpy(bridge+2, &label, sizeof label);
    char *stack = mmap(NULL, 65536, PROT_READ | PROT_WRITE,
        MAP_ANON | MAP_PRIVATE | MAP_32BIT, -1, 0);
    if (stack == MAP_FAILED) return 205;
    return enter32(header.e_entry, (uintptr_t)(stack + 65520));
}
```

</details>

<details>
<summary><code>inspection/compat_run.s</code></summary>

```asm
.intel_syntax noprefix
.text
.global enter32
.global return64
enter32:
    push rbx
    push rbp
    mov [rip+saved_sp], rsp
    mov esp, esi
    mov ax, 0x2b
    mov ds, ax
    mov es, ax
    push 0x23
    push rdi
    retfq
return64:
    mov rsp, [rip+saved_sp]
    mov eax, ebx
    pop rbp
    pop rbx
    ret
.section .note.GNU-stack,"",@progbits
```

</details>

<details>
<summary><code>inspection/test_patch.py</code></summary>

```python
from pathlib import Path
from struct import pack_into, unpack_from
import subprocess

from inspect_pe import u16, img, off, sections

folder = Path('inspection')
patched = bytearray((folder/'game_patched.dat').read_bytes())
def run(*args):
    return subprocess.check_output(args, text=True)
def nm(file):
    return {row.split()[-1]: int(row.split()[0],16) for row in run('nm',file).splitlines()}
patch_names = nm(folder/'engine_patch.elf')
(folder/'test_symbols.inc').write_text(f".equ TEST_HEAL_PARSE, {patch_names['heal_parse_filter']:#x}\n")
run('as','--32','-o',folder/'test_patch.o',folder/'test_patch.s')
base = 0x2000000
run('ld','-m','elf_i386','-e','_start','-Ttext',hex(base),'-o',folder/'test_patch.elf',folder/'test_patch.o')
run('objcopy','-O','binary','-j','.text',folder/'test_patch.elf',folder/'test_patch.bin')
test_names = nm(folder/'test_patch.elf')
test_bytes = (folder/'test_patch.bin').read_bytes()
stubs = {
    0xf3a233:'filtered_init_done',
    0x44ddec:'active_horde',
    0x68c866:'find_horde_interface',
    0x68c7e9:'member_init',
    0x4b1b5a:'fx',
    0x888056:'filtered_continue',
    0x888065:'filtered_stop',
    0x70c548:'legacy_heal',
    0x7640c1:'filtered_heal',
    0x76392f:'heal_parsed_fields',
    0x8cc3a7:'heal_target_done',
    0x8c567a:'delayed_zero',
    0x8c5564:'delayed_continue',
}
for address,name in stubs.items():
    location = off(address)
    patched[location] = 0xe9
    pack_into('<i',patched,location+1,test_names[name]-address-5)

def section_data(address):
    sec = next(s for s in sections if 0x400000+s[2] == address)
    return bytes(patched[sec[4]:sec[4]+sec[3]])
span = lambda name,size: bytes(patched[len(img):len(img)+size])
segments = [(0x401000,section_data(0x401000)),
            (0xf3a000,section_data(0xf3a000)),
            (0xf8f000,span('.modext1',0x1000)),
            (base,test_bytes)]
elf = bytearray(0x1000)
elf[:16] = b'\x7fELF\x01\x01\x01'+b'\0'*9
pack_into('<HHIIIIIHHHHHH',elf,16,2,3,1,test_names['_start'],52,0,0,52,32,len(segments),0,0,0)
for index,(address,content) in enumerate(segments):
    elf.extend(b'\0'*(-len(elf)%0x1000))
    pack_into('<IIIIIIII',elf,52+index*32,1,len(elf),address,address,len(content),len(content),7,0x1000)
    elf.extend(content)
runner = folder/'test_patch.run'
runner.write_bytes(elf)
runner.chmod(0o700)
result = subprocess.run([folder/'compat_run',runner])
assert result.returncode == 0, f'Unexpected outcome in check {result.returncode}'
print('12 native x86 checks passed with engine calls stubbed')
```

</details>

<details>
<summary><code>inspection/test_patch.s</code></summary>

```asm
.intel_syntax noprefix
.code32
.text
.global _start
.include "inspection/test_symbols.inc"

.macro same lhs, rhs
    cmp \lhs, \rhs
    jne fail
.endm

_start:
    mov ebp, 11
    mov esi, offset filtered_data
    call 0xf3a22c
    same "dword ptr [filtered_data+0x38]", "0"
    same "dword ptr [filtered_data+0x3c]", "1"

    mov ebp, 12
    mov ebx, offset filtered_object+0x24
    mov edi, offset target
    call 0xf3a299
    same "eax", "1"
    same "dword ptr [spawn_count]", "0"

    mov ebp, 13
    mov dword ptr [filtered_data+0x38], 1
    call 0xf3a299
    same "eax", "1"
    same "dword ptr [spawn_count]", "1"
    same "dword ptr [fx_count]", "1"

    mov ebp, 14
    mov byte ptr [filtered_data+0x3c], 0
    call 0xf3a299
    same "eax", "2"
    same "dword ptr [spawn_count]", "2"
    same "dword ptr [fx_count]", "2"

    mov ebp, 15
    mov dword ptr [target+0x458], 1
    call 0xf3a299
    same "eax", "1"
    same "dword ptr [spawn_count]", "2"
    same "dword ptr [fx_count]", "2"

    mov ebp, 16
    mov esi, offset heal_data
    call initialize_heal
    same "eax", "esi"
    same "dword ptr [heal_data+0xac]", "-1"
    same "dword ptr [heal_data+0xb0]", "0"

    mov ebp, 17
    mov edi, offset heal_data
    mov esi, offset target
    mov ebx, offset heal_context
    call 0x8cc399
    same "eax", "1"
    same "dword ptr [legacy_count]", "1"
    same "dword ptr [filter_count]", "0"

    mov ebp, 18
    push 0x202
    push offset heal_data+0xac
    push 0x201
    push 0x200
    call TEST_HEAL_PARSE
    add esp,16
    same "byte ptr [heal_data+0xb0]", "1"
    same "dword ptr [heal_data+0xac]", "42"

    mov ebp, 19
    call 0x8cc399
    same "eax", "0"
    same "dword ptr [legacy_count]", "1"
    same "dword ptr [filter_count]", "1"

    mov ebp, 20
    mov byte ptr [filter_result], 1
    call 0x8cc399
    same "eax", "1"
    same "dword ptr [legacy_count]", "1"
    same "dword ptr [filter_count]", "2"

    mov ebp, 21
    mov esi, offset health_data
    mov eax, 0x40
    test al, 0x44
    call 0x8c555e
    same "eax", "1"
    same "dword ptr [health_data+0xc]", "0"

    mov ebp, 22
    mov dword ptr [health_data+0xc], 0x40000000
    mov eax, 0
    test al, 0x44
    call 0x8c555e
    same "eax", "0"
    same "dword ptr [health_data+0xc]", "0x40000000"

    xor ebx,ebx
    jmp finish
fail:
    mov ebx, ebp
finish:
    push 0x33
    push 0x3000000
    retf

initialize_heal:
    push esi
    push edi
    jmp 0x8cc4af
active_horde:
    mov eax, 0
    ret 4
find_horde_interface:
    same "ecx", "offset target"
    mov eax, offset horde_interface
    ret
horde_capacity:
    mov eax, 10
    ret
horde_size:
    mov eax, 9
    ret
respawn_member:
    mov eax, [esp+4]
    same "eax", "offset target+8"
    inc dword ptr [spawn_count]
    mov eax, offset member
    ret 4
member_init:
    same "ecx", "offset member"
    ret
fx:
    same "dword ptr [esp+4]", "0xd4"
    same "dword ptr [esp+8]", "offset member"
    same "dword ptr [esp+12]", "0"
    inc dword ptr [fx_count]
    ret
filtered_continue:
    mov eax, 1
    ret
filtered_stop:
    mov eax, 2
    ret
filtered_init_done:
    ret
legacy_heal:
    same "ecx", "offset target"
    same "dword ptr [esp+4]", "offset heal_data+0x88"
    inc dword ptr [legacy_count]
    mov eax, 1
    ret 4
filtered_heal:
    same "ecx", "offset heal_data+0xac"
    same "dword ptr [esp+4]", "offset target"
    same "dword ptr [esp+8]", "offset filtered_object"
    inc dword ptr [filter_count]
    movzx eax, byte ptr [filter_result]
    ret 8
heal_parsed_fields:
    same "dword ptr [esp+4]", "0x200"
    same "dword ptr [esp+8]", "0x201"
    same "dword ptr [esp+12]", "offset heal_data+0xac"
    same "dword ptr [esp+16]", "0x202"
    mov dword ptr [heal_data+0xac], 42
    ret
heal_target_done:
    movzx eax, al
    ret
delayed_zero:
    mov eax, 1
    ret
delayed_continue:
    xor eax, eax
    ret

.balign 4
filtered_object:
    .long 0xf3a578, filtered_data
    .space 0x20
filtered_data:
    .space 0x34
    .long 0xd4, -1, -1
target:
    .long 0, target_template
    .space 0x454
target_template:
    .space 0x115
    .byte 0x20
horde_interface:
    .long horde_vtable
horde_vtable:
    .space 0x17c
    .long horde_capacity
    .space 8
    .long horde_size, respawn_member
member:
    .long 0
heal_data:
    .space 0xac
    .long 32, 42
heal_context:
    .long 0, heal_data, filtered_object
health_data:
    .long 0, 0, 0, 0x43c80000
spawn_count:
    .long 0
fx_count:
    .long 0
legacy_count:
    .long 0
filter_count:
    .long 0
filter_result:
    .byte 0
```

</details>

```bash
gcc -O2 -o inspection/compat_run inspection/compat_run.c inspection/compat_run.s
python3 inspection/test_patch.py
```

The expected output is `12 native x86 checks passed with engine calls stubbed`.
