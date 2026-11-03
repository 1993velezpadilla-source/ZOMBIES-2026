// Host-only real EGL/GLES3 smoke probe for the original IW3 shader provider.
// This does not run the IW3 renderer, map loader, or Android gameplay.
#include "r_android_gl_program.h"
#include <EGL/egl.h>
#include <EGL/eglext.h>
#include <GLES3/gl3.h>
#include <cstdio>
#include <string>
int main() {
    auto getPlatform = reinterpret_cast<PFNEGLGETPLATFORMDISPLAYEXTPROC>(
        eglGetProcAddress("eglGetPlatformDisplayEXT"));
    if (!getPlatform) return 10;
    EGLDisplay display = getPlatform(EGL_PLATFORM_SURFACELESS_MESA, EGL_DEFAULT_DISPLAY, nullptr);
    if (display == EGL_NO_DISPLAY || !eglInitialize(display, nullptr, nullptr)) return 11;
    if (!eglBindAPI(EGL_OPENGL_ES_API)) return 12;
    const EGLint attrs[] = { EGL_SURFACE_TYPE, EGL_PBUFFER_BIT,
        EGL_RENDERABLE_TYPE, EGL_OPENGL_ES3_BIT, EGL_NONE };
    EGLConfig config = nullptr;
    EGLint count = 0;
    if (!eglChooseConfig(display, attrs, &config, 1, &count) || count != 1) return 13;
    const EGLint pb[] = { EGL_WIDTH, 8, EGL_HEIGHT, 8, EGL_NONE };
    EGLSurface surface = eglCreatePbufferSurface(display, config, pb);
    if (surface == EGL_NO_SURFACE) return 14;
    const EGLint ctxAttrs[] = { EGL_CONTEXT_CLIENT_VERSION, 3, EGL_NONE };
    EGLContext context = eglCreateContext(display, config, EGL_NO_CONTEXT, ctxAttrs);
    if (context == EGL_NO_CONTEXT || !eglMakeCurrent(display, surface, surface, context)) return 15;
    const std::string vs = "#version 300 es\n"
        "in vec3 iw3_position_in0; in vec4 iw3_vertex_color_in0;\n"
        "out vec4 vColor; void main(){vColor=iw3_vertex_color_in0;"
        "gl_Position=vec4(iw3_position_in0,1.0);}\n";
    const std::string fs = "#version 300 es\n"
        "precision mediump float; in vec4 vColor; out vec4 fragColor;\n"
        "void main(){fragColor=vColor;}\n";
    IW3AndroidGLProgram program{};
    std::string error;
    bool ok = R_AndroidLinkTranslatedIW3Program(vs, fs, &program, &error);
    if (!ok || !program.handle || program.positionAttribute != 0 || program.colorAttribute != 1) {
        std::fprintf(stderr, "GLES3 program failure: %s\n", error.c_str());
        return 16;
    }
    R_AndroidDeleteTranslatedIW3Program(&program);
    if (program.handle) return 17;
    eglMakeCurrent(display, EGL_NO_SURFACE, EGL_NO_SURFACE, EGL_NO_CONTEXT);
    eglDestroyContext(display, context);
    eglDestroySurface(display, surface);
    eglTerminate(display);
    std::puts("IW3_GLES3_REAL_EGL_HOST_PROGRAM_LINK_PASS_NOT_GAME");
    return 0;
}
