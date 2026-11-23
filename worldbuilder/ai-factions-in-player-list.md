# Expand Player List for AI factions

WorldBuilder's internal Player List capacity increases from 20 to 112 total records. The intended use is to make room for up to 100 AI faction entries alongside the normal players and service records. The available number of AI entries depends on the other records in the map.

## Apply

From the directory that contains the [patcher](patch_worldbuilder.py) and its [data file](patch-data.json), run the full patch

```powershell
py -3 .\patch_worldbuilder.py .\worldbuilder.exe .\worldbuilder-patched.exe
```

Open **Player List** and choose **New Player**. Select a faction defined by your mod, enable **Is Computer-controlled?**, and give the entry a unique name. Repeat for additional AI factions.

## Implementation

The new capacity is `0x70` records. The `.wbplay` section moves three arrays out of the inline `SidesList` structure while preserving its compiled object size.

| Offset in `SidesList` | Extended storage |
|---|---|
| `0x40` | Main sides, 112 records of `0x60` bytes |
| `0x7C4` | Skirmish sides, 112 records of `0x60` bytes |
| `0xF80` | Faction build data, 112 records of `0x1C` bytes |

The patch updates initialization, copying, cleanup, indexed access, the **New Player** and **Add Skirmish Players** limits, and the readers and writer for side and script data. The **New Player** path allows manual insertion while the current count is below 111. The storage and serialization changes are needed together when porting to another editor build.

## Verify

In a test map, add AI sides past the old 20-record threshold. Edit a late entry's faction and script assignments, save, and reopen the map. Confirm that the names, faction choices, AI state, and script associations survive the round trip. Check the resulting map in the target `game.dat` separately. That executable applies its own map and player constraints.

[Back to the WorldBuilder index](README.md)
