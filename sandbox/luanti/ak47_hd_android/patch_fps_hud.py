"""Always-on top-right FPS display for the private COD4 Luanti Android trial.

Patch the pinned Luanti 5.18 GameUI, not a Lua HUD. Lua cannot measure the
client's actual rendered frames. The regular debug overlay remains optional.
"""
from pathlib import Path
import argparse

def replace_once(path: Path, before: str, after: str):
    text = path.read_text()
    count = text.count(before)
    if count != 1:
        raise ValueError(f"{path}: expected one FPS HUD anchor; found {count}: {before[:75]!r}")
    path.write_text(text.replace(before, after))

def patch(root: Path):
    header = root / "src/client/gameui.h"
    cpp = root / "src/client/gameui.cpp"
    replace_once(header,
        "\tgui::IGUIStaticText *m_guitext2 = nullptr; // Second line of debug text",
        "\tgui::IGUIStaticText *m_guitext2 = nullptr; // Second line of debug text\n"
        "\tgui::IGUIStaticText *m_ak47_fps_text = nullptr; // Always-on Android FPS")

    replace_once(cpp,
        "\t// Chat text\n\tm_guitext_chat = gui::StaticText::add(",
        "\t// Small, separate HUD, positioned relative to the live viewport.\n"
        "\tm_ak47_fps_text = gui::StaticText::add(guienv, L\"FPS: --\",\n"
        "\t\tcore::recti(), false, false, guiroot);\n"
        "\tm_ak47_fps_text->setOverrideFont(g_fontengine->getFont(\n"
        "\t\tg_fontengine->getDefaultFontSize() * 1.1f, FM_Unspecified));\n"
        "\tm_ak47_fps_text->setTextAlignment(gui::EGUIA_LOWERRIGHT, gui::EGUIA_UPPERLEFT);\n"
        "\tm_ak47_fps_text->setOverrideColor(video::SColor(255, 255, 244, 160));\n"
        "\t// Chat text\n\tm_guitext_chat = gui::StaticText::add(")

    replace_once(cpp,
        "\ts32 minimal_debug_height = 0;",
        "\t// The same jitter-smoothed frame duration used by Luanti's own\n"
        "\t// minimal debug screen. This reports REAL rendered FPS, not a limit.\n"
        "\tconst float avg_dt = stats.dtime_jitter.avg;\n"
        "\tstd::ostringstream fps_label;\n"
        "\tif (avg_dt > 0.000001f && avg_dt < 10.0f)\n"
        "\t\tfps_label << \"FPS: \" << static_cast<int>(1.0f / avg_dt + 0.5f);\n"
        "\telse\n"
        "\t\tfps_label << \"FPS: --\";\n"
        "\tconst s32 right = static_cast<s32>(screensize.X) - 14;\n"
        "\tconst s32 left = std::max(0, right - 180);\n"
        "\tm_ak47_fps_text->setRelativePosition(core::recti(left, 9, right, 57));\n"
        "\tsetStaticText(m_ak47_fps_text, utf8_to_wide(fps_label.str()));\n"
        "\tm_ak47_fps_text->setVisible(m_flags.show_hud && g_menumgr.menuCount() == 0);\n\n"
        "\ts32 minimal_debug_height = 0;")

    replace_once(cpp,
        "void GameUI::clearText()\n{\n",
        "void GameUI::clearText()\n{\n"
        "\tif (m_ak47_fps_text) {\n"
        "\t\tm_ak47_fps_text->remove();\n"
        "\t\tm_ak47_fps_text = nullptr;\n"
        "\t}\n")

    print("Top-right FPS overlay enabled using real GameUI frame stats")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    patch(parser.parse_args().root)
