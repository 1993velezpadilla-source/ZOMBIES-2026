// Android implementation of the Win32 virtual-memory calls used by the
// genuine KisakCOD universal/com_memory.cpp. This is a platform adapter,
// not a replacement for the engine's Hunk/PMem allocator.
#include <cstddef>
#include <cstdint>
#include <cerrno>
#include <limits>
#include <map>
#include <mutex>
#include <sys/mman.h>
#include <unistd.h>

namespace {
constexpr std::uint32_t MEM_COMMIT = 0x1000;
constexpr std::uint32_t MEM_RESERVE = 0x2000;
constexpr std::uint32_t MEM_DECOMMIT = 0x4000;
constexpr std::uint32_t MEM_RELEASE = 0x8000;
constexpr std::uint32_t PAGE_READWRITE = 4;
std::mutex regions_mutex;
std::map<std::uintptr_t, std::size_t> regions;

std::size_t page_size() {
  const long n = sysconf(_SC_PAGESIZE);
  return n > 0 ? static_cast<std::size_t>(n) : 0;
}
bool round_range(std::uintptr_t addr, std::size_t size,
                 std::size_t page, std::uintptr_t &begin, std::size_t &length) {
  if (!page || !size || addr > UINTPTR_MAX - size) return false;
  begin = addr - addr % page;
  const std::uintptr_t end = addr + size;
  if (end > UINTPTR_MAX - (page - 1)) return false;
  const std::uintptr_t aligned_end = ((end + page - 1) / page) * page;
  length = aligned_end - begin;
  return length != 0;
}
bool contained(std::uintptr_t addr, std::size_t len) {
  auto it = regions.upper_bound(addr);
  if (it == regions.begin()) return false;
  --it;
  const auto offset = addr - it->first;
  return offset <= it->second && len <= it->second - offset;
}
}

extern "C" void *VirtualAlloc(void *address, std::size_t size,
                               std::uint32_t allocationType, std::uint32_t protect) {
  if (protect != PAGE_READWRITE || size == 0) { errno = EINVAL; return nullptr; }
  const auto page = page_size();
  if (!page) { errno = EINVAL; return nullptr; }
  if ((allocationType == MEM_RESERVE || allocationType == (MEM_RESERVE | MEM_COMMIT)) && !address) {
    if (size > SIZE_MAX - (page - 1)) { errno = ENOMEM; return nullptr; }
    const std::size_t len = ((size + page - 1) / page) * page;
    const int initial_protection = (allocationType & MEM_COMMIT) ? (PROT_READ | PROT_WRITE) : PROT_NONE;
    void *p = mmap(nullptr, len, initial_protection, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (p == MAP_FAILED) return nullptr;
    std::lock_guard<std::mutex> lock(regions_mutex);
    if (!regions.emplace(reinterpret_cast<std::uintptr_t>(p), len).second) {
      munmap(p, len);
      errno = EEXIST;
      return nullptr;
    }
    return p;
  }
  if (allocationType == MEM_COMMIT && address) {
    std::uintptr_t begin = 0;
    std::size_t len = 0;
    if (!round_range(reinterpret_cast<std::uintptr_t>(address), size, page, begin, len)) {
      errno = EINVAL; return nullptr;
    }
    std::lock_guard<std::mutex> lock(regions_mutex);
    if (!contained(begin, len)) { errno = EINVAL; return nullptr; }
    return mprotect(reinterpret_cast<void *>(begin), len, PROT_READ | PROT_WRITE) == 0
        ? address : nullptr;
  }
  errno = EINVAL;
  return nullptr;
}

extern "C" int VirtualFree(void *address, std::size_t size, std::uint32_t freeType) {
  if (!address) { errno = EINVAL; return 0; }
  std::lock_guard<std::mutex> lock(regions_mutex);
  const auto addr = reinterpret_cast<std::uintptr_t>(address);
  if (freeType == MEM_RELEASE && size == 0) {
    auto it = regions.find(addr);
    if (it == regions.end()) { errno = EINVAL; return 0; }
    if (munmap(address, it->second) != 0) return 0;
    regions.erase(it);
    return 1;
  }
  if (freeType == MEM_DECOMMIT && size) {
    std::uintptr_t begin = 0;
    std::size_t len = 0;
    if (!round_range(addr, size, page_size(), begin, len) || !contained(begin, len)) {
      errno = EINVAL; return 0;
    }
    if (mprotect(reinterpret_cast<void *>(begin), len, PROT_NONE) != 0) return 0;
    // Discard physical pages while retaining the original virtual reservation.
    return madvise(reinterpret_cast<void *>(begin), len, MADV_DONTNEED) == 0;
  }
  errno = EINVAL;
  return 0;
}
