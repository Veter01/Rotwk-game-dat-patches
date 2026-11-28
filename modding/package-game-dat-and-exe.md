# Package game.dat and game.exe

The patched `game.dat` is a 32-bit Windows Portable Executable. Its executable entry point, imports, and code are already present. To make the `game.exe` copy, keep the file bytes and change the filename.

1. Build the engine and APT update using the [README](../interface/display-and-command-bar.md).
2. From `modding/`, run the packaging script on the resulting update archive.

```sh
python src/display_and_commands/package_executables.py build/rotwk-fixed-window.zip build/rotwk-executables.zip
unzip -t build/rotwk-executables.zip
unzip -p build/rotwk-executables.zip game.dat | sha256sum
unzip -p build/rotwk-executables.zip game.exe | sha256sum
```

3. Check that the output contains both files at the root of the ZIP and that both hashes match. The [packaging script](src/display_and_commands/package_executables.py) checks the PE machine type, GUI subsystem, executable flag, and entry-point section, then reopens the ZIP to verify its contents.

On Windows you can create the same copy inside the game directory with PowerShell.

```powershell
Copy-Item -LiteralPath .\game.dat -Destination .\game.exe
Get-FileHash -Algorithm SHA256 -LiteralPath .\game.dat, .\game.exe
```

The regular game launcher can continue to use `game.dat`. The `game.exe` copy uses the same game files and dependencies. If you want to launch it directly, test it from the original game directory with your installed assets and required launch arguments. The package verification covers the file bytes and archive. Direct Windows launch of the renamed executable was outside that verification.
