#pragma once
// Genuine IW3 R_HW_SetSamplerState GLES3 bridge. Not a renderer/frame proof.
#if defined(__ANDROID__)
#include <cstdint>
bool R_AndroidGlesSetSamplerState(uint32_t unit, uint32_t state,
                                  uint32_t oldState, uint32_t *appliedState);
// Must be called while the owning EGL context is current before teardown.
void R_AndroidGlesReleaseSamplerStates();
#endif
