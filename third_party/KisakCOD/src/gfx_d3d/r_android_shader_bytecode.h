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
};
// programSize is the serialized Gfx*ShaderLoadDef byte length, not a token count.
// Validates the D3D9 shader version envelope and terminal END token only;
// does NOT validate all instruction opcodes, register semantics, or translation.
bool R_AndroidInspectD3D9Shader(const void *program, std::size_t programBytes,
                               IW3AndroidShaderStage stage,
                               IW3AndroidShaderEnvelope *out);
#endif
