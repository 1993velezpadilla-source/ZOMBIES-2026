"""Execute the authentic IW3 database geometry-offset helpers under ASan/UBSan.

The zone state is an isolated test provider. Both function bodies are copied
verbatim from KisakCOD; no test function replaces engine geometry logic.
Passing this test is NOT an Android render, map-load, or playable APK proof.
"""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from tools.iw3_android.prepare_g_runframe_prereqs import function_source

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "third_party/KisakCOD/src/database/db_registry.cpp"
INDEX = "void __cdecl DB_GetIndexBufferAndBase(uint8_t zoneHandle, void *indices, void **ib, int32_t *baseIndex)"
VERTEX = "void __cdecl DB_GetVertexBufferAndOffset(uint8_t zoneHandle, _BYTE *verts, void **vb, int32_t *vertexOffset)"


class OriginalDatabaseGeometryOffsetTests(unittest.TestCase):
    def test_original_geometry_offsets_keep_64bit_addresses_and_fail_closed(self):
        source = SOURCE.read_text(encoding="utf-8")
        index_body = function_source(source, INDEX)
        vertex_body = function_source(source, VERTEX)
        self.assertIn("reinterpret_cast<uintptr_t>(indices)", index_body)
        self.assertIn("reinterpret_cast<uintptr_t>(verts)", vertex_body)
        self.assertIn("bytes >> 1", index_body)
        self.assertIn("static_cast<uintptr_t>(INT32_MAX)", index_body)
        self.assertIn("static_cast<uintptr_t>(INT32_MAX)", vertex_body)
        self.assertNotIn("(uint32_t)indices", index_body)
        self.assertNotIn("verts - g_zones", vertex_body)

        fixture = r"""
#include <cassert>
#include <cstdint>
#include <climits>
#include <cstdio>
#define __cdecl
using _BYTE = unsigned char;
constexpr int ERR_DROP = 2;
struct Block { _BYTE *data = nullptr; };
struct XZoneMemory {
    void *indexBuffer = nullptr;
    void *vertexBuffer = nullptr;
    Block blocks[9];
};
struct XZone { XZoneMemory mem; };
XZone g_zones[2]{};
int errors = 0;
void Com_Error(int kind, const char *message, ...) {
    assert(kind == ERR_DROP && message && *message);
    ++errors;
}
/* ORIGINAL_INDEX */
/* ORIGINAL_VERTEX */
template<typename T> T *address(uintptr_t raw) {
    return reinterpret_cast<T *>(raw);
}
int main() {
    auto &mem = g_zones[1].mem;
    mem.indexBuffer = address<void>(0x900000000ULL);
    mem.vertexBuffer = address<void>(0xa00000000ULL);
    mem.blocks[8].data = address<_BYTE>(0x100000000ULL);
    mem.blocks[7].data = address<_BYTE>(0x200000000ULL);
    void *ib = nullptr, *vb = nullptr;
    int32_t base = -1, offset = -1;

    DB_GetIndexBufferAndBase(1, address<void>(0x100000080ULL), &ib, &base);
    assert(ib == mem.indexBuffer && base == 64 && errors == 0);
    DB_GetVertexBufferAndOffset(1, address<_BYTE>(0x200000080ULL), &vb, &offset);
    assert(vb == mem.vertexBuffer && offset == 128 && errors == 0);

    // Crossing a 4 GiB boundary is legal when the true offset is small.
    mem.blocks[8].data = address<_BYTE>(0x1fffffff0ULL);
    DB_GetIndexBufferAndBase(1, address<void>(0x200000010ULL), &ib, &base);
    assert(ib == mem.indexBuffer && base == 16 && errors == 0);

    // A full 4 GiB delta must NOT silently wrap to zero.
    mem.blocks[8].data = address<_BYTE>(0x100000000ULL);
    DB_GetIndexBufferAndBase(1, address<void>(0x200000000ULL), &ib, &base);
    assert(ib == nullptr && base == 0 && errors == 1);
    DB_GetIndexBufferAndBase(1, address<void>(0x100000003ULL), &ib, &base);
    assert(ib == nullptr && base == 0 && errors == 2);
    DB_GetIndexBufferAndBase(1, address<void>(0xffffffffULL), &ib, &base);
    assert(ib == nullptr && base == 0 && errors == 3);
    DB_GetIndexBufferAndBase(2, address<void>(0x100000002ULL), &ib, &base);
    assert(ib == nullptr && base == 0 && errors == 4);
    DB_GetIndexBufferAndBase(1, nullptr, &ib, &base);
    assert(ib == nullptr && base == 0 && errors == 5);

    DB_GetVertexBufferAndOffset(1, address<_BYTE>(0x280000000ULL), &vb, &offset);
    assert(vb == nullptr && offset == 0 && errors == 6);
    DB_GetVertexBufferAndOffset(1, address<_BYTE>(0x1ffffffffULL), &vb, &offset);
    assert(vb == nullptr && offset == 0 && errors == 7);
    DB_GetVertexBufferAndOffset(2, address<_BYTE>(0x200000001ULL), &vb, &offset);
    assert(vb == nullptr && offset == 0 && errors == 8);
    DB_GetVertexBufferAndOffset(1, nullptr, &vb, &offset);
    assert(vb == nullptr && offset == 0 && errors == 9);
    DB_GetIndexBufferAndBase(1, address<void>(0x100000002ULL), nullptr, &base);
    DB_GetVertexBufferAndOffset(1, address<_BYTE>(0x200000002ULL), &vb, nullptr);
    assert(errors == 11);

    std::puts("IW3_ORIGINAL_DB_GEOMETRY_OFFSETS_LP64_PASS");
}
"""
        fixture = fixture.replace("/* ORIGINAL_INDEX */", index_body)
        fixture = fixture.replace("/* ORIGINAL_VERTEX */", vertex_body)
        with tempfile.TemporaryDirectory() as temp:
            cpp = Path(temp) / "iw3_original_db_geometry.cpp"
            exe = Path(temp) / "iw3_original_db_geometry"
            cpp.write_text(fixture, encoding="utf-8")
            build = subprocess.run(
                [os.environ.get("CXX", "g++"), "-std=c++17", "-O1", "-g",
                 "-fsanitize=address,undefined", "-fno-omit-frame-pointer",
                 str(cpp), "-o", str(exe)],
                capture_output=True, text=True, timeout=90)
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            env = os.environ.copy()
            env["ASAN_OPTIONS"] = "detect_leaks=1"
            run = subprocess.run([str(exe)], capture_output=True, text=True,
                                 timeout=30, env=env)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertIn("IW3_ORIGINAL_DB_GEOMETRY_OFFSETS_LP64_PASS", run.stdout)


if __name__ == "__main__":
    unittest.main()
