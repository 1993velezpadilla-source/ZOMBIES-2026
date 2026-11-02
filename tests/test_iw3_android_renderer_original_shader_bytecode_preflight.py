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
#include <cstring>
struct Visits {
    unsigned count = 0;
    std::uint32_t offsets[8]{};
    std::uint16_t opcodes[8]{};
    bool predicate[8]{};
    bool reject = false;
};
static bool Collect(const IW3AndroidShaderInstruction &ins, void *context) {
    auto &visits = *static_cast<Visits *>(context);
    assert(visits.count < 8);
    visits.offsets[visits.count] = ins.tokenOffset;
    visits.opcodes[visits.count] = ins.opcode;
    visits.predicate[visits.count] = ins.predicated;
    ++visits.count;
    return !visits.reject;
}

struct ArithmeticVisits {
    unsigned count = 0;
    IW3AndroidShaderArithmetic records[4]{};
    bool reject = false;
};
static bool CollectArithmetic(const IW3AndroidShaderArithmetic &ins, void *context) {
    auto &visits = *static_cast<ArithmeticVisits *>(context);
    assert(visits.count < 4);
    visits.records[visits.count++] = ins;
    return !visits.reject;
}

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
    // D3D9 SM2/SM3 bit 28 adds a predicate source token to the encoded
    // instruction length. These are authentic token-frame shapes, not
    // executable/translated shaders or register-semantic validation.
    const std::uint32_t predMov[] = {
        0xFFFE0300u, 0x13000001u, 0x800F0000u, 0x90E40000u,
        0xB0E40000u, 0x0000FFFFu
    };
    const std::uint32_t predAdd[] = {
        0xFFFF0300u, 0x14000002u, 0x800F0000u, 0x90E40000u,
        0xA0E40000u, 0xB0E40000u, 0x0000FFFFu
    };
    const std::uint32_t missingPredMov[] = {
        0xFFFE0300u, 0x12000001u, 0x800F0000u, 0x90E40000u,
        0x0000FFFFu
    };
    const std::uint32_t missingPredAdd[] = {
        0xFFFF0300u, 0x13000002u, 0x800F0000u, 0x90E40000u,
        0xA0E40000u, 0x0000FFFFu
    };
    const std::uint32_t predNop[] = {
        0xFFFE0300u, 0x11000000u, 0xB0E40000u, 0x0000FFFFu
    };
    const std::uint32_t predDcl[] = {
        0xFFFE0300u, 0x1300001Fu, 0x00000005u, 0x900F0000u,
        0xB0E40000u, 0x0000FFFFu
    };
    assert(R_AndroidInspectD3D9Shader(predMov, sizeof(predMov),
                                     IW3AndroidShaderStage::Vertex, &info));
    assert(info.predicatedInstructionCount == 1 && info.instructionCount == 1);
    assert(R_AndroidInspectD3D9Shader(predAdd, sizeof(predAdd),
                                     IW3AndroidShaderStage::Pixel, &info));
    assert(info.predicatedInstructionCount == 1 && info.instructionCount == 1);
    assert(!R_AndroidInspectD3D9Shader(missingPredMov, sizeof(missingPredMov),
                                      IW3AndroidShaderStage::Vertex, &info));
    assert(!R_AndroidInspectD3D9Shader(missingPredAdd, sizeof(missingPredAdd),
                                      IW3AndroidShaderStage::Pixel, &info));
    assert(!R_AndroidInspectD3D9Shader(predNop, sizeof(predNop),
                                      IW3AndroidShaderStage::Vertex, &info));
    assert(!R_AndroidInspectD3D9Shader(predDcl, sizeof(predDcl),
                                      IW3AndroidShaderStage::Vertex, &info));
    assert(info.predicatedInstructionCount == 0);
    // Boundary visitor: complete prevalidation, COMMENT skipped, predication
    // preserved, explicit callback rejection, and unaligned input safety.
    Visits visits{};
    assert(R_AndroidVisitD3D9Shader(vs, sizeof(vs), IW3AndroidShaderStage::Vertex,
                                   Collect, &visits));
    assert(visits.count == 1 && visits.offsets[0] == 1 && visits.opcodes[0] == 1);
    visits = {};
    assert(R_AndroidVisitD3D9Shader(predAdd, sizeof(predAdd), IW3AndroidShaderStage::Pixel,
                                   Collect, &visits));
    assert(visits.count == 1 && visits.opcodes[0] == 2 && visits.predicate[0]);
    visits = {};
    assert(!R_AndroidVisitD3D9Shader(truncated, sizeof(truncated), IW3AndroidShaderStage::Vertex,
                                    Collect, &visits));
    assert(visits.count == 0);
    assert(!R_AndroidVisitD3D9Shader(vs, sizeof(vs), IW3AndroidShaderStage::Vertex,
                                    nullptr, &visits));
    visits = {};
    visits.reject = true;
    assert(!R_AndroidVisitD3D9Shader(vs, sizeof(vs), IW3AndroidShaderStage::Vertex,
                                    Collect, &visits));
    assert(visits.count == 1);
    unsigned char unaligned[sizeof(vs) + 1]{};
    std::memcpy(unaligned + 1, vs, sizeof(vs));
    visits = {};
    assert(R_AndroidVisitD3D9Shader(unaligned + 1, sizeof(vs),
                                   IW3AndroidShaderStage::Vertex, Collect, &visits));
    assert(visits.count == 1);
    assert(!R_AndroidInspectD3D9Shader(vs, sizeof(vs),
                                      static_cast<IW3AndroidShaderStage>(255), &info));
    assert(info.dwordCount == 0);

    // Decode original D3D9 register bitfields, not invented GLSL variables.
    IW3AndroidShaderRegister reg{};
    assert(R_AndroidDecodeD3D9Register(0x800F0000u, true, &reg));
    assert(reg.type == 0 && reg.number == 0 && reg.writeMask == 15);
    assert(R_AndroidDecodeD3D9Register(0x90E40003u, false, &reg));
    assert(reg.type == 1 && reg.number == 3 && reg.swizzle == 0xE4);
    assert(R_AndroidDecodeD3D9Register(0xB0E40802u, false, &reg));
    assert(reg.type == 11 && reg.number == 2); // split type bits 11..12
    assert(R_AndroidDecodeD3D9Register(0x90E42000u, false, &reg));
    assert(reg.relativeAddressing);
    assert(!R_AndroidDecodeD3D9Register(0x10E40000u, false, &reg));
    assert(!R_AndroidDecodeD3D9Register(0xF0E41800u, false, &reg));
    assert(!R_AndroidDecodeD3D9Register(0x9EE40000u, false, &reg));
    assert(!R_AndroidDecodeD3D9Register(0x80000000u, true, &reg));
    assert(reg.number == 0 && reg.writeMask == 0);

    const std::uint32_t arithmetic[] = {
        0xFFFE0300u,
        0x02000001u, 0x800F0000u, 0x90E40003u,
        0x03000002u, 0x80070001u, 0x80E40000u, 0xA0E40002u,
        0x0000FFFFu
    };
    ArithmeticVisits av{};
    assert(R_AndroidVisitD3D9Arithmetic(arithmetic, sizeof(arithmetic),
                                         IW3AndroidShaderStage::Vertex,
                                         CollectArithmetic, &av));
    assert(av.count == 2 && av.records[0].tokenOffset == 1);
    assert(av.records[0].opcode == 1 && av.records[0].sourceCount == 1);
    assert(av.records[0].sources[0].number == 3);
    assert(av.records[1].tokenOffset == 4 && av.records[1].opcode == 2);
    assert(av.records[1].destination.writeMask == 7);
    assert(av.records[1].sources[1].type == 2 && av.records[1].sources[1].number == 2);
    // Two-pass semantic validation: a later unsupported register must yield
    // ZERO earlier callbacks. Relative addressing requires separate tokens.
    const std::uint32_t lateRelative[] = {
        0xFFFE0300u,
        0x02000001u, 0x800F0000u, 0x90E40000u,
        0x03000002u, 0x800F0000u, 0x90E42000u, 0xA0E40000u,
        0x0000FFFFu
    };
    av = {};
    assert(!R_AndroidVisitD3D9Arithmetic(lateRelative, sizeof(lateRelative),
                                          IW3AndroidShaderStage::Vertex,
                                          CollectArithmetic, &av));
    assert(av.count == 0);
    av = {};
    assert(!R_AndroidVisitD3D9Arithmetic(predMov, sizeof(predMov),
                                          IW3AndroidShaderStage::Vertex,
                                          CollectArithmetic, &av));
    assert(av.count == 0);
    av = {};
    assert(R_AndroidVisitD3D9Arithmetic(vs, sizeof(vs),
                                         IW3AndroidShaderStage::Vertex,
                                         CollectArithmetic, &av));
    assert(av.count == 1); // COMMENT payload skipped

    const std::uint32_t unsupportedOpcode[] = {
        0xFFFE0300u, 0x00000005u, 0x0000FFFFu
    };
    av = {};
    assert(!R_AndroidVisitD3D9Arithmetic(unsupportedOpcode, sizeof(unsupportedOpcode),
                                          IW3AndroidShaderStage::Vertex,
                                          CollectArithmetic, &av));
    assert(av.count == 0);
    av = {};
    av.reject = true;
    assert(!R_AndroidVisitD3D9Arithmetic(arithmetic, sizeof(arithmetic),
                                          IW3AndroidShaderStage::Vertex,
                                          CollectArithmetic, &av));
    assert(av.count == 1);
    assert(!R_AndroidVisitD3D9Arithmetic(arithmetic, sizeof(arithmetic),
                                          IW3AndroidShaderStage::Vertex,
                                          nullptr, &av));

    std::puts("IW3_ORIGINAL_D3D9_SHADER_PREDICATION_PASS_NOT_TRANSLATED");
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
            self.assertIn("IW3_ORIGINAL_D3D9_SHADER_PREDICATION_PASS_NOT_TRANSLATED", run.stdout)

if __name__ == "__main__":
    unittest.main()
