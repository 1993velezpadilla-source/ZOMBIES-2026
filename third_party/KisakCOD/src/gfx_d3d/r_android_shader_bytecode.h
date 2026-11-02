#pragma once
// Bounded inspection of ORIGINAL IW3 D3D9 shader token streams.
// This is NOT a bytecode-to-GLSL translator and never creates a GLES shader.
#if defined(__ANDROID__)
#include <cstddef>
#include <cstdint>

enum class IW3AndroidShaderStage : std::uint8_t { Vertex, Pixel };
struct IW3AndroidShaderEnvelope {
    std::uint8_t major;
    std::uint8_t minor;
    std::uint32_t dwordCount;
    std::uint32_t instructionCount;
    std::uint32_t commentCount;
};
// programSize is the serialized Gfx*ShaderLoadDef byte length, not a token count.
// Walks bounded D3D9 SM2/SM3 instruction lengths and COMMENT payloads, requiring
// a terminal END at an instruction boundary. This is structural validation,
// NOT opcode/register/semantic verification and NOT GLSL translation.
bool R_AndroidInspectD3D9Shader(const void *program, std::size_t programBytes,
                               IW3AndroidShaderStage stage,
                               IW3AndroidShaderEnvelope *out);
#endif
