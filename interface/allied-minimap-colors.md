# ROTWK team colors on the minimap

This patch adds **Show allied players in one color** to the **Other** tab in Settings. With the option enabled, your own objects and your allies’ objects appear blue on the minimap. Enemy objects appear red. Neutral map units such as Wargs and Trolls keep their original colors. The option defaults to off and is saved locally in `Options.ini`.

## Minimap color rules

The renderer evaluates each object from the local player’s perspective. It resolves the object’s owner, then queries the engine’s relationship between the local player and the owner's default team. This uses the current in-game relationship even if teams change during the match.

| Object owner or viewing context | Color with the option on |
| --- | --- |
| Local player | Blue `#4C94FF` |
| Ally | Blue `#4C94FF` |
| Enemy | Red `#FF4444` |
| Neutral player, map creeps, civilians, or neutral relationship | Original color |
| Missing local player, neutral local player, or spectator view | Original color |
| Object with no owner, or another owner's team is unavailable | Original color |

Check whether the owner is the local player before looking up its team. This makes the local player blue even when its default team is unavailable. Check the engine’s neutral player and the map-player names `PlyrCreeps`, `PlyrCreep`, and `PlyrCivilian` before looking up diplomacy. The engine can treat those map players as hostile for targeting, so checking diplomacy alone would color neutral creeps red. For red and blue, preserve the original alpha byte and replace only the RGB bytes.

## Engine changes in `game.dat`

The patch applies the same color rules at two draw call sites. Ordinary radar blips pass their color to the engine’s tint routine. Wall markers fetch their color separately from the object. Hook both paths so walls and ordinary markers follow the same rules.

| Purpose | Virtual address | Original target or entry |
| --- | --- | --- |
| Recolor an ordinary blip before applying the original tint | `0x0044FB08` | Tint routine at `0x0044D013` |
| Recolor a wall marker after reading its original color | `0x0044D8F5` | Object color routine at `0x0068B6F5` |
| Register and initialize the native checkbox | `0x00F23007` | `0x00F35070` |
| Save the checkbox into the existing settings map | `0x00F2302E` | `0x00F35189` |
| Load the preference through the normal settings path | `0x00F23048` | `0x00F3511C` |
| Update the checkbox visibility on page changes | `0x00F350C6` | `0x00F350D0` |
| Clear the checkbox reference when resetting the settings session | `0x00F2334F` | `0x00F350ED` |
| Restore the checkbox to its default | `0x00F23203` | Existing reset handler |

At the ordinary blip call, `EDI` holds the object. The hook replaces the first stack argument with the resolved color, restores the registers and calls through to the original tint routine. The wall hook takes the object from `ECX`, calls the original color getter and returns the resolved color in `EAX`. Both hooks go straight to the original routine when the setting is off.

The 32-bit build uses image base `0x00400000`. Its new `.allymap` PE section starts at virtual address `0x00F3D000` and file offset `0x00B22400`. It contains the hooks, preference state and expanded settings command table. The build checks the input SHA-256 and the original bytes at every patched site. The addresses are specific to the input build below.

## Settings tab and preference

1. Extract `Options.apt`, `Options.const`, `Options.dat` and the companion geometry from the existing `apt/options.big`. Convert the APT movie to XML with `sage_apt`.
2. Use the existing Network tab as a template for the navigation and selected state of page `5`. Add an `OtherPage` sprite with the heading and option label. In `ETSelectPage`, show the page and its selected state only when `page == 5`. Send `ETPage5` through `GameCode` so the engine selects the same page as the movie.
3. Clone the `Options::HealthBars` native checkbox under `NativeGadgets` and name the new instance `Options::ETMinimapAllyColor`. The engine registers `AptOptions::ETPage5` as the tenth settings command and shows the checkbox only on page `5`.
4. Load `ETMinimapAllyColor` from `Options.ini`. Enable the color override when the value is `1`. When accepting the settings, write `1` or `0` to the normal preferences map before the game flushes it to disk, and update the runtime flag. **Defaults** clears the checkbox. Canceling discards the pending change.
5. Compile the XML back to APT and repack the archive. In the shipped patch only `Options.apt` and `Options.const` differ inside `apt/options.big`.

## Localization in `lotr.str`

The APT movie uses `$ETOther` for the tab and page title and `$ETMinimapAllyColor` for the checkbox label. The game resolves them as the following entries in the active language pack’s `lotr.str`.

```text
APT:ETOther
"Other"
END
APT:ETMinimapAllyColor
"Show allied players in one color"
END
```

The Russian patch includes the corresponding translations in `localization/lotr-minimap.str`. Merge those entries into the active Russian `lotr.str`. For another language, translate the quoted text with the same keys. When a key is absent from the loaded text table, the engine displays its normal `MISSING: 'APT:…'` marker.

## Build inputs and verification

| File | SHA-256 |
| --- | --- |
| Input `game.dat` from `ROTWK_Command_Points_Fix.zip` | `cdc28b2743fde10914fbd20cc2b846d9190ac81dc60d12181eaa5f9a6e42115c` |
| Input `apt/options.big` from `ROTWK_Graphics_Layout.zip` | `09dd36273328f8fcb0b0dc7f5f290c22a5f5359e12e14985140b5770113daebc` |
| Patched `game.dat` from `ROTWK_Allied_Minimap_Colors.zip` | `85a3543fe20917f82845634f8c3f9f6963c02aa1f224ed075caac16725595535` |
| Patched `apt/options.big` from `ROTWK_Allied_Minimap_Colors.zip` | `198915f365027b841b6c115e98c28cd093f6da48d12e1488be02fc08affc28e3` |

The implementation uses `feature.c` for the settings and color logic, `hooks.s` for the x86 wrappers, and `build.py` for the PE patch and APT repack. The existing x86 emulator tests were rerun on the shipped output. They exercised both draw call sites, changes in diplomacy, observer behavior, persistence through the settings save path, repeated tab switches, and the native translation lookup with and without the two keys. Runtime verification for this write-up used the emulator.

To verify in ROTWK, open **Settings → Other**, enable the option, and accept the changes. Start a skirmish with an ally, an enemy and a neutral lair. Check that both your markers and your ally’s are blue, enemy markers are red, neutral creatures keep their original colors, and walls match their owners. Disable the option and confirm the original minimap colors return. Restart the game and check the checkbox reflects your last saved choice.
