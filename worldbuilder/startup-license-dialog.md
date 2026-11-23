# Hide the WorldBuilder startup license dialog

WorldBuilder already checks for an empty marker file named `worldbuilder_noeula.txt`. After you have accepted the license terms, create the marker in the editor's working directory. If you start the editor from a shortcut, check its **Start in** field.

On Windows, open PowerShell in that directory and run

```powershell
New-Item -ItemType File -Path .\worldbuilder_noeula.txt
```

Start WorldBuilder again. To restore the startup dialog, close WorldBuilder and remove the marker you created.

## Implementation

The original and patched executables have the same check at preferred VA `0x0068FB7D`. The branch at `0x0068FB9C` skips the dialog when the engine finds the marker. The patched release ships the zero-byte marker alongside `worldbuilder.exe`.

[Back to the WorldBuilder index](README.md)
