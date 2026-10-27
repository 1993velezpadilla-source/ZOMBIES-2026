#include "iw3_android_dvar_pointer_compat.h"

#include <cassert>
#include <cstddef>
#include <cstdarg>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <strings.h>

static_assert(
    offsetof(DvarLimits_Integer, min) ==
        offsetof(DvarLimits_Enumeration, stringCount),
    "DvarLimits integer min and enum count must share the original union offset");
static_assert(
    offsetof(DvarLimits_Enumeration, strings) >
        offsetof(DvarLimits_Integer, max),
    "LP64 enum string pointers must not be assumed to alias integer max");

namespace {
dvar_s g_registered{};
DvarValue g_last_value{};
DvarLimits g_last_domain{};
uint8_t g_last_type = 0xff;
}

const dvar_s *__cdecl Dvar_RegisterVariant(
    const char *, uint8_t type, uint16_t, DvarValue value,
    DvarLimits domain, const char *) {
    g_last_type = type;
    g_last_value = value;
    g_last_domain = domain;
    return &g_registered;
}

bool __cdecl CanKeepStringPointer(const char *string) {
    return string != nullptr;
}

void __cdecl MyAssertHandler(const char *, int, int, const char *, ...) {
    std::abort();
}

char *QDECL va(const char *format, ...) {
    static char buffer[1024];
    va_list args;
    va_start(args, format);
    std::vsnprintf(buffer, sizeof(buffer), format, args);
    va_end(args);
    return buffer;
}

int I_stricmp(const char *left, const char *right) {
    return strcasecmp(left, right);
}

int I_strnicmp(const char *left, const char *right, int count) {
    return strncasecmp(left, right, static_cast<std::size_t>(count));
}

bool __cdecl Dvar_StringToBool(const char *string) {
    return string && (std::strcmp(string, "1") == 0 ||
                      strcasecmp(string, "true") == 0);
}

int __cdecl Dvar_StringToInt(const char *string) {
    return std::atoi(string);
}

double __cdecl Dvar_StringToFloat(const char *string) {
    return std::strtod(string, nullptr);
}

void __cdecl Dvar_StringToVec2(const char *string, float *vector) {
    std::sscanf(string, "%f %f", &vector[0], &vector[1]);
}

void __cdecl Dvar_StringToVec3(const char *string, float *vector) {
    std::sscanf(string, "%f %f %f", &vector[0], &vector[1], &vector[2]);
}

void __cdecl Dvar_StringToVec4(const char *string, float *vector) {
    std::sscanf(string, "%f %f %f %f",
                &vector[0], &vector[1], &vector[2], &vector[3]);
}

void __cdecl Dvar_StringToColor(const char *, uint8_t *color) {
    std::memset(color, 0, 4);
}

int main() {
    static_assert(sizeof(void *) == 8,
                  "This regression must exercise a 64-bit pointer ABI");

    assert(!Dvar_IsValidName(nullptr));
    assert(Dvar_IsValidName("alpha_123"));
    assert(!Dvar_IsValidName("bad-name"));
    const char high_bit_name[] = {static_cast<char>(0xFF), '\0'};
    assert(!Dvar_IsValidName(high_bit_name));

    char stringValue[] = "filesDir/main";
    assert(reinterpret_cast<std::uintptr_t>(stringValue) > UINT32_MAX);
    const dvar_s *registered = Dvar_RegisterString(
        "fs_homepath", stringValue, 0, "Android app-private path");
    assert(registered == &g_registered);
    assert(g_last_type == DVAR_TYPE_STRING);
    assert(g_last_value.string == stringValue);
    assert(reinterpret_cast<std::uintptr_t>(g_last_value.string) ==
           reinterpret_cast<std::uintptr_t>(stringValue));

    const char *names[] = {"alpha", "beta", "gamma", nullptr};
    assert(reinterpret_cast<std::uintptr_t>(names) > UINT32_MAX);
    registered = Dvar_RegisterEnum(
        "test_enum", names, 1, 0, "pointer-width enum table");
    assert(registered == &g_registered);
    assert(g_last_type == DVAR_TYPE_ENUM);
    assert(g_last_domain.enumeration.stringCount == 3);
    assert(g_last_domain.enumeration.strings == names);

    assert(Dvar_StringToEnum(&g_last_domain, "beta") == 1);
    assert(Dvar_StringToEnum(&g_last_domain, "be") == 1);

    dvar_s enum_dvar{};
    enum_dvar.name = "test_enum";
    enum_dvar.type = DVAR_TYPE_ENUM;
    enum_dvar.domain.enumeration.stringCount = 3;
    enum_dvar.domain.enumeration.strings = names;
    enum_dvar.current.integer = 2;
    assert(std::strcmp(Dvar_EnumToString(&enum_dvar), "gamma") == 0);
    assert(std::strcmp(Dvar_IndexStringToEnumString(&enum_dvar, "1"),
                       "beta") == 0);

    DvarValue enum_value{};
    enum_value.integer = 0;
    assert(std::strcmp(Dvar_ValueToString(&enum_dvar, enum_value), "alpha") == 0);

    DvarValue parsed{};
    DvarLimits domain{};
    domain.enumeration.stringCount = 3;
    domain.enumeration.strings = names;
    assert(Dvar_StringToValue(&parsed, DVAR_TYPE_STRING, domain, stringValue) ==
           &parsed);
    assert(parsed.string == stringValue);
    assert(Dvar_StringToValue(&parsed, DVAR_TYPE_ENUM, domain, "gamma") ==
           &parsed);
    assert(parsed.integer == 2);

    Dvar_UpdateEnumDomain(&enum_dvar, names);
    assert(enum_dvar.domain.enumeration.strings == names);
    assert(enum_dvar.domain.enumeration.stringCount == 3);
    assert(std::strcmp(Dvar_EnumToString(&enum_dvar), "gamma") == 0);

    // Exercise the authentic original clamp body with the LP64 DvarLimits ABI.
    // Integer domains must use integer.min/max, not the wider enum union member.
    DvarLimits integerDomain{};
    integerDomain.integer.min = -5;
    integerDomain.integer.max = 9;
    DvarValue resetValue{};
    resetValue.integer = 0;
    DvarValue input{};
    DvarValue clamped{};

    input.integer = -20;
    assert(Dvar_ClampValueToDomain(
        &clamped, DVAR_TYPE_INT, input, resetValue, integerDomain) == &clamped);
    assert(clamped.integer == -5);

    input.integer = 42;
    assert(Dvar_ClampValueToDomain(
        &clamped, DVAR_TYPE_INT, input, resetValue, integerDomain) == &clamped);
    assert(clamped.integer == 9);

    input.integer = 4;
    assert(Dvar_ClampValueToDomain(
        &clamped, DVAR_TYPE_INT, input, resetValue, integerDomain) == &clamped);
    assert(clamped.integer == 4);
    return 0;
}
