#pragma once

// Android platform boundary for the original KisakCOD four-slot thread value
// contract. This is not an engine bootstrap or a replacement Com_Init.
#include <qcommon/thread_context.h>

bool IW3_AndroidBindThreadContext(ThreadContext_t context);
void IW3_AndroidUnbindThreadContext();
bool IW3_AndroidThreadHasErrorJump();
