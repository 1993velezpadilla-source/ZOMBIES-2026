#pragma once

// Android platform boundary for the original KisakCOD four-slot thread value
// contract. This is not an engine bootstrap or a replacement Com_Init.
#include <qcommon/thread_context.h>

bool IW3_AndroidBindThreadContext(ThreadContext_t context);
void IW3_AndroidUnbindThreadContext();
bool IW3_AndroidThreadHasErrorJump();
// Calls the original q_shared.cpp Com_InitThreadData for the MAIN context.
// Only slots 1-3 are prepared; this is not a full Sys_InitMainThread.
bool IW3_AndroidBindMainThreadSharedData();
