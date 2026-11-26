# Menu language pack

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
| `APT:ETDisplayMode` | Display Mode |
| `APT:DisplayModeFullscreen` | Fullscreen |
| `APT:DisplayModeBorderless` | Borderless Fullscreen |
| `APT:DisplayModeWindowed` | Windowed |
| `APT:ETCursorClipping` | Cursor Clipping |
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
| `RULE:RandomTeams` | Random Teams |

`APT:ETKeysNote` is the optional note under the hotkey controls. Use an empty quoted value to leave it blank. Keep both `APT:ETKeyMatchType` and `APT:ETKeyBuildPath` because the patched engine and APT movie reference different names for that label. Replace `Your Mod Name` with the name of your mod.

Use the new display and lobby entries with the [Display Mode and Cursor Clipping](../interface/display-mode-and-cursor-clipping.md#language-packs) and [Random Teams](../multiplayer/random-teams.md#menu-assets-and-localization) patches.

For the editable interface sources and build instructions, see the [APT guide](../apt/README.md).
