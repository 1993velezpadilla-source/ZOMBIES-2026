// Android GLES3 translation of original IW3 R_HW_SetDepth* operations.
#if defined(__ANDROID__)
#include "r_android_depth_state.h"
#include <EGL/egl.h>
#include <GLES3/gl3.h>
#include <cmath>
namespace {
bool Ready()
{
    return eglGetCurrentDisplay() != EGL_NO_DISPLAY
        && eglGetCurrentContext() != EGL_NO_CONTEXT
        && glGetError() == GL_NO_ERROR;
}
}
bool R_AndroidGlesSetDepthWrite(uint8_t bits)
{
    if (!Ready()) return false;
    GLboolean previous = GL_FALSE;
    glGetBooleanv(GL_DEPTH_WRITEMASK, &previous);
    if (glGetError() != GL_NO_ERROR) return false;
    glDepthMask((bits & 1u) ? GL_TRUE : GL_FALSE);
    if (glGetError() == GL_NO_ERROR) return true;
    glDepthMask(previous);
    (void)glGetError();
    return false;
}
bool R_AndroidGlesSetDepthTest(uint8_t bits)
{
    if (!Ready()) return false;
    GLboolean previous = glIsEnabled(GL_DEPTH_TEST);
    if (glGetError() != GL_NO_ERROR) return false;
    if (bits & 2u) glDisable(GL_DEPTH_TEST);
    else glEnable(GL_DEPTH_TEST);
    if (glGetError() == GL_NO_ERROR) return true;
    if (previous) glEnable(GL_DEPTH_TEST);
    else glDisable(GL_DEPTH_TEST);
    (void)glGetError();
    return false;
}
bool R_AndroidGlesSetDepthFunc(uint8_t bits)
{
    // Original s_depthTestTable_30 = {D3DCMP_ALWAYS, LESS, EQUAL, LESSEQUAL}.
    const GLenum functions[4] = {GL_ALWAYS, GL_LESS, GL_EQUAL, GL_LEQUAL};
    if (!Ready()) return false;
    GLint previous = 0;
    glGetIntegerv(GL_DEPTH_FUNC, &previous);
    if (glGetError() != GL_NO_ERROR) return false;
    glDepthFunc(functions[(bits >> 2) & 3u]);
    if (glGetError() == GL_NO_ERROR) return true;
    glDepthFunc(static_cast<GLenum>(previous));
    (void)glGetError();
    return false;
}
// Original IW3 R_HW_SetPolygonOffset receives D3D9 slope scale and a
// normalized constant depth bias. GLES3 uses a device-dependent minimum
// resolvable depth unit instead. For 16/24-bit fixed-point depth attachments
// we use the nominal 2^depthBits scale; parity must still be tested on GPU.
bool R_AndroidGlesSetPolygonOffset(float slopeScale, float normalizedDepthBias)
{
    if (!std::isfinite(slopeScale) || !std::isfinite(normalizedDepthBias)
        || std::fabs(normalizedDepthBias) > 1.0f || !Ready())
        return false;

    const bool offset = slopeScale != 0.0f || normalizedDepthBias != 0.0f;
    GLint depthBits = 0;
    if (offset)
    {
        glGetIntegerv(GL_DEPTH_BITS, &depthBits);
        if (glGetError() != GL_NO_ERROR || (depthBits != 16 && depthBits != 24))
            return false; // No depth attachment, float depth, or unknown format.
    }

    const double nominalUnits = std::ldexp(
        static_cast<double>(normalizedDepthBias), depthBits);
    if (!std::isfinite(nominalUnits))
        return false;
    const GLfloat units = static_cast<GLfloat>(nominalUnits);
    if (!std::isfinite(units))
        return false;

    GLfloat oldFactor = 0.0f;
    GLfloat oldUnits = 0.0f;
    glGetFloatv(GL_POLYGON_OFFSET_FACTOR, &oldFactor);
    if (glGetError() != GL_NO_ERROR) return false;
    glGetFloatv(GL_POLYGON_OFFSET_UNITS, &oldUnits);
    if (glGetError() != GL_NO_ERROR) return false;
    const GLboolean oldEnabled = glIsEnabled(GL_POLYGON_OFFSET_FILL);
    if (glGetError() != GL_NO_ERROR) return false;

    glPolygonOffset(slopeScale, units);
    if (glGetError() == GL_NO_ERROR)
    {
        if (offset) glEnable(GL_POLYGON_OFFSET_FILL);
        else glDisable(GL_POLYGON_OFFSET_FILL);
        if (glGetError() == GL_NO_ERROR) return true;
    }

    // Best-effort restoration; caller fails fatally instead of rendering
    // with a potentially inconsistent GPU state.
    glPolygonOffset(oldFactor, oldUnits);
    if (oldEnabled) glEnable(GL_POLYGON_OFFSET_FILL);
    else glDisable(GL_POLYGON_OFFSET_FILL);
    (void)glGetError();
    return false;
}
#endif
