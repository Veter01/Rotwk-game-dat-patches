# Weather effect colors

The executable from Shared Army Control v9 or Options Help v3 supports a per-spell `DarkeningFactor` for Cloud Break rays and precipitation. The Ennorath data patch applies the sample tint `R:30 G:130 B:130` and also colors the separate Avalanche snowflake effect.

## Configure the spellbook

Add the RGB line to the existing weather-setting behavior on the spellbook object. In the Ennorath input used here, Freezing Rain runs through `OCLSpecialPower`. Keep the module type, creation list, and other fields as defined in the mod. The relevant fields in its existing block are shown below.

```ini
Behavior = OCLSpecialPower ModuleTag_FreezingRain
    SpecialPowerTemplate          = SpellBookFreezingRain
    OCL                           = OCL_FreezingRainWeatherChanger
    CreateLocation                = CREATE_AT_LOCATION
    AttributeModifierWeatherBased = Yes
    WeatherDuration              = SPELL_FREEZINGRAIN_DURATION
    ChangeWeather                = RAINY
    DarkeningFactor              = R:30 G:130 B:130
    AvailableAtStart             = No
    RequirementsFilterMPSkirmish  = SPELL_BOOK_REQUIREMENTS_FILTER
    RequirementsFilterStrategic   = SPELL_BOOK_REQUIREMENTS_FILTER_STRATEGIC
End
```

The same field follows `ChangeWeather = SUNNY` in the Cloud Break behaviors and `ChangeWeather = CLOUDYRAINY` in `SpellBookSnowRain`.

| Member inside `____enrth_data.big` | Edited definition |
| --- | --- |
| `data/ini/object/system/system.ini` | `SpellBookFreezingRain` and `SpellBookCloudBreak` |
| `data/ini/object/system/includes/systemgood.inc` | `SpellBookCloudBreakRohan`, `SpellBookCloudBreakLothlorien`, `SpellBookCloudBreakImladris`, and `SpellBookCloudBreakKampagne` |
| `data/ini/object/system/includes/systemevil.inc` | `SpellBookCloudBreakHarad` and `SpellBookSnowRain` |
| `data/ini/includes/fxparticlesystem.inc` | `FXParticleSystem AvalancheSnowFlakesRain` |

Avalanche creates local snowflakes through its FX list. In `FXParticleSystem AvalancheSnowFlakesRain`, replace the three existing color keys and keep the frame numbers.

```ini
Color = DefaultColor
    Color1 = R:30 G:130 B:130 0
    Color2 = R:30 G:130 B:130 50
    Color3 = R:30 G:130 B:130 60
End
```

For map-driven precipitation, the executable also accepts `DarkeningFactor` inside an existing `Weather` block. The native map weather settings supply a fallback tint for precipitation when the relevant spell tint is inactive. The supplied data patch edits the spellbook and Avalanche definitions in the table above.

## Engine implementation

The [executable builder](src/shared_army/build_game.py) installs the weather hooks from the [assembly source](src/shared_army/shared_army.s). The preexisting shared SpecialPower parser stores the three tint bytes next to the weather-based flag and marks the factor as configured. The new code reads that field for the weather types below.

| Hook | Responsibility |
| --- | --- |
| `0x897B45`, `0x71A0CF` | Record the packed color with the active weather ID and clear the effect tint on expiry. Keep the original cloudy lighting path. |
| `0x492F80`, `0x493A3C` | Scale the two native precipitation vertex color paths while preserving alpha. |
| `0x5F448D` | Modulate weather particle colors. For sunny weather this covers `CloudBreakRays*` and `GildorCloudBreakRays*`. For precipitation it covers `SnowFlakesRain*` and `WeatherStormRain*`. |
| `0x600A0E`, `0x6012BE`, `0x6010C1`, `0x600E1B` | Extend the `Weather` parser, initialize the optional tint to white, and keep it when the native map settings are copied. |

Each channel is multiplied by its factor divided by 255. A factor of 255 preserves that channel and 0 removes it. The source particles' colors and intensity affect the result, and opacity is retained.

## Example palette

| Effect | `DarkeningFactor` |
| --- | --- |
| Cold blue rain | `R:145 G:190 B:255` |
| Light icy rain | `R:190 G:225 B:255` |
| Dark storm rain | `R:85 G:115 B:165` |
| Emerald raindrops | `R:55 G:210 B:110` |
| Magical purple rain | `R:175 G:100 B:235` |
| Amber rain | `R:245 G:165 B:70` |

## Build and verify

The [weather data builder](src/weather/build.py) creates `build/weather/____enrth_data_WeatherColors.zip`. It contains a BIG with the four edited entries. Import them into the main data archive using their original paths. The [weather test](src/weather/verify.py) checks registration, RGB parsing from each modified spell behavior, and the active weather state and precipitation color in emulation.

In the game, cast Cloud Break and Freezing Rain and watch the rays and drops as the effect begins and expires. For the active Angmar spellbook, use Avalanche to test the local snowflakes. The base input has the standalone `SpellBookSnowRain` definition, but the normal Angmar command set uses Plague Mist in its place. Live particle appearance remains to be checked on Windows.
