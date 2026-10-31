#pragma once
// Android AArch64 compile-only declarations for the *original* client.
// The upstream gfx_d3d/r_cinematic.h pulls in Win32 Direct3D9/Bink types.
// cl_main.cpp uses only these three real external cinematic entry points.
// NO functions are implemented here: the genuine renderer/cinematic backend
// must still be ported and linked before the client can execute on Android.
#include <stdint.h>
void __cdecl R_Cinematic_StartPlayback(char *name, uint32_t playbackFlags, float volume);
bool __cdecl R_Cinematic_IsStarted();
bool R_Cinematic_IsPending();
