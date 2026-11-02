// Original IW3 Material_BuildVertexDecl metadata identity for Android ARM64.
// No synthetic vertex formats or substitute rendering pipeline.
#if defined(__ANDROID__)
#include "r_android_vertex_declaration.h"
#include <array>
#include <memory>
#include <new>
#include <unordered_map>

namespace {
struct Declaration {
    std::array<IW3AndroidVertexElement, 16> elements{};
    std::size_t count = 0;
};
std::unordered_map<const void *, std::unique_ptr<Declaration>> declarations;
const void *current = nullptr;

bool Valid(const IW3AndroidVertexElement &element)
{
    // Only types present in KisakCOD's original s_streamSourceInfo table:
    // FLOAT2/FLOAT3/FLOAT4, D3DCOLOR, UBYTE4, SHORT4. D3DCOLOR needs
    // explicit BGRA handling when the real GLES shader/VAO bridge arrives.
    const bool knownType = element.type == 1 || element.type == 2
        || element.type == 3 || element.type == 4
        || element.type == 5 || element.type == 8;
    const bool knownUsage = element.usage == 0 || element.usage == 3
        || element.usage == 5 || element.usage == 10;
    return element.stream < 2 && element.offset <= 4096
        && element.method == 0 && knownType && knownUsage
        && (element.usage == 5 ? element.usageIndex < 8
                              : element.usageIndex == 0);
}
}

void *R_AndroidCreateVertexDeclaration(const IW3AndroidVertexElement *elements,
                                       std::size_t count)
{
    if (!elements || !count || count > 16) return nullptr;
    for (std::size_t i = 0; i < count; ++i) {
        if (!Valid(elements[i])) return nullptr;
        for (std::size_t j = 0; j < i; ++j) {
            if (elements[j].usage == elements[i].usage
                && elements[j].usageIndex == elements[i].usageIndex)
                return nullptr; // Shader semantic collision.
        }
    }
    std::unique_ptr<Declaration> decl(new (std::nothrow) Declaration);
    if (!decl) return nullptr;
    decl->count = count;
    for (std::size_t i = 0; i < count; ++i) decl->elements[i] = elements[i];
    void *identity = decl.get();
    declarations.emplace(identity, std::move(decl));
    return identity;
}

bool R_AndroidSelectVertexDeclaration(const void *identity)
{
    if (identity && declarations.find(identity) == declarations.end())
        return false;
    current = identity;
    return true; // Metadata selection ONLY. Does not bind a GLES3 VAO.
}

bool R_AndroidReleaseVertexDeclaration(const void *identity)
{
    if (!identity || !declarations.erase(identity)) return false;
    if (current == identity) current = nullptr;
    return true;
}

bool R_AndroidCopyVertexDeclaration(const void *identity,
                                    IW3AndroidVertexElement *out,
                                    std::size_t capacity, std::size_t *count)
{
    if (!count) return false;
    const auto it = declarations.find(identity);
    if (it == declarations.end()) return false;
    const Declaration &decl = *it->second;
    if (!out || capacity < decl.count) return false;
    for (std::size_t i = 0; i < decl.count; ++i) out[i] = decl.elements[i];
    *count = decl.count;
    return true;
}

const void *R_AndroidCurrentVertexDeclaration() { return current; }

void R_AndroidInvalidateVertexDeclarations()
{
    declarations.clear();
    current = nullptr;
}
#endif
