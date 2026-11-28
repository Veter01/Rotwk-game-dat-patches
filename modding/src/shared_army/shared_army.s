.intel_syntax noprefix
.section .text
.global order_owner, local_control, on_donation, on_status_row, on_reset, explicit_power
.global grants, on_attack_move, authorized_ui_owner, builder_panel_player
.global upgrade_affordability, upgrade_order_owner, authorize_construction
.global formation_preview_access, formation_order_access
.global mark_voice_feedback, voice_listener_index, borderless_edge_scroll, edge_scroll_tick
.global rts_checkboxes, share_rule_label, army_rule_enabled

.equ PLAYER_LIST, 0x00de4928
.equ GAME_LOGIC, 0x00de412c
.equ MESSAGE_STREAM, 0x00de6398
.equ APT, 0x00de3f0c
.equ DONATION_MESSAGE, 0x466
.equ CONTROL_TAG, 0x53480000
.equ PLAYER_COUNT, 20
.equ ROW_COUNT, 8
.equ SUPPORT_INTERVAL, 60
.equ AUDIO_MANAGER, 0x00de42fc
.equ SHARED_VOICE, 0x53485643
.equ DISPLAY_MODE, 0x00f4d184
.equ MAIN_WINDOW, 0x00dc3c64
.equ GET_FOREGROUND_WINDOW, 0x00bd0850
.equ GET_CURSOR_POS, 0x00bd081c
.equ SCREEN_TO_CLIENT, 0x00bd0890
.equ GET_CLIENT_RECT, 0x00bd08b8
.equ GET_TICK_COUNT, 0x00bd0920
.equ TEXT_MANAGER, 0x00de4b04
.equ LOBBY_UI, 0x00de8d78
.equ SHARED_ARMY_RULE, 8
.equ MATCH_GAME_INFO, 0x00de892c
.equ SKIRMISH_GAME_INFO, 0x00de8930
.equ GAME_MODE_SKIRMISH, 2

# One bit per recipient in each owner's row. Written only by the synchronized
# game command and match reset, never by the local UI.
.balign 4
grants:
    .zero PLAYER_COUNT * 4
# Reverse lookup for AI recipients so attack orders can take the fast path.
ai_recipients:
    .long 0
ai_grantors:
    .zero PLAYER_COUNT * 4
ai_next_frame:
    .zero PLAYER_COUNT * 4
state_end:

# ECX = human owner, EDX = recipient. Returns true for active, distinct allies.
allied_pair:
    xor eax, eax
    test ecx, ecx
    jz pair_return
    test edx, edx
    jz pair_return
    cmp ecx, edx
    je pair_return
    cmp dword ptr [ecx+0x54], PLAYER_COUNT
    jae pair_return
    cmp dword ptr [edx+0x54], PLAYER_COUNT
    jae pair_return
    cmp dword ptr [ecx+0x5c], 0
    jne pair_return
    cmp dword ptr [edx+0x5c], 1
    ja pair_return
    cmp byte ptr [ecx+0x35a], 0
    jne pair_return
    cmp byte ptr [edx+0x35a], 0
    jne pair_return
    cmp byte ptr [ecx+0x754], 0
    jne pair_return
    cmp byte ptr [edx+0x754], 0
    jne pair_return
    cmp dword ptr [ecx+0x30c], 0
    je pair_return
    cmp dword ptr [edx+0x30c], 0
    je pair_return
    push esi
    push edi
    mov esi, ecx
    mov edi, edx
    push dword ptr [edi+0x30c]
    call player_relationship
    cmp eax, 2
    jne pair_denied
    mov ecx, edi
    push dword ptr [esi+0x30c]
    call player_relationship
    cmp eax, 2
    sete al
    movzx eax, al
    jmp pair_done
pair_denied:
    xor eax, eax
pair_done:
    pop edi
    pop esi
pair_return:
    ret

# ECX = object. Foreign structures, immobile props, and spellbooks stay outside unit control.
is_unit:
    xor eax, eax
    cmp dword ptr [ecx+0x260], 0
    je is_unit_out
    mov edx, [ecx+4]
    test edx, edx
    jz is_unit_out
    test byte ptr [edx+0x108], 0x84
    jnz is_unit_out
    test byte ptr [edx+0x117], 0x08
    jnz is_unit_out
    inc eax
is_unit_out:
    ret

# ECX = controller, EDX = owner. Called after distinguishing stock own-unit access.
has_grant:
    xor eax, eax
    test ecx, ecx
    jz grant_return
    test edx, edx
    jz grant_return
    mov eax, [edx+0x54]
    cmp eax, PLAYER_COUNT
    jae grant_no
    push esi
    mov esi, [ecx+0x54]
    cmp esi, PLAYER_COUNT
    jae grant_bit_clear
    bt dword ptr [grants+eax*4], esi
grant_bit_clear:
    pop esi
    jae grant_no
    # A permission is valid only while both seats are still active allies.
    xchg ecx, edx
    jmp allied_pair
grant_no:
    xor eax, eax
grant_return:
    ret

# Called instead of the controlling-player getter in the synchronized AIGroup filter.
order_owner:
    push ecx
    call object_owner
    mov ecx, [esp+0x18]
    cmp eax, ecx
    je filter_out
    push eax
    mov ecx, [esp+4]
    call is_unit
    test eax, eax
    jz filter_restore
    mov ecx, [esp+0x1c]
    mov edx, [esp]
    call has_grant
    test eax, eax
    jz filter_restore
    pop eax
    mov eax, [esp+0x18]
    jmp filter_out
filter_restore:
    pop eax
filter_out:
    add esp, 4
    ret

# Object::isLocallyControlled used by selection, cursors and order creation.
local_control:
    mov eax, [PLAYER_LIST]
    test eax, eax
    jz command_no
    mov edx, [eax+0x10]
    # Fall through to the same test used with the synchronized sender.
command_access:
    test ecx, ecx
    jz command_no
    test edx, edx
    jz command_no
    push esi
    push edi
    mov edi, ecx
    mov esi, edx
    call object_owner
    cmp eax, esi
    je command_own
    push eax
    mov ecx, edi
    call is_unit
    pop edx
    test eax, eax
    jz command_done
    mov ecx, esi
    call has_grant
    jmp command_done
command_own:
    mov eax, 1
command_done:
    pop edi
    pop esi
    ret
command_no:
    xor eax, eax
    ret

# These sites use the player for a local UI comparison or cursor display.
authorized_ui_owner:
    push ecx
    call local_control
    pop ecx
    test eax, eax
    jz ui_actual_owner
    mov eax, [PLAYER_LIST]
    mov eax, [eax+0x10]
    ret
ui_actual_owner:
    jmp object_owner

# These gates precede the engine's formation eligibility and sorting.
formation_preview_access:
    mov edx, [ebp+8]
    jmp command_access

formation_order_access:
    mov edx, [ebp+0xc]
    jmp command_access

# Mark the two runtime voice events created by the native selection/order
# feedback routine. The offset holds the fallback player index, which the
# audio manager normally ignores once a positional source has been attached.
mark_voice_feedback:
    mov ecx, [esi+0x24]
    test ecx, ecx
    jz voice_preflight
    call local_control
    test eax, eax
    jz voice_preflight
    mov ecx, [esi+0x24]
    call object_owner
    mov edx, [PLAYER_LIST]
    cmp eax, [edx+0x10]
    je voice_preflight
    mov dword ptr [ebp-0x2e8+0x6c], SHARED_VOICE
    mov dword ptr [ebp-0x370+0x6c], SHARED_VOICE
voice_preflight:
    mov ecx, [AUDIO_MANAGER]
    jmp voice_event_preflight

# EDI is the listener from the audio visibility routine. Its other tests
# still use the real event and object, including position and cooldown.
voice_listener_index:
    cmp dword ptr [ecx+0x6c], SHARED_VOICE
    jne audio_index_stock
    test edi, edi
    jz audio_index_unknown
    mov eax, [edi+0x54]
    ret
audio_index_unknown:
    mov eax, -1
    ret
audio_index_stock:
    jmp audio_owner_index

# Continue through the engine's edge checks when the window is focused.
# A decorated window must also have the pointer over its client surface.
borderless_edge_scroll:
    cmp byte ptr [ecx+0x2c], bl
    je edge_scroll_continue
    push eax
    push ecx
    push edx
    call edge_window_has_pointer
    test eax, eax
    pop edx
    pop ecx
    pop eax
    jz edge_scroll_skip
    jmp edge_scroll_continue

# The regular per-frame movement may outlive the last WM_MOUSEMOVE.
edge_scroll_tick:
    cmp dword ptr [DISPLAY_MODE], 0
    je edge_scroll_time
    call edge_window_has_pointer
    test eax, eax
    jnz edge_scroll_time
    mov ecx, esi
    call edge_scroll_stop
    mov dword ptr [ebp-0xc], 0
    xorps xmm0, xmm0
    jmp edge_scroll_idle
edge_scroll_time:
    call dword ptr [GET_TICK_COUNT]
    jmp edge_scroll_update

edge_window_has_pointer:
    push ebx
    sub esp, 24
    mov ebx, [MAIN_WINDOW]
    test ebx, ebx
    jz edge_pointer_out
    call dword ptr [GET_FOREGROUND_WINDOW]
    cmp eax, ebx
    jne edge_pointer_out
    cmp dword ptr [DISPLAY_MODE], 1
    je edge_pointer_in
    lea eax, [esp]
    push eax
    call dword ptr [GET_CURSOR_POS]
    test eax, eax
    jz edge_pointer_out
    lea eax, [esp]
    push eax
    push ebx
    call dword ptr [SCREEN_TO_CLIENT]
    test eax, eax
    jz edge_pointer_out
    lea eax, [esp+8]
    push eax
    push ebx
    call dword ptr [GET_CLIENT_RECT]
    test eax, eax
    jz edge_pointer_out
    mov eax, [esp]
    cmp eax, [esp+16]
    jae edge_pointer_out
    mov eax, [esp+4]
    cmp eax, [esp+20]
    jae edge_pointer_out
edge_pointer_in:
    mov eax, 1
    jmp edge_pointer_done
edge_pointer_out:
    xor eax, eax
edge_pointer_done:
    add esp, 24
    pop ebx
    ret

# APT checks that this player matches EBX before displaying the builder's
# tools. EBX keeps the actual owner for the scenario and construction checks.
builder_panel_player:
    push ecx
    mov ecx, edi
    call local_control
    pop ecx
    test eax, eax
    jz panel_stock_player
    mov eax, ebx
    ret
panel_stock_player:
    jmp ui_get_player

# Client-side affordability uses the same payer as the synchronized upgrade.
# Preserve observer and stock contexts when there is no locally shared object.
upgrade_affordability:
    push ecx
    mov ecx, [esp+16]
    call local_control
    test eax, eax
    jz upgrade_use_stock_player
    mov ecx, [esp+16]
    call object_owner
    mov [esp+8], eax
upgrade_use_stock_player:
    pop ecx
    jmp check_upgrade_cost

# These synchronized calls use the result only to compare with the sender.
upgrade_order_owner:
    push ecx
    mov edx, [ebp-0x14]
    call command_access
    pop ecx
    test eax, eax
    jz ui_actual_owner
    mov eax, [ebp-0x14]
    ret

# Keep the actual owner in EDX for build limits, resources and object creation.
authorize_construction:
    push edx
    mov ecx, edi
    mov edx, [ebp-0x14]
    call command_access
    pop edx
    test eax, eax
    jz donation_done
    mov eax, [edi+4]
    mov ecx, 0x4000
    jmp construction_continue

# Explicit-source special powers may bypass the selection group. Require the
# same grant for foreign mobile units here, leaving player-level sources stock.
explicit_power:
    cmp dword ptr [ebp+8], ebx
    je power_no_explicit
    pushad
    mov ecx, [ebp+8]
    call is_unit
    test eax, eax
    jz power_allow
    mov ecx, [ebp+8]
    call object_owner
    mov ecx, [ebp-0x14]
    cmp eax, ecx
    je power_allow
    mov edx, eax
    call has_grant
    test eax, eax
    jz power_deny
power_allow:
    popad
    mov ecx, dword ptr [0xde4b40]
    jmp power_continue
power_deny:
    popad
    jmp donation_done
power_no_explicit:
    jmp power_use_selection

# Existing synchronized command's three integer arguments:
# arg0 = sender, arg1 = tagged recipient & explicit grant/revoke, arg2 = zero.
# On a stock game the tagged recipient is outside the donation range.
on_donation:
    mov ecx, [ebp+8]
    mov edx, [ecx]
    push edx
    and edx, 0xfffffe00
    cmp edx, CONTROL_TAG
    pop edx
    jne normal_donation
    pushad
    call army_rule_enabled
    test al, al
    popad
    jz invalid_share
    cmp byte ptr [esi+0x18], 3
    jne invalid_share
    cmp dword ptr [eax+0x10], 0
    jne invalid_share
    cmp dword ptr [ecx+0x10], 0
    jne invalid_share
    cmp dword ptr [edi+0x10], 0
    jne invalid_share
    cmp dword ptr [edi], 0
    jne invalid_share
    mov ecx, [ebp-0x14]
    test ecx, ecx
    jz invalid_share
    mov eax, [eax]
    cmp eax, [esi+0x14]
    jne invalid_share
    cmp eax, [ecx+0x54]
    jne invalid_share
    movzx eax, dl
    cmp eax, PLAYER_COUNT
    jae invalid_share
    mov ecx, [PLAYER_LIST]
    test ecx, ecx
    jz invalid_share
    push edx
    push eax
    call nth_player
    mov edx, eax
    pop ecx
    test edx, edx
    jz invalid_share
    movzx eax, cl
    cmp eax, [edx+0x54]
    jne invalid_share
    push ecx
    push edx
    mov ecx, [ebp-0x14]
    call allied_pair
    pop edx
    pop ecx
    test eax, eax
    jz invalid_share
    cmp dword ptr [edx+0x5c], 1
    sete al
    mov byte ptr [ebp+8], al
    mov eax, [ebp-0x14]
    mov eax, [eax+0x54]
    mov edx, [edx+0x54]
    test ecx, 0x100
    jz revoke_permission
    bts dword ptr [grants+eax*4], edx
    cmp byte ptr [ebp+8], 0
    je invalid_share
    bts dword ptr [ai_grantors+edx*4], eax
    bts dword ptr [ai_recipients], edx
    mov dword ptr [ai_next_frame+edx*4], 0
    jmp donation_done
revoke_permission:
    btr dword ptr [grants+eax*4], edx
    btr dword ptr [ai_grantors+edx*4], eax
    cmp dword ptr [ai_grantors+edx*4], 0
    jne invalid_share
    btr dword ptr [ai_recipients], edx
    jmp donation_done
normal_donation:
    push dword ptr [edi]
    mov ecx, [ebp+8]
    jmp donation_continue
invalid_share:
    jmp donation_done

on_reset:
    push ecx
    push edi
    lea edi, [grants]
    xor eax, eax
    mov ecx, (state_end - grants) / 4
    rep stosd
    pop edi
    pop ecx
    jmp reset_original

# Skirmish AI issues its attack-moves with CMD_FROM_PLAYER, just like a human.
# Confirm the army unit's owner is an AI player with at least one active grant
# before looking for nearby idle reinforcements.
on_attack_move:
    cmp dword ptr [ai_recipients], 0
    je attack_move_original
    cmp dword ptr [esp+12], 0
    jne attack_move_original
    pushad
    push dword ptr [esp+36]
    push ecx
    call issue_ai_support
    add esp, 8
    popad
attack_move_original:
    mov eax, 0xb88ac2
    jmp attack_move_resume

# issue_ai_support(AIUpdateInterface*, Coord3D*) uses simulation state only.
issue_ai_support:
    push ebp
    mov ebp, esp
    sub esp, 20
    push ebx
    push esi
    push edi
    mov ecx, [ebp+8]
    mov ecx, [ecx-0x18]
    test ecx, ecx
    jz support_done
    mov [ebp-4], ecx
    call object_owner
    test eax, eax
    jz support_done
    cmp dword ptr [eax+0x5c], 1
    jne support_done
    mov edx, [eax+0x54]
    cmp edx, PLAYER_COUNT
    jae support_done
    bt dword ptr [ai_recipients], edx
    jnc support_done
    mov edi, eax
    mov eax, [GAME_LOGIC]
    test eax, eax
    jz support_done
    mov ecx, [eax+0x40]
    cmp ecx, [ai_next_frame+edx*4]
    jb support_done
    lea ebx, [ecx+SUPPORT_INTERVAL]
    mov [ai_next_frame+edx*4], ebx
    mov esi, [eax+0xac]

    # Copy the destination before sending any orders since the engine may
    # have supplied a temporary or a pointer into another unit.
    mov eax, [ebp+12]
    mov ecx, [eax]
    mov [ebp-20], ecx
    mov ecx, [eax+4]
    mov [ebp-16], ecx
    mov ecx, [eax+8]
    mov [ebp-12], ecx
support_next:
    test esi, esi
    jz support_done
    mov eax, [esi+0x8c]
    mov [ebp-8], eax
    cmp esi, [ebp-4]
    je support_advance
    # Destroyed, under construction, unselectable, sold, busy attacking or
    # explicitly refusing AI attacks, horde rank and file, or outside world.
    test dword ptr [esi+0x94], 0x97c8202d
    jnz support_advance
    test dword ptr [esi+0x98], 0x000e004f
    jnz support_advance
    mov ecx, esi
    call is_unit
    test eax, eax
    jz support_advance
    # Combat units only. Keep builders and resource workers at their jobs.
    mov eax, [esi+4]
    test byte ptr [eax+0x108], 0x08
    jz support_advance
    test byte ptr [eax+0x109], 0xc0
    jnz support_advance
    test byte ptr [eax+0x10a], 0x01
    jnz support_advance
    test byte ptr [eax+0x119], 0x80
    jnz support_advance

    mov ecx, [ebp-4]
    movss xmm0, [esi+0x38]
    subss xmm0, [ecx+0x38]
    mulss xmm0, xmm0
    movss xmm1, [esi+0x3c]
    subss xmm1, [ecx+0x3c]
    mulss xmm1, xmm1
    addss xmm0, xmm1
    movss xmm1, [support_radius_squared]
    ucomiss xmm1, xmm0
    jb support_advance

    mov ecx, esi
    call object_owner
    mov edx, eax
    mov ecx, edi
    call has_grant
    test eax, eax
    jz support_advance
    mov ebx, [esi+0x260]
    cmp dword ptr [ebx+0x30], 0
    je support_advance
    cmp dword ptr [ebx+0x34], 0
    jne support_advance
    mov ecx, ebx
    call ai_state
    test eax, eax
    jnz support_advance
    push 0                          # same source as the AI's leading order
    push 0x7fffffff
    lea eax, [ebp-20]
    push eax
    lea ecx, [ebx+0x20]
    call attack_move_original
support_advance:
    mov esi, [ebp-8]
    jmp support_next
support_done:
    pop edi
    pop esi
    pop ebx
    leave
    ret

.balign 4
support_radius_squared: .float 250000.0

# Intercept only the new status-table row callbacks. Everything else goes through
# the already installed chat-mute handler.
on_status_row:
    pushad
    mov eax, [esp+0x24]
    call status_control
    test eax, eax
    popad
    jz original_status
    ret 4
original_status:
    jmp original_status_hook

# ECX = status page, EAX = row callback string.
status_control:
    test eax, eax
    jz status_unknown
    mov edx, [eax]
    cmp edx, 0x3d716373                  # scq=
    je status_known
    cmp edx, 0x3d676373                  # scg=
    je status_known
    cmp edx, 0x3d726373                  # scr=
    jne status_unknown
status_known:
    push ebp
    mov ebp, esp
    sub esp, 20
    push ebx
    push esi
    push edi
    mov [ebp-4], edx
    mov [ebp-8], eax
    mov dword ptr [ebp-12], 0
    movzx ebx, byte ptr [eax+4]
    sub ebx, '0'
    cmp ebx, ROW_COUNT
    jae status_done
    cmp dword ptr [eax+5], 0x6d616e26     # &nam
    jne status_done
    cmp word ptr [eax+9], 0x3d65         # e=
    jne status_done
    cmp byte ptr [eax+11], 0
    je status_done
    cmp ebx, [ecx+0x6c]
    jae status_done
    imul ebx, ebx, 12
    mov edi, [ecx+ebx+0x74]
    mov ebx, [PLAYER_LIST]
    test ebx, ebx
    jz status_done
    mov esi, [ebx+0x10]
    cmp esi, edi
    je status_hidden
    call army_rule_enabled
    test al, al
    jz status_hidden
    mov ecx, esi
    mov edx, edi
    call allied_pair
    test eax, eax
    jz status_disabled
    # Require the game roster to resolve the target to the row's current player.
    mov ecx, ebx
    push dword ptr [edi+0x54]
    call nth_player
    cmp eax, edi
    jne status_disabled
    cmp dword ptr [ebp-4], 0x3d716373
    je status_display
    mov edx, [edi+0x54]
    or edx, CONTROL_TAG
    cmp dword ptr [ebp-4], 0x3d676373
    jne status_send
    or edx, 0x100
status_send:
    push edx
    push dword ptr [esi+0x54]
    call queue_permission
    add esp, 8
status_display:
    mov eax, [esi+0x54]
    mov edx, [edi+0x54]
    mov esi, offset state_off
    bt dword ptr [grants+eax*4], edx
    jnc status_render
    mov esi, offset state_on
    jmp status_render
status_disabled:
    mov esi, offset state_disabled
    jmp status_render
status_hidden:
    mov esi, offset state_hidden
status_render:
    mov eax, [ebp-8]
    add eax, 11
    push eax
    call apt_scope
    add esp, 4
    cmp eax, 13
    ja status_done
    mov [ebp-16], eax
    mov eax, [ebp-8]
    add eax, 11
    push eax
    call apt_row_name
    add esp, 4
    push eax
    push offset share_path
    lea eax, [ebp-12]
    push eax
    call format_ansi
    add esp, 12
    mov eax, [ebp-12]
    test eax, eax
    jz status_release_string
    add eax, 8
    mov ecx, [APT]
    test ecx, ecx
    jz status_release_string
    push 0
    push 0
    push 0
    push 0
    push esi
    push 1
    push offset share_state_method
    push eax
    push dword ptr [ebp-16]
    call apt_invoke
status_release_string:
    lea ecx, [ebp-12]
    call free_ansi
status_done:
    pop edi
    pop esi
    pop ebx
    leave
    mov eax, 1
    ret
status_unknown:
    xor eax, eax
    ret

# queue_permission(sender, taggedRecipient), cdecl.
queue_permission:
    push ebp
    mov ebp, esp
    push esi
    mov ecx, [MESSAGE_STREAM]
    test ecx, ecx
    jz queue_done
    mov eax, [ecx]
    push DONATION_MESSAGE
    call dword ptr [eax+0x48]
    mov esi, eax
    test esi, esi
    jz queue_done
    push dword ptr [ebp+8]
    mov ecx, esi
    call append_int
    push dword ptr [ebp+12]
    mov ecx, esi
    call append_int
    push 0
    mov ecx, esi
    call append_int
queue_done:
    pop esi
    leave
    ret

share_path: .asciz "%s.ShareArmy"
share_state_method: .asciz "SetShareState"
state_off: .asciz "_audible"
state_on: .asciz "_muted"
state_disabled: .asciz "_disabled"
state_hidden: .asciz "_hidden"

.global new_lobby_rule_defaults

# ReadLobbyRules epilogue for both multiplayer hosts. Keep saved preferences
# for every other rule and preserve live changes made by the host.
new_lobby_rule_defaults:
    cmp dword ptr [edi+0x14], 0
    jne lobby_rules_return
    mov edx, [esp+0x14]
    mov dword ptr [edx+9*4], 0
    mov dword ptr [edx+SHARED_ARMY_RULE*4], 0
lobby_rules_return:
    pop ecx
    pop ecx
    pop edi
    pop esi
    ret 4

# Use the GameInfo installed for the battle. The native recorder's
# mode-specific sources also cover matches without an installed GameInfo.
army_rule_enabled:
    mov edx, [GAME_LOGIC]
    test edx, edx
    jz share_rule_unavailable
    mov eax, [MATCH_GAME_INFO]
    test eax, eax
    jnz share_rule_read
    mov eax, [edx+0x114]
    cmp eax, 1
    je share_rule_network
    cmp eax, 2
    je share_rule_online
    test eax, eax
    jnz share_rule_unavailable
    mov eax, [SKIRMISH_GAME_INFO]
    jmp share_rule_read
share_rule_online:
    mov eax, [0xde7d6c]
    jmp share_rule_read
share_rule_network:
    mov ecx, [0xde4394]
    test ecx, ecx
    jz share_rule_unavailable
    mov eax, [ecx]
    call dword ptr [eax+0xe0]
share_rule_read:
    test eax, eax
    jz share_rule_unavailable
    cmp dword ptr [eax+0x5c], 0
    je share_rule_read_option
    # The standard single-player lobby copies all ten rules into its
    # GameInfo while leaving the game type at the constructor default -1.
    cmp dword ptr [eax+0x5c], -1
    jne share_rule_unavailable
    cmp eax, [SKIRMISH_GAME_INFO]
    jne share_rule_unavailable
    mov edx, [GAME_LOGIC]
    cmp dword ptr [edx+0x110], GAME_MODE_SKIRMISH
    jne share_rule_unavailable
share_rule_read_option:
    cmp dword ptr [eax+0x60+SHARED_ARMY_RULE*4], 1
    sete al
    movzx eax, al
    ret
share_rule_unavailable:
    xor eax, eax
    ret

# The same index can mean a strategic rule in another game type.
share_rule_label:
    cmp dword ptr [esp+8], SHARED_ARMY_RULE
    jne stock_rule_name
    cmp dword ptr [esp], 0x9868c9
    je share_rule_fetch_label
    mov eax, [LOBBY_UI]
    test eax, eax
    jz stock_rule_name
    cmp dword ptr [eax+0x7c], 0
    jne stock_rule_name
share_rule_fetch_label:
    mov ecx, [TEXT_MANAGER]
    mov edx, [ecx]
    mov eax, [esp+4]
    push 0
    push offset share_rule_key
    push eax
    call dword ptr [edx+0x3c]
    mov eax, [esp+4]
    ret

share_rule_key: .asciz "RULE:ShareArmy"
.balign 4
rts_checkboxes:
    .long 0xc82528, 0xc82530, 0xf4e2ec, share_rule_default, 0xc82538
share_rule_default:
    .long SHARED_ARMY_RULE, 0

.global set_weather_effect_color, expire_weather_effect_color
.global tint_weather_vertices, tint_weather_particle
.equ WEATHER_STATE, 0xde772c
.equ WEATHER_COLOR, 0xf4629c
.equ START_WEATHER, 0x71a024
.equ NATIVE_PARTICLE_COLOR, 0x5f4493

# The existing INI parser is shared by FreezingRainSpecialPower and
# CloudBreakSpecialPower. The upper byte selects the weather type. Only
# CLOUDY uses bit 24, which the existing scene-lighting hook tests.
set_weather_effect_color:
    push ecx
    mov ecx, [esp+8]
    xor eax, eax
    cmp ecx, 1
    jb store_weather_effect_color
    cmp ecx, 4
    ja store_weather_effect_color
    cmp byte ptr [ebx+0x69], 0
    je store_weather_effect_color
    mov eax, 0x01000000
    dec ecx
    shl eax, cl
    mov edx, [ebx+0x2c]
    shr edx, 8
    or eax, edx
store_weather_effect_color:
    mov [WEATHER_COLOR], eax
    pop ecx
    jmp START_WEATHER

expire_weather_effect_color:
    cmp byte ptr [WEATHER_COLOR+3], 1
    je expire_native_weather
    mov dword ptr [WEATHER_COLOR], 0
expire_native_weather:
    jmp START_WEATHER

# Select only the color of the weather currently in effect. The saved
# packed tint is ignored after expiry or for another weather type.
weather_effect_color:
    mov eax, [WEATHER_STATE]
    test eax, eax
    jz weather_color_inactive
    mov ecx, [eax+0x10]
    dec ecx
    cmp ecx, 3
    ja weather_color_inactive
    mov eax, [WEATHER_COLOR]
    add ecx, 24
    bt eax, ecx
    jnc weather_color_inactive
    ret
weather_color_inactive:
    xor eax, eax
    ret

# Both native precipitation paths build one grayscale ARGB before writing
# their vertices. Preserve the native intensity and alpha fade.
tint_weather_vertices:
    sub eax, 0x01000000
    push ecx
    push edx
    push ebx
    push eax
    call weather_effect_color
    test eax, eax
    jz map_vertex_color
    test eax, 0x08000000
    jz scale_weather_vertices
map_vertex_color:
    mov ecx, [0xde3b58]
    test ecx, ecx
    jz native_vertex_color
    call 0x465af4
    mov eax, [eax+0x54]
    shr eax, 8
    cmp eax, 0xffffff
    je native_vertex_color
scale_weather_vertices:
    mov ebx, eax
    movzx ecx, byte ptr [esp]
    movzx eax, bl
    call weather_color_channel
    shl eax, 16
    and dword ptr [esp], 0xff000000
    or [esp], eax
    movzx eax, bh
    call weather_color_channel
    shl eax, 8
    or [esp], eax
    shr ebx, 16
    movzx eax, bl
    call weather_color_channel
    or [esp], eax
native_vertex_color:
    pop eax
    pop ebx
    pop edx
    pop ecx
    ret
weather_color_channel:
    imul eax, ecx
    add eax, 128
    mov edx, eax
    shr edx, 8
    add eax, edx
    shr eax, 8
    ret

# Multiply the rendered FX color of the weather particle templates. The
# system references its original template at +0x198. The template owns
# the INI name at +0x9c. Native simulation colors and opacity stay intact.
tint_weather_particle:
    push ebx
    push esi
    mov esi, ecx
    mov ecx, [ecx+0x94]
    call NATIVE_PARTICLE_COLOR
    mov ebx, eax
    test ebx, ebx
    jz finish_weather_particle
    call weather_effect_color
    test eax, eax
    jz finish_weather_particle
    mov ecx, [esi+0x3c]
    test ecx, ecx
    jz finish_weather_particle
    mov ecx, [ecx+0x198]
    test ecx, ecx
    jz finish_weather_particle
    mov ecx, [ecx+0x9c]
    test ecx, ecx
    jz finish_weather_particle
    lea esi, [ecx+8]
    push eax
    test eax, 0x08000000
    jnz check_cloud_rays
    mov edx, offset fx_snowflakes
    call weather_name_prefix
    test eax, eax
    jnz shade_weather_particle
    mov edx, offset fx_storm_rain
    call weather_name_prefix
    jmp check_weather_particle
check_cloud_rays:
    mov edx, offset fx_cloudbreak_rays
    call weather_name_prefix
    test eax, eax
    jnz shade_weather_particle
    mov edx, offset fx_gildor_rays
    call weather_name_prefix
check_weather_particle:
    test eax, eax
    jnz shade_weather_particle
    add esp, 4
    jmp finish_weather_particle
shade_weather_particle:
    pop edx
    sub esp, 16
    movups [esp], xmm0
    mov eax, offset tinted_fx_color
    .irp channel, 0,4,8
        movzx ecx, dl
        cvtsi2ss xmm0, ecx
        mulss xmm0, dword ptr [0xbd1920]
        mulss xmm0, dword ptr [ebx+\channel]
        movss dword ptr [eax+\channel], xmm0
        shr edx, 8
    .endr
    movups xmm0, [esp]
    add esp, 16
    mov ebx, eax
finish_weather_particle:
    mov eax, ebx
    pop esi
    pop ebx
    ret

# Compare the INI name in ESI with a lowercase prefix in EDX.
weather_name_prefix:
    xor ecx, ecx
weather_name_next_char:
    mov al, [edx+ecx]
    test al, al
    jz weather_name_matched
    mov ah, [esi+ecx]
    or ah, 0x20
    cmp al, ah
    jne weather_name_mismatch
    inc ecx
    jmp weather_name_next_char
weather_name_matched:
    mov eax, 1
    ret
weather_name_mismatch:
    xor eax, eax
    ret

fx_snowflakes: .asciz "snowflakesrain"
fx_storm_rain: .asciz "weatherstormrain"
fx_cloudbreak_rays: .asciz "cloudbreakrays"
fx_gildor_rays: .asciz "gildorcloudbreakrays"
.balign 4
tinted_fx_color: .space 12

.global initialize_weather_settings, parse_map_weather_tint, weather_field_table, weather_field_name
.equ NATIVE_RGB_PARSE, 0x42ef99
.equ WEATHER_SETTINGS_CONTINUE, 0x6010cb

# Store the optional tint beside SnowPointSprites in WeatherSettings'
# three padding bytes. Map overlays inherit it through the native copy.
initialize_weather_settings:
    mov dword ptr [esi+0x54], 0xffffff00
    mov dword ptr [esi+0x64], 30
    jmp WEATHER_SETTINGS_CONTINUE

parse_map_weather_tint:
    push ebp
    mov ebp, esp
    sub esp, 12
    push dword ptr [ebp+0x14]
    lea eax, [ebp-12]
    push eax
    push dword ptr [ebp+0x0c]
    push dword ptr [ebp+0x08]
    call NATIVE_RGB_PARSE
    add esp, 16
    mov eax, [ebp+0x10]
    .irp channel, 0,1,2
        movss xmm0, dword ptr [ebp-12+4*\channel]
        mulss xmm0, dword ptr [0xf46294]
        addss xmm0, dword ptr [0xf46298]
        cvttss2si edx, xmm0
        mov [eax+\channel], dl
    .endr
    leave
    ret

weather_field_name: .asciz "DarkeningFactor"
.balign 4
weather_field_table: .space 0x210
