#include <array>
#include <cassert>
#include <cstdint>
#include <cstring>
#include <cstdio>

void G_HitLocStrcpy(unsigned char *destination, const char *source);
extern "C" int z2026_iw3_hitloc_copy_smoke();

int main() {
    static_assert(sizeof(void*) == 8, "Run native pointer-width regression on 64-bit host");
    std::array<unsigned char, 48> dest{};
    dest.fill(0xD1);
    G_HitLocStrcpy(dest.data() + 7, "torso_upper");
    assert(std::strcmp(reinterpret_cast<const char*>(dest.data() + 7), "torso_upper") == 0);
    assert(dest[6] == 0xD1 && dest[19] == 0xD1);
    // The original function is a forward copy, not a padded string write.
    G_HitLocStrcpy(dest.data() + 7, "");
    assert(dest[7] == 0 && dest[8] == 'o');
    assert(z2026_iw3_hitloc_copy_smoke() == 1);
    std::puts("IW3_REAL_SP_HITLOC_64BIT_POINTER_COPY_GREEN");
    return 0;
}
