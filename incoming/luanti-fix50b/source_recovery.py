#!/usr/bin/env python3
"""Read-only forensic recovery of the exact missing FIX49C COD4 source headers.

This is NOT a native-code reconstruction. A successful match must come from
the working APK itself or a source archive embedded within it.
"""
import hashlib
import json
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

WANTED = {"weapon_bridge.h", "weapon_hud.h", "native_attachment_override.h"}
REPORT = Path("fix50b-recovery-report")
REPORT.mkdir(exist_ok=True)
FOUND = {}
SEEN = []
ARCHIVES = []

def visit(archive_path, prefix="", depth=0):
    if depth > 3:
        return
    try:
        with zipfile.ZipFile(archive_path) as archive:
            for info in archive.infolist():
                name = info.filename
                logical = prefix + name
                base = Path(name).name
                if base in WANTED:
                    body = archive.read(info)
                    digest = hashlib.sha256(body).hexdigest()
                    if len(body) >= 32 and b"\x00" not in body[:128]:
                        if base in FOUND and FOUND[base]["sha256"] != digest:
                            raise RuntimeError("Conflicting originals for " + base)
                        dst = REPORT / "original_headers" / base
                        dst.parent.mkdir(parents=True, exist_ok=True)
                        dst.write_bytes(body)
                        FOUND[base] = {"location": logical, "bytes": len(body), "sha256": digest}
                if logical.lower().endswith((".h", ".hpp", ".cpp", ".patch", ".diff")):
                    SEEN.append(logical)
                if depth < 3 and name.lower().endswith((".zip", ".jar", ".apk")) and info.file_size <= 800_000_000:
                    ARCHIVES.append({"path": logical, "size": info.file_size})
                    with tempfile.TemporaryFile() as tmp:
                        with archive.open(info) as f:
                            shutil.copyfileobj(f, tmp, length=8*1024*1024)
                        tmp.seek(0)
                        if zipfile.is_zipfile(tmp):
                            visit(tmp, logical + "::", depth + 1)
    except (OSError, zipfile.BadZipFile) as exc:
        print("Archive scan skipped:", prefix, str(exc), flush=True)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: source_recovery.py <known-working-FIX49C.apk>")
    apk = Path(sys.argv[1])
    if not apk.is_file():
        raise SystemExit("FIX49C source APK missing: " + str(apk))
    with zipfile.ZipFile(apk) as z:
        names = set(z.namelist())
        if "lib/arm64-v8a/libluanti.so" not in names:
            raise SystemExit("Not a working Android ARM64 Luanti APK")
        lib = z.read("lib/arm64-v8a/libluanti.so")
        markers = ("[weapon_bridge]", "ak47_hip_idle", "isAK47Aiming")
        marker_state = {x: x.encode() in lib for x in markers}
    visit(apk)
    missing = sorted(WANTED - set(FOUND))
    report = {
        "apk": apk.name, "native_marker_present": marker_state,
        "verified_header_matches": FOUND, "missing_header_names": missing,
        "nested_archives_examined": ARCHIVES,
        "source_paths_found": SEEN[:300],
        "conclusion": "SOURCE_RECOVERED" if not missing else "SOURCE_NOT_IN_PACKAGED_APK",
    }
    (REPORT / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(json.dumps({key: report[key] for key in ("native_marker_present","verified_header_matches","missing_header_names","conclusion")}, indent=2), flush=True)
    if missing:
        print("FAIL CLOSED: never fabricate source headers or ship a stripped COD4 engine.", flush=True)
        sys.exit(2)
