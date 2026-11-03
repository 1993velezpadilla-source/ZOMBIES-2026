#if defined(__ANDROID__)
#include "r_android_gl_program.h"
#include <vector>
#include <limits>
namespace {
GLuint Compile(GLenum stage, const std::string &source, std::string *error) {
    if (source.empty()) { if (error) *error = "empty shader source"; return 0; }
    // glShaderSource consumes a GLsizei count. Reject oversized source before
    // narrowing size_t to GLint, otherwise a wrapped negative length can
    // cause an out-of-bounds driver read or silent truncation.
    if (source.size() > static_cast<size_t>(std::numeric_limits<GLint>::max())) {
        if (error) *error = "shader source exceeds GLsizei length";
        return 0;
    }
    GLuint shader = glCreateShader(stage);
    if (!shader) { if (error) *error = "glCreateShader failed"; return 0; }
    const GLchar *text = source.c_str();
    GLint length = static_cast<GLint>(source.size());
    glShaderSource(shader, 1, &text, &length);
    glCompileShader(shader);
    GLint ok = GL_FALSE;
    glGetShaderiv(shader, GL_COMPILE_STATUS, &ok);
    if (ok != GL_TRUE) {
        GLint n = 0; glGetShaderiv(shader, GL_INFO_LOG_LENGTH, &n);
        if (error) {
            std::vector<GLchar> log(n > 1 ? n : 1, 0);
            GLsizei written = 0;
            glGetShaderInfoLog(shader, static_cast<GLsizei>(log.size()), &written, log.data());
            *error = std::string(log.data(), written > 0 ? static_cast<size_t>(written) : 0);
        }
        glDeleteShader(shader);
        return 0;
    }
    return shader;
}
}
bool R_AndroidLinkTranslatedIW3Program(const std::string &vertexGLSL,
                                       const std::string &pixelGLSL,
                                       IW3AndroidGLProgram *out,
                                       std::string *error) {
    if (!out) return false;
    *out = {};
    if (error) error->clear();
    // Shader creation requires a current GLES3 context. A successful host
    // syntax audit cannot establish that Android has created one.
    const GLubyte *version = glGetString(GL_VERSION);
    if (!version) {
        if (error) *error = "no current OpenGL ES context";
        return false;
    }
    GLint major = 0;
    glGetIntegerv(GL_MAJOR_VERSION, &major);
    if (major < 3) {
        if (error) *error = "OpenGL ES 3.0 or newer is required";
        return false;
    }
    const GLuint vs = Compile(GL_VERTEX_SHADER, vertexGLSL, error);
    if (!vs) return false;
    const GLuint ps = Compile(GL_FRAGMENT_SHADER, pixelGLSL, error);
    if (!ps) { glDeleteShader(vs); return false; }
    GLuint program = glCreateProgram();
    if (!program) {
        if (error) *error = "glCreateProgram failed";
        glDeleteShader(vs); glDeleteShader(ps); return false;
    }
    glAttachShader(program, vs); glAttachShader(program, ps);
    glLinkProgram(program);
    GLint linked = GL_FALSE;
    glGetProgramiv(program, GL_LINK_STATUS, &linked);
    glDetachShader(program, vs); glDetachShader(program, ps);
    glDeleteShader(vs); glDeleteShader(ps);
    if (linked != GL_TRUE) {
        GLint n = 0; glGetProgramiv(program, GL_INFO_LOG_LENGTH, &n);
        if (error) {
            std::vector<GLchar> log(n > 1 ? n : 1, 0);
            GLsizei written = 0;
            glGetProgramInfoLog(program, static_cast<GLsizei>(log.size()), &written, log.data());
            *error = std::string(log.data(), written > 0 ? static_cast<size_t>(written) : 0);
        }
        glDeleteProgram(program);
        return false;
    }
    const GLint position = glGetAttribLocation(program, "iw3_position_in0");
    const GLint color = glGetAttribLocation(program, "iw3_vertex_color_in0");
    if (position != 0 || color != 1) {
        if (error) *error = "original POSITION0/COLOR0 attributes do not match expected GLES locations";
        glDeleteProgram(program);
        return false;
    }
    out->handle = program;
    out->positionAttribute = position;
    out->colorAttribute = color;
    return true;
}
void R_AndroidDeleteTranslatedIW3Program(IW3AndroidGLProgram *program) {
    if (!program) return;
    if (program->handle) glDeleteProgram(program->handle);
    *program = {};
}
#endif
