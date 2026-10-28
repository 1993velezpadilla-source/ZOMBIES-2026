#!/usr/bin/env python3
"""Stage authentic KisakCOD language selection and StringEd startup hooks for ARM64 audit.

The extracted hooks preserve upstream bodies. The complete original
stringed_ingame.cpp is compiled separately as its provider archive; neither
this source slice nor that archive proves the runtime loaded localization data.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

try:
    from tools.iw3_android.prepare_g_runframe_prereqs import function_source
except ModuleNotFoundError:
    from prepare_g_runframe_prereqs import function_source

SOURCE = Path("src/stringed/stringed_hooks.cpp")
FUNCTIONS = (
    "void __cdecl SEH_InitLanguage()",
    "const dvar_s *SEH_UpdateCurrentLanguage()",
    "const char *__cdecl SEH_GetLanguageName(uint32_t iLanguage)",
    "int __cdecl SEH_GetLanguageIndexForName(const char *pszLanguageName, int *piLanguageIndex)",
    "int __cdecl FS_LanguageHasAssets(int iLanguage)",
    "int __cdecl SEH_StringEd_SetLanguageStrings(uint32_t iLanguage)",
    "void __cdecl SEH_UpdateLanguageInfo()",
    "void __cdecl SEH_Init_StringEd()",
    "void __cdecl SEH_Shutdown_StringEd()",
)
TABLE_START = "languageInfo_t g_languages[15] ="
GLOBAL_DECLARATIONS = (
    "const dvar_t *loc_language;",
    "const dvar_t *loc_forceEnglish;",
    "const dvar_t *loc_translate;",
    "const dvar_t *loc_warnings;",
    "const dvar_t *loc_warningsAsErrors;",
    "int g_currentAsian;",
)
HEADER = (
    '#include <universal/q_shared.h>\n'
    '#include <qcommon/qcommon.h>\n'
    '#include <universal/com_files.h>\n'
    '#include <stringed/stringed_ingame.h>\n'
    '#include "iw3_android_language_compat.h"\n'
    '#include <cstdint>\n'
)
REQUIRED = (
    'Dvar_RegisterInt("loc_language"',
    'Dvar_RegisterBool("loc_forceEnglish"',
    'Dvar_RegisterBool("loc_translate"',
    'Dvar_RegisterBool("loc_warnings"',
    'Dvar_RegisterBool("loc_warningsAsErrors"',
    "SEH_UpdateCurrentLanguage();",
    "g_currentAsian = integer >= 8 && integer <= 12;",
    "return g_languages[iLanguage].pszName;",
    "if (!I_stricmp(pszLanguageName, g_languages[i].pszName))",
    "g_languages[0].pszName",
    "if (FS_LanguageHasAssets(i))",
    "SE_LoadLanguage(loc_forceEnglish->current.enabled)",
    "SEH_StringEd_SetLanguageStrings(loc_language->current.unsignedInt)",
    "void __cdecl SEH_Init_StringEd()",
    "SE_Init();",
    "void __cdecl SEH_Shutdown_StringEd()",
    "SE_ShutDown();",
)
FORBIDDEN = (
    'return language == 0 ? "english" : "";',
    'I_stricmp(name, "english") != 0',
    "TRACK_stringed_hooks()",
    "track_static_alloc_internal(g_languages, 120",
)


def prepare(engine: Path, output: Path, report_path: Path | None = None) -> dict:
    engine = engine.resolve()
    source_path = engine / SOURCE
    output = output.resolve()
    if output == source_path:
        raise ValueError("Refusing to overwrite authentic KisakCOD stringed_hooks.cpp")
    original = source_path.read_bytes()
    source = original.decode("utf-8")

    table_start = source.find(TABLE_START)
    table_end = source.find("};", table_start)
    if table_start < 0 or table_end < 0:
        raise ValueError("Original 15-entry KisakCOD language table is missing")
    table = source[table_start:table_end + 2]
    language_names = re.findall(r'\{\s*"([^"]+)"\s*,\s*0\s*\}', table)
    if len(language_names) != 15:
        raise ValueError(f"Expected 15 original language names, found {len(language_names)}")

    for declaration in GLOBAL_DECLARATIONS:
        if source.count(declaration) != 1:
            raise ValueError("Expected one original language global: " + declaration)
    globals_source = "\n".join(GLOBAL_DECLARATIONS)

    bodies = [function_source(source, signature) for signature in FUNCTIONS]
    rendered = HEADER + table + "\n\n" + globals_source + "\n\n" + "\n\n".join(bodies) + "\n"
    for marker in REQUIRED:
        if marker not in rendered:
            raise ValueError("Original language initialization contract missing: " + marker)
    for marker in FORBIDDEN:
        if marker in rendered:
            raise ValueError("Diagnostic/Win32-only language code leaked into source slice: " + marker)

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
    if source_path.read_bytes() != original:
        raise RuntimeError("Vendored KisakCOD language source changed during staging")

    evidence = {
        "source": str(SOURCE),
        "source_sha256": hashlib.sha256(original).hexdigest(),
        "language_table_sha256": hashlib.sha256(table.encode("utf-8")).hexdigest(),
        "language_names": language_names,
        "function_signatures": list(FUNCTIONS),
        "function_body_sha256": {
            signature: hashlib.sha256(body.encode("utf-8")).hexdigest()
            for signature, body in zip(FUNCTIONS, bodies)
        },
        "original_language_table_preserved_verbatim": True,
        "original_SEH_InitLanguage_body_preserved_verbatim": True,
        "original_SEH_UpdateCurrentLanguage_body_preserved_verbatim": True,
        "original_language_name_and_index_helpers_preserved_verbatim": True,
        "original_FS_LanguageHasAssets_body_preserved_verbatim": True,
        "original_SEH_StringEd_SetLanguageStrings_body_preserved_verbatim": True,
        "original_SEH_UpdateLanguageInfo_body_preserved_verbatim": True,
        "original_SEH_Init_StringEd_and_shutdown_bodies_preserved_verbatim": True,
        "languageInfo_t_native_pointer_layout_guarded": True,
        "full_stringed_database_and_translation_loading_ported": False,
        "stringed_runtime_invoked": False,
        "filesystem_startup_runtime_invoked": False,
        "real_game_data_mounted": False,
        "map_loading_proven": False,
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
    evidence = prepare(args.engine, args.output, args.report)
    print("IW3_ORIGINAL_LANGUAGE_INIT_STAGED", json.dumps(evidence, sort_keys=True))


if __name__ == "__main__":
    main()
