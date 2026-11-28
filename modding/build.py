"""Rebuild the documented ROTWK patches from matching local input files."""

import argparse
from hashlib import sha256
import os
from pathlib import Path
from shutil import copyfile
import subprocess
import sys


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "src"
OUTPUT = ROOT / "build"
INPUTS = {
    "game.dat": "bad61adac79fa2e1919d65387196913610685b5c0b05b6219e4872e6dd49f3f5",
    "____enrth_data.big": "e9402f6398813313bf94653033fd681514e35bae4f3004c9fc85737c5b950e3a",
    "playertribute.big": "6ba45687b855765ca1fb8da17db0da417dccdd00b747ffb284545c7e2db59906",
    "mpgamesetup.big": "fa0d60542bcd7d83f9ba24230cfeec2dd2d087b35fec8ce568467231164490db",
    "options.big": "a099295aef0ae307b29f4356900456535a3d44c63dbd5c716ac531e9e58f8acc",
}


def verify_inputs():
    for name, expected in INPUTS.items():
        path = ROOT / "inputs" / name
        if not path.is_file():
            raise SystemExit(f"Missing {path.relative_to(ROOT)}. See README.md for the required inputs.")
        with path.open("rb") as stream:
            actual = sha256()
            while chunk := stream.read(1024 * 1024):
                actual.update(chunk)
        if actual.hexdigest() != expected:
            raise SystemExit(f"Unexpected SHA-256 for {path.relative_to(ROOT)}: {actual.hexdigest()}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true", help="also run the emulation checks")
    args = parser.parse_args()
    verify_inputs()

    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(filter(None, (str(SOURCE), env.get("PYTHONPATH"))))

    def run(name, *script_args):
        subprocess.run([sys.executable, str(SOURCE / name), *(str(arg) for arg in script_args)],
                       cwd=ROOT, env=env, check=True)

    for directory in ("harvest", "shared-army/apt", "weather", "help"):
        (OUTPUT / directory).mkdir(parents=True, exist_ok=True)

    run("harvest/build_ini.py")
    run("harvest/build_game.py")
    run("shared_army/build_game.py")
    run("shared_army/build_player_tribute.py")
    run("shared_army/build_rules.py", ROOT / "inputs" / "mpgamesetup.big",
        OUTPUT / "shared-army" / "apt" / "mpgamesetup.big")
    run("weather/build.py")
    run("help/build_game.py")
    run("help/build_page.py")
    run("help/build_atlas.py")

    for directory in ("shared-army", "help"):
        root = OUTPUT / directory
        copyfile(root / "game.dat", root / "game.exe")

    if args.verify:
        for script in ("harvest/verify.py", "shared_army/verify.py",
                       "shared_army/verify_localization.py", "weather/verify.py", "help/verify.py"):
            run(script)


if __name__ == "__main__":
    main()
