"""Source-anchor and display-layout regression for always-on Luanti FPS HUD."""
from pathlib import Path
from tempfile import TemporaryDirectory

from patch_fps_hud import patch

# Exercise the source patch without NDK, on the exact required anchors.
with TemporaryDirectory() as td:
    root=Path(td); folder=root/"src/client"; folder.mkdir(parents=True)
    cpp=folder/"gameui.cpp";header=folder/"gameui.h"
    header.write_text("class GameUI {\n\tgui::IGUIStaticText *m_guitext2 = nullptr; // Second line of debug text\n};\n")
    cpp.write_text("""void GameUI::init() {
\t// Chat text
\tm_guitext_chat = gui::StaticText::add(guienv, L"", core::recti(), false, true, guiroot);
}
void GameUI::update() {
\ts32 minimal_debug_height = 0;
}
void GameUI::clearText()
{
}
""")
    patch(root)
    updated_cpp=cpp.read_text();updated_header=header.read_text()
    assert "m_ak47_fps_text" in updated_header
    assert 'fps_label << "FPS: "' in updated_cpp
    assert "stats.dtime_jitter.avg" in updated_cpp
    assert "right - 180" in updated_cpp
    assert "screensize.X" in updated_cpp
    assert "menuCount() == 0" in updated_cpp
    assert "m_ak47_fps_text->remove()" in updated_cpp
    try:
        patch(root)
    except ValueError:
        pass
    else:
        raise AssertionError("FPS UI patch must be idempotence guarded")
print("FPS_OVERLAY_STATIC_TEST_PASS: native client FPS, right corner, GUI cleanup")
