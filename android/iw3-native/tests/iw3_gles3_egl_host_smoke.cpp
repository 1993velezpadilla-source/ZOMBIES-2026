// Host-only real EGL/GLES3 smoke probe for the original IW3 shader provider.
// This does not run the IW3 renderer, map loader, or Android gameplay.
#include "r_android_gl_program.h"
#include <EGL/egl.h>
#include <EGL/eglext.h>
#include <GLES3/gl3.h>
#include <cstdio>
#include <cstddef>
#include <string>
int main() {
    // The Android bootstrap must make EGL current before asking the genuine
    // IW3 shader provider to allocate GPU resources. Verify the missing-
    // context path explicitly, not just successful host rendering.
    IW3AndroidGLProgram noContextProgram{};
    std::string noContextError;
    if (R_AndroidLinkTranslatedIW3Program(
            "#version 300 es\nvoid main(){gl_Position=vec4(0.0);}",
            "#version 300 es\nprecision mediump float; out vec4 c; void main(){c=vec4(1.0);}",
            &noContextProgram, &noContextError) ||
        noContextProgram.handle != 0 ||
        noContextError != "no current OpenGL ES context") {
        std::fprintf(stderr, "GLES3 missing-context regression: %s\\n",
                     noContextError.c_str());
        return 23;
    }
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
    // Exercise the authentic provider's failure and ownership paths on the
    // same real EGL context. A failed relink must preserve the live program.
    const GLuint originalHandle = program.handle;
    std::string rejectedError;
    if (R_AndroidLinkTranslatedIW3Program(vs, fs, &program, &rejectedError) ||
        program.handle != originalHandle || rejectedError.empty()) {
        std::fprintf(stderr, "GLES3 occupied-output regression: %s\\n", rejectedError.c_str());
        return 19;
    }
    IW3AndroidGLProgram invalidProgram{};
    rejectedError.clear();
    if (R_AndroidLinkTranslatedIW3Program(vs, "#version 300 es\ninvalid shader", 
                                          &invalidProgram, &rejectedError) ||
        invalidProgram.handle != 0 || rejectedError.empty()) {
        std::fprintf(stderr, "GLES3 invalid-fragment regression: %s\\n", rejectedError.c_str());
        return 20;
    }
    // A rejected vertex shader must leave the output empty and must not
    // poison the active GLES context or the previously linked IW3 program.
    rejectedError.clear();
    if (R_AndroidLinkTranslatedIW3Program(
            "#version 300 es\nthis is not valid GLSL", fs,
            &invalidProgram, &rejectedError) ||
        invalidProgram.handle != 0 || rejectedError.empty() ||
        !glIsProgram(originalHandle)) {
        std::fprintf(stderr, "GLES3 invalid-vertex regression: %s\\n",
                     rejectedError.c_str());
        return 24;
    }
    rejectedError.clear();
    if (R_AndroidLinkTranslatedIW3Program(vs, std::string("a\0b", 3),
                                          &invalidProgram, &rejectedError) ||
        invalidProgram.handle != 0 ||
        rejectedError != "shader source contains embedded NUL") {
        std::fprintf(stderr, "GLES3 embedded-NUL regression: %s\\n", rejectedError.c_str());
        return 21;
    }
    // A failed shader compilation must not leave stale GL error state or
    // prevent the original IW3 shader provider from linking a fresh program.
    IW3AndroidGLProgram recoveredProgram{};
    std::string recoveredError;
    if (!R_AndroidLinkTranslatedIW3Program(vs, fs, &recoveredProgram,
                                           &recoveredError) ||
        !recoveredProgram.handle ||
        recoveredProgram.handle == originalHandle ||
        !glIsProgram(recoveredProgram.handle)) {
        std::fprintf(stderr, "GLES3 post-failure recovery regression: %s\\n",
                     recoveredError.c_str());
        return 25;
    }
    R_AndroidDeleteTranslatedIW3Program(&recoveredProgram);
    if (recoveredProgram.handle != 0 || !glIsProgram(originalHandle)) {
        std::fputs("GLES3 recovery cleanup damaged original program\\n", stderr);
        return 26;
    }
    if (!glIsProgram(originalHandle) || glGetError() != GL_NO_ERROR) {
        std::fputs("GLES3 failure path damaged the live program\\n", stderr);
        return 22;
    }
    // Real GLES3 draw/readback on the host: exercises the linked provider's
    // attribute bindings, not IW3 map geometry or an Android device.
    const float vertices[] = {
        -1.f, -1.f, 0.f, 1.f, 0.f, 0.f, 1.f,
         3.f, -1.f, 0.f, 1.f, 0.f, 0.f, 1.f,
        -1.f,  3.f, 0.f, 1.f, 0.f, 0.f, 1.f
    };
    GLuint vao = 0, vbo = 0;
    glGenVertexArrays(1, &vao);
    glBindVertexArray(vao);
    glGenBuffers(1, &vbo);
    glBindBuffer(GL_ARRAY_BUFFER, vbo);
    glBufferData(GL_ARRAY_BUFFER, sizeof(vertices), vertices, GL_STATIC_DRAW);
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 7 * sizeof(float), nullptr);
    glEnableVertexAttribArray(0);
    glVertexAttribPointer(1, 4, GL_FLOAT, GL_FALSE, 7 * sizeof(float),
                          reinterpret_cast<const void*>(3 * sizeof(float)));
    glEnableVertexAttribArray(1);
    glViewport(0, 0, 8, 8);
    glClearColor(0.f, 0.f, 0.f, 1.f);
    glClear(GL_COLOR_BUFFER_BIT);
    glUseProgram(program.handle);
    glDrawArrays(GL_TRIANGLES, 0, 3);
    glFinish();
    unsigned char pixel[4] = {};
    glReadPixels(4, 4, 1, 1, GL_RGBA, GL_UNSIGNED_BYTE, pixel);
    const GLenum glError = glGetError();
    glUseProgram(0);
    glBindVertexArray(0);
    glDeleteBuffers(1, &vbo);
    glDeleteVertexArrays(1, &vao);
    if (glError != GL_NO_ERROR || pixel[0] < 240 || pixel[1] > 15 ||
        pixel[2] > 15 || pixel[3] < 240) {
        std::fprintf(stderr, "GLES3 draw/readback failed: GL=0x%x RGBA=%u,%u,%u,%u\\n",
                     static_cast<unsigned>(glError), pixel[0], pixel[1], pixel[2], pixel[3]);
        R_AndroidDeleteTranslatedIW3Program(&program);
        return 18;
    }
    // Simulate Android Surface pause: deleting without a current EGL context
    // must preserve the real GPU handle for cleanup after context recovery.
    if (!eglMakeCurrent(display, EGL_NO_SURFACE, EGL_NO_SURFACE, EGL_NO_CONTEXT))
        return 27;
    R_AndroidDeleteTranslatedIW3Program(&program);
    if (program.handle != originalHandle) {
        std::fputs("GLES3 context-loss cleanup discarded owned program\\n", stderr);
        return 28;
    }
    if (!eglMakeCurrent(display, surface, surface, context))
        return 29;
    if (!glIsProgram(originalHandle)) {
        std::fputs("GLES3 context recovery lost original program\\n", stderr);
        return 30;
    }
    R_AndroidDeleteTranslatedIW3Program(&program);
    if (program.handle || glIsProgram(originalHandle)) return 17;
    eglMakeCurrent(display, EGL_NO_SURFACE, EGL_NO_SURFACE, EGL_NO_CONTEXT);
    eglDestroyContext(display, context);
    eglDestroySurface(display, surface);
    eglTerminate(display);
    std::puts("IW3_GLES3_REAL_EGL_HOST_DRAW_READBACK_PASS_NOT_GAME");
    return 0;
}
