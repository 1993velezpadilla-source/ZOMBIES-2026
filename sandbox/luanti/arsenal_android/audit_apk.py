"""Fail-closed structural audit for a Luanti Arsenal Android APK.

This checks real nested APK bytes against a full external catalog. It does not
prove audio timing, runtime controls, Android installation or actual device FPS.
"""
import argparse
from collections import Counter
from io import BytesIO
import hashlib
import json
from pathlib import Path
import posixpath
import struct
from zipfile import BadZipFile, ZipFile

MODEL_EXTENSIONS = ('.glb', '.gltf', '.b3d', '.obj')
CATEGORIES = {'assault', 'pistol', 'smg', 'shotgun', 'sniper', 'lmg', 'marksman'}
MAX_UNCOMPRESSED_ASSET = 32 * 1024 * 1024
MAX_ASSET_COUNT = 20000


class AuditError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise AuditError(message)


def clean_path(path):
    require(isinstance(path, str) and path, f'invalid asset path: {path!r}')
    require('\\' not in path and not path.startswith('/'), f'unsafe asset path: {path}')
    require(posixpath.normpath(path) == path and '..' not in path.split('/'),
            f'unsafe asset path: {path}')
    return path


def check_zip(z, label):
    names = z.namelist()
    require(len(names) <= MAX_ASSET_COUNT, f'{label}: too many files')
    require(len(names) == len(set(names)), f'{label}: duplicate ZIP names')
    for info in z.infolist():
        clean_path(info.filename.rstrip('/'))
        require(info.file_size <= MAX_UNCOMPRESSED_ASSET or
                (label == 'APK' and info.filename == 'assets/assets.zip'),
                f'{label}: oversized entry {info.filename}')
    return set(names)


def parse_glb(blob, path):
    require(len(blob) >= 20 and blob[:4] == b'glTF', f'{path}: not GLB')
    version, total = struct.unpack_from('<II', blob, 4)
    require(version == 2 and total == len(blob), f'{path}: malformed GLB header')
    json_len, kind = struct.unpack_from('<I4s', blob, 12)
    require(kind == b'JSON' and json_len <= len(blob) - 20,
            f'{path}: missing JSON chunk')
    doc = json.loads(blob[20:20 + json_len].decode('utf-8'))
    require(isinstance(doc.get('meshes'), list) and doc['meshes'],
            f'{path}: no mesh')
    return {a.get('name', '') for a in doc.get('animations', [])
            if isinstance(a, dict)}


def inspect(apk, catalog, expected_weapons=28, expected_models=95,
            expected_configurations=184):
    require(catalog.get('schema_version') == 1, 'catalog: unsupported schema_version')
    weapons = catalog.get('weapons')
    models = catalog.get('models')
    configs = catalog.get('configurations')
    require(isinstance(weapons, list) and len(weapons) == expected_weapons,
            f'weapons: expected {expected_weapons}, got '
            f'{len(weapons) if isinstance(weapons, list) else "invalid"}')
    require(isinstance(models, list) and len(models) == expected_models,
            f'models: expected {expected_models}, got '
            f'{len(models) if isinstance(models, list) else "invalid"}')
    require(isinstance(configs, list) and len(configs) == expected_configurations,
            f'configurations: expected {expected_configurations}, got '
            f'{len(configs) if isinstance(configs, list) else "invalid"}')
    model_paths = [clean_path(m) for m in models]
    require(len(set(model_paths)) == len(model_paths), 'models: duplicate paths')
    require(all(m.lower().endswith(MODEL_EXTENSIONS) for m in model_paths),
            'models: unsupported formats')
    weapon_ids = [w.get('id') for w in weapons]
    require(all(isinstance(w, str) and w for w in weapon_ids),
            'weapons: missing id')
    require(len(set(weapon_ids)) == len(weapon_ids), 'weapons: duplicate ids')
    declared = set(weapon_ids)
    cfg_keys = []
    for w in weapons:
        require(w.get('category') in CATEGORIES, f'weapon {w["id"]}: invalid category')
        m = clean_path(w.get('model'))
        require(m in model_paths, f'weapon {w["id"]}: undeclared model {m}')
        anim = w.get('animations')
        require(isinstance(anim, list) and len(anim) >= 2 and
                all(isinstance(x, str) and x for x in anim),
                f'weapon {w["id"]}: missing animation requirements')
        require(len(set(anim)) == len(anim),
                f'weapon {w["id"]}: duplicate animation names')
        for p in w.get('textures', []) + w.get('sounds', []):
            clean_path(p)
    for c in configs:
        require(c.get('weapon') in declared,
                f'configuration references unknown weapon: {c}')
        attachments = c.get('attachments')
        require(isinstance(attachments, list) and
                all(isinstance(x, str) and x for x in attachments),
                f'configuration attachments invalid: {c}')
        require(len(set(attachments)) == len(attachments),
                f'duplicate attachment in {c}')
        ident = c.get('id')
        require(isinstance(ident, str) and ident,
                f'configuration missing id: {c}')
        cfg_keys.append(ident)
        if 'model' in c:
            require(clean_path(c['model']) in model_paths,
                    f'configuration model not declared: {ident}')
    require(len(set(cfg_keys)) == len(cfg_keys),
            'configurations: duplicate ids')

    with ZipFile(apk) as outer:
        outer_names = check_zip(outer, 'APK')
        require('AndroidManifest.xml' in outer_names,
                'APK: AndroidManifest.xml absent')
        require(any(n.startswith('lib/arm64-v8a/') and n.endswith('.so')
                    for n in outer_names), 'APK: ARM64 native library absent')
        require('assets/assets.zip' in outer_names,
                'APK: Luanti assets/assets.zip absent')
        with ZipFile(BytesIO(outer.read('assets/assets.zip'))) as assets:
            asset_names = check_zip(assets, 'nested assets')
            require(all(m in asset_names for m in model_paths),
                    f'missing models: {sorted(set(model_paths)-asset_names)[:8]}')
            checked_animation_models = {}
            for w in weapons:
                p = w['model']
                if p not in checked_animation_models:
                    require(p.endswith('.glb'),
                            f'weapon {w["id"]}: animated primary model must be GLB')
                    checked_animation_models[p] = parse_glb(assets.read(p), p)
                missing = set(w['animations']) - checked_animation_models[p]
                require(not missing,
                        f'weapon {w["id"]}: model missing declared animation clips '
                        f'{sorted(missing)}')
                for path in w.get('textures', []) + w.get('sounds', []):
                    require(path in asset_names,
                            f'weapon {w["id"]}: missing resource {path}')
                    data = assets.read(path)
                    if path.endswith('.png'):
                        require(data.startswith(b'\x89PNG\r\n\x1a\n'),
                                f'not PNG: {path}')
                    if path.endswith('.ogg'):
                        require(data.startswith(b'OggS'), f'not OGG: {path}')
            for path in model_paths:
                require(assets.getinfo(path).file_size > 0, f'model empty: {path}')
                if path.endswith('.glb') and path not in checked_animation_models:
                    parse_glb(assets.read(path), path)
    digest = hashlib.sha256(apk.read_bytes()).hexdigest()
    return {
        'apk': apk.name, 'apk_sha256': digest,
        'weapons_declared_and_present': len(weapons),
        'models_present': len(models),
        'configurations_declared': len(configs),
        'primary_animated_models_checked': len(checked_animation_models),
        'categories': dict(Counter(w['category'] for w in weapons)),
        'static_apk_structure': 'PASS', 'glb_animation_names': 'PASS',
        'signature_verified': False, 'runtime_equipping_verified': False,
        'universal_ammo_refill_verified': False,
        'attachment_combinations_verified': False,
        'device_ads_verified': False, 'device_fps_verified': False,
        'commercial_distribution_cleared': False
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('apk', type=Path)
    p.add_argument('--catalog', type=Path, required=True)
    p.add_argument('--expected-weapons', type=int, default=28)
    p.add_argument('--expected-models', type=int, default=95)
    p.add_argument('--expected-configurations', type=int, default=184)
    p.add_argument('--report', type=Path)
    args = p.parse_args()
    try:
        catalog = json.loads(args.catalog.read_text(encoding='utf-8'))
        result = inspect(args.apk, catalog, args.expected_weapons,
                         args.expected_models, args.expected_configurations)
    except (AuditError, OSError, BadZipFile, KeyError, TypeError,
            json.JSONDecodeError) as exc:
        p.exit(2, f'ARSENAL_APK_AUDIT_FAILED: {exc}\n')
    output = json.dumps(result, indent=2, sort_keys=True) + '\n'
    if args.report:
        args.report.write_text(output, encoding='utf-8')
    print(output, end='')


if __name__ == '__main__':
    main()
