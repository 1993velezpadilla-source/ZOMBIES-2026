"""Audit all 502 original IW3 weapon fields and execute native LP64 writes.

This is a host regression using the original table/function bodies with test
services. It is NOT proof of an Android game, real asset load, or renderer.
"""
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

from tools.iw3_android.prepare_g_runframe_prereqs import function_source

ROOT = Path(__file__).resolve().parents[1]
WEAPON_CPP = ROOT / "third_party/KisakCOD/src/bgame/bg_weapons_load_obj.cpp"
SHARED_CPP = ROOT / "third_party/KisakCOD/src/universal/q_shared.cpp"
WEAPON_H = ROOT / "third_party/KisakCOD/src/xanim/xanim.h"
LEGACY = ROOT / "tests/fixtures/iw3_weapon_fields_legacy_offsets.tsv"
TABLE_RE = re.compile(
    r'\{\s*"([^"]+)",\s*offsetof\(WeaponDef,\s*(\w+)(?:\[(\d+)\])?\),\s*(\w+)\s*\}'
)
COUNTS = {"NUM_WEAP_ANIMS": 33, "WEAP_ACCURACY_COUNT": 2}


def native_layout():
    text = WEAPON_H.read_text(encoding="utf-8")
    body = text.split("struct WeaponDef // sizeof=0x878", 1)[1].split("};", 1)[0]
    fields = {}
    mirror = []
    off32 = off64 = 0
    for raw in body.splitlines():
        line = raw.strip()
        if not line.endswith(";"):
            continue
        special = re.fullmatch(
            r"float \(\*(\w+)\[(\d+)\]\)\[WEAP_ACCURACY_COUNT\];", line
        )
        if special:
            name, count, pointer, kind = special[1], int(special[2]), True, "void*"
        else:
            match = re.fullmatch(r"(.+?)\s+(\w+)(?:\[(\w+)\])?;", line)
            if not match:
                raise AssertionError(f"Unrecognized WeaponDef member: {line}")
            dtype, name, raw_count = match.groups()
            count = COUNTS.get(raw_count, None)
            if count is None:
                count = int(raw_count) if raw_count else 1
            pointer = "*" in dtype
            kind = "void*" if pointer else (
                "uint16_t" if dtype == "uint16_t" else
                "float" if dtype == "float" else "uint32_t"
            )
        size32 = 4 if pointer else (2 if kind == "uint16_t" else 4)
        size64 = 8 if pointer else size32
        off32 = (off32 + size32 - 1) // size32 * size32
        off64 = (off64 + size64 - 1) // size64 * size64
        fields[name] = (off32, off64, size32, size64, count)
        mirror.append(f"    {kind} {name}" + (f"[{count}]" if count > 1 else "") + ";")
        off32 += size32 * count
        off64 += size64 * count
    if (off32, off64) != (2168, 2832) or len(fields) != 363:
        raise AssertionError(f"Unexpected native/legacy layout: {off32}, {off64}, {len(fields)}")
    return fields, "\n".join(mirror)


def source_table():
    source = WEAPON_CPP.read_text(encoding="utf-8")
    start = source.index("cspField_t weaponDefFields[502] =")
    end = source.index("}; // idb", start) + len("};")
    table = source[start:end]
    return table, TABLE_RE.findall(table)


def run_cpp(fixture, marker):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "weapon_lp64.cpp"
        exe = Path(tmp) / "weapon_lp64"
        path.write_text(fixture, encoding="utf-8")
        build = subprocess.run(
            [os.environ.get("CXX", "g++"), "-std=c++17", "-O1", "-g",
             "-fsanitize=address,undefined", "-fno-omit-frame-pointer",
             str(path), "-o", str(exe)],
            capture_output=True, text=True, timeout=120,
        )
        if build.returncode:
            raise AssertionError(build.stdout + build.stderr)
        env = os.environ.copy()
        env["ASAN_OPTIONS"] = "detect_leaks=1"
        run = subprocess.run([str(exe)], capture_output=True, text=True,
                             timeout=30, env=env)
        if run.returncode:
            raise AssertionError(run.stdout + run.stderr)
        if marker not in run.stdout:
            raise AssertionError(run.stdout + run.stderr)


class OriginalWeaponFieldLP64Tests(unittest.TestCase):
    def test_all_502_fields_match_original_32bit_layout_and_native_64bit_layout(self):
        layout, mirror = native_layout()
        table, entries = source_table()
        legacy = [
            line.split("\t") for line in LEGACY.read_text(encoding="utf-8").splitlines()
            if line and not line.startswith("#")
        ]
        self.assertEqual(len(legacy), 502)
        self.assertEqual(len(entries), 502)
        expected_native = []
        for (old_name, old_offset, old_type), (name, member, index, dtype) in zip(legacy, entries):
            self.assertEqual((name, dtype), (old_name, old_type))
            self.assertIn(member, layout)
            start32, start64, width32, width64, count = layout[member]
            idx = int(index) if index else 0
            self.assertLess(idx, count)
            self.assertEqual(start32 + idx * width32, int(old_offset),
                             f"legacy field {name} must retain original member mapping")
            expected_native.append(start64 + idx * width64)
        types = sorted({entry[3] for entry in entries} - {"CSPFT_STRING"})
        enum_def = "enum { CSPFT_STRING = 0, " + ", ".join(types) + " };"
        init = function_source(
            WEAPON_CPP.read_text(encoding="utf-8"),
            "void __cdecl InitWeaponDef(WeaponDef *weapDef)",
        )
        self.assertIn("(char *)weapDef + pField->iOffset", init)
        fixture = (
            "#include <cassert>\n#include <cstddef>\n#include <cstdint>\n"
            "#include <cstdio>\n#define __cdecl\n"
            + "struct WeaponDef {\n" + mirror + "\n};\n"
            + "static_assert(sizeof(WeaponDef) == 2832);\n"
            + "struct cspField_t { const char* szName; int iOffset; int iFieldType; };\n"
            + enum_def + "\n" + table + "\n" + init + "\n"
            + "int main() {\n"
            + "  static_assert(sizeof(void*) == 8);\n"
            + "  const int expected[502] = {" + ",".join(map(str, expected_native)) + "};\n"
            + "  for (int i = 0; i < 502; ++i) assert(weaponDefFields[i].iOffset == expected[i]);\n"
            + "  WeaponDef w{}; w.damage = 123456;\n"
            + "  w.gunXModel[0] = reinterpret_cast<void*>(uintptr_t(0x12345000));\n"
            + "  InitWeaponDef(&w);\n"
            + "  assert(w.damage == 123456 && w.gunXModel[0] == reinterpret_cast<void*>(uintptr_t(0x12345000)));\n"
            + "  assert(w.szInternalName && !w.szInternalName[0]);\n"
            + "  for (const auto &field : weaponDefFields) if (field.iFieldType == CSPFT_STRING) {\n"
            + "    const char *value = *reinterpret_cast<const char *const *>(reinterpret_cast<const char*>(&w) + field.iOffset);\n"
            + "    assert(value && !value[0]);\n"
            + "  }\n"
            + '  std::puts("IW3_ORIGINAL_502_WEAPON_FIELDS_LP64_PASS");\n'
            + "}\n"
        )
        run_cpp(fixture, "IW3_ORIGINAL_502_WEAPON_FIELDS_LP64_PASS")

    def test_original_parser_keeps_full_width_asset_pointers(self):
        source = SHARED_CPP.read_text(encoding="utf-8")
        original = function_source(source, "bool __cdecl ParseConfigStringToStructCustomSize(")
        for var in ("v9", "v22", "v10", "SoundAlias"):
            self.assertIn(f"memcpy(&pStruct[v20->iOffset], &{var}, sizeof({var}));", original)
        fixture = r"""
#include <cassert>
#include <cstdint>
#include <cstddef>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#define __cdecl
enum { CSPFT_STRING=0, CSPFT_STRING_MAX_STRING_CHARS=1,
 CSPFT_STRING_MAX_QPATH=2, CSPFT_STRING_MAX_OSPATH=3,
 CSPFT_INT=4, CSPFT_QBOOLEAN=5, CSPFT_FLOAT=6,
 CSPFT_MILLISECONDS=7, CSPFT_FX=8, CSPFT_XMODEL=9,
 CSPFT_MATERIAL=10, CSPFT_SOUND=11, CSPFT_NUM_BASE_FIELD_TYPES=12 };
constexpr int ERR_DROP=1, IMAGE_TRACK_MISC=2;
bool alwaysfails = false;
struct FxEffectDef { int id; };
struct XModel { int id; };
struct Material { int id; };
struct snd_alias_list_t { int id; };
struct cspField_t { const char* szName; int iOffset; int iFieldType; };
static FxEffectDef fx{1};
static XModel model{2};
static Material material{3};
static snd_alias_list_t sound{4};
const char* Info_ValueForKey(char*, char*) { return "asset"; }
void I_strncpyz(char* dst, const char* src, int size) {
    std::snprintf(dst, static_cast<size_t>(size), "%s", src);
}
const FxEffectDef* FX_Register(const char*) { return &fx; }
XModel* R_RegisterModel(const char*) { return &model; }
Material* Material_RegisterHandle(const char*, int) { return &material; }
snd_alias_list_t* Com_FindSoundAlias(const char*) { return &sound; }
const char* va(const char*, ...) { return "bad field"; }
void MyAssertHandler(const char*, int, int, const char*, ...) { std::abort(); }
void Com_Error(int, const char*, ...) { std::abort(); }
/* ORIGINAL_PARSER */
struct Slots {
    uint64_t guard0;
    const FxEffectDef* effect;
    uint64_t guard1;
    XModel* xmodel;
    uint64_t guard2;
    Material* materialPtr;
    uint64_t guard3;
    snd_alias_list_t* soundPtr;
    uint64_t guard4;
};
void set_string(uint8_t*, const char*) { std::abort(); }
int main() {
    static_assert(sizeof(void*) == 8);
    assert(reinterpret_cast<uintptr_t>(&fx) > UINT32_MAX);
    Slots slots{};
    slots.guard0 = slots.guard1 = slots.guard2 = slots.guard3 = slots.guard4 =
        UINT64_C(0xDDAABBAACCDDEEFF);
    cspField_t fields[] = {
        {"fx", offsetof(Slots, effect), CSPFT_FX},
        {"model", offsetof(Slots, xmodel), CSPFT_XMODEL},
        {"material", offsetof(Slots, materialPtr), CSPFT_MATERIAL},
        {"sound", offsetof(Slots, soundPtr), CSPFT_SOUND},
    };
    char config[] = "test";
    assert(ParseConfigStringToStructCustomSize(
        reinterpret_cast<uint8_t*>(&slots), fields, 4, config, 12,
        nullptr, set_string));
    assert(slots.effect == &fx && slots.xmodel == &model);
    assert(slots.materialPtr == &material && slots.soundPtr == &sound);
    assert(slots.guard0 == UINT64_C(0xDDAABBAACCDDEEFF));
    assert(slots.guard1 == slots.guard0 && slots.guard2 == slots.guard0);
    assert(slots.guard3 == slots.guard0 && slots.guard4 == slots.guard0);
    std::puts("IW3_ORIGINAL_ASSET_POINTERS_LP64_PASS");
}
"""
        run_cpp(fixture.replace("/* ORIGINAL_PARSER */", original),
                "IW3_ORIGINAL_ASSET_POINTERS_LP64_PASS")


if __name__ == "__main__":
    unittest.main()
