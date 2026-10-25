cmake_minimum_required(VERSION 3.21)
project(Z2026_Original_IW3_Math_Port LANGUAGES CXX)

# Not a Godot game, an empty Android shell, or a substitute engine.
# This is an incremental Android ABI port of a genuine KisakCOD source TU.
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

if(NOT IW3_EXTRACTED_MATH OR NOT EXISTS "${IW3_EXTRACTED_MATH}")
    message(FATAL_ERROR "Supply -DIW3_EXTRACTED_MATH=<generated real KisakCOD source>; no mock math allowed")
endif()

if(NOT IW3_EXTRACTED_SURFACE OR NOT EXISTS "${IW3_EXTRACTED_SURFACE}")
    message(FATAL_ERROR "Original IW3 surface translation unit required; no mock data")
endif()
if(NOT IW3_REAL_HEADER_ROOT OR NOT EXISTS "${IW3_REAL_HEADER_ROOT}/surfaceflags.h")
    message(FATAL_ERROR "Original KisakCOD surfaceflags.h required")
endif()
if(NOT IW3_EXTRACTED_CONSTANTS OR NOT EXISTS "${IW3_EXTRACTED_CONSTANTS}")
    message(FATAL_ERROR "Original 833-slot IW3 config registry required")
endif()
if(NOT EXISTS "${IW3_REAL_HEADER_ROOT}/com_constantconfigstrings.h")
    message(FATAL_ERROR "Original engine config registry declarations required")
endif()

add_library(iw3_sp_math SHARED
    "${IW3_EXTRACTED_MATH}"
    "${IW3_EXTRACTED_SURFACE}"
    "${IW3_EXTRACTED_CONSTANTS}"
    "${CMAKE_CURRENT_SOURCE_DIR}/native_math_abi.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/iw3_android_platform.cpp"
)
target_include_directories(iw3_sp_math PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}" "${IW3_REAL_HEADER_ROOT}")
set_target_properties(iw3_sp_math PROPERTIES
    CXX_VISIBILITY_PRESET hidden
    VISIBILITY_INLINES_HIDDEN YES
    OUTPUT_NAME "iw3_sp_math"
)
target_compile_options(iw3_sp_math PRIVATE
    -ffunction-sections -fdata-sections -Wall -Wextra
)
target_link_options(iw3_sp_math PRIVATE
    -Wl,--gc-sections
    -Wl,--no-undefined
)
if(ANDROID)
    if(NOT ANDROID_ABI STREQUAL "arm64-v8a")
        message(FATAL_ERROR "Only real Android arm64-v8a accepted in this gate")
    endif()
    if(NOT CMAKE_SIZEOF_VOID_P EQUAL 8)
        message(FATAL_ERROR "IW3 Android native gate requires 64-bit pointers")
    endif()
    message(STATUS "IW3 original source -> Android ARM64 shared library")
else()
    enable_testing()
    add_executable(iw3_math_host_test
        "${CMAKE_CURRENT_SOURCE_DIR}/math_native_test.cpp")
    target_link_libraries(iw3_math_host_test PRIVATE iw3_sp_math)
    # CMake Release normally defines NDEBUG; keep C++ assert() ACTIVE in
    # this verification executable, otherwise ctest yields a false-green.
    target_compile_options(iw3_math_host_test PRIVATE -UNDEBUG)
    add_test(NAME iw3_real_math COMMAND iw3_math_host_test)
    add_executable(iw3_platform_host_test
        "${CMAKE_CURRENT_SOURCE_DIR}/platform_native_test.cpp")
    target_compile_options(iw3_platform_host_test PRIVATE -UNDEBUG)
    target_link_libraries(iw3_platform_host_test PRIVATE iw3_sp_math)
    add_test(NAME iw3_portable_platform COMMAND iw3_platform_host_test)
endif()
