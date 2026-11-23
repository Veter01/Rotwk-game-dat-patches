# ROTWK game.dat patch guides

These guides document the differences between two Windows x86 builds of *The Rise of the Witch-king*. Each feature has its own guide with engine addresses, installation steps and a test to run in the game.

| Input | Embedded engine build | SHA-256 |
|---|---|---|
| `Original.zip` → `game.dat` | `2.1.2614.37001` | `b70c58fd522efc81c3e25fed406f8b6d1c7a4158688e6fa501115b4236d81ed0` |
| `GameDataNew.rar` → `game.dat` | `2.1.2614.37001` | `8853bde32ff0be8941b0d53fb6e4845df96df643142451abd3e995c218e0fbee` |

Both inputs are compiled PE32 executables. The version string is shared across the two files and the reference baseline already contains mod patches. The SHA-256 identifies the required baseline for the copy-and-apply commands. File offsets are zero-based. Preferred virtual addresses (VAs) use the PE image base `0x00400000`. Some table rows show only changed bytes inside a larger instruction. Disassemble the full instruction before editing a different build.

## Build a patched game file

1. Extract the matching baseline as `original/game.dat`. Keep a backup of the installed game file. Use Python 3.8 or newer. In PowerShell, run `Get-FileHash original/game.dat -Algorithm SHA256` and compare the result with the first row above.
2. Save the Python block below as `build_patch.py`. Keep the raw `README.md` beside it.
3. Pass the bundle name listed in the feature guide. The output path must be new. For example

   ```console
   python build_patch.py original/game.dat game.patched.dat replay-pause
   ```

4. To combine features, list their bundles in the same run. Use `all` to install the documented bundles together. Build each combination from the checked baseline. Shared input hooks are applied together for key bindings, camera behavior, frame rate and the delay toggle. The input and structure bundles also install the expanded CommandSet layout from the reference build.
5. Put the generated file in the game installation under the name `game.dat`. Use the original launcher and its matching game assets. For multiplayer checks, use matching builds and relevant game data on participating clients.

The builder checks the baseline hash, checks each old byte range and retains the section RVAs from the reference while assigning raw offsets. A selection of bundles has its own output hash. External APT, localization, map and INI data come from the target mod, where the individual guide calls for them. The two input archives contained only `game.dat`. The archive of guides contains the patch builder and its data in this README.

**Verification scope.** The byte ranges, section layouts and section contents were checked against the supplied binaries for each bundle, a multi-bundle selection and the full documented set. Gameplay and compatibility tests in the guides are procedures to run in ROTWK. A build with a different SHA-256 needs a port. Match the surrounding routine in a disassembler, recheck its calling convention, object offsets and parser tables, then recalculate hook targets for that build.

## Feature index

- [Restore the builder selection click](01-builder-selection-click-sound.md)
- [Cycle through all hired builders](02-cycle-through-all-builders.md)
- [Add Planning Mode and Select All Heroes hotkeys](03-planning-mode-and-select-all-heroes.md)
- [Keep the camera in place for on-screen builders](04-builder-camera-visibility.md)
- [Add a Select All Units on Map hotkey](05-select-all-units-on-map-hotkey.md)
- [Keep resource workers out of the builder hotkey](06-builder-worker-hotkey-filter.md)
- [Add filtering to horde member respawn](07-filtered-horde-respawn.md)
- [Change a portrait and button image without transforming the unit](08-portrait-and-button-image-upgrade.md)
- [Block spellbook power-point earnings on selected units](09-cant-earn-powerpoints.md)
- [Allow mounted special abilities at zero locomotor speed](10-mounted-special-ability-at-zero-speed.md)
- [Extend lobby faction IDs to 127](11-faction-limit-127.md)
- [Support the common unload command for Battlewagons and the Witch-king](12-general-unload-for-battlewagons-and-witch-king.md)
- [Keep units moving when switching to Defensive Stance](13-defensive-stance-keeps-units-moving.md)
- [Add map search to the lobby](14-lobby-map-search.md)
- [Add and repair the basic configurable hotkeys](15-configurable-base-hotkeys.md)
- [Expose the network delay fix in Options](16-network-delay-toggle.md)
- [Restore camera reset on a middle mouse click](17-middle-mouse-camera-reset.md)
- [Open Heroes and Upgrades tabs in replays](18-replay-heroes-and-upgrades-tabs.md)
- [Show recorded match chat in replays](19-record-match-chat-in-replays.md)
- [Pause and resume replays with Ctrl + ]](20-replay-pause-hotkey.md)
- [Mute a player's messages from the multiplayer player list](21-mute-player-messages.md)
- [Select and group buildings](22-select-buildings.md)
- [Expand engine display-mode support](23-display-mode-support.md)
- [Add missing entries to the resolution settings](24-resolution-options-list.md)
- [Offer 30 FPS and 60 FPS in Options](25-30-and-60-fps-settings.md)
- [Enforce the construction limit](26-enforce-building-limit.md)
- [Extend War of the Ring from six to eight players](27-wotr-eight-player-support.md)
- [Allow War of the Ring multiplayer with more than two participants](28-wotr-multiplayer-beyond-two-players.md)
- [Allow War of the Ring territory transfers from a non-host player](29-wotr-territory-transfers-without-host.md)
- [Raise the upgrade ID limit from 1,152 to 5,120](30-upgrade-limit-5120.md)
- [Add upgrade triggers to PillageModule](31-pillage-upgrade-trigger.md)
- [Apply RATE_OF_FIRE to ranged and melee weapon timing](32-rate-of-fire-for-ranged-and-melee.md)

## Patch builder

Save this code block as `build_patch.py`.

```python
import argparse
import base64
import hashlib
import json
from pathlib import Path
import struct
import zlib

BASE_SHA = "b70c58fd522efc81c3e25fed406f8b6d1c7a4158688e6fa501115b4236d81ed0"


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def align(size, alignment):
    return ((size + alignment - 1) // alignment) * alignment


def read_manifest(path):
    marker = "\n## Patch data\n"
    _, divider, appendix = path.read_text(encoding="utf-8").partition(marker)
    if not divider:
        raise ValueError("Patch data is missing from the original README.md")
    encoded = appendix.split("```text\n", 1)[1].split("```", 1)[0]
    return json.loads(zlib.decompress(base64.b64decode("".join(encoded.split()))))


def resolve_groups(groups, requested):
    selected = set(groups if requested == ["all"] else requested)
    pending = list(selected)
    while pending:
        name = pending.pop()
        if name not in groups:
            raise ValueError(f"Unknown patch bundle: {name}")
        for dependency in groups[name]["requires"]:
            if dependency not in selected:
                selected.add(dependency)
                pending.append(dependency)
    return selected


def build(source, manifest, requested):
    if sha256(source) != BASE_SHA:
        raise ValueError("game.dat SHA-256 differs from the documented Original build")

    selected = resolve_groups(manifest["groups"], requested)
    ranges = {}
    section_names = set()
    for name in selected:
        group = manifest["groups"][name]
        ranges.update(group["ranges"])
        section_names.update(group["sections"])

    result = bytearray(source)
    for offset_hex, (before_hex, after_hex) in sorted(ranges.items()):
        offset = int(offset_hex, 16)
        before = bytes.fromhex(before_hex)
        after = bytes.fromhex(after_hex)
        if len(before) != len(after) or result[offset:offset + len(before)] != before:
            raise ValueError(f"Original bytes differ at file offset 0x{offset:08X}")
        result[offset:offset + len(after)] = after

    if section_names:
        append_sections(result, manifest["sections"], section_names)
    return result, selected, len(ranges)


def append_sections(result, sections, selected):
    def get(fmt, offset):
        return struct.unpack_from("<" + fmt, result, offset)[0]

    def put(fmt, offset, value):
        struct.pack_into("<" + fmt, result, offset, value)

    pe = get("I", 0x3C)
    optional = pe + 24
    section_table = optional + get("H", pe + 20)
    count = get("H", pe + 6)
    if get("H", optional) != 0x10B:
        raise ValueError("Expected a PE32 executable")
    section_alignment = get("I", optional + 32)
    file_alignment = get("I", optional + 36)
    old_image_size = get("I", optional + 56)
    code_size = get("I", optional + 4)
    data_size = get("I", optional + 8)
    if section_table + 40 * (count + len(selected)) > get("I", optional + 60):
        raise ValueError("No room in the PE headers for the section table")

    image_end = old_image_size
    for name in sorted(selected, key=lambda name: sections[name][0]):
        rva, virtual_size, flags, raw_size, encoded = sections[name]
        payload = base64.b64decode(encoded, validate=True)
        if len(payload) != raw_size or rva < image_end or rva % section_alignment:
            raise ValueError(f"Invalid layout for section {name}")
        raw_offset = align(len(result), file_alignment)
        result.extend(bytes(raw_offset - len(result)))
        result.extend(payload)
        struct.pack_into(
            "<8sIIIIIIHHI",
            result,
            section_table + 40 * count,
            name.encode("ascii"),
            virtual_size,
            rva,
            raw_size,
            raw_offset,
            0,
            0,
            0,
            0,
            flags,
        )
        count += 1
        code_size += raw_size if flags & 0x20 else 0
        data_size += raw_size if flags & 0x40 else 0
        image_end = align(rva + max(virtual_size, raw_size), section_alignment)

    put("H", pe + 6, count)
    put("I", optional + 4, code_size)
    put("I", optional + 8, data_size)
    put("I", optional + 56, image_end)
    put("I", optional + 64, 0)
    put("Q", optional + 96 + 4 * 8, 0)


def main():
    parser = argparse.ArgumentParser(description="Build a ROTWK patch from an exact Original game.dat")
    parser.add_argument("original", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("bundles", nargs="+")
    parser.add_argument("--readme", type=Path, default=Path("README.md"))
    args = parser.parse_args()
    try:
        manifest = read_manifest(args.readme)
        image, selected, count = build(args.original.read_bytes(), manifest, args.bundles)
        with args.output.open("xb") as stream:
            stream.write(image)
    except (OSError, ValueError, IndexError, KeyError) as error:
        parser.exit(1, f"{error}\n")
    print(f"Bundles: {', '.join(sorted(selected))}")
    print(f"Patched byte ranges: {count}")
    print(f"SHA-256: {sha256(image)}")


if __name__ == "__main__":
    main()
```

## Patch data

The builder reads this fixture from the raw Markdown file.

```text
eNrsvFeT6lqQoPtfziv7jLzriH6QRaJwAoTrmAd5BBRQOEFN9H+fXEvClNn7VHfPje64kd8JDka5fK40S6r9f/7K99vT7vDX
v/yfv4rN7nQkHw5pfCy2G/jx3/76X9vd8VT89Yt+yIoL+bRKr/FrQj4l62v922J7hJ8P9eUkzcin8jVLw2P16XY1Dl/rItnu
kOzDsv54Dvd//e9ff+3Tt1OxT2nb8fb1Ndwkfx/S44FeCzd5SrvKslwSqhlLpEJOUAU5SVlWjRSWjdNIjqHOVEtiltNklk21
WEkUTWJZUgktqnG0qCopKScqopjRAmmUyh/FVJ6KRWyiqbJA2qCCclbVrN1E00RQQiIqSWqUxqqgJBxbC3OilGgCEb6J8wIv
CRIRzxQhYdlQTONaOIv4UGPZZ9FQi4hopLI8S0kjTotVKh7xvFSJP9euZTD9db+VWBTv/VYVjVXTp9pFVZW5myinVqLwmcsy
iRVoIVULBaUq9PjvUTxK/qG4kP62uJZySvK5o6S4KsSyoEoyqUYSoRpZ5dRYjFUYvJpGisTBQoOQyIpP1aWSIsRVdWKSiWoU
y3TUrAirJ9yWVZCgAdpqlikSG0N7MoimVFQSs0hJntcKxHkhuneSVdT7bCZiplbClajI8bGqPWtBGnOVKoaqJCj8B9E0oQoD
qpKxIsspklKvkQqj+yCaQe+pBoQq1YBaDLSdu4uEYdVHIUulmM1UCdQlvgtLLGg6x36af5FnlVQlxeQYxsWDaMJqYibUl4Uw
EerlEWWB5eH/PDQrpYIGesRnSqJCeyorQXuKDItFoLIilY0fVyXldpWFQqLwrCdKTKRF9i4tiGwlXal4GvOw3z7oz//3/z2m
IJVvi/+149DBLOMkslpRwn5XPA2FuriqamIqQGERLsBnmKU0krRqMbmY+26MVTVQP2gwrSYRkzhOVRn2PdiKaoJEjY/kTzYA
isgstV1EF1SN5e66kGm8Jj9ZGInn+IiqoiDEmqpJSW1bWJVLieBNLIYd+Em5xZvZ5D/WGIeSVA1bSTI2lkUpuxk4sAXcrbd3
8SSqjZBI7JPKRll0W3/Ynd/NCJSoTBwLOxDMggRGgZdrmxhqn1tIYDvUW17kwWoQkxKCDX+IgEeQb9u8Xl0VdhKIh5UVhy0k
hZ+3kMpFYkRnRQYHIBMjksRCkvH1ZZUVOHpZkUVRI83CECWyw/7933/9ddoUx79ft8lpXXm1D3639p0fXeInJ8hLoSaylW2I
lXrKojiT1YS9G1kxY6kKS2DmMg7sZ5jF993FyhKvhh+VRwCfFN2MU1xPF6wcm7BKVms2jIyrfaOoKGBrhQh0Wkor1VF5npej
zyqZwKtes1RKQSUzVQSr9FBNMU64hyZ/KMqJdBrJvgE3APaCrQ0r1HrTPTKlu22Z7v/ebYvN8T87pVIkK3RFVZbY6F9/xWwo
3YwiuRz+8XJczcv3l8MwYbM/XubZx2WWhYDkoyD56VORLBYe21LiJKHa5lwmwCLdtCAE+8V+DFDItql0gK9En1xpCP6XWpyE
qnR2/zlK1C8/C6yiZfL3P/9+sILMQ2DxtVQkgDn4falIUqtKP5WSlVT4QylZyf54WZW1P15WpT9e1v5cOkl+e1mUhCzkKtsE
O5On+xJMmSint8UTs1SNq5nSRNjAVEQUo0imQQ1R+9ftaXP8Ozz+/Z7ut38fdmma/Ke0XwSzmqW0NzLEY6IS8RzVESFRNVm9
NZeFt3o/tbHeRnDtH9oQw0iqllDMtNoSaUkqynd1BZGYpXMGrv8mkmap8CwChofaBBECT44EL2GSwFzfLyuVPRdDlaOXIzlR
yeXK8q634X9yimQwhDfTJ4MlFEJZiW+xeRUYRoIqfxcPKHGmibUjTzOVuBpwQzwtFMuJdrOZtdkDy8tRvYOAl+xq7W7mDsdw
E3/jNKrfX/9pBDx3i/o1EjrQvqtSEikiW3k7LQTf/2kEVM/CHWRj4T5efGkaLmXFhmaF8PGbdO5TL1gNDJdyC9eJ2xcEKeGV
eg55XhBJJvTBMfG8IkqfYhC1nnJwttxT1AzxpFLFTJoGngWs0W11eJVXq2DrLqrVHvJzZJPBRvwoKktp5RkjqEN8WnNNi0M5
/SCqhJUJhcWuVZiT46Ta12Qy9+luHV7/PobR14XcRgeSYv9xBiWRixJq1WCxoGLaBAR3IkkJPzQRL8Kvif1+R3/+szdMlDCk
M54IIVs3oSqsoN4DQ/AkcRbX0UICU5coRGupc85CFlKsx/rB9cr9PUTZKgKOYi37KJopUaUdkObBYt4yNFFUZeWeowuw9bWk
So8TXgB9rhpOhVCR6oVIIG6rtF0iGR/E5BDwJI8EA2II4TnquBeTZbrNBQUC3LBav7QSrfcnpyhJ3XgKpjkK64QFgqr4LgKW
jdYCJlSGdJEkEND/SmulBOx/zH7YYvWS7cLTIf1mzarff9GP/7jHyEFDUkXiYhKF3C2DgRWq+qrAr2r2eey8kHFR5dFkauT4
UK2tlMin6fMJAqyTLNfnE7IgiPUCyGkaKmE1IKJlf7+ejl9HQ67AhX8YAw8Ly1ctCBmofDV1PJuyanhLZOU45urQUmVDMsNi
3V9VlCqrel9WQRRu4TBYj0gkES6p8+krlHkoT5o810wUkQUrLkpsVHnGUIq/C1qJArHRPUeJyKxLVd9D9lbkpiUSMQp0iJKm
cbUicZDSPBRJ5jOpEuEFja9FBEgIiUjlE/an+Hjap2Ch19U0f5nxaJ3k+x1RH/gUh5v6U3qhh3S7MIGi9W/r8/o/ch7H85Ks
0Q3LSynkUmRCJVFTo1voCEaXzgZswIRu+lCLFPUexvKaJFcax6a3rSmDO3+c23BJGNHgM4LQkSfLG0cqOPfbZdiC8k3VaS4S
K2K9zxIlEpSPvlVgU75OkDOZ2vAMQncpfLhe4TbdcizU062pMi9ldxFNkb49HgzZWJG0p/UFrc2oFkHOr958gRDVhroS4RWh
OuWBtDu+2RJY6/TRIMQatEFBzqS6FjHlEil71CKqKbXFYpxx1JcrMheTGoiGJMWB2hZIOb+JHWCRD9v9P+xG2BpcFFUZLcvd
Y5Jf9aU4/SYV4ZM4De8JKYjxvFbXEH2IamLoClVi6NPf6+K1OH6nwHG4+3MfBXD3Ct1OHC8kCtE1lmSbfNVKuT3uv0Z+8GN1
zE0+gfelH4/7c5GW9Ucye/9kqpRY5Oo8FbY0OUypMmIVIjjpw7kuiMq1Y4D9ohLRjKa0avSNaHw7H4EMGxwiW1ljNcm+iqZR
HWBKqUjCTIGGMipER59F0yrXJBYeOgB+iAryEPxodx/H8xB1VwkB5C4SWXFF0yAHe1zWbs4fhpGlMND6zBHSGjV7PsnmuES4
N8iKrFQ1CHEwFazFIjZUaIwAyXQEuk21PIaNrjxEwCFXcXFCj4huiVYYRrSrEFOzMrQuQ7UyT/Lom7GUFOWzsxMySB3ZqkGi
KTefIsRSpaYCeElVBBmxOo9SPh7xxZJIzR455SJWvtZo7Tm+DDW6ftQqsvcMhZOrn2MFPJgocCSaud1gCGVNTtkPtXCKShtS
xKdBQ5gJzuBL5RK5S1Af4cRgcVLwa1VwoqXgSe72gmzBW0IisbEExlCCMKrqQ6Rm0kejqchSJNzEk4/iqqKGX8Qhurhr40dx
iNfFhzjNyXb5PkzS32x8uCqt/sk2yRxX+XZBkiWwp3F95shq9K7KzQCp9XqosK4qdCyjHidTEp7nau1lBTl9pB/Py8mKmsTR
UcUcrBCvShy4GQgJJBGSevKtHmHCy0JVBbjyVL5nM7dbRlHCV+5D0sg5Y/x0ECbTVfssLsr1XIrVvYQ69QnFm/BD9HbQRnUW
fhLvl1IprfuusZJKHQZ/z1qjL42mqvxtTZCXi9U2hZpCUpMgalwdtrCyqjxtfDmTK10U+USA1rR6jgUeluKxq+Usjm75oMKx
9IgcVJd8rsQVNlW/bF9ejWP5dteHnu3KIS/W6QcPZo19Fs2q+35Vn3mBvfUZ4o/4o2jKKlRHQF9FiFPqBL8SFiAIlT6cl6mQ
y2bPnYAWVFaqFzOLyMb+IJ4IXBWEyqrGPqWRgpiFlfDt+JYjUeNNWflbR0BZIYsXbvFGqtxa+HyLDVJEpfbJiQyxrVrZAQmc
MrU2tRiMMry3It9auesYDEh8buFRTJG/LVbPVPx9MVGLo8cGlNXqds+jWBQJ3xQLwzgSnidZqg/8BVF5xIl8GPGxdFs6yIaf
NxYofKh+vBcbRkIVe1fiUfy0GhH7VTyVpXqmtCdxWA8BjEedAcacciv2eQypXAeNtPitcx+KZ8ofisNlupVY2EpEhL+pJPs8
BWlaHQrznBoL7K2TZLpB5+s279MtZlVhjZqqUH58e24501jlsWZ8vWYfjGaUsPJvOp7yqiLexy1J4r24AmpcjTuUE0XJfldc
E6pjiJRMFstz9ciT+FboIVqFQJ+sTSJUgncxrbozQ4Q+mf5Efa5RYJW4Ojx+MnVVZKukEBgkH0QT/mYVVSLKQcxepw5fRaP6
ph45RLz3UxYrwdu9mChlteegGuLD2/FBmgiyEn68W51wNw9NlklhP22tCBIfRf0SAylgGuKbd1EFUb0XACFZkdkPorJ0bwHm
qjZftwIkcqkKfAiCIFlK5OfNKwhJtYJsCtnw8210NkrSJ/8sfx6DksLOT762kKbVnQHi92EPiWrtjyAQl+8TCmJZnZZ/9hdR
yMofO5JmvPitqAhh4EfRDOLpR+MS9DuJq3vavKjwWWWp1IT7dDCsPT8SoHB3Dw/hePxBK7UkAT/HfjpPluRIfXbnJLapb6WF
ify0bES0ukHyxZWLCmTi4be1gLaHH2sJtSpW/lpLBBqUPVZNFL8xECkn0ujzm9FHsaDWGkjG/01hJfxc+FY0Aa3/Tacg8w8/
xzu3W4ccn9zqe4jXT2V8qSnOZDH6brsmbAYWk32I1feyExrc3MQk/pOYkt7iMJnEkEosQL5WJ05sKnMf+hVnKlspogTzdLee
9TC+E+eS74eR8CoXf1rr+uEnOUmfD6WIaH0+/00tWnXpSy1c9qUWTcq+ryWNsrtd/ah3kQL6+nzunsYwqm9rkVhIS9n7tpGJ
pbnZOpYHzXg6hgFRNX2EK5r4yXTF3K3Ah7vPoZCk2ad+VofRkFWFksA+i6bC96G3lKZcyD5Ztfhm1ep0QdJ4RfxyFAv5b8wL
H7MNDlypnNFMo46XNBYS/SrTUKTq86N4+P2GlVmVE5NvhxXK4KyeJo6I1r7qm1rEylg/+gdBoQh+6tE/cvu0qo88nVF9vheX
xK/9o3fyi/U6zL85NN6+Rl9uW3xKHr/c0xekqv8Rz4YcR++wqkQX6pv2sPfqszcSw5K7KBAkPe7pC1JWnYaHnEhOv2M2SW7P
T9B6Puw+VYX4q7qhKyqsSrKZ2zEkJyQfDqNBNKH7OmOrZ1+IWPzhbkB4TP/eZn9nMNCfTcXnscckgiXiKXQlU+92g88gi3lk
X3EYKmrt6zjoWaSSg4tH5MypnPpN9hUnSXWMlQngAmNwUIIo18fcbJZKqvwheo7JcU/VmViIlHtnJAm2pvzoDOgM3Ub08Tn+
6efbQZgqf+hdKiaq+uSoiGh2e/Iq4WORI4ez0DfI1VnhU+FYvRX+3XNgUF2m0A5R/8+rj5+TOmX9NF1ZAubzQ4cytloGMlEc
JHUZ7BKOJU8hSQo5H4ENTQ6tJHKDAZQMYmHyEFRlZuRbZT99cI00V6UpUHkU0/Pw7P7EzOeecaJ0i3I4lj6odhMGf8h9XsKs
zpdAXCBPsikCpNmfxy/wCfu1y7dj3qfbCF90+pXejfjzAS8X85VFTtRMiCu7IbNpcrsVEItVWEQfXhDZx88xdSJa9eQL6AL3
uFTd0//+Eq1Mqx5h49QPl9LfXdKqI+iwmhEuvl/iIQHWfndJlpLfj0uT2Orc88O4RDZWY/Xbnyvj8qV39FLy7XDJpVT8trKM
+21l1SMjn0toVZz9XRsQlH9bojpSgqxVA/dctQRBNHz50J5WPWX7pWJJFJIs+t2llONuZ5Hk+IZsC9hnYKbuxlxWeFn6cuj3
7/TmWvp44uWmo//ybxwnyOQU6RfH8/A/CMNkDqIm/hcnCfKvv1YOr+k9t5XrFQ75n7FUy9xaXGfw2Sffyf/0gOl4uhi/wkeP
fif/s/vvZl3eupfX3+/lDf1W3rS1g1+XD+7l835k1+Wb9/LuO3/R6/LlrbwhPsrn9/LJo3zrUd66lzfze/nDo/zhXj58lO/c
yzdH9/LWffxG/igv3stPH+X79/LO8l7evo/fCO7lDftePniUH97L24/x24/xe4/y/r384FF+/Cj/GL9zH7+uPsrH9/K9R/nZ
vbz1GH/zsf7lo/z2Xr79KB/dy5uP8bv38eurR3n2Xt57lE8f+vcYv3sfvz67lzf1R/nm6FiXXzza764UvyrvPcb/Ou+xdfnO
vfzL5F5+9Sh/uZdvPcZ/fpSf3ct3Xu/lN4/5G9/LvzzGLz7Krx7zz9/Lvz3KS4/yj/U3HuXLx/o/xn98rH9yL99+6P/Lo7x6
Lz96jL986K9xL9956P/oXt567P/xY/zvj/Lre/nuQ//jR/nH/p8+xs8/9l/rUf4x/vWj/GP/h4/xS4/yx3v53mP8p0f5x/6P
H+NXH/ZjcC/ff4xfeJR/7P/0MX7mYf+I/hupYnuVUTV8Q/8NnXcfXgG8ZvCK4ZXDa6V3wZp2LRteHrw68PLhFcBrBq8YXjm8
QG4EciOQG4HcCORGIDcCuRHIjUBuBHIjkFuC3BLkliC3BLmlry+DiRh457bstd4W/UZ7EBXtUXS1Grbez6/ERphWY2j3lzkZ
qil5ZBraO9rvF01XrnmjR02xd35ZxKv+sqTjfb/O1t1zbx3wYcToyP9oSOhxe8yuChZkSD9+CSoH/1MklSWHvewvEd5//RWs
tGDMHrNgNfZHtjOfsl3PHw+ywXjhD8at1igY98a205lyswtOLYIgCIIgCIIgX2hd8kI8bD3d1nNm5cXXjjTKL6yRN5ajwnhv
eofxrp/NdW/KJHrYXsvk+MfsJpm1ZcnxWrOZLDK1v5hM4w3DbK/KKWMaq1ehxTCnrieefGvndIoXpvwfOn5nP3gtrV66s/Xr
5jrQnf5kk+vutmXrybY50Lu7Qewb710Pkutx66J3M3GoG1dWPOjxsdfWm4ay8q1DKtn6mYE0v3fyVr6pZyf2S1PT9BTpHevt
tTTPSuugz1zlqLtGQ/F1tbdT/3+mV6a/+vTaDi+GkJtO6fppruQ+PdwWgvE2Waj1751cyGN9GjRP9OjWsjqxZd3KFxdhlnVF
fZEc+ov+lh6QpJdSt8Qp1a6CO/j0Wo8emCzatpuC3sL1ET0xLFhD35bGRfFNR8sb9pWeYB74RTbrL9r0UKl/ZEWbHKYs2uQw
xTQaWW7ousE3o41I+mspaVPLO3ApoCdOfd8ix+ScHmxcwx9A3VZADs0vZeDFaa0DL/Z2mEC/Y4O1xKNuQ58SvWj7znBpuu5R
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
Ob/bv/scI6riXuhb8FW/Ljd9bmo/tY/z/jmr7KNJ9OvrHNK4obJHe/rAxpc5bd7nFDr9wzmd9bRqTmdlWenPuVzO/JLqaevr
vH7jY4Obj133+z/1sb5SzWvLBh8L9tB5IWcqTDa879/hP+zfyh421J/aw2wj0vkd2tRerFtjel6oaek9Dhz3mToO/KCvx+JS
rm66I2ftn45x8OLROGLRA91hG6Cn9XyaXl+XfrMv3NsatvbXn66hYKY6XUO/vdeC9kis402XtKFfrTIftgPyWi6J322xsbvQ
i4333Rr6Px7fJmyJ1n0N2UZbYP9T7VbzKjHuT/fkW93uwqbx2acYqfGIkWw6x+Y/xEhFW81+GCMNOSU/M4asE/uf09hlATmd
zL7cYhef7BGb2trLl9jlHnNb08tPY25bOJmMyNq59Dymb/MUg9bdt8qf6s2Y1A16Y5I8Zcbbi6lF9tx9P8T3/fCH9lrvP25P
jxvuoz3OztmiziFMq7SLf4oNuupPbelwsSuy59igT//q8bZGRpLr/xyLLCXlx7GW8am9cf4xFrF+EIsU6x+3Nyrk1fnR3sCb
dh75bGGVnes/2M1F8POxHZYr5mY3IW73ie6vKt33hy9Puh9Qv0t1f/H7uL2/PP1U96fcy5xR3Z0xv1qNYevd2PGO4e33/q7O
vwya4wbPudd3edf2pPww71q1d/MNic+dwWd/FIx+4I8WQ+Wn8WQy0TbZwx8taf3M3Yaa+tim562/9bmV3WRS4af+SD3vhCe7
+Smvzd8/5rX69bu8tvPd/L6ehJ/Or81CH5b+0Hq2l3+KKcY/Ht+6p7aUR0zhD93nc5A/5ABtJfvhmk325eb8yGGl/GnP9Wg7
Hpmvaq7aqw9tzg5x67YH2tPDT/dAwDRTeuYyLTmpd36/6+P4ro+PNuMWjWl+265z/nG71q3dqORoXNQ4l086Q3ytvWwc9Vvu
XFzg9Q/7kOmdf3r+4Xot+PpfbO/tx+299rz51/aK0yOWcKjfpecCsy+xxOM8YCgzP4wlsqGwhbxp4M3sp3Ms+5/2g5mef7rf
Pfat/RxjN9e3f+Wiyg2DW274p/aO6f6n8SDHho/2vqzd01waND78x7mcy+efzmXM7mEuwe8ePvrd9+9tdrUnqvhFf3/7afwy
PRYljV9Gyw/nuvYjP/P/eNbaPu9+uv+W2culPmudkXPdRd+9HrJbbFaf7db7/lvbVp//yT+NbUcC1A+2bRYEnd6Z/a+vX976
cdv+WDhAXC3qxJ4e7FY9n5b5iCE+6ma1v8veT89T1366b9MzZMeCtdMb9nrzdmWkp/Hc8+s/rF/zvP3p+uku1F+tX0nPyvua
YPcKt/Y1NvSlPbiYrcFyyQwu1u7Qd0TSn2UgxLK+BD2GtYhy+sw55BoreeJuIOYbjrjBdHg1uLiZXGeTwdpr0meo6LNT0XKb
hxOJnU9bp9mkzKOJ8x5eDX42uezmTYcNJ9rJa84X4eSynpuiXv0rmoc8mRqb+NVZzYfGOnWNRbTp7iJelD13XM6F1mLeDEi9
q/k0zyNhzEJbIKuX7ULkOiNbaufGP/erud6EJnecTbt7r7lYxHyez3jtEDXX71W/BuukOV7Ca/WT+pKJtI9eNSEqjG04Sbbt
CQd1wlhenUMyCU660+qPnaT9PIb5dFHOJhJtr1cYOxgnN3+d72b8eh1tfJiv8TESWhLM0TkuntsmdR/ff9KvaKJdYR7ZEH7z
rODSWerP87uaT+a76HVN1yK+PtagPTTGtzrjqw7z6uFfzyMIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAI
giAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAI
giAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAI
giAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAI
giAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAI
giAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAI
giAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAI
giAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAI
giAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAI
giAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAI
giAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAI
giAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAI
giAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAI
giAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAI
giAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiAIgiDIf5G//vevv/5XtE7icPfXv/wbx8myJrHiL5X9
xckcK3O8Iqu/JI7/9dc4yof96Uov0vEkEI+J6R05y5mPGM2YTc6hNdF9qM9hWzNT2eSkbkNy+6G1KXX6uy0e20Z7aXLTjs4I
M5vRTLt0fZMpw+48K8Sq+DGdxh1cFuS/wr9Srd6nh8N2f6zUWhFklv3Fs+pXvZ5t1mNuPsobZZALrKfrDe9AdLa51U+msQt8
i2G9k3jQA133TvqOvq81yXKZIpgeptsjJ1kbwRL5F9J4URatUWYajYFqwR5oJN7RM711V/T6kiNIu05yao/T8nKdrRPZO4R5
dsh0aC8r3tpxXljMIml4y3WiukFQcLndG2/tRA/6m05/by7XnOgGZi9W+xu10z8eD8Y0XRi56vm9QFglca89SnNl5C+45vY4
tryjpnorueACv2Bzu/Df2oFetAeDYcvuHVoDsa/bvfWeAZaTKTvhpGwaez6q0P9gvd7ujqei1mpF1uRfnCqo4i9BkVRWk0Vi
ulVRAM3eNI0JIwTeuLFYebqt56rfWcQGa/DNRE6WyYbRFhu/4URamjGNzYKbM8ymaXYHieFDmYnn0zLebM53R/H71uqnHtN4
jbkWkTMmckfNdd+0LvpgsZkdu5q3KeU0eM36jXjW1zgVXgy8tN5iZoJOkfahrkXPilK9t5bT5rmqpx/ArrvVc+hm9ohcLyLB
Jf1piaJ7sHUQ8forVW+cDHPY9a8LnxE6M7m/6lZl8/4+L1dFcllsxpOWNOtqtm7tTm+tAyNd8iINDcXQTSIr9XWQ9VdBYxka
Oe2Xbclip+Vt2NmcpTvz2tt0RJgPah22G/B4G6sTmy+W3ntx9NC+Tn3Ht5aDpG9fSnifcGJ/3TGSUuyKlm5wnfFE3gTWVfc2
60A8zIpkuS3JNhOnejJsyvvq2kxu9+HHhlO6waBICrkkvzvHRJaHlUfsdKNp3GuV0VY/9Ds69MFK89JK/Jk0XCw469CF/nur
nMmzJD1Z1z5jkT6Dhw5da9NO/KHDC8Hc9/pmy+uLruB3c2Hb0YXppRdsZ0nq7nWx7zHcEfq+MYrEtBq+w5newV4nA1hhy8qZ
lZn4adtoTcRR39NLDuZ3HLa4pTuEdmZWOzeJeubMwUj0hrgg1tPrK/omcE469eZSuWF7ZA4OZxju+6ZM9LkpaxPretaiIjHA
63fHNLJQDnScuXDo6K6fFUInX2RztukdRzaZrxaZRO1Nd0wxC7owVxFY575teX2r5bnKtD16192p34mNPWsO26uFWaql2XK8
cXyEen06B9M3sHYiWLuklJt2cvZ0s5zo5N0SpzR2efIKXu0V7Atdj9jJ3eiqw34CXVL0tvWue10FTH1/4dFQ58JuObC6x3e7
vcwTu6MX42lZZBsmLkfQ16NjOml3qA/F1mvi6H3GL7JXOXA4C7yKo/SZYQHtFez00GNjO7Hktm8MQT98IXdzD+bkkqu610le
WoP02h6kZf+cF0Qfk+V0A3XlqjmNJ3n2li9yW89Kac/mewZku2N978vaa4vbbq5kLXaMAqq3Cqawz1fe+t15nkO94UzIVKux
s7iPV7+ULz06Tw9v0bfKxuvcpXVs1gUbeFthwINlANmuSmS3glF9t9wW0dUi2KsFuy8L/+rQtmzQOUPjZEewej7HkjKJfiT6
MJDbGVnv2TVdr5hztR+DtNiQrk06G6v+Hj1/J+t2Ksm6G34B9q9IGu3x1XTY7Xqsuv60yJbbPiNUe1G/tseZKdrBAHSpzbBO
YV2uQ4PhriyU5ziv3zCn49f8naNjMaeDpJM1rLQs9cR+aftQL6yNErQXsS94OkTD8yJ+gd/yQ8F2OiffI3piNSACtpRXt9on
OeyniUS8vm5tXjL/fTvrk/6s7POYtuvmagf2tJolIeMaUzp/Bo0uRmPaDxJFFFeq2w6s/agT69KhLOC73l/Hhn8yj+OYRi71
mhJj4k5n8siLwWb7q9ZvXh631kgUzgl0Lh/rkQxkT2nAWoRhvtkqZ9AdbtmitmC06iZER1zfDdLFlazT5HVry912g64d3duB
ZE2JXoD/4dztmJbfvemNgqfy9dp9aM/a1+21t6+/bS9P6/YM2VV+255+a6+3KJ7bu0V+sOc6RHd7/vjWvi939xqp77SWDDU3
W43e4gINMOBDObu9u/qZpxNdmmXnSpeMa3s0MMUXbnyB6NFgNItJfNhnGaxt46D2Fr6bBC292FkjH+zootviVI+NDXHbXo5d
P+9vW8n1Tc/02NDdYFmtofGmg2+1wU5YimjljbwMess+A9ti0s6pTsgRC++mvGBd4lPETnLeqmcI6sRNk/h7l5Rv5/vx1NbD
3GXY3vKtCbZBVjWw7YfMEocdoh4h6Fwh6dT+QmS7JWM79/fV2LoNsDUFjE93apsHfs4kNqg1NMH2dQ4k4xucvMSIc4vaOcVp
yDqxpt5RB/ss6lO/f9rG9X5ocUa0tUj/Q+awyuO4apeNO7A/jMR/hWxxUhJ/I19SKm/ODvZxTn3S3pycmxZE40Mb9MA79j1v
PRbtsDVKfeK/u6rHdVXH2vbila6DXp8Mx4tz4w3Wk8YlErG73DQnMUkvmXO7WUeLqZ0zWGd2dOSOK+qvG703U5Y97xAs6L60
wFcepw4ZW68QG7DsYW74ZN4YRc9J/08uZ1XjJz6JyC3PjYzqDNuenGEvnnyLzF87tytbsLUSnXs50YkyYE4qXwr2pO9PwZ4I
gU8z7FdSFmIj0kfr1TPpGvBltRawvnpjXOoNvnRq/YPx5YLY0adBRPS6YFk/bxc6beZJ9sANqGyoHVYktjiVV2JDdEuaPtl4
6pun43Xnwov9A/hizbRcsEEv3SShmYwjgO8SIWYQ0oFD9so4LYhuQOg2IH4N1mNzKabCinkfJaI9veqg0KzHORKskwj9yM1G
TvqxnKkx6SMjTPNT86Vc5RDDamZLjRb+NOiAfQXdKdfc9tlOiZwKuwriuiWTMJe6rz1LMYZtQ5y2LNFPiX4XsShZw4ElgE2A
jMyweiuq96d3YohNv3fhxCoGGM3JLPUubEc7ruD7kNGp6zfbfdiQZ5/oPR1fd5Au/HBlbGFXQMaY62KT+IDUgfm16ckHxCwn
PyD1zzXmVTZzavP9bT57nZVmMTLnS13XOuVb21Og7HbZob+zw91Sh/lRHLAh6eJz/S3Xf+d53xSpskCs5W78F4gfK5/S2giN
sKPveiXEHsKKZ6crPrZm/flgCntn7g4tKGslxnxBvs+uySpp9aM5rFMidY+O1F0lL+R7d7MVzi7I07Za7nTBk71nbA+JReVv
Y7Oag5VuvM7WqdXPpCKYidsJmWfqG+3LSn/VZ7f14rtzZpGVuV/FWGvIWP2C+DCp57MrXxP1ZNS0+jMaQ+iJWSh9MsaWLlXt
G5xjreeWG/RhvA3Dr8bLLNdGz/WbQWNxIfb9Ht/RWDWB+L1/cF5ssXsUdRJfLWKwWTqdPsnIjITU2xSPJdmzttfP9dnmnWT3
4BMtUW96g7S/K0g/LDfaMkSexHmrRHOEq94JTZ7GTIaZMzs1yfr7C3/2LOt1rjsK8VMw3RszY0wDtNwkNsZvnl8sjzP1sM9O
iR+Zr/QpiatmNn0v2INXBJCxswcf3r1F0hKbsw3YGr0Dq2wTGcM3UthrbV8vWkFZtPwLfC6HrUFmbTkGQiKxL4L9CIrLyeHL
hp1TfTyMaZ9h/8qSsb+aQ6P0aRzRDgZDsJ9Dh92Iaqh5nULc6QPSF6ll0/dxh9hMiN+EbRFA/1ih7LHbOIlmUpYuOGNraCLE
TKbX1RSwZc3eaQl2pwOyYF/0FZUXtzGxk8mM2YtbbqqPVsEiKWislYPdtby1AnvTsnvrdxLTFVkP8pfBFWIpW7YyHhyp1ehr
rN086y2vJzrE/ulGw/AOkayplxJ+o/ZV73Jt0E563ZsOs6ILcfC1W6yMJpmzFX3XpaCEHEo8tgxr3bbdwIUt7zE0T+vrLYuL
iYNNYmt/8o6pQfKP7oir+0ByJB5yE05uHAQyvlypxqa7o0NP2s7oOGE+GUHJtVXg65tR2JuKXpJM2lO/lKYLg3ufwRzMbnNg
7csZnTvWHbn6chwbvQHkbzSnCVqd+LVledPZUx6zBf8VfLTRYPcssz3wc8mg8Q/oebwi8YHVr+JI2FOmTP0G6ADNBV2wHWUd
i3vrFwfi8bIY0phcenejXDl0qnEN3ELsUD9H/Fl/bIpTG3Iw4kvj1ozoaHt7sir/tqpzwpzkhFKdE4o0J/SrnPC6YduyOSXz
2covQ6KDVgmxd4MrbeILd6OntkneSmLi7FitSfq+H3k9pV5/Vl66fC+RWMnrNe7rL54set16bdJ3N1gU4oz2H2L41nlB2yQ2
qg9+/JFTEt8JcUGuzlay0mhXPoPG2W3mPQhIedkcQUCpgj/sKVV7MM+tmOZI19lJMaje1e23xepkMBA88IH2ciosXzPNuYLf
vvazBuREZWH4fRJXKjNuzHkbb2i/vIx02Gv2nsabqnh0rpY7XE6nHSjvQ07ZKbJma5yYMvWxnbkNQRPxmzajvXQHybD63dtI
AeSUJ3e2n+nGhOxH4k/LcSp2moZFxnpyoCTkyBCnQP7YFGkuSufgMd+WOO6SbUHnqbln5P6ejr8kcc5Lt/yYE3bH4Csfdtc7
wl45JhY9BV07qjflk0ET9rVvXfKOfn4l9tTarYktbx4dVb+2EogrB+mwnb8YUxJPkNizznXhPe+fF2brqi/9xHzppmDqBuk7
vAqLuawFXewbnsfJZ7HPNKexBfOb9xKHfT8dTvKoFImvX3lu883JIHbsifQd9M1iGuWO/ra5nFxD8EsSx02jxJw29dLde30N
+t7VVHPM5aeV40BOvGovlukr+JRp4N3HnzE5+VxkRjRda0mZ58/nCaviPRBprAt+KGekVTIgZ04rLaG+JHZi8t4kk2G2rMmF
zo1A/TyxjwcSm4MtDSBf0W34nNefPRKzbye+KpC4HOKyEvoqwN6wGHUc6IWmWxCn6Y2Axn5W3Z4bdHqjcUl8EDkrKt1gR84W
+pDnknnvTg367tB+kPdB/b4g70R+KQcetS9ZmkMOJFt9Kgt7dDB1jepzlacM/Ydcemovykv/9h36PivE2B+VZJ9Mg8Q6tQdJ
0Z6m/q4UeatBpsOC/sJ7cpnAtWF7lOq7csYbH64tYnLusCLj2fILOndXanuOoHvHRIL5jci4q/OM/l4TLbcaS4vXG+f3vbSi
Z60lR+t4zbJGEfdaV8gvWBJnbLuaDPNbgq9ivdV4Tup66W6r+XsDu3ttNb21Z/SOXMFOZ3rcg776Rkl922pGfbqY2mScvWTB
mOLJLWyVxISWxSpWIaUdei3ekWvTVXVtANcGPVj3xA+kcQq5hPjqWuQaOTMicaL3OrWr72OVxIzJO+PMSw9iVWLfOmAXSngd
mMtkZrbZ573aj93BLuKl995yZ8+ng0U4KfWRYLDhRDvF71s5eB2/R/yFS5rrc5Qbz/L96PWyi17HYPk+/O6MHWMx5wPdnxrs
c12D8cCfTZJ1RzcMkP+uzEW3nTKxtZK2t+nIvdU4CJrOZj7yfl9f+dv62N/Xt/quPnM+SXYwzq/12d1F9NpdR9/2vbWO+TFp
yx9bRDa5zqbGNpx03++/Od1l/Dpek7oDxydtjSJhfJrr9+9eJAz28+n6UcaW1ombnOPXg+6PjYD0fdAcs7PJ+vCQaV3DSbJN
mtI6Fjp3uWFzvIjcwfbRPumjdkimpN/io761MXrUNfcDVjonzeB+PeDHp5hfs+F0vkvc/9vemzWprgPrgv/lvLIjbIMx8NAP
kgds40kGg+ENbLDNZKoYDETc/96ZMkOtWmuf3jtun3v79C1HVFCfNVhKpVKZUkrafHnv3YAvvpTjtF3Gng912L7fSRKkXb/x
eDfbjdep+S7neNc7TJvv77GJVMwn43P6pou3aM0Os/idJoyM6TvP/DBr5jSdQL2qVxo7eqfXZ5NrvmQvzBYt+91WBr0k+9CC
ONUvdYmgvaPrdrZnb5o2x23WNE7Rbrufm7++n+x6l0W0Pf+Sx/hwWTSlII1/z2MW2zn2rdn3sP34sOiH2+TNJw7wxCjt976V
zxDTvrGei9Il3UV/yoNN4y/tz8vjVVDP4xTKOq9+zR/fk2/9JNzb+WIyHkI+2+9ho0kP2nYM6dr3OfBUutuKQONvfeZXOn7r
a/hdbTqRhpx/yR/S1vSzv8md32j7N/luk50xnMXe9o95R7Y0n1w3s9j6U/oHvX+tM6dtHEL/8z6h/s0Z+/t8QcaI8z/W6Zc2
+FP4dtH/VQazvY08LoKsvSe/pgG+NY5pP1ensX3/pbxblDe948LA7403v9al7pfQ944p0Olbuks6aW/CfT5Bub+YRL+Upe6v
4z+GvfquMbsszPHpG33qfjz+YxgwafZr+Tdf+rVkSNPJlcufr98bNdvH+aS9jfq9W6q3pcWveSJvbkBeHqfxhswOdLfpz9nv
v9oa52MDLQbdPyWgr2QejOcqzqcSJgFe4Vyvoo3AbvYo6BSuB/FDDHeI2M3oAsP39wD0th7OFX+6gkVyHedjk3s3+xdrvN41
hPjL94vrCHD1gvSA+PzCao74/QVthnj4wnqIOH9hw0ZcvHCfIl6/cRtx/MIm//7mhS3+/e0L2/z7uxce8O/fXtjh37++sMu/
P33Xl39/9sb8+28PBJ9/f/TCAf/+6k2fPAIcvekzQzx50ydEfHnTx0YcvulDEZ/euI14/KbXFfHxTZ8D4s67PDNsr+4b8/br
vctnDwE3vpQXsfDGbcD0DWmImH5pb8Tquz4UsfbGM8T6G18Rv9tP4/m96a1huGZ+4Q/EwZf6I7bf9cf8tTe9+hxbb/7A8mnv
9jJ5eufNL1h/zXtjXt7hF35C/P6+zcPf+Q0wPX1/f8Dp9c7f4enfLmMuT//+nsfTm1/4C/G7/D5Pb39pz+Gz/9WNYL/6H8eU
vvpfjduv/kdr+r/6H8fa4dX/ONbzV/+jNX1f/Y/jfvjqfxyb9qv/cWzRV/+rcfvV/zi2r6/+x/Hg8Op/HDv5q//Rml6v/sex
F776H8e+/ep/HAf01f9qzL8fvel1ffW/mj6HV/+r6ZO/+l9Nn9mr/9X0CV/9r6aP/ep/NX14f+Xtw2p5FT3bh9X8GD3bh9X8
Fj3bh2Ob5zd8Y54+f+EBT1+8sMPTr1/Y5enjN+bpNy/s8fTbF/Z5+t0LBzz97Y15+usLk8P42T51I8zGz/bhWLXHz/apcXv8
bB9W89v42T4c6zx99MIGTz95Y57+8qYnTx++6cnTn9705OnHb8zTH9/05Ol5++j1eDB+to9e03P8bB+95r/xs3049jgevrDP
cf7CAcfFC5PZ5Nk+ek2vybN99Fo+Tp7to9f8Nnm2j17TZ/JsH73uj5Nn++i1vJs820ev6TF5to9e89fk2T56Lb8mz/Z51H/y
bJ9H/SfP9nnUf/Jsn0f9J8/2edR/8myfR/0nz/Z51D9+ts+j/vGzfR71j5/t86g/YJqMQT+ZbVc3qD9ihniCuI9rRPSMeMnn
wnh6To8h94rEqlE+vm2x1QY49NXjgcnXtnhTj2BE0l0S6lTLdD9jFfZdhzGlfs96iI2K3ajuYjhk6epBFhKqd/WwYjLVIh0y
Vah2xPg3zGdI4D2SnDGJ6pbuMXxP9FHFMgLhbgXpNV7NOf5CPhBP11mG8WTMD/JN4Dvs+ihHE78TMMgXvgvpLvgeytOo04Uu
fq+P5dWY7hMoP+TLeDjRh/y7ie6RGgf4Hb3C8gDdef4tfO+x0Hp9h9eLelQrdbD6KqqJOl+EVBOkF8V6AR1U/E5df0hPsF6y
7mbwPRUaH8dHwyUDPkX4D9MBfbyKdetyhAH+Qv0o1hvi31DDcCvWwXQQv4fpAoLpKqRzj+qy7mT19xhvtyddM/yVsJ1GpE7H
GJQD6AD5dql+/NpuCg8nX+gL3w2qupw+b38X81Mw32c9GMH8jjW71/VpPPijx+tZsd6rvYGe0E4S5gu/vL4eluf1nazms2e5
gW4Oyh/axXjw3sJ2bT/iazy/rE5vqBAP2s2vsN0s+A62K6nrCeXysD1V+a0KEUyfYH7Kgy9PVGd6iOXD9s9Ch9MFsZ4g/XBq
Gvmo93jfQLrWfIf+AtQguo7C4c77M6YHOgZZTVdoJ14+4AeTty/WW0O+qPnUzbA8Zc1v+gaFzom8+ATjYz9EfmIix7x/8PgZ
0h3oJTz6zQ3f+5gPFTH/7iM+xOs++rFVf4fydMh/6AlY4S/QS3z0xybRIuIxqI/GReDqwa8S708Mygv5jMizXs/vwHvk1wz5
Nar5AeldIb2sRzuKwKcvPuT0D0idL+P9FujykBfv9DVfuAzz5f1F/tvvc3mH9GX4vlPzU83PXN7xflPzM4rOB316NX//J/GA
z11Wl+sZj7G6nh5+F/rhEOWf5tbtWvejuv9gP4F4fgX9uy4ffbRD70HXL/XhfH59yWOg17AKDcrHiVqO8PLV3+ftWtM1etBx
U8sFpBMDuuD3eLm6WE/pIR9vtXyD8vD+9Or3dXnZq18ssVx1/z9+kQtIn2NdPp33N/Ioj4zvOb/Uclf8Si8X+4Wmv+QryN2n
vGg92utZboL9vqaji/Xi/S2s6nTwPR/rFT7G//AxDsLv/fErPn6lx2/z8dt6/MqP3zZ55sMtN9onmk5clN/6FH/r8ZXQC+mL
ZMbfR2SRUa63RITmpJ/g+4wYEeGrjAYhU0b3pB9BfwIq9LskrSjXqzZDII3t5ihM0Jd/UwDWZZIyekLvA24sfcXsG86+4epX
7H1L731L731L731L739L7/P0LkkJBf2jIoOqtn+hFURiWmRByCeXstgrTEaSjB6JeoTw39Lpv6eLfksXZr+lM39Pl/2Wbvh7
OQe/pzv+lq5W/n5J5/2eTv493e/1Y7+lM/Tf0kW/12/0ezr2W7rx7/Wb/J4u+S3d5Pf6zX5PV3LjGcNTXl/9G7a+YfcbZt9w
9A1Pv+HkG86+4c03/L18x2+4+obFb1j+hru/YoN8w9/qb3yrv/Gt/sa3+hvf6m98q7/xrf7Gt/ob3+pft88IfczmjO6wfZ/9
MKpoSfobMsugPbHfYVZQvjkY96Q//dpe39Prf0ofsj+ln/4pvfmn9Nw4/C395k/pB39MX/0pffWn9N6f0o/+WP/un9KzP6WP
/lT/uv2/px/9Kf34T/Wv+eF7+skf0/+p/jV/fE8/+1P6Cbfz9FqfU7nedkUTEMYBblfDeCLhOGezOh7If+kR74bvIV0dr8L0
5GXPEK4Pot4L46OB36316OVm1P1YmcPRxGZBO8f59wT9guv5wBTx8YWdELH8wi4FTNTR6onRl5sUL+xdEXdf2N8CprsXDg6I
my9MUrWbqcsXpjlg7Z2/aqu8PE8MmirO744uD6xjOD2+ca/O74mNtorzISPBes43Iz6/sInfI40XtkLMz3phm+fP3hjzp8sX
HmwRly/sIFYnL+xievUd7mJ5NPeFPYyvbV7Y5+XpR096BxhOxBcmJw2+t3lhili1Xli9Ii5fWDcAa+/8DFvD9ZPoSc8+Rfzx
wmaI6c/Z6jEFbKWI3/HtA+KPL+lbUJ4qFawviy5qyQAfo+DpF1JPbZLXfMa3R+1h/OsG4/Pv8vl53ln6f9o8qc0wvvyOr/0a
Tvl6wJdFnAvGb+h/F1/l5cveCfoh0EsTR38Xn+P3IhBZYHxb/9v4fLTK3/lfMb6/+dv45rf6OBh//Lf509U3nGP8+d/mT3ff
sIjxV9Hfxm98K5+H8dOpef+b+Mm3+FuM//n39R1+5weMf/37+PNvOGWB9S8WBTUW/rv4m38XXz29y6P/k/zld/7/aLe+F77k
5z8qV/Ev47f/XXzq/8v4238ZX/l38VXr38XX6Lu9/slmbfULPf9R/Pa/i//ndfWfDds/z8/z8/w8P8/P8/P8PD/Pz/Pz/Dw/
z8/z8/w8P8/P8/P8PD/Pz/Pz/Dw/z8/z8/w8P8/P8/P8PP8Fj7/3zEwnGz/nPlX8PHh531eSjikIvc9wRdyiFW+U+Qhwwwlx
P1KKe9qpaIwkGfcFpjTq5bhX0Iyu563RwjMhNci3z3SiVBMljCHM6DsaC51WppUG9zfd4TlEXlGft6bhGdZFxDbU316IYQpu
ws9XO2atLSEx2423S/te7uNClI95shXV7aqUK6PLz6JlTWe05vH748Z6SOK7EEsd7ev5J2F/vJvG4+OXM2T6keHe3V9xs/Ze
+nLOTDP08dwQfBsyeiZ9mSwq9GvX0b+9/O/U1Py2gKo8fT6vC+h1pY7yV7v12x0YmYkngbF1IUVW1ih1firttWhz/2V1HxbV
3GHqDVvO8qNMTzPfHpKRSVV2JTIjysSfbFbdn9718/xXP//Xi6vLxZGzdUdsNjvNv6SWKP1yCUa7pfz1H/8lZcBztPrXfBn1
iqQ5vqW78Q26iaONqc3PiWQNnfvoW+eQb7y24qEmh338t1B2fE9YJrQETWZ8n1ghlVEhWVO/VwbZDfcxqA4BOQfhfB97IWab
PNkEeb2Nvv0R8e3UgFEcqVpVjQ78sNR7QCr5FPetU2Bql1CT3cMjf71olpbfE4OsPomlTaqGXu9fDzTX35eYPOtaiZI6eB9F
RRL3Xrm+ow2v9FmnOY/vtw3uI6oH+Rhrpxq9rKFzX33La1AyDfKI10Fb5bhttOK+zYoa1/dckIbO95dZF7moJDZMZcLrpvL9
Dx8k6DVHfjG6m2uBn9FbHxJR8rsI5BHkF3Hf2iMxNberafkKvsf39sD3MtaHcO77m7XkKSENl2/g8NcmngnM81P5+eNOwzp6
kb5fQtvYTzrPM01IN/fSS66yUNOf+0Erq1ZDELpIDztcqna8zLPsFkGp8U4Sd2vZ2o2frxreWDcjliZ7/DyRohKPxbN+GtJK
EzweRyvj1s57fCPlcQWtVPCMel5HxrfIXcv5kbtfJlOj/oYp0Dr94QPv0WiaWjFudad+0cD6lZkKYTTPNJHwspGGUZNvu+y7
vvw411Ymrpcp9hrq1CgI5tvvk4BhWvTsjWo+FafTPNG0M15Pgu3m+l/iMO7qPrVOhkLYtdwo+N2SYV6W5LX93L5sWsJ0ys/3
9j34XiHGZVkVEA/4lQzWlMc9eo5uPtqA73YjWWcT8TqzhiHjGz9XhNWj7TzcI6SutUfad/uNtJrHimIZ1Dx24jx2JjHy6sBl
SI9yeOP9k5/Nzc8ucCN8f62iKacX39cSNP17ZCGGdmw92pHHG5+zydJq1WUxRM5zS4I8Nx7VPJdxnuP7BK0TGf3KY3LNY5Qp
/fvgWU6+Qck6WYZ29HTexg2dbyGwjj1eTz9b8fq72N+nnIdoiHSkfSVuYdvkfYw3cHUs43Su899KJr2aZyBdfUb3IRFjVeha
OumrTggdq7wNsT1IMHy264if26FAJ4R8dSyfWNelbw5c8UGrI/4Kj7tBXPxGzSOaPSx4PtldLDGOShpaVtfFc6wnHUK+d1a4
RzyOQvPWelXTgu8/tC6VQu+v7/O9mpbbcx51WfPNZ1h+dc3fQZj7DOOEh344Gj7qUz3k5zTxq0is2zSyHu9Yecd6Az15uYE+
2KcUvcJ42MZrxts4r7+DfbXifYMN3M2D1vx3sqXDSprFRdV/yzfSaEVkqDUyOcgKfv47/N8N8is/a95LSOGsVOaeOVto3a4C
cozxbQj3yt9wfna7lIBeq9KfUf9/Ugc+fV6KZfXQFpQWqL1SS/pdC4YxQ4CxbMHHsi/9p8/HDHI26vsqgIfn9bg6FfPUgvGH
7/3bZa1S16qGwQ9nsQxF5XpCFeQjnp4us1pnAB784PIiLhnXH7KGYfKzj+d0meO5jw2Db3e1pMAd5QMDMNfE/c0m3muCMuwt
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
+w65fpBAmGDfXE9i+eWbMD0ZqrYxHrQMgTfWpKYb54WyyjIo+xc/huDoDHSCYYUkWkUUR69vtSI3auQUlwtw/TtrtSJibY07
qPpKbS4Z0vNbYEI1a/6r2wnwnV82RNk6ije4JhveQtxwA+3T2kC5+Nr7LWa61kkp1cyhn9hisJs7saFbRdreZctZ7aNQUJH7
KFRbqb9xPuWpVKHHVGxivB7ES+t4N6C/ta8gn1t7ecS17Y4aj26DVLWvnxm/D8BPpkEokGvzvpHqftAYV5U5hH7mUdq3w5S0
ey22L8SYQbn0JVmXinDHZZbhbL3Tg6rK0EzaJvaumDJBwzx0KHjjMl5Hrc2r7cGE5vnjsiL5cMJ01M8clHmEQt7YZmJtLnsg
A8fxeOt3yMNXwbG+tCHQMX9sJHr229UYyi+pXrgMP4ihytEtrHCtW0PatlqbyXZnCK0QBGtqUus45um0PUs22UHUzCa28Zqx
ppseaQPaU9T282Icu6l6hnKS4CSGU9XPbgLIukKK3SLRg5PMFlqdD02Zpym9vO/HcZR0s2uzAXKtqvvjaDmUj/1Uw3bGOhZp
/qV/Ir/tHeT3oiVaPhM536VspwUM+ZKQNPTtFV+rH4J8KYzAYoTTaSVkRac/xX2k/sJP8DelO963Got1NIsI9E2BYX/Asegm
B33qX1ZvOls60Q021g7eNKaj2cS4TZvZj4Lw7eHawvE03yfL3UNb6LSa3b/k33feF+0TH0pxVsqQ1c6R8XvUJK3cz4rKFDYO
uuqo6HBoKJGQb2C4Zn5/KFQ/ZP55/tdqwZyt0+3t5ZLTluSm/FdXFn/Zd88nIjKtVUYXF512P99OtmwRDfQj4+6SFPQqVEC4
Z4ZMYKTIhMyYuN70lTYJyit6PrSY07uL5OBXRFmNIlB2WgFbN5tMOyhpeBEaxQGnP2GIkPkeXn87be5AAbiLVu+0IUViHtze
4SKg+Fz1JFARJA3+VH8dt4OO8BB3UtAvFvhdHLKVwalxDBoPVTjaFaLICtZKMFzrTA3FcO4wLIeKZegrdIGDIY5f0cj7K6jM
lXWt3L2mkHrvbdMPQDU/ei1Mhx4wFMJhOFqZC/QXgKGQMkXr6qCOa9cq5t+pVy0nCnFgyPC3I/nSEZTgngmXRv7Ih6Tk9EHG
WmnqIXebU90AzQ5d0VY5xINyDUmw3A75sDBeaiv0NDJDxj2iGpU+H/QgDIac1b3cDj0myJIhgEo1Qg8NNirvdDysTYoTpSab
oIsotp0GqsKSZJXWHhGP9AtOD0vyBH/NVAkdmeND3YZ77fEtC+kKf5Zi7D/qshVOyLIOjcNmN6NS/GHyemP+Y6hTtfF4nejA
4fww92ZYD0pVRnFmdbRal1oBZW4WFwwH1aGrEH0dBQ0vXF1BRRJdxbrMFkHDrqaS0TC00s/aWEev4edDLCdPo5dOFAh2Jc3K
iwT18LPTaqEhX1jIF2l58mRrf1M8ccP3wpvjHGlXLKHNzL2ecD4Z4oysUTnCB5YlpR9aRfLyvkU+0cqueat4+2CbsYmgbdEj
YA8mmDiI6vSet6TYFlSo2iOcXaalKLU5Xd0GqvRjUIsVf7OB+HbX2veV5egT6GjH7OaMltqhu7w0BLFXpf3tZbF3FTwLB70d
pvG2P48zMtqNxbTZu83FcLvoG+1wt5Ufw7kx1r+8M20paXmH6UTG272uxFZ/99dj1Me7h1NCW3j3cJLRT36XI6FbvFN0ymj7
cbfjgZhcRZjyu8rfd2536rvo8S5nvJuZ0vpOerxDmt9Zzu9g9/hdzOxx9/QU76SW/8/dD/2YiFhs0+1l+5DB7XZT/Ksp4nai
726R3Fe7Xmpzi2tUDUEIl8Pcfuy40JG5KbqqiR/OkqrOpFBB5x3dUBnplMe7n7ZFRdssU3/ohBkKwlFayGtuL6O/uyiDUECG
dm9gS9aCb5n48tKZlai7+kkqna1j01950r0MdM3aT7/o66DHnqrE2mtrEOkg/GmaTaDXpZKxzCsU6FzQWCdngQIT9FsIE3V0
1aoajq7t1TSYtodZLoJ+PlQED3TkFhc24/IkqYZvV/KeDdKy3d1b8yKxDt2ynGfdY+bnW0mLbAo2jtRdfBHYxmkZJ+5VLNGu
HYX1ElkW0aph8H37lirT2lMzyB1++IrDsNODLfdZH4ACzKkH+Zxfxvq0SVC/RjvawN0eee3Dr4GNBQNdBh3II4rAfZy11GTB
aY9CqeNnwYamzcJbBt12o8XszFw34lakreN1g/tNr7Z7EBZ2o9xP57iT/CLUftPYHqM598EWmisUMgrYDx+kkT0OeeE+2JKJ
/twQdmZeifk00Z+bdITan5twGqSksLuk0eha0kS0pG3P2rO6/Xw+94L1K5KlPL+OD8RAPru6xXgiF1GzK/RUXu/RImfngXNJ
GNpz+3492AL93Jp+BWWo4MpcwrgpPyss07rtivX61chcuMnOHiVDO1wM7Ti5wV9hx+nQGS8YmEIsyC1kR/4tuwuDu+RkrZtF
CH7/Cu/CFFTpeknNUM1xibRDW7oANQUP4xBaky4/+AXi5VWErqrAj1z4u5wnrzew5551uQuJOpStMDwgf/O6uMCjUE6w6y0Q
0lkmHLWUog04moVLLPPVAVtRR1u4OW4R+N+COMDrawHiHGbozimfpJt/DN0E6H580qBhh1DfcQJ9L7nPwkS1PXkLtujJuHrb
lWptTa1uE/mbDQx8HxwDazu+AD2vfG5KM8OU5fVc2NxZO0Hy7MPT0uskJJU02esscO5leu4em3gBqvZplOjzXyRbqFo03Xpi
Pe/AoM1x3sEGu9cT/WKKcxtg4+oY5qeg2MmxkIYNoMFQW8F3NXHUR3tZuapyaYyvSDugmySftwba62EZNKx44uHciMUaIOx1
Pi9y0Uwb568EeevdrCPSzsX5PmgPaP+qPU6uYlKejLt1slSUEWTuFKvqwQ93IU2GXpgWdrPcemd/LT/KmUBbbLAfrKNPAfIk
gKeZsKHIE2nVBJoXTgrfucpYv2PJ9yxYUCdydjBslKo2hjesUw++LVVA6xvSwjoKRdwCW3/1mZexoMlDfrhPJsgZyDYnTUef
viX1PVmM6iV21aGWj3L1I2udKtqKAvg9Ah/ZhcxGvMH8o488Gz3agfM1328RA59OW8Vq53iW7xlWVC8jj+MoMlTZOdkS6Zeg
zMasnmfMGveWTsbSAvrhaSxZ++tZPY0TptoX6tcXde9KzB/4Dfp9VGgNkGXbI7pgU3Z2vKjuwyjHgQc5b3FjFeqX6ZocXflS
+Jc5mfNgmXXYe37WQf4BPiijsAVjEPIGtilLjTPuuouVYKWA/BG4Eg/9EOkeyvU45Fkn//c2vjnjVIU2zmPFNrv8wML0hnPb
Fu+7VYHjFvDL6FOfHptKt/DCqi+QWgbL1D+3oO2jX+aRoO7tsW/fJBDwOB+NBw6SnV2BnFVMpwdmBYxhLZWCfD/3u70tUev4
OP/8NCxwvwSOdee137jU45g63atFui5Z0ML+ngruXlW/jhHaDfdXOCt2s0cg3+JQddIQyo79PwT5B3wXJqOS4h4VeWuIKOeH
KBuQH4c2xoU0NsSFd0Mb8/m6X0NZ8nl/UBxHJE3nKJ/KSfDJ87rzMXzJ++sSL4QfLo1mi62R75B/oM9EIDOnRbovc6RJb2vI
wAM3C8ebU9ryNlOl5XM5pYA+4a4ajgvhd23fTw2Qm6A74GGNhbznugPmC7JQxzyf+Su62Xm3nwayE/p4uga5N/SGoCA3mNGi
p9YUXV9M6FspK0CHidxWuv8kp9asgH7eOB/VVlo4XrnXinT1uZ9CGaFsv8yhQcf7ohcd+XwtGCZFBHKtBUYetFFD2PO5SpTV
xUq1x+kQ1wyWtYxno2JV4ISMhzJd6Y/a6BaOPEZx7xny9yxff+FvNyU4vx1Ni1is5WcM3xuL1ovvlru8dnmCAJDPfT4njPqA
7yyrAnQyoF1HeNEOaGYBzRhvk9W+HK+wHU9GC9tDx35rtBjgprVvFy2yOdvzvMP7LspKHPePZE75GoozSu5CpBdKP8ehYm8W
iYFz4kPIV0jXhdwODS6vLxmfm8Qx1ek3zv18NRN1Z62WS5HgXDzmLbozMiB9Pu/YRV0K+okGY7t99BUwYJ39QBPOtKOfM+0Q
dBqZ0Lxu0934SPrXJow9t+mk/fkzz/Lz/LcwwpL57j0R1lMk5a9m8/eN78Vm2i4MuR0QQ+qv86VvRuPnaSUDcUaCMZqztEWX
23Ew0wRlRrqboOGAeueDCCXU2vY99eQPrIDSadBW94kzEKfHrEsMGOIGaTYko/VGVRbTxuYPZ0IpZn1emhlf8YQSEOvhIesc
db5MYoZZ1jpOidmew28CvxF0+C6fj042Qeh2ylWz1+NDoK7a1TK/9faBgOpfB0wDeWvHRbpzyKrBpnweD+KFS4eq7JPdSIdd
87uG3o8EMQN8vanG0m5Oj1SQaITzK8q8V6WX3mQsBYeRSZs/89r/m+d38/K0Wd4eJ6sqrQ4wsdRuib+frJoJ7QQU3M9l2QHj
vb3S5PE8lzvCc4IBjeLpdO4LMm7sxhMTl/31RShdNLfRF9ffDnJM29ro3HC6t6LixGeJ42iCiivbaH7GHo4GFneeIAFXvGqH
h/thMLh5kL+Ai8bm1O1J1ucSV08MUMIaxqKU+abmetZNk+PJZ9mC73V1PF3yMlA8obE1+btY1jfYUcwoLOfqtVtRK5hyv8wg
+9TL+aVhrHIwNgcZ/C8cxmr+wR0hhJ7UhW8J8NcztNK9csVSN6wtOnHk++XOGPQ/4ZutyjZZhL9g4Bj7nikInXaRrVyizOIQ
TMDDxoN37YefsskNUL2o2AaVR2MaELVf6Bg/8rNs9PmanRQdnEVUnWTEZ6GHctsyccZQxrrAYF6uEfvZobcRhLM/pGjsX8+b
/LLqCMXSLHunU8BnWf2t3oN3X0/RHk0McdrMo2VMt0T/w7svM4VRVc/8zRhdQxuC2UlHeGr2gsF7lZAxoW1iEghHm8HShxW7
4k42l4Qq1SsdzNQGzvQFjDWobuk+YQLVRIwn4UxgkGH8EoxDpmA4vH8wLleiR9H06Ln6ekmsYxqaq2U9yz5HRXaY3ZtsWa9A
2NlddIP6OBHdTS+fIUotOiDngc59s1O/Qc5mfQiAcruBkhkXmbkZE3OUwO8EfieZs2E8ghl771Nst6LayQfmhqERBQrfRAal
cw7GgvZF4UyK+yQ7omNEtBCCKZ8oaqpr0y5Y08oD4IdK4YbAkoJh0zijMtekOOk1rB13+EQEA1U6u165gVdPdGjB7Cq3MqIW
11zqW0HHYI2ogl8H9xRne6aBed/Dwwe1zbVqXvqgBEq8v1hNxvQF+p8Lxn7sF9cJL4efHqRDGQ/TgXUVy824sHDP1W7K45KG
wQ+t0DZSbvG9msahdmYYa9a+Ulzuo2xXU+x3Qz6Rdh4IfW5A+jvjYahu/Fn+8CUfj/jkFE5UiqJ1tmU3YfSDrAQ0DjZFVUAd
q+B81q2kEq+VtkmL+rtR5Z+4g0ZdPpP0jrqrtWNSLYna6+r8qOSU+NoNmEiG/kLkwGLaVkV/9Qbfa/sos75qPE8oVnDfqPz4
hvWo42Nl5xcDVyUM+9PTwO3Xzkc9A4yivuHFTweQx6J6xk8rtupTnMOsCvLpY+9yZYurMtiTfdjOYtHlTvLmuMJDGHRz/AE8
y5BnQEFX03EDJ28LPG0yboFRkW7WwzwU9elJUS0J+3JbiJM+hLsknvaKq/PZPCYG35tg8P3RJk0ontrPT0K9VrGVChZ3BcIz
zu4Yj08aqWu+LwFoWnZD3Kcg1/sUpG2vVu61zfcxZGBUw1O9uufKJ8InI9Wbk7n8ZFZ08ikeNwAk2V3qPlYFR9A/p1PeJ9mA
GyDn7DCeCQKeqhrJ+0CZig70k7LvjiziF0MRZTbIx4lMeyqxRY3/4l5newKm2yGS5iuhkdWnN0dbeFdrGJMzGK/PPVorhRsb
6egjT3TsB/V+/WzawYNQWH3Kr0rXl8a7/MAbrOzDmHa06lOdC4pjWlpM8XTOM6Y9l3zC7eCYQ4jn9jTHQYcT5Atb9fOYgbl4
JCaOY0FihodFs33317gCc9oux9520R+vU904LvR8m+x626T6U7wwn4ImN20ax9FkfE6ZyrIVlAr3ibCzY66ufTzRdscq7jx0
7hPSrbRDhNh6l8kaHcc97M9mNMO9ErZ2lBo19op7xI4Xl7gr4XC3wMBs7FvFl30Gz71B6XL1UBY6XRE9IMXXWX3dVvOpLKwU
GZksVQttlYVgGDe0IMSBlh+navcnn4Jy9TEsSVlTC+LbI4yJPGwyqgShB5XzneSq0oZwq/gSmRw0yJ4FStWgjWZxfb6jMXq+
LQ7XgdMQGptTLxCEcSOfP70W66PF8zC9NGAw3G9bfMP/0aP65TFwzD5w2U5abpV6BujDqZdbh1pF1tp5MGB8My2h4VnDzqGV
d5zJlXY2HuagLFa7ERjsRdTajNGbT4w3ePLM46SUBK+/iLZ2OTiAYDFUmbmNNVrZrzgo2MotztK1zwZNa28onLWLh5oYL795
BckWRS+p1yAz5bMaUuTyGY3aE2063qbDSHgIovQIygy/zaLNKhBEc27dG3hCya72oNqRrKHzDh7MjD68yC1+/LYzZlXbGOd9
vBJE67RLZDo/HHdRkKdk9blwOl3cdJS15AiEWH4W+cYpZ3gdestVgwoyH/RaRv9ia9ouZDXD2Vlnq2MeIASUrOtustWJIAOm
qe+M8sI2aqH1y0YqGDS7yFdlBzdSgSwbBDrH9Qar3wTWLytirXrmBzoOL28Kg645wU1O2mckm8LcMbknZXFt8nIpYnDYXAKu
pI23K1zN0J4n2mi7uUP6c2zb/mwtRpYZ5dmyxzdfZULvmLaW7amNg8iHtUXPS20QAf+UNh9o9tp5PgSsKhfkByfncRQi1IPo
yIQm4CcRSXplVuuZktSCG7hZzch6THTl5u2KK9NmOGD74a4IWR8PQ1B68H9l7HgZJ3OblIEKf5Ss9/PkfDFJwY/qt7syX0mY
fltJACX7lg/4EeanngqKVaEHD0HJZDQhOR9puFqgOt7DxMTrAAbcHDxKuz6P34T4c34QCghWdzW3w/TGhanKFfRjC2ebtjkf
YK/iprDHyxC9QNtCe8qPwC9wxQa9TkdmE0xHvUiSa2XhLCTOso/4bQtFu54h42VyuPLeOdfrSsDffLWJXO7cxQ69VuuZ+c6J
m7uowNS8vtT43S9ERE9HGKB57GYm8ekvmsZLh1U4mxdWvZLYWDaGvOtks9qk3i7Rc/e1AhrFSTrWDhvM6MsmxEJ+uH0lW6lf
ejD0UYnhxjzo225C2qslC7auyq8baJ2PK+4KZnI6c6Uq9QqHn8iECqBEps+VqKt8BmNIx8GIu8SADPwk5b6WFytay4vWW2n/
Vdnfbmb965btx2La753frgEw4EThdrYzpIUZjtLJbIfuBBtV1xnB5XpU2sOA6l1U4hVU2kFZB+W91PHoBKJVoKyHIKKQhtQj
/Q2ZEbqpjQWgAqRKGShmYDQsKnrmzVCBEQA9nFWsSzVZ96vQRLcB7i6goz2J6SMyy2gOfZQsCBXrYUnVgnHBx460z0BRNIcK
WZxqt40wLpK5o42oVR/W2mD9x7TFauN9oDvG3LjfrkQrmx6MGKBiR9b+qng5XeE4UYKhpcXWw9Ayenu2QBmn7qPxPANldQx5
85UNrRQmSgbG5ZorIMPDbX35F2f4WV6vSyRJ/QRdcAVyhw0OAhid8y/KSx2PT6N0+erUcr9bfsSguEwtZUWVw7czA5E3VPno
JSYYSH4x1mRHUKALgXLzphfthUJLtxRvSmuXppAfiqSVnmyQg6Q+FOAKbHJlNjmX/+II8vpMvd1qOT/VykJH6onyXy3QEr5O
mbXETvOv/xiDxjfPVFueFJsDF4QtOgp6JZ8jN4DQeKyevUQX7FKe84GvrXgOS1YNW15m6QVGuWJplJc5CFN/var0uzDPDMYb
qZ95JfoSmUrBl8+XxV40TW4Jdz+vtSUM+cWN3RjfnwfDDQ70RdXabDyRzGtcLpZpJnR9mX8D70lZDlmL0cc380m7qaH2+gHf
l094GCVa88kcmWaEpw/VS1mn8qJA+Y1FSdZohe+r+Oh9qH42zw97gccDJYRecwg7uTYJsfw1TYIkBpNJw1kSNeiJNlmXUt+7
vnyMSAtsbXULZTUZJdUBBulKMfS0V2vnlE/Vm1q0KLkgVzQcUyg2uKSN5/b9vA4+9rGgLNVTuhK0rFVtKB4dWGI5CiXgQiYL
6mVk0G5Lr4vSUJmIlywQtEhCAQ111Ce2KJ/bI7QocAlV2zkUFSrNpz4vH5VsiwKDUdEsTyDhzGl2z4AZh46W0AG/eyZmQeQX
LRJ/CtxlRQ5M6l9sN6GrSTfg2wwys70kcQSqBghoshbwfoX67hqtrFYh40qcaoM1BoNl36ndHED8h5srWE5b4+rOjG5lHqyi
Aby/bTogPpWlddnj0s7mRlarWkEIs/thhHFkyWtBGgGExdCBtmvsiQOa/XhXdhX3FD2EBAiNuAlKr91d5ovWYSRcxSmrUA66
ad+vBRaefGXx2YMmqGTAm+Nz3vKRh1d0Wb3aPY94u5viBNt9XJ6eW4yi8QW3G434/4rTnGToW0c1M6wHVBIfuU+gxXnFz2HM
NF+zR/SYkOUgRh6my95VRj5Jw8JhDVVbcveUTyHRhtBPMn4elzK7p9ug4YStoePLW0Pxt6PWbCREeP9FogB9Rs2MRvjdLO13
mvn2MXBOxmjV6b5kCrj0PylBsJruNl1xwRwUydJuTI+m0KZdPuAn/gOrFt9ykOZ3l7dhwwuznOGyNxUabP2cd6ZNFNBUcZIN
5In31tWKGciK8VYrjVYeY9/QjN5ygnegGFjeuVDfgQRtZAydMZa9cPnRiGl0c/I9bjXgCvsYFBcdBvwxP63SZDb8v34M/qee
bGWkXs5H5TUtxJnMZ+3Wp35qshDvAUKf18hfz7pbTSiSWZDOs2uFW5m43U1X0O/DQsT2KWwcuOutYgdUxMKosW+qrZXgJpoK
uhaPp/n55zvelc+IrmCsVZaRmwrda+VaFt7BF660csRPu8P79yJDmX308+ARbp36DpcV+2amPuq9vBwya64LHZRzdNnZWLUE
17gfunv97JL43FYfcr1L/u4kP0qaF1BwOtEjfX25zhx5eDAPn6fz8NQr9SwQ41w8T0/hKfrqEqBath5+sP/JkYFRv3dLTTuf
x+E46ae36STcwjhxSfYh/L+FlpsdQHEBa3q8GULcWX88nMUe6FHpme3G5TSGcHRx2Y3vSd9oLTa1LyTRPTrahqswMoajbY+N
pNSItjQYRu0oqlQ8+a86y0dytEAZ6+9wPIrRTWWBMt0R7tNKFbpNl1wEb11jbRNNM7K9Kgaxk2XOND3fbMjlNvdI4O7WjNDB
VCSKXITEQax+riC/fIT2u58DfU7h9oiLOneidzvQvZu+PCX+HcL16IUVdek9vmetyqwun6VC+bQN4vzjH5dv3moyYrQaFjHt
TkHUz6UM4ebt0ahq5He6ROkvKPHI8MKIaCxEIiJ28l3F1OPsqJOJuyJkQAGTSHBkssNwMwRDWnUxfFVjCKcl4hixfsX4XcQu
YrVOj1hDHFy3FdOOs0Qncj+G7+eIXcQVYicErJaI94htCph2Ec8QGxifWohdxCqGkyliFXGQbyC/cubqpNUfUeJeAatdxEfE
A4p4iniN2MRwyuNPEOuYnlT6J1g8iDWMTxIMVxH71zXkP512dXLrg0HmIFYrxCVimwKmMuIZYiNErCP2EWsYThLEBuIgLyC/
zRToI/UdpH+B9Ee8RmyBGGK0QjxHrGM44dhATDBcE6dQf6VvQvloDvE32F53xA5idTPl9ARsh4C1RAEdcI3YvGL8I4bHiA2M
T3h+FmKKWJOnUP92X4P2uma8/oBXWlMA+mZIX8QfGG6HGbYX4gVig2OC2EOs5hmvP2CKOLiuIL8qBnq0DQHbC7AqIj4gtkPE
LuIlYkPrXjJaIp5yjOGUIPYQq4gJjy8YHWyvJfLLFep7o/0e8cMl1j8G+t0x3IWxGuiNeIfYyjG+jHiO2KBuRShDzBBrGE54
fBNxcE2Rn2OgV8toYflTpAfiErGdI9YRJ4gNxJAf4CFiDTHh6U3EhGOCuGfcsT2TCjdsIn0R29eE0wNwirgfAqYcB4jVPOH1
B0wQB/kC+8ME6NE0LhCf9S4gXxB/ILYxXOU4RWyEC8wPcYhYHQ1BnouIHY7pAvszYorYD+dYv2DRBSHyif0BcTIB+jR9BwaF
HDAVEccYrtM58i9iGzHF+JAfYBVxkM+gvPvD83StYKGHZgmG94wb3oWsyfXdeqBPLneH9LACg2jc3AoNb3TT6oueLMlvgJE1
z5zDQJ1HguRNwDZxFDN5zmafipYrFncZtztuCrFrFXehLLj7GoyrvuJEjay9ifk2bUkGBX3Y0MpBMYyExmUaS+1F1V32V+Q5
RuJWVkOOB3MhR714mZUP/Vo0rdOobalKVp/OKepomGrHZzkMJXTMzaWB+tdBcee4ZwPinzTFioegG2GcWeZ81IfImhFDfUbr
zEFjQS8gfhgsqe4m/0Nd1J367QkvFxUHwZzWkyIGaG9zOuGEMySjPIU0mKsGumuqYANkjWaWu3yVSiYj3KJbNu6exA/Gp6rd
XNYnQqExSpfbhbICHXu2B027Nxk31uc52BtFJT1slK1oo94WjRtcd6c3+7o2Bb4Hwi5Tfmecyfronu3FbBDKgcBMpwQd6ZM+
XLrxTuBoDHaI0+MnOL3vWjutJsvdCV1vM+E4TsNLM1zpFA/vD1esTR+n+6jHxFjjqUm1AnKYlTGUJegYceSD4Y+rL1YhxmIp
Y3zV0bjbl3ZIg/ZBeBrbaAMZPr9HGcrKjP1Yr+82PvY2/ESmPfCXVk6bRg/SMLwHWdwz379O6lOf2HzNy6Crax6f23o3sCcy
k04doRg1Gcar74nTDr1qqOJppmikF9VcC2aqxI17sqNLciPNtsV1+pRhHjuQaA60wUbPLr3/fDXitdLKjxroh0vQNVmS7oXe
13dUWWUJ2ExktUQbzuTx5nSt38BOWg/OXm1fn3rd2nY6zK7ABdUfJwvebggdRRTFvyS52f3lxBu+svChBzeQKFo3I/SlUmpV
rZz+4blEEN+dYXztpZfyGxfp5k/xmxjft9/xvxV2VT011vrpiBA/yP82fn0h4jsB3eCRWD39b+Pz/N/Kb1+E+Gr4t/G5X7E1
fWE3gvja4e/jf8NDzN/4+/zjb3iK+ff/Pv/Zt+3BqQ7xTelv46++xV9j/uaEAhP/uTzf2uuA8Qftv81/k33nhxHyw9/G332L
v5tf7mQw+Py78sy+lScpodOaZ+Pv4n98L58F8e3d38bffbOD9tHzSqp/9oj66F/Fb//L+J/v8vyjfVqNd/7aP4mvRfEzvvqP
JlM3/y6+/y/zH/3L/Gf/Mv/lv8y/0P9d/OrdXvo/iV++y/OP4p+jfxf/5/l5/vVZC0m5WzxXFrqi2FP+AiXv9yNK5wM+CVVK
6xlO2F7T2BQU40xA+YlB8fJW+bBto3wN7vcPSdA++mtCHOfIsi8dyrqWFVFvHf05hqOApt052BnOfdv8OrF173+akFnzOQZy
f5RB/nGt6LT9nBgb/P3EVrEyRnwzOpWfir5fRPFREBNQPBNLCQN1GwhmWNUfUFaIe9wdbrwrCU7IxuxelvUkJ7piefU+Axe9
Ayx+JYXFV/6dCCc/Mz7JR1Jz/AHGj9Ez6IeBE7XqxsRJVVYVzng1pDLflN8TJ5apYPxVy2PdrPtRwTeWbH3TpMzouiYoq24w
2bTEbtabVpNpMO5ud9qtQ5PiAnFEo4Fx+tPAySJSXVyS5AG8rwziOnh8eOC4Ncky/2hB/sfKP6r8zBsSLidd3D+jesPrqJyv
ndpLg9mkks0jV+SsJrQeLjrsc1DX72tDE4qVWXZXoVh7dChexr3DVFsea6VYHSRBWpSR82HUSipONqvPRQQhoaPynj4WEjCt
xSeHedpDBmnlfb6O3Ciy1M6hHv5E2ljPlP1CUKq47KUTV6gazcoya68K93HE6/MJKO65y3BStyM+RaWWMTw7DCdwuz06r/cF
4oLIZs3YZp4ZH7ggZiwzg3LjibuLNuhdhHpTIclWJsW92xYRulWXUXUItBvhvqqGJ2llxSeGcV+vfNRusqHSXY+YbN2tevMK
6D84Ylt2gPa9VGNrtVtpN+12p9jWIrbb8dAkkaZB3seKeP2JtZ8peBaVIBxkemgLfH8wLmAMnUzHfZ64FxPrgpPP537IJ+9P
nuoXPr4G3s7AqNgvgddGbI1nkwloSPFL4olHGfEM2d8c7NZeKGTKndixTfl1Lo39zTH3vI1Nfl2GG+hRLEPZwjBdH8JCagt3
fqE38IlCV2nG6ZKSCb8DK5DQMX1rCP5GcGJcfGNMBf7V9XiqqHzByA5X94MxbGO9NGpt7wPrTHgdnvEI92I8nIteW2jkh1a8
FtCdUfHRtVA47IZjfB+/3nsxf39phPJ/X8d33A/xP/7H/w2e4wXT
```
