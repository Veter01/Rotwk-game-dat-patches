# 03. Checking for construction sites in SpecialPower

**Status:** Implemented. Emulation covered both targeting paths, the construction flags, the filter, and the distance boundary. Verification in a running match is pending.

## INI configuration

```ini
SpecialPower SpecialAbilityToggleBalhothCampPack
    Enum = SPECIAL_TOGGLE_MOUNTED
    ReloadTime = 30000
    Flags = NO_FORBIDDEN_OBJECTS
    ForbiddenObjectFilter = ANY +STRUCTURE
    ForbiddenObjectRange = 50
    RadiusCursorRadius = 50
    PhantomStructureCheck = Yes
End
```

If the existing power already sets the relevant flag, filter, and radius, add `PhantomStructureCheck = Yes`. Keep the power's other flags and settings. The build also accepts `PhantomStrucrureCheck`, the spelling used in the original specification.

## Rohan's 25-point camp

Open `data/ini/includes/specialpower.inc` and edit the existing `SpecialPower SpellBookSummonHeerlager` block. Keep `RequiredSciences = SCIENCE_Heerlager` and `Flags = NO_FORBIDDEN_OBJECTS RESPECT_RECHARGE_TIME_DISCOUNT`. Keep both `ForbiddenObjectRange` and `RadiusCursorRadius` at `130.0`.

1. Find `NO_SUMMON_CITADEL_NEAR_OBJECT_FILTER` in `data/ini/_gamedata.inc`.
2. Replace the camp's `ForbiddenObjectFilter` value with the full contents of that macro, followed by `+STRUCTURE`. Keep every original filter entry. This sets the structure rule for the camp specifically.
3. Add `PhantomStrucrureCheck = Yes` to the camp's `SpecialPower` block. Both the original spelling and `PhantomStructureCheck` resolve to the same field.
4. Keep `SciencePurchasePointCostMP = 25` in `Science SCIENCE_Heerlager` in `data/ini/science.ini`.

## Implementation

The patch increases the size of `SpecialPowerTemplate` from `0x88` to `0x8C`. The constructor zeroes the field at `+0x88`, and the template copy routine preserves it. Both INI table references point to the extended table. The check uses the final resolved template after overrides.

The engine first runs the existing check for ordinary buildings. When `NO_FORBIDDEN_OBJECTS` is set and `PhantomStructureCheck` is enabled, an additional pass checks the game logic objects. The check uses the same flags for unfinished construction as the build's existing `.bldcap` code. It measures two-dimensional distance from the target center and evaluates `ForbiddenObjectFilter` through the native `ObjectFilter`.

| Hook | Purpose |
|---|---|
| `0x0082E128` | Check casts aimed at a position. |
| `0x0082DA69` | Check nearby forbidden objects on the object-targeting path. |
| `0x007B1ABE`, `0x007B2325` | Both references to the `SpecialPower` field table. |

The listing below builds the initial optional check. Apply the live construction-status correction described after it.

<details>
<summary><code>inspection/next/power_extras.s</code></summary>

```asm
.intel_syntax noprefix
.code32
.section .text

power_template_init:
    mov [esi+0x84], ebx
    mov [esi+0x88], ebx
    jmp 0x7b2013

power_template_copy:
    mov eax, [ebp+0x88]
    mov [ebx+0x88], eax
    mov eax, ebx
    pop esi
    pop ebp
    pop ebx
    ret 4

# Call sites retain the stock result and add the opt-in scan.
phantom_location_gate:
    push ebp
    mov ebp, esp
    push dword ptr [ebp+0x10]
    push dword ptr [ebp+0x0c]
    push dword ptr [ebp+0x08]
    call 0x82d2fd
    test al, al
    jz phantom_location_done
    push dword ptr [ebp+0x10]
    push dword ptr [ebp+0x0c]
    push dword ptr [ebp+0x08]
    call phantom_refuses
    xor al, 1
phantom_location_done:
    pop ebp
    ret 12

phantom_object_gate:
    push dword ptr [esp+4]
    call 0x82c366
    test al, al
    jnz phantom_object_done
    mov eax, [ebp+0xc]
    test eax, eax
    jz phantom_object_done
    add eax, 0x38
    push dword ptr [ebp+0x14]
    push eax
    push ebx
    call phantom_refuses
phantom_object_done:
    ret 4

# stdcall(caster, position, template). Pending construction structures are inert
# and may not exist in the spatial query that checks ordinary buildings.
phantom_refuses:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    sub esp, 4
    mov ecx, [ebp+0x10]
    test ecx, ecx
    jz phantom_allow
    call 0x688d3c
    cmp byte ptr [eax+0x88], 0
    je phantom_allow
    test byte ptr [eax+0x18], 0x10
    jz phantom_allow
    mov esi, [ebp+0xc]
    test esi, esi
    jz phantom_allow
    xorps xmm0, xmm0
    movss xmm1, [eax+0x7c]
    ucomiss xmm1, xmm0
    jb phantom_allow
    mulss xmm1, xmm1
    movss [ebp-0x10], xmm1
    lea edi, [eax+0x78]
    mov ecx, dword ptr [0xde412c]
    test ecx, ecx
    jz phantom_allow
    call 0x97338f
    mov ebx, eax
phantom_scan:
    test ebx, ebx
    jz phantom_allow
    test byte ptr [ebx+0x458], 1
    jz phantom_next
    test byte ptr [ebx+0x9e], 0x80
    jz phantom_next
    test byte ptr [ebx+0x9f], 1
    jz phantom_next
    movss xmm0, [ebx+0x38]
    movss xmm1, [ebx+0x3c]
    subss xmm0, [esi]
    subss xmm1, [esi+4]
    mulss xmm0, xmm0
    mulss xmm1, xmm1
    addss xmm0, xmm1
    ucomiss xmm0, [ebp-0x10]
    jp phantom_next
    ja phantom_next
    push dword ptr [ebp+8]
    push ebx
    mov ecx, edi
    call 0x7640c1
    test al, al
    jnz phantom_deny
phantom_next:
    mov ebx, [ebx+0x8c]
    jmp phantom_scan
phantom_allow:
    xor eax, eax
    jmp phantom_end
phantom_deny:
    mov eax, 1
phantom_end:
    add esp, 4
    pop edi
    pop esi
    pop ebx
    pop ebp
    ret 12

.include "inspection/next/cloudy.s"
.include "inspection/next/banner_down.s"
```

</details>

The build script and commands are in [10](negative-experience.md). This file includes the weather handlers from [02](cloudy-darkening-factor.md) and the banner removal handler from [10](negative-experience.md).

## Live construction-status correction

A builder can create a pending, phantom structure as soon as the player confirms the order. The earlier scan read a byte at `object+0x458` that the builder leaves unset, skipping these live sites. Read the native `DESTROYED` bit at `object+0x94` and skip the object when that bit is set. Keep the `PENDING_CONSTRUCTION` and `PHANTOM_STRUCTURE` tests at `+0x9E` and `+0x9F`.

For the assembly listing above, replace the first two instructions in this sequence with the following pair.

```asm
    test byte ptr [ebx+0x94], 1
    jnz phantom_next
    test byte ptr [ebx+0x9e], 0x80
    jz phantom_next
    test byte ptr [ebx+0x9f], 1
    jz phantom_next
```

To patch the assembled code, locate offset `+0xDB` in `.pwrxtra` and require the exact old bytes. The final engine build in [08](special-power-money-cost.md) applies this correction and preserves the following construction tests.

| | Bytes |
| --- | --- |
| Expected | `F6 83 58 04 00 00 01 74 48` |
| Replacement | `F6 83 94 00 00 00 01 75 48` |

## In-game verification

1. In a new Rohan skirmish, unlock the camp. Order a builder to construct a building far enough away that the builder must walk to it.
2. While the builder is walking to the confirmed site, try placing the camp on the site. Expect the placement to be rejected within 130 units of the pending structure. Check an unobstructed position outside the radius.
3. Cancel the build order. Once the pending site is removed, the camp should be placeable if the other placement conditions are met.
4. For another power such as the Balhoth camp or a Lothlórien seal, enable the option on that power's own template and repeat with finished and unfinished buildings.

An unconfirmed building preview under the mouse is local to the UI. The simulation checks sites created by confirmed build orders.
