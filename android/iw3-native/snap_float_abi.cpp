// Directly compile the same header used by genuine IW3 qcommon/game code.
#include "../qcommon/snap_float.h"

extern "C" __attribute__((visibility("default")))
int z2026_iw3_snap_float_to_int(float value)
{
    return SnapFloatToInt(value);
}

extern "C" __attribute__((visibility("default")))
int z2026_iw3_snap_float_smoke()
{
    std::fenv_t saved;
    if (std::fegetenv(&saved) != 0) return 0;
    if (std::fesetround(FE_TONEAREST) != 0) return 0;
    const bool passed =
        z2026_iw3_snap_float_to_int(0.5f) == 0 &&
        z2026_iw3_snap_float_to_int(1.5f) == 2 &&
        z2026_iw3_snap_float_to_int(2.5f) == 2 &&
        z2026_iw3_snap_float_to_int(-1.5f) == -2 &&
        z2026_iw3_snap_float_to_int(2147483648.0f) ==
            std::numeric_limits<int>::min();
    const int restored = std::fesetenv(&saved);
    return passed && restored == 0;
}
