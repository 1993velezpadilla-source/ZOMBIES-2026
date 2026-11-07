#pragma once
// Authentic IW3 depth state -> GLES3. NOT a renderer/frame/game proof.
#if defined(__ANDROID__)
#include <cstdint>
bool R_AndroidGlesSetDepthWrite(uint8_t originalStateBits1);
bool R_AndroidGlesSetDepthTest(uint8_t originalStateBits1);
bool R_AndroidGlesSetDepthFunc(uint8_t originalStateBits1);
// Approximate D3D9 normalized depth bias for GLES3 fixed-point depth attachments.
// Fails closed when EGL, depth precision, or GL state is unsupported.
bool R_AndroidGlesSetPolygonOffset(float slopeScale, float normalizedDepthBias);
#endif
