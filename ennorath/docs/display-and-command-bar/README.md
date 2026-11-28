# Display and command bar updates

These patches build on the repository's cumulative Options Help v3 executable and Shared Army Control interface. The final update puts Other above Help and keeps a fixed-size window in windowed mode.

| Guide | Change |
| --- | --- |
| [Help and Other in Options](../options-help.md#put-other-above-help) | Move the two tabs, their captions, and their selected highlights. |
| [Windowed camera](windowed-camera-and-cursor-clipping.md) | Scroll at all four client edges and align cursor clipping with the viewport. |
| [Group autocast](group-autocast.md) | Toggle matching abilities for selected units with one right-click. |
| [CommandButton discounts and prices](commandbutton-discounts-and-upgrade-prices.md) | Resolve each unit's upgrade and show its effective price. |
| [Training crash](training-crash-tooltip-pointer.md) | Keep the original command button available on the missing-requirements tooltip path. |
| [Window fit and display crash](window-fit-and-display-crash.md) | Fit the window on screen, invalidate stale controls, and restore the fixed frame. |
| [Player list and rule labels](player-list-and-rule-labels.md) | Match header sizes and extend the backing gradient through the last column. |
| [Fullscreen and match lock](fullscreen-and-match-lock.md) | Select a supported exclusive resolution and lock the mode selector in matches. |
| [Package the engine](package-game-dat-and-exe.md) | Package the verified x86 executable under both filenames. |

## Build from the repository outputs

These steps require the files under `src/display_and_commands/` from the Ennorath source archive. Run the commands from the `ennorath` directory.

Run the [repository builder](../../README.md#rebuild-the-patches) first. Then work from the repository root. Use Python 3.12 and a Linux or WSL toolchain with GCC that supports 32-bit compilation and GNU binutils. The follow-up reference build used Python 3.12.14, GCC 14.2.0, and GNU binutils 2.44. Because the stages verify executable bytes, another compiler version may trigger an intermediate fingerprint check.

Prepare the four matching input files using the paths below. You can also supply an existing ZIP with the same member names and fingerprints.

| Repository output | Input ZIP path | SHA-256 |
| --- | --- | --- |
| `build/help/game.dat` | `game.dat` | `947a02859ea7791fcc6f12bdf1da71a09a165c840275ea54e8e4ed66ddb91240` |
| `build/help/options.big` | `apt/options.big` | `7593627ba7b7a9f2df03e6337f0a6537d0ea0e19825a409a41c04a214e797b4e` |
| `build/shared-army/playertribute.big` | `apt/playertribute.big` | `368be51a05a7781320b313bbd1e3188fd1f3f1158697e94153577fdb11cfd66a` |
| `build/shared-army/apt/mpgamesetup.big` | `apt/mpgamesetup.big` | `21f815302c94ae064c8f2106f33c44e31f6fada6d05b66f82bbc55c946d3ffdd` |

```sh
stage=build/display-baseline
mkdir -p "$stage/apt"
cp build/help/game.dat "$stage/"
cp build/help/options.big "$stage/apt/"
cp build/shared-army/playertribute.big "$stage/apt/"
cp build/shared-army/apt/mpgamesetup.big "$stage/apt/"
(cd "$stage" && python -m zipfile -c ../display-baseline.zip game.dat apt)
```

The follow-up uses its own pySAGE checkout. The bundled compatibility patch (`src/display_and_commands/patches/commands/pysage-multiselect.patch`) updates the shared command-slot matcher. Keep the original repository builder's checkout at the revision in the root README.

```sh
git clone https://github.com/ClementJ18/pySAGE.git ../pySAGE-display
git -C ../pySAGE-display checkout --detach 10e069500929452ad96c3896bc04eb71e025dfb8
git -C ../pySAGE-display apply "$PWD/src/display_and_commands/patches/commands/pysage-multiselect.patch"
display_pysage="$(cd ../pySAGE-display && pwd)"
python -m pip install pefile

PYTHONPATH="$display_pysage" python src/display_and_commands/build.py \
    build/display-baseline.zip build/rotwk-fixed-window.zip
python src/display_and_commands/package_executables.py \
    build/rotwk-fixed-window.zip build/rotwk-executables.zip
```

The follow-up builder (`src/display_and_commands/build.py`) verifies the input and output checksums and the ZIP CRCs. The final `game.dat` SHA-256 is `9562f81e6e71de72cb78e01501aba1dcf4d58db9bf2e33091e320dae624433e9`. Install that engine and the three APT files from `build/rotwk-fixed-window.zip` at the paths your mod loads. If your launcher uses `game.exe`, take it from `build/rotwk-executables.zip`. Use the same localization and Ennorath data files described in the root README.

## Verification and porting

The update was rebuilt from the matching cumulative input files and checked against the reference build member by member. The original development checks exercised the command hooks, camera input, and display mode paths in x86 emulation. The individual guides include live Windows checks.

The engine addresses are virtual addresses for the documented PE image with base `0x400000`. For a different build, locate the equivalent code and APT entries, confirm the calling conventions, and verify the original bytes before porting the patches. [pySAGE](https://github.com/ClementJ18/pySAGE/tree/10e069500929452ad96c3896bc04eb71e025dfb8) · [Open-BFME-2](https://github.com/Open-BFME/Open-BFME-2)
