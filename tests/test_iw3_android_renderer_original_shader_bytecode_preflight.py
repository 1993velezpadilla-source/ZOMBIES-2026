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
#include <string>
#include <vector>
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


struct DeclarationVisits {
    unsigned count = 0;
    IW3AndroidShaderDeclaration records[8]{};
    bool reject = false;
};
static bool CollectDeclaration(const IW3AndroidShaderDeclaration &decl, void *context) {
    auto &visits = *static_cast<DeclarationVisits *>(context);
    assert(visits.count < 8);
    visits.records[visits.count++] = decl;
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


struct DecodedVisits {
    unsigned count = 0;
    IW3AndroidShaderDecodedKind kinds[8]{};
    std::uint32_t offsets[8]{};
    bool reject = false;
};
static bool CollectDecoded(const IW3AndroidShaderDecodedInstruction &record,
                           void *context) {
    auto &visits = *static_cast<DecodedVisits *>(context);
    assert(visits.count < 8);
    visits.kinds[visits.count] = record.kind;
    visits.offsets[visits.count] = record.tokenOffset;
    if (record.kind == IW3AndroidShaderDecodedKind::Declaration)
        assert(record.declaration.tokenOffset == record.tokenOffset);
    else
        assert(record.arithmetic.tokenOffset == record.tokenOffset);
    ++visits.count;
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


    // D3D9 SM3 vertex DCL: input TEXCOORD0, output COLOR1,
    // sampler 2D. This tests original metadata, not GLES VAOs/programs.
    const std::uint32_t declarations[] = {
        0xFFFE0300u,
        0x0200001Fu, 0x00000005u, 0x900F0000u,
        0x0200001Fu, 0x0001000Au, 0xE00F0001u,
        0x0200001Fu, 0x10000000u, 0xA00F0800u,
        0x02000001u, 0x800F0000u, 0x90E40000u,
        0x0000FFFFu
    };
    DeclarationVisits dv{};
    assert(R_AndroidVisitD3D9Declarations(declarations, sizeof(declarations),
            IW3AndroidShaderStage::Vertex, CollectDeclaration, &dv));
    assert(dv.count == 3 && dv.records[0].tokenOffset == 1);
    assert(dv.records[0].usage == 5 && dv.records[0].usageIndex == 0);
    assert(dv.records[0].registerOperand.type == 1);
    assert(dv.records[1].usage == 10 && dv.records[1].usageIndex == 1);
    assert(dv.records[1].registerOperand.type == 6);
    assert(dv.records[2].sampler && dv.records[2].samplerTextureType == 2);
    assert(dv.records[2].registerOperand.type == 10);
    // Pixel SM2 texcoord input and cube sampler declaration.
    const std::uint32_t pixelDeclarations[] = {
        0xFFFF0200u,
        0x0200001Fu, 0x00000005u, 0xB00F0000u,
        0x0200001Fu, 0x18000000u, 0xA00F0801u,
        0x0000FFFFu
    };
    dv = {};
    assert(R_AndroidVisitD3D9Declarations(pixelDeclarations, sizeof(pixelDeclarations),
            IW3AndroidShaderStage::Pixel, CollectDeclaration, &dv));
    assert(dv.count == 2 && dv.records[1].sampler);
    assert(dv.records[1].samplerTextureType == 3);
    // A later invalid DCL must produce NO partial callback output.
    const std::uint32_t lateBadDeclaration[] = {
        0xFFFE0300u,
        0x0200001Fu, 0x00000005u, 0x900F0000u,
        0x0200001Fu, 0x0000000Eu, 0x900F0001u,
        0x0000FFFFu
    };
    dv = {};
    assert(!R_AndroidVisitD3D9Declarations(lateBadDeclaration,
            sizeof(lateBadDeclaration), IW3AndroidShaderStage::Vertex,
            CollectDeclaration, &dv));
    assert(dv.count == 0);
    const std::uint32_t invalidSampler[] = {
        0xFFFE0300u, 0x0200001Fu, 0x08000000u,
        0xA00F0800u, 0x0000FFFFu
    };
    dv = {};
    assert(!R_AndroidVisitD3D9Declarations(invalidSampler, sizeof(invalidSampler),
            IW3AndroidShaderStage::Vertex, CollectDeclaration, &dv));
    assert(dv.count == 0);
    const std::uint32_t relativeDeclaration[] = {
        0xFFFE0300u, 0x0200001Fu, 0x00000005u,
        0x900F2000u, 0x0000FFFFu
    };
    assert(!R_AndroidVisitD3D9Declarations(relativeDeclaration,
            sizeof(relativeDeclaration), IW3AndroidShaderStage::Vertex,
            CollectDeclaration, &dv));
    // Vertex shader output DCL is not a pixel shader input declaration.
    const std::uint32_t invalidPixelOutput[] = {
        0xFFFF0300u, 0x0200001Fu, 0x0000000Au,
        0xE00F0000u, 0x0000FFFFu
    };
    assert(!R_AndroidVisitD3D9Declarations(invalidPixelOutput,
            sizeof(invalidPixelOutput), IW3AndroidShaderStage::Pixel,
            CollectDeclaration, &dv));
    // Shader-model constraints: VS2 has no vertex texture samplers and
    // PS3 uses v# input declarations, not the old PS2 t# class.
    const std::uint32_t vs2Sampler[] = {
        0xFFFE0200u, 0x0200001Fu, 0x10000000u,
        0xA00F0800u, 0x0000FFFFu
    };
    const std::uint32_t ps3Texcoord[] = {
        0xFFFF0300u, 0x0200001Fu, 0x00000005u,
        0xB00F0000u, 0x0000FFFFu
    };
    assert(!R_AndroidVisitD3D9Declarations(vs2Sampler, sizeof(vs2Sampler),
            IW3AndroidShaderStage::Vertex, CollectDeclaration, &dv));
    assert(!R_AndroidVisitD3D9Declarations(ps3Texcoord, sizeof(ps3Texcoord),
            IW3AndroidShaderStage::Pixel, CollectDeclaration, &dv));
    assert(dv.count == 0);
    dv = {};
    dv.reject = true;
    assert(!R_AndroidVisitD3D9Declarations(declarations, sizeof(declarations),
            IW3AndroidShaderStage::Vertex, CollectDeclaration, &dv));
    assert(dv.count == 1);
    assert(!R_AndroidVisitD3D9Declarations(declarations, sizeof(declarations),
            IW3AndroidShaderStage::Vertex, nullptr, &dv));
    dv = {};
    assert(!R_AndroidVisitD3D9Declarations(unsupportedOpcode,
            sizeof(unsupportedOpcode), IW3AndroidShaderStage::Vertex,
            CollectDeclaration, &dv));
    assert(dv.count == 0);


    // Unified original bytecode subset: DCL and arithmetic coexist and
    // retain exact order. Neither old single-kind visitor can do this.
    DecodedVisits uv{};
    assert(R_AndroidVisitD3D9DecodedShader(declarations, sizeof(declarations),
            IW3AndroidShaderStage::Vertex, CollectDecoded, &uv));
    assert(uv.count == 4);
    assert(uv.kinds[0] == IW3AndroidShaderDecodedKind::Declaration);
    assert(uv.kinds[1] == IW3AndroidShaderDecodedKind::Declaration);
    assert(uv.kinds[2] == IW3AndroidShaderDecodedKind::Declaration);
    assert(uv.kinds[3] == IW3AndroidShaderDecodedKind::Arithmetic);
    assert(uv.offsets[0] == 1 && uv.offsets[1] == 4);
    assert(uv.offsets[2] == 7 && uv.offsets[3] == 10);
    uv = {};
    assert(R_AndroidVisitD3D9DecodedShader(arithmetic, sizeof(arithmetic),
            IW3AndroidShaderStage::Vertex, CollectDecoded, &uv));
    assert(uv.count == 2 && uv.kinds[0] == IW3AndroidShaderDecodedKind::Arithmetic);
    // Late malformed arithmetic must produce zero callbacks despite a
    // valid earlier declaration; relative addressing is not decoded yet.
    const std::uint32_t dclThenBadMov[] = {
        0xFFFE0300u,
        0x0200001Fu, 0x00000005u, 0x900F0000u,
        0x02000001u, 0x800F0000u, 0x90E42000u,
        0x0000FFFFu
    };
    uv = {};
    assert(!R_AndroidVisitD3D9DecodedShader(dclThenBadMov,
            sizeof(dclThenBadMov), IW3AndroidShaderStage::Vertex,
            CollectDecoded, &uv));
    assert(uv.count == 0);
    // DCL after arithmetic is invalid, and must not leak the earlier MOV.
    const std::uint32_t lateDcl[] = {
        0xFFFE0300u,
        0x02000001u, 0x800F0000u, 0x90E40000u,
        0x0200001Fu, 0x00000005u, 0x900F0000u,
        0x0000FFFFu
    };
    uv = {};
    assert(!R_AndroidVisitD3D9DecodedShader(lateDcl, sizeof(lateDcl),
            IW3AndroidShaderStage::Vertex, CollectDecoded, &uv));
    assert(uv.count == 0);
    uv = {};
    assert(!R_AndroidVisitD3D9DecodedShader(lateBadDeclaration,
            sizeof(lateBadDeclaration), IW3AndroidShaderStage::Vertex,
            CollectDecoded, &uv));
    assert(uv.count == 0);
    uv = {};
    assert(!R_AndroidVisitD3D9DecodedShader(predMov, sizeof(predMov),
            IW3AndroidShaderStage::Vertex, CollectDecoded, &uv));
    assert(uv.count == 0);
    uv = {};
    assert(!R_AndroidVisitD3D9DecodedShader(unsupportedOpcode,
            sizeof(unsupportedOpcode), IW3AndroidShaderStage::Vertex,
            CollectDecoded, &uv));
    assert(uv.count == 0);
    uv = {};
    uv.reject = true;
    assert(!R_AndroidVisitD3D9DecodedShader(declarations,
            sizeof(declarations), IW3AndroidShaderStage::Vertex,
            CollectDecoded, &uv));
    assert(uv.count == 1);
    uv = {};
    assert(!R_AndroidVisitD3D9DecodedShader(declarations,
            sizeof(declarations), IW3AndroidShaderStage::Vertex,
            nullptr, &uv));
    unsigned char unalignedMixed[sizeof(declarations) + 1]{};
    std::memcpy(unalignedMixed + 1, declarations, sizeof(declarations));
    assert(R_AndroidVisitD3D9DecodedShader(unalignedMixed + 1,
            sizeof(declarations), IW3AndroidShaderStage::Vertex,
            CollectDecoded, &uv));
    assert(uv.count == 4);


    // First faithful D3D9 ps_3_0 -> GLSL ES 3.0 source emission.
    // This is NOT a GPU program, renderer, map or playable APK.
    const std::uint32_t ps3Color[] = {
        0xFFFF0300u,
        0x0200001Fu, 0x0000000Au, 0x900F0000u, // dcl_color0 v0
        0x02000001u, 0x800F0000u, 0x90E40000u, // mov r0, v0
        0x03000002u, 0x800F0800u, 0x80E40000u,
                     0x90E40000u, // add oC0, r0, v0
        0x0000FFFFu
    };
    std::string glsl = "must-clear";
    assert(R_AndroidTranslateD3D9PixelColorSubsetToGLSL(
        ps3Color, sizeof(ps3Color), &glsl));
    assert(glsl.find("#version 300 es") != std::string::npos);
    assert(glsl.find("iw3_r0 = iw3_color_in0;") != std::string::npos);
    assert(glsl.find("iw3_color_out0 = iw3_r0 + iw3_color_in0;") != std::string::npos);
    assert(!R_AndroidTranslateD3D9PixelColorSubsetToGLSL(
        ps3Color, sizeof(ps3Color), nullptr));
    // No implicit shader input, no uninitialized temp, no silently dropped
    // swizzle, modifier or partial component write.
    const std::uint32_t missingDcl[] = {
        0xFFFF0300u, 0x02000001u, 0x800F0800u, 0x90E40000u, 0x0000FFFFu
    };
    const std::uint32_t readBeforeWrite[] = {
        0xFFFF0300u, 0x0200001Fu, 0x0000000Au, 0x900F0000u,
        0x03000002u, 0x800F0800u, 0x80E40000u, 0x90E40000u,
        0x0000FFFFu
    };
    const std::uint32_t noColorOutput[] = {
        0xFFFF0300u, 0x0200001Fu, 0x0000000Au, 0x900F0000u,
        0x02000001u, 0x800F0000u, 0x90E40000u, 0x0000FFFFu
    };
    const std::uint32_t partialColor[] = {
        0xFFFF0300u, 0x0200001Fu, 0x0000000Au, 0x900F0000u,
        0x02000001u, 0x80070800u, 0x90E40000u, 0x0000FFFFu
    };
    const std::uint32_t swizzledInput[] = {
        0xFFFF0300u, 0x0200001Fu, 0x0000000Au, 0x900F0000u,
        0x02000001u, 0x800F0800u, 0x90000000u, 0x0000FFFFu
    };
    const std::uint32_t modifiedInput[] = {
        0xFFFF0300u, 0x0200001Fu, 0x0000000Au, 0x900F0000u,
        0x02000001u, 0x800F0800u, 0x91E40000u, 0x0000FFFFu
    };
    const std::uint32_t lateUnsupported[] = {
        0xFFFF0300u, 0x0200001Fu, 0x0000000Au, 0x900F0000u,
        0x02000001u, 0x800F0800u, 0x90E40000u,
        0x01000003u, 0x800F0000u, 0x0000FFFFu
    };
    const std::uint32_t *badShaders[] = {
        missingDcl, readBeforeWrite, noColorOutput, partialColor,
        swizzledInput, modifiedInput, lateUnsupported
    };
    const std::size_t badSizes[] = {
        sizeof(missingDcl), sizeof(readBeforeWrite), sizeof(noColorOutput),
        sizeof(partialColor), sizeof(swizzledInput), sizeof(modifiedInput),
        sizeof(lateUnsupported)
    };
    for (std::size_t i = 0; i < sizeof(badShaders)/sizeof(badShaders[0]); ++i) {
        glsl = "must-clear";
        assert(!R_AndroidTranslateD3D9PixelColorSubsetToGLSL(
            badShaders[i], badSizes[i], &glsl));
        assert(glsl.empty());
    }
    glsl = "must-clear";
    assert(!R_AndroidTranslateD3D9PixelColorSubsetToGLSL(
        ps3Color, sizeof(ps3Color) - 4, &glsl));
    assert(glsl.empty());
    // No accidental stage/version acceptance: vs_3_0 and ps_2_0 fail.
    auto stageMismatch = std::vector<std::uint32_t>(
        ps3Color, ps3Color + sizeof(ps3Color)/sizeof(ps3Color[0]));
    stageMismatch[0] = 0xFFFE0300u;
    assert(!R_AndroidTranslateD3D9PixelColorSubsetToGLSL(
        stageMismatch.data(), stageMismatch.size()*4, &glsl));
    stageMismatch[0] = 0xFFFF0200u;
    assert(!R_AndroidTranslateD3D9PixelColorSubsetToGLSL(
        stageMismatch.data(), stageMismatch.size()*4, &glsl));


    // Original vs_3_0 DCL/MOV stream. The two GLSL stages share a
    // name-matched varying, not a forbidden ES3 fragment-input location.
    const std::uint32_t vs3PositionColor[] = {
        0xFFFE0300u,
        0x0200001Fu, 0x00000000u, 0x900F0000u, // dcl_position0 v0
        0x0200001Fu, 0x0000000Au, 0x900F0001u, // dcl_color0 v1
        0x0200001Fu, 0x00000000u, 0xE00F0000u, // dcl_position0 o0
        0x0200001Fu, 0x0000000Au, 0xE00F0001u, // dcl_color0 o1
        0x02000001u, 0xE00F0000u, 0x90E40000u, // mov o0, v0
        0x02000001u, 0xE00F0001u, 0x90E40001u, // mov o1, v1
        0x0000FFFFu
    };
    std::string vertexGLSL = "must-clear";
    assert(R_AndroidTranslateD3D9VertexPositionColorSubsetToGLSL(
        vs3PositionColor, sizeof(vs3PositionColor), &vertexGLSL));
    assert(vertexGLSL.find("#version 300 es") != std::string::npos);
    assert(vertexGLSL.find("iw3_clip_position = iw3_position_in0;") != std::string::npos);
    assert(vertexGLSL.find("iw3_color_in0 = iw3_vertex_color_in0;") != std::string::npos);
    assert(vertexGLSL.find("2.0 * iw3_clip_position.z - iw3_clip_position.w") != std::string::npos);
    assert(vertexGLSL.find("out vec4 iw3_color_in0;") != std::string::npos);
    assert(glsl.find("in vec4 iw3_color_in0;") != std::string::npos);
    assert(glsl.find("layout(location = 0) in vec4") == std::string::npos);
    assert(!R_AndroidTranslateD3D9VertexPositionColorSubsetToGLSL(
        vs3PositionColor, sizeof(vs3PositionColor), nullptr));
    auto badVertex = std::vector<std::uint32_t>(
        vs3PositionColor,
        vs3PositionColor + sizeof(vs3PositionColor)/sizeof(vs3PositionColor[0]));
    const auto expectBadVertex = [&](const std::vector<std::uint32_t> &tokens) {
        vertexGLSL = "must-clear";
        assert(!R_AndroidTranslateD3D9VertexPositionColorSubsetToGLSL(
            tokens.data(), tokens.size()*sizeof(std::uint32_t), &vertexGLSL));
        assert(vertexGLSL.empty());
    };
    badVertex[0] = 0xFFFF0300u; // Pixel-stage token stream is not a VS.
    expectBadVertex(badVertex);
    badVertex[0] = 0xFFFE0200u; // SM2 not silently treated as SM3.
    expectBadVertex(badVertex);
    badVertex[0] = 0xFFFE0300u;
    badVertex[8] = 0x00000005u; // Unsupported TEXCOORD semantic on o0.
    expectBadVertex(badVertex);
    badVertex[8] = 0x00000000u;
    badVertex[15] = 0x90000000u; // Nonidentity swizzle on position input.
    expectBadVertex(badVertex);
    badVertex[15] = 0x90E40000u;
    badVertex[17] = 0xE0070001u; // Partial color output mask.
    expectBadVertex(badVertex);
    badVertex[17] = 0xE00F0001u;
    badVertex[16] = 0x03000002u; // Unsupported ADD, must fail closed.
    expectBadVertex(badVertex);
    badVertex[16] = 0x02000001u;
    badVertex[18] = 0x90E40000u; // Wrong input for COLOR0.
    expectBadVertex(badVertex);
    badVertex[18] = 0x90E40001u;
    badVertex[4] = 0x02000001u; // Late malformed DCL => no GLSL.
    expectBadVertex(badVertex);
    vertexGLSL = "must-clear";
    assert(!R_AndroidTranslateD3D9VertexPositionColorSubsetToGLSL(
        vs3PositionColor, sizeof(vs3PositionColor) - 4, &vertexGLSL));
    assert(vertexGLSL.empty());
    std::puts("IW3_ORIGINAL_D3D9_VS3_PS3_GLSL_SOURCE_PAIR_PASS_NOT_GPU");

    std::puts("IW3_ORIGINAL_D3D9_SHADER_COLOR0_GLSL_SUBSET_PASS_NOT_GPU");
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
            self.assertIn("IW3_ORIGINAL_D3D9_SHADER_COLOR0_GLSL_SUBSET_PASS_NOT_GPU", run.stdout)

if __name__ == "__main__":
    unittest.main()
