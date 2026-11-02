#pragma once
// Real GLES3 GPU storage for original KisakCOD IW3 vertex/index resource handles.
// The original r_buffers.cpp call sites are NOT wired to this allocator yet.
// This provider does not create shaders, VAOs, meshes, or a substitute renderer.
#if defined(__ANDROID__)
#include <cstddef>
bool R_AndroidGlesCreateVertexStorage(const void *originalHandle,
                                      std::size_t byteCount, const void *initialData,
                                      bool dynamic);
bool R_AndroidGlesCreateIndexStorage(const void *originalHandle,
                                     std::size_t byteCount, const void *initialData,
                                     bool dynamic);
bool R_AndroidGlesUpdateBufferStorage(const void *originalHandle,
                                      std::size_t byteOffset, const void *data,
                                      std::size_t byteCount);
bool R_AndroidGlesDestroyBufferStorage(const void *originalHandle);
// Call ONLY when the owning EGL context has been destroyed. No GL calls.
void R_AndroidGlesInvalidateBufferStorage();
#endif
