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
    // IW3 load definitions store a uint16_t byte length. Do not infer a
    // length from a potentially malformed or unterminated shader stream.
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
    // D3D9 shader END is a complete DWORD, not a 16-bit suffix. Reject
    // early ENDs; no bytes may trail the terminal token.
    const std::size_t words = programBytes / sizeof(std::uint32_t);
    for (std::size_t i = 1; i < words; ++i) {
        const std::uint32_t token = ReadDword(bytes + i * sizeof(std::uint32_t));
        if (token == 0x0000FFFFu && i != words - 1)
            return false;
    }
    if (ReadDword(bytes + programBytes - 4) != 0x0000FFFFu)
        return false;
    out->major = major;
    out->minor = minor;
    out->dwordCount = static_cast<std::uint32_t>(words);
    return true;
}
#endif
