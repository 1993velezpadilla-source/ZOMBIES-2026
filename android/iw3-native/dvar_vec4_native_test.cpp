#include <cassert>
#include <cmath>
#include <cstdio>
#include <limits>
#include <universal/q_shared.h>

bool __cdecl Vec4Compare(const float *a, const float *b);

int main()
{
    const float a[4] = {1.0f, -0.0f, 3.5f, -8.0f};
    float b[4] = {1.0f, 0.0f, 3.5f, -8.0f};
    assert(Vec4Compare(a, b)); // exact original comparison treats signed zero as equal

    for (int component = 0; component < 4; ++component)
    {
        for (int i = 0; i < 4; ++i) b[i] = a[i];
        b[component] = a[component] + 1.0f;
        assert(!Vec4Compare(a, b));
    }

    float nan_vector[4] = {1.0f, 2.0f, 3.0f, 4.0f};
    nan_vector[2] = std::numeric_limits<float>::quiet_NaN();
    assert(!Vec4Compare(nan_vector, nan_vector));

    std::puts("IW3_ORIGINAL_VEC4_COMPARE_HOST_GREEN");
    return 0;
}
