import argparse
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from patches.commands import build as commands
from patches.fixed_window import build as fixed_window
from patches.fullscreen import build as fullscreen
from patches.labels import build as labels
from patches.match_display import build as match_display
from patches.navigation_camera import build as navigation_camera
from patches.window_fit import build as window_fit
from patches.window_lifetime import build as window_lifetime

ENGINE = 'game.dat'
OPTIONS = 'apt/options.big'
PLAYERS = 'apt/playertribute.big'
RULES = 'apt/mpgamesetup.big'

BASELINE = {
    ENGINE: '947a02859ea7791fcc6f12bdf1da71a09a165c840275ea54e8e4ed66ddb91240',
    OPTIONS: '7593627ba7b7a9f2df03e6337f0a6537d0ea0e19825a409a41c04a214e797b4e',
    PLAYERS: '368be51a05a7781320b313bbd1e3188fd1f3f1158697e94153577fdb11cfd66a',
    RULES: '21f815302c94ae064c8f2106f33c44e31f6fada6d05b66f82bbc55c946d3ffdd',
}
FINAL = {
    ENGINE: '9562f81e6e71de72cb78e01501aba1dcf4d58db9bf2e33091e320dae624433e9',
    OPTIONS: '1cc858807146deb77ab0097846719c81fd8f34d656d7559c19687685352d8265',
    PLAYERS: '4742efd86c622028b0a600bb8cc5650cd1b6be0634a9875b7991a1e1076b3148',
    RULES: 'e36116574a69cdd73738370d5b01ef55693b212772bee4af0377e4966b8886e4',
}


def check_hashes(members, expected, stage):
    for name, wanted in expected.items():
        actual = sha256(members[name]).hexdigest()
        if actual != wanted:
            raise ValueError(f'{stage} {name}: expected SHA-256 {wanted}, got {actual}')


def patch(members, work):
    updated = dict(members)

    for step in (navigation_camera, commands, window_fit):
        updated[ENGINE], _ = step.patch_game(updated[ENGINE], work)
    updated[OPTIONS] = navigation_camera.patch_options(updated[OPTIONS])
    updated[PLAYERS] = labels.patch_players(updated[PLAYERS])
    updated[RULES] = labels.patch_rules(updated[RULES])

    # Build the historical resize and display changes, then restore a fixed frame.
    for step in (window_lifetime, fullscreen, match_display):
        updated[ENGINE], _ = step.patch_game(updated[ENGINE], work)
    updated[PLAYERS] = fullscreen.patch_players(updated[PLAYERS])
    updated[ENGINE] = fixed_window.patch_game(updated[ENGINE])
    return updated


def build_archive(source_path, output_path):
    if source_path.resolve() == output_path.resolve():
        raise ValueError('Use a different output path to keep the baseline intact.')
    with ZipFile(source_path) as source:
        infos = source.infolist()
        names = [item.filename for item in infos]
        if len(names) != len(set(names)):
            raise ValueError('The baseline ZIP has duplicate member names.')
        members = {name: source.read(name) for name in BASELINE}
        check_hashes(members, BASELINE, 'Input')
        with TemporaryDirectory() as temp:
            updated = patch(members, Path(temp))
        check_hashes(updated, FINAL, 'Output')
        comment = source.comment

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(source_path) as source, ZipFile(output_path, 'w') as output:
        output.comment = comment
        for item in infos:
            name = item.filename
            output.writestr(item, updated[name] if name in updated else source.read(name))

    with ZipFile(output_path) as output:
        if output.testzip() is not None or output.namelist() != names:
            raise ValueError('The output ZIP failed its integrity check.')
        check_hashes({name: output.read(name) for name in FINAL}, FINAL, 'Archive')


def main():
    parser = argparse.ArgumentParser(description='Build the fixed-window ROTWK update from the matching baseline ZIP.')
    parser.add_argument('baseline', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    try:
        build_archive(args.baseline, args.output)
    except (AssertionError, KeyError, ValueError) as exc:
        if not str(exc):
            raise SystemExit('A patch check failed. Check the baseline and the toolchain versions in README.md.') from exc
        raise SystemExit(str(exc)) from exc
    print(f'Wrote {args.output}')


if __name__ == '__main__':
    main()
