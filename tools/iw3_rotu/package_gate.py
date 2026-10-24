#!/usr/bin/env python3
"""Audit RotU fastfile manifests and prepare an *unpublished* source-only overlay.

The overlay is not a compiled mod.ff, not a valid standalone game, and never
downloads or packages COD4 commercial data, xmodels, animations, or game audio.
"""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

ACTIVE_INCLUDE = re.compile(r'^\s*include\s*,\s*mod_scripts\s*$', re.I)
COMMENTED_INCLUDE = re.compile(r'^(\s*)//\s*include\s*,\s*mod_scripts\s*$', re.I)
COMPILED_SCRIPT = ('.gsc', '.gsx')
KNOWN_MANIFEST_ASSETS = {'fx', 'xmodel', 'xanim', 'weapon', 'sound', 'material', 'localize', 'menufile', 'stringtable'}


def read_manifest(filename: Path) -> list[tuple[str, str]]:
    rows = []
    for line in filename.read_text(encoding='utf-8', errors='replace').splitlines():
        item = line.strip()
        if not item or item.startswith('//') or item.startswith('#'):
            continue
        parts = [p.strip() for p in item.split(',')]
        if len(parts) >= 2 and parts[0] and parts[1]:
            rows.append((parts[0].lower(), parts[1]))
    return rows


def repo_files(root: Path) -> set[str]:
    result = subprocess.run(
        ['git', '-C', str(root), 'ls-tree', '--name-only', '-r', 'HEAD'],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True,
        timeout=30,
    )
    return {p.strip() for p in result.stdout.splitlines() if p.strip()}


def activate_scripts_include(content: str) -> tuple[str, str]:
    lines = content.splitlines(keepends=True)
    active = [i for i, line in enumerate(lines) if ACTIVE_INCLUDE.fullmatch(line.strip())]
    if len(active) == 1:
        return content, 'already_active'
    if len(active) > 1:
        raise ValueError('Multiple active include,mod_scripts statements')
    candidates = [i for i, line in enumerate(lines) if COMMENTED_INCLUDE.fullmatch(line.strip())]
    if len(candidates) != 1:
        raise ValueError('Expected exactly one commented include,mod_scripts statement to activate')
    i = candidates[0]
    newline = '\r\n' if lines[i].endswith('\r\n') else '\n' if lines[i].endswith('\n') else ''
    lines[i] = 'include,mod_scripts' + newline
    return ''.join(lines), 'activated_in_overlay'


def audit(rotu: Path, files: set[str] | None = None, stage: Path | None = None) -> dict:
    mod = rotu / 'mod.csv'
    scripts = rotu / 'mod_scripts.csv'
    if not mod.is_file() or not scripts.is_file():
        raise FileNotFoundError('Both mod.csv and mod_scripts.csv are required')
    contents = mod.read_text(encoding='utf-8', errors='replace')
    rows = read_manifest(mod)
    script_rows = read_manifest(scripts)
    script_paths = [p for kind, p in script_rows if kind == 'rawfile']
    # Inspect the full Git tree, not the sparse-checkout working tree.
    all_files = files if files is not None else repo_files(rotu)
    missing_script = sorted({p for p in script_paths if p not in all_files})
    rawfiles = [p for kind, p in rows if kind == 'rawfile']
    unresolved_raw = sorted({p for p in rawfiles if p not in all_files})
    missing_mod_gsc = [p for p in unresolved_raw if p.lower().endswith(COMPILED_SCRIPT)]
    gametype_hooks = [p for p in rawfiles if p.startswith('maps/mp/gametypes/') and p.endswith('.gsc')]
    asset_references = {kind: sum(1 for k, _ in rows if k == kind) for kind in KNOWN_MANIFEST_ASSETS}
    custom_compiler_refs = sorted(p for p in script_paths if p.lower().endswith('.gsx'))
    staged_content = None
    stage_result = None
    stage_error = None
    try:
        staged_content, stage_result = activate_scripts_include(contents)
    except ValueError as exc:
        stage_error = str(exc)
    if stage is not None and staged_content is not None:
        stage.mkdir(parents=True, exist_ok=True)
        (stage / 'mod.csv').write_text(staged_content, encoding='utf-8')
        (stage / 'mod_scripts.csv').write_text(scripts.read_text('utf-8', errors='replace'), encoding='utf-8')
    staging_source_ready = bool(
        staged_content is not None and script_paths and not missing_script
        and gametype_hooks and not missing_mod_gsc
    )
    return {
        'schema_version': 1,
        'upstream_source_only': True,
        'mod_scripts_include_originally_active': ('include', 'mod_scripts') in rows,
        'staging_overlay_status': stage_result,
        'staging_error': stage_error,
        'script_manifest_count': len(script_paths),
        'missing_script_manifest_files': missing_script,
        'mod_rawfile_count': len(rawfiles),
        'rawfiles_not_present_in_upstream_git_tree': unresolved_raw,
        'unresolved_gametype_script_paths': missing_mod_gsc,
        'gametype_entrypoints_listed': gametype_hooks,
        'nonstandard_gsx_scripts': custom_compiler_refs,
        'asset_references_by_type': dict(sorted(asset_references.items())),
        'staging_source_ready': staging_source_ready,
        'mod_fastfile_compiled': False,
        'live_zombie_verified': False,
        'asset_dependencies_verified': False,
        'authorized_cod4_data_present': False,
        'note': ('Tree absence is not conclusive if a required resource comes from a '
                 'separately authorized COD4 installation or mod asset pack. '
                 'Staging includes only CSV manifests. No source, assets, DLLs, or .ff files published.'),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--rotu', type=Path, required=True)
    ap.add_argument('--output', type=Path)
    ap.add_argument('--stage', type=Path, help='Generate an ephemeral two-file CSV overlay; no assets or binaries.')
    ap.add_argument('--strict-staging', action='store_true',
                    help='Exit nonzero if overlay cannot be staged due to known missing script paths')
    a = ap.parse_args()
    report = audit(a.rotu, stage=a.stage)
    data = json.dumps(report, indent=2, ensure_ascii=False)
    print(data)
    if a.output:
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(data + '\n', encoding='utf-8')
    return 1 if a.strict_staging and not report['staging_source_ready'] else 0


if __name__ == '__main__':
    sys.exit(main())
