typedef unsigned int Word;
typedef void *Handle;
typedef struct { int left, top, right, bottom; } Rect;
typedef struct {
    int left, top, outer_width, outer_height, client_width, client_height;
} Placement;

#define STDCALL __attribute__((stdcall))
#define THISCALL __attribute__((thiscall))
#define IMPORT(type, address) (*(type *)(address))

enum { WINDOWED = 2, WINDOW_STYLE = 0x10ca0000 };

typedef Handle (STDCALL *ModuleHandle)(const char *);
typedef void *(STDCALL *FindExport)(Handle, const char *);
typedef Word (STDCALL *WindowDpi)(Handle);
typedef int (STDCALL *AdjustForDpi)(Rect *, Word, int, Word, Word);
typedef int (STDCALL *AdjustRect)(Rect *, Word, int);
typedef int (STDCALL *ReadRect)(Handle, Rect *);
typedef int (STDCALL *ClipCursor)(const Rect *);
typedef unsigned char (THISCALL *ChangeMode)(void *, int, int, int, int);

typedef struct { void *set_style; Rect bounds; Handle order; int style; } WindowState;

extern int configure_window(int mode, int *width, int *height, WindowState *previous);
extern void restore_window(Handle window, const WindowState *previous);
extern void apply_cursor(void);

static int original_width, original_height;

static int window_decoration(Handle window, Rect *adjustment, int width, int height)
{
    Handle user32 = IMPORT(ModuleHandle, 0xbd0134)("user32.dll");
    if (user32) {
        FindExport find = IMPORT(FindExport, 0xbd018c);
        WindowDpi get_dpi = (WindowDpi)find(user32, "GetDpiForWindow");
        AdjustForDpi adjust = (AdjustForDpi)find(user32, "AdjustWindowRectExForDpi");
        if (get_dpi && adjust) {
            Word dpi = get_dpi(window);
            if (dpi && adjust(adjustment, WINDOW_STYLE, 0, 0, dpi))
                return 1;
        }
    }
    *adjustment = (Rect){0, 0, width, height};
    return IMPORT(AdjustRect, 0xbd08f8)(adjustment, WINDOW_STYLE, 0);
}

int fit_window(Handle window, const Rect *work, int width, int height, Placement *place)
{
    Rect decoration = {0, 0, width, height};
    if (width <= 0 || height <= 0 || !window_decoration(window, &decoration, width, height))
        return 0;
    int work_width = work->right - work->left;
    int work_height = work->bottom - work->top;
    int frame_width = decoration.right - decoration.left - width;
    int frame_height = decoration.bottom - decoration.top - height;
    int max_width = work_width - frame_width;
    int max_height = work_height - frame_height;
    if (frame_width < 0 || frame_height < 0 || max_width <= 0 || max_height <= 0)
        return 0;

    if (width > max_width || height > max_height) {
        if ((double)max_width * height <= (double)max_height * width) {
            height = (int)((double)max_width * height / width + 0.5);
            width = max_width;
        } else {
            width = (int)((double)max_height * width / height + 0.5);
            height = max_height;
        }
        if (width <= 0 || height <= 0)
            return 0;
    }

    place->client_width = width;
    place->client_height = height;
    place->outer_width = width + frame_width;
    place->outer_height = height + frame_height;
    place->left = work->left + (work_width - place->outer_width) / 2;
    place->top = work->top + (work_height - place->outer_height) / 2;
    return 1;
}

void measure_client(Handle window, int *width, int *height)
{
    Rect client;
    if (IMPORT(ReadRect, 0xbd08b8)(window, &client) &&
        client.right > client.left && client.bottom > client.top) {
        *width = client.right - client.left;
        *height = client.bottom - client.top;
    }
}

unsigned char apply_windowed_resolution(void *display, char *client, int width, int height,
                                         int depth, int windowed)
{
    ChangeMode change = IMPORT(ChangeMode, IMPORT(char *, display) + 0x58);
    if (IMPORT(int, 0xf4d184) != WINDOWED || !windowed || IMPORT(int, 0xf4d188))
        return change(display, width, height, depth, windowed);

    Handle window = IMPORT(Handle, 0xdc3c64);
    int desired_width = width;
    int desired_height = height;
    int confirm = *(unsigned char *)(client + 0xca) != 0;
    WindowState previous;
    if (!window)
        return 0;

    IMPORT(int, 0xf4d188) = 1;
    IMPORT(ClipCursor, 0xbd08cc)(0);
    unsigned char success = 0;
    if (configure_window(WINDOWED, &width, &height, &previous)) {
        IMPORT(const WindowState *, 0xf4d1d0) = &previous;
        success = change(display, width, height, depth, windowed);
        if (success) {
            IMPORT(int, client + 0xcc) = width;
            IMPORT(int, client + 0xd0) = height;
            if (confirm) {
                original_width = IMPORT(int, 0xf4d1cc);
                original_height = IMPORT(int, 0xf4d1c8);
            } else if (original_width > 0 && original_height > 0) {
                desired_width = original_width;
                desired_height = original_height;
            }
            IMPORT(int, 0xf4d1cc) = desired_width;
            IMPORT(int, 0xf4d1c8) = desired_height;
        } else if (IMPORT(const WindowState *, 0xf4d1d0)) {
            restore_window(window, &previous);
        }
        IMPORT(const WindowState *, 0xf4d1d0) = 0;
    }
    IMPORT(int, 0xf4d188) = 0;
    apply_cursor();
    return success;
}
