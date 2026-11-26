# 09. Worker harvest and warehouse filters

`WorkerAIUpdate` can filter resource sources and drop-off buildings by their `KindOf` tags. The patch uses the same rules for automatic searches and manual orders. All four fields are optional. A worker with none of the new fields uses the native gathering rules.

## INI configuration

Keep the new fields inside the worker's existing `Behavior = WorkerAIUpdate ... End` block. The stone and wood examples use the same fields available to every object that uses `WorkerAIUpdate`. A builder that uses `DozerAIUpdate` needs a worker gathering setup before it can use these fields.

| Field | Accepted values | Effect |
| --- | --- | --- |
| `HarvestKindOf` | Space-separated `KindOf` tags | Require at least one matching tag on a source. |
| `WarehouseKindOf` | Space-separated `KindOf` tags | Require at least one matching tag on a drop-off building. |
| `ForbiddenHarvestKindOf` | Space-separated `KindOf` tags | Reject a source with any listed tag. |
| `ForbiddenWarehouseKindOf` | Space-separated `KindOf` tags | Reject a drop-off building with any listed tag. |

A matching exclusion takes precedence. Use `NONE` to clear an inherited list. The fields accept existing `KindOf` tags and the resource tags below.

| Resource | Source tag | Drop-off tag |
| --- | --- | --- |
| Stone | `HARVEST_STONE` | `STONE_WAREHOUSE` |
| Wood | `HARVEST_TREE` | `TREE_WAREHOUSE` |
| Meat | `HARVEST_MEAT` | `MEAT_WAREHOUSE` |
| Fish | `HARVEST_FISH` | `FISH_WAREHOUSE` |

### Stone worker

In `data/ini/object/goodfaction/units/arnor/new/arnorharvester.ini`, add the two filter fields to `ArnorHarvester`. This is the full module block from the example, with comments removed.

```ini
Behavior = WorkerAIUpdate ModuleTag_10
    BoredTime = 4000
    BoredRange = 120
    SpecialContactPoints = Repair
    MaxBoxes = 1
    SupplyWarehouseScanDistance = 8000
    SupplyCenterActionDelay = 200
    SupplyWarehouseActionDelay = 2500
    HarvestTrees = No
    HarvestKindOf = HARVEST_STONE
    WarehouseKindOf = STONE_WAREHOUSE
    HarvestActivationRange = 20
    HarvestPreparationTime = 6000
    HarvestActionTime = 5000
    AILuaEventsList = InfantryFunctions
End
```

### Wood worker

In `data/ini/object/evilfaction/units/mordor/worker.ini`, add the two exclusion fields to `MordorWorker`.

```ini
Behavior = WorkerAIUpdate ModuleTag_10
    BoredTime = 6000
    BoredRange = 120
    SpecialContactPoints = Repair
    MaxBoxes = 1
    SupplyWarehouseScanDistance = 5000
    SupplyCenterActionDelay = 3000
    HarvestTrees = Yes
    ForbiddenHarvestKindOf = HARVEST_STONE HARVEST_MEAT
    ForbiddenWarehouseKindOf = STONE_WAREHOUSE MEAT_WAREHOUSE
    SupplyWarehouseActionDelay = -1
    HarvestActivationRange = 25
    HarvestPreparationTime = 7500
    HarvestActionTime = 4500
    AILuaEventsList = LumbermillWorkerFunctions
End
```

`HarvestTrees = Yes` enables the native search for trees on the map. That path matches both `TREE` and `HARVEST_TREE`. To restrict a wood worker to wood, also set `HarvestKindOf = HARVEST_TREE` and `WarehouseKindOf = TREE_WAREHOUSE`.

### Resource objects and drop-off buildings

The five example INIs live under `data/ini/object`. The two worker definitions above are accompanied by these three object edits.

| File | Object | Edit |
| --- | --- | --- |
| `neutral/SupplyRocks.ini` | `SupplyRocksPile01` and the other stone deposits | Append `HARVEST_STONE` to each existing `KindOf` list. |
| `goodfaction/structures/arnor/new/stoneworkerMod.ini` | `ArnorStoneworkerMod` | Append `STONE_WAREHOUSE` to the existing `KindOf` list. |
| `evilfaction/structures/mordor/mordorlumbermill.ini` | `MordorLumberMill`, `MordorLumberMillMod`, and `MordorLumberMillModAI` | Add `KindOf = +TREE_WAREHOUSE` to each child object. The `+` preserves the tags inherited from `LumberMill`. |

For example, the first deposit's full flag line becomes the following.

```ini
KindOf = STRUCTURE IMMOBILE SELECTABLE SUPPLY_SOURCE_ON_PREVIEW IGNORED_IN_GUI NO_COLLIDE SUPPLY_SOURCE HARVEST_STONE
```

Keep the native supply behaviors. A docked source uses `SupplyWarehouseDockUpdate` to supply boxes. A drop-off building uses `SupplyCenterDockUpdate` to receive them. The INI filter names follow the player's view of sources and warehouses. Existing dependencies such as supply registration and approach points still apply. To add fish or meat, start from an existing docked source and receiving building, then apply the corresponding tags. All deliveries credit the normal treasury.

An `Unknown field ... in block 'Object'` error points to the outer scope. Place the field above the `End` of the existing `WorkerAIUpdate` block and run the patched `game.dat` so that module can parse it.

## Engine implementation

The native field table has twelve entries. The builder retains all twelve, adds four masks at module offsets `0x94`, `0xB4`, `0xD4`, and `0xF4`, then redirects the table pointer at `0x0064EF92`. The allocation grows from `0x94` to `0x114` and the constructor clears the new fields.

Each filter mask contains seven native words and a separate resource word. The object template gets a resource word at `+0x650`, zeroed on creation and copied with the template. The field parser at `0x00DA414C` and the worker field handlers use the native token parser for existing names. They capture the new tokens in the extra word while preserving full-list replacement and relative `+` or `-` edits. This keeps the base `KindOf` indices and mask width intact.

| Hook or pointer | Use |
| --- | --- |
| `0x0082C666`, `0x0082C6C6` | Filter pickup and drop-off after the native supply dock lookup. The search can continue to the next candidate after a rejection. |
| `0x0082C786` | Check the manual docking fallback before it can accept an excluded target. |
| `0x00C6ACA8 + 4 * 51`, `+ 4 * 52` | Filter the worker's direct dock and coordinate harvest orders. |
| `0x00C6ABE0` | Apply the source filter to terrain trees during automatic search. |

The native availability, relationship, distance and transfer checks still apply. The two reference workers keep their existing timings and use the same gathering system.

## Build the patched game.dat

Use Python 3, GCC with i386 support, GNU binutils, and the [pinned pySAGE checkout](https://github.com/ClementJ18/pySAGE/tree/0a1f1b5d71b1b080008a7e9fff6f997601ec5a7f). Save the three listings below together. The supported input is the reference output of [13. Random Teams](../multiplayer/random-teams.md#build-the-patched-gamedat). The builder checks the input digest and all overwritten bytes.

| File | Reference SHA-256 |
| --- | --- |
| Input `game.dat` | `9518fa33d00580cee50e735fe7141e24796d37d6ce9560b85e74dcd45cbb5828` |
| Output with GCC 14.2.0 and GNU binutils 2.44 | `4d9e7bbe44766173fcb81f53cbf712da9cd4c3e74b43beec29f643d17cf97400` |

```bash
PYTHONPATH=pySAGE python3 build_harvest_filters.py game.dat game_with_harvest_filters.dat
```

Use the output as `game.dat` for testing. Apply the INI edits at the paths shown. If you package them as a BIG overlay, keep the original internal paths and give the overlay precedence over the source BIG.

## Verify in game

1. Place a stone deposit and trees near the two workers. Check that the stone worker chooses stone and the wood worker ignores stone even when it is closer.
2. Check deliveries to the stone yard and lumber mill. Issue manual orders for both permitted and excluded targets.
3. Exhaust the nearest deposit and check that the worker finds another eligible source. Destroy the preferred drop-off building and check that delivery uses the next eligible one.
4. Repeat with a worker that omits the fields. Check an inherited definition with an additional tag prefixed by `+`.

The packaged x86 routines, native parser calls, and automatic and manual target checks were exercised in emulation. A full Windows match is pending.

[Worker module field reference](https://github.com/ClementJ18/pySAGE/blob/0a1f1b5d71b1b080008a7e9fff6f997601ec5a7f/sage_patch/docs/module-reference.md#workeraiupdate) · [BFME II worker implementation](https://github.com/Open-BFME/Open-BFME-2/blob/e2e99959950e6eebfe1ced5663aa05de320afc52/Code/GameEngine/Source/GameLogic/Object/Update/AIUpdate/WorkerAIUpdateCtor.cpp)

## Build sources

<details>
<summary><code>harvest_filters.c</code></summary>

```c
typedef unsigned int Word;
typedef unsigned char Byte;
#define THISCALL __attribute__((thiscall))
#define READ_PTR(object, offset) (*(void *const *)((const Byte *)(object) + (offset)))
#define READ_WORD(object, offset) (*(const Word *)((const Byte *)(object) + (offset)))

enum {
    NativeKinds = 7,
    TemplateKindsOffset = 0x108,
    TemplateResourceKindsOffset = 0x650,
    WorkerAIDataVTable = 0xc086d8,
    WorkerDataFiltersOffset = 0x94,
    HarvestTree = 1 << 1,
    NativeTree = 94
};

struct KindMask {
    Word native[NativeKinds];
    Word resource;
};

struct WorkerFilters {
    struct KindMask harvest;
    struct KindMask warehouse;
    struct KindMask forbidden_harvest;
    struct KindMask forbidden_warehouse;
};

typedef void (ParseField)(void *, void *, void *, const void *);
typedef Byte (THISCALL ParseToken)(Word *, const char *, Byte *, Byte *);
typedef void *(THISCALL FindModule)(const void *, Word);
typedef Word (THISCALL NameToKey)(void *, const char *);
typedef void (THISCALL WorkerCommand)(void *, const void *, int);

#ifndef FILTERS_TEST
#define native_parse_field ((ParseField *)0x6564e7)
#define native_parse_token ((ParseToken *)0x655b0b)
#define native_find_module ((FindModule *)0x68bda5)
#define native_name_to_key ((NameToKey *)0x5487ec)
#define native_worker_dock ((WorkerCommand *)0x8ace4a)
#define native_worker_harvest ((WorkerCommand *)0x8ace75)
#define name_key_generator (*(void **)0xdd90e4)
#else
extern ParseField native_parse_field;
extern ParseToken native_parse_token;
extern FindModule native_find_module;
extern NameToKey native_name_to_key;
extern WorkerCommand native_worker_dock;
extern WorkerCommand native_worker_harvest;
extern void *name_key_generator;
#endif

static Word *extra_parse_mask;

static const char *const resources[] = {
    "HARVEST_STONE", "HARVEST_TREE", "HARVEST_MEAT", "HARVEST_FISH",
    "STONE_WAREHOUSE", "TREE_WAREHOUSE", "MEAT_WAREHOUSE", "FISH_WAREHOUSE"
};

static Byte equal_token(const char *token, const char *upper)
{
    while (*token) {
        char letter = *token++;
        if (letter >= 'a' && letter <= 'z')
            letter -= 'a' - 'A';
        if (letter != *upper++)
            return 0;
    }
    return *upper == 0;
}

static Word find_resource_bit(const char *token)
{
    for (unsigned i = 0; i < sizeof(resources) / sizeof(resources[0]); ++i)
        if (equal_token(token, resources[i]))
            return 1u << i;
    return 0;
}

static void parse_with_resource_mask(void *ini, void *object, Word *native, Word *extra)
{
    Word *previous = extra_parse_mask;
    extra_parse_mask = extra;
    native_parse_field(ini, object, native, 0);
    extra_parse_mask = previous;
}

void parse_object_kinds(void *ini, void *object, void *store, const void *unused)
{
    (void)unused;
    Byte *template = (Byte *)store - TemplateKindsOffset;
    parse_with_resource_mask(ini, object, store, (Word *)(template + TemplateResourceKindsOffset));
}

void parse_worker_mask(void *ini, void *object, void *store, const void *unused)
{
    (void)unused;
    struct KindMask *mask = store;
    parse_with_resource_mask(ini, object, mask->native, &mask->resource);
}

Byte THISCALL parse_kind_token(Word *mask, const char *token, Byte *assigned, Byte *modified)
{
    if (!extra_parse_mask)
        return native_parse_token(mask, token, assigned, modified);

    char prefix = *token;
    Byte relative = prefix == '+' || prefix == '-';
    Word resource = find_resource_bit(token + relative);
    if (!resource) {
        if (!relative && !*modified && (!*assigned || equal_token(token, "NONE")))
            *extra_parse_mask = 0;
        return native_parse_token(mask, token, assigned, modified);
    }

    if ((relative && *assigned) || (!relative && *modified))
        return native_parse_token(mask, token, assigned, modified);

    if (relative) {
        if (prefix == '+')
            *extra_parse_mask |= resource;
        else
            *extra_parse_mask &= ~resource;
        *modified = 1;
    } else {
        if (!*assigned) {
            for (unsigned i = 0; i < NativeKinds; ++i)
                mask[i] = 0;
            *extra_parse_mask = 0;
        }
        *extra_parse_mask |= resource;
        *assigned = 1;
    }
    return 1;
}

static Byte permits(const struct KindMask *allow, const struct KindMask *deny,
                    const Word *native, Word resource)
{
    Word allowed_kinds = allow->resource;
    Word intersection = allowed_kinds & resource;
    Word forbidden = deny->resource & resource;
    for (unsigned i = 0; i < NativeKinds; ++i) {
        allowed_kinds |= allow->native[i];
        intersection |= allow->native[i] & native[i];
        forbidden |= deny->native[i] & native[i];
    }
    return !forbidden && (!allowed_kinds || intersection);
}

static const void *worker_data(const void *object)
{
    if (!object)
        return 0;
    const void *ai = READ_PTR(object, 0x260);
    if (!ai)
        return 0;
    const void *data = READ_PTR(ai, 4);
    return data && READ_WORD(data, 0) == WorkerAIDataVTable ? data : 0;
}

static Byte any_filters(const struct WorkerFilters *filters)
{
    const struct KindMask *masks[] = {
        &filters->harvest, &filters->warehouse,
        &filters->forbidden_harvest, &filters->forbidden_warehouse
    };
    for (unsigned i = 0; i < sizeof(masks) / sizeof(masks[0]); ++i) {
        if (masks[i]->resource)
            return 1;
        for (unsigned j = 0; j < NativeKinds; ++j)
            if (masks[i]->native[j])
                return 1;
    }
    return 0;
}

static Byte candidate_permitted(const struct WorkerFilters *filters, const void *target, Byte dropoff)
{
    const void *template = READ_PTR(target, 4);
    const Word *native = (const Word *)((const Byte *)template + TemplateKindsOffset);
    Word resource = READ_WORD(template, TemplateResourceKindsOffset);
    if (!dropoff && native[NativeTree / 32] & (1u << (NativeTree % 32)))
        resource |= HarvestTree;
    if (dropoff)
        return permits(&filters->warehouse, &filters->forbidden_warehouse, native, resource);
    return permits(&filters->harvest, &filters->forbidden_harvest, native, resource);
}

Byte filter_candidate(const void *worker, const void *target, Byte dropoff)
{
    const Byte *data = worker_data(worker);
    if (!data || !target || !READ_PTR(target, 4))
        return 1;
    return candidate_permitted((const struct WorkerFilters *)(data + WorkerDataFiltersOffset),
                               target, dropoff);
}

Byte filter_manual_dock(const void *worker, const void *target)
{
    const Byte *data = worker_data(worker);
    if (!data || !target || !READ_PTR(target, 4))
        return 1;
    const struct WorkerFilters *filters = (const void *)(data + WorkerDataFiltersOffset);
    if (!any_filters(filters))
        return 1;
    Word warehouse_key = native_name_to_key(name_key_generator, "SupplyWarehouseDockUpdate");
    Word center_key = native_name_to_key(name_key_generator, "SupplyCenterDockUpdate");
    if (warehouse_key && native_find_module(target, warehouse_key)
        && !candidate_permitted(filters, target, 0))
        return 0;
    if (center_key && native_find_module(target, center_key)
        && !candidate_permitted(filters, target, 1))
        return 0;
    return 1;
}

static Byte permits_trees(const Byte *data)
{
    static const Word tree_kinds[NativeKinds] = {[NativeTree / 32] = 1u << (NativeTree % 32)};
    const struct WorkerFilters *filters = (const void *)(data + WorkerDataFiltersOffset);
    return permits(&filters->harvest, &filters->forbidden_harvest, tree_kinds, HarvestTree);
}

Byte THISCALL worker_harvest_trees(const void *supply_interface)
{
    const Byte *data = READ_PTR(supply_interface, -0x4a8);
    return data[0x80] && permits_trees(data);
}

void THISCALL worker_dock(void *ai, const void *target, int source)
{
    const void *worker = READ_PTR(ai, 8);
    if (filter_manual_dock(worker, target))
        native_worker_dock(ai, target, source);
}

void THISCALL worker_harvest(void *ai, const void *coordinates, int source)
{
    const Byte *data = READ_PTR(ai, 4);
    if (permits_trees(data))
        native_worker_harvest(ai, coordinates, source);
}
```

</details>

<details>
<summary><code>harvest_hooks.s</code></summary>

```asm
.intel_syntax noprefix
.section .text

.set native_worker_ctor, 0x65417b
.set native_template_ctor, 0x73fb7a
.set supply_candidate_failed, 0x82c72c
.set manual_candidate_failed, 0x82c76b
.set pickup_after_check, 0x82c66c
.set pickup_absent, 0x82c689
.set dropoff_after_check, 0x82c6cc
.set dropoff_absent, 0x82c6f3
.set manual_fallback, 0x82c78c

.global init_worker_filters
init_worker_filters:
    call native_worker_ctor
    push edi
    lea edi, [eax+0x94]
    mov edx, eax
    xor eax, eax
    mov ecx, 32
    rep stosd
    mov eax, edx
    pop edi
    ret

.global init_template_resources
init_template_resources:
    call native_template_ctor
    mov dword ptr [eax+0x650], 0
    ret

.global copy_template_resources
copy_template_resources:
    mov eax, [ebp+8]
    mov ecx, [eax+0x650]
    mov [ebx+0x650], ecx
    pop esi
    mov eax, ebx
    pop ebx
    leave
    ret 4

.global filter_pickup
filter_pickup:
    mov edi, eax
    test edi, edi
    jz pickup_absent
    push 0
    push ebx
    push esi
    call filter_candidate
    add esp, 12
    test al, al
    jz supply_candidate_failed
    jmp pickup_after_check

.global filter_dropoff
filter_dropoff:
    mov esi, eax
    test esi, esi
    jz dropoff_absent
    push 1
    push ebx
    push dword ptr [ebp+8]
    call filter_candidate
    add esp, 12
    test al, al
    jz supply_candidate_failed
    jmp dropoff_after_check

.global filter_dock_fallback
filter_dock_fallback:
    cmp byte ptr [ebp+0x14], 0
    je manual_candidate_failed
    push edi
    push dword ptr [ebp+8]
    call filter_manual_dock
    add esp, 8
    test al, al
    jz manual_candidate_failed
    jmp manual_fallback
.section .note.GNU-stack,"",@progbits
```

</details>

<details>
<summary><code>build_harvest_filters.py</code></summary>

```python
from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
from struct import pack, unpack_from
from subprocess import check_output, run
from tempfile import TemporaryDirectory

from sage_patch.utils import allocate_section, apply_byte_patch, call_rel32, file_offset, jmp_rel32

HERE = Path(__file__).resolve().parent
BASE_HASH = '9518fa33d00580cee50e735fe7141e24796d37d6ce9560b85e74dcd45cbb5828'
CALLS = (
    (0x65425c, 0x65417b, 'init_worker_filters'),
    (0x6d2768, 0x73fb7a, 'init_template_resources'),
    (0x6d27d8, 0x73fb7a, 'init_template_resources'),
    (0x656289, 0x655b0b, 'parse_kind_token'),
    (0x6562d5, 0x655b0b, 'parse_kind_token'),
)
JUMPS = (
    (0x6d272b, '5e8bc35bc9c20400', 'copy_template_resources'),
    (0x82c666, '8bf885ff741d', 'filter_pickup'),
    (0x82c6c6, '8bf085f67427', 'filter_dropoff'),
    (0x82c786, '807d140074df', 'filter_dock_fallback'),
)
FILTER_NAMES = ('HarvestKindOf', 'WarehouseKindOf', 'ForbiddenHarvestKindOf', 'ForbiddenWarehouseKindOf')
C_FLAGS = (
    '-m32', '-Os', '-std=c11', '-ffreestanding', '-fno-pic', '-fno-pie',
    '-fno-stack-protector', '-fno-asynchronous-unwind-tables', '-fno-unwind-tables',
    '-fno-ident', '-mno-sse', '-mno-mmx', '-mpreferred-stack-boundary=2',
    '-mincoming-stack-boundary=2', '-Wall', '-Wextra', '-Werror',
)

def patch_executable(stock, work):
    assert sha256(stock).hexdigest() == BASE_HASH
    image = bytearray(stock)
    address_of = lambda address: file_offset(image, address)
    field_table = stock[address_of(0xc058c8):address_of(0xc058c8) + 13 * 16]
    assert field_table[-16:] == bytes(16)
    field_source = ['.section .rodata', '.balign 4', '.global worker_field_table', 'worker_field_table:']
    for i in range(12):
        row = unpack_from('<4I', field_table, i * 16)
        field_source.append('.long ' + ', '.join(hex(value) for value in row))
    for i, name in enumerate(FILTER_NAMES):
        field_source.append(f'.long name_{i}, parse_worker_mask, 0, {0x94 + 0x20 * i}')
    field_source.append('.zero 16')
    for i, name in enumerate(FILTER_NAMES):
        field_source.extend((f'name_{i}:', f'.asciz "{name}"'))
    table = work / 'fields.s'
    table.write_text('\n'.join(field_source) + '\n')
    native, hooks, fields, elf, binary, script = (
        work / file for file in ('filters.o', 'hooks.o', 'fields.o', 'filters.elf', 'filters.bin', 'filters.ld')
    )
    run(['gcc', *C_FLAGS, '-c', HERE / 'harvest_filters.c', '-o', native], check=True)
    run(['as', '--32', HERE / 'harvest_hooks.s', '-o', hooks], check=True)
    run(['as', '--32', table, '-o', fields], check=True)
    script.write_text('''
SECTIONS {
    . = PATCH_ADDRESS;
    .patch : { *(.text*) *(.rodata*) *(.data*) *(.bss*) BYTE(0) }
    /DISCARD/ : { *(.note*) *(.comment*) }
}
''')
    symbols = {}

    def payload(address):
        run(['ld', '-m', 'elf_i386', '--no-warn-rwx-segments', '-z', 'noexecstack', '-T', script,
             '--defsym', f'PATCH_ADDRESS={address:#x}', '-o', elf, native, hooks, fields], check=True)
        for row in check_output(['nm', '--defined-only', elf], text=True).splitlines():
            value, _, name = row.split()
            symbols[name] = int(value, 16)
        run(['objcopy', '-O', 'binary', '-j', '.patch', elf, binary], check=True)
        return binary.read_bytes()

    allocate_section(image, '.harvest', payload, 0xe0000060)
    for location, target, symbol in CALLS:
        apply_byte_patch(image, address_of(location), call_rel32(location, target),
                         call_rel32(location, symbols[symbol]), symbol)
    for location, original, symbol in JUMPS:
        original = bytes.fromhex(original)
        apply_byte_patch(image, address_of(location), original,
                         jmp_rel32(location, symbols[symbol], len(original)), symbol)

    pointers = (
        (0xda414c, 0x6564e7, 'parse_object_kinds'),
        (0x64ef92, 0xc058c8, 'worker_field_table'),
        (0xc6abe0, 0x8ace11, 'worker_harvest_trees'),
        (0xc6aca8 + 4 * 51, 0x8ace4a, 'worker_dock'),
        (0xc6aca8 + 4 * 52, 0x8ace75, 'worker_harvest'),
    )
    for location, original, symbol in pointers:
        apply_byte_patch(image, address_of(location), pack('<I', original), pack('<I', symbols[symbol]), symbol)

    for location in (0x6d2751, 0x6d27be):
        apply_byte_patch(image, address_of(location), pack('<I', 0x650), pack('<I', 0x654),
                         'ThingTemplate resource flags allocation')
    apply_byte_patch(image, address_of(0x654245), pack('<I', 0x94), pack('<I', 0x114),
                     'WorkerAIUpdateModuleData filter allocation')
    return image, symbols


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
