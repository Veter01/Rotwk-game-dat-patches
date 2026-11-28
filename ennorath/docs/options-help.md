# Help in Options

Options Help v3 adds a **Help** page with localized, wrapped text and a Discord button. The button passes the URL from the active language pack to Windows. The initial build placed Help above Other. The later [display and command bar update](display-and-command-bar/README.md) puts **Other** above **Help**.

## Build and install

Run the [repository builder](../README.md#rebuild-the-patches) and take `options.big`, `game.dat`, and `game.exe` from `build/help/`. If your mod ships a parent archive with nested APT files, replace `apt/options.big` inside it. The updated executable includes the earlier Arnor, shared control, and weather changes. To install the final tab order, use the files from the [display and command bar build](display-and-command-bar/README.md#build-from-the-repository-outputs).

## Edit the text and the link

Merge these four records into the appropriate `lotr.str`, preserving its existing encoding. Replace the example URL with your server invite or another URL.

```text
APT:ETHelp
  "Help"
END

APT:ETHelpText
  "Find the mod's documentation and community below."
END

APT:ETHelpLink
  "Discord"
END

APT:ETHelpURL
  "https://discord.com/"
END
```

| Key | Role |
| --- | --- |
| `APT:ETHelp` | Tab name and page heading |
| `APT:ETHelpText` | Wrapped page text |
| `APT:ETHelpLink` | Button caption |
| `APT:ETHelpURL` | URL read when the player clicks the button |

Web URLs use the default browser. Application URLs, such as a supported `discord://` link, use the protocol handler registered in Windows. A missing or invalid URL produces no launch. Missing visible labels use the game's normal `MISSING:` display.

## APT and executable wiring

The page builder (`src/help/build_page.py`) edits `Options.apt` and its constant pool. It gives Help page ID `6`, moves the existing Other tab down, and preserves the other page IDs. `ETSelectPage` switches the Help panel and selected-tab marker. The new panel hides when initialized and is removed along with the other basic pages when the Advanced Graphics view opens.

The link button calls `GameCode("ETOpenHelp", "1")`. The fixed token belongs to the UI command. Inside `game.dat`, the extended Options command table registers `AptOptions::ETPage6` and `AptOptions::ETOpenHelp`. The first uses the normal page switch to hide native controls from other pages. The second verifies that this Options screen and Help page are active, retrieves `APT:ETHelpURL` from GameText, and passes the validated UTF-16 URL to `ShellExecuteW` with the `open` verb. Executable builder (`src/help/build_game.py`) · x86 implementation (`src/help/help.s`)

## Put Other above Help

The follow-up moves each tab's hit area, selected background, and caption together. Open `Options.apt` with its `Options.const` pool, find the `Navigation` placement, and follow its character to sprite `347`, frame `0`. Apply these vertical translations in APT units.

| Depth | Character | Placement | Help v3 Y | Final Y |
| --- | --- | --- | ---: | ---: |
| 17 | 363 | Other button (`Tab5`) | 392 | 332 |
| 18 | 335 | Other selection highlight (`Selected5`) | 392 | 332 |
| 19 | 364 | Other caption (`$ETOther`) | 404 | 344 |
| 20 | 370 | Help button (`Tab6`) | 332 | 392 |
| 21 | 335 | Help selection highlight (`Selected6`) | 332 | 392 |
| 22 | 371 | Help caption (`$ETHelp`) | 344 | 404 |

The layout patch (`src/display_and_commands/patches/navigation_camera/build.py`) verifies the six input placements and writes only their little-endian Float32 Y translations at `PlaceObject + 36`. It decodes the patched movie to check the result before replacing the same-length APT member. This retains page IDs `5` and `6`, clip names, translation keys, and actions. The Help link still invokes the original localized URL callback.

In the final build, click both tabs and check that the upper row opens Other and the lower row opens Help. Compare the selected highlight and the caption with the clickable area. Repeat in each installed language.

## Discord texture in the shared atlas

The atlas builder (`src/help/build_atlas.py`) takes the Discord icon from the included vector source (`src/help/discord.svg`), renders it at high resolution, resamples it to 64 × 64, and writes it into the existing 32-bit TGA. The symbol outline comes from [Simple Icons](https://simpleicons.org/).

| Item | Value |
| --- | --- |
| Texture member | `art/Textures/apt_Options_1.tga` |
| Icon rectangle | `X=952, Y=64` from the top-left corner, 64 × 64 pixels |
| Image map entry in `Options.dat` | `377->1` |
| Shape geometry member | `Options_geometry/378.ru` |
| Shape size in the movie | 26 × 32 menu units |

The geometry samples image character 377 from atlas 1 using the matrix below. The translation selects the icon's rectangle in the atlas.

```text
c
s tc:255:255:255:255:377:2.46153846:0:0:2:952:64
t 0:32:0:0:26:0
t 26:0:26:32:0:32
```

Before writing, the builder checks the source atlas for transparency and verifies that the sampled areas of the existing geometries leave the icon rectangle and its padding unused. It then verifies that pixels outside the rectangle match the input.

## Earlier test version

Help v1 introduced the localized tab and a single generic link. Help v2 used two separate button commands and TGA textures for Discord and YouTube. The second action used `ETOpenHelp2` and the keys `APT:ETHelpLink2` and `APT:ETHelpURL2`. In v3, one Discord button uses the original keys and the shared texture. You can remove the second pair of keys from a language pack carried over from v2.

## Verify the behavior

The verification script (`src/help/verify.py`) exercises the APT navigation states, callback registration, native localization lookup, and the Windows API arguments with a stubbed call. The atlas builder verifies the packaged image region and preserves the original pixels outside it. In a live Windows test, open Help and check the icon, then try a web URL and, if registered, an application link.
