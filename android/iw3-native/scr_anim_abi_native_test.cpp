// Executes the original scr_anim_s constructor from KisakCOD's bg_local.h.
// The encoded pointer-sized union value is only round-tripped; it is never dereferenced.
#include <cassert>
#include <bit>
#include <cstdint>
#include <cstdio>
#include <bgame/bg_local.h>

static_assert(sizeof(int) == sizeof(std::uint32_t));
static_assert(sizeof(std::uintptr_t) >= sizeof(std::uint32_t));
static_assert(sizeof(scr_anim_s) == sizeof(void *));

int main() {
    constexpr std::uint32_t payloads[] = {
        0x00000000u,
        0x00000001u,
        0x12345678u,
        0x7fffffffu,
        0x80000000u,
        0xffffffffu,
    };

    for (const std::uint32_t bits : payloads) {
        const int input = std::bit_cast<int>(bits);
        const scr_anim_s value(input);
        const std::uintptr_t round_trip =
            reinterpret_cast<std::uintptr_t>(value.linkPointer);
        assert(round_trip == static_cast<std::uintptr_t>(bits));
        if constexpr (sizeof(std::uintptr_t) > sizeof(std::uint32_t)) {
            assert((round_trip >> 32u) == 0u);
        }
    }

    std::puts("IW3_SCR_ANIM_HANDLE_ZERO_EXTEND_RUNTIME_PASS");
    return 0;
}
