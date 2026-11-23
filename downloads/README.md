# ROTWK downloads

| File | Contents |
|---|---|
| [game.dat](https://raw.githubusercontent.com/Veter01/Rotwk-game-dat-patches/main/downloads/game.dat) | Patched ROTWK engine file for the usual game launcher |
| [lotrbfme2ep1.exe](https://raw.githubusercontent.com/Veter01/Rotwk-game-dat-patches/main/downloads/lotrbfme2ep1.exe) | The same Windows x86 executable with an `.exe` extension |
| [apt.zip](https://raw.githubusercontent.com/Veter01/Rotwk-game-dat-patches/main/downloads/apt.zip) | Compiled `mpgamesetup.big`, `options.big`, and `playertribute.big` |
| [worldbuilder.zip](https://raw.githubusercontent.com/Veter01/Rotwk-game-dat-patches/main/downloads/worldbuilder.zip) | Patched ROTWK WorldBuilder editor (`worldbuilder.exe`) and `worldbuilder_noeula.txt` |

Use these files with a compatible ROTWK installation and mod setup. Back up your existing files first. For the usual game launcher, replace its `game.dat`. The renamed executable requires the game's assets and dependencies. Extract the three `.big` archives to the location where your mod loads these menus. The custom menus require the [language entries below](#menu-language-pack) in your mod's `lotr.str`.

| File | SHA-256 |
|---|---|
| `game.dat` and `lotrbfme2ep1.exe` | `8853bde32ff0be8941b0d53fb6e4845df96df643142451abd3e995c218e0fbee` |
| `apt.zip` | `35c62d309b8778d40637b80599bf84b11c201344b3f3d130d48f6274693f2cf2` |
| `worldbuilder.zip` | `02c4dc8d29986d660b767234cd39ca85ed9ee6b1b21061a1f753cbd4bceb2dab` |

See the [WorldBuilder guide](../worldbuilder/README.md) for details about the editor patches.

## Menu language pack

Add these entries to the `lotr.str` loaded by your mod for the selected language. If a key already exists, update its value in place. Keep the key exactly as shown and translate the text in quotes for each language. A missing entry can appear as a `MISSING` label. For example

```text
APT:ETKeySelectAllHeroes
    "Select All Heroes"
END
```

| Key in `lotr.str` | English menu text |
|---|---|
| `APT:ETModName` | Your Mod Name |
| `APT:ETGraphics` | Graphics |
| `APT:ETScreen` | Screen |
| `APT:ETSound` | Sound |
| `APT:ETHotkeys` | Hotkeys |
| `APT:ETNetwork` | Multiplayer |
| `APT:ETDetail` | Graphics Quality |
| `APT:ETBrightness` | Brightness |
| `APT:ETHealth` | Health Bars |
| `APT:ETResolution` | Screen Resolution |
| `APT:ETFPS` | Frame Rate (FPS) |
| `APT:ETFPS30` | 30 FPS |
| `APT:ETFPS60` | 60 FPS |
| `APT:ETFPSNote` | Frame rate can be changed in the main menu. |
| `APT:ETSensitivity` | Mouse Sensitivity |
| `APT:ETScroll` | Map Scroll Speed |
| `APT:ETKeysNote` | `""` |
| `APT:ETKeyCamLeft` | Rotate Camera Left |
| `APT:ETKeyCamRight` | Rotate Camera Right |
| `APT:ETKeyZoomIn` | Zoom In |
| `APT:ETKeyZoomOut` | Zoom Out |
| `APT:ETKeyCameraReset` | Reset Camera |
| `APT:ETKeyBuilder` | Select Next Builder |
| `APT:ETKeyStop` | Stop Selected Units |
| `APT:ETKeyAttackMove` | Attack Move |
| `APT:ETKeyMatchType` | Select Same Type |
| `APT:ETKeyBuildPath` | Select Same Type |
| `APT:ETKeySpellbook` | Open Spellbook |
| `APT:ETKeySell` | Sell Selected Building |
| `APT:ETKeySelectAll` | Select All Units on the Map |
| `APT:ETKeySelectAllHeroes` | Select All Heroes |
| `APT:ETKeyTacticalMenu` | Open Planning Mode |
| `APT:ETKeyDefault` | Default |
| `APT:ETKeyDefaultSuffix` | default |
| `APT:ETKeyMiddleButton` | Middle Mouse Button |
| `APT:ETMusic` | Music |
| `APT:ETEffects` | Sound Effects |
| `APT:ETVoice` | Voice |
| `APT:ETAmbient` | Ambient Sound |
| `APT:ETMovies` | Movies |
| `APT:ETEAX` | EAX3 |
| `APT:ETHighAudio` | High-Quality Audio |
| `APT:ETIP` | IP Address |
| `APT:ETDelay` | Send Delay |
| `APT:ETDelayFix` | Network Delay Fix |
| `APT:ETPort` | Port Number |
| `APT:ETPortHelp` | 8008 to 65535 |
| `APT:MapSearch` | Search Maps |

`APT:ETKeysNote` is the optional note under the hotkey controls. Use an empty quoted value to leave it blank. Keep both `APT:ETKeyMatchType` and `APT:ETKeyBuildPath` because the patched engine and APT movie reference different names for that label. Replace `Your Mod Name` with the name of your mod.

For the editable interface sources and build instructions, see the [APT guide](../apt/README.md).
