#include "db_fastfile_posix_io.h"

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
#include <unistd.h>

static int checks = 0;

static void Check(bool condition, const char *label)
{
    ++checks;
    if (!condition)
    {
        std::fprintf(stderr, "FAIL: %s\n", label);
        std::exit(1);
    }
}

static bool WriteAll(int fd, const unsigned char *data, size_t size)
{
    size_t done = 0;
    while (done < size)
    {
        const ssize_t n = write(fd, data + done, size - done);
        if (n > 0)
        {
            done += static_cast<size_t>(n);
            continue;
        }
        if (n < 0 && errno == EINTR)
            continue;
        return false;
    }
    return true;
}

int main()
{
    char path[] = "/tmp/iw3-fastfile-posix-XXXXXX";
    const int fd = mkstemp(path);
    Check(fd >= 0, "mkstemp creates a real file");
    if (fd < 0)
        return 1;
    unlink(path);

    constexpr size_t chunk = 0x40000;
    constexpr size_t tail = 37;
    std::vector<unsigned char> source(chunk + tail);
    for (size_t i = 0; i < source.size(); ++i)
        source[i] = static_cast<unsigned char>((i * 17u + 3u) % 251u);
    Check(WriteAll(fd, source.data(), source.size()), "write complete fixture");

    std::vector<unsigned char> output(chunk);
    size_t bytesRead = 0;
    int errorNumber = 0;
    Check(DBFastFilePosixReadAt(fd, output.data(), output.size(), 0, &bytesRead, &errorNumber) == 0
            && errorNumber == 0 && bytesRead == chunk,
        "first 256 KiB chunk is filled");
    Check(std::memcmp(output.data(), source.data(), chunk) == 0,
        "first chunk bytes match original file");

    bytesRead = 0;
    errorNumber = 0;
    Check(DBFastFilePosixReadAt(fd, output.data(), output.size(), chunk, &bytesRead, &errorNumber) == 0
            && errorNumber == 0 && bytesRead == tail,
        "final short chunk reports exact byte count");
    Check(std::memcmp(output.data(), source.data() + chunk, tail) == 0,
        "final short chunk bytes match original file");

    bytesRead = 123;
    errorNumber = 123;
    Check(DBFastFilePosixReadAt(fd, output.data(), 16, chunk + tail, &bytesRead, &errorNumber) == 0
            && errorNumber == 0 && bytesRead == 0,
        "EOF is successful zero-byte read");

    bytesRead = 123;
    errorNumber = 0;
    Check(DBFastFilePosixReadAt(fd, output.data(), 1, UINT64_MAX, &bytesRead, &errorNumber) == -1
            && bytesRead == 0 && errorNumber == EOVERFLOW,
        "offset overflow fails closed");

    bytesRead = 123;
    errorNumber = 0;
    Check(DBFastFilePosixReadAt(-1, output.data(), 1, 0, &bytesRead, &errorNumber) == -1
            && bytesRead == 0 && errorNumber == EINVAL,
        "negative descriptor is rejected");

    bytesRead = 123;
    errorNumber = 0;
    Check(DBFastFilePosixReadAt(fd, nullptr, 0, 0, &bytesRead, &errorNumber) == 0
            && bytesRead == 0 && errorNumber == 0,
        "zero-capacity read permits null destination");

    Check(DBFastFilePosixFdFromOpaque(DBFastFilePosixOpaqueFromFd(0)) == 0,
        "opaque encoding preserves descriptor zero");
    Check(DBFastFilePosixFdFromOpaque(DBFastFilePosixOpaqueFromFd(fd)) == fd,
        "opaque encoding preserves ordinary descriptor");
    Check(DBFastFilePosixFdFromOpaque(nullptr) == -1,
        "null opaque handle is rejected");

    errno = 0;
    bytesRead = 0;
    errorNumber = 0;
    Check(DBFastFilePosixReadAt(999999, output.data(), 1, 0, &bytesRead, &errorNumber) == -1
            && errorNumber == EBADF,
        "invalid live descriptor reports EBADF");

    close(fd);
    std::printf("IW3_FASTFILE_POSIX_IO_TESTS_PASS checks=%d\n", checks);
    return checks == 11 ? 0 : 2;
}
