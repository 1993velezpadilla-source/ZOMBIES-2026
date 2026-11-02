// GLES3 sampler-object translation for the original IW3 decoded D3D9 sampler bits.
// Keeps per-texture-unit sampling independent of shared texture objects.
#if defined(__ANDROID__)
#include "r_android_sampler_state.h"
#include <EGL/egl.h>
#include <GLES3/gl3.h>
#include <cstring>

namespace {
constexpr uint32_t kMaxIw3Samplers = 16;
constexpr GLenum kTextureMaxAnisotropy = 0x84FE; // GL_TEXTURE_MAX_ANISOTROPY_EXT
constexpr GLenum kMaxTextureMaxAnisotropy = 0x84FF;
struct Slot { EGLContext context; GLuint object; };
Slot slots[kMaxIw3Samplers] = {};
bool Ready()
{
    return eglGetCurrentDisplay() != EGL_NO_DISPLAY
        && eglGetCurrentContext() != EGL_NO_CONTEXT
        && glGetError() == GL_NO_ERROR;
}
GLenum Wrap(uint32_t value)
{
    switch (value) {
    case 1: return GL_REPEAT;          // D3DTADDRESS_WRAP
    case 2: return GL_MIRRORED_REPEAT; // D3DTADDRESS_MIRROR
    case 3: return GL_CLAMP_TO_EDGE;   // D3DTADDRESS_CLAMP
    default: return 0;                // BORDER / MIRRORONCE unsupported
    }
}
bool HasAnisotropy()
{
    GLint count = 0;
    glGetIntegerv(GL_NUM_EXTENSIONS, &count);
    if (glGetError() != GL_NO_ERROR || count < 0) return false;
    for (GLint i = 0; i < count; ++i) {
        const char *ext = reinterpret_cast<const char *>(glGetStringi(GL_EXTENSIONS, static_cast<GLuint>(i)));
        if (ext && std::strcmp(ext, "GL_EXT_texture_filter_anisotropic") == 0)
            return true;
    }
    return glGetError() == GL_NO_ERROR && false;
}
} // namespace

bool R_AndroidGlesSetSamplerState(uint32_t unit, uint32_t state,
                                  uint32_t oldState, uint32_t *appliedState)
{
    if (!appliedState || unit >= kMaxIw3Samplers || !Ready()) return false;
    GLint maxUnits = 0;
    glGetIntegerv(GL_MAX_COMBINED_TEXTURE_IMAGE_UNITS, &maxUnits);
    if (glGetError() != GL_NO_ERROR || maxUnits <= 0 ||
        unit >= static_cast<uint32_t>(maxUnits)) return false;

    const uint32_t min = (state >> 8) & 15u;
    const uint32_t mag = (state >> 12) & 15u;
    const uint32_t mip = (state >> 16) & 15u;
    const uint32_t aniso = state & 255u;
    const GLenum wrapS = Wrap((state >> 20) & 3u);
    const GLenum wrapT = Wrap((state >> 22) & 3u);
    const GLenum wrapR = Wrap((state >> 24) & 3u);
    if ((min != 1 && min != 2 && min != 3) ||
        (mag != 1 && mag != 2 && mag != 3) || mip > 2 ||
        !wrapS || !wrapT || !wrapR) return false;

    const bool linearMin = min != 1;
    const GLenum minFilter = mip == 0 ? (linearMin ? GL_LINEAR : GL_NEAREST)
        : mip == 1 ? (linearMin ? GL_LINEAR_MIPMAP_NEAREST : GL_NEAREST_MIPMAP_NEAREST)
                   : (linearMin ? GL_LINEAR_MIPMAP_LINEAR : GL_NEAREST_MIPMAP_LINEAR);
    const GLenum magFilter = mag == 1 ? GL_NEAREST : GL_LINEAR;
    GLfloat maxAniso = 1.0f;
    if (aniso > 1) {
        if (!HasAnisotropy()) return false;
        glGetFloatv(kMaxTextureMaxAnisotropy, &maxAniso);
        if (glGetError() != GL_NO_ERROR || maxAniso < static_cast<GLfloat>(aniso))
            return false; // never silently lower the original requested quality
    }

    // glGetIntegerv(GL_SAMPLER_BINDING) refers to the active texture unit.
    GLint previousActive = 0, previousBinding = 0;
    glGetIntegerv(GL_ACTIVE_TEXTURE, &previousActive);
    if (glGetError() != GL_NO_ERROR) return false;
    glActiveTexture(GL_TEXTURE0 + unit);
    if (glGetError() != GL_NO_ERROR) return false;
    glGetIntegerv(GL_SAMPLER_BINDING, &previousBinding);
    const bool captured = glGetError() == GL_NO_ERROR;
    glActiveTexture(static_cast<GLenum>(previousActive));
    if (!captured || glGetError() != GL_NO_ERROR) return false;

    GLuint next = 0;
    glGenSamplers(1, &next);
    if (!next || glGetError() != GL_NO_ERROR) return false;
    glSamplerParameteri(next, GL_TEXTURE_MIN_FILTER, static_cast<GLint>(minFilter));
    glSamplerParameteri(next, GL_TEXTURE_MAG_FILTER, static_cast<GLint>(magFilter));
    glSamplerParameteri(next, GL_TEXTURE_WRAP_S, static_cast<GLint>(wrapS));
    glSamplerParameteri(next, GL_TEXTURE_WRAP_T, static_cast<GLint>(wrapT));
    glSamplerParameteri(next, GL_TEXTURE_WRAP_R, static_cast<GLint>(wrapR));
    if (aniso > 1) glSamplerParameterf(next, kTextureMaxAnisotropy, static_cast<GLfloat>(aniso));
    if (glGetError() == GL_NO_ERROR) {
        glBindSampler(unit, next);
        if (glGetError() == GL_NO_ERROR) {
            const EGLContext context = eglGetCurrentContext();
            Slot &slot = slots[unit];
            if (slot.object && slot.context == context && slot.object != next)
                glDeleteSamplers(1, &slot.object);
            slot = {context, next};
            // D3D9 retains the previous anisotropy field when new value <= 1.
            *appliedState = aniso <= 1
                ? ((state & ~255u) | (oldState & 255u)) : state;
            return true;
        }
    }
    // An unsuccessful mutation must not corrupt subsequent original draws.
    glBindSampler(unit, static_cast<GLuint>(previousBinding));
    (void)glGetError();
    glDeleteSamplers(1, &next);
    (void)glGetError();
    return false;
}

void R_AndroidGlesReleaseSamplerStates()
{
    if (!Ready()) return;
    const EGLContext context = eglGetCurrentContext();
    for (Slot &slot : slots) {
        if (slot.object && slot.context == context) {
            glDeleteSamplers(1, &slot.object);
            slot = {};
        }
    }
    (void)glGetError();
}
#endif
