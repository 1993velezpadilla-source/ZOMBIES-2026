#pragma once
// Narrow declarations for authentic FS_CompareIwds/FS_CompareFFs source slices.
// The full qcommon/files.cpp includes renderer/database headers that are not
// part of this ABI audit; no function bodies are replaced here.
#include <cstdint>
#include <universal/q_shared.h>
#include <universal/com_files.h>
#include <qcommon/files.h>
#include <qcommon/qcommon.h>

#ifndef __cdecl
#define __cdecl
#endif

extern int fs_numServerReferencedIwds;
extern const char *fs_serverReferencedIwdNames[1024];
extern int fs_serverReferencedIwds[1024];
extern int fs_serverReferencedFFCheckSums[32];

// Providers are intentionally unresolved in the audit archive. The signatures
// match the original engine declarations; this header does not implement them.
int __cdecl FS_serverPak(const char *pak);
int32_t __cdecl DB_FileSize(const char *zoneName, int32_t isMod);
