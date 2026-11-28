.intel_syntax noprefix
.text

# configure_window has regparm(3): EAX=mode, EDX=width*, ECX=height*.
# Its one stack argument and return address stay in place for the tail jump.
.global configure_startup_window
configure_startup_window:
    test eax, eax
    jnz native_configure_window
    push 32
    jmp select_resolution

.global configure_live_window
configure_live_window:
    test eax, eax
    jnz native_configure_window
    push dword ptr [ebp - 0x60]

select_resolution:
    push ecx
    push edx
    call choose_fullscreen_size
    pop edx
    pop ecx
    add esp, 4
    xor eax, eax
    jmp native_configure_window
