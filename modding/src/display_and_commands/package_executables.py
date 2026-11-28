import argparse
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

import pefile


def package(source_path, output_path):
    if source_path.resolve() == output_path.resolve():
        raise ValueError('Use a different output path to keep the source ZIP intact.')
    with ZipFile(source_path) as source:
        original = source.getinfo('game.dat')
        image = source.read(original)

    pe = pefile.PE(data=image)
    executable = bool(pe.FILE_HEADER.Characteristics & 0x0002)
    dll = bool(pe.FILE_HEADER.Characteristics & 0x2000)
    entry = pe.get_section_by_rva(pe.OPTIONAL_HEADER.AddressOfEntryPoint)
    if (pe.FILE_HEADER.Machine != 0x14c or pe.OPTIONAL_HEADER.Magic != 0x10b
            or pe.OPTIONAL_HEADER.Subsystem != 2 or not executable or dll
            or entry is None or not entry.Characteristics & 0x20000000):
        raise ValueError('game.dat is not an x86 Windows GUI executable.')

    output_path.parent.mkdir(parents=True, exist_ok=True)
    names = ['game.dat', 'game.exe']
    with ZipFile(output_path, 'w') as output:
        for name in names:
            member = ZipInfo(name, date_time=original.date_time)
            output.writestr(member, image, compress_type=ZIP_DEFLATED, compresslevel=9)
    with ZipFile(output_path) as output:
        if (output.namelist() != names or output.testzip() is not None
                or any(output.read(name) != image for name in names)):
            raise ValueError('The executable archive failed its integrity check.')


def main():
    parser = argparse.ArgumentParser(description='Package a built ROTWK engine under both filenames.')
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    package(args.source, args.output)
    print(f'Wrote {args.output}')


if __name__ == '__main__':
    main()
