.intel_syntax noprefix
.text
.global select_help_page, open_help_link

.equ OPTIONS_SCREEN, 0x00f27674
.equ OPTIONS_PAGE, 0x00f2767c
.equ INIT_OPTIONS_SCREEN, 0x00f3d000
.equ APPLY_OPTIONS_PAGE, 0x00f3d00e
.equ MAIN_WINDOW, 0x00dc3c64
.equ GAME_TEXT, 0x00de4b04
.equ INIT_ASCII_STRING, 0x004374e0
.equ FREE_ASCII_STRING, 0x00435d50
.equ FREE_UTF16_STRING, 0x004367b0
.equ SHELL_EXECUTE_W, 0x00bd07a4
.equ HELP_PAGE, 6

# Registers the active options screen if necessary, then uses its normal page
# switch to hide every native gadget belonging to other pages.
select_help_page:
    cmp ecx, dword ptr [OPTIONS_SCREEN]
    je apply_help_page
    push ecx
    call INIT_OPTIONS_SCREEN
    add esp, 4
apply_help_page:
    push HELP_PAGE
    call APPLY_OPTIONS_PAGE
    add esp, 4
    ret

# The APT button supplies only the command. GameText supplies the URL, using
# the same language table and fallback order as all other APT translations.
open_help_link:
    cmp ecx, dword ptr [OPTIONS_SCREEN]
    jne skip_help_link
    cmp dword ptr [OPTIONS_PAGE], HELP_PAGE
    jne skip_help_link
    cmp dword ptr [GAME_TEXT], 0
    je skip_help_link
    push ebp
    mov ebp, esp
    sub esp, 12
    xor eax, eax
    mov [ebp-4], eax
    mov [ebp-8], eax
    mov [ebp-12], eax

    push offset help_url_key
    lea ecx, [ebp-4]
    call INIT_ASCII_STRING

    lea eax, [ebp-12]
    push eax
    lea eax, [ebp-4]
    push eax
    lea eax, [ebp-8]
    push eax
    mov ecx, [GAME_TEXT]
    mov edx, [ecx]
    call dword ptr [edx+0x38]
    cmp byte ptr [ebp-12], 0
    je release_help_strings
    mov eax, [ebp-8]
    test eax, eax
    jz release_help_strings
    add eax, 8
    push eax
    call validate_help_uri
    pop edx
    test eax, eax
    jz release_help_strings

    push 1
    push 0
    push 0
    push edx
    push offset open_verb
    push dword ptr [MAIN_WINDOW]
    call dword ptr [SHELL_EXECUTE_W]

release_help_strings:
    lea ecx, [ebp-8]
    call FREE_UTF16_STRING
    lea ecx, [ebp-4]
    call FREE_ASCII_STRING
    leave
skip_help_link:
    ret

# Accept a URI and never treat the text as a command, a network share, or a
# local path. Keep Unicode in the target and exclude Windows shell protocols.
validate_help_uri:
    push ebx
    push esi
    push edi
    mov esi, [esp+16]
    mov edi, esi
    movzx eax, word ptr [edi]
    or eax, 0x20
    sub eax, 'a'
    cmp eax, 25
    ja bad_uri

next_scheme_character:
    inc edi
    inc edi
    movzx eax, word ptr [edi]
    cmp eax, ':'
    je got_scheme
    lea edx, [eax-'0']
    cmp edx, 9
    jbe next_scheme_character
    cmp eax, '+'
    je next_scheme_character
    cmp eax, '-'
    je next_scheme_character
    cmp eax, '.'
    je next_scheme_character
    or eax, 0x20
    sub eax, 'a'
    cmp eax, 25
    jbe next_scheme_character
    jmp bad_uri

got_scheme:
    lea edx, [esi+2]
    cmp edi, edx
    je bad_uri
    lea ebx, [edi+2]
    cmp word ptr [ebx], 0
    je bad_uri
    mov edx, offset blocked_schemes
next_blocked_scheme:
    cmp byte ptr [edx], 0
    je check_web_scheme
    call match_scheme
    test eax, eax
    jnz bad_uri
skip_blocked_scheme:
    inc edx
    cmp byte ptr [edx-1], 0
    jne skip_blocked_scheme
    jmp next_blocked_scheme

check_web_scheme:
    mov edx, offset http_scheme
    call match_scheme
    test eax, eax
    jnz check_web_authority
    mov edx, offset https_scheme
    call match_scheme
    test eax, eax
    jz check_target_characters
check_web_authority:
    cmp dword ptr [ebx], 0x002f002f
    jne bad_uri
    movzx eax, word ptr [ebx+4]
    cmp eax, '/'
    je bad_uri
    cmp eax, '?'
    je bad_uri
    cmp eax, '#'
    je bad_uri
    test eax, eax
    jz bad_uri

check_target_characters:
    mov ecx, 8192
next_target_character:
    movzx eax, word ptr [ebx]
    test eax, eax
    jz good_uri
    cmp eax, 0x20
    jbe bad_uri
    cmp eax, 0x7f
    je bad_uri
    cmp eax, '"'
    je bad_uri
    cmp eax, '<'
    je bad_uri
    cmp eax, '>'
    je bad_uri
    cmp eax, 0x5c
    je bad_uri
    add ebx, 2
    dec ecx
    jnz next_target_character
bad_uri:
    xor eax, eax
    jmp uri_result
good_uri:
    mov eax, 1
uri_result:
    pop edi
    pop esi
    pop ebx
    ret

# Compare the lowercase ASCII name at EDX with the URI scheme at ESI..EDI.
match_scheme:
    push edx
    mov ecx, esi
match_character:
    cmp ecx, edi
    je end_of_scheme
    movzx eax, word ptr [ecx]
    cmp eax, 'A'
    jb same_case
    cmp eax, 'Z'
    ja same_case
    or al, 0x20
same_case:
    cmp al, [edx]
    jne different_scheme
    add ecx, 2
    inc edx
    jmp match_character
end_of_scheme:
    xor eax, eax
    cmp byte ptr [edx], 0
    sete al
    pop edx
    ret
different_scheme:
    xor eax, eax
    pop edx
    ret

help_url_key: .asciz "APT:ETHelpURL"
open_verb: .short 'o', 'p', 'e', 'n', 0
http_scheme: .asciz "http"
https_scheme: .asciz "https"
blocked_schemes:
    .asciz "file", "shell", "javascript", "vbscript", "data", "about", "res"
    .asciz "search", "search-ms", "ms-msdt", "ms-appinstaller", "ms-its", "mk"
    .byte 0
