# 07. Wall climbing for Corsairs, Goblins, and spiders

Wall climbing depends on the unit and wall configuration and on the quick horde movement fallback. The data and the fallback branch were tested. The route and `CLIMBING` animation still need confirmation in a running match.

## Configure the climbers

Append `CAN_CLIMB_WALLS` to each relevant object's existing `KindOf` line. Add it to the horde, its members, and the banner carrier. Inherited templates should retain their other flags.

| Path under `data/ini/object/` | Objects changed |
| --- | --- |
| `evilfaction/units/mordor/mordorcorsairsofumbar.ini` | `MordorCorsairsOfUmbar` |
| `evilfaction/units/mordor/mordorcorsairbanner.ini` | `MordorCorsairBanner` |
| `evilfaction/hordes/mordor/mordorhordes.ini` | `MordorCorsairsOfUmbarHorde`, `MordorCorsairsOfUmbarHordeFree`, `WildCorsairsOfUmbarHordeFree`, `IronHillsBanditen_KampagneHorde` |
| `evilfaction/units/harad/haradcorsairsofumbar.ini` | `HaradCorsairsOfUmbar` |
| `evilfaction/units/harad/haradbanner.ini` | `HaradCorsairBanner` |
| `evilfaction/hordes/harad/haradhordes.ini` | `HaradCorsairsOfUmbarHorde` |
| `evilfaction/units/mordor/mordorspidercavalry.ini` | `MordorSpiderCavalry`. Its horde already carries the flag. |
| `evilfaction/units/wild/goblinfighter.ini` | `GoblinFighter`, `GoblinFighterGroork`, `GoblinFighterUpgraded_Summoned` |
| `evilfaction/hordes/wild/wildhordes.ini` | `GoblinFighterHorde`, `GoblinFighteGroorkHorde`, `GoblinFighterHorde_FromDefectedLair` |

For the Mordor and Harad Corsair members and the Mordor banner, remove the competing `HumanLocomotor` entry for `SET_NORMAL` so the existing `WallScalingMeleeHordeLocomotor` entry is the only match. For `HaradCorsairBanner`, replace `HumanLocomotor` with `WallScalingMeleeHordeLocomotor` in its normal set and retain its speed. Keep the existing `AnimationState = CLIMBING` blocks.

Check the active climbing locomotor in `data/ini/locomotor.ini`. The existing `WallScalingMeleeHordeLocomotor` includes these fields.

```ini
    ScalesWalls = Yes
    ZAxisBehavior = SCALING_WALLS
```

## Make the wall segments climbable

Append `SCALEABLE_WALL` to the `KindOf` of the actual segment built by the wall hub. Spelling is significant. Keep the segment's collision geometry and built-in wall bounds. Apply this to the following segment templates.

| Faction | Segment objects |
| --- | --- |
| Gondor | `GondorCastleWallSegment`, `MenWallSegmentSmall` |
| Arnor | `ArnorCastleWallSegment`, `ArnorWallSegmentSmall` |
| Dwarves | `DwarvenWallSegmentSmall`, `DwarvenCastleWallSegment` |
| Elves | `ElvenCastleWallSegment` |
| Rohan | `RohanCastleWallSegment` |
| Angmar | `AngmarWallSegmentSmall` |
| Isengard | `IsengardCastleWallSegment`, `IsengardCastleWallSegmentPlayer` |
| Mordor | `MordorCastleWallSegmentNew` |
| Dol Guldur | `DolguldurCastleWallSegment` |

The patch targets wall segments. Test the center of a straight section between hubs, away from gates and towers. A map-specific wall object may have its own `KindOf` and geometry.

## Engine fallback

The quick movement path can assign the formation destination after a rejected step when it cannot find a local path. The hook at virtual address `0x0066CCD8` makes an eligible climber wait for the next native path update. It requires both `CAN_CLIMB_WALLS` and an active locomotor with `ScalesWalls`. All other cases resume the original continuation. The expected original bytes are `8B 75 F4 81 C6 00 02 00 00`. Install a relative jump to the handler and pad the remainder of the overwritten span with NOPs. The final engine build in [08](special-power-money-cost.md) installs this hook.

```asm
wall_path_fallback:
    mov esi, [ebp-0xc]
    mov eax, [ebx+4]
    test byte ptr [eax+0x11f], 1
    jz default_goal
    mov eax, [esi+0x1f0]
    test eax, eax
    jz default_goal
    mov eax, [eax+4]
    cmp byte ptr [eax+0x150], 0
    jne retry_next_tick
default_goal:
    add esi, 0x200
    jmp 0x66cce1
retry_next_tick:
    jmp 0x66d166
```

The test configuration uses `HordesWaitForHordes = No` in `data/ini/default/aidata.ini`. The tests verify the fallback branch. The effect of changing that global setting on the reported bug remains unconfirmed.

## In-game verification

1. Build several connected climbable segments in a new skirmish and order a Corsair horde to a point directly across the center of the wall. Test a veteran horde with its banner as well.
2. Inspect individual members for the `CLIMBING` animation and make sure they reach the far side. Repeat with Goblin Fighters and Mordor spiders. Use ordinary infantry on the same wall as a control.
3. If the Corsairs detour, inspect the template of the actual segment, the active `SET_NORMAL` locomotor for the members, and the `KindOf` on both levels of the horde. Use a longer wall so walking around has a meaningful path cost.

[Open-BFME-2 pathfinding reference](https://github.com/Open-BFME/Open-BFME-2/blob/e2e99959950e6eebfe1ced5663aa05de320afc52/Code/GameEngine/Source/GameLogic/Object/Update/AIUpdateInterface_computePath.cpp) · [pySAGE horde movement notes](https://github.com/ClementJ18/pySAGE/blob/0a1f1b5d71b1b080008a7e9fff6f997601ec5a7f/sage_patch/docs/horde-formation-orphans.md)
