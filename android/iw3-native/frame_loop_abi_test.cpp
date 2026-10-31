// ABI fixture executing the EXACT entity-iteration block extracted from
// KisakCOD's g_main.cpp G_RunFrame. This is NOT a game simulation and
// does not claim full G_RunFrame or Android game runtime has been ported.
// Deliberately perturb pointer and field layout to catch baked-in x86 offsets.
#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <type_traits>

enum : unsigned int {
    FL_NO_AUTO_ANIM_UPDATE = 0x1000u,
    FL_REPEAT_ANIM_UPDATE = 0x40000u,
};

struct gentity_s {
    // Artificially different from legacy Windows 628-byte entity so the
    // actual ported source *cannot* accidentally rely on the old layout.
    std::array<std::uint64_t, 41> before_r{};
    struct {
        std::uint8_t inuse = 0;
    } r;
    std::array<std::uint64_t, 41> before_flags{};
    unsigned int flags = 0;
    std::uint64_t user_token = 0;
};
static_assert(sizeof(void*) == 8, "Run ABI regression as 64-bit host");
static_assert(sizeof(gentity_s) != 628, "Legacy 32-bit entity stride must NOT match");
static_assert(offsetof(gentity_s, r.inuse) != 168, "Legacy embedded offset must NOT match");
static_assert((offsetof(gentity_s, flags) - offsetof(gentity_s, r.inuse)) != 136,
              "Legacy flags offset must NOT match");

struct Level {
    int num_entities = 0;
    int currentIndex = -1;
    bool checkAnimChange = false;
} level;
std::array<gentity_s, 5> g_entities{};
std::array<int, 5> calls{};
int script_calls = 0;
bool return_false_for_entity_three = false;

bool G_DObjUpdateServerTime(gentity_s *ent, int delta) {
    assert(delta == 1);
    assert(ent >= g_entities.data());
    assert(ent < g_entities.data() + g_entities.size());
    const auto id = static_cast<int>(ent - g_entities.data());
    ++calls[static_cast<std::size_t>(id)];
    // This fixture only mocks the DObj callback; entity LOOP under test
    // below is copied byte-for-byte from the actual game G_RunFrame.
    if (id == 3 && return_false_for_entity_three) return false;
    ent->r.inuse = 0;
    return true;
}
void Scr_RunCurrentThreads() { ++script_calls; }

void run_source_loop() {
    level.currentIndex = 1;
    level.checkAnimChange = false;
    bool checkAnimChange = false;
    // BEGIN EXACT SOURCE — emitted from KisakCOD/src/game/g_main.cpp.
#include "iw3_g_runframe_entity_loop.inc"
    // END EXACT SOURCE. Keep it unchanged and fail on source drift.
    assert(level.currentIndex == level.num_entities);
}

int main() {
    level.num_entities = 5;
    g_entities[1].r.inuse = 1;
    g_entities[1].flags = FL_REPEAT_ANIM_UPDATE;
    g_entities[2].r.inuse = 1;
    g_entities[2].flags = FL_NO_AUTO_ANIM_UPDATE | FL_REPEAT_ANIM_UPDATE;
    g_entities[3].r.inuse = 1;
    g_entities[3].flags = FL_REPEAT_ANIM_UPDATE;
    g_entities[4].r.inuse = 1;
    g_entities[4].flags = 0;

    run_source_loop();
    assert(calls[0] == 0);
    assert(calls[1] == 1 && calls[2] == 0);
    assert(calls[3] == 1 && calls[4] == 0);
    assert(script_calls == 2 && level.checkAnimChange);
    // Test original source's G_DObjUpdateServerTime FALSE branch.
    calls.fill(0);
    script_calls = 0;
    g_entities[3].r.inuse = 1;
    return_false_for_entity_three = true;
    run_source_loop();
    assert(calls[3] == 1);
    assert(script_calls == 0);
    std::puts("IW3_AUTHENTIC_G_RUNFRAME_TYPED_ENTITY_LOOP_64BIT_HOST_GREEN");
    return 0;
}
