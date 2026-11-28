typedef void *Handle;
typedef unsigned int Word;
typedef struct { int left, top, right, bottom; } Rect;

#define STDCALL __attribute__((stdcall))
#define THISCALL __attribute__((thiscall))
#define PTR(type, address) (*(type *)(address))
#define METHOD(type, object, slot) PTR(type, PTR(char *, object) + (slot))

enum {
    WINDOWED = 2,
    WM_DESTROY = 2, WM_SIZE = 5, WM_CANCELMODE = 0x1f,
    WM_ENTERSIZEMOVE = 0x231, WM_EXITSIZEMOVE = 0x232,
    SIZE_RESTORED = 0, SIZE_MAXIMIZED = 2
};

typedef Handle (STDCALL *ModuleHandle)(const char *);
typedef void *(STDCALL *FindExport)(Handle, const char *);
typedef int (STDCALL *WindowRect)(Handle, Rect *);
typedef int (STDCALL *WindowLong)(Handle, int);
typedef int (STDCALL *SetStyle)(Handle, int, int);
typedef int (STDCALL *IsIconic)(Handle);
typedef Handle (STDCALL *GetForeground)(void);
typedef int (THISCALL *GetDimension)(void *);
typedef unsigned char (THISCALL *SetMode)(void *, int, int, int, int);
typedef void (THISCALL *NoArg)(void *);
typedef struct { SetStyle set_style; Rect bounds; Handle order; int style; } WindowState;

extern void stock_cursor_event(Handle window, Word event, Word parameter);
extern int STDCALL stock_window_clip(const Rect *bounds);
extern void apply_cursor(void);
extern void release_cursor(void);
extern void stock_apply_pending_mode(void);
extern void restore_window(Handle window, const WindowState *previous);

int moving_window;
static int resize_pending;
static Handle tracked_window;
static Rect last_bounds;
static int last_width, last_height;

void forget_window_control(void *window)
{
    if (PTR(void *, 0xf4d1ac) == window)
        PTR(void *, 0xf4d1ac) = 0;
    if (PTR(void *, 0xf4d1a8) == window)
        PTR(void *, 0xf4d1a8) = 0;
    if (PTR(void *, 0xf4d1a4) == window) {
        PTR(void *, 0xf4d1a4) = 0;
        PTR(int, 0xf4d1a0) = 0;
    }
}

void discard_detached_controls(void)
{
    void *mode = PTR(void *, 0xf4d1ac);
    void *clipping = PTR(void *, 0xf4d1a8);
    void *resolution = PTR(void *, 0xf4d1a4);
    if (!mode && !clipping && !resolution)
        return;

    char *manager = PTR(char *, 0xde495c);
    char *window = manager ? PTR(char *, manager + 0x0c) : 0;
    while (window && (mode || clipping || resolution)) {
        if (!(PTR(unsigned, window + 8) & 0x800)) {
            if (window == mode)
                mode = 0;
            if (window == clipping)
                clipping = 0;
            if (window == resolution)
                resolution = 0;
        }
        char *child = PTR(char *, window + 0x204);
        if (child) {
            window = child;
        } else {
            while (!PTR(char *, window + 0x1f8) && PTR(char *, window + 0x200))
                window = PTR(char *, window + 0x200);
            window = PTR(char *, window + 0x1f8);
        }
    }
    if (mode)
        forget_window_control(mode);
    if (clipping)
        forget_window_control(clipping);
    if (resolution)
        forget_window_control(resolution);
}

int STDCALL clip_resize_window(const Rect *client)
{
    Rect frame;
    Handle window = PTR(Handle, 0xdc3c64);
    if (PTR(int, 0xf4d184) == WINDOWED && window &&
        PTR(WindowRect, 0xbd08b0)(window, &frame) &&
        frame.left <= client->left && frame.top <= client->top &&
        frame.right >= client->right && frame.bottom >= client->bottom)
        return stock_window_clip(&frame);
    return stock_window_clip(client);
}

void window_resize_message(Handle window, Word event, Word parameter)
{
    if (window && window == PTR(Handle, 0xdc3c64)) {
        if (event == WM_DESTROY) {
            moving_window = 0;
            resize_pending = 0;
            tracked_window = 0;
        } else if (PTR(int, 0xf4d184) == WINDOWED && !PTR(int, 0xf4d188)) {
            if (event == WM_ENTERSIZEMOVE) {
                moving_window = 1;
                release_cursor();
            } else if (event == WM_EXITSIZEMOVE || (event == WM_CANCELMODE && moving_window)) {
                moving_window = 0;
                resize_pending = 1;
            } else if (event == WM_SIZE && (parameter == SIZE_RESTORED || parameter == SIZE_MAXIMIZED)) {
                resize_pending = 1;
            }
        }
    }
    stock_cursor_event(window, event, parameter);
}

static void remember_bounds(Handle window, int width, int height)
{
    if (PTR(WindowRect, 0xbd08b0)(window, &last_bounds)) {
        tracked_window = window;
        last_width = width;
        last_height = height;
    }
}

static int previous_window(Handle window, int width, int height, WindowState *state)
{
    if (tracked_window != window || last_width != width || last_height != height)
        return 0;
    Handle user32 = PTR(ModuleHandle, 0xbd0134)("user32.dll");
    if (!user32)
        return 0;
    state->set_style = (SetStyle)PTR(FindExport, 0xbd018c)(user32, "SetWindowLongA");
    if (!state->set_style)
        return 0;
    WindowLong attributes = PTR(WindowLong, 0xbd07f8);
    state->order = (attributes(window, -20) & 8) ? (Handle)-1 : (Handle)-2;
    state->style = attributes(window, -16);
    state->bounds = last_bounds;
    return 1;
}

static void refresh_window_ui(void)
{
    void *header = PTR(void *, 0xde3b64);
    void *mouse = PTR(void *, 0xde36e0);
    if (header)
        ((NoArg)0x6015ad)(header);
    if (mouse)
        ((NoArg)0x63f3bf)(mouse);
    ((void (*)(void))0x8153a8)();
    void *hud = PTR(void *, 0xde4830);
    if (hud)
        METHOD(NoArg, hud, 0x1b0)(hud);
}

void apply_resized_window(void)
{
    if (moving_window)
        return;
    stock_apply_pending_mode();
    if (PTR(int, 0xf4d184) != WINDOWED) {
        tracked_window = 0;
        resize_pending = 0;
        moving_window = 0;
        return;
    }
    if (PTR(int, 0xf4d188))
        return;

    Handle window = PTR(Handle, 0xdc3c64);
    void *display = PTR(void *, 0xde4418);
    char *settings = PTR(char *, 0xde4364);
    if (!window || !display || !settings || !PTR(unsigned char, 0xdd1e14))
        return;

    int old_width = PTR(int, settings+0x30);
    int old_height = PTR(int, settings+0x34);
    if (!resize_pending && tracked_window == window &&
        last_width == old_width && last_height == old_height)
        return;

    Rect client;
    if (PTR(IsIconic, 0xbd0800)(window) || !PTR(WindowRect, 0xbd08b8)(window, &client))
        return;
    int width = client.right - client.left;
    int height = client.bottom - client.top;
    if (width <= 0 || height <= 0)
        return;

    if (width == old_width && height == old_height) {
        if (resize_pending || tracked_window != window ||
            last_width != width || last_height != height)
            remember_bounds(window, width, height);
        if (resize_pending)
            apply_cursor();
        resize_pending = 0;
        return;
    }
    if (!resize_pending || PTR(GetForeground, 0xbd0850)() != window)
        return;

    int depth = METHOD(GetDimension, display, 0x4c)(display);
    WindowState previous;
    int can_restore = previous_window(window, old_width, old_height, &previous);
    resize_pending = 0;
    PTR(int, 0xf4d188) = 1;
    release_cursor();
    PTR(const WindowState *, 0xf4d1d0) = can_restore ? &previous : 0;
    int success = METHOD(SetMode, display, 0x58)(display, width, height, depth, 1);
    if (success) {
        PTR(int, settings+0x30) = width;
        PTR(int, settings+0x34) = height;
        remember_bounds(window, width, height);
        refresh_window_ui();
        discard_detached_controls();
    } else if (PTR(const WindowState *, 0xf4d1d0)) {
        restore_window(window, &previous);
    }
    PTR(const WindowState *, 0xf4d1d0) = 0;
    PTR(int, 0xf4d188) = 0;
    apply_cursor();
}
