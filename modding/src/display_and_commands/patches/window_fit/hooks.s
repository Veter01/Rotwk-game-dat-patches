.intel_syntax noprefix
.text

.global fit_configure_window
fit_configure_window:
    lea eax,[ebp-0x58]
    push eax
    push dword ptr [ebp-0x64]
    push ebx
    lea eax,[ebp-0x2c]
    push eax
    push dword ptr [ebp-0x5c]
    call fit_window
    add esp,20
    test eax,eax
    jz configure_failed
    mov eax,[ebp-0x58]
    mov [ebp-0x70],eax
    mov eax,[ebp-0x54]
    mov [ebp-0x68],eax
    mov ecx,[ebp-0x50]
    mov edi,[ebp-0x4c]
    mov ebx,[ebp-0x48]
    mov eax,[ebp-0x44]
    mov [ebp-0x64],eax
    mov eax,0x10ca0000
    jmp apply_window_geometry

.global configure_client_size
configure_client_size:
    cmp dword ptr [ebp-0x60],2
    jne .requested_dimensions
    lea eax,[ebp-0x64]
    push eax
    mov [ebp-0x48],ebx
    lea eax,[ebp-0x48]
    push eax
    push dword ptr [ebp-0x5c]
    call measure_client
    add esp,12
    mov ebx,[ebp-0x48]
.requested_dimensions:
    mov eax,[ebp-0x74]
    mov edi,[ebp-0x64]
    jmp store_client_size

.global keep_preferred_resolution
keep_preferred_resolution:
    mov [ebp-0x60],eax
    cmp dword ptr [0xf4d184],0
    je update_preferred
    jmp use_preferred

.global initial_window_mode
initial_window_mode:
    cmp ebx,2
    jbe configure_initial_mode
    cmp eax,2
    jne commit_initial_mode
    mov ebx,eax
    jmp configure_initial_mode

.global apply_queued_resolution
apply_queued_resolution:
    push dword ptr [esp+12]
    push dword ptr [esp+12]
    push dword ptr [esp+12]
    push dword ptr [esp+12]
    push esi
    push ecx
    call apply_windowed_resolution
    add esp,40
    test al,al
    jmp resolution_result

.global configure_window
configure_window:
    mov eax,[esp+4]
    mov edx,[esp+8]
    mov ecx,[esp+12]
    push dword ptr [esp+16]
    call original_configure
    add esp,4
    ret

.global restore_window
restore_window:
    mov eax,[esp+4]
    mov edx,[esp+8]
    jmp original_restore

.section .note.GNU-stack,"",@progbits
