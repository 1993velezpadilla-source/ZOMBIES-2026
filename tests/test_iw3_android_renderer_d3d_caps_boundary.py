"""Preprocessor boundary audit of the genuine KisakCOD D3D9 capability chain.

The desktop implementation remains in the original r_init.cpp. Android must
not instantiate D3D9 COM caps or Win32 windows; this is NOT GLES rendering.
"""
import os
from pathlib import Path
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "third_party/KisakCOD/src/gfx_d3d/r_init.cpp"

class RendererD3DCapsBoundaryTests(unittest.TestCase):
    def test_android_excludes_d3d9_caps_and_win32_chain_without_losing_neutral_code(self):
        source = SOURCE.read_text(encoding="utf-8")
        start = "int __cdecl R_CheckDxCaps(const _D3DCAPS9 *caps)"
        end = "void R_LoadGraphicsAssets()"
        self.assertEqual(source.count(start), 1)
        self.assertEqual(source.count(end), 1)
        # Include the original preprocessor guards and the neutral loader
        # declaration to catch an accidental over-broad #if region.
        begin = source.rfind("#if !defined(__ANDROID__)", 0, source.index(start))
        self.assertGreaterEqual(begin, 0)
        finish = source.index(end) + len(end)
        fragment = source[begin:finish]
        for platform, flags in (("android", ["-D__ANDROID__"]), ("desktop", [])):
            with self.subTest(platform=platform):
                result = subprocess.run(
                    [os.environ.get("CXX", "g++"), "-E", "-P", "-x", "c++",
                     *flags, "-"],
                    input=fragment, text=True, capture_output=True, timeout=30)
                self.assertEqual(result.returncode, 0, result.stderr)
                processed = result.stdout
                self.assertIn("R_DescribeRenderer(int renderer)", processed)
                self.assertIn("R_LoadGraphicsAssets()", processed)
                desktop_only = (
                    "R_CheckDxCaps(", "R_PickRenderer(", "R_GetDirect3DCaps(",
                    "R_StoreDirect3DCaps(", "R_SetShadowmapFormats_DX(",
                    "R_ChooseMonitor(", "R_ChooseAdapter(", "R_CreateWindow(",
                    "R_CreateGameWindow(", "GetAdapterIdentifier(",
                )
                for marker in desktop_only:
                    if platform == "android":
                        self.assertNotIn(marker, processed)
                    else:
                        self.assertIn(marker, processed)
        # Keep the genuine startup fail-closed until GLES draws exist.
        precreate = source[source.index("char __cdecl R_PreCreateWindow()"):
                           source.index("void __cdecl R_RespondToMissingCaps(")]
        self.assertIn("authentic GLES renderer command backend not integrated", precreate)
        self.assertIn("return 0;", precreate)

    def test_android_d3d9_query_device_boundary_and_real_hardware_fail_closed(self):
        # Probe the original source, not a fabricated renderer implementation.
        import tempfile
        source = SOURCE.read_text(encoding="utf-8")
        hardware = source[source.index("char __cdecl R_InitHardware("):
                          source.index("void __cdecl R_StoreWindowSettings(")]
        start = source.rfind("#if !defined(__ANDROID__)", 0,
                             source.index("char __cdecl R_CreateForInitOrReset()"))
        self.assertGreaterEqual(start, 0)
        device = source[start:source.index("const char *__cdecl R_ClosestRefreshRateForMode(")]
        for platform, flags in (("android", ["-D__ANDROID__"]), ("desktop", [])):
            with self.subTest(platform=platform):
                result = subprocess.run(
                    [os.environ.get("CXX", "g++"), "-E", "-P", "-x", "c++", *flags, "-"],
                    input=hardware + "\n" + device,
                    capture_output=True, text=True, timeout=30)
                self.assertEqual(result.returncode, 0, result.stderr)
                processed = result.stdout
                self.assertIn("R_InitHardware(", processed)
                self.assertIn("R_SetCustomResolution(", processed)
                if platform == "android":
                    self.assertNotIn("dx.device->CreateQuery(", processed)
                    self.assertNotIn("_D3DPRESENT_PARAMETERS_ d3dpp", processed)
                    self.assertNotIn("R_CreateDevice(wndParms)", processed)
                    self.assertIn("original renderer hardware requires GLES draw backend", processed)
                    self.assertIn("(void)wndParms;", processed)
                else:
                    self.assertIn("dx.device->CreateQuery(", processed)
                    self.assertIn("_D3DPRESENT_PARAMETERS_ d3dpp", processed)
                    self.assertIn("R_CreateDevice(wndParms)", processed)
                    self.assertIn("R_GetMonitorDimensions(", processed)

        # Execute the actual Android hardware-entry function with only its
        # logging dependency supplied. It must reject startup, not claim a frame.
        fixture = """
#include <cassert>
#include <cstdarg>
#include <cstdio>
#include <cstring>
#define __cdecl
struct GfxWindowParms {};
constexpr int CON_CHANNEL_GFX = 0;
int calls = 0;
void Com_Printf(int, const char *format, ...) {
    ++calls;
    assert(std::strstr(format, "requires GLES draw backend"));
}
""" + hardware + """
int main() {
    GfxWindowParms params{};
    assert(R_InitHardware(&params) == 0);
    assert(calls == 1);
}
"""
        with tempfile.TemporaryDirectory() as temp:
            cpp = Path(temp) / "r_init_hardware_android.cpp"
            exe = Path(temp) / "r_init_hardware_android"
            cpp.write_text(fixture, encoding="utf-8")
            compile_result = subprocess.run(
                [os.environ.get("CXX", "g++"), "-std=c++17", "-D__ANDROID__",
                 "-fsanitize=address,undefined", "-fno-omit-frame-pointer",
                 str(cpp), "-o", str(exe)],
                capture_output=True, text=True, timeout=60)
            self.assertEqual(compile_result.returncode, 0,
                             compile_result.stdout + compile_result.stderr)
            run = subprocess.run([str(exe)], capture_output=True, text=True,
                                 timeout=30, env={**os.environ, "ASAN_OPTIONS": "detect_leaks=1"})
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)


    def test_android_excludes_d3d9_device_loss_recovery_without_hiding_shutdown(self):
        source = SOURCE.read_text(encoding="utf-8")
        start = source.index("void __cdecl R_ComErrorCleanup()")
        end = source.index("void __cdecl R_MakeDedicated(")
        fragment = source[start:end]
        for platform, flags in (("android", ["-D__ANDROID__"]), ("desktop", [])):
            with self.subTest(platform=platform):
                result = subprocess.run(
                    [os.environ.get("CXX", "g++"), "-E", "-P", "-x", "c++",
                     *flags, "-"], input=fragment, capture_output=True,
                    text=True, timeout=30)
                self.assertEqual(result.returncode, 0, result.stderr)
                processed = result.stdout
                self.assertIn("R_ComErrorCleanup()", processed)
                self.assertIn("R_ReleaseForShutdownOrReset()", processed)
                if platform == "android":
                    self.assertIn("in-scene error cleanup requires native GLES backend",
                                  processed)
                    self.assertNotIn("dx.device->EndScene()", processed)
                    self.assertNotIn("R_CanRecoverLostDevice()", processed)
                    self.assertNotIn("void R_ResetDevice()", processed)
                    self.assertNotIn("R_RecoverLostDevice()", processed)
                    self.assertNotIn("R_CheckLostDevice()", processed)
                else:
                    self.assertIn("dx.device->EndScene()", processed)
                    self.assertIn("R_CanRecoverLostDevice()", processed)
                    self.assertIn("void R_ResetDevice()", processed)
                    self.assertIn("R_RecoverLostDevice()", processed)
                    self.assertIn("R_CheckLostDevice()", processed)


if __name__ == "__main__":
    unittest.main()
