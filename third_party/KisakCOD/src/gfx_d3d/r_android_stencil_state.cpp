// GLES3 bridge for authentic KisakCOD IW3 stencil operations in r_state.cpp.
// D3D9 s_stencilOpTable_30 and s_stencilFuncTable_30 are 1-based enums.
// GL_FRONT matches IW3's clockwise front after R_AndroidGlesSetCullFace.
#if defined(__ANDROID__)
#include "r_android_stencil_state.h"
#include <EGL/egl.h>
#include <GLES3/gl3.h>

namespace {
bool Ready()
{
    return eglGetCurrentDisplay() != EGL_NO_DISPLAY
        && eglGetCurrentContext() != EGL_NO_CONTEXT
        && glGetError() == GL_NO_ERROR;
}
GLenum Operation(uint32_t index)
{
    static const GLenum values[8] = {
        GL_KEEP, GL_ZERO, GL_REPLACE, GL_INCR, GL_DECR,
        GL_INVERT, GL_INCR_WRAP, GL_DECR_WRAP
    };
    return index < 8 ? values[index] : GL_INVALID_ENUM;
}
GLenum Comparison(uint32_t index)
{
    static const GLenum values[8] = {
        GL_NEVER, GL_LESS, GL_EQUAL, GL_LEQUAL,
        GL_GREATER, GL_NOTEQUAL, GL_GEQUAL, GL_ALWAYS
    };
    return index < 8 ? values[index] : GL_INVALID_ENUM;
}
GLenum Face(bool back) { return back ? GL_BACK : GL_FRONT; }
struct StencilOpSnapshot { GLint fail, depthFail, pass; };
bool CaptureOp(bool back, StencilOpSnapshot &s)
{
    glGetIntegerv(back ? GL_STENCIL_BACK_FAIL : GL_STENCIL_FAIL, &s.fail);
    glGetIntegerv(back ? GL_STENCIL_BACK_PASS_DEPTH_FAIL : GL_STENCIL_PASS_DEPTH_FAIL, &s.depthFail);
    glGetIntegerv(back ? GL_STENCIL_BACK_PASS_DEPTH_PASS : GL_STENCIL_PASS_DEPTH_PASS, &s.pass);
    return glGetError() == GL_NO_ERROR;
}
struct StencilFuncSnapshot { GLint function, reference, mask; };
bool CaptureFunc(bool back, StencilFuncSnapshot &s)
{
    glGetIntegerv(back ? GL_STENCIL_BACK_FUNC : GL_STENCIL_FUNC, &s.function);
    glGetIntegerv(back ? GL_STENCIL_BACK_REF : GL_STENCIL_REF, &s.reference);
    glGetIntegerv(back ? GL_STENCIL_BACK_VALUE_MASK : GL_STENCIL_VALUE_MASK, &s.mask);
    return glGetError() == GL_NO_ERROR;
}
} // namespace

bool R_AndroidGlesEnableStencil(bool enabled)
{
    if (!Ready()) return false;
    const GLboolean oldEnabled = glIsEnabled(GL_STENCIL_TEST);
    if (glGetError() != GL_NO_ERROR) return false;
    if (enabled) glEnable(GL_STENCIL_TEST);
    else glDisable(GL_STENCIL_TEST);
    if (glGetError() == GL_NO_ERROR) return true;
    if (oldEnabled) glEnable(GL_STENCIL_TEST);
    else glDisable(GL_STENCIL_TEST);
    (void)glGetError();
    return false;
}

bool R_AndroidGlesSetStencilOp(bool back, uint32_t pass, uint32_t fail, uint32_t depthFail)
{
    // Do not index the original tables with untrusted values.
    if (pass >= 8 || fail >= 8 || depthFail >= 8 || !Ready()) return false;
    StencilOpSnapshot old{};
    if (!CaptureOp(back, old)) return false;
    // D3D9 call order is pass/fail/zfail; GLES order is fail/zfail/pass.
    glStencilOpSeparate(Face(back), Operation(fail), Operation(depthFail), Operation(pass));
    if (glGetError() == GL_NO_ERROR) return true;
    glStencilOpSeparate(Face(back), static_cast<GLenum>(old.fail),
                        static_cast<GLenum>(old.depthFail), static_cast<GLenum>(old.pass));
    (void)glGetError();
    return false;
}

bool R_AndroidGlesSetStencilFunc(bool back, uint32_t function)
{
    if (function >= 8 || !Ready()) return false;
    StencilFuncSnapshot old{};
    if (!CaptureFunc(back, old)) return false;
    // The original functions only change the comparison; keep ref/mask.
    glStencilFuncSeparate(Face(back), Comparison(function), old.reference,
                          static_cast<GLuint>(old.mask));
    if (glGetError() == GL_NO_ERROR) return true;
    glStencilFuncSeparate(Face(back), static_cast<GLenum>(old.function),
                          old.reference, static_cast<GLuint>(old.mask));
    (void)glGetError();
    return false;
}
#endif
