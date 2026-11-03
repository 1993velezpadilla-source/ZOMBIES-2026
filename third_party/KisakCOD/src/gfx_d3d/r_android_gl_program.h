#pragma once
// GLES3 GPU program for the narrowly translated *original* IW3 D3D9 shader pair.
// A GL context must be current. This does not bind IW3 materials or draw maps.
#if defined(__ANDROID__)
#include <GLES3/gl3.h>
#include <string>
struct IW3AndroidGLProgram {
    GLuint handle = 0;
    GLint positionAttribute = -1;
    GLint colorAttribute = -1;
};
bool R_AndroidLinkTranslatedIW3Program(const std::string &vertexGLSL,
                                       const std::string &pixelGLSL,
                                       IW3AndroidGLProgram *out,
                                       std::string *error);
void R_AndroidDeleteTranslatedIW3Program(IW3AndroidGLProgram *program);
#endif
