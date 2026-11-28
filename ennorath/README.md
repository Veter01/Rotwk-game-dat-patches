# ROTWK and Ennorath patch guides

These guides document changes built for a specific Ennorath edition of *The Lord of the Rings: The Battle for Middle-earth II — The Rise of the Witch-king*. They cover the latest tested build for each feature and explain the important revisions along the way.

| Guide | Changes |
| --- | --- |
| [Arnor stone auto-harvest](docs/arnor-stone-autoharvest.md) | Add a one-click stone gathering order for Arnor while retaining Mordor's wood gathering. |
| [Shared Army Control](docs/shared-army-control.md) | Add a match rule and player controls for sharing an army, restore allied orders and feedback, fix edge scrolling, and default Random Teams to off. |
| [Weather effect colors](docs/weather-effect-colors.md) | Tint Cloud Break rays, freezing rain, and snow. Includes an RGB palette and the four edited INI files' locations. |
| [Help in Options](docs/options-help.md) | Add a localized Help page and Discord link, then place Other above Help. |
| [Display and command bar](docs/display-and-command-bar/README.md) | Fix windowed scrolling, fullscreen, autocast, upgrade prices, and player-list labels. Build and package the final cumulative engine. |

## Source files

This directory includes the main build script, the [weather build and verification scripts](src/weather), and the [APT archive helper](src/apt_big.py). The complete build also requires the source files under `src/harvest/`, `src/shared_army/`, `src/help/`, and `src/display_and_commands/` from the Ennorath source archive.

## Rebuild the patches

Use Python 3.12, GNU binutils with i386 support, and the Inkscape CLI on Linux or WSL. The reference build used binutils 2.44 and Inkscape 1.4. Pillow processes the options textures. Unicorn runs the optional x86 tests. The APT and PE tools come from a pinned [pySAGE revision](https://github.com/ClementJ18/pySAGE/tree/0a1f1b5d71b1b080008a7e9fff6f997601ec5a7f).

```sh
git clone https://github.com/ClementJ18/pySAGE.git ../pySAGE
git -C ../pySAGE checkout 0a1f1b5d71b1b080008a7e9fff6f997601ec5a7f
python3 -m venv .venv
. .venv/bin/activate
python -m pip install Pillow==13.0.0 unicorn==2.1.4
mkdir -p inputs
```

Supply the following files from your matching Ennorath inputs. The directory and file names in the left column are the paths the builder reads. The executable offsets and APT character IDs are specific to these inputs.

| Input | Required version | SHA-256 |
| --- | --- | --- |
| `inputs/game.dat` | Base Ennorath PE32 from the Arnor test input, with the existing `.harvest` section | `bad61adac79fa2e1919d65387196913610685b5c0b05b6219e4872e6dd49f3f5` |
| `inputs/____enrth_data.big` | Unmodified Ennorath data used for the Arnor and weather edits | `e9402f6398813313bf94653033fd681514e35bae4f3004c9fc85737c5b950e3a` |
| `inputs/playertribute.big` | Ennorath Players dialog with the existing chat-block control | `6ba45687b855765ca1fb8da17db0da417dccdd00b747ffb284545c7e2db59906` |
| `inputs/mpgamesetup.big` | Ennorath match setup with the search placeholder and the Random Teams rule | `fa0d60542bcd7d83f9ba24230cfeec2dd2d087b35fec8ce568467231164490db` |
| `inputs/options.big` | Ennorath Options before the Help page was added | `a099295aef0ae307b29f4356900456535a3d44c63dbd5c716ac531e9e58f8acc` |

```sh
export PYTHONPATH="$(cd ../pySAGE && pwd)${PYTHONPATH:+:$PYTHONPATH}"
python build.py --verify
```

The builder validates the input hashes before patching. Use `python build.py` to produce the same outputs without the emulation tests.

| Output | Use |
| --- | --- |
| `build/harvest/game.dat` and `build/harvest/____enrth_data_ArnorAutoHarvest.big` | Reproduce the Arnor v2 test build or use the executable as the input to Shared Army Control. |
| `build/shared-army/game.dat`, its `.exe` copy, `playertribute.big`, and `apt/mpgamesetup.big` | Install Shared Army Control v9 with its match and Players UI. This executable includes the weather rendering patch. |
| `build/weather/____enrth_data_WeatherColors.zip` | Import the four edited data members from the BIG in the ZIP into the main Ennorath data archive. |
| `build/help/game.dat`, its `.exe` copy, and `options.big` | Install Options Help v3 or use this executable and interface as inputs for the display and command bar update. |

## Install the combined changes

For the final tab order and display and command bar fixes, run the [follow-up build](docs/display-and-command-bar/README.md#build-from-the-repository-outputs). Use its engine and three APT archives together. Use the steps below for the original cumulative Help v3 build and its separate data changes.

1. Install the Arnor data changes. Import the four weather entries afterward if you also want the sample colors. Use their existing internal paths when merging them into the main data archive.
2. Use the executable from `build/help/` when installing all features together. Match the filename your launcher uses. If an install uses both `game.dat` and `game.exe`, update both from the same output directory.
3. Replace `playertribute.big`, `apt/mpgamesetup.big`, and `options.big` at the paths your build loads. In a parent APT archive, replace the nested member at its original path, typically `apt/options.big` for Options.
4. Add the English localization entries from the shared-army and Options guides to the appropriate `lotr.str`. Preserve the language file's encoding and replace the sample Discord URL with your own.
5. Use the same executable and data files on all peers when testing network matches.

### Why `game.dat` and `game.exe` have the same checksum

This build's `game.dat` already contains a Windows PE32 executable. The builder copies the bytes to `game.exe` so the filename matches launchers that use the `.exe` extension.

```sh
cp build/help/game.dat build/help/game.exe
cmp build/help/game.dat build/help/game.exe
```

### Reference output checksums

| Relative to `build/` | SHA-256 |
| --- | --- |
| `harvest/game.dat` | `46abb4a13baefa097a00f18c27d230e827a256712904b8b42ae5d92070c9a7b2` |
| `harvest/____enrth_data_ArnorAutoHarvest.big` | `fd79742a7e2ebf2be88db9e433b8a827bdf01d5aea260e169de246b3611de669` |
| `shared-army/game.dat` and `shared-army/game.exe` | `600afcae2ff784d09d758e05f5db65d89620b1bf05b8d9d1d5535b919ec7e19f` |
| `shared-army/playertribute.big` | `368be51a05a7781320b313bbd1e3188fd1f3f1158697e94153577fdb11cfd66a` |
| `shared-army/apt/mpgamesetup.big` | `21f815302c94ae064c8f2106f33c44e31f6fada6d05b66f82bbc55c946d3ffdd` |
| `weather/____enrth_data_WeatherColors.big` inside its ZIP | `6d311e87754b0c94497bf56317376d9a05551fa37eb2c3dba125316701e62346` |
| `help/game.dat` and `help/game.exe` | `947a02859ea7791fcc6f12bdf1da71a09a165c840275ea54e8e4ed66ddb91240` |
| `help/options.big` | `7593627ba7b7a9f2df03e6337f0a6537d0ea0e19825a409a41c04a214e797b4e` |

The reference outputs match the previously packaged builds byte for byte. The guides list the remaining live Windows checks for each feature.
