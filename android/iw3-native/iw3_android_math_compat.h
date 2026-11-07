#pragma once
// Thin ABI portability declarations ONLY. The maths executed by the shared
// library come from the original KisakCOD com_math_anglevectors.cpp file.
// All formulae, arithmetic and player aiming semantics stay in engine source.
#include <cmath>
#include <cstdint>

#if !defined(_MSC_VER) && !defined(__cdecl)
#define __cdecl
#endif

// IW3's original Windows q_shared.h used these degree-array indices.
#ifndef PITCH
#define PITCH 0
#endif
#ifndef YAW
#define YAW 1
#endif
#ifndef ROLL
#define ROLL 2
#endif
#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

// This dependency belongs to KisakCOD's larger com_math.cpp module.
// Phase A deliberately does not export or use AnglesToQuat; this native
// port must remove the dead reference rather than replace it with a stub.
void __cdecl AxisToQuat(const float (*axis)[3], float *quat);
