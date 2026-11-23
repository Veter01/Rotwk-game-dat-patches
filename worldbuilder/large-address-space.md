# Enable a larger address space for WorldBuilder

Set the PE flag `IMAGE_FILE_LARGE_ADDRESS_AWARE` so 32-bit WorldBuilder can use up to 4 GiB of user-mode virtual address space on 64-bit Windows. Actual allocations depend on the system and workload. The editor remains a PE32 x86 executable. [Microsoft's Windows memory limits](https://learn.microsoft.com/en-us/windows/win32/memory/memory-limits-for-windows-releases)

## Apply

From the directory that contains the [patcher](patch_worldbuilder.py) and its [data file](patch-data.json), run

```powershell
py -3 .\patch_worldbuilder.py .\worldbuilder.exe .\worldbuilder-memory.exe --patch memory
```

All three patch modes apply this flag. Install the output as described in [the WorldBuilder index](README.md#build-the-patched-editor).

## Implementation

For the supported executable, the PE header starts at raw offset `0x128`. The COFF `Characteristics` word is at `0x13E` and changes from `0x010E` to `0x012E` by setting bit `0x0020`. For another build, locate the PE header through the DOS `e_lfanew` field and inspect the COFF flag before applying an equivalent change.

## Verify

Run `dumpbin /headers worldbuilder-memory.exe` and check that the file can handle large addresses. Launch the editor on 64-bit Windows and load a large map to check editor behavior with your assets.

[Back to the WorldBuilder index](README.md)
