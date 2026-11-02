// Android GLES3 translation of original KisakCOD IW3 R_HW_{Disable,Set}Blend.
// D3D9 RGB and alpha blend factors/equations are separate. Windows keeps D3D9.
#if defined(__ANDROID__)
#include "r_android_blend.h"
#include <EGL/egl.h>
#include <GLES3/gl3.h>

namespace {
bool Ready()
{
    return eglGetCurrentDisplay() != EGL_NO_DISPLAY
        && eglGetCurrentContext() != EGL_NO_CONTEXT
        && glGetError() == GL_NO_ERROR;
}

// IW3 s_blendTable_30 maps indices 1..10 directly to D3DBLEND enums.
// Index 0 is invalid; GL_ZERO is valid and must not be rejected.
GLenum Factor(uint32_t index)
{
    switch (index)
    {
    case 1: return GL_ZERO;
    case 2: return GL_ONE;
    case 3: return GL_SRC_COLOR;
    case 4: return GL_ONE_MINUS_SRC_COLOR;
    case 5: return GL_SRC_ALPHA;
    case 6: return GL_ONE_MINUS_SRC_ALPHA;
    case 7: return GL_DST_ALPHA;
    case 8: return GL_ONE_MINUS_DST_ALPHA;
    case 9: return GL_DST_COLOR;
    case 10: return GL_ONE_MINUS_DST_COLOR;
    default: return 0xFFFFFFFFu;
    }
}

// IW3 s_blendOpTable_30 likewise retains D3DBLENDOP enum values 1..5.
GLenum Equation(uint32_t index)
{
    switch (index)
    {
    case 1: return GL_FUNC_ADD;
    case 2: return GL_FUNC_SUBTRACT;
    case 3: return GL_FUNC_REVERSE_SUBTRACT;
    case 4: return GL_MIN;
    case 5: return GL_MAX;
    default: return 0;
    }
}

struct Snapshot
{
    GLboolean enabled;
    GLint rgbEquation, alphaEquation;
    GLint srcRgb, dstRgb, srcAlpha, dstAlpha;
};

bool Capture(Snapshot &s)
{
    s.enabled = glIsEnabled(GL_BLEND);
    glGetIntegerv(GL_BLEND_EQUATION_RGB, &s.rgbEquation);
    glGetIntegerv(GL_BLEND_EQUATION_ALPHA, &s.alphaEquation);
    glGetIntegerv(GL_BLEND_SRC_RGB, &s.srcRgb);
    glGetIntegerv(GL_BLEND_DST_RGB, &s.dstRgb);
    glGetIntegerv(GL_BLEND_SRC_ALPHA, &s.srcAlpha);
    glGetIntegerv(GL_BLEND_DST_ALPHA, &s.dstAlpha);
    return glGetError() == GL_NO_ERROR;
}

void Restore(const Snapshot &s)
{
    glBlendEquationSeparate(static_cast<GLenum>(s.rgbEquation),
                            static_cast<GLenum>(s.alphaEquation));
    glBlendFuncSeparate(static_cast<GLenum>(s.srcRgb),
                        static_cast<GLenum>(s.dstRgb),
                        static_cast<GLenum>(s.srcAlpha),
                        static_cast<GLenum>(s.dstAlpha));
    if (s.enabled) glEnable(GL_BLEND);
    else glDisable(GL_BLEND);
    (void)glGetError();
}
} // namespace

bool R_AndroidGlesDisableBlend()
{
    if (!Ready()) return false;
    const GLboolean enabled = glIsEnabled(GL_BLEND);
    if (glGetError() != GL_NO_ERROR) return false;
    glDisable(GL_BLEND);
    if (glGetError() == GL_NO_ERROR) return true;
    if (enabled) glEnable(GL_BLEND);
    else glDisable(GL_BLEND);
    (void)glGetError();
    return false;
}

bool R_AndroidGlesSetBlend(uint32_t bits)
{
    // The original R_ChangeState_0 has already normalized an omitted
    // alpha equation/factors to the RGB values before invoking this bridge.
    const GLenum rgbEquation = Equation((bits >> 8) & 7u);
    const GLenum alphaEquation = Equation((bits >> 24) & 7u);
    const GLenum srcRgb = Factor(bits & 15u);
    const GLenum dstRgb = Factor((bits >> 4) & 15u);
    const GLenum srcAlpha = Factor((bits >> 16) & 15u);
    const GLenum dstAlpha = Factor((bits >> 20) & 15u);
    if (!rgbEquation || !alphaEquation || srcRgb == 0xFFFFFFFFu || dstRgb == 0xFFFFFFFFu
        || srcAlpha == 0xFFFFFFFFu || dstAlpha == 0xFFFFFFFFu)
        return false; // never silently substitute an invalid D3D9 state
    if (!Ready()) return false;

    Snapshot before{};
    if (!Capture(before)) return false;
    glBlendEquationSeparate(rgbEquation, alphaEquation);
    glBlendFuncSeparate(srcRgb, dstRgb, srcAlpha, dstAlpha);
    glEnable(GL_BLEND);
    if (glGetError() == GL_NO_ERROR) return true;
    Restore(before);
    return false;
}
#endif
