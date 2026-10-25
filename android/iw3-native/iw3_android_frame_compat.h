#pragma once
// The only adapter around the unchanged original Com_Memcpy in KisakCOD.
// In original source iassert(expr) checks critical pointer invariants.
// This native shim retains a fail-closed runtime check even in Release.
#include "iw3_android_math_compat.h"
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <cstdlib>

#define iassert(expr) do { if (!(expr)) std::abort(); } while (0)
