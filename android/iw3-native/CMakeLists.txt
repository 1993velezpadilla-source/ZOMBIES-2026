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
if(NOT IW3_EXTRACTED_FRAME_MEMCPY OR NOT EXISTS "${IW3_EXTRACTED_FRAME_MEMCPY}")
    message(FATAL_ERROR "Actual KisakCOD G_RunFrame Com_Memcpy prerequisite required")
endif()
if(NOT IW3_EXTRACTED_POOL OR NOT EXISTS "${IW3_EXTRACTED_POOL}")
    message(FATAL_ERROR "Authentic IW3 64-bit-safe pool allocator source required")
endif()
if(NOT IW3_EXTRACTED_HITLOC OR NOT EXISTS "${IW3_EXTRACTED_HITLOC}")
    message(FATAL_ERROR "Authentic IW3 SP 64-bit-safe hit-location source required")
endif()
if(NOT IW3_EXTRACTED_IWD_NAMES OR NOT EXISTS "${IW3_EXTRACTED_IWD_NAMES}")
    message(FATAL_ERROR "Authentic KisakCOD IWD filename hash/compare source required")
endif()
if(NOT EXISTS "${IW3_REAL_HEADER_ROOT}/pool_allocator.h")
    message(FATAL_ERROR "Authentic original IW3 pool declarations required")
endif()
if(NOT EXISTS "${IW3_REAL_HEADER_ROOT}/com_constantconfigstrings.h")
    message(FATAL_ERROR "Original engine config registry declarations required")
endif()

# Compile the complete ORIGINAL frame from its engine source module and
# real state headers. This archive deliberately keeps unported service
# references unresolved; it is not linked into the diagnostic APK.
get_filename_component(IW3_ENGINE_SOURCE_ROOT "${IW3_REAL_HEADER_ROOT}/.." ABSOLUTE)
if(NOT EXISTS "${IW3_ENGINE_SOURCE_ROOT}/game/g_runframe.cpp")
    message(FATAL_ERROR "Complete original IW3 SP frame source required")
endif()
add_library(iw3_sp_frame STATIC "${IW3_ENGINE_SOURCE_ROOT}/game/g_runframe.cpp")
target_include_directories(iw3_sp_frame PRIVATE "${IW3_ENGINE_SOURCE_ROOT}")
target_compile_definitions(iw3_sp_frame PRIVATE KISAK_SP=1)
target_compile_options(iw3_sp_frame PRIVATE -fsigned-char -frounding-math -fno-fast-math)

add_library(iw3_sp_math SHARED
    "${IW3_EXTRACTED_MATH}"
    "${IW3_EXTRACTED_SURFACE}"
    "${IW3_EXTRACTED_CONSTANTS}"
    "${IW3_EXTRACTED_FRAME_MEMCPY}"
    "${IW3_EXTRACTED_POOL}"
    "${IW3_EXTRACTED_HITLOC}"
    "${IW3_EXTRACTED_IWD_NAMES}"
    "${CMAKE_CURRENT_SOURCE_DIR}/native_math_abi.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/iw3_android_platform.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/snap_float_abi.cpp"
)
target_include_directories(iw3_sp_math PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}" "${IW3_REAL_HEADER_ROOT}")
set_target_properties(iw3_sp_math PROPERTIES
    CXX_VISIBILITY_PRESET hidden
    VISIBILITY_INLINES_HIDDEN YES
    OUTPUT_NAME "iw3_sp_math"
)
target_compile_options(iw3_sp_math PRIVATE
    -ffunction-sections -fdata-sections -Wall -Wextra
    -frounding-math -fno-fast-math
)
target_link_options(iw3_sp_math PRIVATE
    -Wl,--gc-sections
    -Wl,--no-undefined
)
if(ANDROID)
    # Java Activity JNI entry points are tied directly to the authentic
    # IW3 native C++ library; not a gameplay stand-in or second engine.
    target_sources(iw3_sp_math PRIVATE
        "${CMAKE_CURRENT_SOURCE_DIR}/iw3_android_jni.cpp")
    target_link_libraries(iw3_sp_math PRIVATE log)
    if(ANDROID_ABI STREQUAL "arm64-v8a")
        message(STATUS "IW3 original source -> Android ARM64 shared library")
    elseif(ANDROID_ABI STREQUAL "x86_64" AND IW3_EMULATOR_DIAGNOSTIC_ONLY)
        message(STATUS "IW3 original source -> x86_64 Android emulator DIAGNOSTIC ONLY")
    else()
        message(FATAL_ERROR "IW3 native target requires ARM64, or gated Android x86_64 emulator diagnostics")
    endif()
    if(NOT CMAKE_SIZEOF_VOID_P EQUAL 8)
        message(FATAL_ERROR "IW3 Android native gate requires 64-bit pointers")
    endif()
    message(STATUS "IW3 original code native Android JNI enabled")
else()
    enable_testing()
    add_executable(iw3_snap_float_host_test
        "${CMAKE_CURRENT_SOURCE_DIR}/snap_float_native_test.cpp")
    target_include_directories(iw3_snap_float_host_test PRIVATE "${IW3_REAL_HEADER_ROOT}")
    target_compile_options(iw3_snap_float_host_test PRIVATE
        -UNDEBUG -frounding-math -fno-fast-math)
    target_link_libraries(iw3_snap_float_host_test PRIVATE iw3_sp_math)
    add_test(NAME iw3_original_snap_float_arm_portability COMMAND iw3_snap_float_host_test)
    add_executable(iw3_math_host_test
        "${CMAKE_CURRENT_SOURCE_DIR}/math_native_test.cpp")
    target_link_libraries(iw3_math_host_test PRIVATE iw3_sp_math)
    # CMake Release normally defines NDEBUG; keep C++ assert() ACTIVE in
    # this verification executable, otherwise ctest yields a false-green.
    target_compile_options(iw3_math_host_test PRIVATE -UNDEBUG)
    add_test(NAME iw3_real_math COMMAND iw3_math_host_test)
    add_executable(iw3_real_pool_host_test
        "${CMAKE_CURRENT_SOURCE_DIR}/pool_native_test.cpp"
        "${IW3_EXTRACTED_POOL}")
    target_include_directories(iw3_real_pool_host_test PRIVATE
        "${CMAKE_CURRENT_SOURCE_DIR}" "${IW3_REAL_HEADER_ROOT}")
    target_compile_options(iw3_real_pool_host_test PRIVATE -UNDEBUG)
    target_link_libraries(iw3_real_pool_host_test PRIVATE iw3_sp_math)
    add_test(NAME iw3_original_engine_pool_allocator_64bit COMMAND iw3_real_pool_host_test)
    add_executable(iw3_real_hitloc_host_test
        "${CMAKE_CURRENT_SOURCE_DIR}/hitloc_native_test.cpp"
        "${IW3_EXTRACTED_HITLOC}")
    target_include_directories(iw3_real_hitloc_host_test PRIVATE
        "${CMAKE_CURRENT_SOURCE_DIR}")
    target_compile_options(iw3_real_hitloc_host_test PRIVATE -UNDEBUG)
    target_link_libraries(iw3_real_hitloc_host_test PRIVATE iw3_sp_math)
    add_test(NAME iw3_original_sp_hitloc_copy_64bit COMMAND iw3_real_hitloc_host_test)
    add_executable(iw3_real_iwd_names_host_test
        "${CMAKE_CURRENT_SOURCE_DIR}/iwd_names_native_test.cpp"
        "${IW3_EXTRACTED_IWD_NAMES}")
    target_include_directories(iw3_real_iwd_names_host_test PRIVATE
        "${CMAKE_CURRENT_SOURCE_DIR}")
    target_compile_options(iw3_real_iwd_names_host_test PRIVATE -UNDEBUG)
    target_link_libraries(iw3_real_iwd_names_host_test PRIVATE iw3_sp_math)
    add_test(NAME iw3_original_iwd_filename_hash_compare COMMAND iw3_real_iwd_names_host_test)
    add_executable(iw3_platform_host_test
        "${CMAKE_CURRENT_SOURCE_DIR}/platform_native_test.cpp")
    target_compile_options(iw3_platform_host_test PRIVATE -UNDEBUG)
    target_link_libraries(iw3_platform_host_test PRIVATE iw3_sp_math)
    add_test(NAME iw3_portable_platform COMMAND iw3_platform_host_test)
    if(NOT IW3_ENTITY_LOOP_INC OR NOT EXISTS "${IW3_ENTITY_LOOP_INC}")
        message(FATAL_ERROR "Original G_RunFrame typed entity source extraction required for ABI fixture")
    endif()
    add_executable(iw3_real_frame_loop_abi_test
        "${CMAKE_CURRENT_SOURCE_DIR}/frame_loop_abi_test.cpp")
    get_filename_component(IW3_ENTITY_LOOP_DIR "${IW3_ENTITY_LOOP_INC}" DIRECTORY)
    target_include_directories(iw3_real_frame_loop_abi_test PRIVATE "${IW3_ENTITY_LOOP_DIR}")
    target_compile_options(iw3_real_frame_loop_abi_test PRIVATE -UNDEBUG)
    add_test(NAME iw3_real_g_runframe_typed_entity_64bit COMMAND iw3_real_frame_loop_abi_test)
endif()
