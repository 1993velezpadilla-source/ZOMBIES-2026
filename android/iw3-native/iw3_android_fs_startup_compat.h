#pragma once
// Native platform services required by the authentic KisakCOD filesystem startup.
// The original FS_RegisterDvars/FS_Startup bodies remain upstream source.
#include "iw3_android_platform.h"
#include "universal/com_files.h"
#include "qcommon/qcommon.h"
#include "stringed/stringed_hooks.h"

#ifndef __cdecl
#define __cdecl
#endif

#ifndef BOOL
typedef int BOOL;
#endif

// Globals shared with the original com_files.cpp translation unit.
extern const dvar_t *fs_homepath;
extern const dvar_s *fs_debug;
extern const dvar_s *fs_restrict;
extern const dvar_s *fs_ignoreLocalized;
extern const dvar_s *fs_basepath;
extern const dvar_s *fs_copyfiles;
extern const dvar_s *fs_cdpath;
extern const dvar_s *fs_gameDirVar;
extern const dvar_s *fs_basegame;
extern int fs_iwdFileCount;
extern int fs_checksumFeed;
extern searchpath_s *fs_searchpaths;
extern char lastValidBase[256];
extern char lastValidGame[256];

void FS_RegisterDvars();
void __cdecl Com_ReadCDKey();
bool __cdecl FS_GameDirDomainFunc(dvar_s *dvar, DvarValue newValue);
BOOL __cdecl FS_UseSearchPath(const searchpath_s *pSearch);
void FS_AddLocalizedGameDirectory(char *path, char *dir);
void FS_AddCommands();
void FS_Path_f();
void FS_Shutdown();

// These names match the original platform declarations consumed by
// com_files.cpp. Sys_Cwd uses Android's configured app-private data root.
char *Sys_Cwd();
char *Sys_DefaultCDPath();

extern "C" IW3_ANDROID_EXPORT int z2026_iw3_fs_startup_path_smoke();
