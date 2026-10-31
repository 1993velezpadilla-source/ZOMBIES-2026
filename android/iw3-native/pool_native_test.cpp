#include "iw3_android_math_compat.h"
#include "pool_allocator.h"
#include "../physics/phys_userdata.h"
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
    // The actual physics payload grows from 112 to 120 bytes on ARM64.
    // The old Phys_Init call still passed 0x70 after Pool_Init was repaired,
    // so its free-list nodes landed inside adjacent live payloads.
    static_assert(sizeof(PhysObjUserData) > 0x70);
    constexpr std::size_t physicsCount = 512;
    PhysObjUserData physics[physicsCount]{};
    INIT_STATIC_POOL(physics, &state);
    for (std::size_t i = 0; i < physicsCount; ++i) {
        assert(Pool_Alloc(&state) == reinterpret_cast<freenode*>(&physics[i]));
        physics[i].savedPos[0] = static_cast<float>(i);
        physics[i].state = PHYS_OBJ_STATE_FREE;
    }
    assert(Pool_Alloc(&state) == nullptr);
    for (std::size_t i = 0; i < physicsCount; ++i) {
        assert(physics[i].savedPos[0] == static_cast<float>(i));
        assert(physics[i].state == PHYS_OBJ_STATE_FREE);
        Pool_Free(reinterpret_cast<freenode*>(&physics[i]), &state);
    }
    assert(state.activeCount == 0 && Pool_FreeCount(&state) == physicsCount);
    assert(z2026_iw3_real_pool_smoke() == 1);
    std::puts("IW3_REAL_64BIT_POOL_ALLOCATOR_HOST_GREEN");
}
