.intel_syntax noprefix
.section .text
.set active_mode, 0xf4d184
.set windowed, 2

.global edge_event
edge_event:
    cmp dword ptr [active_mode],windowed
    jne original_edge_event
    cmp al,bl
    jne finish_mouse_event
    pushad
    call window_edges
    test eax,eax
    popad
    jz .inside_or_outside_client
    cmp byte ptr [esi+0x38],bl
    je start_edge_scroll
    jmp finish_mouse_event
.inside_or_outside_client:
    cmp byte ptr [esi+0x38],bl
    je finish_mouse_event
    cmp dword ptr [esi+0x148],3
    je stop_edge_scroll
    jmp finish_mouse_event

.global edge_tick
edge_tick:
    cmp dword ptr [active_mode],windowed
    jne .native_viewport
    lea eax,[ebp-0x10]
    push eax
    push ebx
    call window_scroll
    add esp,8
    test eax,eax
    jz stop_edge_tick
    movss xmm0,dword ptr [ebp-0x10]
    jmp apply_edge_scroll
.native_viewport:
    mov ecx,dword ptr [0xde4418]
    jmp original_viewport_tick

.section .note.GNU-stack,"",@progbits
