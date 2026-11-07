#pragma once
// Compile-only declaration shim for the original KisakCOD com_memory.cpp.
// The source uses Win32 VirtualAlloc/VirtualFree directly; Android's NDK
// does not declare them. These are declarations ONLY, not emulations.
// The strict --no-undefined link MUST continue to fail until the original
// memory service is wired to a verified Android mmap/mprotect provider.
// Do not include this header in a playable runtime build.
#if !defined(__ANDROID__) || !defined(__aarch64__)
#error "This declaration shim is only for the Android ARM64 compile audit"
#endif
#include <cstddef>
extern "C" void *VirtualAlloc(void *address, std::size_t size,
                              unsigned long allocationType, unsigned long protect);
extern "C" int VirtualFree(void *address, std::size_t size,
                            unsigned long freeType);
