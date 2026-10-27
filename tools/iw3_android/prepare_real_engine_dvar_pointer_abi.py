#!/usr/bin/env python3
"""Stage corrected authentic KisakCOD dvar pointer/ABI functions for LP64 verification.

Only the listed function bodies are extracted from src/universal/dvar.cpp.
This is a compile/runtime regression slice, not the complete dvar registry or
filesystem startup runtime.
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

SOURCE = Path("src/universal/dvar.cpp")
DVAR_REGISTER_VARIANT = ("const dvar_s *__cdecl Dvar_RegisterVariant(\n    const char *dvarName,\n    uint8_t type,\n    uint16_t flags,\n    DvarValue value,\n    DvarLimits domain,\n    const char *description)")

FUNCTIONS = (
    DVAR_REGISTER_VARIANT,
    "const char *__cdecl Dvar_EnumToString(const dvar_s *dvar)",
    "const char *__cdecl Dvar_IndexStringToEnumString(const dvar_s *dvar, const char *indexString)",
    "const char *__cdecl Dvar_ValueToString(const dvar_s *dvar, DvarValue value)",
    "const char *__cdecl Dvar_DomainToString_Internal(\n    uint8_t type,\n    DvarLimits domain,\n    char *outBuffer,\n    uint32_t outBufferLen,\n    int *outLineCount)",
    "char __cdecl Dvar_ValueInDomain(uint8_t type, DvarValue value, DvarLimits domain)",
    "int __cdecl Dvar_ValuesEqual(uint8_t type, DvarValue val0, DvarValue val1)",
    "void __cdecl Dvar_UpdateEnumDomain(dvar_s *dvar, const char **stringTable)",
    "bool __cdecl Dvar_ShouldFreeCurrentString(dvar_s *dvar)",
    "bool __cdecl Dvar_ShouldFreeLatchedString(dvar_s *dvar)",
    "bool __cdecl Dvar_ShouldFreeResetString(dvar_s *dvar)",
    "void __cdecl Dvar_FreeString(DvarValue *value)",
    "void __cdecl Dvar_UpdateResetValue(dvar_s *dvar, DvarValue value)",
    "void __cdecl Dvar_AssignResetStringValue(dvar_s *dvar, DvarValue *dest, const char *string)",
    "void __cdecl Dvar_CopyString(const char *string, DvarValue *value)",
    "void __cdecl Dvar_WeakCopyString(const char *string, DvarValue *value)",
    "void __cdecl Dvar_SetVariant(dvar_s *dvar, DvarValue value, DvarSetSource source)",
    "void __cdecl Dvar_AssignCurrentStringValue(dvar_s *dvar, DvarValue *dest, char *string)",
    "void __cdecl Dvar_SetLatchedValue(dvar_s *dvar, DvarValue value)",
    "void __cdecl Dvar_AssignLatchedStringValue(dvar_s *dvar, DvarValue *dest, char *string)",
    "const dvar_s *__cdecl Dvar_RegisterString(\n    const char *dvarName,\n    const char *value,\n    uint16_t flags,\n    const char *description)",
    "const dvar_s *__cdecl Dvar_RegisterEnum(\n    const char *dvarName,\n    const char **valueList,\n    int defaultIndex,\n    uint16_t flags,\n    const char *description)",
    "DvarValue *__cdecl Dvar_ClampValueToDomain(\n    DvarValue *result,\n    uint8_t type,\n    DvarValue value,\n    DvarValue resetValue,\n    DvarLimits domain)",
    "void __cdecl Dvar_ClampVectorToDomain(float *vector, int components, float min, float max)",
    "void __cdecl Dvar_MakeExplicitType(\n    dvar_s *dvar,\n    const char *dvarName,\n    uint8_t type,\n    uint16_t flags,\n    DvarValue resetValue,\n    DvarLimits domain)",
    "DvarValue *__cdecl Dvar_StringToValue(DvarValue *result, uint8_t type, DvarLimits domain, const char *string)",
    "int __cdecl Dvar_StringToEnum(const DvarLimits *domain, const char *string)",
    "void __cdecl Dvar_UpdateValue(dvar_s *dvar, DvarValue value)",
    "void __cdecl Dvar_SetBoolFromSource(dvar_s *dvar, bool value, DvarSetSource source)",
    "void __cdecl Dvar_SetIntFromSource(dvar_s *dvar, int value, DvarSetSource source)",
    "void __cdecl Dvar_SetFloatFromSource(dvar_s *dvar, float value, DvarSetSource source)",
    "void __cdecl Dvar_SetVec2FromSource(dvar_s *dvar, float x, float y, DvarSetSource source)",
    "void __cdecl Dvar_SetVec3FromSource(dvar_s *dvar, float x, float y, float z, DvarSetSource source)",
    "void __cdecl Dvar_SetVec4FromSource(dvar_s *dvar, float x, float y, float z, float w, DvarSetSource source)",
    "void __cdecl Dvar_SetColorFromSource(dvar_s *dvar, float r, float g, float b, float a, DvarSetSource source)",
    "void __cdecl Dvar_SetStringFromSource(dvar_s *dvar, char *string, DvarSetSource source)",
    "void __cdecl Dvar_SetDomainFunc(dvar_s *dvar, bool(__cdecl *customFunc)(dvar_s *, DvarValue))",
)

SMOKE_FUNCTIONS = (
    "const char *__cdecl Dvar_EnumToString(const dvar_s *dvar)",
    "const char *__cdecl Dvar_IndexStringToEnumString(const dvar_s *dvar, const char *indexString)",
    "const char *__cdecl Dvar_ValueToString(const dvar_s *dvar, DvarValue value)",
    "const dvar_s *__cdecl Dvar_RegisterString(\n    const char *dvarName,\n    const char *value,\n    uint16_t flags,\n    const char *description)",
    "const dvar_s *__cdecl Dvar_RegisterEnum(\n    const char *dvarName,\n    const char **valueList,\n    int defaultIndex,\n    uint16_t flags,\n    const char *description)",
    "void __cdecl Dvar_UpdateEnumDomain(dvar_s *dvar, const char **stringTable)",
    "DvarValue *__cdecl Dvar_ClampValueToDomain(\n    DvarValue *result,\n    uint8_t type,\n    DvarValue value,\n    DvarValue resetValue,\n    DvarLimits domain)",
    "void __cdecl Dvar_ClampVectorToDomain(float *vector, int components, float min, float max)",
    "DvarValue *__cdecl Dvar_StringToValue(DvarValue *result, uint8_t type, DvarLimits domain, const char *string)",
    "int __cdecl Dvar_StringToEnum(const DvarLimits *domain, const char *string)",
)

REQUIRED = (
    "dvar = Dvar_FindMalleableVar(dvarName);",
    "return Dvar_RegisterNew(dvarName, type, flags, value, domain, description);",
    "Dvar_Reregister(dvar, dvarName, type, flags, value, domain, description);",
    "v5.string = value;",
    "value->string = CopyString(string);",
    "value->string = string;",
    "dvarDomain.enumeration.strings = valueList;",
    "malleableDvar->domain.enumeration.strings = stringTable;",
    "domain->enumeration.strings[stringIndex]",
    "domain->enumeration.strings[stringIndexb]",
    "dvar->domain.enumeration.strings[dvar->current.integer]",
    "if (dvar->domainFunc && !dvar->domainFunc(dvar, value))",
    "if (!customFunc(dvar, dvar->current))",
    "iassert(dvar->current.string != stringCopy);",
    "domain.integer.min <= domain.integer.max",
    "if (value.integer < domain.integer.min)",
    "else if (value.integer > domain.integer.max)",
)

FORBIDDEN = (
    "v5.integer = (int)value;",
    "dvarDomain.integer.max = (int)valueList;",
    "malleableDvar->domain.integer.max = (int)stringTable;",
    "value->integer = (int)CopyString(string);",
    "value->integer = (int)string;",
    "value.integer = (int)string;",
    "newValue.integer = (int)string;",
    "newValue.integer = (int)stringCopy;",
    "domain->integer.max + 4 * stringIndex",
    "dvar->domain.integer.max + 4 * dvar->current.integer",
    "uint8_t(__cdecl *)(dvar_s *, int, uint32_t, uint32_t, uint32_t)",
)


def _render(source: str, signatures: tuple[str, ...]) -> str:
    bodies = [function_source(source, signature) for signature in signatures]
    return (
        '#include "iw3_android_dvar_pointer_compat.h"\n\n'
        # Dvar_FindMalleableVar is private in upstream dvar.cpp; this external
        # declaration deliberately exposes the unresolved cross-TU dependency.
        'dvar_s *__cdecl Dvar_FindMalleableVar(const char *dvarName);\n\n'
        + "\n\n".join(bodies) + "\n"
    )


def prepare(engine: Path, output: Path, smoke_output: Path, report_path: Path) -> dict:
    engine = engine.resolve()
    source_path = engine / SOURCE
    original = source_path.read_bytes()
    source = original.decode("utf-8")
    rendered = _render(source, FUNCTIONS)
    smoke = _render(source, SMOKE_FUNCTIONS)

    for marker in REQUIRED:
        if marker not in rendered:
            raise ValueError("LP64 dvar pointer contract missing: " + marker)
    for marker in FORBIDDEN:
        if marker in source or marker in rendered:
            raise ValueError("32-bit-only dvar pointer/ABI code remains: " + marker)

    output = output.resolve()
    smoke_output = smoke_output.resolve()
    report_path = report_path.resolve()
    if output == source_path or smoke_output == source_path:
        raise ValueError("Refusing to overwrite authentic KisakCOD dvar.cpp")
    for path, contents in ((output, rendered), (smoke_output, smoke)):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents, encoding="utf-8")

    if source_path.read_bytes() != original:
        raise RuntimeError("Vendored KisakCOD dvar.cpp changed during extraction")

    report = {
        "source": str(SOURCE),
        "source_sha256": hashlib.sha256(original).hexdigest(),
        "audit_function_signatures": list(FUNCTIONS),
        "smoke_function_signatures": list(SMOKE_FUNCTIONS),
        "audit_body_sha256": {
            signature: hashlib.sha256(function_source(source, signature).encode("utf-8")).hexdigest()
            for signature in FUNCTIONS
        },
        "authentic_kisakcod_function_bodies_extracted": True,
        "dvar_register_variant_body_staged_verbatim": DVAR_REGISTER_VARIANT in FUNCTIONS,
        "dvar_register_variant_dependencies_unresolved": ["Dvar_FindMalleableVar", "Dvar_RegisterNew", "Dvar_Reregister"],
        "string_values_use_native_pointer_union_member": True,
        "enum_tables_use_native_pointer_member_and_indexing": True,
        "domain_callbacks_use_declared_DvarValue_by_value_abi": True,
        "integer_domains_use_native_min_max_fields": True,
        "full_dvar_registry_linked": False,
        "filesystem_startup_invoked": False,
        "fastfile_or_map_loaded": False,
        "renderer_or_gameplay_proven": False,
        "playable_apk": False,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--smoke-output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    report = prepare(args.engine, args.output, args.smoke_output, args.report)
    print("IW3_ORIGINAL_DVAR_LP64_POINTER_ABI_STAGED", json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
