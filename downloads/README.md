# ROTWK downloads

| File | Contents |
|---|---|
| [game.dat](https://raw.githubusercontent.com/Veter01/Rotwk-game-dat-patches/main/downloads/game.dat) | Patched ROTWK engine file for the usual game launcher |
| [lotrbfme2ep1.exe](https://raw.githubusercontent.com/Veter01/Rotwk-game-dat-patches/main/downloads/lotrbfme2ep1.exe) | The same Windows x86 executable with an `.exe` extension |
| [apt.zip](https://raw.githubusercontent.com/Veter01/Rotwk-game-dat-patches/main/downloads/apt.zip) | Compiled `mpgamesetup.big`, `options.big`, and `playertribute.big` |

Use these files with a compatible ROTWK installation and mod setup. Back up your existing files first. For the usual game launcher, replace its `game.dat`. The renamed executable requires the game's assets and dependencies. Extract the three `.big` archives to the location where your mod loads these menus. The custom menus require the [language entries below](#menu-language-pack) in your mod's `lotr.str`.

| File | SHA-256 |
|---|---|
| `game.dat` and `lotrbfme2ep1.exe` | `8853bde32ff0be8941b0d53fb6e4845df96df643142451abd3e995c218e0fbee` |
| `apt.zip` | `35c62d309b8778d40637b80599bf84b11c201344b3f3d130d48f6274693f2cf2` |

## Menu language pack

Add these entries to the `lotr.str` loaded by your mod for the selected language. If a key already exists, update its value in place. Keep the key exactly as shown and translate the text in quotes for each language. A missing entry can appear as a `MISSING` label. For example

```text
APT:ETKeySelectAllHeroes
    "Выбрать всех героев"
END
```

| Key in `lotr.str` | Russian menu text |
|---|---|
| `APT:ETModName` | Ennorath |
| `APT:ETGraphics` | Графика |
| `APT:ETScreen` | Экран |
| `APT:ETSound` | Звук |
| `APT:ETHotkeys` | Горячие клавиши |
| `APT:ETNetwork` | Сетевая игра |
| `APT:ETDetail` | Качество изображения |
| `APT:ETBrightness` | Яркость |
| `APT:ETHealth` | Индикаторы здоровья |
| `APT:ETResolution` | Разрешение экрана |
| `APT:ETFPS` | Частота кадров (FPS) |
| `APT:ETFPS30` | 30 FPS |
| `APT:ETFPS60` | 60 FPS |
| `APT:ETFPSNote` | Частота кадров изменяется в главном меню. |
| `APT:ETSensitivity` | Чувствительность мыши |
| `APT:ETScroll` | Скорость прокрутки карты |
| `APT:ETKeysNote` | `""` |
| `APT:ETKeyCamLeft` | Повернуть камеру влево |
| `APT:ETKeyCamRight` | Повернуть камеру вправо |
| `APT:ETKeyZoomIn` | Приблизить камеру |
| `APT:ETKeyZoomOut` | Отдалить камеру |
| `APT:ETKeyCameraReset` | Вернуть камеру |
| `APT:ETKeyBuilder` | Выбрать следующего строителя |
| `APT:ETKeyStop` | Остановить выбранных |
| `APT:ETKeyAttackMove` | Атака с перемещением |
| `APT:ETKeyMatchType` | Выбрать тот же тип |
| `APT:ETKeyBuildPath` | Выбрать тот же тип |
| `APT:ETKeySpellbook` | Открыть книгу заклинаний |
| `APT:ETKeySell` | Продать выбранное здание |
| `APT:ETKeySelectAll` | Выбор всех юнитов на карте |
| `APT:ETKeySelectAllHeroes` | Выбрать всех героев |
| `APT:ETKeyTacticalMenu` | Открыть режим планирования |
| `APT:ETKeyDefault` | По умолчанию |
| `APT:ETKeyDefaultSuffix` | по умолчанию |
| `APT:ETKeyMiddleButton` | СКМ |
| `APT:ETMusic` | Музыка |
| `APT:ETEffects` | Эффекты |
| `APT:ETVoice` | Речь |
| `APT:ETAmbient` | Фоновые звуки |
| `APT:ETMovies` | Ролики |
| `APT:ETEAX` | EAX3 |
| `APT:ETHighAudio` | Высокое качество звука |
| `APT:ETIP` | IP-адрес |
| `APT:ETDelay` | Задержка отправки |
| `APT:ETDelayFix` | Исправление сетевой задержки |
| `APT:ETPort` | Номер порта |
| `APT:ETPortHelp` | От 8008 до 65535 |
| `APT:MapSearch` | Поиск карты |

`APT:ETKeysNote` is the optional note under the hotkey controls. Use an empty quoted value to leave it blank. Keep both `APT:ETKeyMatchType` and `APT:ETKeyBuildPath` because the patched engine and APT movie reference different names for that label. You can set `APT:ETModName` to your mod's name.

For the editable interface sources and build instructions, see the [APT guide](../apt/README.md).
