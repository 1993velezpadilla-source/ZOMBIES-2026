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
    std::uint32_t instructions = 0, comments = 0;
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
        // Check common known operand counts. Other opcode/register
        // semantics still require a real D3D9 decoder before translation.
        if ((opcode == 0 && operands != 0) // NOP
            || (opcode == 1 && operands != 2) // MOV
            || (opcode == 2 && operands != 3) // ADD
            || (opcode == 31 && operands != 2)) // DCL
            return false;
        ++instructions;
        i += operands + 1;
    }
    if (!terminated) return false;
    out->major = major;
    out->minor = minor;
    out->dwordCount = static_cast<std::uint32_t>(words);
    out->instructionCount = instructions;
    out->commentCount = comments;
    return true;
}
#endif
