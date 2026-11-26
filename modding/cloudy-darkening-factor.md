# 02. Setting the CLOUDY color for a special power

**Status:** Implemented. Machine-code tests covered RGB parsing, color selection, reset, and serialization. Visual verification in ROTWK is still pending.

## INI configuration

Open `data/ini/object/system/includes/systemevil.inc`, or the file defining `OCLSpecialPower ModuleTag_DarknessWild` in your data. Find the behavior for `SpellBookDarknessWild` and add `DarkeningFactor` immediately after `ChangeWeather = CLOUDY`. Keep the existing OCL, duration, and spellbook requirements.

```ini
Behavior = OCLSpecialPower ModuleTag_DarknessWild
    SpecialPowerTemplate = SpellBookDarknessWild
    OCL = OCL_DarknessWeatherChanger
    CreateLocation = CREATE_AT_LOCATION
    AttributeModifierWeatherBased = Yes
    WeatherDuration = SPELL_DARKNESS_DURATION
    ChangeWeather = CLOUDY
    DarkeningFactor = R:30 G:130 B:130
    AvailableAtStart = No
    RequirementsFilterMPSkirmish = SPELL_BOOK_REQUIREMENTS_FILTER
    RequirementsFilterStrategic = SPELL_BOOK_REQUIREMENTS_FILTER_STRATEGIC
End
```

Set each RGB component to an integer from 0 to 255. Omit the field to use the `CloudEffect` color from `environment.ini`. The executable supplies support for the new field.

## Implementation

1. The base `SpecialPowerModuleData` field table moves from `0x00C64DB0` to the `.pwrxtra` section. The patch copies all 35 original entries and adds `DarkeningFactor`. It updates the table reference at `0x008969A2`.
2. The handler calls the native RGB parser at `0x0042EF99` and stores three bytes next to the original flag at `+0x2C`. The presence flag is stored separately at `+0x69`, so black is a valid custom color. The constructor initializes both fields.
3. The weather activation hook at `0x00897B45` sets the current cloud color. A subsequent `CLOUDY` cast with no custom color restores the default. The hook at `0x00494DE0` supplies the RGB values to the native fade code.
4. Resetting the weather clears the custom state. Version 5 of the save game's weather block stores the color. Loading an original version 4 block falls back to the environment color. Use a save made before installing the patch when switching back to the original engine.

<details>
<summary><code>inspection/next/cloudy.s</code></summary>

```asm
.intel_syntax noprefix
.code32
.section .text

# Native INI RGB parsing into a local, then compress its three INI octets
# into SpecialPowerModuleData's padding adjacent to its +0x2c bool.
weather_parse_rgb:
    push ebp
    mov ebp, esp
    sub esp, 12
    push dword ptr [ebp+0x14]
    lea eax, [ebp-12]
    push eax
    push dword ptr [ebp+0xc]
    push dword ptr [ebp+8]
    call 0x42ef99
    add esp, 16
    mov eax, [ebp+0x10]
    movss xmm0, dword ptr [rgb_max]
    movss xmm1, [ebp-12]
    mulss xmm1, xmm0
    addss xmm1, dword ptr [rgb_half]
    cvttss2si edx, xmm1
    mov [eax+1], dl
    movss xmm1, [ebp-8]
    mulss xmm1, xmm0
    addss xmm1, dword ptr [rgb_half]
    cvttss2si edx, xmm1
    mov [eax+2], dl
    movss xmm1, [ebp-4]
    mulss xmm1, xmm0
    addss xmm1, dword ptr [rgb_half]
    cvttss2si edx, xmm1
    mov [eax+3], dl
    mov byte ptr [eax+0x3d], 1
    leave
    ret

# Retain the last cloudy tint for its native fade-out. An uncoloured CLOUDY
# cast restores the environment settings, including between two cloudy casts.
weather_cast:
    cmp dword ptr [esp+4], 1
    jne weather_apply
    xor eax, eax
    cmp byte ptr [ebx+0x69], 0
    je weather_store
    mov eax, [ebx+0x2c]
    shr eax, 8
    or eax, 0x01000000
weather_store:
    mov dword ptr [current_tint], eax
weather_apply:
    jmp 0x71a024

weather_reset:
    mov dword ptr [current_tint], 0
    push esi
    mov esi, ecx
    push edi
    push dword ptr [esi+0x14]
    jmp 0x719fe2

weather_xfer:
    cmp byte ptr [ebp-3], 5
    jb weather_xfer_legacy
    mov ecx, edi
    mov eax, [edi]
    push offset current_tint
    call dword ptr [eax+0x78]
    jmp weather_xfer_done
weather_xfer_legacy:
    mov dword ptr [current_tint], 0
weather_xfer_done:
    pop edi
    pop esi
    leave
    ret 4

# Called at the original CloudEffect base colour copy. Preserve the flags
# from the fade-state test before the immediately following branch.
weather_copy_rgb:
    pushfd
    push eax
    mov eax, dword ptr [current_tint]
    test eax, 0x01000000
    jz weather_stock_rgb
    cmp dword ptr [ebx+0xbc], 1
    ja weather_stock_rgb
    sub esp, 16
    movups [esp], xmm0
    movzx esi, al
    cvtsi2ss xmm0, esi
    mulss xmm0, dword ptr [0xbd1920]
    movss [edi], xmm0
    shr eax, 8
    movzx esi, al
    cvtsi2ss xmm0, esi
    mulss xmm0, dword ptr [0xbd1920]
    movss [edi+4], xmm0
    shr eax, 8
    movzx esi, al
    cvtsi2ss xmm0, esi
    mulss xmm0, dword ptr [0xbd1920]
    movss [edi+8], xmm0
    lea edi, [edi+12]
    lea esi, [ebx+0x3c]
    movups xmm0, [esp]
    add esp, 16
    jmp weather_rgb_done
weather_stock_rgb:
    lea esi, [ebx+0x30]
    movsd
    movsd
    movsd
weather_rgb_done:
    pop eax
    popfd
    jmp 0x494de6

.balign 4
rgb_max: .float 255.0
rgb_half: .float 0.5
current_tint: .long 0
```

</details>

The source file in [03](phantom-structure-check.md) includes this file. See [10](negative-experience.md) for the build, the remaining hook addresses, and the output checksum.

## In-game verification

Start a fresh Goblin skirmish, unlock Darkness, and cast it over a well-lit area. Check the transition into the custom tint and the return to normal lighting.

1. Cast `CLOUDY` with a teal RGB color. Check the tint, its duration, and the fade back to the normal color.
2. Before the effect ends, cast a second `CLOUDY` power with no custom color. It should use the value from `environment.ini`.
3. Save while the custom color is active and reload with the same build. Also try loading an older save with a version 4 weather block.

Ostkannit's weather research helped identify the rendering path. [pySAGE documentation](https://github.com/ClementJ18/pySAGE/blob/0a1f1b5d71b1b080008a7e9fff6f997601ec5a7f/sage_patch/docs/foggy-weather.md)
