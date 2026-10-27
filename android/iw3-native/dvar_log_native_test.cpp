#include <cassert>
#include <cstdio>
#include <string>
#include <unistd.h>

void Com_Printf(int channel, const char *fmt, ...);

int main()
{
    FILE *capture = std::tmpfile();
    assert(capture != nullptr);
    std::fflush(stderr);
    const int saved_stderr = dup(STDERR_FILENO);
    assert(saved_stderr >= 0);
    assert(dup2(fileno(capture), STDERR_FILENO) >= 0);

    Com_Printf(7, "engine value=%d\n", 42);
    std::fflush(stderr);
    assert(dup2(saved_stderr, STDERR_FILENO) >= 0);
    close(saved_stderr);

    std::rewind(capture);
    char buffer[256]{};
    const std::size_t count = std::fread(buffer, 1, sizeof(buffer) - 1, capture);
    std::fclose(capture);
    const std::string actual(buffer, count);
    assert(actual == "[channel 7] engine value=42\n");
    std::puts("IW3_ANDROID_DVAR_COM_PRINTF_HOST_GREEN");
    return 0;
}
