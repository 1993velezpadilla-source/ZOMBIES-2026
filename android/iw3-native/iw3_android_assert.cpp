#include <cstdarg>
#include <cstdio>
#include <cstdlib>

#if defined(__ANDROID__)
#include <android/log.h>
#endif

// Android replacement for the Win32-only assert dispatch in assertive.cpp.
// This is deliberately fatal: a broken engine invariant must not continue
// with corrupted client, database, or gameplay state.
void MyAssertHandler(const char *filename, int line, int type, const char *fmt, ...)
{
    char message[1024]{};
    va_list args;
    va_start(args, fmt);
    std::vsnprintf(message, sizeof(message), fmt ? fmt : "", args);
    va_end(args);

#if defined(__ANDROID__)
    __android_log_print(
        ANDROID_LOG_FATAL,
        "KisakCOD",
        "ASSERTION FAIL AT %s:%d (TYPE: %d): %s",
        filename ? filename : "(unknown)",
        line,
        type,
        message);
#else
    std::fprintf(
        stderr,
        "ASSERTION FAIL AT %s:%d (TYPE: %d): %s\n",
        filename ? filename : "(unknown)",
        line,
        type,
        message);
    std::fflush(stderr);
#endif

    std::abort();
}
