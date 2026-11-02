"""Bounded original KisakCOD IW3 D3D9 shader-token walk: NOT GLSL/NOT GAME."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
GFX = ROOT / "third_party/KisakCOD/src/gfx_d3d"
HARNESS = r'''
#include "r_android_shader_bytecode.h"
#include <cassert>
#include <cstdint>
#include <cstdio>
int main() {
    // Real D3D9 token framing: MOV has two operands, ADD has three.
    // A COMMENT payload is arbitrary data, including the END bit pattern.
    const std::uint32_t vs[] = {
        0xFFFE0300u, 0x02000001u, 0x800F0000u, 0x90E40000u,
        0x0002FFFEu, 0x0000FFFFu, 0xDEADBEEFu, 0x0000FFFFu
    };
    const std::uint32_t ps[] = {
        0xFFFF0200u, 0x03000002u, 0x800F0000u, 0x90E40000u,
        0xA0E40000u, 0x0000FFFFu
    };
    IW3AndroidShaderEnvelope info{};
    assert(R_AndroidInspectD3D9Shader(vs, sizeof(vs), IW3AndroidShaderStage::Vertex, &info));
    assert(info.major == 3 && info.minor == 0 && info.dwordCount == 8);
    assert(info.instructionCount == 1 && info.commentCount == 1);
    assert(R_AndroidInspectD3D9Shader(ps, sizeof(ps), IW3AndroidShaderStage::Pixel, &info));
    assert(info.major == 2 && info.instructionCount == 1 && info.commentCount == 0);
    assert(!R_AndroidInspectD3D9Shader(vs, sizeof(vs), IW3AndroidShaderStage::Pixel, &info));
    assert(info.dwordCount == 0 && info.instructionCount == 0);
    assert(!R_AndroidInspectD3D9Shader(nullptr, sizeof(vs), IW3AndroidShaderStage::Vertex, &info));
    assert(!R_AndroidInspectD3D9Shader(vs, sizeof(vs), IW3AndroidShaderStage::Vertex, nullptr));
    assert(!R_AndroidInspectD3D9Shader(vs, 7, IW3AndroidShaderStage::Vertex, &info));
    assert(!R_AndroidInspectD3D9Shader(vs, sizeof(vs)-4, IW3AndroidShaderStage::Vertex, &info));
    const std::uint32_t early[] = {0xFFFE0300u, 0x0000FFFFu, 0x0000FFFFu};
    assert(!R_AndroidInspectD3D9Shader(early, sizeof(early), IW3AndroidShaderStage::Vertex, &info));
    const std::uint32_t invalid[] = {0xFFFE0400u, 0x00000001u, 0x0000FFFFu};
    assert(!R_AndroidInspectD3D9Shader(invalid, sizeof(invalid), IW3AndroidShaderStage::Vertex, &info));
    const std::uint32_t badEnd[] = {0xFFFF0300u, 0x00000000u, 0x0000FFFEu};
    assert(!R_AndroidInspectD3D9Shader(badEnd, sizeof(badEnd), IW3AndroidShaderStage::Pixel, &info));
    const std::uint32_t truncated[] = {0xFFFE0300u, 0x03000002u, 0x800F0000u, 0x0000FFFFu};
    assert(!R_AndroidInspectD3D9Shader(truncated, sizeof(truncated), IW3AndroidShaderStage::Vertex, &info));
    const std::uint32_t badComment[] = {0xFFFE0300u, 0x0003FFFEu, 0x0000FFFFu};
    assert(!R_AndroidInspectD3D9Shader(badComment, sizeof(badComment), IW3AndroidShaderStage::Vertex, &info));
    const std::uint32_t swallowedEnd[] = {0xFFFE0300u, 0x0001FFFEu, 0x0000FFFFu};
    assert(!R_AndroidInspectD3D9Shader(swallowedEnd, sizeof(swallowedEnd), IW3AndroidShaderStage::Vertex, &info));
    const std::uint32_t badMov[] = {0xFFFE0300u, 0x01000001u, 0x800F0000u, 0x0000FFFFu};
    assert(!R_AndroidInspectD3D9Shader(badMov, sizeof(badMov), IW3AndroidShaderStage::Vertex, &info));
    const std::uint32_t badDcl[] = {0xFFFE0300u, 0x0100001Fu, 0x800F0000u, 0x0000FFFFu};
    assert(!R_AndroidInspectD3D9Shader(badDcl, sizeof(badDcl), IW3AndroidShaderStage::Vertex, &info));
    // An operand equal to END must not terminate the instruction stream.
    // This is token framing only; register semantics remain unvalidated.
    const std::uint32_t operandEnd[] = {
        0xFFFE0300u, 0x02000001u, 0x0000FFFFu, 0x90E40000u, 0x0000FFFFu
    };
    assert(R_AndroidInspectD3D9Shader(operandEnd, sizeof(operandEnd),
                                     IW3AndroidShaderStage::Vertex, &info));
    std::puts("IW3_ORIGINAL_D3D9_SHADER_TOKEN_WALK_PASS_NOT_TRANSLATED");
}
'''

class OriginalShaderBytecodePreflight(unittest.TestCase):
    def test_original_shader_load_and_bind_are_explicitly_fail_closed(self):
        material = (GFX/"r_material.cpp").read_text()
        shade = (GFX/"rb_shade.cpp").read_text()
        self.assertIn("R_AndroidInspectD3D9Shader(", material)
        self.assertIn("IW3 Android shader bytecode needs GLES3 translation", material)
        self.assertIn("IW3 Android shader binding requires translated GLES3 program", shade)
        self.assertIn("dx.device->CreatePixelShader(", material)
        self.assertIn("dx.device->CreateVertexShader(", material)
        self.assertIn("device->SetPixelShader(", shade)
        self.assertIn("device->SetVertexShader(", shade)

    def test_sanitized_host_token_framing(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            (tmp/"test.cpp").write_text(HARNESS)
            binary = tmp/"test"
            build = subprocess.run([os.environ.get("CXX","g++"), "-std=c++17",
                "-D__ANDROID__", "-UNDEBUG", "-O1", "-g",
                "-fsanitize=address,undefined", "-fno-omit-frame-pointer",
                "-I", str(GFX), str(tmp/"test.cpp"),
                str(GFX/"r_android_shader_bytecode.cpp"), "-o", str(binary)],
                capture_output=True, text=True, timeout=90)
            self.assertEqual(build.returncode, 0, build.stdout+build.stderr)
            env = os.environ.copy()
            env["ASAN_OPTIONS"] = "detect_leaks=1"
            run = subprocess.run([str(binary)], capture_output=True, text=True,
                                 env=env, timeout=30)
            self.assertEqual(run.returncode, 0, run.stdout+run.stderr)
            self.assertIn("IW3_ORIGINAL_D3D9_SHADER_TOKEN_WALK_PASS_NOT_TRANSLATED", run.stdout)

if __name__ == "__main__":
    unittest.main()
