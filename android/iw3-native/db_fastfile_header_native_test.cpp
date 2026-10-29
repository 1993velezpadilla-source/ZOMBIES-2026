#include "db_fastfile_header.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int g_checks = 0;

static void check(bool condition, const char *message)
{
    ++g_checks;
    if (!condition)
    {
        fprintf(stderr, "FAIL: %s\n", message);
        exit(1);
    }
}

static void make_header(uint8_t *out, const char *magic, uint32_t version)
{
    memcpy(out, magic, 8);
    out[8] = (uint8_t)(version & 0xff);
    out[9] = (uint8_t)((version >> 8) & 0xff);
    out[10] = (uint8_t)((version >> 16) & 0xff);
    out[11] = (uint8_t)((version >> 24) & 0xff);
}

int main()
{
    uint8_t unaligned[13] = {};
    DBFastFileHeader parsed = {};

    // Deliberately offset the input by one byte to catch the old unaligned
    // uint32_t dereferences on the original zlib buffer.
    make_header(unaligned + 1, "IWffu100", 5);
    check(DB_ParseFastFileHeader(unaligned + 1, 12, &parsed)
              == DBFastFileHeaderStatus::Ok,
          "unaligned valid unsecure header");
    check(parsed.version == 5 && !parsed.secure && parsed.consumed == 12,
          "version/secure/consumed for unsecure header");
    check(memcmp(parsed.magic, "IWffu100", 8) == 0,
          "magic copied exactly");

    make_header(unaligned + 1, "IWff0100", 5);
    check(DB_ParseFastFileHeader(unaligned + 1, 12, &parsed)
              == DBFastFileHeaderStatus::Ok,
          "secure magic is parsed by original loader contract");
    check(parsed.secure && parsed.consumed == 12,
          "secure variant remains marked for the original rejection path");

    make_header(unaligned + 1, "BADMAGIC", 5);
    check(DB_ParseFastFileHeader(unaligned + 1, 12, &parsed)
              == DBFastFileHeaderStatus::InvalidMagic && parsed.consumed == 8,
          "invalid magic consumes only eight bytes");

    make_header(unaligned + 1, "IWffu100", 5);
    check(DB_ParseFastFileHeader(unaligned + 1, 7, &parsed)
              == DBFastFileHeaderStatus::TruncatedMagic && parsed.consumed == 0,
          "truncated magic is bounded");
    check(DB_ParseFastFileHeader(unaligned + 1, 11, &parsed)
              == DBFastFileHeaderStatus::TruncatedVersion && parsed.consumed == 8,
          "truncated version preserves original eight-byte boundary");

    make_header(unaligned + 1, "IWffu100", 4);
    check(DB_ParseFastFileHeader(unaligned + 1, 12, &parsed)
              == DBFastFileHeaderStatus::UnsupportedVersion && parsed.version == 4,
          "older version is reported exactly");
    make_header(unaligned + 1, "IWffu100", 6);
    check(DB_ParseFastFileHeader(unaligned + 1, 12, &parsed)
              == DBFastFileHeaderStatus::UnsupportedVersion && parsed.version == 6,
          "newer version is reported exactly");

    check(DB_ParseFastFileHeader(NULL, 12, &parsed)
              == DBFastFileHeaderStatus::InvalidArgument,
          "null input is rejected");
    check(DB_ParseFastFileHeader(unaligned + 1, 12, NULL)
              == DBFastFileHeaderStatus::InvalidArgument,
          "null output is rejected");

    printf("IW3_FASTFILE_HEADER_PORTABILITY_PASS checks=%d\n", g_checks);
    return 0;
}
