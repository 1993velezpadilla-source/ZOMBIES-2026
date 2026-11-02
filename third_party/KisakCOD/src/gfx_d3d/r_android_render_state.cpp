// Android GLES3 translation of authentic IW3 R_HW_SetAlphaTestEnable
// and R_HW_SetColorMask. Windows D3D9 remains in original r_state.cpp.
// GLES3 does not implement fixed-function alpha testing; reject enabled
// alpha test until the genuine IW3 fragment shader path uses discard.
#if defined(__ANDROID__)
#include "r_android_render_state.h"
#include <EGL/egl.h>
#include <GLES3/gl3.h>

namespace {
bool HasCurrentContextAndNoError()
{
    return eglGetCurrentDisplay() != EGL_NO_DISPLAY
        && eglGetCurrentContext() != EGL_NO_CONTEXT
        && glGetError() == GL_NO_ERROR;
}
}

bool R_AndroidGlesSetAlphaTestEnable(uint16_t originalStateBits0)
{
    if (!HasCurrentContextAndNoError())
        return false;
    // GFXS0_ATEST_DISABLE (0x800): only this mode is currently safe.
    // Never pretend that glDisable(GL_SAMPLE_ALPHA_TO_COVERAGE) implements
    // D3D9 alpha comparison; GLES3 needs shader-side fragment discard.
    return (originalStateBits0 & 0x800u) != 0;
}

bool R_AndroidGlesSetColorMask(uint32_t originalStateBits0)
{
    if (!HasCurrentContextAndNoError())
        return false;

    GLboolean previous[4] = {GL_FALSE, GL_FALSE, GL_FALSE, GL_FALSE};
    glGetBooleanv(GL_COLOR_WRITEMASK, previous);
    if (glGetError() != GL_NO_ERROR)
        return false;

    // Original D3DRS_COLORWRITEENABLE mask: RGB=7, alpha=8.
    const GLboolean rgb = (originalStateBits0 & 0x08000000u) ? GL_TRUE : GL_FALSE;
    const GLboolean alpha = (originalStateBits0 & 0x10000000u) ? GL_TRUE : GL_FALSE;
    glColorMask(rgb, rgb, rgb, alpha);
    if (glGetError() == GL_NO_ERROR)
        return true;

    // Failed mutation must not leave the original command buffer's
    // subsequent draws with an unexpected color-write mask.
    glColorMask(previous[0], previous[1], previous[2], previous[3]);
    (void)glGetError();
    return false;
}
#endif
