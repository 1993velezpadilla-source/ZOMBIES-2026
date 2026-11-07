#pragma once
// Original IW3 R_HW_DisableSampler -> GLES3 texture unbinding only.
// This does not register/upload IW3 GfxImage resources or render a frame.
#if defined(__ANDROID__)
#include <cstdint>
bool R_AndroidGlesDisableSamplerTexture(uint32_t samplerIndex);
#endif
