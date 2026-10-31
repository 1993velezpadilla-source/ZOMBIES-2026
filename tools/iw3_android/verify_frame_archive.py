#!/usr/bin/env python3
"""Audit the compiled complete IW3 frame, without claiming linkage/execution."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

REQUIRED_SERVICES = (
    "G_UpdatePlayer(gentity_s*)", "G_UpdatePlayerTriggers(gentity_s*)",
    "G_RunFrameForEntity(gentity_s*)", "Scr_RunCurrentThreads()",
    "Scr_IncTime()", "ClientEndFrame(gentity_s*)", "G_UpdateActorCorpses()",
    "Actor_DumpEventListners()", "Path_RunBadPlaces()",
)


def audit(archive: Path, source: Path, build: Path, nm: str,
          readelf: str, machine: str) -> dict:
    if not archive.is_file() or not source.is_file():
        raise ValueError("Actual frame source/archive missing")
    def run(*args):
        return subprocess.check_output(args, text=True, stderr=subprocess.STDOUT)
    elf = run(readelf, "-h", str(archive))
    if "ELF64" not in elf or machine not in elf:
        raise ValueError("Frame archive has wrong native architecture")
    defined = run(nm, "-C", "--defined-only", str(archive))
    if len(re.findall(r"\bT G_RunFrame\(ServerFrameExtent, int\)\s*$", defined, re.M)) != 1:
        raise ValueError("The full original SP G_RunFrame is not defined exactly once")
    undefined = run(nm, "-C", "--undefined-only", str(archive))
    for name in REQUIRED_SERVICES:
        if name not in undefined or name in defined:
            raise ValueError("Original service must remain real/unresolved here: " + name)
    dependencies = list(build.rglob("g_runframe.cpp.o.d"))
    if len(dependencies) != 1:
        raise ValueError("Compiler-generated full frame dependency file missing/ambiguous")
    dep = dependencies[0].read_text(encoding="utf-8")
    if re.search(r"(?:/|\\)(?:d3d9\.h|windows\.h|win_local\.h|mss\.h)\b", dep, re.I):
        raise ValueError("Platform SDK leaked back into the real frame include graph")
    for header in ("game/g_level.h", "bgame/bg_public.h", "server/server_frame.h"):
        if header not in dep.replace("\\", "/"):
            raise ValueError("Actual engine state header absent from compiler dependency graph: " + header)
    return {
        "full_original_g_runframe_compiled": True,
        "machine": machine,
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        "real_engine_state_headers_used": True,
        "direct3d_or_windows_sdk_required_by_frame": False,
        "unported_services_still_unresolved": list(REQUIRED_SERVICES),
        "frame_linked_to_working_runtime": False,
        "frame_executed_on_android": False,
        "gameplay_verified": False,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--archive", type=Path, required=True)
    ap.add_argument("--source", type=Path, required=True)
    ap.add_argument("--build", type=Path, required=True)
    ap.add_argument("--nm", required=True)
    ap.add_argument("--readelf", required=True)
    ap.add_argument("--machine", required=True)
    ap.add_argument("--report", type=Path, required=True)
    args = ap.parse_args()
    result = audit(args.archive, args.source, args.build, args.nm, args.readelf, args.machine)
    args.report.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("IW3_COMPLETE_ORIGINAL_FRAME_COMPILE_VERIFIED", json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
