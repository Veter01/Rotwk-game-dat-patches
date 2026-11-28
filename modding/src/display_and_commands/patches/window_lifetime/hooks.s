.intel_syntax noprefix
.text

.global on_destroy_game_window
on_destroy_game_window:
    pushad
    push esi
    call forget_window_control
    add esp,4
    popad
    or eax,ecx
    mov [esi+8],eax
    jmp native_destroy_next

# A display layout rebuild can remove a gadget from the manager's tree.
# Consult the live tree before the mode switch reuses any saved gadget.
.global check_display_controls
check_display_controls:
    call discard_detached_controls
    mov eax,[0xf4d1ac]
    jmp native_control_update_next

.global cursor_clipping_guard
cursor_clipping_guard:
    cmp dword ptr [moving_window],0
    jne .dragging
    mov eax,[0xf4d174]
    jmp native_apply_clip_next
.dragging:
    ret

.global restore_window
restore_window:
    mov eax,[esp+4]
    mov edx,[esp+8]
    jmp native_restore_window

.section .note.GNU-stack,"",@progbits
