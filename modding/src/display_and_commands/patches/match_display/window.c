typedef void *Handle;
typedef struct { int x, y; } Point;
typedef struct { Point first, end; } Rect;

#define STDCALL __attribute__((stdcall))
#define THISCALL __attribute__((thiscall))
#define READ(type, address) (*(type *)(address))
#define METHOD(type, object, slot) READ(type, READ(char *, object) + (slot))

typedef Handle (STDCALL *Foreground)(void);
typedef int (STDCALL *WindowRect)(Handle, Rect *);
typedef int (STDCALL *CursorPos)(Point *);
typedef int (STDCALL *PointToScreen)(Handle, Point *);
typedef unsigned char (THISCALL *Predicate)(void *);
typedef void (THISCALL *WindowEnable)(void *, int);
typedef void (THISCALL *StartScroll)(void *, int);

enum { WINDOWED = 2, SCREEN_PAGE = 1, EDGE_SCROLL = 3, EDGE_WIDTH = 3 };
enum { LEFT = 1, RIGHT = 2, TOP = 4, BOTTOM = 8 };
#define ACTIVE_MODE READ(int, 0xf4d184)
#define PENDING_MODE READ(int, 0xf4d17c)
#define COMMIT_MODE READ(int, 0xf4d178)
#define MODE_WIDGET READ(char *, 0xf4d1ac)

extern int moving_window;
extern unsigned stock_window_edges(void);
extern int stock_cursor_in_window(void);
extern void stock_apply_pending_mode(void);

static int contains(const Rect *rect, Point cursor)
{
    return cursor.x >= rect->first.x && cursor.x < rect->end.x &&
           cursor.y >= rect->first.y && cursor.y < rect->end.y;
}

unsigned window_scroll_edges(void)
{
    if (moving_window || READ(int, 0xf4d188) || READ(void *, 0xf4d19c))
        return 0;

    unsigned edges = stock_window_edges();
    Handle window = READ(Handle, 0xdc3c64);
    if (edges || !window || READ(Foreground, 0xbd0850)() != window)
        return edges;

    // A resizable window can capture the pointer all the way to its outer frame.
    Rect outer, client;
    Point cursor;
    PointToScreen to_screen = READ(PointToScreen, 0xbd089c);
    if (!READ(CursorPos, 0xbd081c)(&cursor) ||
        !READ(WindowRect, 0xbd08b0)(window, &outer) || !contains(&outer, cursor) ||
        !READ(WindowRect, 0xbd08b8)(window, &client) ||
        !to_screen(window, &client.first) || !to_screen(window, &client.end) ||
        contains(&client, cursor))
        return 0;

    int at_top = cursor.y < outer.first.y + EDGE_WIDTH;
    if (cursor.y >= client.first.y || at_top) {
        if (cursor.x < client.first.x)
            edges |= LEFT;
        if (cursor.x >= client.end.x)
            edges |= RIGHT;
    }
    if (at_top)
        edges |= TOP;
    if (cursor.y >= client.end.y)
        edges |= BOTTOM;
    return edges;
}

int legacy_scroll_guard(void)
{
    // The windowed tick checks the visible client and the outer frame itself.
    return ACTIVE_MODE == WINDOWED || stock_cursor_in_window();
}

void poll_edge_scroll(void *translator)
{
    const char *state = translator;
    void *hud = READ(void *, 0xde4830);
    char *mouse = READ(char *, 0xde36e0);
    if (READ(unsigned char, state + 0x38) || !hud || !mouse ||
        !READ(void *, 0xde447c) || !READ(void *, 0xde4388) ||
        !READ(unsigned char, (char *)hud + 0x15) || !READ(unsigned char, (char *)hud + 0x16) ||
        !window_scroll_edges())
        return;

    // The native mouse-move handler suppresses scroll in this cursor/UI state.
    if (READ(int, mouse + 0x4f24) == 1 && METHOD(Predicate, hud, 0xb0)(hud))
        return;
    ((StartScroll)0x83a9bd)(translator, EDGE_SCROLL);
}

int match_blocks_display_mode(void)
{
    void *logic = READ(void *, 0xde412c);
    // AptOptions uses the same GameLogic predicate when saving the resolution.
    return logic && ((Predicate)0x441b60)(logic);
}

void sync_display_mode_lock(void)
{
    char *widget = MODE_WIDGET;
    if (widget && READ(int, 0xf2767c) == SCREEN_PAGE) {
        int enable = !match_blocks_display_mode();
        if (!!(READ(unsigned, widget + 8) & 8) != enable)
            ((WindowEnable)0x7154b3)(widget, enable);
    }
}

void *editable_display_mode(void)
{
    return match_blocks_display_mode() ? 0 : MODE_WIDGET;
}

void queue_display_mode(int mode)
{
    if (!match_blocks_display_mode())
        PENDING_MODE = mode;
}

void clear_display_mode_request(void)
{
    PENDING_MODE = -1;
    COMMIT_MODE = -1;
}

void apply_allowed_display_mode(void)
{
    if ((PENDING_MODE >= 0 || COMMIT_MODE >= 0) && match_blocks_display_mode()) {
        clear_display_mode_request();
        return;
    }
    stock_apply_pending_mode();
}
