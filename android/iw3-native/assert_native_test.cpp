#include <csignal>
#include <cstdio>
#include <cstring>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

void MyAssertHandler(const char *filename, int line, int type, const char *fmt, ...);

int main()
{
    int outputPipe[2]{};
    if (pipe(outputPipe) != 0)
        return 10;

    const pid_t child = fork();
    if (child < 0)
        return 11;

    if (child == 0)
    {
        close(outputPipe[0]);
        if (dup2(outputPipe[1], STDERR_FILENO) < 0)
            _exit(12);
        close(outputPipe[1]);
        MyAssertHandler("android_assert_native_test.cpp", 42, 7, "probe=%d", 17);
        _exit(13);
    }

    close(outputPipe[1]);
    char captured[2048]{};
    std::size_t used = 0;
    while (used + 1 < sizeof(captured))
    {
        const ssize_t count = read(outputPipe[0], captured + used, sizeof(captured) - used - 1);
        if (count <= 0)
            break;
        used += static_cast<std::size_t>(count);
    }
    close(outputPipe[0]);

    int status = 0;
    if (waitpid(child, &status, 0) != child)
        return 14;
    if (!WIFSIGNALED(status) || WTERMSIG(status) != SIGABRT)
        return 15;
    if (std::strstr(captured, "ASSERTION FAIL AT android_assert_native_test.cpp:42 (TYPE: 7): probe=17") == nullptr)
        return 16;

    std::puts("IW3_ANDROID_ASSERT_PROVIDER_ABORT_HOST_GREEN");
    return 0;
}
