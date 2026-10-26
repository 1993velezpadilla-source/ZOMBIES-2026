#pragma once
// Native platform services required by the authentic KisakCOD filesystem startup.
// The original FS_RegisterDvars/FS_Startup bodies remain upstream source.
#include "iw3_android_platform.h"

#ifndef __cdecl
#define __cdecl
#endif

// These names match the original platform declarations consumed by
// com_files.cpp. Sys_Cwd uses Android's configured app-private data root.
char *Sys_Cwd();
char *Sys_DefaultCDPath();

extern "C" IW3_ANDROID_EXPORT int z2026_iw3_fs_startup_path_smoke();
