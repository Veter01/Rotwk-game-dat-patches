from dataclasses import dataclass
from struct import pack, pack_into, unpack_from
from xml.etree import ElementTree as ET

from sage_apt.aptfile import CHAR_SIG, EDITTEXT, MOVIE, PLACEOBJECT, SHAPE, SPRITE, apt_bytes_to_xml

PLAYERS = 'apt/playertribute.big'
RULES = 'apt/mpgamesetup.big'
EXTRA_WIDTH = 26.0

# X coordinates of the old and new column separators in the status-page grid geometry.
OLD_EDGES = (-4.95, 86.040811, 179.0308797, 217.0268217, 281.0199873, 345.0131528, 436.3)
NEW_EDGES = (-4.95, 75.05, 165.05, 199.05, 253.05, 335.05, 462.3)


@dataclass(frozen=True)
class BigEntry:
    header: int
    offset: int
    length: int


def big_index(blob):
    assert blob[:4] == b'BIGF' and unpack_from('<I', blob, 4)[0] == len(blob)
    count, data_start = unpack_from('>II', blob, 8)
    cursor = 16
    entries = {}
    for _ in range(count):
        offset, size = unpack_from('>II', blob, cursor)
        end = blob.index(0, cursor + 8)
        name = blob[cursor + 8:end].decode('ascii')
        assert name not in entries and offset >= data_start and offset + size <= len(blob)
        entries[name] = BigEntry(cursor, offset, size)
        cursor = end + 1
    assert cursor <= data_start
    return entries


def entry_data(blob, entry):
    return bytes(blob[entry.offset:entry.offset + entry.length])


def patch_big(blob, changes):
    before = big_index(blob)
    out = bytearray(blob)
    for name, data in changes.items():
        entry = before[name]
        if len(data) == entry.length:
            out[entry.offset:entry.offset + entry.length] = data
        else:
            pack_into('>II', out, entry.header, len(out), len(data))
            out.extend(data)
    pack_into('<I', out, 4, len(out))
    after = big_index(out)
    assert list(after) == list(before)
    modified = {name for name in before if entry_data(blob, before[name]) != entry_data(out, after[name])}
    assert modified == set(changes)
    return bytes(out)


def f32(value):
    return unpack_from('<f', pack('<f', value))[0]


class Movie:
    """Edit only known Float32 fields in place, retaining all actions and references."""

    def __init__(self, apt, constants):
        self.apt = bytearray(apt)
        self.constants = constants
        self.xml = ET.fromstring(apt_bytes_to_xml(apt, constants))
        movie = unpack_from('<I', constants, 0x14)[0]
        self._check_type(movie, MOVIE)
        self.count, self.table = unpack_from('<II', apt, movie + 20)

    def _check_type(self, offset, kind):
        assert unpack_from('<II', self.apt, offset) == (kind, CHAR_SIG)

    def _character(self, number, kind):
        assert number < self.count
        offset = unpack_from('<I', self.apt, self.table + number * 4)[0]
        self._check_type(offset, kind)
        return offset

    def _set_float(self, offset, element, field, value):
        assert unpack_from('<f', self.apt, offset)[0] == f32(float(element.get(field)))
        pack_into('<f', self.apt, offset, value)
        element.set(field, format(f32(value), '.8g'))

    def text(self, char, key=None):
        element = self.xml.find(f'edittext[@id="{char}"]')
        assert element is not None
        if key is not None:
            assert element.find('ettext').get('text') == key
        return element

    def text_float(self, char, field, value):
        fields = {'left': 8, 'top': 12, 'right': 16, 'bottom': 20, 'height': 36}
        self._set_float(self._character(char, EDITTEXT) + fields[field], self.text(char), field, value)

    def shape_right(self, char, value):
        node = self.xml.find(f'shape[@id="{char}"]')
        assert node.get('geometry') == str(char)
        self._set_float(self._character(char, SHAPE) + 16, node, 'right', value)

    def place(self, sprite, frame, depth, character, **changes):
        element = self.xml.find(f'sprite[@id="{sprite}"]/frames/frame[@id="{frame}"]/placeobject[@depth="{depth}"]')
        assert element is not None and int(element.get('character')) == character
        span = self._character(sprite, SPRITE)
        num_frames, frames = unpack_from('<II', self.apt, span + 8)
        assert frame < num_frames
        count, table = unpack_from('<II', self.apt, frames + frame * 8)
        positions = [unpack_from('<I', self.apt, table + index * 4)[0] for index in range(count)]
        [offset] = [pos for pos in positions if unpack_from('<I', self.apt, pos)[0] == PLACEOBJECT
                    and unpack_from('<ii', self.apt, pos + 8) == (depth, character)]
        fields = {'rotm00': 16, 'tx': 32, 'ty': 36}
        for field, value in changes.items():
            if callable(value):
                value = value(float(element.get(field)))
            self._set_float(offset + fields[field], element, field, value)

    def finish(self):
        parsed = ET.fromstring(apt_bytes_to_xml(bytes(self.apt), self.constants))
        assert ET.tostring(parsed) == ET.tostring(self.xml)
        return bytes(self.apt)


def edit_movie(blob, name):
    entries = big_index(blob)
    return Movie(entry_data(blob, entries[f'{name}.apt']), entry_data(blob, entries[f'{name}.const']))


def shift(amount):
    return lambda value: value + amount


def center(edges, column):
    return (edges[column] + edges[column + 1]) / 2


def shift_center(column, extra=0):
    return shift(center(NEW_EDGES, column) - center(OLD_EDGES, column) + extra)


def widen_ru(blob, move):
    """Rewrite X coordinates only. Keep strokes, colors, triangles, and Y coordinates."""
    before = blob.decode('ascii')
    lines = []
    hits = set()
    for line in before.splitlines(keepends=True):
        if line.startswith(('l ', 't ')):
            points = line[2:].rstrip('\r\n').split(':')
            for index in range(0, len(points), 2):
                x = float(points[index])
                if x in move:
                    hits.add(x)
                    points[index] = format(move[x], '.10g')
            line = line[:2] + ':'.join(points) + ('\r\n' if line.endswith('\r\n') else '\n')
        lines.append(line)
    assert hits == set(move)
    return ''.join(lines).encode('ascii')


def patch_players(blob):
    name = 'PlayerTribute'
    movie = edit_movie(blob, name)

    # Scale the existing gradient, then move the data table and its status-tab frame together.
    movie.place(61, 0, 1, 45, rotm00=(441.15 + EXTRA_WIDTH) / 441.15)
    movie.place(80, 0, 34, 61, tx=shift(-EXTRA_WIDTH / 2))
    movie.place(80, 1, 1, 69, tx=shift(-EXTRA_WIDTH / 2))
    movie.place(80, 1, 59, 73, tx=shift(-EXTRA_WIDTH / 2))

    for edge_id in (57, 59, 62, 65):
        element = movie.xml.find(f'shape[@id="{edge_id}"]')
        movie.shape_right(edge_id, float(element.get('right')) + EXTRA_WIDTH)

    for column, depth, char in ((0, 18, 53), (1, 20, 55), (2, 21, 56), (3, 19, 54)):
        movie.place(61, 0, depth, char, tx=shift_center(column))

    header = movie.text(56, '$HeaderTeam')
    font_height = float(header.get('height'))
    for column, depth, char, key in ((4, 23, 96, '$ETBlock'), (5, 25, 101, '$ShareArmy')):
        text = movie.text(char, key)
        assert text.get('font') == header.get('font') and text.get('alignment') == header.get('alignment')
        movie.text_float(char, 'height', font_height)
        left, right = -2.0, (NEW_EDGES[column+1] - NEW_EDGES[column]) - 5.0
        movie.text_float(char, 'left', left)
        movie.text_float(char, 'right', right)
        center_in_sprite = center(NEW_EDGES, column) * 1.0001068 + 4.9499998
        movie.place(61, 0, depth, char, rotm00=1.0, tx=center_in_sprite-(left+right)/2, ty=4.6)

    # Preserve alignment for player names, status values and the actual row buttons.
    movie.text_float(46, 'right', 93.9)
    movie.text_float(49, 'right', 73.9)
    for column, depth, char, extra in ((1, 2, 47, 0), (2, 3, 48, 0), (3, 4, 49, 3)):
        movie.place(50, 0, depth, char, tx=shift_center(column, extra))
    movie.place(51, 4, 2, 90, tx=shift_center(4))
    movie.place(51, 4, 3, 100, tx=shift_center(5))

    entries = big_index(blob)
    changes = {f'{name}.apt': movie.finish()}
    geometry = {
        57: {445.35: 445.35 + EXTRA_WIDTH},
        59: dict(zip(OLD_EDGES[1:], NEW_EDGES[1:])),
        62: {437.25: 437.25 + EXTRA_WIDTH},
        65: {448.0: 448.0 + EXTRA_WIDTH},
    }
    for number, mapping in geometry.items():
        path = f'{name}_geometry/{number}.ru'
        changes[path] = widen_ru(entry_data(blob, entries[path]), mapping)
    return patch_big(blob, changes)


def patch_rules(blob):
    name = 'MpGameSetup'
    movie = edit_movie(blob, name)
    text = movie.text(8, '')
    assert text.get('height') == movie.text(15, '').get('height') == '14'
    [field] = [place for place in movie.xml.findall('sprite[@id="9"]/frames/frame/placeobject')
               if place.find('poname[@name="RuleText"]') is not None]
    assert field.get('character') == '8'
    rows = movie.xml.findall('sprite[@id="10"]/frames/frame/placeobject')
    assert len(rows) == 5 and all(row.get('character') == '9' for row in rows)
    movie.text_float(8, 'right', 480)
    return patch_big(blob, {f'{name}.apt': movie.finish()})
