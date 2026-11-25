# Adding and localizing the Block column in ROTWK

The **Players → Data** tab has a fifth column after **Status**. It displays **Заблокировать** in Russian and **Block** in English. The existing chat mute checkbox sits under the new heading for each player. The heading uses `APT:PlayerTributeBlock` in `lotr.str`. If the game cannot find that key in its loaded string tables, it displays the standard `MISSING` message.

## Inspect the table in `PlayerTribute.apt`

I extracted `PlayerTribute.apt`, `PlayerTribute.const`, and `PlayerTribute_geometry/59.ru` from `playertribute.big`. I kept the `.apt` and `.const` files in the same directory and decompiled the movie to identify the display records. [pySAGE `sage_apt` documentation](https://github.com/ClementJ18/pySAGE/tree/master/sage_apt)

```bash
python -m sage_apt to-xml PlayerTribute.apt
```

| APT record | What it controls |
| --- | --- |
| Sprite `61`, frame `0` | `StatusPage`, including the headings and the placement of the player table |
| Sprite `52`, frame `1` | All eight instances of the player row |
| Sprite `51`, frame `4` (`_show`) | The visible player row, including the `ChatMute` placement for character `90` |
| Sprite `50`, frame `0` | The four existing row text fields |
| Shape `59` | The table grid drawn by `PlayerTribute_geometry/59.ru` |

## Make room for the new column

I used the existing table width. In `StatusPage` coordinates, the new column boundaries are approximately `0`, `110`, `231`, `274`, `344`, and `441.3` from left to right. I moved each existing heading and its matching row field into its new cell. The numbers below are local APT coordinates from the edited file. `tx` belongs to the `placeobject` record, and `right` belongs to the `edittext` record.

| Column | Heading ID | Heading `tx` | Heading `right` | Row text ID | Row `tx` | Row `right` |
| --- | --- | ---: | ---: | --- | ---: | ---: |
| Player | `53` | `-20.892342` | `127.93333` | `46` | `-240.17984` | `121.88953` |
| Army | `55` | `89.09745` | `138.88771` | `47` | `-132.19138` | `136.88792` |
| Team | `56` | `210.09744` | `60.896049` | `48` | `-12.20419` | `60.896049` |
| Status | `54` | `253.09744` | `87.893166` | `49` | `30.791218` | `87.893166` |

In `PlayerTribute_geometry/59.ru`, I changed the X coordinates of the three existing interior dividers wherever they occur as segment endpoints. The numbers here are local to shape `59`.

| Original X | New X |
| ---: | ---: |
| `118.45` | `105.03878` |
| `277.45` | `226.02586` |
| `337.3` | `269.02127` |

I added this vertical segment to divide **Status** from **Block** across the header and all player rows.

```text
l 339.01379:0:339.01379:229.1
```

## Draw the heading and place the checkbox

1. I cloned the **Status** text field (`54`) into a new read-only `edittext` character (`96`). The new field uses font `14`, centered alignment (`2`), and a font height of `13`. Its bounds are `left=23.9`, `top=-2`, `right=128.67401`, and `bottom=18.75`. I set `multiline` and `wordwrap` to `0` for a one-line heading and left `etvar` empty. The first build embedded `Заблокировать` as the default text. The translated build uses `$PlayerTributeBlock` in that field.
2. I added a `placeobject` for character `96` at depth `23` in sprite `61`, frame `0`, using `HasCharacter|HasMatrix`. Its transform is `tx=323.98999`, `ty=4.05`, `rotm00=0.90`, and `rotm11=0.99981689`. The horizontal scale helps the Russian label fit inside the column.
3. In sprite `51`, frame `4`, I moved the existing `ChatMute` placement for character `90` to `tx=282.27716` and `ty=-2.7`. These are coordinates within the row sprite. Because sprite `52` reuses sprite `51` for all eight rows, this moves the same control and its click target into the center of the new column for every player.
4. I made the layout changes directly in the APT binary. I appended the new text character and placement, updated the movie's character list and frame's item list, then repacked `PlayerTribute.apt` and `PlayerTribute_geometry/59.ru` into `playertribute.big`. Repacking recalculated the offsets and sizes in the BIG directory.

## Add a translation

Add one entry to the existing `lotr.str` used by each language package. Keep the key and translate the text inside the quotes. Save the file in its existing encoding.

**English `lotr.str`**

```text
APT:PlayerTributeBlock
    "Block"
END
```

**Russian `lotr.str`**

```text
APT:PlayerTributeBlock
    "Заблокировать"
END
```

## Connect the heading to `lotr.str`

I located the default text field of `edittext` character `96`. Use the character ID to find the field because `sage_apt` displays the original UTF-8 caption bytes as Latin-1. The diff shows the caption as it appears in the game.

```diff
- <ettext text="Заблокировать"/>
+ <ettext text="$PlayerTributeBlock"/>
```

ROTWK recognizes the leading `$` and adds the `APT:` namespace to an unqualified key. This is the same mechanism the adjacent `$HeaderStatus` field uses. I replaced the null-terminated caption bytes directly in the `.apt` and zero-filled the remaining space in the same slot.

## Reproduce the localization edit

These offsets are for the **pre-localization Block Column build**. Use the build with a visible, hard-coded Russian caption as your input. On other builds, locate the header's default text field by inspecting the decompiled movie.

| Location | File | Offset |
| --- | --- | --- |
| Header `edittext` record | `PlayerTribute.apt` | `0x7934` |
| Default text pointer, at record offset `+0x34` | `PlayerTribute.apt` | `0x7968` |
| Null-terminated caption | `PlayerTribute.apt` | `0x7918` |
| Same caption inside the packed archive | `playertribute.big` | `0x207DC4` |

Save this script as `localize_playertribute.py`. It verifies the input build, writes the token into the original 27-byte caption slot, and verifies the SHA-256 of the resulting `.big`.

```bash
python3 localize_playertribute.py playertribute.big localized/playertribute.big
```

```python
from hashlib import sha256
from pathlib import Path
import sys


INPUT_SHA256 = "6ba45687b855765ca1fb8da17db0da417dccdd00b747ffb284545c7e2db59906"
OUTPUT_SHA256 = "77977d551874adedfa732606f1482c7fee9dca93450191816306b9a8a4f6e0a7"
CAPTION_OFFSET = 0x207DC4
OLD_CAPTION = "Заблокировать".encode("utf-8") + b"\0"
NEW_CAPTION = b"$PlayerTributeBlock\0"


def main():
    if len(sys.argv) != 3:
        raise SystemExit("Usage: localize_playertribute.py INPUT_BIG OUTPUT_BIG")

    source, output = map(Path, sys.argv[1:])
    data = bytearray(source.read_bytes())
    if sha256(data).hexdigest() != INPUT_SHA256:
        raise SystemExit("Expected the pre-localization Block Column build of playertribute.big.")

    caption_end = CAPTION_OFFSET + len(OLD_CAPTION)
    if data[CAPTION_OFFSET:caption_end] != OLD_CAPTION:
        raise SystemExit("The expected Russian caption was not found at the patch offset.")

    data[CAPTION_OFFSET:caption_end] = NEW_CAPTION.ljust(len(OLD_CAPTION), b"\0")
    if sha256(data).hexdigest() != OUTPUT_SHA256:
        raise SystemExit("The patched archive did not match the expected SHA-256.")

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as file:
        file.write(data)


if __name__ == "__main__":
    main()
```

## Verify in ROTWK

Install the generated `playertribute.big` in the same location as the previous version. Start the game with a language package that provides the key and open **Players → Data**. Check that the translated header appears to the right of **Status** and that each player's checkbox sits beneath it and can be clicked there. Repeat with a language package whose loaded strings have no entry for the key to check the `MISSING` behavior.

I checked the positions of all eight checkbox hitboxes against the grid and emulated the engine's lookup for both a present and an absent key. The in-game display still needs to be checked.
