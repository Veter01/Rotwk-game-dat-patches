# Arnor Stone Auto-Harvest for ROTWK

This patch lets an Arnor Stoneworker start gathering stone with one click. The ability finds a nearby eligible stone deposit and issues the game's standard gathering order. The worker's AI handles mining and delivery to the Stoneworks. Mordor Lumber Workers still use the same ability to gather wood.

The change has two parts. Ennorath's BIG supplies the button and resource filters. The patched `game.dat` routes the ability to the stone-gathering logic. Apply both parts to test the feature. The [repository build](../README.md#rebuild-the-patches) runs the INI patch (`src/harvest/build_ini.py`) and the executable patch (`src/harvest/build_game.py`).

## 1. Configure the Ennorath BIG

Edit these files inside `____enrth_data.big`.

| File | Change |
| --- | --- |
| `data/ini/object/goodfaction/units/arnor/new/arnorharvester.ini` | Set the fields below in `WorkerAIUpdate ModuleTag_10` on `ArnorHarvester`. |
| `data/ini/object/neutral/SupplyRocks.ini` | Add `HARVEST_STONE` to the existing `KindOf` line of each resource pile with `SupplyWarehouseDockUpdate`. The test BIG has 33 such objects. |
| `data/ini/object/goodfaction/structures/arnor/new/stoneworkerMod.ini` | Add `STONE_WAREHOUSE` to the existing `KindOf` line on `ArnorStoneworkerMod`, the Stoneworks. |
| `data/ini/includes/commandset.inc` | Enable `1 = Command_HarvestArnor` in `ArnorHarvesterCommandSet`. |

Place the new `KindOf` flags before any inline comment. In the worker's existing `WorkerAIUpdate` block, use:

```ini
HarvestTrees    = No
HarvestKindOf   = HARVEST_STONE
WarehouseKindOf = STONE_WAREHOUSE
```

`HarvestKindOf` filters resource sources. `WarehouseKindOf` filters buildings that receive the gathered resource. Keep the existing `SpecialPowerModule` on the worker. The existing `Command_HarvestArnor` button calls `SpecialAbilityHarvest`, which uses `SPECIAL_HARVEST` with a 6,000 ms reload time.

## 2. Patch the ability in `game.dat`

In the original handler, `SPECIAL_HARVEST` calls the engine's tree search. That search exits immediately for a worker with `HarvestTrees = No`. The patch checks for a `WorkerAIUpdate` with tree harvesting disabled and the stone flag set. For those workers it calls the engine's supply-source search and issues a dock order on the selected deposit. If the search returns no deposit, the worker keeps its current order.

The addresses below are specific to the Ennorath PE32 build used for this patch. It already has the `.harvest` section and support for the resource and warehouse filters. The patch script checks the exact input build before writing a separate output file.

The dispatch source (`src/harvest/dispatch.s`) uses the following branch.

```asm
.intel_syntax noprefix
.section .text
.global harvest_dispatch_v2

# EDI is the unit, EBX is its AI update, and ECX is the player's supply manager.
harvest_dispatch_v2:
    mov eax, edi
    call worker_module_data
    test eax, eax
    jz harvest_trees
    cmp byte ptr [eax + 0x80], 0       # HarvestTrees
    jne harvest_trees
    test byte ptr [eax + 0xb0], 1     # HARVEST_STONE bit in HarvestKindOf
    jz harvest_trees

    push edi
    call nearest_supply_source
    test eax, eax
    jz finish_power
    push 2
    push eax
    lea ecx, [ebx + 0x20]
    call issue_dock
    jmp finish_harvest_order

harvest_trees:
    lea eax, [ebp - 0x20]            # Replay the instructions replaced by the jump.
    push eax
    push edi
    jmp resume_tree_search
```

To assemble it manually, run GNU binutils in a working folder that contains a copy of `dispatch.s`.

```sh
as --32 -o dispatch.o dispatch.s
ld -m elf_i386 -Ttext=0xf4f770 --oformat binary -e harvest_dispatch_v2 \
  --defsym=worker_module_data=0xf4f097 \
  --defsym=nearest_supply_source=0x8faa51 \
  --defsym=issue_dock=0x66c609 \
  --defsym=finish_harvest_order=0x897f00 \
  --defsym=finish_power=0x897f25 \
  --defsym=resume_tree_search=0x897ee9 \
  -o dispatch.bin dispatch.o
```

For a manual build, save and run the following Python code beside the original `game.dat` and the assembled `dispatch.bin`.

```python
from hashlib import sha256
from pathlib import Path
from struct import pack_into, unpack_from

game = bytearray(Path("game.dat").read_bytes())
original_hash = "bad61adac79fa2e1919d65387196913610685b5c0b05b6219e4872e6dd49f3f5"
if sha256(game).hexdigest() != original_hash:
    raise SystemExit("This patch requires the matching Ennorath game.dat build.")

dispatch = Path("dispatch.bin").read_bytes()
if len(dispatch) != 0x45:
    raise SystemExit("Unexpected dispatch size.")

hook_va, dispatch_va = 0x897EE4, 0xF4F770
hook_offset, dispatch_offset = 0x497EE4, 0xB27370
harvest_section_header, harvest_raw_offset = 0xC38, 0xB26C00
virtual_size_field = harvest_section_header + 8
dispatch_end = dispatch_offset + len(dispatch)

assert game[hook_offset:hook_offset + 5] == bytes.fromhex("8D 45 E0 50 57")
assert unpack_from("<I", game, virtual_size_field)[0] == 0x765
assert not any(game[dispatch_offset:dispatch_end])

game[hook_offset] = 0xE9
pack_into("<i", game, hook_offset + 1, dispatch_va - (hook_va + 5))
game[dispatch_offset:dispatch_end] = dispatch
pack_into("<I", game, virtual_size_field, dispatch_end - harvest_raw_offset)

patched_hash = "46abb4a13baefa097a00f18c27d230e827a256712904b8b42ae5d92070c9a7b2"
if sha256(game).hexdigest() != patched_hash:
    raise SystemExit("The result differs from the v2 build.")
Path("game-patched.dat").write_bytes(game)
```

## 3. Test in skirmish

1. Repack the BIG with the original internal paths, or use `build/harvest/____enrth_data_ArnorAutoHarvest.big`. Use `build/harvest/game.dat` or the manual `game-patched.dat` as `game.dat` in your test install.
2. Play as Arnor on a map with a harvestable stone deposit. Build the Stoneworks nearby, select an Arnor Stoneworker, and click the harvest button with the stone icon.
3. Check that the worker goes to the deposit, delivers resources to the Stoneworks, and returns to gather again. Test once with trees closer than the deposit and once with no usable stone nearby.
4. Play as Mordor and click the harvest button on a Lumber Worker to verify that wood gathering still starts normally.

The dispatch verification script (`src/harvest/verify.py`) checks the v2 handler with test inputs covering a valid stone source, an empty stone search, the original wood-gathering path, and the resource and warehouse filters. The full in-game gather-and-deliver loop still needs verification.
