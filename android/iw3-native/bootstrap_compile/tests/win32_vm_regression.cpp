// Standalone regression for the Android Win32 VM adapter used by original KisakCOD.
// Host Linux test uses the same mmap/mprotect implementation; it does NOT prove
// the complete engine links, starts or renders on an ARM64 Android device.
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstring>
extern "C" void *VirtualAlloc(void *, std::size_t, std::uint32_t, std::uint32_t);
extern "C" int VirtualFree(void *, std::size_t, std::uint32_t);
int main() {
  constexpr std::uint32_t commit = 0x1000, reserve = 0x2000;
  constexpr std::uint32_t decommit = 0x4000, release = 0x8000, rw = 4;
  constexpr std::size_t bytes = 16384;
  auto *p = static_cast<unsigned char *>(VirtualAlloc(nullptr, bytes, reserve, rw));
  assert(p);
  assert(VirtualAlloc(p, bytes, commit, rw) == p);
  std::memset(p, 0x5a, bytes);
  assert(VirtualFree(p, bytes, decommit));
  assert(VirtualAlloc(p, bytes, commit, rw) == p);
  // Anonymous private pages discarded by MADV_DONTNEED read back as zero.
  for (std::size_t i = 0; i < bytes; ++i) assert(p[i] == 0);
  assert(VirtualFree(p, 0, release));
  auto *q = static_cast<unsigned char *>(VirtualAlloc(nullptr, bytes, reserve | commit, rw));
  assert(q);
  std::memset(q, 0xa5, bytes);
  assert(q[0] == 0xa5 && q[bytes - 1] == 0xa5);
  assert(VirtualFree(q, 0, release));
  assert(!VirtualAlloc(nullptr, bytes, 0, rw));
  assert(!VirtualFree(q, 0, release));
}
