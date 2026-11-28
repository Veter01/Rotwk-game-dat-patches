.intel_syntax noprefix
.text
.global group_right_click
group_right_click:
    cmp byte ptr [ebp+0xc],0
    jne .manual_click
    pushad
    push esi
    push edi
    call toggle_group
    add esp,8
    test eax,eax
    popad
    jnz finish_click
    jmp .native_click
.manual_click:
    cmp dword ptr [edi+0x70],7
    jne .native_click
    cmp dword ptr [edi+0x6c],0
    jne .native_click
    test byte ptr [esi+0x1d],1
    jz refuse_click
.native_click:
    test ebx,ebx
    jz no_representative
    push ebx
    mov ecx,esi
    jmp native_click

# Show a shared autocast button even without OK_FOR_MULTI_SELECT. The click hook
# still checks that flag for the corresponding left-click path above.
.global seed_autocast_button
seed_autocast_button:
    test byte ptr [ebx+0x1d],1
    jnz seed_button
    cmp byte ptr [ebx+0x10c],0
    je skip_button
    cmp dword ptr [ebx+0x14],0x17
    je seed_button
    cmp dword ptr [ebx+0x14],0x18
    je seed_button
    jmp skip_button

# The tooltip sets ESI to an inner string on the missing-requirements path.
# Save the real command button while the original tooltip descriptor is live.
.global remember_tooltip_button
remember_tooltip_button:
    mov eax,[esi+0xc]
    mov [ebp-0x50],eax
    mov eax,[eax+0x14]
    jmp tooltip_command_resume

.global tooltip_price
tooltip_price:
    lea eax,[ebp-0x54]
    push eax
    push dword ptr [ebp-0x1c]
    push dword ptr [ebp-0x20]
    push dword ptr [ebp-0x24]
    push dword ptr [ebp-0x50]
    call upgrade_price_range
    add esp,20
    mov [ebp-0x50],eax
    xor edi,edi
    cmp [ebp-0x54],edi
    jle no_price
    jmp price_prefix

.global tooltip_suffix
tooltip_suffix:
    mov eax,[ebp-0x54]
    cmp eax,[ebp-0x50]
    jle no_price
    push eax
    lea eax,[ebp-0x28]
    push eax
    call append_price_range
    add esp,8
    jmp no_price

.global remember_upgrade_button
remember_upgrade_button:
    mov [ebp-0x50],esi
    mov edi,[esi+0x24]
    test edi,edi
    jmp upgrade_click_resume

.global group_upgrade_gate
group_upgrade_gate:
    push [esp+16]
    push [esp+16]
    push [esp+16]
    push [esp+16]
    push ecx
    push [ebp-0x50]
    push [ebp-0x14]
    call group_can_buy
    add esp,28
    ret 16

.global building_upgrade_role
building_upgrade_role:
    mov eax,[esp+4]
    jmp native_building_upgrade_role

.global combine_template_discounts
combine_template_discounts:
    cmp dword ptr [ebp+8],0
    je template_price_done
    cmp byte ptr [esi+0x79],0
    jne template_price_done
    push eax
    push esi
    add esi,8
    push ecx
    mov ecx,esp
    push esi
    call copy_string
    mov ecx,[ebp+8]
    call discount_query
    pop esi
    fadd dword ptr [one_value]
    fild dword ptr [esp]
    fmulp st(1),st
    fstp dword ptr [esp]
    cvttss2si eax,[esp]
    add esp,4
    test eax,eax
    jns template_price_done
    xor eax,eax
    jmp template_price_done

.section .rodata
one_value:
    .float 1.0
.section .note.GNU-stack,"",@progbits
