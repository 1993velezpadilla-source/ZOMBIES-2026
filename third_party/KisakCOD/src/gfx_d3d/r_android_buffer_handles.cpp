// Original IW3 r_buffers.cpp Android handle lifecycle and CPU lock staging.
// No synthetic D3D9 COM objects or replacement renderer.
#if defined(__ANDROID__)
#include "r_android_buffer_handles.h"
#include "r_android_buffer_storage.h"
#include <cstddef>
#include <cstdint>
#include <limits>
#include <memory>
#include <unordered_map>
#include <vector>

namespace {
constexpr unsigned int kDiscard = 0x2000u; // D3DLOCK_DISCARD
constexpr unsigned int kNoOverwrite = 0x1000u; // D3DLOCK_NOOVERWRITE
struct Handle {
    explicit Handle(std::size_t n, bool idx, bool dyn)
        : staging(n), index(idx), dynamic(dyn) {}
    std::vector<std::uint8_t> staging;
    bool index;
    bool dynamic;
    bool locked = false;
    std::size_t offset = 0;
    std::size_t count = 0;
};
std::unordered_map<const void *, std::unique_ptr<Handle>> handles;
}

void *R_AndroidCreateBufferHandle(bool indexBuffer, std::size_t bytes, bool dynamic)
{
    if (!bytes || (indexBuffer && (bytes % sizeof(std::uint16_t)))
        || bytes > static_cast<std::size_t>(std::numeric_limits<std::ptrdiff_t>::max()))
        return nullptr;
    std::unique_ptr<Handle> handle(new Handle(bytes, indexBuffer, dynamic));
    void *identity = handle.get(); // Stable, unique token while owned by the map.
    const bool created = indexBuffer
        ? R_AndroidGlesCreateIndexStorage(identity, bytes, nullptr, dynamic)
        : R_AndroidGlesCreateVertexStorage(identity, bytes, nullptr, dynamic);
    if (!created) return nullptr;
    handles.emplace(identity, std::move(handle));
    return identity;
}

void *R_AndroidLockBufferHandle(const void *identity, std::size_t offset,
                                std::size_t bytes, unsigned int flags)
{
    const auto it = handles.find(identity);
    if (it == handles.end()) return nullptr;
    Handle &handle = *it->second;
    if (handle.locked || offset >= handle.staging.size()
        || (flags != 0 && flags != kDiscard && flags != kNoOverwrite)
        || (!handle.dynamic && flags != 0)
        || (handle.index && (offset % 2 || bytes % 2)))
        return nullptr;
    // D3D9 bytes=0 locks to the end. Do not allow an empty mapped region.
    const std::size_t count = bytes ? bytes : handle.staging.size() - offset;
    if (!count || count > handle.staging.size() - offset) return nullptr;
    // DISCARD may overwrite prior data; no GPU orphaning is promised yet.
    // NOOVERWRITE relies on the original caller's no-in-flight-overlap contract.
    handle.locked = true;
    handle.offset = offset;
    handle.count = count;
    return handle.staging.data() + offset;
}

bool R_AndroidUnlockBufferHandle(const void *identity)
{
    const auto it = handles.find(identity);
    if (it == handles.end() || !it->second->locked) return false;
    Handle &handle = *it->second;
    if (!R_AndroidGlesUpdateBufferStorage(identity, handle.offset,
                                          handle.staging.data() + handle.offset,
                                          handle.count))
        return false; // Remain locked; caller can retry or fail loudly.
    handle.locked = false;
    handle.offset = 0;
    handle.count = 0;
    return true;
}

bool R_AndroidReleaseBufferHandle(const void *identity)
{
    const auto it = handles.find(identity);
    if (it == handles.end() || it->second->locked
        || !R_AndroidGlesDestroyBufferStorage(identity))
        return false;
    handles.erase(it);
    return true;
}

void R_AndroidInvalidateBufferHandles()
{
    // No GL calls: the owner EGL context must already be destroyed.
    handles.clear();
}
#endif
