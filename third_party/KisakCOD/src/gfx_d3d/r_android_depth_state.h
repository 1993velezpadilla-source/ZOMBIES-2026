#pragma once
// Authentic IW3 depth state -> GLES3. NOT a renderer/frame/game proof.
#if defined(__ANDROID__)
#include <cstdint>
bool R_AndroidGlesSetDepthWrite(uint8_t originalStateBits1);
bool R_AndroidGlesSetDepthTest(uint8_t originalStateBits1);
bool R_AndroidGlesSetDepthFunc(uint8_t originalStateBits1);
#endif
