typedef void *Handle;
typedef unsigned int UInt;
typedef struct { int width, height; } Resolution;
typedef struct { Resolution size; UInt refresh_rate, format; } DisplayMode;

#define STDCALL __attribute__((stdcall))
#define READ(type, address) (*(type *)(address))
#define METHOD(type, object, slot) READ(type, READ(char *, object) + (slot))

typedef UInt (STDCALL *ModeCount)(void *, UInt, UInt);
typedef int (STDCALL *EnumAdapterMode)(void *, UInt, UInt, UInt, DisplayMode *);
typedef int (STDCALL *AdapterDisplayMode)(void *, UInt, DisplayMode *);
typedef Handle (STDCALL *ModuleHandle)(const char *);
typedef void *(STDCALL *FindExport)(Handle, const char *);

typedef struct {
    char device_name[32];
    unsigned short spec_version, driver_version, size, driver_extra;
    char fields_before_display[64];
    UInt bits_per_pixel;
    Resolution display;
    char fields_after_display[40];
} Win32DisplayMode;

_Static_assert(sizeof(Win32DisplayMode) == 156, "DEVMODEA size");
_Static_assert(__builtin_offsetof(Win32DisplayMode, size) == 36, "DEVMODEA dmSize");
_Static_assert(__builtin_offsetof(Win32DisplayMode, display) == 108, "DEVMODEA display dimensions");

typedef int (STDCALL *EnumDisplaySettings)(const char *, UInt, Win32DisplayMode *);

static int same_size(Resolution a, Resolution b)
{
    return a.width == b.width && a.height == b.height;
}

static int absolute(int value)
{
    return value < 0 ? -value : value;
}

static int distance(Resolution a, Resolution b)
{
    return absolute(a.width - b.width) + absolute(a.height - b.height);
}

static void consider_mode(Resolution requested, Resolution desktop, Resolution mode,
                          Resolution *best, int *best_score)
{
    if (mode.width <= 0 || mode.height <= 0)
        return;
    int score = same_size(mode, requested) ? 0 : 1 + distance(mode, desktop);
    if (score < *best_score) {
        *best = mode;
        *best_score = score;
    }
}

static Resolution runtime_resolution(void *d3d, Resolution requested, int depth)
{
    enum { X8R8G8B8 = 22, R5G6B5 = 23, X1R5G5B5 = 24 };
    int adapter = READ(int, 0xd9b088);
    if (adapter < 0)
        adapter = 0;
    DisplayMode current;
    Resolution desktop = requested;
    if (METHOD(AdapterDisplayMode, d3d, 0x20)(d3d, adapter, &current) == 0)
        desktop = current.size;
    UInt formats[] = { X8R8G8B8, 0 };
    if (depth == 16) {
        formats[0] = R5G6B5;
        formats[1] = X1R5G5B5;
    }

    Resolution best = {0, 0};
    int best_score = 0x7fffffff;
    for (UInt f = 0; f < sizeof(formats) / sizeof(formats[0]) && formats[f]; ++f) {
        UInt format = formats[f];
        UInt count = METHOD(ModeCount, d3d, 0x18)(d3d, adapter, format);
        for (UInt i = 0; i < count; ++i) {
            DisplayMode mode;
            if (METHOD(EnumAdapterMode, d3d, 0x1c)(d3d, adapter, format, i, &mode) == 0) {
                consider_mode(requested, desktop, mode.size, &best, &best_score);
                if (best_score == 0)
                    return best;
            }
        }
    }
    return best;
}

static Resolution startup_resolution(Resolution requested)
{
    Handle user32 = READ(ModuleHandle, 0xbd0134)("user32.dll");
    EnumDisplaySettings enumerate = user32 ?
        (EnumDisplaySettings)READ(FindExport, 0xbd018c)(user32, "EnumDisplaySettingsA") : 0;
    if (!enumerate)
        return requested;

    Win32DisplayMode mode = {0};
    mode.size = sizeof(mode);
    Resolution desktop = requested;
    /* The engine opens adapter 0 at startup. Use the primary display until D3D is ready. */
    if (enumerate(0, (UInt)-1, &mode))
        desktop = mode.display;

    Resolution best = {0, 0};
    int best_score = 0x7fffffff;
    for (UInt index = 0; best_score != 0; ++index) {
        mode.size = sizeof(mode);
        mode.driver_extra = 0;
        if (!enumerate(0, index, &mode))
            break;
        if (mode.bits_per_pixel >= 16)
            consider_mode(requested, desktop, mode.display, &best, &best_score);
    }
    return best.width ? best : desktop;
}

void choose_fullscreen_size(int *width, int *height, int depth)
{
    Resolution requested = {*width, *height};
    void *d3d = READ(void *, 0xdd3470);
    Resolution chosen = d3d ? runtime_resolution(d3d, requested, depth) :
                             startup_resolution(requested);
    if (chosen.width > 0 && chosen.height > 0) {
        *width = chosen.width;
        *height = chosen.height;
    }
}
