from pathlib import Path
import re
import struct
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / "build" / "weather"
NAME = "____enrth_data_WeatherColors"
COLOR = b"R:30 G:130 B:130"
SYSTEM = r"data\ini\object\system\system.ini"
GOOD = r"data\ini\object\system\includes\systemgood.inc"
EVIL = r"data\ini\object\system\includes\systemevil.inc"
PARTICLES = r"data\ini\includes\fxparticlesystem.inc"
SPELLS = {
    SYSTEM: {
        b"SpellBookCloudBreak": (b"CloudBreakSpecialPower", b"SUNNY"),
        b"SpellBookFreezingRain": (b"OCLSpecialPower", b"RAINY"),
    },
    GOOD: {
        b"SpellBookCloudBreakRohan": (b"CloudBreakSpecialPower", b"SUNNY"),
        b"SpellBookCloudBreakLothlorien": (b"CloudBreakSpecialPower", b"SUNNY"),
        b"SpellBookCloudBreakImladris": (b"CloudBreakSpecialPower", b"SUNNY"),
        b"SpellBookCloudBreakKampagne": (b"CloudBreakSpecialPower", b"SUNNY"),
    },
    EVIL: {
        b"SpellBookCloudBreakHarad": (b"CloudBreakSpecialPower", b"SUNNY"),
        b"SpellBookSnowRain": (b"CloudBreakSpecialPower", b"CLOUDYRAINY"),
    },
}
BEHAVIOR = re.compile(rb"(?ms)^[ \t]*Behavior[ \t]*=[ \t]*(\w+)[^\r\n]*\r?\n.*?^[ \t]*End\b[^\r\n]*")
TRAILER = b"L225\0\0\0\0"


def read_big(data):
    assert data[:4] == b"BIGF"
    assert struct.unpack_from("<I", data, 4)[0] == len(data)
    count, end = struct.unpack_from(">II", data, 8)
    position = 16
    expected_offset = end + 1
    entries = {}
    for _ in range(count):
        offset, size = struct.unpack_from(">II", data, position)
        name_end = data.index(0, position + 8, end)
        name = data[position + 8:name_end].decode("cp1252")
        assert name not in entries and offset == expected_offset
        entries[name] = memoryview(data)[offset:offset + size]
        assert len(entries[name]) == size
        position = name_end + 1
        expected_offset += size
    assert data[position:end + 1] == TRAILER
    assert expected_offset == len(data)
    return entries


def write_big(entries):
    paths = {name: name.encode("cp1252") + b"\x00" for name in entries}
    payload_start = 16 + sum(8 + len(name) for name in paths.values()) + len(TRAILER)
    total = payload_start + sum(len(data) for data in entries.values())
    header = bytearray(b"BIGF" + struct.pack("<I", total))
    header.extend(struct.pack(">II", len(entries), payload_start - 1))
    offset = payload_start
    for name, data in entries.items():
        header.extend(struct.pack(">II", offset, len(data)))
        header.extend(paths[name])
        offset += len(data)
    header.extend(TRAILER)
    assert len(header) == payload_start and offset == total
    return b"".join([header, *entries.values()])


def tint_weather_spells(source, spells):
    edited = set()

    def update(match):
        block = match[0]
        template = re.search(rb"(?m)^[ \t]*SpecialPowerTemplate[ \t]*=[ \t]*(\w+)", block)
        if not template or template[1] not in spells:
            return block
        spell = template[1]
        module, weather = spells[spell]
        assert spell not in edited and match[1] == module
        assert re.search(rb"(?m)^[ \t]*AttributeModifierWeatherBased[ \t]*=[ \t]*Yes\b", block)
        assert not re.search(rb"(?m)^[ \t]*DarkeningFactor\b", block)
        assert re.search(rb"(?m)^[ \t]*ChangeWeather[ \t]*=[ \t]*" + weather + rb"\b", block)

        def append_factor(line):
            return line[0] + line[1] + b"DarkeningFactor" + line[2] + COLOR + line[3]

        block, count = re.subn(
            rb"(?m)^([ \t]*)ChangeWeather([ \t]*=[ \t]*)[^\r\n]*(\r?\n)",
            append_factor,
            block,
        )
        assert count == 1
        edited.add(spell)
        return block

    result = BEHAVIOR.sub(update, source)
    assert edited == set(spells)
    assert re.sub(rb"(?m)^[ \t]*DarkeningFactor[ \t]*=[ \t]*" + COLOR + rb"\r?\n", b"", result) == source
    return result


def tint_avalanche_snow(source):
    particle = re.compile(rb"(?ms)^FXParticleSystem AvalancheSnowFlakesRain\r?\n.*?^End\b")

    def update(match):
        block, count = re.subn(
            rb"(?m)^([ \t]*Color[123][ \t]*=[ \t]*)R:255 G:255 B:255(?=[ \t]+\d+\b)",
            rb"\g<1>" + COLOR,
            match[0],
        )
        assert count == 3
        return block

    result, count = particle.subn(update, source)
    assert count == 1
    assert particle.sub(lambda match: match[0].replace(COLOR, b"R:255 G:255 B:255"), result) == source
    return result


source = read_big((ROOT / "inputs" / "____enrth_data.big").read_bytes())
edits = {name: tint_weather_spells(bytes(source[name]), spells) for name, spells in SPELLS.items()}
edits[PARTICLES] = tint_avalanche_snow(bytes(source[PARTICLES]))
expected = {name: edits[name] for name in source if name in edits}
assert all(data != source[name] for name, data in expected.items())

path = WORK / f"{NAME}.zip"
with ZipFile(path, "w", compression=ZIP_DEFLATED, compresslevel=9) as output:
    output.writestr(f"{NAME}.big", write_big(expected))
with ZipFile(path) as output:
    assert output.testzip() is None
    assert output.namelist() == [f"{NAME}.big"]
    packed = read_big(output.read(f"{NAME}.big"))
    assert list(packed) == list(expected) and packed == expected

print(f"{path.name} ({path.stat().st_size:,} bytes) contains exactly these {len(packed)} changed entries:")
for name in packed:
    print(name)
