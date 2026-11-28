typedef void *Handle;
typedef unsigned int Word;
typedef struct { int x, y; } Point;
typedef struct { Point topLeft, bottomRight; } Rect;
typedef struct { Word size; Rect monitor, work; Word flags; } MonitorInfo;

#define STDCALL __attribute__((stdcall))
#define IMPORT(type, address) (*(type *)(address))
typedef int (STDCALL *ReadCursor)(Point *);
typedef int (STDCALL *ClipCursor)(const Rect *);
typedef int (STDCALL *GetSystemMetrics)(int);
typedef int (STDCALL *ReadClient)(Handle, Rect *);
typedef int (STDCALL *ConvertPoint)(Handle, Point *);
typedef Handle (STDCALL *GetForeground)(void);
typedef Handle (STDCALL *GetModule)(const char *);
typedef void *(STDCALL *GetProc)(Handle, const char *);
typedef Handle (STDCALL *MonitorFromPoint)(Point, Word);
typedef int (STDCALL *GetMonitorInfo)(Handle, MonitorInfo *);

enum { LEFT = 1, RIGHT = 2, TOP = 4, BOTTOM = 8, EDGE_SIZE = 3 };

static MonitorFromPoint locate_monitor;
static GetMonitorInfo inspect_monitor;

static int read_work_area(Point point, Rect *rect)
{
    if (!locate_monitor || !inspect_monitor) {
        Handle user32 = IMPORT(GetModule, 0xbd0134)("user32.dll");
        if (!user32)
            return 0;
        GetProc get_proc = IMPORT(GetProc, 0xbd018c);
        locate_monitor = (MonitorFromPoint)get_proc(user32, "MonitorFromPoint");
        inspect_monitor = (GetMonitorInfo)get_proc(user32, "GetMonitorInfoA");
        if (!locate_monitor || !inspect_monitor)
            return 0;
    }
    Handle monitor = locate_monitor(point, 0);
    MonitorInfo info;
    info.size = sizeof(info);
    if (!monitor || !inspect_monitor(monitor, &info))
        return 0;
    *rect = info.work;
    return 1;
}

static int contains(const Rect *rect, Point p)
{
    return p.x >= rect->topLeft.x && p.x < rect->bottomRight.x
        && p.y >= rect->topLeft.y && p.y < rect->bottomRight.y;
}

static int within_desktop(const Rect *client, Point p)
{
    Rect adjacent;
    return contains(client, p) && read_work_area(p, &adjacent) && contains(&adjacent, p);
}

unsigned window_edges(void)
{
    Handle window = *(Handle *)0xdc3c64;
    if (!window || IMPORT(GetForeground, 0xbd0850)() != window)
        return 0;

    Rect client;
    Point cursor;
    ConvertPoint to_screen = IMPORT(ConvertPoint, 0xbd089c);
    if (!IMPORT(ReadClient, 0xbd08b8)(window, &client)
        || !to_screen(window, &client.topLeft)
        || !to_screen(window, &client.bottomRight)
        || !IMPORT(ReadCursor, 0xbd081c)(&cursor)
        || !contains(&client, cursor))
        return 0;

    unsigned edges = 0;
    if (cursor.x - client.topLeft.x < EDGE_SIZE)
        edges |= LEFT;
    if (client.bottomRight.x - cursor.x <= EDGE_SIZE)
        edges |= RIGHT;
    if (cursor.y - client.topLeft.y < EDGE_SIZE)
        edges |= TOP;
    if (client.bottomRight.y - cursor.y <= EDGE_SIZE)
        edges |= BOTTOM;

    Rect work;
    if (!read_work_area(cursor, &work))
        return edges;
    if (!contains(&work, cursor))
        return 0;

    // A client larger than the working area still has reachable scroll edges.
    // Leave open a monitor seam if the game continues into the adjacent display.
    if (cursor.x - work.topLeft.x < EDGE_SIZE
        && !within_desktop(&client, (Point){work.topLeft.x - 1, cursor.y}))
        edges |= LEFT;
    if (work.bottomRight.x - cursor.x <= EDGE_SIZE
        && !within_desktop(&client, (Point){work.bottomRight.x, cursor.y}))
        edges |= RIGHT;
    if (cursor.y - work.topLeft.y < EDGE_SIZE
        && !within_desktop(&client, (Point){cursor.x, work.topLeft.y - 1}))
        edges |= TOP;
    if (work.bottomRight.y - cursor.y <= EDGE_SIZE
        && !within_desktop(&client, (Point){cursor.x, work.bottomRight.y}))
        edges |= BOTTOM;
    return edges;
}

int window_scroll(int amount, float *delta)
{
    unsigned edges = window_edges();
    if (!edges)
        return 0;
    const char *settings = *(const char **)0xde4364;
    float speed = *(const float *)(settings + 0xaf8);
    speed *= *(const float *)(settings + 0xaa4);
    float horizontal = speed * *(const float *)(settings + 0xa9c) * amount;
    float vertical = speed * *(const float *)(settings + 0xaa0) * amount;

    if (edges & LEFT)
        delta[0] -= horizontal;
    if (edges & RIGHT)
        delta[0] += horizontal;
    if (edges & TOP)
        delta[1] -= vertical;
    if (edges & BOTTOM)
        delta[1] += vertical;
    return 1;
}

int STDCALL clip_window_cursor(const Rect *client)
{
    ClipCursor clip = IMPORT(ClipCursor, 0xbd08cc);
    if (*(const int *)0xf4d184 != 2 || IMPORT(GetSystemMetrics, 0xbd08f4)(80) != 1)
        return clip(client);

    Rect work;
    if (!read_work_area((Point){0, 0}, &work))
        return clip(client);

    if (work.topLeft.x < client->topLeft.x)
        work.topLeft.x = client->topLeft.x;
    if (work.topLeft.y < client->topLeft.y)
        work.topLeft.y = client->topLeft.y;
    if (work.bottomRight.x > client->bottomRight.x)
        work.bottomRight.x = client->bottomRight.x;
    if (work.bottomRight.y > client->bottomRight.y)
        work.bottomRight.y = client->bottomRight.y;

    return work.topLeft.x < work.bottomRight.x && work.topLeft.y < work.bottomRight.y
        ? clip(&work) : clip(client);
}
