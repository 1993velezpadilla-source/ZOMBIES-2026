#pragma once
// D3D9 declaration metadata from the ORIGINAL KisakCOD material builder.
// This does not create a GLES3 VAO, translate shaders, or render geometry.
#if defined(__ANDROID__)
#include <cstddef>
#include <cstdint>
struct IW3AndroidVertexElement {
    std::uint16_t stream;
    std::uint16_t offset;
    std::uint8_t type;
    std::uint8_t method;
    std::uint8_t usage;
    std::uint8_t usageIndex;
};
static_assert(sizeof(IW3AndroidVertexElement) == 8, "D3D9 vertex element ABI");
void *R_AndroidCreateVertexDeclaration(const IW3AndroidVertexElement *elements,
                                       std::size_t count);
bool R_AndroidSelectVertexDeclaration(const void *identity);
bool R_AndroidReleaseVertexDeclaration(const void *identity);
bool R_AndroidCopyVertexDeclaration(const void *identity,
                                    IW3AndroidVertexElement *out,
                                    std::size_t capacity, std::size_t *count);
const void *R_AndroidCurrentVertexDeclaration();
// Only after original renderer resources are invalidated on the owning thread.
void R_AndroidInvalidateVertexDeclarations();
#endif
