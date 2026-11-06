"""Verify always-on FPS patch uses Luanti's existing visible text control."""
from pathlib import Path
from tempfile import TemporaryDirectory
from patch_fps_hud import patch

with TemporaryDirectory() as d:
    root=Path(d);p=root/'src/client';p.mkdir(parents=True)
    (p/'gameui.cpp').write_text("""void GameUI::update() {
\tv2u32 screensize = RenderingEngine::getWindowSize();
\ts32 minimal_debug_height = 0;
\tif (m_flags.show_minimal_debug) {
\t\tconst u16 fps = 1.0f / stats.dtime_jitter.avg;
\t\tstd::ostringstream os(std::ios_base::binary);
\t\tm_guitext->setRelativePosition(core::rect<s32>(5, 5, screensize.X, screensize.Y));
\t\tsetStaticText(m_guitext, utf8_to_wide(os.str()));
\t}
\tm_guitext->setVisible(m_flags.show_minimal_debug);
}
""")
    patch(root)
    out=(p/'gameui.cpp').read_text()
    assert "AK47_REAL_FPS_METER" in out
    assert 'm_flags.show_minimal_debug = true;' in out
    assert 'm_guitext->setTextAlignment(gui::EGUIA_LOWERRIGHT' in out
    assert 'm_guitext->setVisible(m_flags.show_minimal_debug);' in out
    assert 'meter << "FPS: "' in out
    assert 'setStaticText(m_guitext, utf8_to_wide(meter.str()));' in out
    assert out.count('setTextAlignment')==1
    assert 'm_ak47_fps_text' not in out
    try:patch(root)
    except ValueError:pass
    else:raise AssertionError('patch applied twice')
print('FPS_GAMEUI_VISIBLE_CONTROL_TEST_GREEN')
