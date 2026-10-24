#!/usr/bin/env python3
"""Diagnostic-only stage markers for SP game-level load in a disposable clone.

Never patch vendored source or game binaries. Marker events do not imply
weapons, enemies, or graphics work; they measure the engine's internal stage.
"""
from pathlib import Path
import argparse

GAME_FILE = Path("src/game/g_main.cpp")
FN_HEADER = "void __cdecl G_InitGame("
FRAME_HEADER = "int __cdecl G_RunFrame("
SPAWN_CALL = "    G_SpawnEntitiesFromString();"

HELPER = """
// Z2026 offline SP probe: source-only diagnostics, no data/Steam ticket logging.
static void Z2026_SPTrace(const char* stage)
{
    FILE* output = std::fopen("z2026-sp-level-trace.txt", "a");
    if (output)
    {
        std::fprintf(output, "%s\\n", stage);
        std::fclose(output);
    }
}
"""


def instrument(source_root: Path) -> dict:
    file = source_root / GAME_FILE
    source = file.read_text(encoding="utf-8")
    if "Z2026_SPTrace" in source:
        raise ValueError("SP instrumentation already applied")
    for needle in (FN_HEADER, FRAME_HEADER, SPAWN_CALL):
        if source.count(needle) != 1:
            raise ValueError(f"Expected unique SP source anchor: {needle}")
    if not source.startswith("#ifndef KISAK_SP"):
        raise ValueError("Expected single-player-only game source")
    # Explicit own C++ header; no guessed linkage or macro assumptions.
    source = source.replace("#include <universal/q_shared.h>",
                            "#include <cstdio>\n#include <universal/q_shared.h>",
                            1)
    source = source.replace(FN_HEADER, HELPER + "\n" + FN_HEADER, 1)
    for anchor, stage in (
        (FN_HEADER, "G_INIT_ENTER"),
        (FRAME_HEADER, "G_FRAME_ENTER"),
    ):
        p = source.index(anchor)
        brace = source.index("{", p)
        if source[p:brace].count(";") > 0:
            raise ValueError("Unexpected function body boundary")
        code = f'\n    Z2026_SPTrace("{stage}");\n'
        if stage == "G_FRAME_ENTER":
            code = ('\n    static bool z2026_first_frame = false;\n'
                    '    if (!z2026_first_frame)\n'
                    '    {\n'
                    '        z2026_first_frame = true;\n'
                    '        Z2026_SPTrace("G_FRAME_ENTER");\n'
                    '    }\n')
        source = source[:brace+1] + code + source[brace+1:]
    source = source.replace(
        SPAWN_CALL,
        SPAWN_CALL + '\n    Z2026_SPTrace("G_SPAWN_ENTITIES_RETURN");',
        1
    )
    file.write_text(source, encoding="utf-8")
    return {"patched": str(file),
            "stage_markers": ["G_INIT_ENTER", "G_SPAWN_ENTITIES_RETURN",
                              "G_FRAME_ENTER"],
            "modifies_multiplayer_auth": False,
            "changes_gameplay": False}


def main() -> None:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--source-copy", type=Path, required=True)
    args = cli.parse_args()
    import json
    print(json.dumps(instrument(args.source_copy), sort_keys=True))


if __name__ == "__main__":
    main()
