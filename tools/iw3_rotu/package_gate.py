#!/usr/bin/env python3
"""Reproduce RotU's source-script IWD packaging, without COD4 commercial assets.

RotU's compile_mod.bat packages maps/mp, scripts and common_scripts in
z_svr_scripts.iwd. It intentionally comments out include,mod_scripts in
mod.csv. This tool follows that layout: it does NOT change upstream manifests
or pretend to build mod.ff. The ephemeral IWD must not be published.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import zipfile

SCRIPT_DIRS = ('maps/mp/', 'scripts/', 'common_scripts/')
REQUIRED = (
    'maps/mp/gametypes/surv.gsc',
    'scripts/bots/_bots.gsc',
    'scripts/include/waypoints.gsc',
    'scripts/gamemodes/_waves.gsc',
)
ASSET_TYPES = ('fx', 'xmodel', 'xanim', 'weapon', 'sound', 'material', 'localize', 'menufile', 'stringtable')


def parse_manifest(filename: Path) -> list[tuple[str, str]]:
    result = []
    for raw in filename.read_text(encoding='utf-8', errors='replace').splitlines():
        s = raw.strip()
        if not s or s.startswith('//') or s.startswith('#'):
            continue
        fields = [x.strip() for x in s.split(',')]
        if len(fields) >= 2 and fields[0] and fields[1]:
            result.append((fields[0].lower(), fields[1]))
    return result


def git_tree_paths(root: Path) -> set[str]:
    proc = subprocess.run(
        ['git', '-C', str(root), 'ls-tree', '-r', '--name-only', 'HEAD'],
        capture_output=True, text=True, timeout=30, check=True,
    )
    return {p.strip() for p in proc.stdout.splitlines() if p.strip()}


def script_members(paths: set[str]) -> list[str]:
    """Only tracked files in the same directories as original compile_mod.bat."""
    return sorted(p for p in paths if p.startswith(SCRIPT_DIRS)
                  and '..' not in Path(p).parts and not Path(p).is_absolute())


def source_audit(root: Path, inventory: set[str]) -> dict:
    mod = root / 'mod.csv'
    scripts = root / 'mod_scripts.csv'
    builder = root / 'compile_mod.bat'
    if not mod.is_file() or not scripts.is_file() or not builder.is_file():
        raise FileNotFoundError('RotU mod.csv, mod_scripts.csv and compile_mod.bat are all required')
    mod_rows = parse_manifest(mod)
    script_rows = parse_manifest(scripts)
    builder_txt = builder.read_text(encoding='utf-8', errors='replace').lower()
    canonical_iwd = ('z_svr_scripts.iwd' in builder_txt and
                     all(fragment in builder_txt for fragment in (
                         'maps\\mp\\*.*', 'scripts\\*.*', 'common_scripts\\*.*')))
    present = script_members(inventory)
    missing_required = sorted(set(REQUIRED) - inventory)
    listed_scripts = [p for k, p in script_rows if k == 'rawfile']
    missing_listed = sorted(set(listed_scripts) - inventory)
    rawfiles = [p for k, p in mod_rows if k == 'rawfile']
    missing_rawfiles = sorted(set(rawfiles) - inventory)
    mod_gametype_missing = [p for p in missing_rawfiles if p.endswith('.gsc') and p.startswith('maps/mp/')]
    asset_counts = {key: sum(k == key for k, _ in mod_rows) for key in ASSET_TYPES}
    # Mod references resources supplied by game data or third-party content;
    # even a complete upstream git tree doesn't validate these dependencies.
    return {
        'schema_version': 2,
        'canonical_script_delivery': 'z_svr_scripts.iwd',
        'canonical_builder_uses_script_iwd': canonical_iwd,
        'mod_csv_script_include_enabled': ('include', 'mod_scripts') in mod_rows,
        'mod_scripts_manifest_listed_rawfiles': len(listed_scripts),
        'script_iwd_members_in_git_tree': len(present),
        'missing_critical_script_paths': missing_required,
        'missing_mod_scripts_manifest_paths': missing_listed,
        'missing_mod_gametype_paths_from_upstream_tree': mod_gametype_missing,
        'upstream_tree_rawfile_absences': missing_rawfiles,
        'referenced_asset_types': dict(sorted(asset_counts.items())),
        'mod_ff_built': False,
        'mod_ff_asset_dependencies_verified': False,
        'live_zombie_verified': False,
        'script_iwd_source_gate': canonical_iwd and bool(present)
                                  and not missing_required and not missing_listed,
        'notes': [
            'RotU scripts are normally placed in an IWD (ZIP), not included in mod.ff; a commented include,mod_scripts is expected.',
            'Non-script rawfile paths missing from the upstream tree may require game or other authorized mod tools; no inference of missing ownership.',
            'No game binary, COD4 data, proprietary mod assets or mod.ff is copied or released.',
        ],
    }


def make_iwd(root: Path, dest: Path, paths: set[str]) -> dict:
    names = script_members(paths)
    if not names:
        raise ValueError('No tracked script files to package')
    root = root.resolve()
    dest.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(dest, 'w') as archive:
        for name in names:
            file = root / name
            # Fail on missing sparse files; never archive symlinks or traversal.
            if not file.is_file() or file.is_symlink() or not file.resolve().is_relative_to(root):
                raise ValueError(f'Missing or unsafe script source: {name}')
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o100644 << 16)
            archive.writestr(info, file.read_bytes(), compress_type=zipfile.ZIP_DEFLATED)
    with zipfile.ZipFile(dest) as archive:
        corrupt = archive.testzip()
        if corrupt is not None:
            raise RuntimeError('IWD CRC failed on ' + corrupt)
        packaged = set(archive.namelist())
        if not set(REQUIRED).issubset(packaged):
            raise RuntimeError('Critical GSC files missing from IWD')
    return {
        'archive_filename': dest.name,
        'member_count': len(names),
        'sha256': hashlib.sha256(dest.read_bytes()).hexdigest(),
        'crc_verified': True,
        'runtime_mod_ff': False,
        'generated_only_locally': True,
    }


def audit(root: Path, inventory: set[str] | None = None, output_iwd: Path | None = None) -> dict:
    paths = inventory if inventory is not None else git_tree_paths(root)
    report = source_audit(root, paths)
    report['iwd_archive'] = None
    if output_iwd is not None and report['script_iwd_source_gate']:
        report['iwd_archive'] = make_iwd(root, output_iwd, paths)
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--rotu', type=Path, required=True)
    ap.add_argument('--output', type=Path)
    ap.add_argument('--iwd-temp', type=Path, help='Temporary local output only. Never publish archive.')
    ap.add_argument('--strict', action='store_true', help='Require a verified source-script IWD')
    args = ap.parse_args()
    report = audit(args.rotu, output_iwd=args.iwd_temp)
    data = json.dumps(report, ensure_ascii=False, indent=2)
    print(data)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(data + '\n', encoding='utf-8')
    passed = report['script_iwd_source_gate'] and (
        args.iwd_temp is None or report['iwd_archive'] is not None)
    return 0 if (passed or not args.strict) else 1


if __name__ == '__main__':
    sys.exit(main())
