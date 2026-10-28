#include <universal/q_shared.h>

#include <cstdarg>
#include <cstdio>
#include <cstring>

#if defined(__ANDROID__)
#include <android/log.h>
#endif

// Android platform sink for the original dvar registry's Com_Printf dependency.
// This is deliberately scoped to the dvar dependency archive, not a replacement
// for the engine's full Com_PrintMessage/console/log-file subsystem.
#if !defined(IW3_ORIGINAL_COM_PRINT_PRINTF_LINK_AUDIT)
void QDECL Com_Printf(int channel, const char *fmt, ...)
{
    if (!fmt)
        return;

    char message[4096]{};
    va_list args;
    va_start(args, fmt);
    const int formatted = std::vsnprintf(message, sizeof(message), fmt, args);
    va_end(args);
    if (formatted < 0)
        return;
    message[sizeof(message) - 1] = '\0';

    char line[4160]{};
    const int prefix = std::snprintf(line, sizeof(line), "[channel %d] ", channel);
    if (prefix < 0 || static_cast<std::size_t>(prefix) >= sizeof(line))
        return;

    const std::size_t prefix_length = static_cast<std::size_t>(prefix);
    std::size_t message_length = 0;
    while (message_length < sizeof(message) && message[message_length] != '\0')
        ++message_length;

    const std::size_t available = sizeof(line) - prefix_length - 1;
    const std::size_t copy_length = message_length < available ? message_length : available;
    std::memcpy(line + prefix_length, message, copy_length);
    line[prefix_length + copy_length] = '\0';

#if defined(__ANDROID__)
    (void)__android_log_write(ANDROID_LOG_INFO, "IW3-Dvar", line);
#else
    // Host-only test path; Android builds always use logcat.
    (void)std::fwrite(line, 1, prefix_length + copy_length, stderr);
    (void)std::fflush(stderr);
#endif
}
#endif // !IW3_ORIGINAL_COM_PRINT_PRINTF_LINK_AUDIT
