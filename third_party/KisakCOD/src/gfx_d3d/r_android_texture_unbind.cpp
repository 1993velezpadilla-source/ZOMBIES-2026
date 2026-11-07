// GLES3 implementation of original IW3 R_HW_DisableSampler / D3D9 SetTexture(unit, nullptr).
// Preserve the sampler object and the previously active GL texture unit.
#if defined(__ANDROID__)
#include "r_android_texture_unbind.h"
#include <EGL/egl.h>
#include <GLES3/gl3.h>

namespace {
constexpr uint32_t kMaxIw3Samplers = 16;
struct Binding { GLenum target; GLenum query; GLint previous; };
}

bool R_AndroidGlesDisableSamplerTexture(uint32_t samplerIndex)
{
    if (samplerIndex >= kMaxIw3Samplers ||
        eglGetCurrentDisplay() == EGL_NO_DISPLAY ||
        eglGetCurrentContext() == EGL_NO_CONTEXT ||
        glGetError() != GL_NO_ERROR)
        return false;

    GLint maxUnits = 0, previousActive = 0;
    glGetIntegerv(GL_MAX_COMBINED_TEXTURE_IMAGE_UNITS, &maxUnits);
    if (glGetError() != GL_NO_ERROR || maxUnits <= 0 ||
        samplerIndex >= static_cast<uint32_t>(maxUnits)) return false;
    glGetIntegerv(GL_ACTIVE_TEXTURE, &previousActive);
    if (glGetError() != GL_NO_ERROR) return false;
    glActiveTexture(GL_TEXTURE0 + samplerIndex);
    if (glGetError() != GL_NO_ERROR) return false;

    // D3D9 accepts 2D, cube and volume textures on a stage. GLES3 has a
    // separate binding for each target, so clear all three, not only 2D.
    Binding bindings[] = {
        {GL_TEXTURE_2D, GL_TEXTURE_BINDING_2D, 0},
        {GL_TEXTURE_CUBE_MAP, GL_TEXTURE_BINDING_CUBE_MAP, 0},
        {GL_TEXTURE_3D, GL_TEXTURE_BINDING_3D, 0},
    };
    bool captured = true;
    for (Binding &binding : bindings) {
        glGetIntegerv(binding.query, &binding.previous);
        if (glGetError() != GL_NO_ERROR) { captured = false; break; }
    }
    bool ok = captured;
    if (captured) {
        for (const Binding &binding : bindings) {
            glBindTexture(binding.target, 0);
            if (glGetError() != GL_NO_ERROR) { ok = false; break; }
        }
        if (!ok) {
            // A failed GL mutation can still alter state. Roll back all
            // three targets while this texture unit remains active.
            for (const Binding &binding : bindings)
                glBindTexture(binding.target, static_cast<GLuint>(binding.previous));
            if (glGetError() != GL_NO_ERROR) ok = false;
        }
    }
    glActiveTexture(static_cast<GLenum>(previousActive));
    if (glGetError() != GL_NO_ERROR) {
        // A failed active-unit restoration invalidates the transaction.
        glActiveTexture(GL_TEXTURE0 + samplerIndex);
        if (captured) {
            for (const Binding &binding : bindings)
                glBindTexture(binding.target, static_cast<GLuint>(binding.previous));
        }
        glActiveTexture(static_cast<GLenum>(previousActive));
        (void)glGetError();
        return false;
    }
    return ok;
}
#endif
