#pragma once
// Bounded inspection of ORIGINAL IW3 D3D9 shader token streams.
// The bounded inspector and visitors are separate from the narrow GLSL source translators below; none creates a GLES GPU shader.
#if defined(__ANDROID__)
#include <cstddef>
#include <cstdint>
#include <string>

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


// D3D9 DCL declarations are decoded separately from arithmetic instructions.
// Keep the original usage/sampler tokens and stage; this is metadata for a
// future faithful input/output/sampler binding, NOT a GLES vertex attribute.
struct IW3AndroidShaderDeclaration {
    std::uint32_t tokenOffset;
    std::uint32_t declarationToken;
    std::uint8_t usage;
    std::uint8_t usageIndex;
    std::uint8_t samplerTextureType; // D3DSTT_2D=2, CUBE=3, VOLUME=4.
    bool sampler;
    IW3AndroidShaderRegister registerOperand;
};
using IW3AndroidShaderDeclarationVisitor =
    bool (*)(const IW3AndroidShaderDeclaration &, void *);
// Accepts only structurally valid DCL/NOP/MOV/ADD instruction streams,
// validates every DCL before emitting any callback, and rejects unsupported
// DCL register classes, reserved declaration bits and invalid sampler types.
// Arithmetic tokens are not translated or interpreted by this visitor.
bool R_AndroidVisitD3D9Declarations(const void *program, std::size_t programBytes,
                                    IW3AndroidShaderStage stage,
                                    IW3AndroidShaderDeclarationVisitor visitor,
                                    void *user);


// Unified, ORDERED subset IR for genuine D3D9 DCL/MOV/ADD/NOP streams.
// Existing declaration-only and arithmetic-only visitors deliberately reject
// each other's instructions; neither can consume an ordinary mixed shader.
// This API reuses both semantic decoders, prevalidates the entire mixed stream,
// then publishes DCL and arithmetic records in original token order.
// It does NOT generate GLSL, create GPU programs, or execute a shader.
enum class IW3AndroidShaderDecodedKind : std::uint8_t { Declaration, Arithmetic };
struct IW3AndroidShaderDecodedInstruction {
    IW3AndroidShaderDecodedKind kind;
    std::uint32_t tokenOffset;
    IW3AndroidShaderDeclaration declaration;
    IW3AndroidShaderArithmetic arithmetic;
};
using IW3AndroidShaderDecodedVisitor =
    bool (*)(const IW3AndroidShaderDecodedInstruction &, void *);
// No callbacks on malformed or unsupported bytecode; an explicit callback
// rejection can stop a partially delivered (otherwise valid) stream.
bool R_AndroidVisitD3D9DecodedShader(const void *program, std::size_t programBytes,
                                     IW3AndroidShaderStage stage,
                                     IW3AndroidShaderDecodedVisitor visitor,
                                     void *user);

#endif

#if defined(__ANDROID__)
// Faithful GLSL ES 3.0 translation for an intentionally TINY authentic D3D9
// ps_3_0 subset: COLOR0 v0 declaration, MOV/ADD, r0 and oC0. Full-vector,
// identity-swizzle, unmodified operands only. All other tokens FAIL CLOSED.
// Produces SOURCE TEXT only; it does not compile/link a GPU program, map a
// vertex varying, or make the Android game renderer operational.
// On failure outGLSL is cleared, never a partially translated shader.
bool R_AndroidTranslateD3D9PixelColorSubsetToGLSL(
    const void *program, std::size_t programBytes, std::string *outGLSL);

// Genuine vs_3_0 POSITION0 v0 / COLOR0 v1 -> POSITION0 o0 / COLOR0 o1
// companion for the tiny ps_3_0 COLOR0 subset. Supports full-vector MOV
// only and validates declarations/operands before emitting any source.
// This is source-only; no GPU compilation, linking, map or gameplay.
bool R_AndroidTranslateD3D9VertexPositionColorSubsetToGLSL(
    const void *program, std::size_t programBytes, std::string *outGLSL);

#endif
