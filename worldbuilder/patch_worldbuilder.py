"""Apply the documented ROTWK WorldBuilder patches to a matching local executable."""

import argparse
import hashlib
import json
from pathlib import Path


PATCH_STAGES = {"memory": 1, "map": 2, "full": 3}


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def apply_stage(image, stage):
    name = stage["name"]
    extra_bytes = stage["size_bytes"] - len(image)
    if extra_bytes < 0:
        raise ValueError(f"Invalid output size for {name}")
    image.extend(bytes(extra_bytes))

    for address, before_hex, after_hex in stage["edits"]:
        start = int(address, 16)
        before = bytes.fromhex(before_hex)
        after = bytes.fromhex(after_hex)
        end = start + len(before)
        if start < 0 or end > len(image) or len(before) != len(after):
            raise ValueError(f"Invalid patch record at {address}")
        if image[start:end] != before:
            raise ValueError(f"Unexpected original bytes at {address} in {name}")
        image[start:end] = after

    if sha256(image) != stage["sha256"]:
        raise ValueError(f"Output SHA-256 mismatch after {name}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="original worldbuilder.exe")
    parser.add_argument("output", type=Path, help="new executable path")
    parser.add_argument(
        "--patch",
        choices=PATCH_STAGES,
        default="full",
        help="choose memory only, map and memory, or the full patch",
    )
    args = parser.parse_args()

    try:
        manifest_path = Path(__file__).with_name("patch-data.json")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        image = bytearray(args.source.read_bytes())
        if sha256(image) != manifest["original_sha256"]:
            raise ValueError("Unsupported source SHA-256. Use the original build from the guide.")
        for stage in manifest["stages"][:PATCH_STAGES[args.patch]]:
            apply_stage(image, stage)
        with args.output.open("xb") as stream:
            stream.write(image)
    except (OSError, ValueError) as error:
        parser.exit(1, f"{error}\n")

    print(f"Created {args.output} (SHA-256 {sha256(image)})")


if __name__ == "__main__":
    main()
