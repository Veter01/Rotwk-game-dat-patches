# 12. Live display modes and cursor clipping in ROTWK

This change adds **Display Mode** and **Cursor Clipping** to the right column of **Options → Display**. The dropdown switches among exclusive fullscreen, borderless fullscreen, and windowed mode during the current session. **Save** remembers the active mode. **Cancel** restores the last saved mode. Cursor clipping takes effect when the player saves the checkbox.

## Fix the layout in an existing build

Use this procedure if both controls already work and the dropdown extends past the panel. Run the `layout` command from [Build the files](#build-the-files), then replace `apt/options.big` with the generated file.

The final patch changes the translations below in the APT coordinate system. Both sprites share the same origin. The dropdown, its border, and its heading move 100 units left as a group so the dropdown keeps its full width and fits within the panel. The checkbox follows the dropdown's left edge. Its label sits six units lower so the text aligns with the center of the checkbox.

| Element | Frame 0 sprite | Depth | Previous `(tx, ty)` | Final `(tx, ty)` |
| --- | --- | --- | --- | --- |
| `$ETDisplayMode` label | `302`, `ScreenPage` | `7` | `(420, 53)` | `(320, 53)` |
| `Border_DisplayMode` | `302` | `8` | `(420, 80)` | `(320, 80)` |
| `Options::DisplayMode` | `353` | `34` | `(420, 80)` | `(320, 80)` |
| `Options::CursorClipping` | `353` | `35` | `(420, 192)` | `(320, 192)` |
| `$ETCursorClipping` label | `302` | `9` | `(456, 191)` | `(356, 197)` |

For a new installation of the feature, run the `full` command. The builder clones the resolution combo, the resolution border, and the health-bars checkbox. Cloning preserves the APT initialization actions and gadget types. It creates both captions from the resolution edit-text record, keeping references to the language keys. It round-trips `Options.apt` and `Options.const` with `sage_apt` and replaces those members in the BIG.

## Language packs

Add the five entries below to the active `Lotr.str` or `Lotr.csf`. The complete build also produces a standalone `lang/ROTWKDisplay.csf`. The option screen first asks the game's active text table for each key, then looks in the standalone CSF. When neither table defines a key, the native lookup result displays `MISSING` with that key. If an existing language pack says “after restarting” in `APT:ETDisplayMode`, shorten that entry to “Display Mode” in the active pack.

Save this English example as `ROTWKDisplay.str` beside the builder. The same file accepts translations for other languages.

```text
APT:ETDisplayMode
"Display Mode"
END

APT:DisplayModeFullscreen
"Fullscreen"
END

APT:DisplayModeBorderless
"Borderless Fullscreen"
END

APT:DisplayModeWindowed
"Windowed"
END

APT:ETCursorClipping
"Cursor Clipping"
END
```

## Changes in game.dat

The display-mode combo sends the existing `0x4026` selection notification. The options handler stores the selected index, and the game-client update applies it at the end of the tick when the window is foreground and the renderer is ready. The C patch calls the display object's mode setter at vtable offset `0x58`. Its two W3D resize calls use the native `Set_Render_Device` path at `0x005168B0` during a mode switch so Direct3D receives the new windowed flag. If the reset fails, the code restores the previous window geometry and lets the setter retry the previous renderer mode. The selection is then synchronized with the active mode.

| `DisplayMode` | Mode | Window and renderer |
| --- | --- | --- |
| `0` | Fullscreen | Topmost popup with an exclusive Direct3D device |
| `1` | Borderless fullscreen | Popup covering the monitor with a windowed Direct3D device |
| `2` | Windowed | Captioned window sized to the preferred resolution with a windowed Direct3D device |

Borderless mode uses the monitor dimensions. The patch keeps the preferred width and height for the other modes and disables the resolution combo while borderless is active. The options save routine writes `DisplayMode` and `CursorClipping=Yes` or `CursorClipping=No` to the user's `Options.ini`. The renderer startup hook reads those preferences on the next launch. With explicit cursor clipping enabled, the patch passes the foreground window's client rectangle in screen coordinates to `ClipCursor`. It releases the cursor on deactivation, focus loss, or window destruction and checks for minimization when applying clipping.

The builder checks the expected bytes at every hook before writing the new PE file. All addresses are virtual addresses in the supported 32-bit executable.

| Address | Expected bytes | Purpose |
| --- | --- | --- |
| `0x00F23007` | `E8 D3 A0 01 00` | Register the display combo and cursor checkbox. |
| `0x00F2302E` | `E8 89 A1 01 00` | Save the preferences through the options map. |
| `0x00F350C6` | `E8 C8 7F 00 00` | Synchronize native gadget visibility with the selected page. |
| `0x00F3D002` | `E8 99 00 00 00` | Clear gadget references when the options UI is reset or rebuilt. |
| `0x00F3D015` | `E8 8E 00 00 00` | Restore the default display controls. |
| `0x0044657F` | `8B 0D 64 43 DE 00` | Read the saved settings before renderer initialization. |
| `0x004466D3` | `8B 06 8B CE FF 50 54` | Apply clipping once the renderer is ready. |
| `0x0091FCC8` | `38 9F 80 02 00 00` | Skip the normal resolution change while borderless is active. |
| `0x0091F975` | `8D BE B0 02 00 00` | Queue a mode when the dropdown selection changes. |
| `0x0091EC83` | `56 8D 4D E0 E8 67 6A DC FF` | Queue the saved mode on Cancel. |
| `0x006488D3` | `5F 5E 5B C9 C3` | Apply the queued mode at the end of the client update. |
| `0x00442B87` | `E8 C4 3D 0D 00` | Route the requested device mode through the native reset. |
| `0x00442C0D` | `E8 3E 3D 0D 00` | Use the same reset path for the previous mode on failure. |
| `0x00442A44` | `B8 7D 11 B7 00` | Suppress a second reset from focus messages during a switch. |
| `0x004429E2` | `55 8B EC 83 EC 18` | Honor the user's explicit clipping preference. |
| `0x004016F8` | `B8 28 F7 B6 00` | Update clipping on focus and window changes. |

## Build the files

Use Python 3.12, `lxml`, GCC with i386 support, GNU binutils, and the pinned pySAGE checkout shown below. The full build expects the ROTWK 2.01.2614.37001 executable with the required options-page extensions already installed. The executable digest identifies the exact supported input. Use the corresponding options BIG from before the new controls were added. The layout-only command expects a BIG that already contains the controls.

| Full build file | Reference SHA-256 |
| --- | --- |
| Input `game.dat` | `3af4062d360b0662b596666260a9e698a7397140cd77eb689914bcf39fc1590a` |
| Input `options.big` | `198915f365027b841b6c115e98c28cd093f6da48d12e1488be02fc08affc28e3` |
| Output `game.dat` built with GCC 14.2.0 and binutils 2.44 | `1b4c0d8963aedf46e3d939e4057a05e1a55050b7f4e01472320fbd64e90c5112` |
| Output `apt/options.big` from a full build | `a099295aef0ae307b29f4356900456535a3d44c63dbd5c716ac531e9e58f8acc` |

Save the three source listings below beside `ROTWKDisplay.str`. For a layout-only build, save just `build_display.py`.

```bash
git clone https://github.com/ClementJ18/pySAGE.git pySAGE
git -C pySAGE checkout 0a1f1b5d71b1b080008a7e9fff6f997601ec5a7f
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install lxml

# Full build from the compatible executable and menu assets
PYTHONPATH=pySAGE python3 build_display.py full game.dat apt/options.big build/display

# Layout fix for an installation that already has both controls
PYTHONPATH=pySAGE python3 build_display.py layout apt/options.big build/layout/apt/options.big
```

The full build produces `game.dat`, `apt/options.big`, and `lang/ROTWKDisplay.csf` under the output directory. Close ROTWK before copying them to a test installation. The language file is optional when the active pack already defines the five entries. The layout-only build can have a different archive checksum because it appends replacement members to its input BIG.

## Verify in game

1. Open **Options → Display**. Check that the closed and expanded dropdown fit inside the panel and that the cursor clipping label is vertically aligned with the checkbox.
2. Switch through all three modes in the main menu and in a match. In borderless mode, check that the monitor is filled and the resolution dropdown is disabled. Return to windowed mode and check that the preferred size is restored.
3. Preview a mode and select **Cancel**. Preview it again, select **Save**, and relaunch to check persistence.
4. Save cursor clipping enabled and verify that `Alt+Tab` and minimization release the cursor. Save it disabled and verify that the cursor can leave the window.
5. Remove the five keys from the active language pack and start the game without the standalone CSF. Verify that all five entries display the native `MISSING` text. Restore the language file and restart to check the translations.

The APT round-trip and the game hooks were checked in emulation, including all three render-mode requests, reset failure and rollback, saving, cancellation, cursor focus handling, and missing localization keys. The final alignment was checked against the reported screenshot and the encoded APT coordinates. A live Windows run is still pending.

## Build sources

<details>
<summary><code>build_display.py</code></summary>

```python
from argparse import ArgumentParser
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from struct import pack, pack_into, unpack_from
from subprocess import check_output, run
from sys import executable
from tempfile import TemporaryDirectory

from lxml import etree
from sage_patch.utils import allocate_section, apply_byte_patch, call_rel32, file_offset, jmp_rel32
from sage_ini.strings import parse_str

HERE = Path(__file__).resolve().parent
LANGUAGE_SOURCE = HERE / 'ROTWKDisplay.str'
LANGUAGE_FILE = 'lang/ROTWKDisplay.csf'
GAME_SHA256 = '3af4062d360b0662b596666260a9e698a7397140cd77eb689914bcf39fc1590a'
HOOKS = (
    (0xf23007, 'e8d3a00100', 'display_gadget', call_rel32),
    (0xf2302e, 'e889a10100', 'save_display', call_rel32),
    (0xf350c6, 'e8c87f0000', 'sync_page', call_rel32),
    (0xf3d002, 'e899000000', 'clear_gadgets', call_rel32),
    (0xf3d015, 'e88e000000', 'reset_gadgets', call_rel32),
    (0x44657f, '8b0d6443de00', 'on_renderer_start', jmp_rel32),
    (0x4466d3, '8b068bceff5054', 'on_renderer_ready', jmp_rel32),
    (0x91fcc8, '389f80020000', 'on_select_resolution', jmp_rel32),
    (0x91f975, '8dbeb0020000', 'on_display_choice', jmp_rel32),
    (0x91ec83, '568d4de0e8676adcff', 'on_cancel_display', jmp_rel32),
    (0x6488d3, '5f5e5bc9c3', 'on_display_tick', jmp_rel32),
    (0x442b87, 'e8c43d0d00', 'reset_render_mode', call_rel32),
    (0x442c0d, 'e83e3d0d00', 'reset_render_mode', call_rel32),
    (0x442a44, 'b87d11b700', 'on_focus_reset', jmp_rel32),
    (0x4429e2, '558bec83ec18', 'on_clip', jmp_rel32),
    (0x4016f8, 'b828f7b600', 'on_window_message', jmp_rel32),
)
CFLAGS = (
    '-m32', '-Os', '-std=c11', '-ffreestanding', '-fshort-wchar', '-fno-pic',
    '-fno-pie', '-fno-stack-protector', '-fno-asynchronous-unwind-tables',
    '-fno-unwind-tables', '-fno-ident', '-mno-sse', '-mno-mmx', '-Wall', '-Wextra', '-Werror',
)


def patch_game(previous, work):
    if sha256(previous).hexdigest() != GAME_SHA256:
        raise ValueError("Unsupported game.dat SHA-256")
    image = bytearray(previous)
    cfile, asfile = work / 'display.o', work / 'hooks.o'
    script, elf, raw = (work / name for name in ('patch.ld', 'patch.elf', 'patch.bin'))
    run(['gcc', *CFLAGS, '-c', HERE / 'display.c', '-o', cfile], check=True)
    run(['as', '--32', HERE / 'hooks.s', '-o', asfile], check=True)
    script.write_text('''
        SECTIONS {
            . = PATCH_ADDRESS;
            .patch : { *(.text*) *(.rodata*) *(.data*) *(.bss*) BYTE(0) }
            /DISCARD/ : { *(.note*) *(.comment*) }
        }
    ''')
    symbols = {}

    def payload(va):
        run(['ld', '-m', 'elf_i386', '--no-warn-rwx-segments', '-T', script,
             '--defsym', f'PATCH_ADDRESS={va:#x}', '-o', elf, cfile, asfile], check=True)
        run(['objcopy', '-O', 'binary', '-j', '.patch', elf, raw], check=True)
        for row in check_output(['nm', '--defined-only', elf], text=True).splitlines():
            address, _, name = row.split()
            symbols[name] = int(address, 16)
        return raw.read_bytes()

    allocate_section(image, '.dispopt', payload, 0xe0000060)
    for site, encoded, name, branch in HOOKS:
        before = bytes.fromhex(encoded)
        if branch is call_rel32:
            patch = branch(site, symbols[name])
        else:
            patch = branch(site, symbols[name], len(before))
        apply_byte_patch(image, file_offset(image, site), before, patch, name)
    return image, symbols


def big_index(blob):
    assert blob[:4] == b'BIGF' and int.from_bytes(blob[4:8], 'little') == len(blob)
    entries = {}
    entry = 16
    for _ in range(unpack_from('>I', blob, 8)[0]):
        offset, size = unpack_from('>II', blob, entry)
        end = blob.index(0, entry + 8)
        name = blob[entry+8:end].decode('ascii').replace('\\', '/')
        assert name not in entries and offset+size <= len(blob)
        entries[name] = (entry, offset, size)
        entry = end + 1
    return entries


def replace_entries(blob, entries, replacements):
    result = bytearray(blob)
    for name, data in replacements.items():
        header, _, _ = entries[name]
        pack_into('>II', result, header, len(result), len(data))
        result.extend(data)
    pack_into('<I', result, 4, len(result))
    return result


def place(frame, source, depth, character=None, x=None, y=None, name=None):
    copy = deepcopy(source)
    copy.set('depth', str(depth))
    if character is not None:
        copy.set('character', str(character))
    if x is not None:
        copy.set('tx', str(x))
    if y is not None:
        copy.set('ty', str(y))
    if name is not None:
        copy.find('poname').set('name', name)
    assert not frame.xpath(f'./placeobject[@depth="{depth}"]')
    frame.append(copy)
    return copy


def patch_movie(doc):
    root = doc.getroot()
    [screen_ref] = root.xpath(".//poname[@name='ScreenPage']")
    screen_id = screen_ref.getparent().get('character')
    [screen] = root.xpath(f'./sprite[@id="{screen_id}"]/frames/frame[@id="0"]')
    [advanced] = root.xpath('./sprite[@id="353"]/frames/frame[@id="0"]')
    [combo] = advanced.xpath("./placeobject[poname/@name='Options::Resolution']")
    [check] = advanced.xpath("./placeobject[poname/@name='Options::HealthBars']")
    [res_label] = screen.xpath('./placeobject[@character="299"]')
    [res_border] = screen.xpath("./placeobject[poname/@name='Border_Resolution']")
    [source_label] = root.xpath('./edittext[@id="299"]')
    # Match the left column's outer margin while keeping the full combo width.
    column_x = 320

    for key in ('ETDisplayMode', 'ETCursorClipping'):
        label = deepcopy(source_label)
        char_id = max(int(character.get('id')) for character in root if character.get('id')) + 1
        label.set('id', str(char_id))
        label.find('ettext').set('text', '$' + key)
        root.append(label)
        if key == 'ETDisplayMode':
            place(screen, res_label, 7, char_id, column_x, 53)
        else:
            place(screen, res_label, 9, char_id, column_x + 36, 197)

    place(screen, res_border, 8, x=column_x, y=80, name='Border_DisplayMode')
    place(advanced, combo, 34, x=column_x, y=80, name='Options::DisplayMode')
    place(advanced, check, 35, x=column_x, y=192, name='Options::CursorClipping')


def fix_existing_layout(document):
    root = document.getroot()
    [screen_ref] = root.xpath(".//poname[@name='ScreenPage']")
    screen_id = screen_ref.getparent().get('character')
    [screen] = root.xpath(f'./sprite[@id="{screen_id}"]/frames/frame[@id="0"]')
    [gadgets] = root.xpath('./sprite[@id="353"]/frames/frame[@id="0"]')

    for key, x, y in (('ETDisplayMode', 320, 53), ('ETCursorClipping', 356, 197)):
        [label] = root.xpath(f'./edittext[ettext/@text="${key}"]')
        [placement] = screen.xpath(f'./placeobject[@character="{label.get("id")}"]')
        placement.set('tx', str(x))
        placement.set('ty', str(y))

    for frame, name, y in (
        (screen, 'Border_DisplayMode', 80),
        (gadgets, 'Options::DisplayMode', 80),
        (gadgets, 'Options::CursorClipping', 192),
    ):
        [placement] = frame.xpath(f'./placeobject[poname/@name="{name}"]')
        placement.set('tx', '320')
        placement.set('ty', str(y))


def patch_options(blob, work, edit_movie):
    entries = big_index(blob)
    names = ('Options.apt', 'Options.const', 'Options.dat')
    for name in names:
        _, offset, size = entries[name]
        (work / name).write_bytes(blob[offset:offset+size])
    apt = work / 'Options.apt'
    xml = work / 'Options.xml'
    tool = [executable, '-m', 'sage_apt']
    run([*tool, 'to-xml', apt], check=True)
    document = etree.parse(xml)
    edit_movie(document)
    document.write(xml, encoding='utf-8')
    run([*tool, 'to-apt', xml], check=True)
    run([*tool, 'check', apt], check=True)
    replacements = {}
    for name in names:
        _, offset, size = entries[name]
        changed = (work / name).read_bytes()
        if changed != blob[offset:offset+size]:
            replacements[name] = changed
    result = replace_entries(blob, entries, replacements)
    updated = big_index(result)
    assert list(updated) == list(entries)
    for name, (_, offset, size) in updated.items():
        _, old_offset, old_size = entries[name]
        assert bytes(result[offset:offset+size]) == replacements.get(name, blob[old_offset:old_offset+old_size])
    return result


def encode_csf(translations):
    count = len(translations)
    csf = bytearray(pack('<4s5I', b' FSC', 3, count, count, 0, 0))
    for key, text in translations.items():
        key_bytes = key.encode('ascii')
        wide = text.encode('utf-16-le')
        csf.extend(pack('<4sII', b' LBL', 1, len(key_bytes)) + key_bytes)
        csf.extend(pack('<4sI', b' RTS', len(wide) // 2))
        csf.extend(byte ^ 0xff for byte in wide)
    return bytes(csf)


def main():
    parser = ArgumentParser()
    commands = parser.add_subparsers(dest='command', required=True)
    full = commands.add_parser('full')
    full.add_argument('game', type=Path)
    full.add_argument('options', type=Path)
    full.add_argument('output', type=Path)
    layout = commands.add_parser('layout')
    layout.add_argument('options', type=Path)
    layout.add_argument('output', type=Path)
    args = parser.parse_args()

    if args.command == 'layout':
        if args.options.resolve() == args.output.resolve():
            parser.error('Choose a separate output path for the updated BIG.')
        with TemporaryDirectory() as folder:
            movie = patch_options(args.options.read_bytes(), Path(folder), fix_existing_layout)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(movie)
        return

    if ((args.output / 'game.dat').resolve() == args.game.resolve()
            or (args.output / 'apt/options.big').resolve() == args.options.resolve()):
        parser.error('Choose an output directory outside the input installation.')
    translations = parse_str(LANGUAGE_SOURCE.read_text(encoding='utf-8'))
    with TemporaryDirectory() as folder:
        work = Path(folder)
        game, _ = patch_game(args.game.read_bytes(), work)
        movie = patch_options(args.options.read_bytes(), work, patch_movie)
    for name, data in {
        'game.dat': game,
        'apt/options.big': movie,
        LANGUAGE_FILE: encode_csf(translations),
    }.items():
        target = args.output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)


if __name__ == '__main__':
    main()
```

</details>

<details>
<summary><code>display.c</code></summary>

```c
typedef unsigned int u32;
typedef void *Handle;
typedef u32 String;
typedef struct { int left, top, right, bottom; } Rect;
typedef struct { int size; Rect monitor, work; u32 flags; } MonitorInfo;

#define STDCALL __attribute__((stdcall))
#define THISCALL __attribute__((thiscall))
#define PTR(type, at) (*(type *)(at))
#define API(type, at) PTR(type, at)
#define GET_WINDOW() PTR(Handle, 0xdc3c64)
#define GLOBAL() PTR(char *, 0xde4364)
#define CURRENT_PAGE PTR(int, 0xf2767c)
#define OWNER PTR(void *, 0xf27674)
#define DISPLAY() PTR(void *, 0xde4418)
#define METHOD(type, object, slot) PTR(type, PTR(char *, object) + (slot))

typedef int (STDCALL *RectCall)(Handle, Rect *);
typedef int (STDCALL *PointCall)(Handle, int *);
typedef int (STDCALL *SetStyle)(Handle, int, int);
typedef int (STDCALL *GetStyle)(Handle, int);
typedef Handle (STDCALL *FindMonitor)(Handle, u32);
typedef int (STDCALL *ReadMonitor)(Handle, MonitorInfo *);
typedef int (STDCALL *WindowPos)(Handle, Handle, int, int, int, int, u32);
typedef int (STDCALL *ClipCall)(const Rect *);
typedef int (STDCALL *WindowFlagCall)(Handle);
typedef Handle (STDCALL *WindowGetter)(void);
typedef Handle (STDCALL *ModuleGetter)(const char *);
typedef void *(STDCALL *FunctionGetter)(Handle, const char *);
typedef int (STDCALL *GetMetric)(int);
typedef int (STDCALL *AdjustRect)(Rect *, u32, int);
typedef void (THISCALL *StringCtor)(String *, const void *);
typedef void (THISCALL *StringDtor)(String *);
typedef void (THISCALL *StringAssign)(String *, const String *);
typedef void *(THISCALL *MapFind)(void *, const String *);
typedef String *(THISCALL *MapInsert)(void *, const String *);
typedef void (THISCALL *PreferenceCall)(void *);
typedef const String *(THISCALL *FetchText)(void *, const char *, unsigned char *);
typedef unsigned char (THISCALL *LoadTextTable)(void *, const char *, const char *, unsigned char *);
typedef const String *(THISCALL *FindText)(void *, const char *);
typedef void (THISCALL *SetAptText)(void *, const String *, const String *, int);
typedef void (THISCALL *SetWindowFlag)(void *, int);
typedef int (THISCALL *DisplayDimension)(void *);
typedef unsigned char (THISCALL *ChangeDisplayMode)(void *, int, int, int, int);
typedef struct { SetStyle set_style; Rect bounds; Handle order; int style; } WindowState;

enum { FULLSCREEN, BORDERLESS, WINDOWED };
enum { SWP_NOSIZE = 1, SWP_NOMOVE = 2, SWP_NOZORDER = 4, SWP_NOACTIVATE = 16, SWP_FRAMECHANGED = 32 };
enum { SCREEN_PAGE = 1 };

static int active_mode = -1;
static int committed_mode = -1;
static int pending_mode = -1;
static int commit_after_switch = -1;
int switching_mode;
static const WindowState *mode_rollback;
static int preferred_width, preferred_height;
static Rect desktop_bounds;
static Handle desktop_monitor;
static int clip_setting = -1;
static int clip_owned;
static void *mode_gadget;
static void *clip_gadget;
static void *resolution_gadget;
static int resolution_disabled_by_mode;
static void *gadget_owner;
static u32 display_text_table[3];
static int display_text_loaded;
static const String empty_text;

static const char mode_key[] = "DisplayMode";
static const char clip_key[] = "CursorClipping";
static const char *const mode_values[] = {"0", "1", "2"};

static int equal_name(const char *name, const char *match)
{
    return ((int (*)(const char *, const char *))0xa3cf40)(name, match) == 0;
}

static int read_preference(void *map, const char *name)
{
    String key;
    ((StringCtor)0x4374e0)(&key, name);
    char *node = ((MapFind)0x456726)(map, &key);
    ((StringDtor)0x435d50)(&key);
    if (!node || node == PTR(char *, map))
        return -1;
    const char *value = PTR(const char *, node + 0x14);
    if (!value)
        return -1;
    value += 8;
    if (value[0] >= '0' && value[0] <= '2' && value[1] == 0)
        return value[0] - '0';
    if (equal_name(value, "Yes"))
        return 1;
    if (equal_name(value, "No"))
        return 0;
    return -1;
}

static void write_preference(void *map, const char *name, const char *value)
{
    String key, text;
    ((StringCtor)0x4374e0)(&key, name);
    ((StringCtor)0x4374e0)(&text, value);
    String *entry = ((MapInsert)0x602b76)(map, &key);
    ((StringAssign)0x436030)(entry, &text);
    ((StringDtor)0x435d50)(&text);
    ((StringDtor)0x435d50)(&key);
}

static void release_cursor(void)
{
    if (clip_owned || (GET_WINDOW() && API(WindowGetter, 0xbd0850)() == GET_WINDOW()))
        API(ClipCall, 0xbd08cc)(0);
    clip_owned = 0;
}

void apply_cursor(void)
{
    if (clip_setting < 0)
        return;
    Handle window = GET_WINDOW();
    Rect bounds;
    if (!clip_setting || !window || API(WindowGetter, 0xbd0850)() != window ||
        API(WindowFlagCall, 0xbd0800)(window) ||
        !API(RectCall, 0xbd08b8)(window, &bounds) ||
        !API(PointCall, 0xbd089c)(window, &bounds.left) ||
        !API(PointCall, 0xbd089c)(window, &bounds.right) ||
        bounds.right <= bounds.left || bounds.bottom <= bounds.top) {
        release_cursor();
        return;
    }
    if (API(ClipCall, 0xbd08cc)(&bounds))
        clip_owned = 1;
    else
        release_cursor();
}

int use_explicit_clipping(void)
{
    if (clip_setting < 0)
        return 0;
    apply_cursor();
    return 1;
}

void cursor_event(Handle window, u32 event, u32 param)
{
    if (switching_mode || clip_setting < 0 || !window || window != GET_WINDOW())
        return;
    if (event == 2 || event == 8 || (event == 6 && !(param & 0xffff)) ||
        (event == 0x1c && !param)) {
        release_cursor();
        return;
    }
    if (event == 7 || event == 6 || event == 0x1c || event == 0x47)
        apply_cursor();
}

static Handle monitor_bounds(Handle window, Handle user, MonitorInfo *info)
{
    FunctionGetter get = API(FunctionGetter, 0xbd018c);
    FindMonitor monitor = (FindMonitor)get(user, "MonitorFromWindow");
    ReadMonitor read = (ReadMonitor)get(user, "GetMonitorInfoA");
    info->size = sizeof *info;
    Handle current = monitor ? monitor(window, 2) : 0;
    if (current && read && read(current, info))
        return current;
    info->monitor.left = info->monitor.top = 0;
    info->monitor.right = API(GetMetric, 0xbd08f4)(0);
    info->monitor.bottom = API(GetMetric, 0xbd08f4)(1);
    info->work = info->monitor;
    return 0;
}

static void restore_window(Handle window, const WindowState *state)
{
    const Rect *bounds = &state->bounds;
    state->set_style(window, -16, state->style);
    API(WindowPos, 0xbd08ec)(window, state->order, bounds->left, bounds->top,
                            bounds->right - bounds->left, bounds->bottom - bounds->top,
                            SWP_NOACTIVATE | SWP_FRAMECHANGED);
}

static int configure_window(int mode, int *render_width, int *render_height, WindowState *previous)
{
    Handle window = GET_WINDOW();
    Handle user = API(ModuleGetter, 0xbd0134)("user32.dll");
    if (!window || !user)
        return 0;
    SetStyle set_style = (SetStyle)API(FunctionGetter, 0xbd018c)(user, "SetWindowLongA");
    if (!set_style)
        return 0;

    if (previous) {
        if (!API(RectCall, 0xbd08b0)(window, &previous->bounds))
            return 0;
        previous->set_style = set_style;
        previous->order = API(GetStyle, 0xbd07f8)(window, -20) & 8 ? (Handle)-1 : (Handle)-2;
    }

    MonitorInfo dimensions;
    Handle monitor = monitor_bounds(window, user, &dimensions);
    Rect area = dimensions.monitor;
    if (mode == BORDERLESS && active_mode == FULLSCREEN && monitor && monitor == desktop_monitor)
        area = desktop_bounds;
    if (active_mode != FULLSCREEN || !desktop_monitor) {
        desktop_monitor = monitor;
        desktop_bounds = dimensions.monitor;
    }
    int width = mode == BORDERLESS ? area.right - area.left : *render_width;
    int height = mode == BORDERLESS ? area.bottom - area.top : *render_height;
    if (width <= 0 || height <= 0)
        return 0;
    int left = area.left;
    int top = area.top;
    int content_width = width;
    int content_height = height;
    u32 style = 0x90000000;
    if (mode == WINDOWED) {
        style = 0x10ca0000;
        Rect outer = {0, 0, width, height};
        if (!API(AdjustRect, 0xbd08f8)(&outer, style, 0))
            return 0;
        width = outer.right - outer.left;
        height = outer.bottom - outer.top;
        area = dimensions.work;
        int margin_x = (area.right - area.left - width) / 2;
        int margin_y = (area.bottom - area.top - height) / 2;
        left = area.left + (margin_x > 0 ? margin_x : 0);
        top = area.top + (margin_y > 0 ? margin_y : 0);
    }
    int previous_style = set_style(window, -16, style);
    if (!previous_style)
        return 0;
    if (previous)
        previous->style = previous_style;

    u32 flags = SWP_NOACTIVATE | SWP_FRAMECHANGED;
    Handle z_order = (Handle)-2;  /* HWND_NOTOPMOST */
    if (mode == FULLSCREEN) {
        if (!previous)
            flags |= SWP_NOSIZE;
        z_order = (Handle)-1;    /* HWND_TOPMOST */
    }
    if (!API(WindowPos, 0xbd08ec)(window, z_order, left, top, width, height, flags)) {
        if (previous) {
            restore_window(window, previous);
        } else {
            set_style(window, -16, previous_style);
            API(WindowPos, 0xbd08ec)(window, 0, 0, 0, 0, 0,
                                   SWP_NOSIZE | SWP_NOMOVE | SWP_NOZORDER | flags);
        }
        return 0;
    }
    *render_width = content_width;
    *render_height = content_height;
    return 1;
}

static void record_mode(int mode, int width, int height)
{
    PTR(int, GLOBAL() + 0x30) = width;
    PTR(int, GLOBAL() + 0x34) = height;
    PTR(unsigned char, GLOBAL() + 0x2c) = mode != FULLSCREEN;
    PTR(unsigned char, 0xdc3c68) = mode != FULLSCREEN;
    active_mode = mode;
}

void start_display(void)
{
    if (!GLOBAL())
        return;
    char prefs[32];
    ((PreferenceCall)0x6e56f3)(prefs);
    int saved = read_preference(prefs + 4, mode_key);
    int clipping = read_preference(prefs + 4, clip_key);
    ((PreferenceCall)0x6e562f)(prefs);
    clip_setting = (unsigned)clipping <= 1 ? clipping : -1;

    preferred_width = PTR(int, GLOBAL() + 0x30);
    preferred_height = PTR(int, GLOBAL() + 0x34);
    Handle window = GET_WINDOW();
    Handle user = API(ModuleGetter, 0xbd0134)("user32.dll");
    if (window && user) {
        MonitorInfo dimensions;
        desktop_monitor = monitor_bounds(window, user, &dimensions);
        desktop_bounds = dimensions.monitor;
    }
    active_mode = PTR(unsigned char, GLOBAL() + 0x2c) ? WINDOWED : FULLSCREEN;
    if ((unsigned)saved <= WINDOWED) {
        int width = preferred_width, height = preferred_height;
        if (configure_window(saved, &width, &height, 0))
            record_mode(saved, width, height);
    }
    committed_mode = active_mode;
}

static void set_combo(void *gadget, int index)
{
    ((void (*)(void *, int, int))0x72437d)(gadget, index, 0);
}

static void set_check(void *gadget, int on)
{
    ((void (*)(void *, int))0x729534)(gadget, on);
}

static int combo_mode(void *gadget)
{
    int result = -1;
    ((void (*)(void *, int *))0x724337)(gadget, &result);
    return result;
}

void display_choice(void *owner, void *gadget)
{
    if (!mode_gadget || gadget != mode_gadget || owner != gadget_owner ||
        owner != OWNER || CURRENT_PAGE != SCREEN_PAGE || switching_mode)
        return;
    int mode = combo_mode(gadget);
    if ((unsigned)mode <= WINDOWED)
        pending_mode = mode;
}

void cancel_display(void *owner)
{
    if (owner == gadget_owner && owner == OWNER) {
        pending_mode = committed_mode;
        commit_after_switch = -1;
        if (mode_gadget && committed_mode >= 0)
            set_combo(mode_gadget, committed_mode);
    }
}

unsigned char reset_render_mode(int width, int height, int depth, int windowed, int resize)
{
    if (!switching_mode)
        return ((unsigned char (*)(int, int, int, int, int))0x516950)(
            width, height, depth, windowed, resize);
    /* W3D's ordinary resize path does not update D3D's Windowed parameter. */
    unsigned char success = ((unsigned char (*)(int, int, int, int, int, int, int, int))0x5168b0)(
        -1, width, height, depth, windowed, 0, 1, 1);
    if (!success && mode_rollback) {
        /* The W3D method next tries its previous device mode. */
        restore_window(GET_WINDOW(), mode_rollback);
        mode_rollback = 0;
    }
    return success;
}

static void refresh_layout(void)
{
    void *header = PTR(void *, 0xde3b64);
    void *mouse = PTR(void *, 0xde36e0);
    void *hud = PTR(void *, 0xde4830);
    if (header)
        ((PreferenceCall)0x6015ad)(header);
    if (mouse)
        ((PreferenceCall)0x63f3bf)(mouse);
    ((void (*)(void))0x8153a8)();
    if (hud)
        METHOD(PreferenceCall, hud, 0x1b0)(hud);
}

static void update_resolution_control(void)
{
    if (!resolution_gadget)
        return;
    if (active_mode == BORDERLESS && (PTR(u32, resolution_gadget + 8) & 8)) {
        resolution_disabled_by_mode = 1;
        ((SetWindowFlag)0x7154b3)(resolution_gadget, 0);
    } else if (active_mode != BORDERLESS && resolution_disabled_by_mode) {
        resolution_disabled_by_mode = 0;
        ((SetWindowFlag)0x7154b3)(resolution_gadget, 1);
    }
}

static void commit_mode(void *map, int mode)
{
    write_preference(map, mode_key, mode_values[mode]);
    committed_mode = mode;
}

void apply_pending_mode(void)
{
    if (pending_mode < 0 || switching_mode)
        return;
    void *display = DISPLAY();
    Handle window = GET_WINDOW();
    if (!GLOBAL() || !display || !window || !PTR(unsigned char, 0xdd1e14) ||
        API(WindowGetter, 0xbd0850)() != window || API(WindowFlagCall, 0xbd0800)(window))
        return;
    int target = pending_mode;
    pending_mode = -1;
    if (target != active_mode) {
        int old_width = METHOD(DisplayDimension, display, 0x40)(display);
        int old_height = METHOD(DisplayDimension, display, 0x44)(display);
        int depth = METHOD(DisplayDimension, display, 0x4c)(display);
        if (active_mode != BORDERLESS) {
            preferred_width = old_width;
            preferred_height = old_height;
        }
        int width = preferred_width, height = preferred_height;
        WindowState previous;
        switching_mode = 1;
        release_cursor();
        if (configure_window(target, &width, &height, &previous)) {
            mode_rollback = &previous;
            int success = METHOD(ChangeDisplayMode, display, 0x58)(display, width, height, depth,
                                                                   target != FULLSCREEN);
            if (success) {
                METHOD(SetWindowFlag, display, 0x50)(display, target != FULLSCREEN);
                record_mode(target, width, height);
                if (width != old_width || height != old_height)
                    refresh_layout();
            } else if (mode_rollback) {
                restore_window(window, &previous);
            }
            mode_rollback = 0;
        }
        switching_mode = 0;
        if (clip_setting >= 0)
            apply_cursor();
        else if (active_mode == FULLSCREEN)
            ((void (*)(void))0x4429e2)();
        if (mode_gadget)
            set_combo(mode_gadget, active_mode);
        update_resolution_control();
    }
    if (commit_after_switch >= 0) {
        int requested = commit_after_switch;
        commit_after_switch = -1;
        if (target == active_mode && target == requested) {
            char prefs[32];
            ((PreferenceCall)0x6e56f3)(prefs);
            commit_mode(prefs + 4, active_mode);
            ((PreferenceCall)0x7b274c)(prefs);
            ((PreferenceCall)0x6e562f)(prefs);
        }
    }
}

static const String *localized_text(const char *key)
{
    void *game_text = PTR(void *, 0xde4b04);
    if (!game_text)
        return &empty_text;

    unsigned char found = 0;
    const String *text = ((FetchText)0x6e7a63)(game_text, key, &found);
    if (found)
        return text;

    if (!display_text_loaded) {
        display_text_loaded = 1;
        ((LoadTextTable)0x6e7d9e)(display_text_table, 0, "lang\\ROTWKDisplay.csf", 0);
    }
    if (display_text_table[0]) {
        const String *translation = ((FindText)0x6e7903)(display_text_table, key);
        if (translation)
            return translation;
    }
    return text;
}

static void label(const char *name)
{
    void *manager = PTR(void *, 0xde3f0c);
    if (!manager)
        return;
    String key;
    ((StringCtor)0x4374e0)(&key, name);
    ((SetAptText)0x624ffd)(manager, &key, localized_text(name), 0);
    ((StringDtor)0x435d50)(&key);
}

void sync_page(void)
{
    ((void (*)(void))0xf3d093)();
    int hidden = CURRENT_PAGE != SCREEN_PAGE;
    if (mode_gadget) {
        if (hidden)
            ((void (*)(void *))0x724411)(mode_gadget);
        ((SetWindowFlag)0x71552b)(mode_gadget, hidden);
    }
    if (clip_gadget)
        ((SetWindowFlag)0x71552b)(clip_gadget, hidden);
    if (!hidden)
        update_resolution_control();
}

void clear_gadgets(void)
{
    ((void (*)(void))0xf3d0a0)();
    mode_gadget = clip_gadget = resolution_gadget = gadget_owner = 0;
    resolution_disabled_by_mode = 0;
}

void reset_gadgets(void)
{
    ((void (*)(void))0xf3d0a8)();
    if (mode_gadget) {
        set_combo(mode_gadget, FULLSCREEN);
        pending_mode = FULLSCREEN;
    }
    if (clip_gadget)
        set_check(clip_gadget, 1);
}

int display_gadget(void *owner, const char *name, void *gadget)
{
    int stock = ((int (*)(void *, const char *, void *))0xf3d0df)(owner, name, gadget);
    if (gadget_owner != owner) {
        gadget_owner = owner;
        mode_gadget = clip_gadget = resolution_gadget = 0;
        resolution_disabled_by_mode = 0;
    }
    if (equal_name(name, "Options::Resolution")) {
        if (resolution_gadget != gadget)
            resolution_disabled_by_mode = 0;
        resolution_gadget = gadget;
        update_resolution_control();
    }
    if (stock)
        return stock;
    if (equal_name(name, "Options::DisplayMode")) {
        static const char *const modes[] = {
            "APT:DisplayModeFullscreen", "APT:DisplayModeBorderless", "APT:DisplayModeWindowed",
        };
        mode_gadget = gadget;
        for (int i = 0; i < 3; ++i) {
            String value = 0;
            ((StringAssign)0x436a90)(&value, localized_text(modes[i]));
            /* The combo takes a UnicodeString by value and destroys its copy. */
            ((int (*)(void *, String, int))0x724811)(gadget, value, -1);
        }
        ((void (*)(void *, int))0x72414f)(gadget, 3);
        set_combo(gadget, pending_mode >= 0 ? pending_mode : active_mode >= 0 ? active_mode : FULLSCREEN);
        label("APT:ETDisplayMode");
    } else if (equal_name(name, "Options::CursorClipping")) {
        clip_gadget = gadget;
        set_check(gadget, clip_setting >= 0 ? clip_setting : active_mode == FULLSCREEN);
        label("APT:ETCursorClipping");
    } else {
        return 0;
    }
    sync_page();
    return 1;
}

void save_display(void *owner, void *map)
{
    ((void (*)(void *, void *))0xf3d1bc)(owner, map);
    if (!map || gadget_owner != owner || OWNER != owner)
        return;
    if (mode_gadget) {
        int mode = combo_mode(mode_gadget);
        if ((unsigned)mode <= WINDOWED) {
            if (mode == active_mode) {
                commit_mode(map, mode);
                pending_mode = -1;
                commit_after_switch = -1;
            } else {
                pending_mode = mode;
                commit_after_switch = mode;
            }
        }
    }
    if (clip_gadget) {
        int on = ((unsigned char (*)(void *))0x729579)(clip_gadget) != 0;
        int was_native = clip_setting < 0;
        write_preference(map, clip_key, on ? "Yes" : "No");
        clip_setting = on;
        if (was_native && !on && GET_WINDOW())
            API(ClipCall, 0xbd08cc)(0);
        apply_cursor();
    }
}

int borderless_active(void)
{
    return active_mode == BORDERLESS;
}
```

</details>

<details>
<summary><code>hooks.s</code></summary>

```asm
.intel_syntax noprefix
.code32
.text

.global on_renderer_start, on_renderer_ready, on_select_resolution, on_clip, on_window_message
.global on_display_choice, on_cancel_display, on_display_tick, on_focus_reset

on_renderer_start:
    pushf
    pusha
    call start_display
    popa
    popf
    mov ecx, [0xde4364]
    jmp 0x446585

on_renderer_ready:
    pushf
    pusha
    call apply_cursor
    popa
    popf
    mov eax, [esi]
    mov ecx, esi
    call [eax+0x54]
    jmp 0x4466da

on_select_resolution:
    pushf
    pusha
    call borderless_active
    test eax, eax
    jnz .Lskip_resolution
    popa
    popf
    cmp byte ptr [edi+0x280], bl
    jmp 0x91fcce
.Lskip_resolution:
    popa
    popf
    mov [ebp-4], ebx
    jmp 0x91fd8b

on_display_choice:
    pushf
    pusha
    push ebx
    push esi
    call display_choice
    add esp, 8
    popa
    popf
    lea edi, [esi+0x2b0]
    jmp 0x91f97b

on_cancel_display:
    pushf
    pusha
    push ecx
    call cancel_display
    add esp, 4
    popa
    popf
    push esi
    lea ecx, [ebp-0x20]
    call 0x6e56f3
    jmp 0x91ec8c

on_display_tick:
    pushf
    pusha
    call apply_pending_mode
    popa
    popf
    pop edi
    pop esi
    pop ebx
    leave
    ret

on_focus_reset:
    cmp dword ptr [switching_mode], 0
    jne .Lfocus_done
    mov eax, 0xb7117d
    jmp 0x442a49
.Lfocus_done:
    ret

on_clip:
    call use_explicit_clipping
    test eax, eax
    jnz .Lclip_done
    push ebp
    mov ebp, esp
    sub esp, 0x18
    jmp 0x4429e8
.Lclip_done:
    ret

on_window_message:
    pushf
    pusha
    push dword ptr [esp+48]
    push dword ptr [esp+48]
    push dword ptr [esp+48]
    call cursor_event
    add esp, 12
    popa
    popf
    mov eax, 0xb6f728
    jmp 0x4016fd
```

</details>
