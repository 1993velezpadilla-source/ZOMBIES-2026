#pragma once
// Android-only backing handles for the ORIGINAL KisakCOD r_buffers.cpp API.
// Opaque D3D9 pointer values are identity tokens only; NEVER dereference them.
// Actual vertex/index data resides in GLES3 VBO/EBO storage, not COM objects.
#if defined(__ANDROID__)
#include <cstddef>
void *R_AndroidCreateBufferHandle(bool indexBuffer, std::size_t bytes, bool dynamic);
void *R_AndroidLockBufferHandle(const void *handle, std::size_t offset,
                                std::size_t bytes, unsigned int lockFlags);
bool R_AndroidUnlockBufferHandle(const void *handle);
bool R_AndroidReleaseBufferHandle(const void *handle);
// Only after EGL context destruction; caller must also invalidate GLES3 registries.
void R_AndroidInvalidateBufferHandles();
#endif
