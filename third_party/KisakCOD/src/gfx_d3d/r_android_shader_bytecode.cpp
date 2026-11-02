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

#endif
