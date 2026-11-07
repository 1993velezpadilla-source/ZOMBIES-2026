#!/usr/bin/env python3
"""Diagnostic-only stage markers for SP game-level load in a disposable clone.

Never patch vendored source or game binaries. Marker events do not imply
weapons, enemies, or graphics work; they measure the engine's internal stage.
"""
from pathlib import Path
import argparse

GAME_FILE = Path("src/game/g_main.cpp")
FRAME_FILE = Path("src/game/g_runframe.cpp")
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
    file, frame_file = source_root / GAME_FILE, source_root / FRAME_FILE
    if not file.is_file() or not frame_file.is_file():
        raise ValueError("Missing original SP bootstrap/frame module")
    source = file.read_text(encoding="utf-8")
    frame = frame_file.read_text(encoding="utf-8")
    if "Z2026_SPTrace" in source or "Z2026_SPTrace" in frame:
        raise ValueError("SP instrumentation already applied")
    for text, needles in ((source, (FN_HEADER, SPAWN_CALL)), (frame, (FRAME_HEADER,))):
        if not text.startswith("#ifndef KISAK_SP"):
            raise ValueError("Expected single-player-only game source")
        for needle in needles:
            if text.count(needle) != 1:
                raise ValueError(f"Expected unique SP source anchor: {needle}")
    def entry(text, anchor, code):
        pos = text.index(anchor)
        brace = text.index("{", pos)
        if ";" in text[pos:brace]:
            raise ValueError("Unexpected function body boundary")
        text = text[:brace+1] + code + text[brace+1:]
        text = text.replace(anchor, HELPER + "\n" + anchor, 1)
        return "#include <cstdio>\n" + text
    source = entry(source, FN_HEADER, '\n    Z2026_SPTrace("G_INIT_ENTER");\n')
    frame = entry(frame, FRAME_HEADER,
                  '\n    static bool z2026_first_frame = false;\n'
                  '    if (!z2026_first_frame)\n'
                  '    {\n'
                  '        z2026_first_frame = true;\n'
                  '        Z2026_SPTrace("G_FRAME_ENTER");\n'
                  '    }\n')
    source = source.replace(SPAWN_CALL,
                            SPAWN_CALL + '\n    Z2026_SPTrace("G_SPAWN_ENTITIES_RETURN");', 1)
    file.write_text(source, encoding="utf-8")
    frame_file.write_text(frame, encoding="utf-8")
    return {"patched": str(file), "frame_patched": str(frame_file),
            "stage_markers": ["G_INIT_ENTER", "G_SPAWN_ENTITIES_RETURN", "G_FRAME_ENTER"],
            "modifies_multiplayer_auth": False, "changes_gameplay": False}


def main() -> None:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--source-copy", type=Path, required=True)
    args = cli.parse_args()
    import json
    print(json.dumps(instrument(args.source_copy), sort_keys=True))


if __name__ == "__main__":
    main()
