#include <cstddef>
#include <script/scr_parser.h>

static_assert(sizeof(void *) == 8, "This gate must compile for Android ARM64");
static_assert(sizeof(OpcodeLookup) == 0x20);
static_assert(sizeof(SourceBufferInfo) == 56);
static_assert(sizeof(SaveSourceBufferInfo) == 0x10);
static_assert(sizeof(scrParserGlob_t) == 0x50);
static_assert(sizeof(scrParserPub_t) == 0x20);
static_assert(offsetof(scrParserGlob_t, currentCodePos) == 40);
static_assert(offsetof(scrParserGlob_t, saveSourceBufferLookup) == 56);
static_assert(offsetof(scrParserPub_t, scriptfilename) == 16);
static_assert(offsetof(scrParserPub_t, sourceBuf) == 24);

extern "C" int iw3_script_parser_layout_abi_anchor()
{
    return static_cast<int>(sizeof(scrParserGlob_t) + sizeof(scrParserPub_t));
}
