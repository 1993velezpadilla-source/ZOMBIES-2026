"""Permanent FPS meter for Luanti 5.18: REUSE its working minimal-debug text.

Earlier dedicated StaticText had no visible output on a real Pixel Fold.
Instead, this uses the pre-existing GameUI text that is already rendered by
the engine, and makes its contents simply "FPS: N" at the upper-right.
Never use a Lua/server timer as a substitute for measured client frame FPS.
"""
from pathlib import Path
import argparse


def replace_once(path: Path, old: str, new: str):
    text=path.read_text()
    if text.count(old)!=1:
        raise ValueError(f"{path}: FPS anchor count={text.count(old)}: {old[:95]!r}")
    path.write_text(text.replace(old,new))


def patch(root: Path):
    cpp=root/'src/client/gameui.cpp'
    if 'AK47_REAL_FPS_METER' in cpp.read_text():
        raise ValueError('FPS source already patched')
    # Existing engine debug text is reliably rendered even on Android.
    replace_once(cpp,
        '\ts32 minimal_debug_height = 0;',
        '\t// AK47_REAL_FPS_METER: always show genuine smoothed render FPS.\n'
        '\t// The previous new StaticText control was hidden on the test phone.\n'
        '\tm_flags.show_minimal_debug = true;\n'
        '\tm_flags.show_basic_debug = false; // no pos/yaw/pitch/seed overlay\n'
        '\ts32 minimal_debug_height = 0;')
    replace_once(cpp,
        '\t\tm_guitext->setRelativePosition(core::rect<s32>(5, 5, screensize.X, screensize.Y));',
        '\t\t// Right-anchored using the actual window dimension on rotation.\n'
        '\t\tm_guitext->setRelativePosition(core::rect<s32>(\n'
        '\t\t\tstd::max<s32>(0, static_cast<s32>(screensize.X) - 235),\n'
        '\t\t\t12, static_cast<s32>(screensize.X) - 14, 65));\n'
        '\t\tm_guitext->setTextAlignment(gui::EGUIA_LOWERRIGHT, gui::EGUIA_UPPERLEFT);\n'
        '\t\tm_guitext->setOverrideColor(video::SColor(255, 255, 235, 122));')
    replace_once(cpp,
        '\t\tsetStaticText(m_guitext, utf8_to_wide(os.str()));',
        '\t\t// Show only the frame rate, not the original long debug line.\n'
        '\t\tstd::ostringstream meter;\n'
        '\t\tif (stats.dtime_jitter.avg > 0.0001f && stats.dtime_jitter.avg < 10.0f)\n'
        '\t\t\tmeter << "FPS: " << static_cast<int>(1.0f / stats.dtime_jitter.avg + 0.5f);\n'
        '\t\telse\n'
        '\t\t\tmeter << "FPS: --";\n'
        '\t\tsetStaticText(m_guitext, utf8_to_wide(meter.str()));')
    replace_once(cpp,
        '\tm_guitext2->setVisible(m_flags.show_basic_debug);',
        '\t// Suppress world/debug telemetry permanently; keep only upper-right FPS.\n'
        '\tm_guitext2->setVisible(false);')
    print('AK47_REAL_FPS_METER: FPS only; basic pos/yaw/pitch/seed hidden')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('root',type=Path)
    patch(parser.parse_args().root)
