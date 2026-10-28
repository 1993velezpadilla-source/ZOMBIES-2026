#include "com_files.h"

// Shared engine file-system state. These were zero-initialized globals in the
// original com_files.cpp; keeping one definition lets the authentic engine and
// the Android-extracted original functions operate on the same search path and
// IWD bookkeeping rather than parallel diagnostic copies.
int fs_iwdFileCount = 0;
int fs_checksumFeed = 0;
int bLanguagesListed = 0;
int com_fileAccessed = 0;
int fs_loadStack = 0;
char fs_gamedir[256] = {};
searchpath_s *fs_searchpaths = nullptr;
