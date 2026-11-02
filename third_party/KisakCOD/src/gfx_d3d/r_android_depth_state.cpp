// Android GLES3 translation of original IW3 R_HW_SetDepth* operations.
#if defined(__ANDROID__)
#include "r_android_depth_state.h"
#include <EGL/egl.h>
#include <GLES3/gl3.h>
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
#endif
