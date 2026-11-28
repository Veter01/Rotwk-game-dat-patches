# Editable ROTWK APT menus

The three modified menus are available as editable XML. Each source folder also contains the text `.ru` geometry files that were added or changed. The builder reuses the texture atlases, image maps, and other geometry from your copy of the original archives.

| Archive | Editable movie | What changed |
|---|---|---|
| `mpgamesetup.big` | [MpGameSetup.xml](source/mpgamesetup/MpGameSetup.xml) | [Map search and lobby slots](multiplayer-setup.md) |
| `options.big` | [Options.xml](source/options/Options.xml) | [Settings pages and hotkeys](options-menu.md) |
| `playertribute.big` | [PlayerTribute.xml](source/playertribute/PlayerTribute.xml) | [Per-player chat mute](player-tribute.md) |

The engine packages include compiled `options.big` and `playertribute.big`. [Releases](https://github.com/Veter01/Rotwk-game-dat-patches/releases/tag/engine-2026-11-26)

## Edit and rebuild

1. Clone this repository. Extract `mpgamesetup.big`, `options.big`, and `playertribute.big` from your original archive into a local directory such as `Orig`.
2. Install Python 3.12 or newer. Install the revision of pySAGE used to convert and test these movies. Run the following from the repository root.

   ```powershell
   py -3.12 -m pip install "pysage-tools @ git+https://github.com/ClementJ18/pySAGE.git@0a1f1b5d71b1b080008a7e9fff6f997601ec5a7f"
   ```

3. Open the movie's XML in a text editor. Search for `poname` entries to find named controls, then edit the enclosing `placeobject` to change its position or scale. For example, change `tx` or `ty` on the object named `MapSearch`. Change `ettext` for labels and add localization entries in the appropriate game language files. To use the local visual editor for placement changes, run

   ```powershell
   py -3.12 -m sage_apt edit apt/source/options/Options.xml --label _basic
   ```

   The supplied `.ru` files are also text. Put any additional meshes in the corresponding `*_geometry` directory. Keep the mesh filename and the `geometry` ID in the XML in sync. Controls can appear as placeholders in the visual editor when it has no access to the game textures.

4. Compile the XML and build all three archives into a new directory.

   ```powershell
   py -3.12 apt/build_apt.py Orig rebuilt-apt
   ```

5. Back up the current archives in your mod. Replace them with the ones in `rebuilt-apt`. Launch with a `game.dat` that implements the corresponding [lobby search](../interface/lobby-map-search.md), [settings and hotkey callbacks](../interface/configurable-base-hotkeys.md), and [chat mute callbacks](../multiplayer/mute-player-messages.md).

On Linux or macOS, use `python3.12` in place of `py -3.12`. The three XML files were checked by compiling them to APT and decompiling the result to the same XML. Compiling can change the binary layout of the movie and its constant pool. For the original archive identification and in-game smoke tests, see the individual guides.

Format references [pySAGE APT tools](https://github.com/ClementJ18/pySAGE/tree/0a1f1b5d71b1b080008a7e9fff6f997601ec5a7f/sage_apt) and [OpenSAGE APT documentation](https://opensage.readthedocs.io/file-formats/apt/).

[Back to the patch index](../README.md#feature-index)
