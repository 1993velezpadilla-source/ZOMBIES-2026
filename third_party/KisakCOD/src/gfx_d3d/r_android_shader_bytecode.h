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
    std::uint32_t predicatedInstructionCount;
};
// Instruction-boundary records for a future authentic D3D9 decoder. Token
// offsets/counts are DWORDs into the original serialized byte stream; no
// pointer cast or unaligned uint32_t access is required by callers.
struct IW3AndroidShaderInstruction {
    std::uint32_t tokenOffset;
    std::uint32_t instructionToken;
    std::uint16_t opcode;
    std::uint8_t operandTokenCount;
    bool predicated;
};
using IW3AndroidShaderVisitor = bool (*)(const IW3AndroidShaderInstruction &, void *);
// Validates the COMPLETE stream before invoking the visitor. COMMENT payloads
// and END are never emitted. Visitor returning false stops iteration; records
// already delivered remain visible. This does NOT decode register semantics,
// translate bytecode, or create a GLES program.
bool R_AndroidVisitD3D9Shader(const void *program, std::size_t programBytes,
                             IW3AndroidShaderStage stage,
                             IW3AndroidShaderVisitor visitor, void *user);

// programSize is the serialized Gfx*ShaderLoadDef byte length, not a token count.
// Walks bounded D3D9 SM2/SM3 instruction lengths and COMMENT payloads, requiring
// a terminal END at an instruction boundary. This is structural validation,
// NOT full opcode/register/semantic verification and NOT GLSL translation.
// For MOV/ADD, the instruction length includes a predicate token when bit 28
// is set; this preflight counts such instructions but does not execute them.
bool R_AndroidInspectD3D9Shader(const void *program, std::size_t programBytes,
                               IW3AndroidShaderStage stage,
                               IW3AndroidShaderEnvelope *out);
#endif
