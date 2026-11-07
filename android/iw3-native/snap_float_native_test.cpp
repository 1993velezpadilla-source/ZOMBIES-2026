#include <array>
#include <bit>
#include <cassert>
#include <cstdio>
#include <cfenv>
#include <cmath>
#include <cstdint>
#include <limits>
#if defined(_M_IX86) || defined(_M_X64) || defined(__i386__) || defined(__x86_64__)
#include <xmmintrin.h>
#endif
// Reproduce Win32's function-like macros before including the actual
// engine header. Native Android compilation alone missed this regression.
#define min(a, b) (((a) < (b)) ? (a) : (b))
#define max(a, b) (((a) > (b)) ? (a) : (b))
#include "../qcommon/snap_float.h"
#undef min
#undef max

extern "C" int z2026_iw3_snap_float_smoke();
extern "C" int z2026_iw3_snap_float_to_int(float);

int main()
{
    std::fenv_t saved;
    assert(std::fegetenv(&saved) == 0);
    const std::array<int, 4> modes = {
        FE_TONEAREST, FE_DOWNWARD, FE_UPWARD, FE_TOWARDZERO};
    struct Case { float value; std::array<int, 4> expected; };
    const Case cases[] = {
        {0.0f, {0, 0, 0, 0}}, {-0.0f, {0, 0, 0, 0}},
        {0.5f, {0, 0, 1, 0}}, {-0.5f, {0, -1, 0, 0}},
        {1.5f, {2, 1, 2, 1}}, {-1.5f, {-2, -2, -1, -1}},
        {2.5f, {2, 2, 3, 2}}, {-2.5f, {-2, -3, -2, -2}},
        {2147483520.0f, {2147483520, 2147483520, 2147483520, 2147483520}},
        {-2147483648.0f, {INT32_MIN, INT32_MIN, INT32_MIN, INT32_MIN}},
        {2147483648.0f, {INT32_MIN, INT32_MIN, INT32_MIN, INT32_MIN}},
        {std::numeric_limits<float>::infinity(),
            {INT32_MIN, INT32_MIN, INT32_MIN, INT32_MIN}},
        {-std::numeric_limits<float>::infinity(),
            {INT32_MIN, INT32_MIN, INT32_MIN, INT32_MIN}},
        {std::numeric_limits<float>::quiet_NaN(),
            {INT32_MIN, INT32_MIN, INT32_MIN, INT32_MIN}},
    };
    std::size_t comparisons = 0;
    for (std::size_t mode = 0; mode < modes.size(); ++mode)
    {
        assert(std::fesetround(modes[mode]) == 0);
        for (const auto &test : cases)
        {
            assert(kisak_detail::SnapFloatToIntPortable(test.value) == test.expected[mode]);
            assert(SnapFloatToInt(test.value) == test.expected[mode]);
            assert(z2026_iw3_snap_float_to_int(test.value) == test.expected[mode]);
        }
#if defined(_M_IX86) || defined(_M_X64) || defined(__i386__) || defined(__x86_64__)
        // Independent hardware oracle: original x86 CVTSS2SI instruction.
        // Arbitrary bit patterns exercise subnormals, ties, huge values and
        // both signs of NaN/Infinity, not merely a few convenient decimals.
        std::uint32_t bits = 0x8f701123;
        for (int i = 0; i < 1000000; ++i)
        {
            bits ^= bits << 13;
            bits ^= bits >> 17;
            bits ^= bits << 5;
            const float input = std::bit_cast<float>(bits);
            const int expected = _mm_cvtss_si32(_mm_set_ss(input));
            const int actual = kisak_detail::SnapFloatToIntPortable(input);
            if (expected != actual)
            {
                std::fprintf(stderr, "SNAP mismatch bits=%08x mode=%d expected=%d actual=%d\n",
                             bits, modes[mode], expected, actual);
                return 1;
            }
            ++comparisons;
        }
#endif
    }
    assert(std::fesetround(FE_TONEAREST) == 0);
    assert(z2026_iw3_snap_float_smoke() == 1);
    assert(SnapFloat(2.5f) == 2.0f);
    assert(SnapFloat(-1.5f) == -2.0f);
    assert(std::fesetenv(&saved) == 0);
    std::printf("IW3_ORIGINAL_SNAP_PORTABLE_GREEN comparisons=%zu modes=4\n", comparisons);
}
