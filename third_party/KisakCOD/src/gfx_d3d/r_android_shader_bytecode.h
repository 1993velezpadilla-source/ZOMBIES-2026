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
// Decoded D3D9 register fields for a narrow arithmetic instruction subset.
// These are ORIGINAL bytecode metadata, not validated GLSL bindings.
struct IW3AndroidShaderRegister {
    std::uint16_t number;
    std::uint8_t type;
    std::uint8_t writeMask;       // Destination only, bits 16..19.
    std::uint8_t swizzle;         // Source only, bits 16..23 (0xE4 = xyzw).
    std::uint8_t modifier;        // Destination bits 20..23; source bits 24..27.
    std::uint8_t destinationShift; // Destination bits 24..27.
    bool relativeAddressing;      // Relative addressing needs extra decoding.
};
struct IW3AndroidShaderArithmetic {
    std::uint32_t tokenOffset;
    std::uint16_t opcode;        // 1 = MOV, 2 = ADD.
    std::uint8_t sourceCount;
    IW3AndroidShaderRegister destination;
    IW3AndroidShaderRegister sources[2];
};
using IW3AndroidShaderArithmeticVisitor = bool (*)(const IW3AndroidShaderArithmetic &, void *);
// Decodes register field layout, including the SPLIT D3D9 register-type bits.
// Rejects malformed register tokens and reserved modifiers; it does not map
// register types to GLSL, resolve relative addressing or validate shader IO.
bool R_AndroidDecodeD3D9Register(std::uint32_t token, bool destination,
                                 IW3AndroidShaderRegister *out);
// Fully prevalidates a limited non-predicated, non-relative MOV/ADD/NOP stream
// before any callback. DCL and all other instructions FAIL CLOSED, as do
// unsupported addressing and malformed operands. NOP produces no callback.
// This is NOT a D3D9-to-GLSL translator and creates no GPU shader.
bool R_AndroidVisitD3D9Arithmetic(const void *program, std::size_t programBytes,
                                  IW3AndroidShaderStage stage,
                                  IW3AndroidShaderArithmeticVisitor visitor, void *user);

#endif
