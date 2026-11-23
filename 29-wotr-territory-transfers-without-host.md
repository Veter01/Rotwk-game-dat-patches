# Allow War of the Ring territory transfers from a non-host player

The supplied War of the Ring bundle changes ownership and permission handling used for non-host territory actions.

## Reproduce the patch

Run the [patch builder](README.md#build-a-patched-game-file) with `wotr`.

## Implementation

The candidate permission sites are the flag test and override near `0x006BEBE5`, the action flags at `0x007F67E0`, and the participant lookup in `.wtrdisp+0x78`. The first edit bypasses rewriting permission bits. The second adds bit `0x08` alongside `0x02`. The lookup scans player records and returns the corresponding participant ID. The supplied build includes all three changes. Their individual roles in territory transfers are inferred from the disassembly.

The table identifies the corresponding changed byte ranges. The builder supplies any shared code and data sections.

| File offset | Preferred VA | Original bytes | Replacement bytes |
|---|---|---|---|
| `0x002BEBE5` | `0x006BEBE5` | `7d` | `eb` |
| `0x003F67E0` | `0x007F67E0` | `02` | `0a` |
| `0x00500EBA` | `0x00900EBA` | `83 c8 ff eb 4c` | `e9 b9 e1 62 00` |

## Verify in ROTWK

Host a War of the Ring session with a second human client. Let the non-host select a territory it owns and transfer it to an eligible ally. Confirm that both clients show the same territory owner after ending the turn and after loading a save. Repeat for an ineligible transfer and a host-initiated transfer.

[Back to the patch index](README.md#feature-index)
