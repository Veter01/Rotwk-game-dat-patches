# Multiplayer lobby layout and map search

Compared `mpgamesetup.big` from the original and modified inputs. The movie grows from 557 to 560 character slots. The change replaces the APT movie and five mesh entries. The original `MpGameSetup.const`, texture atlas, and `MpGameSetup.dat` are identical in the two supplied archives.

## Map search field

The original `NameTab` at depth 26 is replaced by a transparent placement. Depth 27 adds shape 557 as the search icon. Depth 28 places sprite 559, names it `MapSearch`, and sets up a `TextEntry` control. The initialization action calls `MpGameSetup::InitGadgets` and loads `Apt/TextEntry.wnd`. Sprite 559 places geometry 558 as the input area.

To change the search field's position, edit `tx` and `ty` on its `placeobject` in [MpGameSetup.xml](source/mpgamesetup/MpGameSetup.xml). Keep the `MapSearch` name and initialization properties for the [game.dat map-search handler](../interface/lobby-map-search.md). Adjust the icon at depth 27 independently if needed.

## Player slots

Sprite 285 adds named rows `6` and `7`, moves its bottom placement to depth 100, and stretches its background. Meshes 281, 286, and 296 extend the lower edge of the lobby panel. Sprite 323 also stretches its background. Its frame-zero action now forces the branch that skips hiding `PlayerList.~6` and `PlayerList.~7`. The game and scenario still control which slots may be populated.

## Verify

In a LAN or multiplayer lobby, type and clear a map name in the search box. Select a filtered result and check the launched map. Open an eight-slot lobby and check that the two extra rows, ready indicators, and surrounding panel display correctly. The original archive used for comparison has SHA-256 `a974e18d7f934431bb2f9a640906eef8891159cb87eac04bf054069f3970883e`.

[Back to the APT index](README.md)
