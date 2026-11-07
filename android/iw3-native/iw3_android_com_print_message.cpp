#include "iw3_android_fs_startup_compat.h"

#include <cstdio>

#if defined(__ANDROID__)
#include <android/log.h>
#endif

// Platform sink for the authentic Com_PrintWarning body. It preserves the
// engine channel and severity and never simulates game or console state.
void __cdecl Com_PrintMessage(int channel, const char *msg, int error)
{
    if (!msg)
        return;

#if defined(__ANDROID__)
    const int priority = error >= 3 ? ANDROID_LOG_ERROR
                      : error == 2 ? ANDROID_LOG_WARN
                                   : ANDROID_LOG_INFO;
    char tag[32];
    std::snprintf(tag, sizeof(tag), "KisakCOD-%d", channel);
    __android_log_write(priority, tag, msg);
#else
    std::fprintf(stderr, "[KisakCOD channel=%d type=%d] %s", channel, error, msg);
#endif
}
