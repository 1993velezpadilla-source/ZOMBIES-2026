#!/usr/bin/env python3
"""Read-only IW3/KisakCOD <-> RotU source compatibility gate.

No COD4 content is embedded, fetched, compiled or redistributed by this tool.
The experimental RotU source is inspected, never executed.
"""
import argparse
import json
from pathlib import Path
import re
import sys

CORE = (
    'scripts/bots/_bots.gsc',
    'scripts/bots/_types.gsc',
    'scripts/gamemodes/_gamemodes.gsc',
    'scripts/gamemodes/_survival.gsc',
    'scripts/gamemodes/_waves.gsc',
    'scripts/gamemodes/_mysterybox.gsc',
    'scripts/players/_players.gsc',
    'scripts/include/waypoints.gsc',
    'scripts/include/codx_wrapper.gsc',
    'mod_scripts.csv',
    'mod.csv',
    'cfgs/general.cfg',
)
ENGINE = (
    'CMakeLists.txt',
    'generate-project.bat',
    'scripts/mp/CMakeLists.txt',
    'scripts/dedi/CMakeLists.txt',
)
GSC_REF = re.compile(r'^\s*rawfile\s*,\s*(scripts/[^\s,]+)\s*$', re.I)


def within(base: Path, relative: str) -> Path | None:
    """Reject absolute paths, traversal and symlinks from an untrusted manifest."""
    p = Path(relative)
    if p.is_absolute() or '..' in p.parts or '\\' in relative or not p.parts:
        return None
    root = base.resolve()
    file = (root / p).resolve()
    if not file.is_relative_to(root):
        return None
    return file


def scan_engine(root: Path) -> dict:
    missing = [p for p in ENGINE if not (root / p).is_file()]
    cmake = (root / 'CMakeLists.txt')
    content = cmake.read_text('utf-8', errors='replace') if cmake.is_file() else ''
    return {
        'source_snapshot_present': not missing and (root / 'src').is_dir(),
        'missing': missing + ([] if (root / 'src').is_dir() else ['src/']),
        'windows_platform_selected': bool(re.search(r'set\s*\(\s*KISAK_PLATFORM\s+win32\s*\)', content)),
        'android_native_build_verified': False,
    }


def scan_rotu(root: Path) -> dict:
    missing = [p for p in CORE if not (root / p).is_file()]
    manifest = root / 'mod_scripts.csv'
    refs: list[str] = []
    invalid: list[str] = []
    if manifest.is_file():
        for line in manifest.read_text('utf-8', errors='replace').splitlines():
            stripped = line.strip()
            if stripped.startswith('//') or not stripped:
                continue
            if not stripped.lower().startswith('rawfile,'):
                continue
            match = GSC_REF.fullmatch(stripped)
            if not match or within(root, match.group(1)) is None:
                invalid.append(stripped[:180])
            else:
                refs.append(match.group(1))
    absent = [ref for ref in refs if not within(root, ref).is_file()]
    bot = root / 'scripts/bots/_bots.gsc'
    waves = root / 'scripts/gamemodes/_waves.gsc'
    bot_src = bot.read_text('utf-8', errors='replace') if bot.is_file() else ''
    waves_src = waves.read_text('utf-8', errors='replace') if waves.is_file() else ''
    return {
        'core_scripts_present': not missing,
        'missing_core': missing,
        'listed_rawfiles': len(refs),
        'missing_rawfiles': absent,
        'invalid_manifest_entries': invalid,
        'zombie_bot_entrypoint_detected': 'loadWaypoints()' in bot_src and 'initZomTypes()' in bot_src,
        'wave_entrypoint_detected': 'startRegularWave()' in waves_src,
        'packaged_mod_ff_verified': False,
    }


def scan_game_data(root: Path | None) -> dict:
    if root is None:
        return {'checked': False, 'authorized_game_data_required': True}
    return {
        'checked': True,
        'multiplayer_iwd_present': (root / 'main/iw_00.iwd').is_file(),
        'mp_map_fastfiles': sorted(str(p.relative_to(root)) for p in (root / 'zone').glob('*/mp_*.ff'))[:32] if (root / 'zone').is_dir() else [],
        'note': 'Presence is not proof of ownership, valid hashes or runtime compatibility.',
    }


def preflight(kisak: Path, rotu: Path, game_data: Path | None = None) -> dict:
    engine = scan_engine(kisak)
    scripts = scan_rotu(rotu)
    data = scan_game_data(game_data)
    source_gate = (
        engine['source_snapshot_present']
        and scripts['core_scripts_present']
        and scripts['listed_rawfiles'] >= 6
        and not scripts['invalid_manifest_entries']
        and not scripts['missing_rawfiles']
        and scripts['zombie_bot_entrypoint_detected']
        and scripts['wave_entrypoint_detected']
    )
    return {
        'schema_version': 1,
        'source_preflight_pass': source_gate,
        'engine': engine,
        'rotu': scripts,
        'game_data': data,
        'runtime': {
            'iw3_rotu_compiled': False,
            'zombie_running': False,
            'apk_built': False,
            'android_port_implemented': False,
        },
        'next_gate': 'Validate an authorized COD4 MP build and required mod assets; test KisakCOD Windows dedicated + client with RotU before ARM64 research.',
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kisak', type=Path, required=True, help='Path to KisakCOD source tree')
    parser.add_argument('--rotu', type=Path, required=True, help='Path to upstream RotU source checkout')
    parser.add_argument('--game-data', type=Path, help='OPTIONAL local authorized COD4 root; never uploaded')
    parser.add_argument('--output', type=Path, help='Write static JSON report locally')
    args = parser.parse_args()
    report = preflight(args.kisak, args.rotu, args.game_data)
    result = json.dumps(report, indent=2, ensure_ascii=False)
    print(result)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(result + '\n', encoding='utf-8')
    return 0 if report['source_preflight_pass'] else 1


if __name__ == '__main__':
    sys.exit(main())
