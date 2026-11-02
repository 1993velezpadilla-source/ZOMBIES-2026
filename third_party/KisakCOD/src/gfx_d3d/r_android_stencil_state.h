#pragma once
// Original IW3 stencil state -> GLES3. Provider only; NOT a frame/game proof.
#if defined(__ANDROID__)
#include <cstdint>
bool R_AndroidGlesEnableStencil(bool enabled);
bool R_AndroidGlesSetStencilOp(bool backFace, uint32_t pass, uint32_t fail, uint32_t depthFail);
bool R_AndroidGlesSetStencilFunc(bool backFace, uint32_t function);
#endif
