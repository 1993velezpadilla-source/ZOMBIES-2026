// Genuine GLES3 VBO/EBO storage provider for original IW3 resource identities.
// A resource handle comes from the ORIGINAL allocator (future r_buffers.cpp
// integration); no fake Direct3D COM object is constructed here.
#if defined(__ANDROID__)
#include "r_android_buffer_storage.h"
#include "r_android_vertex_stream.h"
#include "r_android_indexed_draw.h"
#include <EGL/egl.h>
#include <GLES3/gl3.h>
#include <cstdint>
#include <limits>
#include <unordered_map>

namespace {
struct Storage { GLuint id; GLenum target; std::size_t bytes; };
std::unordered_map<const void *, Storage> owned;
EGLDisplay ownerDisplay = EGL_NO_DISPLAY;
EGLContext ownerContext = EGL_NO_CONTEXT;

bool Ready()
{
    const EGLDisplay display = eglGetCurrentDisplay();
    const EGLContext context = eglGetCurrentContext();
    return display != EGL_NO_DISPLAY && context != EGL_NO_CONTEXT
        && (ownerContext == EGL_NO_CONTEXT
            || (ownerDisplay == display && ownerContext == context));
}
void Adopt()
{
    if (ownerContext == EGL_NO_CONTEXT) {
        ownerDisplay = eglGetCurrentDisplay();
        ownerContext = eglGetCurrentContext();
    }
}
GLenum Binding(GLenum target)
{
    return target == GL_ARRAY_BUFFER
        ? GL_ARRAY_BUFFER_BINDING : GL_ELEMENT_ARRAY_BUFFER_BINDING;
}
bool Restore(GLenum target, GLint previous)
{
    glBindBuffer(target, static_cast<GLuint>(previous));
    return glGetError() == GL_NO_ERROR;
}
bool Create(const void *handle, GLenum target, std::size_t bytes,
            const void *data, bool dynamic)
{
    if (!handle || !Ready() || !bytes || owned.count(handle)
        || bytes > static_cast<std::size_t>(std::numeric_limits<GLsizeiptr>::max())
        || (target == GL_ELEMENT_ARRAY_BUFFER && (bytes % sizeof(std::uint16_t)))
        || glGetError() != GL_NO_ERROR)
        return false;
    GLint previous = 0;
    glGetIntegerv(Binding(target), &previous);
    if (glGetError() != GL_NO_ERROR || previous < 0) return false;
    GLuint id = 0;
    glGenBuffers(1, &id);
    if (glGetError() != GL_NO_ERROR || !id) {
        if (id) glDeleteBuffers(1, &id);
        (void)glGetError();
        return false;
    }
    glBindBuffer(target, id);
    const bool bound = glGetError() == GL_NO_ERROR;
    if (bound) {
        glBufferData(target, static_cast<GLsizeiptr>(bytes), data,
                     dynamic ? GL_DYNAMIC_DRAW : GL_STATIC_DRAW);
    }
    const bool allocated = bound && glGetError() == GL_NO_ERROR;
    const bool restored = Restore(target, previous);
    bool registered = false;
    if (allocated && restored) {
        registered = target == GL_ARRAY_BUFFER
            ? R_AndroidGlesRegisterVertexBuffer(handle, id, bytes)
            : R_AndroidGlesRegisterIndexBuffer(handle, id,
                                               bytes / sizeof(std::uint16_t));
    }
    if (!registered) {
        glDeleteBuffers(1, &id);
        (void)glGetError();
        return false;
    }
    owned.emplace(handle, Storage{id, target, bytes});
    Adopt();
    return true;
}
} // namespace

bool R_AndroidGlesCreateVertexStorage(const void *handle, std::size_t bytes,
                                      const void *data, bool dynamic)
{
    return Create(handle, GL_ARRAY_BUFFER, bytes, data, dynamic);
}
bool R_AndroidGlesCreateIndexStorage(const void *handle, std::size_t bytes,
                                     const void *data, bool dynamic)
{
    return Create(handle, GL_ELEMENT_ARRAY_BUFFER, bytes, data, dynamic);
}
bool R_AndroidGlesUpdateBufferStorage(const void *handle, std::size_t offset,
                                      const void *data, std::size_t bytes)
{
    if (!handle || !data || !bytes || !Ready() || glGetError() != GL_NO_ERROR)
        return false;
    const auto it = owned.find(handle);
    if (it == owned.end() || offset > it->second.bytes
        || bytes > it->second.bytes - offset
        || offset > static_cast<std::size_t>(std::numeric_limits<GLintptr>::max())
        || bytes > static_cast<std::size_t>(std::numeric_limits<GLsizeiptr>::max()))
        return false;
    const Storage &storage = it->second;
    GLint previous = 0;
    glGetIntegerv(Binding(storage.target), &previous);
    if (glGetError() != GL_NO_ERROR || previous < 0) return false;
    glBindBuffer(storage.target, storage.id);
    const bool bound = glGetError() == GL_NO_ERROR;
    if (bound) {
        glBufferSubData(storage.target, static_cast<GLintptr>(offset),
                        static_cast<GLsizeiptr>(bytes), data);
    }
    const bool updated = bound && glGetError() == GL_NO_ERROR;
    const bool restored = Restore(storage.target, previous);
    // GL may have partially updated data on failure; never report success.
    return updated && restored;
}
bool R_AndroidGlesDestroyBufferStorage(const void *handle)
{
    if (!handle || !Ready() || glGetError() != GL_NO_ERROR) return false;
    const auto it = owned.find(handle);
    if (it == owned.end()) return false;
    const Storage storage = it->second;
    const bool unregistered = storage.target == GL_ARRAY_BUFFER
        ? R_AndroidGlesUnregisterVertexBuffer(handle)
        : R_AndroidGlesUnregisterIndexBuffer(handle);
    if (!unregistered) return false;
    glDeleteBuffers(1, &storage.id);
    const bool deleted = glGetError() == GL_NO_ERROR;
    owned.erase(it);
    return deleted;
}
void R_AndroidGlesInvalidateBufferStorage()
{
    // EGL has already destroyed the owning context. Its GL objects are gone;
    // the original stream/index registries have independent invalidation.
    owned.clear();
    ownerDisplay = EGL_NO_DISPLAY;
    ownerContext = EGL_NO_CONTEXT;
}
#endif
