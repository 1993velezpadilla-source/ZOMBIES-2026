#!/usr/bin/env python3
"""Read-only, static inventory of ZOMBIES-2026 release archives.

Neither APK nor ZIP contents are executed or extracted. C4's four parts are
read via a virtual seekable stream, avoiding 14 GB of temporary storage.
"""
from __future__ import annotations
import bisect
from collections import Counter, defaultdict
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import struct
import sys
import zipfile

OUT = Path("docs/audit")
OUT.mkdir(parents=True, exist_ok=True)
PARTS = sorted(Path("_release_assets/c4").glob("C4-Mocs.zip.part-*"))
APK = Path("_release_assets/cod4/COD4.apk")
SOURCE_ZIP_BYTES = 7021386357
SOURCE_APK_BYTES = 51760726
ZIP_SHA256 = "6787f2082b39ee76445db7fca92892256bfb97e62bbdebfe63f6ee11de6a8d99"
APK_SHA256 = "40386503d564b0985423339b5ccd5611dc60ce08ebe1b4ae494d4de22a62473c"
ASSET_TYPES = {
    "godot": {".gd", ".tscn", ".tres", ".gdextension", ".godot", ".gdshader"},
    "models": {".glb", ".gltf", ".fbx", ".obj", ".blend", ".dae", ".stl", ".3ds"},
    "animation": {".anim", ".xanim", ".smd", ".vta", ".dmx", ".bvh"},
    "textures": {".png", ".jpg", ".jpeg", ".webp", ".tga", ".dds", ".iwi", ".ktx", ".ktx2", ".exr", ".bmp"},
    "audio": {".wav", ".mp3", ".ogg", ".flac", ".wem", ".fsb", ".mp4", ".opus", ".bank"},
    "unreal": {".uasset", ".umap", ".uexp", ".ubulk", ".pak", ".utoc", ".ucas"},
    "cod_legacy": {".iwd", ".ff", ".iwi", ".xmodel", ".xanim", ".xmaterial", ".ximage", ".gsc", ".cfg"},
    "code_and_config": {".gd", ".cs", ".cpp", ".h", ".hpp", ".py", ".java", ".kt", ".xml", ".json", ".ini", ".cfg", ".yaml", ".yml"},
}
TEXT_EXTS = {".txt", ".json", ".xml", ".ini", ".cfg", ".md", ".csv", ".yaml", ".yml", ".gd", ".cs", ".py", ".gsc", ".bat", ".sh", ".properties", ".gradle"}
INTERESTING = re.compile(r"(^|/)(project\.godot|androidmanifest\.xml|.*\.tscn|.*\.gd|.*\.uproject|.*\.umap|.*\.pak|.*\.iwd|.*\.ff|.*\.gsc|.*\.xmodel|.*\.glb|.*\.gltf|.*\.fbx|.*\.blend|.*\.uasset|.*\.so|.*\.dex)$", re.I)

class SplitReader:
    """Seekable virtual file over consecutive binary parts."""
    def __init__(self, paths):
        if not paths:
            raise RuntimeError("No ZIP parts downloaded")
        self.files = [open(p, "rb") for p in paths]
        self.limits = [0]
        for p in paths:
            self.limits.append(self.limits[-1] + p.stat().st_size)
        self.pos = 0

    def seek(self, offset, whence=0):
        if whence == 0:
            self.pos = offset
        elif whence == 1:
            self.pos += offset
        elif whence == 2:
            self.pos = self.limits[-1] + offset
        else:
            raise ValueError("invalid whence")
        if self.pos < 0:
            raise ValueError("negative offset")
        return self.pos

    def tell(self):
        return self.pos

    def read(self, n=-1):
        if n is None or n < 0:
            n = self.limits[-1] - self.pos
        n = min(n, max(0, self.limits[-1] - self.pos))
        chunks = []
        while n:
            part = bisect.bisect_right(self.limits, self.pos) - 1
            amount = min(n, self.limits[part+1] - self.pos)
            self.files[part].seek(self.pos-self.limits[part])
            data = self.files[part].read(amount)
            if not data:
                break
            chunks.append(data)
            self.pos += len(data)
            n -= len(data)
        return b"".join(chunks)

    def close(self):
        for f in self.files:
            f.close()

def sum_sha256(paths):
    d = hashlib.sha256()
    bytes_read = 0
    for path in paths:
        with open(path, "rb") as f:
            for piece in iter(lambda: f.read(8 * 1024 * 1024), b""):
                d.update(piece)
                bytes_read += len(piece)
    return d.hexdigest(), bytes_read

def format_size(n):
    return f"{n:,} bytes ({n / (1024 * 1024):,.2f} MiB)"

def clean_path(name):
    return name.replace("\\", "/")

def is_unsafe(name):
    q = clean_path(name)
    return q.startswith("/") or bool(re.match(r"^[a-zA-Z]:", q)) or ".." in PurePosixPath(q).parts or "\x00" in q

def tally_zip(label, z):
    infos = z.infolist()
    types = Counter()
    roots = Counter()
    root_uncompressed = Counter()
    category_counts = Counter()
    unsafe = []
    encrypted = []
    suspicious = []
    exact_dupes = []
    seen = set()
    rows = []
    compressed = 0
    uncompressed = 0
    for i in infos:
        name = i.filename
        if i.is_dir():
            continue
        p = PurePosixPath(clean_path(name))
        suffix = p.suffix.lower() or "[none]"
        root = p.parts[0] if p.parts else "[root]"
        types[suffix] += 1
        roots[root] += 1
        root_uncompressed[root] += i.file_size
        compressed += i.compress_size
        uncompressed += i.file_size
        for cat, ext in ASSET_TYPES.items():
            if suffix in ext:
                category_counts[cat] += 1
        if name in seen and len(exact_dupes) < 50:
            exact_dupes.append(name)
        seen.add(name)
        if is_unsafe(name):
            if len(unsafe) < 50:
                unsafe.append(name)
        if i.flag_bits & 1:
            if len(encrypted) < 50:
                encrypted.append(name)
        if INTERESTING.search(name) and len(suspicious) < 200:
            suspicious.append(name)
        rows.append({
            "path": name,
            "bytes": i.file_size,
            "compressed_bytes": i.compress_size,
            "crc32_hex": f"{i.CRC:08x}",
            "method": i.compress_type,
            "encrypted": bool(i.flag_bits & 1),
        })
    rows.sort(key=lambda x: x["path"].lower())
    (OUT / f"{label}-file-inventory.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
    return {
        "label": label,
        "entries_total": len(infos),
        "files": len(rows),
        "directories": len(infos)-len(rows),
        "uncompressed_bytes": uncompressed,
        "compressed_entry_bytes": compressed,
        "extensions": dict(types.most_common()),
        "asset_categories": dict(category_counts.most_common()),
        "top_directories": [
            {"name": name, "files": count, "uncompressed_bytes": root_uncompressed[name]}
            for name, count in roots.most_common(50)
        ],
        "largest": sorted(rows, key=lambda x:x["bytes"], reverse=True)[:35],
        "unsafe_path_examples": unsafe,
        "encrypted_entry_examples": encrypted,
        "duplicate_entry_examples": exact_dupes,
        "interesting_names": suspicious,
        "file_inventory_path": f"docs/audit/{label}-file-inventory.json",
    }

def preview_relevant(z):
    names = z.namelist()
    out = []
    limited_files = 0
    for name in names:
        if limited_files >= 30:
            break
        p = PurePosixPath(name)
        low = name.lower()
        if (p.name.lower() in {"project.godot", "readme.md", "readme.txt", "manifest.json", "package.json"}
            or low.endswith((".uproject", ".gdextension"))
            or (low.endswith((".gsc", ".cfg", ".gd", ".json")) and len(name) < 180)):
            item = z.getinfo(name)
            if item.file_size > 100_000 or item.flag_bits & 1:
                continue
            try:
                raw = z.read(name)
                preview = raw.decode("utf-8", errors="replace")[:1200]
            except Exception:
                continue
            # Previews only in local artifact (not public report), avoid printing config contents.
            out.append({"path":name, "bytes":item.file_size,
                        "sample_text":preview})
            limited_files += 1
    # Do not publish raw contents of untrusted files / potential secrets.
    (OUT / "c4-small-text-file-paths.json").write_text(json.dumps([
        {"path":x["path"],"bytes":x["bytes"]} for x in out
    ],ensure_ascii=False,indent=2)+"\n")
    return len(out)

def analyze_apk(path):
    apk_info = {}
    try:
        from androguard.core.apk import APK
        obj = APK(str(path))
        def value(call):
            try:
                result = call()
                if isinstance(result, (list, set, tuple)):
                    return sorted(str(v) for v in result)[:100]
                return str(result) if result is not None else None
            except Exception as e:
                return f"unavailable: {type(e).__name__}"
        apk_info = {
            "package": value(obj.get_package),
            "app_name": value(obj.get_app_name),
            "version_name": value(obj.get_androidversion_name),
            "version_code": value(obj.get_androidversion_code),
            "min_sdk": value(obj.get_min_sdk_version),
            "target_sdk": value(obj.get_target_sdk_version),
            "permissions": value(obj.get_permissions),
            "activities": value(obj.get_activities),
            "services": value(obj.get_services),
            "receivers": value(obj.get_receivers),
            "providers": value(obj.get_providers),
            "main_activity": value(obj.get_main_activity),
            "signature": {"v1":value(obj.is_signed_v1),"v2":value(obj.is_signed_v2),"v3":value(obj.is_signed_v3)},
        }
    except Exception as e:
        apk_info["metadata_error"] = f"{type(e).__name__}: {str(e)[:200]}"
    return apk_info

def md_table(cols, rows):
    def cell(x):
        return str(x).replace("|","\\|").replace("\n"," ")
    return "| " + " | ".join(cols) + " |\n| " + " | ".join(["---"]*len(cols))+" |\n" + "".join("| " + " | ".join(cell(v) for v in row) + " |\n" for row in rows)

def main():
    if [p.name for p in PARTS] != [f"C4-Mocs.zip.part-{n:03d}" for n in range(4)]:
        raise RuntimeError(f"Expected 4 sequential ZIP parts, found {[p.name for p in PARTS]}")
    if not APK.exists():
        raise RuntimeError("COD4.apk not downloaded")
    print("Verifying SHA-256 of original 7 GB split archive...", flush=True)
    zip_sha, zip_bytes = sum_sha256(PARTS)
    apk_sha, apk_bytes = sum_sha256([APK])
    checks = {
        "c4_sha256": zip_sha, "c4_expected_sha256": ZIP_SHA256,
        "c4_bytes": zip_bytes, "c4_expected_bytes": SOURCE_ZIP_BYTES,
        "apk_sha256": apk_sha, "apk_expected_sha256": APK_SHA256,
        "apk_bytes": apk_bytes, "apk_expected_bytes": SOURCE_APK_BYTES
    }
    if zip_sha != ZIP_SHA256 or zip_bytes != SOURCE_ZIP_BYTES:
        raise RuntimeError(f"C4 archive hash or size mismatch: {checks}")
    if apk_sha != APK_SHA256 or apk_bytes != SOURCE_APK_BYTES:
        raise RuntimeError(f"APK hash or size mismatch: {checks}")
    print("Both originals verified against original import manifests", flush=True)

    reader = SplitReader(PARTS)
    try:
        with zipfile.ZipFile(reader, "r", allowZip64=True) as z:
            c4 = tally_zip("c4-mocs", z)
            c4["zip_integrity_test"] = "Central directory parsed; full entry-by-entry CRC not performed"
            c4["text_preview_candidates"] = preview_relevant(z)
    finally:
        reader.close()
    with zipfile.ZipFile(APK, "r") as z:
        app = tally_zip("cod4-apk", z)
        app["zip_integrity_test"] = "Central directory parsed; full entry-by-entry CRC not performed"
    app["android_metadata"] = analyze_apk(APK)
    names = {row["path"].lower() for row in json.loads((OUT/"cod4-apk-file-inventory.json").read_text())}
    app["game_engine_signatures"] = {
        "unity": any("libunity.so" in x or "assets/bin/data" in x for x in names),
        "unreal": any("libue4.so" in x or "libunreal.so" in x or x.endswith(".pak") or x.endswith(".utoc") for x in names),
        "godot": any("libgodot" in x or x.endswith("project.godot") or ".pck" in x for x in names),
        "cocos": any("libcocos2d" in x for x in names),
    }

    data = {"validation":checks, "c4":c4, "apk":app}
    (OUT/"audit-data.json").write_text(json.dumps(data, indent=2, ensure_ascii=False)+"\n")

    sections = [
        "# ZOMBIES-2026 — static asset audit",
        "",
        "**Method:** Read-only inspection of GitHub release binaries; no APK installation, execution, scene import, or complete decompression.",
        "**Integrity:** Original archive byte sizes and SHA-256 match the import manifests (both PASS).",
        "",
        "## C4-Mocs.zip",
        f"- Archive bytes: {format_size(zip_bytes)}; stored in {len(PARTS)} GitHub Release parts.",
        f"- ZIP entries: {c4['entries_total']:,}; files: {c4['files']:,}; dirs: {c4['directories']:,}.",
        f"- Declared total uncompressed size: {format_size(c4['uncompressed_bytes'])}.",
        f"- Declared total compressed entry bytes: {format_size(c4['compressed_entry_bytes'])}.",
        f"- Encrypted examples: {len(c4['encrypted_entry_examples'])}; path traversal examples: {len(c4['unsafe_path_examples'])}; duplicate entry examples: {len(c4['duplicate_entry_examples'])}.",
        "- ZIP CRC validation: **not performed for every file**; listing and central directory parsed.",
        "",
        "### Largest extension groups",
        md_table(["Extension","Files"], list(c4["extensions"].items())[:35]),
        "### High-level asset categories (overlapping)",
        md_table(["Category","Files"], list(c4["asset_categories"].items())),
        "### Largest files inside C4",
        md_table(["Path","Uncompressed bytes","Compressed bytes"], [(x["path"], x["bytes"],x["compressed_bytes"]) for x in c4["largest"][:20]]),
        "### Top-level directories",
        md_table(["Directory","Files","Declared uncompressed bytes"], [(x["name"],x["files"],x["uncompressed_bytes"]) for x in c4["top_directories"][:30]]),
        "",
        "## COD4.apk",
        f"- APK bytes: {format_size(apk_bytes)}.",
        f"- ZIP entries: {app['entries_total']:,}; files: {app['files']:,}.",
        f"- Declared total uncompressed size: {format_size(app['uncompressed_bytes'])}.",
        "- APK is a ZIP container; this alone does NOT prove authenticity, safe installation, proper licensing, or full game source.",
        "### Android package metadata",
        md_table(["Field","Value"], [(k, ", ".join(v) if isinstance(v,list) else v) for k,v in app["android_metadata"].items() if k not in ("permissions","activities","services","receivers","providers")]),
        "### Requested Android permissions",
        "\n".join("- `"+p+"`" for p in app["android_metadata"].get("permissions", []) if isinstance(p,str)) if isinstance(app["android_metadata"].get("permissions"),list) else "(Unavailable)",
        "### APK extension groups",
        md_table(["Extension","Files"],list(app["extensions"].items())[:35]),
        "### APK engine signatures (heuristics only)",
        md_table(["Engine","Signature detected"],[(k,str(v)) for k,v in app["game_engine_signatures"].items()]),
        "### APK largest entries",
        md_table(["Path","Uncompressed bytes"],[(x["path"],x["bytes"]) for x in app["largest"][:20]]),
        "",
        "## Compatibility and next steps",
        "- Unreal/Godot coordinate transforms cannot be validated from archive names alone. Verify source units, handedness, forward axis, pivot and transforms on individual asset specimens.",
        "- Static APK metadata cannot prove that assets, map layouts, animations or control systems can be imported into Godot.",
        "- Before reusing third-party game assets, confirm rights and license; this audit does not grant permission.",
        "- Detailed file-by-file ZIP inventories: [C4](c4-mocs-file-inventory.json), [APK](cod4-apk-file-inventory.json).",
        "- Complete JSON audit metadata: [audit-data.json](audit-data.json).",
    ]
    (OUT/"README.md").write_text("\n".join(sections)+"\n")
    print("AUDIT COMPLETE:", json.dumps({
        "c4_files":c4["files"],"c4_bytes":zip_bytes,"c4_exts":list(c4["extensions"].items())[:12],
        "apk_files":app["files"],"apk_bytes":apk_bytes, "apk_package":app["android_metadata"].get("package"),
        "engine_signatures":app["game_engine_signatures"]
    }), flush=True)

if __name__ == "__main__":
    main()
