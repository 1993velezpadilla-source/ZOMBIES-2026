#include <cassert>
#include <cmath>
#include <cstdio>

extern "C" int z2026_iw3_math_source_abi_version();
extern "C" void z2026_iw3_angle_vectors(
    const float *, float *, float *, float *);
extern "C" int z2026_iw3_math_smoke();
extern "C" int z2026_iw3_surface_type_from_name(const char*);
extern "C" const char* z2026_iw3_surface_type_name(int);
extern "C" int z2026_iw3_surface_smoke();

static bool near(float a, float b) { return std::fabs(a-b) < 0.0002f; }

int main() {
    assert(z2026_iw3_math_source_abi_version() == 1);
    assert(z2026_iw3_math_smoke() == 1);
    const float original_forward[3] = {0, 0, 0};
    float f[3]{}, r[3]{}, u[3]{};
    z2026_iw3_angle_vectors(original_forward, f, r, u);
    assert(near(f[0], 1) && near(f[1], 0) && near(f[2], 0));
    assert(near(r[0], 0) && near(r[1], -1) && near(r[2], 0));
    assert(near(u[0], 0) && near(u[1], 0) && near(u[2], 1));
    const float pitch[3] = {90, 0, 0};
    z2026_iw3_angle_vectors(pitch, f, r, u);
    assert(near(f[0], 0) && near(f[2], -1));
    assert(z2026_iw3_surface_smoke() == 1);
    assert(z2026_iw3_surface_type_from_name("wood") == 21);
    assert(z2026_iw3_surface_type_from_name("FoLiAgE") == 8);
    assert(z2026_iw3_surface_type_name(20)[0] == \'w\');
    puts("IW3_REAL_AIM_AND_SURFACE_HOST_TEST_GREEN");
    return 0;
}
