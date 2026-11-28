.intel_syntax noprefix
.text

.global poll_camera
poll_camera:
    cmp dword ptr [0xf4d184], 2
    jne .native
    push esi
    call poll_edge_scroll
    add esp, 4
    xorps xmm0, xmm0
.native:
    cmp byte ptr [esi+0x38], 0
    push edi
    jmp native_camera_frame

.global select_mode
select_mode:
    push eax
    call queue_display_mode
    add esp, 4
    jmp native_select_return

.global sync_mode
sync_mode:
    call sync_display_mode_lock
    lea esp, [ebp-8]
    pop ebx
    pop esi
    pop ebp
    jmp native_sync_resolution

.global read_reset_mode
read_reset_mode:
    call editable_display_mode
    jmp native_reset_test

.global read_save_mode
read_save_mode:
    call editable_display_mode
    jmp native_save_test

.global cancel_mode
cancel_mode:
    call match_blocks_display_mode
    test eax, eax
    jz .cancel_allowed
    call clear_display_mode_request
    jmp native_cancel_return
.cancel_allowed:
    mov edx, dword ptr [0xf4d180]
    jmp native_cancel_mode
