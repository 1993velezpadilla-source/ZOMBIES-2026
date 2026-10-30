#!/usr/bin/env python3
"""Extract exact DB_ReadData/DB_WaitXFileStage bodies for Android-branch tests.

The generated translation unit is a host/NDK test harness, not an engine runtime.
It compiles the original function bodies with __ANDROID__ defined and exercises
their real POSIX read path against a temporary file.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


def extract_function(source: str, pattern: str, label: str) -> str:
    match = re.search(pattern, source)
    if not match:
        raise SystemExit(f"missing original {label} function")
    start = match.start()
    open_brace = source.find("{", match.start(), match.end() + 1)
    if open_brace < 0:
        raise SystemExit(f"missing opening brace for {label}")

    depth = 0
    i = open_brace
    state = "normal"
    escaped = False
    while i < len(source):
        ch = source[i]
        nxt = source[i + 1] if i + 1 < len(source) else ""
        if state == "line_comment":
            if ch == "\n":
                state = "normal"
        elif state == "block_comment":
            if ch == "*" and nxt == "/":
                state = "normal"
                i += 1
        elif state in ("string", "char"):
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif (state == "string" and ch == '"') or (state == "char" and ch == "'"):
                state = "normal"
        else:
            if ch == "/" and nxt == "/":
                state = "line_comment"
                i += 1
            elif ch == "/" and nxt == "*":
                state = "block_comment"
                i += 1
            elif ch == '"':
                state = "string"
            elif ch == "'":
                state = "char"
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return source[start:i + 1]
        i += 1
    raise SystemExit(f"unterminated original {label} function")


HARNESS_PREFIX = r"""#define __ANDROID__ 1
#define __cdecl
#include <cerrno>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
#include <unistd.h>
#include "db_fastfile_posix_io.h"

struct DBFastFileTestStream { uint32_t avail_in = 0; };
struct DB_LoadData {
    void *f = nullptr;
    const char *filename = "fastfile-fixture";
    int32_t outstandingReads = 0;
    uint64_t posixOffset = 0;
    size_t posixBytesRead = 0;
    int posixReadError = 0;
    bool posixEof = false;
    uint8_t *compressBufferStart = nullptr;
    uint8_t *compressBufferEnd = nullptr;
    void (*interrupt)() = nullptr;
    DBFastFileTestStream stream;
};
static DB_LoadData g_load;
static volatile int32_t g_loadedSize = 0;
static void MyAssertHandler(const char *, int, int, const char *, ...) { std::abort(); }

static int g_checks = 0;
static void Check(bool condition, const char *label)
{
    ++g_checks;
    if (!condition) {
        std::fprintf(stderr, "FAIL: %s\n", label);
        std::exit(1);
    }
}

static bool WriteAll(int fd, const unsigned char *data, size_t size)
{
    size_t done = 0;
    while (done < size) {
        const ssize_t n = write(fd, data + done, size - done);
        if (n > 0) { done += static_cast<size_t>(n); continue; }
        if (n < 0 && errno == EINTR) continue;
        return false;
    }
    return true;
}
"""

HARNESS_SUFFIX = r"""
int main()
{
    char path[] = "/tmp/iw3-original-db-read-XXXXXX";
    const int fd = mkstemp(path);
    Check(fd >= 0, "create real FastFile input fixture");
    if (fd < 0) return 1;
    unlink(path);

    constexpr size_t chunk = 0x40000;
    constexpr size_t tail = 37;
    std::vector<unsigned char> input(chunk + tail);
    for (size_t i = 0; i < input.size(); ++i)
        input[i] = static_cast<unsigned char>((i * 29u + 11u) % 253u);
    Check(WriteAll(fd, input.data(), input.size()), "write FastFile fixture");

    std::vector<uint8_t> ring(0x80000);
    g_load.f = DBFastFilePosixOpaqueFromFd(fd);
    g_load.compressBufferStart = ring.data();
    g_load.compressBufferEnd = ring.data() + ring.size();

    Check(DB_ReadData() == 1, "original DB_ReadData accepts first POSIX chunk");
    Check(g_load.outstandingReads == 1 && g_load.posixBytesRead == chunk
          && g_load.posixOffset == chunk, "first chunk state matches original ring contract");
    Check(std::memcmp(ring.data(), input.data(), chunk) == 0, "first ring slot contains source bytes");
    Check(DB_WaitXFileStage() == 1 && g_load.outstandingReads == 0
          && g_load.stream.avail_in == chunk && g_load.posixBytesRead == 0,
          "original wait stage publishes exact first chunk length");

    Check(DB_ReadData() == 1, "original DB_ReadData accepts final short chunk");
    Check(g_load.outstandingReads == 1 && g_load.posixBytesRead == tail
          && g_load.posixOffset == 2 * chunk && g_load.posixEof,
          "short final chunk advances one ring slot and publishes physical EOF");
    Check(std::memcmp(ring.data() + chunk, input.data() + chunk, tail) == 0,
          "second ring slot contains final bytes");
    Check(DB_WaitXFileStage() == 2 && g_load.stream.avail_in == chunk + tail,
          "original wait stage adds short read byte count, not a full chunk");

    Check(DB_ReadData() == 0 && g_load.posixEof && g_load.posixReadError == 0,
          "original DB_ReadData distinguishes EOF from I/O failure");

    g_load.f = DBFastFilePosixOpaqueFromFd(999999);
    g_load.posixEof = false;
    g_load.posixReadError = 0;
    Check(DB_ReadData() == 0 && g_load.posixReadError == EBADF,
          "original DB_ReadData preserves real descriptor errors");

    close(fd);
    std::printf("IW3_ORIGINAL_DB_READ_POSIX_BODY_PASS checks=%d\n", g_checks);
    return g_checks == 12 ? 0 : 2;
}
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    source_path = args.engine / "src/database/db_file_load.cpp"
    source = source_path.read_text()
    wait_body = extract_function(
        source, r"\bint32_t\s+DB_WaitXFileStage\s*\(\s*\)\s*\{",
        "DB_WaitXFileStage")
    read_body = extract_function(
        source, r"\bint32_t\s+__cdecl\s+DB_ReadData\s*\(\s*\)\s*\{",
        "DB_ReadData")

    for token in ("DBFastFilePosixReadAt", "posixBytesRead", "posixReadError", "posixEof"):
        if token not in read_body:
            raise SystemExit(f"original DB_ReadData Android branch lost {token}")
    if "g_load.posixBytesRead" not in wait_body or "__atomic_add_fetch" not in wait_body:
        raise SystemExit("original DB_WaitXFileStage Android byte-count path missing")
    if "g_load.posixEof = bytesRead < 0x40000u;" not in read_body:
        raise SystemExit("original DB_ReadData must publish EOF on a final short chunk")
    if "ReadFileEx" not in read_body:
        raise SystemExit("Windows ReadFileEx path must remain in original function")

    generated = HARNESS_PREFIX + "\n" + wait_body + "\n\n" + read_body + "\n" + HARNESS_SUFFIX
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(generated)
    report = {
        "source": str(source_path),
        "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
        "DB_WaitXFileStage_sha256": hashlib.sha256(wait_body.encode()).hexdigest(),
        "DB_ReadData_sha256": hashlib.sha256(read_body.encode()).hexdigest(),
        "functions_copied_from_original_source": True,
        "android_branch_compiled_by_harness": True,
        "windows_ReadFileEx_branch_preserved_in_source": True,
        "harness_is_game_runtime": False,
        "fastfile_loaded": False,
        "map_loaded": False,
        "gameplay_proven": False,
        "playable_apk": False,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print("IW3_ORIGINAL_DB_READ_POSIX_HARNESS_GENERATED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
