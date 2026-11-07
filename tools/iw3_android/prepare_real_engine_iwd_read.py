#!/usr/bin/env python3
"""Stage and audit the ORIGINAL IW3 file-handle lifecycle for the Android port.

This is the next integration gate after the lookup-only probe. It extracts the
vendored KisakCOD FS_HandleForFile, FS_FOpenFileReadForThread, FS_Read and
FS_FCloseFile bodies verbatim into an audit artifact. The artifact is not yet
linked into the diagnostic APK: Android ABI/service dependencies must be
resolved before enabling it in the runtime.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:
    from tools.iw3_android.prepare_g_runframe_prereqs import function_source
except ModuleNotFoundError:
    from prepare_g_runframe_prereqs import function_source

SOURCE = Path("src/universal/com_files.cpp")
FUNCTIONS = (
    "int __cdecl FS_HandleForFile(FsThread thread)",
    "void __cdecl FS_FCloseFile(int h)",
    "uint32_t __cdecl FS_FOpenFileReadForThread(const char *filename, int *file, FsThread thread)",
    "uint32_t __cdecl FS_Read(uint8_t *buffer, uint32_t len, int h)",
)
REQUIRED = (
    "fsh[i + first].handleFiles.file.o",
    "*file = FS_HandleForFile(thread);",
    "unzReOpen(iwd->iwdFilename, iwd->handle)",
    "unzOpenCurrentFile(fsh[*file].handleFiles.file.z);",
    "const int zipRead = unzReadCurrentFile(fsh[h].handleFiles.file.z, buffer, len);",
    "zipRead < 0 || static_cast<uint32_t>(zipRead) > len",
    "return UINT32_MAX;",
    "FS_FileForHandle(h)",
    "unzCloseCurrentFile(fsh[h].handleFiles.file.z);",
    "fsh[h].handleFiles.iwdIsClone",
    "Com_Memcpy((char *)zfi, (char *)iwd->handle, sizeof(*zfi));",
)
FORBIDDEN = (
    "z2026_iw3_original_searchpath_lookup",
    "return -1; // non-null handle path is intentionally outside this probe",
    "Com_Memcpy((char *)zfi, (char *)iwd->handle, 128);",
)

def prepare(engine: Path, output: Path, report_path: Path | None = None) -> dict:
    engine = engine.resolve()
    source_path = engine / SOURCE
    output = output.resolve()
    if output == source_path:
        raise ValueError("Refusing to overwrite authentic KisakCOD com_files.cpp")
    raw = source_path.read_bytes()
    source = raw.decode("utf-8")
    bodies = [function_source(source, signature) for signature in FUNCTIONS]
    combined = "\n\n".join(bodies) + "\n"
    for marker in REQUIRED:
        if marker not in combined:
            raise ValueError("Original file lifecycle contract missing: " + marker)
    for marker in FORBIDDEN:
        if marker in combined:
            raise ValueError("Lookup-only adapter leaked into original lifecycle")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        "// AUDIT ARTIFACT: exact original KisakCOD function bodies.\n"
        "// Not linked into Android runtime until ABI/service audit passes.\n"
        + combined, encoding="utf-8")
    if source_path.read_bytes() != raw:
        raise RuntimeError("Vendored original changed during staging")
    evidence = {
        "source": str(SOURCE),
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "function_signatures": list(FUNCTIONS),
        "function_body_sha256": {
            signature: hashlib.sha256(body.encode("utf-8")).hexdigest()
            for signature, body in zip(FUNCTIONS, bodies)
        },
        "original_handle_allocation_body_staged_verbatim": True,
        "original_FS_FOpenFileReadForThread_body_staged_verbatim": True,
        "original_FS_Read_body_staged_verbatim": True,
        "original_FS_FCloseFile_body_staged_verbatim": True,
        "android_abi_and_service_linkage_proven": False,
        "runtime_handle_path_executed": False,
        "real_game_assets_loaded": False,
        "gameplay_proven": False,
        "playable_apk": False,
    }
    if report_path is not None:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n",
                               encoding="utf-8")
    return evidence

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    report = prepare(args.engine, args.output, args.report)
    print("IW3_ORIGINAL_FILE_HANDLE_LIFECYCLE_STAGED", json.dumps(report, sort_keys=True))

if __name__ == "__main__":
    main()
