# 05. Experience and power points with DelayedDeathBody

**Status:** Implemented and machine-code tested. XP and power point awards still need an in-game check.

## Cause

`DelayedDeathBody` keeps an object alive for a short time after its health reaches zero. A subsequent hit that leaves health unchanged could exit before refreshing the previous health value. The award logic could then reuse the last health delta and award the same experience and power points again.

## Fix

Replace the six-byte conditional jump at `0x008C555E` with a jump into `.modext1`. The new handler checks PF for an unordered comparison and keeps the original path for that result. On the zero-delta path it copies current health from `[esi+0x08]` to the previous health field at `[esi+0x0C]`, then returns to the native exit at `0x008C567A`.

The source is at the end of `engine_patch.s` in [01](filtered-horde-respawn-behavior.md), under `delayed_death_zero_delta`. The rebuilt executable automatically applies the fix to existing INI objects with delayed death.

## In-game verification

Use Haldir as a test target. Temporarily change the type of his existing `Body` to `DelayedDeathBody` and preserve the maximum health and any compatible fields.

```ini
        DelayedDeathTime = 15000
        ImmortalUntilDeathTime = Yes
```

1. Record the attacker's XP and power points before combat.
2. Reduce Haldir's health to zero. Record both values again so you can attribute the awards from the hit that brought him to zero.
3. Continue hitting Haldir during his death delay. These hits should give no further awards from the same health loss.
4. Let the delay expire normally. Separately test a hit on a target with positive health and combat against an object with the regular `ActiveBody`.

Use the same build and game data on both clients when comparing results.
