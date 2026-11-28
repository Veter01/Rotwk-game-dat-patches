typedef unsigned int UInt;
typedef const unsigned char Byte;
typedef const void Data;

#define THISCALL __attribute__((thiscall))
#define STDCALL __attribute__((stdcall))
#define PTR(object, offset) (*(Data * const *)((Byte *)(object) + (offset)))
#define INT(object, offset) (*(const int *)((Byte *)(object) + (offset)))
#define BYTE(object, offset) (*((Byte *)(object) + (offset)))
#define WORD(object, offset) (*(const unsigned short *)((Byte *)(object) + (offset)))

enum { OBJECT_UPGRADE = 7, FIRE_WEAPON = 0x17, SPECIAL_POWER = 0x18 };
enum { TOGGLE_POWER = 0x458, TOGGLE_WEAPON = 0x459, COMMAND_SLOTS = 33 };
enum { UNAVAILABLE = -1, NOT_ACTIVE = 0, ACTIVE = 1 };

typedef struct SelectionNode {
    const struct SelectionNode *next;
    const struct SelectionNode *prev;
    Data *drawable;
} SelectionNode;

typedef Data *(THISCALL *GetPointer)(Data *);
typedef Data *(THISCALL *FindByPointer)(Data *, Data *);
typedef Data *(THISCALL *FindByInt)(Data *, int);
typedef int (THISCALL *CheckByPointer)(Data *, Data *);
typedef void (THISCALL *AddArgument)(Data *, UInt);
typedef int (THISCALL *CalcPrice)(Data *, Data *, Data *);

extern int upgrade_button_usable(Data *button, Data *object);
extern int building_upgrade_role(Data *button);

static const SelectionNode *selection(void)
{
    Data *ui = PTR(0xde4830, 0);
    if (!ui)
        return 0;
    const SelectionNode *const *list = ((GetPointer)PTR(PTR(ui, 0), 0x124))(ui);
    return list ? *list : 0;
}

static Data *selected_object(const SelectionNode *node, Data *player)
{
    Data *object = node->drawable ? PTR(node->drawable, 0xfc) : 0;
    if (!object || (BYTE(object, 0x457) & 3))
        return 0;
    Data *kind = PTR(object, 4);
    if (!kind || (BYTE(kind, 0x10d) & 0x80))
        return 0;
    return ((GetPointer)0xf51261)(object) == player ? object : 0;
}

static Data *command_set(Data *object)
{
    Data *store = PTR(0xde7744, 0);
    if (!store)
        return 0;
    return ((FindByPointer)0x71efa2)(store, ((GetPointer)0x69156b)(object));
}

static Data *slot_button(Data *set, int slot)
{
    return ((FindByInt)0x80c837)(set, slot);
}

static Data *button_power(Data *button)
{
    Data *power = PTR(button, 0x44);
    return power ? ((GetPointer)0x688d3c)(power) : 0;
}

static int compare_string(Data *left, Data *right)
{
    return ((CheckByPointer)0x4065aa)(left, right);
}

static Data *first_auto_module(Data *object)
{
    Data *const *modules = (Data *const *)PTR(object, 0x24c);
    if (modules) {
        for (; *modules; ++modules) {
            if (PTR(*modules, 0) == (Data *)0xc57f8c)
                return *modules;
        }
    }
    return 0;
}

static Data *auto_button(Data *set, Data *clicked, int command, Data *power)
{
    for (int i = 0; i < COMMAND_SLOTS; ++i) {
        Data *button = slot_button(set, i);
        if (!button || INT(button, 0x14) != command)
            continue;
        if (command == FIRE_WEAPON) {
            if (INT(button, 0x80) == INT(clicked, 0x80))
                return button == clicked ? button : 0;
        } else {
            Data *candidate = button_power(button);
            if (candidate == power || (candidate && INT(candidate, 0x1c) == INT(power, 0x1c)
                && compare_string((Byte *)candidate + 0x10, (Byte *)power + 0x10) == 0))
                return button;
        }
    }
    return 0;
}

static int auto_state(Data *object, Data *clicked, int command, Data *power)
{
    Data *set = command_set(object);
    Data *btn = set ? auto_button(set, clicked, command, power) : 0;
    if (!btn || !BYTE(btn, 0x10c) || !upgrade_button_usable(btn, object))
        return UNAVAILABLE;

    Data *module;
    if (power) {
        if (!((FindByPointer)0x68c26d)(object, PTR(btn, 0x44)))
            return UNAVAILABLE;
        typedef Data *(*FindAutoPower)(Data *, Data *);
        module = ((FindAutoPower)0x85d6ad)(object, (Byte *)power + 0x10);
    } else {
        Data *required = PTR(btn, 0x24);
        if (required && !(unsigned char)((CheckByPointer)0x691421)(object, required))
            return UNAVAILABLE;
        module = first_auto_module(object);
    }
    return module ? ((CheckByPointer)0x85d741)(module, btn) : UNAVAILABLE;
}

int toggle_group(Data *bar, Data *clicked)
{
    if (INT(bar, 0x70) != 7 || PTR(bar, 0x6c) || !BYTE(clicked, 0x10c))
        return 0;
    int command = INT(clicked, 0x14);
    if (command != SPECIAL_POWER && command != FIRE_WEAPON)
        return 0;
    Data *power = command == SPECIAL_POWER ? button_power(clicked) : 0;
    if (command == SPECIAL_POWER && !power)
        return 0;
    const SelectionNode *head = selection();
    Data *players = PTR(0xde4928, 0);
    Data *player = players ? ((GetPointer)0x6a8839)(players) : 0;
    Data *stream = PTR(0xde6398, 0);
    if (!head || !player || !stream)
        return 0;

    int desired = NOT_ACTIVE;
    for (const SelectionNode *node = head->next; node != head; node = node->next) {
        Data *object = selected_object(node, player);
        if (object && auto_state(object, clicked, command, power) == NOT_ACTIVE) {
            desired = ACTIVE;
            break;
        }
    }

    int message_id = power ? TOGGLE_POWER : TOGGLE_WEAPON;
    int argument = power ? INT(power, 0x14) : INT(clicked, 0x80);
    FindByInt append = (FindByInt)PTR(PTR(stream, 0), 0x48);
    for (const SelectionNode *node = head->next; node != head; node = node->next) {
        Data *object = selected_object(node, player);
        if (!object || !INT(object, 0x74))
            continue;
        int state = auto_state(object, clicked, command, power);
        if (state == UNAVAILABLE || state == desired)
            continue;
        Data *message = append(stream, message_id);
        if (message) {
            ((AddArgument)0x7111e5)(message, argument);
            ((AddArgument)0x71111a)(message, INT(object, 0x74));
        }
    }
    return 1;
}

static Data *object_upgrade_button(Data *set, Data *clicked)
{
    Data *fallback = 0;
    unsigned group = WORD(clicked, 0x12e);
    for (int slot = 0; slot < COMMAND_SLOTS; ++slot) {
        Data *button = slot_button(set, slot);
        if (button == clicked)
            return button;
        if (!button || INT(button, 0x14) != OBJECT_UPGRADE || !PTR(button, 0x24))
            continue;
        if (PTR(button, 0x24) == PTR(clicked, 0x24))
            return button;
        if (!fallback && group && WORD(button, 0x12e) == group)
            fallback = button;
    }
    return fallback;
}

int THISCALL group_availability(Data *bar, Data *button, Data *window, Data *object,
                                 float *progress, int recurse)
{
    typedef int (THISCALL *Availability)(Data *, Data *, Data *, Data *, float *, int);
    int command = INT(button, 0x14);
    if (object && command == OBJECT_UPGRADE && !building_upgrade_role(button)) {
        Data *set = command_set(object);
        button = set ? object_upgrade_button(set, button) : 0;
    } else if (object && BYTE(button, 0x10c) && (command == SPECIAL_POWER || command == FIRE_WEAPON)) {
        Data *power = command == SPECIAL_POWER ? button_power(button) : 0;
        Data *set = command_set(object);
        button = set && (command == FIRE_WEAPON || power) ? auto_button(set, button, command, power) : 0;
    }
    if (!button) {
        *progress = 1.0f;
        return 0;
    }
    return ((Availability)0x942733)(bar, button, window, object, progress, recurse);
}

int group_can_buy(Data *bar, Data *button, Data *registry, Data *player, Data *upgrade,
                  Data *object, int show_error)
{
    typedef unsigned char (THISCALL *CanBuy)(Data *, Data *, Data *, Data *, int);
    CanBuy stock = (CanBuy)0xf513ba;
    if (INT(bar, 0x70) != 7 || building_upgrade_role(button))
        return stock(registry, player, upgrade, object, show_error);
    const SelectionNode *head = selection();
    if (!head || !player)
        return stock(registry, player, upgrade, object, show_error);
    Data *eligible_owner = 0;
    Data *eligible_upgrade = 0;
    Data *eligible_unit = 0;
    for (const SelectionNode *node = head->next; node != head; node = node->next) {
        Data *unit = selected_object(node, player);
        Data *set = unit ? command_set(unit) : 0;
        Data *candidate = set ? object_upgrade_button(set, button) : 0;
        if (!candidate)
            continue;
        Data *target = PTR(candidate, 0x24);
        if ((unsigned char)((CheckByPointer)0x691421)(unit, target) ||
            !(unsigned char)((CheckByPointer)0x694914)(unit, target) ||
            !upgrade_button_usable(candidate, unit))
            continue;
        Data *owner = ((GetPointer)0x68b678)(unit);
        if (!owner)
            continue;
        if (((CanBuy)0x66f492)(registry, owner, target, unit, 0))
            return 1;
        eligible_owner = owner;
        eligible_unit = unit;
        eligible_upgrade = target;
    }
    if (eligible_unit && show_error)
        return ((CanBuy)0x66f492)(registry, eligible_owner, eligible_upgrade, eligible_unit, 1);
    return 0;
}

int upgrade_price_range(Data *clicked, Data *upgrade, Data *player, Data *object, int *highest)
{
    CalcPrice calc_price = (CalcPrice)0x66f2c8;
    int price = calc_price(upgrade, player, object);
    *highest = price;
    if (!clicked || !player || INT(clicked, 0x14) != OBJECT_UPGRADE || building_upgrade_role(clicked))
        return price;
    const SelectionNode *head = selection();
    if (!head || head->next == head || head->next->next == head)
        return price;
    int lowest = 0x7fffffff;
    int high = -1;
    for (const SelectionNode *node = head->next; node != head; node = node->next) {
        Data *unit = selected_object(node, player);
        Data *set = unit ? command_set(unit) : 0;
        Data *button = set ? object_upgrade_button(set, clicked) : 0;
        if (!button)
            continue;
        Data *candidate = PTR(button, 0x24);
        if ((unsigned char)((CheckByPointer)0x691421)(unit, candidate) ||
            !(unsigned char)((CheckByPointer)0x694914)(unit, candidate) ||
            !upgrade_button_usable(button, unit))
            continue;
        Data *owner = ((GetPointer)0x68b678)(unit);
        int cost = calc_price(candidate, owner ? owner : player, unit);
        if (cost < 0)
            cost = 0;
        if (cost < lowest)
            lowest = cost;
        if (cost > high)
            high = cost;
    }
    if (high < 0)
        return price;
    *highest = high;
    return lowest;
}

void append_price_range(void *line, int highest)
{
    static const unsigned short suffix[] = {' ', 0x2013, ' ', '%', 'd', 0};
    typedef void (*Format)(void *, const unsigned short *, ...);
    typedef void (THISCALL *Append)(void *, void *);
    typedef void (THISCALL *Destroy)(void *);
    void *ending = 0;
    ((Format)0xadf7e0)(&ending, suffix, highest);
    ((Append)0x4065fe)(line, &ending);
    ((Destroy)0x4367b0)(&ending);
}
