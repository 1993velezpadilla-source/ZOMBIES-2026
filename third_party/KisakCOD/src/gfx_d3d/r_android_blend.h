#pragma once
// GLES3 bridge for the authentic IW3 GFXS0 blend-state bit layout.
// This is a renderer component, NOT a complete engine or gameplay APK.
#if defined(__ANDROID__)
#include <cstdint>
bool R_AndroidGlesDisableBlend();
bool R_AndroidGlesSetBlend(uint32_t originalStateBits0);
#endif
