# Shared Army Control

In v9, enable **Shared Army Control** under **Rules** before starting the match. In the in-game **Players** window, check the box beside an ally to let that ally command your eligible units. Both players can then give orders. Clearing the box revokes the ally's ability to issue new orders. The local player's row has no share box.

Build and install `game.dat`, `playertribute.big`, and `apt/mpgamesetup.big` using the [repository instructions](../README.md#rebuild-the-patches).

## Rules and the Skirmish fix

| File or hook | Implementation |
| --- | --- |
| `MpGameSetup.apt`, sprites 10 and 189 | Clone the placement for checkbox `3` into a fifth checkbox named `4`. Both standard Rules layouts bind it to rule index 8. |
| `0x960A40`, `0x960A70` | Point the native UI at the expanded checkbox table, which includes the new index and its unchecked default. |
| `0x960B14` | Resolve `RULE:ShareArmy` using GameText in the RTS rules UI. |
| `0x85085F` | After loading new-lobby preferences for standard RTS, clear rule 8 and the existing Random Teams rule at index 9. The host can enable either rule for the current room. |
| `army_rule_enabled` | Read the running match's GameInfo first. The ten rule values start at `GameInfo + 0x60`, so rule 8 is at `+0x80`. The value `1` enables sharing. |

The v8 reader required the GameInfo type at `+0x5C` to be zero. The standard single-player Skirmish lobby copies the rules into its GameInfo while keeping that field at the constructor default `-1`. This left the share column empty even with the rule checked.

The v9 reader accepts `-1` only when the GameInfo is the native Skirmish object from `0xDE8930` and `GameLogic + 0x110` identifies Skirmish mode `2`. It prefers the installed match object at `0xDE892C` and consults the mode's normal GameInfo source when that pointer is absent. Strategic rule layouts still use their own interpretation of index 8.

Rules UI builder (`src/shared_army/build_rules.py`) · Executable build and hook bytes (`src/shared_army/build_game.py`) · x86 implementation (`src/shared_army/shared_army.s`)

## Players table and synchronized grants

Expand the status table in `PlayerTribute.apt` sprite 61 and add the row control in sprite 51. Reuse the checkbox artwork in separate characters with the `ShareArmy` clip, and extend the table divider in `PlayerTribute_geometry/59.ru`. The control starts hidden and asks the engine for its current state. The existing Block control continues to use its own callbacks.

| APT callback | Purpose |
| --- | --- |
| `scq=` | Query the row and pick the checkbox state. |
| `scg=` | Request a grant for the row's player. |
| `scr=` | Request revocation for the row's player. |

The handler at `0x915E00` hides the checkbox for the local row or when the match rule is off. With the rule on, an eligible allied row has an interactive control. Enemy or ineligible rows use the disabled state. The Players dialog resolves a row to its current in-game roster entry before queuing a change.

The UI sends a tagged message through the existing synchronized donation command `0x466`. The arguments are three integers.

```text
arg0 = sender player index
arg1 = 0x53480000 | (0x100 if granting else 0) | recipient player index
arg2 = 0
```

The hook at `0x77CFB0` distinguishes these messages from resource donations. It verifies the match rule, argument types, sender identity, and active reciprocal alliance. Each owner has a bitset of recipients, with a bit set on grant and cleared on revoke. Match reset clears the bitsets. An allied AI with a valid grant can take nearby idle combat units into its attack move support group. This path skips builders, resource workers, and units that already have work. Players UI builder (`src/shared_army/build_player_tribute.py`)

## Orders, feedback, and camera

Selection and previews use the local player's permission. The synchronized order filters check the actual sender. The owning player can still control the units, and the shared-unit grant applies to eligible mobile units. Buildings, immobile objects, and player spellbooks remain outside the grant.

| Path | Relevant hook addresses | Result |
| --- | --- | --- |
| Selection and synchronized group orders | `0x68B749`, `0x76ED2D` | Recognize the current grant in the local and simulation paths. |
| Unit powers and targeting | `0x77A4A8`, `0x9409B8`, `0x6A0837` | Allow a valid explicit-source power and preserve the targeting cursor and radius preview. |
| Builder sidebar and construction | `0x92F2C8`, `0x77B064` | Show the selected builder's construction panel and authorize placement using the actual owner's limits and resources. |
| Unit upgrades and the Angmar Thrall Master's summon purchase | `0x940DB7`, `0x940DFB`, `0x940E86`, `0x940E45`, `0x94310F`, `0x77A858`, `0x77B1C1` | Apply the grant to the UI and order and charge the actual owner. |
| Unit voices and EVA | `0x8E00BC`, `0x45341B`, `0x8E0055` | Use the authorized local listener for audio visibility while keeping the original unit, position, and cooldown behavior. |
| Left plus right mouse formation gesture | `0x8332C0`, `0x83323E` | Apply the grant to the preview and executed order while retaining formation eligibility checks. |
| Edge scrolling | `0x83AF66`, `0x83B515` | Keep the native mouse-edge checks in foreground windowed and borderless modes. Require the pointer to be inside the client area in a decorated window and clear scroll state when the window loses focus. |

## English localization

The Players headers are APT EditTexts `$ETBlock` and `$ShareArmy`. The Rules UI looks up its own `RULE:` key. Merge these records into the English `lotr.str`.

```text
APT:ETBlock
  "Block"
END

APT:ShareArmy
  "Share Army Control"
END

RULE:ShareArmy
  "Shared Army Control"
END
```

The native game text manager uses its usual fallback and displays a `MISSING:` label if it cannot resolve a key. The patch embeds lookup keys only.

## Verify the behavior

The x86 checks (`src/shared_army/verify.py`) run the actual patched code with stubs for engine services. They cover the original Skirmish checkbox path, on and off behavior, allied grants, sender validation, revocation, AI orders, abilities and upgrades, sound routing, formation filtering, camera edges, and the Random Teams default. The localization check (`src/shared_army/verify_localization.py`) exercises native key lookup and the missing-string path.

For a live Windows check, start a new single-player Skirmish with an allied AI and test the Players table with the rule both on and off. Then test a multiplayer match with two human allies. Issue an order from each side, revoke the grant, and check voices, formation drag, builder placement, targeted powers, and the Thrall Master's summon. Also move the pointer into all four edges in windowed and borderless modes and check that a new room starts with Random Teams off.
