"""Compile editable ROTWK APT movies and rebuild their BIGF archives."""

import argparse
from pathlib import Path
import struct
import tempfile
from xml.etree import ElementTree as ET

from sage_apt.aptfile import AptError, xml_bytes_to_apt


MOVIES = {
    "mpgamesetup": ("MpGameSetup", b"6"),
    "options": ("Options", b"7"),
    "playertribute": ("PlayerTribute", b"7"),
}
SOURCE = Path(__file__).resolve().parent / "source"


def read_big(path):
    data = path.read_bytes()
    if len(data) < 16 or data[:4] != b"BIGF":
        raise ValueError(f"{path.name} is not a BIGF archive")
    size = struct.unpack_from("<I", data, 4)[0]
    count, directory_limit = struct.unpack_from(">II", data, 8)
    if size != len(data) or not 16 <= directory_limit <= size:
        raise ValueError(f"Invalid archive header in {path.name}")

    cursor = 16
    members = {}
    for _ in range(count):
        if cursor + 8 >= directory_limit:
            raise ValueError(f"Truncated directory in {path.name}")
        offset, length = struct.unpack_from(">II", data, cursor)
        start = cursor + 8
        end = data.index(b"\0", start, directory_limit)
        name = data[start:end].decode("ascii")
        cursor = end + 1
        if name in members or offset < directory_limit or offset + length > size:
            raise ValueError(f"Invalid BIGF entry {name!r} in {path.name}")
        members[name] = data[offset:offset + length]
    return members


def write_big(members):
    entries = [(name.encode("ascii") + b"\0", data) for name, data in members.items()]
    directory_end = 16 + sum(8 + len(name) for name, _ in entries)
    padding = bytes((-directory_end) % 4)
    first_offset = directory_end + len(padding)
    offset = first_offset
    directory = bytearray()
    for name, payload in entries:
        directory.extend(struct.pack(">II", offset, len(payload)))
        directory.extend(name)
        offset += len(payload)
    header = b"BIGF" + struct.pack("<I", offset)
    header += struct.pack(">II", len(entries), first_offset)
    return b"".join((header, directory, padding, *(data for _, data in entries)))


def build_movie(members, stem, movie, version):
    for ext in (".apt", ".const", ".dat"):
        if f"{movie}{ext}" not in members:
            raise ValueError(f"Missing {movie}{ext} in {stem}.big")

    folder = SOURCE / stem
    xml = (folder / f"{movie}.xml").read_bytes()
    apt, const = xml_bytes_to_apt(xml)
    if apt[:9] != b"Apt Data:":
        raise ValueError(f"Unexpected compiled APT header for {movie}")

    # The compiler emits version 7. Keep the header version of the edited movie.
    members[f"{movie}.apt"] = apt[:9] + version + apt[10:]
    members[f"{movie}.const"] = const

    geometry = f"{movie}_geometry"
    for path in sorted((folder / geometry).glob("*.ru")):
        members[f"{geometry}/{path.name}"] = path.read_bytes()

    for shape in ET.fromstring(xml).iter("shape"):
        mesh = f"{geometry}/{shape.attrib['geometry']}.ru"
        if mesh not in members:
            raise ValueError(f"Missing {mesh} for APT shape {shape.get('id')}")
    return write_big(members)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("originals", type=Path, help="directory with the three original BIG archives")
    parser.add_argument("output", type=Path, help="new directory for the rebuilt archives")
    args = parser.parse_args()

    try:
        output = args.output.resolve()
        if output.exists():
            raise ValueError(f"Choose a new output directory. {output} already exists.")
        with tempfile.TemporaryDirectory(dir=output.parent) as temp:
            staging = Path(temp) / "archives"
            staging.mkdir()
            for stem, (movie, version) in MOVIES.items():
                name = f"{stem}.big"
                archive = build_movie(read_big(args.originals / name), stem, movie, version)
                (staging / name).write_bytes(archive)
            staging.rename(output)
    except (AptError, ET.ParseError, OSError, ValueError) as exc:
        parser.exit(1, f"{exc}\n")
    print(f"Rebuilt {len(MOVIES)} BIG archives in {output}")


if __name__ == "__main__":
    main()
