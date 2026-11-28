.intel_syntax noprefix
.section .text
.global harvest_dispatch_v2

# Entry from SpecialPowerModule's SPECIAL_HARVEST branch.
# EDI = unit, EBX = AI update, ECX = player's supply manager.
harvest_dispatch_v2:
    mov eax, edi
    call worker_module_data
    test eax, eax
    jz harvest_trees
    cmp byte ptr [eax + 0x80], 0       # HarvestTrees
    jne harvest_trees
    test byte ptr [eax + 0xb0], 1     # HarvestKindOf includes HARVEST_STONE
    jz harvest_trees

    # Use the same search (including resource-kind and stock filters) and
    # dock order that the game's supply-gathering state already uses.
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
    lea eax, [ebp - 0x20]             # instructions covered by the entry jump
    push eax
    push edi
    jmp resume_tree_search
