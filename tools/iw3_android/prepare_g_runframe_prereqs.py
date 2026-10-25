#!/usr/bin/env python3
"""Stage authentic IW3 SP frame prerequisite functions and audit G_RunFrame.

Never synthesize a fake G_RunFrame. Extract unmodified original Com_Memcpy
from com_shared.cpp. The vendored real G_RunFrame source receives a narrow
ABI portability fix: iterate typed entity objects rather than Win32 byte
strides; audit this patched source and reject any legacy pointer arithmetic.
The full G_RunFrame cannot yet link or execute on Android.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

COM_SHARED = Path("src/universal/com_shared.cpp")
G_MAIN = Path("src/game/g_main.cpp")
MEMCPY_SIGNATURE = "void __cdecl Com_Memcpy(void *dest_p, const void *src_p, const size_t count)"
FRAME_SIGNATURE = "int __cdecl G_RunFrame(ServerFrameExtent extent, int timeCap)"
FRAME_PHASES = (
    "update player", "update anim1", "script threads1", "update anim2",
    "script threads2", "bad places", "update ents", "update client",
    "update corpses",
)
IMPORTANT_CALLS = (
    "G_UpdatePlayer(", "G_UpdatePlayerTriggers(", "G_CheckReloadStatus(",
    "Com_Memcpy(", "NotifyTriggers(", "Scr_RunCurrentThreads(",
    "SV_DObjInitServerTime(", "G_DObjUpdateServerTime(",
    "Scr_IncTime(", "Path_RunBadPlaces(", "G_RunFrameForEntity(",
    "ClientEndFrame(", "HudElem_UpdateClient(", "G_UpdateActorCorpses(",
)
FRAME_LEGACY_ASSUMPTIONS = (
    "p_inuse += 628;",
    "(gentity_s *)(p_inuse - 168)",
    "*((unsigned int *)p_inuse + 34)",
)
FRAME_TYPED_PORTABILITY_MARKERS = (
    "gentity_s *animEnt = &g_entities[1];",
    "animEnt->r.inuse",
    "animEnt->flags",
    "FL_REPEAT_ANIM_UPDATE",
    "FL_NO_AUTO_ANIM_UPDATE",
    "G_DObjUpdateServerTime(animEnt, 1)",
    "++animEnt;",
)

# Parser only locates a function region. No replacements of its body.
def function_source(source: str, signature: str) -> str:
    if source.count(signature) != 1:
        raise ValueError("Expected precisely one authentic IW3 function " + signature)
    start = source.index(signature)
    open_brace = source.find("{", start + len(signature))
    if open_brace < 0:
        raise ValueError("Engine function body not found")
    # Avoid false terminators inside // or /* */ comments and strings.
    # Frame source contains literal brace pairs in these cases.
    depth = 0
    i = open_brace
    mode = "code"
    while i < len(source):
        c = source[i]
        nxt = source[i + 1] if i + 1 < len(source) else ""
        if mode == "line":
            if c == "\n":
                mode = "code"
        elif mode == "block":
            if c == "*" and nxt == "/":
                mode = "code"
                i += 1
        elif mode == "string":
            if c == "\\":
                i += 1
            elif c == '"':
                mode = "code"
        elif mode == "char":
            if c == "\\":
                i += 1
            elif c == "'":
                mode = "code"
        else:
            if c == "/" and nxt == "/":
                mode = "line"
                i += 1
            elif c == "/" and nxt == "*":
                mode = "block"
                i += 1
            elif c == '"':
                mode = "string"
            elif c == "'":
                mode = "char"
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return source[start:i + 1]
                if depth < 0:
                    raise ValueError("Unbalanced C++ engine block")
        i += 1
    raise ValueError("Incomplete original C++ function body")


# The C++ test builds this verbatim span from the real G_RunFrame source
# with deliberately adversarial 64-bit entity sizes. This is an ABI-unit
# fixture, NOT a replacement frame or Android playable runtime.
ENTITY_LOOP_BEGIN = "                if (level.num_entities > 1)\n"
ENTITY_LOOP_LAST_LINE = "                    } while (level.currentIndex < level.num_entities);"


def actual_entity_loop(engine_text: str) -> str:
    frame = function_source(engine_text, FRAME_SIGNATURE)
    # Prefix specifically selects the animation re-check pass, not any
    # unrelated entity iteration across the rest of G_RunFrame.
    if frame.count(ENTITY_LOOP_BEGIN) != 1:
        raise ValueError("G_RunFrame native animation pass occurrence changed")
    first = frame.index(ENTITY_LOOP_BEGIN)
    stop = frame.index(ENTITY_LOOP_LAST_LINE, first)
    tail = stop + len(ENTITY_LOOP_LAST_LINE)
    after = frame[tail:]
    if not after.startswith("\n                }\n            } while (checkAnimChange);"):
        raise ValueError("Original SP animation-loop boundary changed")
    out = frame[first:tail] + "\n                }\n"
    if out.count("gentity_s *animEnt = &g_entities[1];") != 1:
        raise ValueError("Typed engine entity loop missing")
    if any(snippet in out for snippet in FRAME_LEGACY_ASSUMPTIONS):
        raise ValueError("Legacy 32-bit field math detected in source loop")
    return out


def prepare(engine: Path, output: Path, report: Path) -> dict:
    engine = engine.resolve()
    com_path = engine / COM_SHARED
    frame_path = engine / G_MAIN
    out = output.resolve()
    if not com_path.is_file() or not frame_path.is_file():
        raise ValueError("Real KisakCOD SP source missing")
    if out == com_path or out == frame_path:
        raise ValueError("Never overwrite a vendored original IW3 source file")
    com_bytes, frame_bytes = com_path.read_bytes(), frame_path.read_bytes()
    com, frame = com_bytes.decode("utf-8"), frame_bytes.decode("utf-8")
    body = function_source(com, MEMCPY_SIGNATURE)
    if 'memcpy(dest_p, src_p, count);' not in body:
        raise ValueError("Original IW3 implementation of Com_Memcpy changed")
    # This preserves the authentic source byte-for-byte as a contiguous
    # substring; iassert is provided by an Android-facing assertion shim.
    header = '#include "iw3_android_frame_compat.h"\n'
    rendered = header + body + "\n"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(rendered, encoding="utf-8")
    if body not in com_path.read_text(encoding="utf-8"):
        raise RuntimeError("Original engine Com_Memcpy body not preserved")
    original_frame = function_source(frame, FRAME_SIGNATURE)
    phases = {name: original_frame.count('PROF_SCOPED("' + name + '")')
              for name in FRAME_PHASES}
    calls = {name: original_frame.count(name) for name in IMPORTANT_CALLS}
    legacy = {snippet: original_frame.count(snippet)
              for snippet in FRAME_LEGACY_ASSUMPTIONS}
    if not all(v >= 1 for v in phases.values()):
        raise ValueError("Original SP G_RunFrame phases missing/changed")
    if not all(v >= 1 for v in calls.values()):
        raise ValueError("Original SP G_RunFrame dependencies missing/changed")
    if any(v != 0 for v in legacy.values()):
        raise ValueError("Hard-coded 32-bit entity addressing remains in SP frame")
    portable = {m: original_frame.count(m) for m in FRAME_TYPED_PORTABILITY_MARKERS}
    if not all(v >= 1 for v in portable.values()):
        raise ValueError("Typed 64-bit-safe entity loop missing/changed; re-audit")
    result = {
        "com_shared_source": str(COM_SHARED),
        "com_shared_sha256": hashlib.sha256(com_bytes).hexdigest(),
        "original_memcpy_function_preserved_exactly": True,
        "original_memcpy_source_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
        "generated_memcpy_sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
        "original_single_player_g_runframe_source": str(G_MAIN),
        "original_single_player_g_runframe_sha256": hashlib.sha256(frame_bytes).hexdigest(),
        "frame_original_function_sha256": hashlib.sha256(original_frame.encode("utf-8")).hexdigest(),
        "frame_source_lines": original_frame.count("\n") + 1,
        "frame_phase_markers": phases,
        "frame_function_call_occurrences": calls,
        "known_32bit_entity_pointer_hazards_remaining": legacy,
        "frame_animation_loop_uses_typed_entity_fields": True,
        "typed_animation_loop_markers": portable,
        "other_sp_engine_abi_assumptions_unverified": True,
        "g_runframe_compiled_on_android": False,
        "g_runframe_executed_on_android": False,
        "iw3_3d_renderer_ported": False,
        "iw3_game_apk_available": False,
        "other_engine_used": False,
    }
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n",
                      encoding="utf-8")
    return result


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--engine", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--report", type=Path, required=True)
    ap.add_argument("--entity-loop-output", type=Path)
    args = ap.parse_args()
    data = prepare(args.engine, args.output, args.report)
    if args.entity_loop_output:
        if args.entity_loop_output.resolve() == (args.engine.resolve() / G_MAIN):
            raise ValueError("Never overwrite actual SP frame source")
        source = (args.engine / G_MAIN).read_text(encoding="utf-8")
        loop = actual_entity_loop(source)
        args.entity_loop_output.parent.mkdir(parents=True, exist_ok=True)
        args.entity_loop_output.write_text(loop, encoding="utf-8")
        print("IW3_SOURCE_EXACT_G_RUNFRAME_ENTITY_LOOP_EXTRACTED",
              hashlib.sha256(loop.encode("utf-8")).hexdigest())
    print("IW3_REAL_G_RUNFRAME_PREREQUISITE_SOURCE_STAGED", json.dumps(data, sort_keys=True))


if __name__ == "__main__":
    main()
