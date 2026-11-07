#if defined(__ANDROID__)
#include "r_android_shader_bytecode.h"
#include <cstring>

namespace {
std::uint32_t ReadDword(const unsigned char *data)
{
    std::uint32_t word = 0;
    std::memcpy(&word, data, sizeof(word));
    return word;
}
}

bool R_AndroidInspectD3D9Shader(const void *program, std::size_t programBytes,
                               IW3AndroidShaderStage stage,
                               IW3AndroidShaderEnvelope *out)
{
    if (out) *out = {};
    // Original IW3 load definitions store a uint16_t byte length. Never
    // scan past that serialized size or assume an unterminated shader ends.
    if (!program || !out || programBytes < 8 || programBytes > 65535
        || (programBytes & 3u) != 0)
        return false;

    if (stage != IW3AndroidShaderStage::Vertex && stage != IW3AndroidShaderStage::Pixel)
        return false;
    const auto *bytes = static_cast<const unsigned char *>(program);
    const std::uint32_t version = ReadDword(bytes);
    const std::uint32_t expectedTag =
        stage == IW3AndroidShaderStage::Vertex ? 0xFFFE0000u : 0xFFFF0000u;
    if ((version & 0xFFFF0000u) != expectedTag)
        return false;
    const std::uint8_t major = static_cast<std::uint8_t>((version >> 8) & 0xFFu);
    const std::uint8_t minor = static_cast<std::uint8_t>(version & 0xFFu);
    if ((major != 2 && major != 3) || (major == 3 && minor != 0))
        return false;

    // D3D9 SM2/SM3 instruction tokens encode the number of following DWORDs
    // in bits 24..27. COMMENT (opcode 0xFFFE) instead uses bits 16..30 for
    // its payload count. Payload/operand words are DATA, not opcodes: a
    // literal 0x0000FFFF there must never be mistaken for shader END.
    const std::size_t words = programBytes / sizeof(std::uint32_t);
    std::size_t i = 1;
    std::uint32_t instructions = 0, comments = 0, predicatedInstructions = 0;
    bool terminated = false;
    while (i < words) {
        const std::uint32_t token = ReadDword(bytes + i * sizeof(std::uint32_t));
        const std::uint32_t opcode = token & 0xFFFFu;
        const std::size_t remaining = words - i - 1;
        if (opcode == 0xFFFFu) {
            // END is exactly 0x0000FFFF and must be the final token.
            if (token != 0x0000FFFFu || remaining != 0)
                return false;
            terminated = true;
            break;
        }
        if (opcode == 0xFFFEu) {
            const std::size_t payload = (token >> 16) & 0x7FFFu;
            if (payload > remaining) return false;
            i += payload + 1;
            ++comments;
            continue;
        }
        // PHASE is a pixel-shader 1.x control token, not SM2/SM3.
        if (opcode == 0xFFFDu) return false;

        const std::size_t operands = (token >> 24) & 0xFu;
        if (operands > remaining) return false;
        // Shader Model 2/3 instruction bit 28 marks predication. The
        // predicate source token is INCLUDED in the encoded length (bits
        // 24..27). The previous fixed MOV/ADD counts rejected legitimate
        // predicated instructions and could accept truncated ones.
        const bool predicated = (token & 0x10000000u) != 0;
        const std::size_t predicateTokens = predicated ? 1u : 0u;
        // NOP and DCL are not predicable; keep the supported opcode
        // checks conservative. Other opcode/register semantics still
        // require a complete D3D9 decoder before GLSL translation.
        if ((opcode == 0 && (predicated || operands != 0)) // NOP
            || (opcode == 1 && operands != 2u + predicateTokens) // MOV
            || (opcode == 2 && operands != 3u + predicateTokens) // ADD
            || (opcode == 31 && (predicated || operands != 2))) // DCL
            return false;
        ++instructions;
        if (predicated) ++predicatedInstructions;
        i += operands + 1;
    }
    if (!terminated) return false;
    out->major = major;
    out->minor = minor;
    out->dwordCount = static_cast<std::uint32_t>(words);
    out->instructionCount = instructions;
    out->commentCount = comments;
    out->predicatedInstructionCount = predicatedInstructions;
    return true;
}

// Two-pass boundary walk: never expose a prefix of a malformed stream to a
// translator. Original D3D9 operand words are deliberately NOT interpreted.
bool R_AndroidVisitD3D9Shader(const void *program, std::size_t programBytes,
                             IW3AndroidShaderStage stage,
                             IW3AndroidShaderVisitor visitor, void *user)
{
    IW3AndroidShaderEnvelope envelope{};
    if (!visitor || !R_AndroidInspectD3D9Shader(program, programBytes, stage, &envelope))
        return false;
    const auto *bytes = static_cast<const unsigned char *>(program);
    std::size_t i = 1;
    while (i < envelope.dwordCount) {
        const std::uint32_t token = ReadDword(bytes + i * sizeof(std::uint32_t));
        const std::uint32_t opcode = token & 0xFFFFu;
        if (opcode == 0xFFFFu) return true;
        if (opcode == 0xFFFEu) {
            i += 1u + ((token >> 16) & 0x7FFFu);
            continue;
        }
        const auto operands = static_cast<std::uint8_t>((token >> 24) & 0xFu);
        const IW3AndroidShaderInstruction record{
            static_cast<std::uint32_t>(i), token,
            static_cast<std::uint16_t>(opcode), operands,
            (token & 0x10000000u) != 0
        };
        if (!visitor(record, user)) return false;
        i += 1u + operands;
    }
    return false;
}

bool R_AndroidDecodeD3D9Register(std::uint32_t token, bool destination,
                                 IW3AndroidShaderRegister *out)
{
    if (out) *out = {};
    // D3D9 register tokens have bit 31 set. Register type uses two
    // NONCONTIGUOUS fields: bits 28..30 and bits 11..12.
    if (!out || (token & 0x80000000u) == 0) return false;
    const auto type = static_cast<std::uint8_t>(
        ((token >> 28) & 7u) | ((token >> 8) & 0x18u));
    // D3DSPR_PREDICATE is 19; 20..31 are not D3D9 register types.
    if (type > 19) return false;
    const auto modifier = static_cast<std::uint8_t>(
        (token >> (destination ? 20u : 24u)) & 15u);
    // Destination modifiers are a three-bit combination of SATURATE,
    // PARTIALPRECISION and CENTROID. Source modifiers 14/15 are reserved.
    if ((destination && modifier > 7) || (!destination && modifier > 13))
        return false;
    const auto writeMask = static_cast<std::uint8_t>((token >> 16) & 15u);
    if (destination && writeMask == 0) return false;
    out->number = static_cast<std::uint16_t>(token & 0x7FFu);
    out->type = type;
    out->writeMask = destination ? writeMask : 0;
    out->swizzle = destination ? 0 : static_cast<std::uint8_t>((token >> 16) & 255u);
    out->modifier = modifier;
    out->destinationShift = destination ? static_cast<std::uint8_t>((token >> 24) & 15u) : 0;
    out->relativeAddressing = (token & 0x00002000u) != 0;
    return true;
}

namespace {
struct ArithmeticWalk {
    const unsigned char *bytes;
    IW3AndroidShaderArithmeticVisitor visitor;
    void *user;
    bool validateOnly;
};
bool WalkArithmetic(const IW3AndroidShaderInstruction &ins, void *context)
{
    auto &state = *static_cast<ArithmeticWalk *>(context);
    if (ins.opcode == 0) return true; // NOP, already length-checked.
    // Never silently drop unsupported original instructions or predication.
    if ((ins.opcode != 1 && ins.opcode != 2) || ins.predicated)
        return false;
    const std::uint8_t sourceCount = ins.opcode == 1 ? 1 : 2;
    if (ins.operandTokenCount != sourceCount + 1) return false;
    IW3AndroidShaderArithmetic decoded{};
    decoded.tokenOffset = ins.tokenOffset;
    decoded.opcode = ins.opcode;
    decoded.sourceCount = sourceCount;
    const auto *operandBytes = state.bytes + (ins.tokenOffset + 1u) * sizeof(std::uint32_t);
    if (!R_AndroidDecodeD3D9Register(ReadDword(operandBytes), true,
                                     &decoded.destination)
        || decoded.destination.relativeAddressing)
        return false;
    for (std::uint8_t n = 0; n < sourceCount; ++n) {
        if (!R_AndroidDecodeD3D9Register(
                ReadDword(operandBytes + (n + 1u) * sizeof(std::uint32_t)),
                false, &decoded.sources[n])
            || decoded.sources[n].relativeAddressing)
            return false;
    }
    return state.validateOnly || state.visitor(decoded, state.user);
}
} // namespace

bool R_AndroidVisitD3D9Arithmetic(const void *program, std::size_t programBytes,
                                  IW3AndroidShaderStage stage,
                                  IW3AndroidShaderArithmeticVisitor visitor, void *user)
{
    if (!visitor) return false;
    // The boundary walker itself validates the WHOLE original stream first.
    // First semantic pass ensures no partially decoded shader is exposed if
    // an unsupported instruction or register occurs later in the stream.
    ArithmeticWalk state{static_cast<const unsigned char *>(program),
                         visitor, user, true};
    if (!R_AndroidVisitD3D9Shader(program, programBytes, stage,
                                 WalkArithmetic, &state))
        return false;
    state.validateOnly = false;
    return R_AndroidVisitD3D9Shader(program, programBytes, stage,
                                   WalkArithmetic, &state);
}


namespace {
struct DeclarationWalk {
    const unsigned char *bytes;
    IW3AndroidShaderStage stage;
    std::uint8_t shaderMajor;
    IW3AndroidShaderDeclarationVisitor visitor;
    void *user;
    bool validateOnly;
};
bool WalkDeclarations(const IW3AndroidShaderInstruction &ins, void *context)
{
    auto &state = *static_cast<DeclarationWalk *>(context);
    // Only this deliberately bounded instruction subset is understood.
    // Other opcodes must not be silently skipped in a future translator.
    if (ins.opcode == 0 || ins.opcode == 1 || ins.opcode == 2)
        return !ins.predicated; // Predicate register semantics not decoded.
    if (ins.opcode != 31 || ins.predicated || ins.operandTokenCount != 2)
        return false;
    const auto *operands = state.bytes +
        (ins.tokenOffset + 1u) * sizeof(std::uint32_t);
    const std::uint32_t declaration = ReadDword(operands);
    const std::uint32_t registerToken = ReadDword(operands + sizeof(std::uint32_t));
    IW3AndroidShaderDeclaration decoded{};
    decoded.tokenOffset = ins.tokenOffset;
    decoded.declarationToken = declaration;
    if (!R_AndroidDecodeD3D9Register(registerToken, true,
                                     &decoded.registerOperand))
        return false;
    const auto &reg = decoded.registerOperand;
    if (reg.relativeAddressing || reg.modifier || reg.destinationShift)
        return false;
    decoded.sampler = reg.type == 10; // D3DSPR_SAMPLER
    decoded.usage = static_cast<std::uint8_t>(declaration & 15u);
    decoded.usageIndex = static_cast<std::uint8_t>((declaration >> 16) & 15u);
    decoded.samplerTextureType =
        static_cast<std::uint8_t>((declaration >> 27) & 15u);
    if (decoded.sampler) {
        // Vertex texture fetch and sampler declarations require VS 3.0.
        if (state.stage == IW3AndroidShaderStage::Vertex && state.shaderMajor < 3)
            return false;
        // D3D9 DCL sampler declaration carries a D3DSTT texture class,
        // not a vertex semantic. Only defined D3D9 texture classes.
        if ((declaration & ~0x78000000u) != 0
            || decoded.samplerTextureType < 2
            || decoded.samplerTextureType > 4
            || reg.writeMask != 15)
            return false;
    } else {
        // D3DDECLUSAGE values are 0..13. Vertex shaders may declare
        // inputs/outputs, pixel shaders inputs (v# and SM2 t#).
        const bool registerClassAllowed =
            (state.stage == IW3AndroidShaderStage::Vertex
                && (reg.type == 1 || reg.type == 6))
            || (state.stage == IW3AndroidShaderStage::Pixel
                && (reg.type == 1 || (reg.type == 3 && state.shaderMajor == 2)));
        if (!registerClassAllowed || decoded.usage > 13
            || (declaration & ~0x000F000Fu) != 0)
            return false;
    }
    return state.validateOnly || state.visitor(decoded, state.user);
}
} // namespace

bool R_AndroidVisitD3D9Declarations(const void *program, std::size_t programBytes,
                                    IW3AndroidShaderStage stage,
                                    IW3AndroidShaderDeclarationVisitor visitor,
                                    void *user)
{
    IW3AndroidShaderEnvelope envelope{};
    if (!visitor || !R_AndroidInspectD3D9Shader(program, programBytes,
                                               stage, &envelope))
        return false;
    // Prevalidate the whole original token stream and every DCL before
    // publishing any declaration, even if a later declaration is invalid.
    DeclarationWalk state{static_cast<const unsigned char *>(program),
                          stage, envelope.major, visitor, user, true};
    if (!R_AndroidVisitD3D9Shader(program, programBytes, stage,
                                 WalkDeclarations, &state))
        return false;
    state.validateOnly = false;
    return R_AndroidVisitD3D9Shader(program, programBytes, stage,
                                   WalkDeclarations, &state);
}


// A single semantic walk for interleaved original DCL and MOV/ADD records.
// Keep decoding in WalkDeclarations/WalkArithmetic, so both the standalone
// visitors and this combined visitor enforce IDENTICAL operand restrictions.
namespace {
struct UnifiedWalk {
    const unsigned char *bytes;
    IW3AndroidShaderStage stage;
    std::uint8_t major;
    IW3AndroidShaderDecodedVisitor visitor;
    void *user;
    bool validateOnly;
    bool seenArithmetic;
};

bool ForwardDeclaration(const IW3AndroidShaderDeclaration &decl, void *context)
{
    auto &state = *static_cast<UnifiedWalk *>(context);
    IW3AndroidShaderDecodedInstruction record{};
    record.kind = IW3AndroidShaderDecodedKind::Declaration;
    record.tokenOffset = decl.tokenOffset;
    record.declaration = decl;
    return state.visitor(record, state.user);
}

bool ForwardArithmetic(const IW3AndroidShaderArithmetic &arithmetic, void *context)
{
    auto &state = *static_cast<UnifiedWalk *>(context);
    IW3AndroidShaderDecodedInstruction record{};
    record.kind = IW3AndroidShaderDecodedKind::Arithmetic;
    record.tokenOffset = arithmetic.tokenOffset;
    record.arithmetic = arithmetic;
    return state.visitor(record, state.user);
}

bool WalkUnified(const IW3AndroidShaderInstruction &ins, void *context)
{
    auto &state = *static_cast<UnifiedWalk *>(context);
    if (ins.opcode == 31) {
        // D3D9 declarations belong before executable instructions.
        if (state.seenArithmetic) return false;
        DeclarationWalk decl{state.bytes, state.stage, state.major,
                             ForwardDeclaration, &state, state.validateOnly};
        return WalkDeclarations(ins, &decl);
    }
    if (ins.opcode != 0 && ins.opcode != 1 && ins.opcode != 2)
        return false;
    if (ins.opcode != 0) state.seenArithmetic = true;
    ArithmeticWalk arithmetic{state.bytes, ForwardArithmetic,
                              &state, state.validateOnly};
    return WalkArithmetic(ins, &arithmetic);
}
} // namespace

bool R_AndroidVisitD3D9DecodedShader(const void *program, std::size_t programBytes,
                                     IW3AndroidShaderStage stage,
                                     IW3AndroidShaderDecodedVisitor visitor,
                                     void *user)
{
    IW3AndroidShaderEnvelope envelope{};
    if (!visitor || !R_AndroidInspectD3D9Shader(program, programBytes,
                                               stage, &envelope))
        return false;
    UnifiedWalk state{static_cast<const unsigned char *>(program), stage,
                      envelope.major, visitor, user, true, false};
    // Pass 1: reject an invalid late DCL, malformed arithmetic register,
    // predication, relative addressing, or unsupported opcode BEFORE the
    // first callback. Pass 2: publish original order without altering tokens.
    if (!R_AndroidVisitD3D9Shader(program, programBytes, stage,
                                 WalkUnified, &state))
        return false;
    state.validateOnly = false;
    state.seenArithmetic = false;
    return R_AndroidVisitD3D9Shader(program, programBytes, stage,
                                   WalkUnified, &state);
}


#if defined(__ANDROID__)
namespace {
struct PixelColorEmit {
    std::string body;
    bool declaredColor0 = false;
    bool temp0Written = false;
    bool color0Written = false;
};
bool EmitPixelColor(const IW3AndroidShaderDecodedInstruction &record, void *context)
{
    auto &state = *static_cast<PixelColorEmit *>(context);
    if (record.kind == IW3AndroidShaderDecodedKind::Declaration) {
        const auto &d = record.declaration;
        // Only the authentic ps_3_0 COLOR0 input declaration v0 is mapped.
        // Samplers, TEXCOORD and other inputs require their own bindings.
        if (state.declaredColor0 || d.sampler || d.usage != 10 ||
            d.usageIndex != 0 || d.registerOperand.type != 1 ||
            d.registerOperand.number != 0 || d.registerOperand.writeMask != 15)
            return false;
        state.declaredColor0 = true;
        return true;
    }
    const auto &a = record.arithmetic;
    if ((a.opcode != 1 && a.opcode != 2) ||
        a.sourceCount != (a.opcode == 1 ? 1 : 2))
        return false;
    std::string sources[2];
    for (std::uint8_t i = 0; i < a.sourceCount; ++i) {
        const auto &s = a.sources[i];
        // D3D9 swizzle/modifier/relative semantics must never be discarded.
        if (s.number != 0 || s.swizzle != 0xE4 || s.modifier != 0 ||
            s.relativeAddressing)
            return false;
        if (s.type == 1 && state.declaredColor0)
            sources[i] = "iw3_color_in0";
        else if (s.type == 0 && state.temp0Written)
            sources[i] = "iw3_r0";
        else
            return false; // undeclared input or read-before-write
    }
    const auto &d = a.destination;
    if (d.number != 0 || d.writeMask != 15 || d.modifier != 0 ||
        d.destinationShift != 0 || d.relativeAddressing)
        return false;
    const char *target = nullptr;
    if (d.type == 0) {
        target = "iw3_r0";
        state.temp0Written = true;
    } else if (d.type == 8) { // D3DSPR_COLOROUT, register oC0
        target = "iw3_color_out0";
        state.color0Written = true;
    } else {
        return false;
    }
    state.body += "  ";
    state.body += target;
    state.body += " = ";
    state.body += sources[0];
    if (a.opcode == 2) {
        state.body += " + ";
        state.body += sources[1];
    }
    state.body += ";\n";
    return true;
}
} // namespace

bool R_AndroidTranslateD3D9PixelColorSubsetToGLSL(
    const void *program, std::size_t programBytes, std::string *outGLSL)
{
    if (!outGLSL) return false;
    outGLSL->clear();
    IW3AndroidShaderEnvelope envelope{};
    if (!R_AndroidInspectD3D9Shader(program, programBytes,
                                   IW3AndroidShaderStage::Pixel, &envelope) ||
        envelope.major != 3 || envelope.minor != 0)
        return false;
    PixelColorEmit state{};
    if (!R_AndroidVisitD3D9DecodedShader(
            program, programBytes, IW3AndroidShaderStage::Pixel,
            EmitPixelColor, &state) || !state.color0Written)
        return false;
    // Shader input and fragment output are genuine D3D9 registers, not
    // synthetic geometry or a fallback shader. Vertex/pixel varying linkage
    // and GLES3 compile/link still require separate verification.
    *outGLSL =
        "#version 300 es\n"
        "precision highp float;\n"
        "in vec4 iw3_color_in0;\n"
        "layout(location = 0) out vec4 iw3_color_out0;\n"
        "void main() {\n"
        "  vec4 iw3_r0;\n" +
        state.body + "}\n";
    return true;
}

// Source-only companion to the original ps_3_0 COLOR0 subset. No fake geometry
// or fallback shaders: only authentic D3D9 vs_3_0 DCL/MOV tokens are accepted.
namespace {
struct VertexColorEmit {
    bool inputPosition = false, inputColor = false;
    bool outputPosition = false, outputColor = false;
    bool wrotePosition = false, wroteColor = false;
    std::string body;
};
bool EmitVertexColor(const IW3AndroidShaderDecodedInstruction &record, void *user)
{
    auto &state = *static_cast<VertexColorEmit *>(user);
    if (record.kind == IW3AndroidShaderDecodedKind::Declaration) {
        const auto &d = record.declaration;
        const auto &r = d.registerOperand;
        if (d.sampler || d.usageIndex || r.writeMask != 15 ||
            r.modifier || r.destinationShift || r.relativeAddressing)
            return false;
        if (r.type == 1 && r.number == 0 && d.usage == 0 && !state.inputPosition) {
            state.inputPosition = true; return true;
        }
        if (r.type == 1 && r.number == 1 && d.usage == 10 && !state.inputColor) {
            state.inputColor = true; return true;
        }
        if (r.type == 6 && r.number == 0 && d.usage == 0 && !state.outputPosition) {
            state.outputPosition = true; return true;
        }
        if (r.type == 6 && r.number == 1 && d.usage == 10 && !state.outputColor) {
            state.outputColor = true; return true;
        }
        return false;
    }
    const auto &a = record.arithmetic;
    if (a.opcode != 1 || a.sourceCount != 1) return false; // MOV only
    const auto &s = a.sources[0];
    const auto &d = a.destination;
    if (s.swizzle != 0xE4 || s.modifier || s.relativeAddressing ||
        d.writeMask != 15 || d.modifier || d.destinationShift ||
        d.relativeAddressing)
        return false;
    if (s.type == 1 && s.number == 0 && d.type == 6 && d.number == 0 &&
        state.inputPosition && state.outputPosition) {
        state.body += "  iw3_clip_position = iw3_position_in0;\n";
        state.wrotePosition = true;
        return true;
    }
    if (s.type == 1 && s.number == 1 && d.type == 6 && d.number == 1 &&
        state.inputColor && state.outputColor) {
        state.body += "  iw3_color_in0 = iw3_vertex_color_in0;\n";
        state.wroteColor = true;
        return true;
    }
    return false; // other registers, temp, swizzle or arithmetic unsupported
}
} // namespace

bool R_AndroidTranslateD3D9VertexPositionColorSubsetToGLSL(
    const void *program, std::size_t programBytes, std::string *outGLSL)
{
    if (!outGLSL) return false;
    outGLSL->clear();
    IW3AndroidShaderEnvelope envelope{};
    if (!R_AndroidInspectD3D9Shader(program, programBytes,
                                   IW3AndroidShaderStage::Vertex, &envelope) ||
        envelope.major != 3 || envelope.minor != 0)
        return false;
    VertexColorEmit state{};
    if (!R_AndroidVisitD3D9DecodedShader(
            program, programBytes, IW3AndroidShaderStage::Vertex,
            EmitVertexColor, &state) ||
        !state.inputPosition || !state.inputColor ||
        !state.outputPosition || !state.outputColor ||
        !state.wrotePosition || !state.wroteColor)
        return false;
    // D3D clip-space z is [0,w]; GLES clip-space z is [-w,w].
    // ES 3.00 fragment inputs use name-matched varyings, NOT layout(location).
    *outGLSL =
        "#version 300 es\n"
        "precision highp float;\n"
        "layout(location = 0) in vec4 iw3_position_in0;\n"
        "layout(location = 1) in vec4 iw3_vertex_color_in0;\n"
        "out vec4 iw3_color_in0;\n"
        "void main() {\n"
        "  vec4 iw3_clip_position;\n" +
        state.body +
        "  gl_Position = vec4(iw3_clip_position.xy, "
        "2.0 * iw3_clip_position.z - iw3_clip_position.w, "
        "iw3_clip_position.w);\n"
        "}\n";
    return true;
}

#endif

#endif
