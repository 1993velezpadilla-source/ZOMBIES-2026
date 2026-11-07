#pragma once
// Android ARM64 ABI declarations for the original KisakCOD com_memory.cpp.
// The source uses Win32 VirtualAlloc/VirtualFree directly; Android's NDK
// does not declare them. These are declarations ONLY, not emulations.
// Implementations are provided by iw3_android_win32_virtual_memory.cpp.
// This declaration header alone does not prove runtime or link readiness.
#if !defined(__ANDROID__) || !defined(__aarch64__)
#error "This declaration shim is only for the Android ARM64 compile audit"
#endif
#include <cstddef>
#include <cstdint>
// Win32 DWORD is 32-bit even on a 64-bit target; Android LP64 unsigned long is 64-bit.
static_assert(sizeof(std::uint32_t) == 4, "Win32 DWORD must be 32-bit");
extern "C" void *VirtualAlloc(void *address, std::size_t size,
                              std::uint32_t allocationType, std::uint32_t protect);
extern "C" int VirtualFree(void *address, std::size_t size,
                            std::uint32_t freeType);
