#if defined(__ANDROID__)
#include "r_android_gl_program.h"
#include <vector>
#include <algorithm>
#include <cstring>
#include <limits>
#include <cstddef>
namespace {
// Driver-provided log lengths are untrusted; bound diagnostic allocation.
constexpr GLint kMaxGLLogBytes = 64 * 1024;
GLsizei SafeLogCapacity(GLint reported) {
    return static_cast<GLsizei>(std::max<GLint>(1, std::min(reported, kMaxGLLogBytes)));
}
bool ValidateSource(const std::string &source, std::string *error) {
    if (source.empty()) { if (error) *error = "empty shader source"; return 0; }
    // glShaderSource consumes a GLsizei count. Reject oversized source before
    // narrowing size_t to GLint, otherwise a wrapped negative length can
    // cause an out-of-bounds driver read or silent truncation.
    if (source.size() > static_cast<size_t>(std::numeric_limits<GLint>::max())) {
        if (error) *error = "shader source exceeds GLsizei length";
        return 0;
    }
    // A translated GLSL shader must be text, not a binary blob.
    // Reject embedded NULs instead of letting the driver compile ambiguous input.
    if (source.find('\0') != std::string::npos) {
        if (error) *error = "shader source contains embedded NUL";
        return 0;
    }
    return true;
}
GLuint Compile(GLenum stage, const std::string &source, std::string *error) {
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
            std::vector<GLchar> log(static_cast<size_t>(SafeLogCapacity(n)), 0);
            GLsizei written = 0;
            glGetShaderInfoLog(shader, static_cast<GLsizei>(log.size()), &written, log.data());
            *error = std::string(log.data(), written > 0 ? std::min(static_cast<size_t>(written), log.size() - 1) : 0);
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
    if (error) error->clear();
    // Do not orphan a previously linked GL program on repeated calls.
    if (out->handle) {
        if (error) *error = "output already owns a GL program; delete it before relinking";
        return false;
    }
    *out = {};
    // Shader creation requires a current GLES3 context. A successful host
    // syntax audit cannot establish that Android has created one.
    const GLubyte *version = glGetString(GL_VERSION);
    if (!version) {
        if (error) *error = "no current OpenGL ES context";
        return false;
    }
    // Desktop GL contexts may also expose GL_MAJOR_VERSION >= 3, but are
    // not an Android GLES3 rendering context.
    if (std::strncmp(reinterpret_cast<const char *>(version), "OpenGL ES ", 10) != 0) {
        if (error) *error = "OpenGL ES context required (desktop GL rejected)";
        return false;
    }
    GLint major = 0;
    glGetIntegerv(GL_MAJOR_VERSION, &major);
    if (major < 3) {
        if (error) *error = "OpenGL ES 3.0 or newer is required";
        return false;
    }
    // Validate both stages before creating any GPU objects. In particular, an
    // invalid fragment source must not trigger vertex shader compilation.
    if (!ValidateSource(vertexGLSL, error) || !ValidateSource(pixelGLSL, error))
        return false;
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
    // D3D9 POSITION0/COLOR0 have fixed input slots in the original IW3
    // vertex declaration. GLSL ES shaders without layout qualifiers would
    // otherwise receive driver-assigned locations and fail validation below.
    // Bind the semantic slots before linking (never after glLinkProgram).
    glBindAttribLocation(program, 0, "iw3_position_in0");
    glBindAttribLocation(program, 1, "iw3_vertex_color_in0");
    glLinkProgram(program);
    GLint linked = GL_FALSE;
    glGetProgramiv(program, GL_LINK_STATUS, &linked);
    glDetachShader(program, vs); glDetachShader(program, ps);
    glDeleteShader(vs); glDeleteShader(ps);
    if (linked != GL_TRUE) {
        GLint n = 0; glGetProgramiv(program, GL_INFO_LOG_LENGTH, &n);
        if (error) {
            std::vector<GLchar> log(static_cast<size_t>(SafeLogCapacity(n)), 0);
            GLsizei written = 0;
            glGetProgramInfoLog(program, static_cast<GLsizei>(log.size()), &written, log.data());
            *error = std::string(log.data(), written > 0 ? std::min(static_cast<size_t>(written), log.size() - 1) : 0);
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
