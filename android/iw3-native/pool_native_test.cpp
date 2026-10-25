#include "iw3_android_math_compat.h"
#include "pool_allocator.h"
#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <limits>

extern "C" int z2026_iw3_real_pool_smoke();

struct alignas(void*) PoolItem {
    void* next;
    std::uint64_t actor_or_asset_tag;
    std::array<std::uint8_t, 29> payload;
};

int main() {
    static_assert(sizeof(void*) == 8, "Pool regression requires 64-bit host");
    static_assert(sizeof(freenode) == sizeof(void*));
    constexpr std::size_t count = 97;
    std::array<PoolItem, count> storage{};
    pooldata_t state{};
    Pool_Init(reinterpret_cast<char*>(storage.data()), &state,
              sizeof(PoolItem), count);
    assert(state.activeCount == 0);
    assert(Pool_FreeCount(&state) == count);
    std::array<freenode*, count> allocations{};
    for(std::size_t i = 0; i < count; ++i) {
        allocations[i] = Pool_Alloc(&state);
        assert(allocations[i] == reinterpret_cast<freenode*>(&storage[i]));
        assert(state.activeCount == static_cast<int>(i + 1));
        assert(Pool_FreeCount(&state) == count - i - 1);
    }
    assert(Pool_Alloc(&state) == nullptr);
    for(std::size_t i = count; i-- > 0;) {
        Pool_Free(allocations[i], &state);
        assert(state.activeCount == static_cast<int>(i));
    }
    assert(Pool_FreeCount(&state) == count);
    for (std::size_t i = 0; i < count; ++i) {
        assert(Pool_Alloc(&state) == reinterpret_cast<freenode*>(&storage[i]));
    }
    assert(Pool_FreeCount(&state) == 0);
    assert(z2026_iw3_real_pool_smoke() == 1);
    std::puts("IW3_REAL_64BIT_POOL_ALLOCATOR_HOST_GREEN");
}
