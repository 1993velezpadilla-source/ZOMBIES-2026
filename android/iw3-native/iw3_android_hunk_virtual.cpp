#include <qcommon/qcommon.h>
#include <universal/com_memory.h>

#include <sys/mman.h>
#include <unistd.h>

#include <cerrno>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <map>
#include <mutex>

namespace {
std::mutex g_virtualMemoryMutex;
std::map<uintptr_t, size_t> g_virtualMemoryRegions;

[[noreturn]] void VirtualMemoryFatal(const char *operation, int errorCode)
{
    Com_Error(ERR_FATAL, "%s failed: %s", operation, std::strerror(errorCode));
    std::abort();
}

size_t PageSize()
{
    const long value = sysconf(_SC_PAGESIZE);
    if (value <= 0)
        VirtualMemoryFatal("sysconf(_SC_PAGESIZE)", errno ? errno : EINVAL);
    return static_cast<size_t>(value);
}

uintptr_t AlignDown(uintptr_t value, size_t alignment)
{
    return value & ~static_cast<uintptr_t>(alignment - 1);
}

uintptr_t AlignUp(uintptr_t value, size_t alignment)
{
    const uintptr_t mask = static_cast<uintptr_t>(alignment - 1);
    if (value > UINTPTR_MAX - mask)
        VirtualMemoryFatal("virtual-memory address overflow", EOVERFLOW);
    return (value + mask) & ~mask;
}

bool IsRangeReservedLocked(uintptr_t address, size_t length)
{
    if (length == 0 || address > UINTPTR_MAX - length)
        return false;
    auto it = g_virtualMemoryRegions.upper_bound(address);
    if (it == g_virtualMemoryRegions.begin())
        return false;
    --it;
    const uintptr_t base = it->first;
    const size_t reserved = it->second;
    if (address < base || address - base > reserved)
        return false;
    return length <= reserved - static_cast<size_t>(address - base);
}
}

void *__cdecl Z_VirtualReserve(int size)
{
    if (size <= 0)
        VirtualMemoryFatal("Z_VirtualReserve invalid size", EINVAL);

    const size_t pageSize = PageSize();
    const size_t requested = static_cast<size_t>(size);
    const size_t length = static_cast<size_t>(AlignUp(requested, pageSize));
    void *memory = mmap(nullptr, length, PROT_NONE,
                        MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (memory == MAP_FAILED)
        VirtualMemoryFatal("mmap(PROT_NONE)", errno);

    {
        std::lock_guard<std::mutex> lock(g_virtualMemoryMutex);
        const auto inserted = g_virtualMemoryRegions.emplace(
            reinterpret_cast<uintptr_t>(memory), length);
        if (!inserted.second) {
            munmap(memory, length);
            VirtualMemoryFatal("duplicate virtual-memory reservation", EEXIST);
        }
    }
    return memory;
}

void __cdecl Z_VirtualCommit(void *ptr, int size)
{
    if (!ptr || size < 0)
        VirtualMemoryFatal("Z_VirtualCommit invalid range", EINVAL);
    if (size == 0)
        return;

    const size_t pageSize = PageSize();
    const uintptr_t address = reinterpret_cast<uintptr_t>(ptr);
    if (address > UINTPTR_MAX - static_cast<uintptr_t>(size))
        VirtualMemoryFatal("Z_VirtualCommit address overflow", EOVERFLOW);
    const uintptr_t start = AlignDown(address, pageSize);
    const uintptr_t end = AlignUp(address + static_cast<uintptr_t>(size), pageSize);
    const size_t length = static_cast<size_t>(end - start);

    std::lock_guard<std::mutex> lock(g_virtualMemoryMutex);
    if (!IsRangeReservedLocked(start, length))
        VirtualMemoryFatal("Z_VirtualCommit outside reservation", EINVAL);
    if (mprotect(reinterpret_cast<void *>(start), length, PROT_READ | PROT_WRITE) != 0)
        VirtualMemoryFatal("mprotect(PROT_READ|PROT_WRITE)", errno);
}

void __cdecl Z_VirtualDecommit(void *ptr, int size)
{
    if (!ptr || size < 0)
        VirtualMemoryFatal("Z_VirtualDecommit invalid range", EINVAL);
    if (size == 0)
        return;

    const size_t pageSize = PageSize();
    const uintptr_t address = reinterpret_cast<uintptr_t>(ptr);
    if (address > UINTPTR_MAX - static_cast<uintptr_t>(size))
        VirtualMemoryFatal("Z_VirtualDecommit address overflow", EOVERFLOW);
    const uintptr_t start = AlignDown(address, pageSize);
    const uintptr_t end = AlignUp(address + static_cast<uintptr_t>(size), pageSize);
    const size_t length = static_cast<size_t>(end - start);

    std::lock_guard<std::mutex> lock(g_virtualMemoryMutex);
    if (!IsRangeReservedLocked(start, length))
        VirtualMemoryFatal("Z_VirtualDecommit outside reservation", EINVAL);
    if (madvise(reinterpret_cast<void *>(start), length, MADV_DONTNEED) != 0)
        VirtualMemoryFatal("madvise(MADV_DONTNEED)", errno);
    if (mprotect(reinterpret_cast<void *>(start), length, PROT_NONE) != 0)
        VirtualMemoryFatal("mprotect(PROT_NONE)", errno);
}

void __cdecl Z_VirtualFree(void *ptr)
{
    if (!ptr)
        VirtualMemoryFatal("Z_VirtualFree null pointer", EINVAL);

    std::lock_guard<std::mutex> lock(g_virtualMemoryMutex);
    const uintptr_t address = reinterpret_cast<uintptr_t>(ptr);
    const auto it = g_virtualMemoryRegions.find(address);
    if (it == g_virtualMemoryRegions.end())
        VirtualMemoryFatal("Z_VirtualFree unknown reservation", EINVAL);
    const size_t length = it->second;
    if (munmap(ptr, length) != 0)
        VirtualMemoryFatal("munmap", errno);
    g_virtualMemoryRegions.erase(it);
}
