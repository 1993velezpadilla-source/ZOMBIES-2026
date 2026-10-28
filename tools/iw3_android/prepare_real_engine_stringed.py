#!/usr/bin/env python3
"""Stage the original StringEd package loader without its D3D/database entry points.

Only source bodies required by FS_InitFilesystem -> SEH_UpdateLanguageInfo ->
SE_LoadLanguage are copied from KisakCOD stringed_ingame.cpp. The original
CStringEdPackage header remains in use, with its LP64-safe ReadLine pointer fix.
This is a dependency audit slice, not proof that localization data was loaded.
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

SOURCE = Path("src/stringed/stringed_ingame.cpp")
FUNCTIONS = (
    "char *__cdecl SE_Load(char *psFileName, bool forceEnglish)",
    "void __cdecl SE_NewLanguage()",
    "void __cdecl SE_Init()",
    "void __cdecl SE_ShutDown()",
    "char *__cdecl SE_LoadLanguage(bool forceEnglish)",
    "char *__cdecl SE_GetFoundFile(std::string *strResult)",
    "uint8_t *__cdecl SE_LoadFileData(const char *psFileName)",
    "void __cdecl SE_FreeFileDataAfterLoad(uint8_t *psLoadedFile)",
    "int __cdecl SE_BuildFileList(",
    "void __cdecl SE_R_ListFiles(",
)
GLOBAL_DECLARATIONS = (
    "CStringEdPackage *TheStringPackage;",
    "int giFilesFound;",
    "char sTemp[64];",
)
HEADER = (
    '#include <universal/q_shared.h>\n'
    '#include <qcommon/qcommon.h>\n'
    '#include <stringed/stringed_ingame.h>\n'
    '#include <universal/assertive.h>\n'
    '#include <universal/com_memory.h>\n'
    '#include <universal/com_files.h>\n'
    '#include <string>\n'
    '#include <cstring>\n'
    '#include <cstdio>\n'
)
REQUIRED = (
    "TheStringPackage->SetupNewFileParse(psFileName);",
    "while (!errorMsg && TheStringPackage->ReadLine(&psParsePos, psDest))",
    "TheStringPackage->Clear();",
    "TheStringPackage = new CStringEdPackage();",
    "SE_NewLanguage();",
    'SE_BuildFileList("localizedstrings", &strResults);',
    "psErrorMessage = SE_Load((char *)p, forceEnglish);",
    "len = FS_ReadFile(psFileName, (void **)&pvLoadedData);",
    "FS_FreeFile((char *)psLoadedFile);",
    'dirFiles = FS_ListFiles(psDir, "/", FS_LIST_PURE_ONLY, &numdirs);',
    "sysFiles = FS_ListFiles(psDir, psExtension, FS_LIST_PURE_ONLY, &numSysFiles);",
    "FS_FreeFileList(sysFiles);",
    "strResults->append(1, ';');",
)
FORBIDDEN = (
    '#include <database/database.h>',
    "DB_FindXAssetHeader",
    "SE_GetString_FastFile",
    "Godot",
    "fake SE_LoadLanguage",
    "diagnostic SE_LoadLanguage stub",
)


def prepare(engine: Path, output: Path, report_path: Path | None = None) -> dict:
    engine = engine.resolve()
    source_path = engine / SOURCE
    output = output.resolve()
    if output == source_path:
        raise ValueError("Refusing to overwrite authentic KisakCOD stringed_ingame.cpp")
    original = source_path.read_bytes()
    source = original.decode("utf-8")

    for declaration in GLOBAL_DECLARATIONS:
        if source.count(declaration) != 1:
            raise ValueError("Expected one original StringEd global: " + declaration)
    globals_source = "\n".join(GLOBAL_DECLARATIONS)
    bodies = [function_source(source, signature) for signature in FUNCTIONS]
    rendered = HEADER + globals_source + "\n\n" + "\n\n".join(bodies) + "\n"

    for marker in REQUIRED:
        if marker not in rendered:
            raise ValueError("Original StringEd loader contract missing: " + marker)
    for marker in FORBIDDEN:
        if marker in rendered:
            raise ValueError("D3D/database or substitute code leaked into StringEd slice: " + marker)

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
    if source_path.read_bytes() != original:
        raise RuntimeError("Vendored KisakCOD StringEd source changed during staging")

    evidence = {
        "source": str(SOURCE),
        "source_sha256": hashlib.sha256(original).hexdigest(),
        "function_signatures": list(FUNCTIONS),
        "function_body_sha256": {
            signature: hashlib.sha256(body.encode("utf-8")).hexdigest()
            for signature, body in zip(FUNCTIONS, bodies)
        },
        "global_declarations": list(GLOBAL_DECLARATIONS),
        "original_StringEd_loader_bodies_preserved_verbatim": True,
        "original_StringEd_globals_preserved": True,
        "D3D_database_entry_points_excluded": True,
        "FS_ListFiles_and_FS_ReadFile_are_original_engine_calls": True,
        "stringed_runtime_invoked": False,
        "localized_assets_loaded": False,
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
    print("IW3_ORIGINAL_STRINGED_LOADER_STAGED_FOR_ARM64_AUDIT", json.dumps(evidence, sort_keys=True))


if __name__ == "__main__":
    main()
