#!/usr/bin/env python3
"""Stage authentic HunkUser allocator bodies with reviewed LP64 pointer fixes."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:
    from tools.iw3_android.prepare_g_runframe_prereqs import function_source
except ModuleNotFoundError:
    from prepare_g_runframe_prereqs import function_source

SOURCE = Path("src/universal/com_memory_hunk_user.cpp")
FUNCTIONS = (
    "HunkUser* __cdecl Hunk_UserCreate(int32_t maxSize, const char* name, bool fixed, bool tempMem, int32_t type)",
    "void* Hunk_UserAlloc(HunkUser* user, uint32_t size, int32_t alignment)",
    "void* Hunk_UserAllocAlignStrict(HunkUser* user, uint32_t size)",
    "void __cdecl Hunk_UserSetPos(HunkUser* user, uint8_t* pos)",
    "void __cdecl Hunk_UserReset(HunkUser* user)",
    "void __cdecl Hunk_UserDestroy(HunkUser* user)",
    "char* __cdecl Hunk_CopyString(HunkUser* user, const char* in)",
)
HEADER = (
    '#include <qcommon/qcommon.h>\n'
    '#include <universal/assertive.h>\n'
    '#include <universal/com_memory.h>\n'
    '#include <cstddef>\n'
    '#include <cstdint>\n'
    '#include <cstring>\n'
)
REQUIRED = (
    "user->end = reinterpret_cast<uintptr_t>(user) + static_cast<uintptr_t>(maxSize);",
    "user->pos = reinterpret_cast<uintptr_t>(user->buf);",
    "Z_VirtualCommit(user, static_cast<int32_t>(offsetof(HunkUser, buf)));",
    "uintptr_t pos;",
    "uintptr_t result;",
    "result = ~static_cast<uintptr_t>(alignment) & (static_cast<uintptr_t>(alignment) + pos);",
    "return reinterpret_cast<void *>(result);",
    "pos = reinterpret_cast<uintptr_t>(user) + 4096u;",
    "Z_VirtualDecommit(reinterpret_cast<void *>(pos), static_cast<int32_t>(user->pos - pos));",
    "memset(user->buf, 0, 4096u - offsetof(HunkUser, buf));",
    "char* __cdecl Hunk_CopyString(HunkUser* user, const char* in)",
)
FORBIDDEN = (
    "user->end = (int)user + maxSize;",
    "user->pos = (int)user->buf;",
    "int32_t pos;",
    "int32_t result;",
    "(void*)result",
    "(uint32_t)pos",
    "(int)pos",
    "user[114].name",
    "0xFE0u",
    "VirtualAlloc(",
)


def replace_once(body: str, old: str, new: str, label: str) -> str:
    count = body.count(old)
    if count == 1:
        return body.replace(old, new, 1)
    if count == 0 and body.count(new) == 1:
        # The vendored engine source may already carry this reviewed LP64 fix.
        # Accept it unchanged so the staging step stays idempotent.
        return body
    raise ValueError(f"{label}: expected one original or corrected expression, found old={count}, new={body.count(new)}: {old!r}")


def transform(signature: str, body: str) -> tuple[str, list[str]]:
    changes: list[str] = []
    rules: dict[str, tuple[tuple[str, str], ...]] = {
        FUNCTIONS[0]: (
            ("Z_VirtualCommit(user, 32);",
             "Z_VirtualCommit(user, static_cast<int32_t>(offsetof(HunkUser, buf)));"),
            ("user->end = (int)user + maxSize;",
             "user->end = reinterpret_cast<uintptr_t>(user) + static_cast<uintptr_t>(maxSize);"),
            ("user->pos = (int)user->buf;",
             "user->pos = reinterpret_cast<uintptr_t>(user->buf);"),
            (r'MyAssertHandler(".\\universal\\com_memory.cpp", 2848, 0, "%s\n\t(user->pos) = %i", "(!(user->pos & 31))", user->pos);',
             r'MyAssertHandler(".\\universal\\com_memory.cpp", 2848, 0, "%s\n\t(user->pos) = %p", "(!(user->pos & 31))", reinterpret_cast<void *>(user->pos));'),
        ),
        FUNCTIONS[1]: (
            ("int32_t pos;", "uintptr_t pos;"),
            ("int32_t result;", "uintptr_t result;"),
            ("result = ~alignment & (alignment + pos);",
             "result = ~static_cast<uintptr_t>(alignment) & (static_cast<uintptr_t>(alignment) + pos);"),
            ("if ((signed int)(size + result) <= current->end)",
             "if (static_cast<uintptr_t>(size) + result <= current->end)"),
            ("current->pos = size + (~alignment & (alignment + pos));",
             "current->pos = static_cast<uintptr_t>(size) + (~static_cast<uintptr_t>(alignment) & (static_cast<uintptr_t>(alignment) + pos));"),
            ("pos = ((pos + 4095) & 0xFFFFF000);",
             "pos = (pos + 4095u) & ~static_cast<uintptr_t>(4095u);"),
            ("if (pos != ((current->pos + 4095) & 0xFFFFF000))",
             "if (pos != ((current->pos + 4095u) & ~static_cast<uintptr_t>(4095u)))"),
            ("Z_VirtualCommit((void*)pos, current->pos - (uint32_t)pos);",
             "Z_VirtualCommit(reinterpret_cast<void *>(pos), static_cast<int32_t>(current->pos - pos));"),
            ("return (void*)result;", "return reinterpret_cast<void *>(result);"),
        ),
        FUNCTIONS[3]: (
            ("user->pos = (int)pos;", "user->pos = reinterpret_cast<uintptr_t>(pos);"),
        ),
        FUNCTIONS[4]: (
            ("void* pos;", "uintptr_t pos;"),
            ("pos = (void*)(((uint32_t)&user[114].name + 3) & 0xFFFFF000);",
             "pos = reinterpret_cast<uintptr_t>(user) + 4096u;"),
            ("if (pos != (void*)((user->pos + 4095) & 0xFFFFF000))",
             "if (pos != ((user->pos + 4095u) & ~static_cast<uintptr_t>(4095u)))"),
            ("if (user->pos - (int)pos <= 0)", "if (user->pos <= pos)"),
            ("Z_VirtualDecommit(pos, user->pos - (uint32_t)pos);",
             "Z_VirtualDecommit(reinterpret_cast<void *>(pos), static_cast<int32_t>(user->pos - pos));"),
            ("user->pos = (int)user->buf;", "user->pos = reinterpret_cast<uintptr_t>(user->buf);"),
            ("memset(user->buf, 0, 0xFE0u);",
             "memset(user->buf, 0, 4096u - offsetof(HunkUser, buf));"),
        ),
    }
    for old, new in rules.get(signature, ()):
        before = body
        body = replace_once(body, old, new, signature)
        if body != before:
            changes.append(f"{old} => {new}")
    return body, changes


def prepare(engine: Path, output: Path, report_path: Path | None = None) -> dict:
    engine = engine.resolve()
    source_path = engine / SOURCE
    output = output.resolve()
    if output == source_path:
        raise ValueError("Refusing to overwrite authentic KisakCOD com_memory.cpp")
    original = source_path.read_bytes()
    source = original.decode("utf-8")
    original_bodies = [function_source(source, signature) for signature in FUNCTIONS]
    transformed = [transform(signature, body) for signature, body in zip(FUNCTIONS, original_bodies)]
    bodies = [body for body, _ in transformed]
    rendered = HEADER + "\n\n".join(bodies) + "\n"

    for marker in REQUIRED:
        if marker not in rendered:
            raise ValueError("Native HunkUser contract missing: " + marker)
    for marker in FORBIDDEN:
        if marker in rendered:
            raise ValueError("32-bit HunkUser pointer assumption remains: " + marker)

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
    if source_path.read_bytes() != original:
        raise RuntimeError("Vendored KisakCOD memory source changed during staging")

    evidence = {
        "source": str(SOURCE),
        "source_sha256": hashlib.sha256(original).hexdigest(),
        "function_signatures": list(FUNCTIONS),
        "original_body_sha256": {
            signature: hashlib.sha256(body.encode("utf-8")).hexdigest()
            for signature, body in zip(FUNCTIONS, original_bodies)
        },
        "transformed_body_sha256": {
            signature: hashlib.sha256(body.encode("utf-8")).hexdigest()
            for signature, body in zip(FUNCTIONS, bodies)
        },
        "native_pointer_width_transformations": {
            signature: changes for signature, (_, changes) in zip(FUNCTIONS, transformed)
        },
        "original_HunkUser_bodies_used_with_reviewed_LP64_fixes": True,
        "HunkUser_header_uses_native_width_address_state": True,
        "virtual_memory_platform_adapter_required": True,
        "hunk_user_runtime_invoked": False,
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
    evidence = prepare(args.engine, args.output, args.report)
    print("IW3_ORIGINAL_HUNK_USER_LP64_SOURCE_STAGED", json.dumps(evidence, sort_keys=True))


if __name__ == "__main__":
    main()
