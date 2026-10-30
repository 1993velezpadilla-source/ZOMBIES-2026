cmake_minimum_required(VERSION 3.21)
project(Z2026_Original_IW3_Math_Port LANGUAGES CXX)

# Not a Godot game, an empty Android shell, or a substitute engine.
# This is an incremental Android ABI port of a genuine KisakCOD source TU.
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# Native Android fatal-assert service for original engine modules. The upstream
# assertive.cpp implementation is Win32-bound; this provider preserves fatal
# invariant handling and reports the original file/line/type/message.
add_library(iw3_sp_android_assert STATIC
    "${CMAKE_CURRENT_SOURCE_DIR}/iw3_android_assert.cpp")
target_compile_options(iw3_sp_android_assert PRIVATE -Wall -Wextra)
if(ANDROID)
    target_link_libraries(iw3_sp_android_assert PUBLIC log)
endif()

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
if(NOT IW3_EXTRACTED_UNZIP OR NOT EXISTS "${IW3_EXTRACTED_UNZIP}")
    message(FATAL_ERROR "Authentic original IW3 ZIP32/IWD parser source required")
endif()
if(NOT IW3_EXTRACTED_IWD_MOUNT OR NOT EXISTS "${IW3_EXTRACTED_IWD_MOUNT}")
    message(FATAL_ERROR "Authentic FS_LoadZipFile source extraction required")
endif()
if(NOT IW3_EXTRACTED_IWD_SERVICES OR NOT EXISTS "${IW3_EXTRACTED_IWD_SERVICES}")
    message(FATAL_ERROR "Authentic IWD allocator/checksum/string service extraction required")
endif()
if(NOT IW3_EXTRACTED_IWD_SEARCHPATH OR NOT EXISTS "${IW3_EXTRACTED_IWD_SEARCHPATH}")
    message(FATAL_ERROR "Original FS_AddSearchPath source extraction required")
endif()
if(NOT IW3_EXTRACTED_IWD_DIRECTORY OR NOT EXISTS "${IW3_EXTRACTED_IWD_DIRECTORY}")
    message(FATAL_ERROR "Original FS_AddIwdFilesForGameDirectory source extraction required")
endif()

if(IW3_EXTRACTED_IWD_DIRECTORY_SERVICES AND NOT EXISTS "${IW3_EXTRACTED_IWD_DIRECTORY_SERVICES}")
    message(FATAL_ERROR "Configured original IWD sort/path comparison helper source does not exist")
endif()
if(NOT IW3_EXTRACTED_IWD_LOOKUP OR NOT EXISTS "${IW3_EXTRACTED_IWD_LOOKUP}")
    message(FATAL_ERROR "Original FS_FOpenFileReadForThread lookup-prefix extraction required")
endif()

if(NOT IW3_EXTRACTED_FS_READ OR NOT EXISTS "${IW3_EXTRACTED_FS_READ}")
    message(FATAL_ERROR "Verbatim original FS_Read source required for the 64-bit ABI compile gate")
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

# Compile the authentic filesystem startup functions on every configured
# build. Silently omitting this target made it too easy for an ABI gate to pass
# without even compiling FS_RegisterDvars/FS_Startup/FS_InitFilesystem.
# This is still a dependency-audit archive: it does NOT claim startup is invoked
# or link the unresolved engine service graph into the diagnostic APK.
if(NOT IW3_EXTRACTED_FS_STARTUP OR NOT EXISTS "${IW3_EXTRACTED_FS_STARTUP}")
    message(FATAL_ERROR
        "Original FS_RegisterDvars/FS_Startup/FS_InitFilesystem source required; refusing to skip the filesystem startup compile gate")
endif()
add_library(iw3_sp_fs_startup STATIC
    "${IW3_EXTRACTED_FS_STARTUP}"
    "${CMAKE_CURRENT_SOURCE_DIR}/iw3_android_fs_startup_io.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/iw3_android_directory_has_contents.cpp")
target_include_directories(iw3_sp_fs_startup PRIVATE
    "${CMAKE_CURRENT_SOURCE_DIR}"
    "${IW3_REAL_HEADER_ROOT}"
    "${IW3_ENGINE_SOURCE_ROOT}"
    "${IW3_ENGINE_SOURCE_ROOT}/qcommon"
    "${IW3_ENGINE_SOURCE_ROOT}/../deps")
target_compile_definitions(iw3_sp_fs_startup PRIVATE KISAK_SP=1)
target_compile_options(iw3_sp_fs_startup PRIVATE
    -Wall -Wextra -fsigned-char -frounding-math -fno-fast-math)

# Compile the complete authentic com_files.cpp translation unit for Android
# ARM64, not only extracted function slices. This is a compile-only portability
# gate: unresolved engine services are expected, and this object is deliberately
# NOT linked into the diagnostic JNI library or presented as a running game.
if(ANDROID)
    add_library(iw3_sp_com_files_full_compile OBJECT
        "${IW3_ENGINE_SOURCE_ROOT}/universal/com_files.cpp")
    target_include_directories(iw3_sp_com_files_full_compile PRIVATE
        "${CMAKE_CURRENT_SOURCE_DIR}"
        "${IW3_ENGINE_SOURCE_ROOT}"
        "${IW3_ENGINE_SOURCE_ROOT}/qcommon"
        "${IW3_ENGINE_SOURCE_ROOT}/../deps")
    target_compile_definitions(iw3_sp_com_files_full_compile PRIVATE KISAK_SP=1)
    target_compile_options(iw3_sp_com_files_full_compile PRIVATE
        -Wall -Wextra -fsigned-char -frounding-math -fno-fast-math)
endif()

# Compile the complete original FastFile loader translation unit for Android
# ARM64. Renderer completion functions are declaration-only and intentionally
# remain unresolved; this gate proves the authentic loader source is portable
# enough to compile, not that the renderer or database runtime is linked.
if(ANDROID)
    add_library(iw3_sp_db_file_load_full_compile OBJECT
        "${IW3_ENGINE_SOURCE_ROOT}/database/db_file_load.cpp")
    target_include_directories(iw3_sp_db_file_load_full_compile PRIVATE
        "${CMAKE_CURRENT_SOURCE_DIR}"
        "${IW3_ENGINE_SOURCE_ROOT}"
        "${IW3_ENGINE_SOURCE_ROOT}/qcommon"
        "${IW3_ENGINE_SOURCE_ROOT}/../deps")
    target_compile_definitions(iw3_sp_db_file_load_full_compile PRIVATE KISAK_SP=1)
    target_compile_options(iw3_sp_db_file_load_full_compile PRIVATE
        -fms-extensions -Wall -Wextra -fsigned-char -frounding-math -fno-fast-math)
endif()

# Compile the complete original database registry translation unit for Android
# ARM64. This is deliberately an OBJECT-only portability gate: the registry
# owns real asset-pool and zone state, but its Win32/D3D service graph is not
# yet linked into the Android process. Keeping it out of JNI prevents a
# diagnostic package from masquerading as a running engine.
if(ANDROID)
    add_library(iw3_sp_db_registry_full_compile OBJECT
        "${IW3_ENGINE_SOURCE_ROOT}/database/db_registry.cpp")
    target_include_directories(iw3_sp_db_registry_full_compile PRIVATE
        "${CMAKE_CURRENT_SOURCE_DIR}"
        "${IW3_ENGINE_SOURCE_ROOT}"
        "${IW3_ENGINE_SOURCE_ROOT}/qcommon"
        "${IW3_ENGINE_SOURCE_ROOT}/../deps")
    target_compile_definitions(iw3_sp_db_registry_full_compile PRIVATE KISAK_SP=1)
    target_compile_options(iw3_sp_db_registry_full_compile PRIVATE
        -fms-extensions -ferror-limit=0 -fno-inline -Wall -Wextra -fsigned-char -frounding-math -fno-fast-math)
endif()

# Compile the complete original client screen-placement translation unit for
# Android ARM64. It owns scrPlaceView and the real viewport setup routines;
# this object is audited separately and is not linked into the JNI diagnostic.
if(ANDROID)
    add_library(iw3_sp_screen_placement_full_compile OBJECT
        "${IW3_ENGINE_SOURCE_ROOT}/client/screen_placement.cpp")
    target_include_directories(iw3_sp_screen_placement_full_compile PRIVATE
        "${CMAKE_CURRENT_SOURCE_DIR}"
        "${IW3_ENGINE_SOURCE_ROOT}"
        "${IW3_ENGINE_SOURCE_ROOT}/client"
        "${IW3_ENGINE_SOURCE_ROOT}/qcommon"
        "${IW3_ENGINE_SOURCE_ROOT}/universal"
        "${IW3_ENGINE_SOURCE_ROOT}/ui"
        "${IW3_ENGINE_SOURCE_ROOT}/gfx_d3d"
        "${IW3_ENGINE_SOURCE_ROOT}/game"
        "${IW3_ENGINE_SOURCE_ROOT}/cgame"
        "${IW3_ENGINE_SOURCE_ROOT}/bgame"
        "${IW3_ENGINE_SOURCE_ROOT}/../deps")
    target_compile_definitions(iw3_sp_screen_placement_full_compile PRIVATE KISAK_SP=1)
    target_compile_options(iw3_sp_screen_placement_full_compile PRIVATE
        -fms-extensions -Wall -Wextra -fsigned-char -frounding-math -fno-fast-math)
endif()

# Compile the complete authentic client-input translation unit for Android ARM64.
# This closes the Win32 SDK-header portability gap around CL_CreateCmd. It is
# deliberately OBJECT-only: the original client state/command loop is not yet
# initialized or linked into the Activity, and this target is not part of JNI.
if(ANDROID)
    add_library(iw3_sp_client_input_full_compile OBJECT
        "${IW3_ENGINE_SOURCE_ROOT}/client/cl_input.cpp")
    target_include_directories(iw3_sp_client_input_full_compile PRIVATE
        "${CMAKE_CURRENT_SOURCE_DIR}"
        "${IW3_ENGINE_SOURCE_ROOT}"
        "${IW3_ENGINE_SOURCE_ROOT}/client"
        "${IW3_ENGINE_SOURCE_ROOT}/qcommon"
        "${IW3_ENGINE_SOURCE_ROOT}/universal"
        "${IW3_ENGINE_SOURCE_ROOT}/ui"
        "${IW3_ENGINE_SOURCE_ROOT}/devgui"
        "${IW3_ENGINE_SOURCE_ROOT}/gfx_d3d"
        "${IW3_ENGINE_SOURCE_ROOT}/game"
        "${IW3_ENGINE_SOURCE_ROOT}/cgame"
        "${IW3_ENGINE_SOURCE_ROOT}/server"
        "${IW3_ENGINE_SOURCE_ROOT}/bgame"
        "${IW3_ENGINE_SOURCE_ROOT}/aim_assist"
        "${IW3_ENGINE_SOURCE_ROOT}/win32"
        "${IW3_ENGINE_SOURCE_ROOT}/sound"
        "${IW3_ENGINE_SOURCE_ROOT}/script"
        "${IW3_ENGINE_SOURCE_ROOT}/../deps")
    target_compile_definitions(iw3_sp_client_input_full_compile PRIVATE
        KISAK_SP=1 KISAK_OPENAL=1)
    target_compile_options(iw3_sp_client_input_full_compile PRIVATE
        -fms-extensions -fno-inline -Wall -Wextra -fsigned-char
        -frounding-math -fno-fast-math)
endif()

# Compile the complete original actor/model-pose translation unit for Android ARM64.
# This preserves authentic DObj pose/bounds code as a portability gate only. It
# does not provide a GPU backend, link the renderer into JNI, or claim a rendered actor.
if(ANDROID)
    add_library(iw3_sp_renderer_model_pose_full_compile OBJECT
        "${IW3_ENGINE_SOURCE_ROOT}/gfx_d3d/r_model_pose.cpp")
    target_include_directories(iw3_sp_renderer_model_pose_full_compile PRIVATE
        "${CMAKE_CURRENT_SOURCE_DIR}"
        "${IW3_ENGINE_SOURCE_ROOT}"
        "${IW3_ENGINE_SOURCE_ROOT}/client"
        "${IW3_ENGINE_SOURCE_ROOT}/qcommon"
        "${IW3_ENGINE_SOURCE_ROOT}/universal"
        "${IW3_ENGINE_SOURCE_ROOT}/gfx_d3d"
        "${IW3_ENGINE_SOURCE_ROOT}/game"
        "${IW3_ENGINE_SOURCE_ROOT}/cgame"
        "${IW3_ENGINE_SOURCE_ROOT}/bgame"
        "${IW3_ENGINE_SOURCE_ROOT}/xanim"
        "${IW3_ENGINE_SOURCE_ROOT}/../deps")
    target_compile_definitions(iw3_sp_renderer_model_pose_full_compile PRIVATE KISAK_SP=1)
    target_compile_options(iw3_sp_renderer_model_pose_full_compile PRIVATE
        -fms-extensions -Wall -Wextra -fsigned-char
        -frounding-math -fno-fast-math)
endif()

# Compile the complete original actor-corpse translation unit for Android ARM64.
# This includes the real G_UpdateActorCorpses/G_RemoveActorCorpses implementation.
# Keep it object-only: it is a frame-service provider audit, not an Android runtime.
if(ANDROID)
    add_library(iw3_sp_actor_corpse_full_compile OBJECT
        "${IW3_ENGINE_SOURCE_ROOT}/game/actor_corpse.cpp")
    target_include_directories(iw3_sp_actor_corpse_full_compile PRIVATE
        "${CMAKE_CURRENT_SOURCE_DIR}"
        "${IW3_ENGINE_SOURCE_ROOT}"
        "${IW3_ENGINE_SOURCE_ROOT}/client"
        "${IW3_ENGINE_SOURCE_ROOT}/qcommon"
        "${IW3_ENGINE_SOURCE_ROOT}/universal"
        "${IW3_ENGINE_SOURCE_ROOT}/gfx_d3d"
        "${IW3_ENGINE_SOURCE_ROOT}/game"
        "${IW3_ENGINE_SOURCE_ROOT}/cgame"
        "${IW3_ENGINE_SOURCE_ROOT}/bgame"
        "${IW3_ENGINE_SOURCE_ROOT}/xanim"
        "${IW3_ENGINE_SOURCE_ROOT}/../deps")
    target_compile_definitions(iw3_sp_actor_corpse_full_compile PRIVATE KISAK_SP=1)
    target_compile_options(iw3_sp_actor_corpse_full_compile PRIVATE
        -fms-extensions -Wall -Wextra -fsigned-char
        -frounding-math -fno-fast-math)
endif()

# Compile the complete original BGame dvar-registration translation unit for Android ARM64.
# Unlike the earlier four-dvar source slice, this compiles the authentic bg_misc.cpp
# in full. It remains OBJECT-only until the complete BGame/client runtime is linked.
if(ANDROID)
    add_library(iw3_sp_bgame_misc_full_compile OBJECT
        "${IW3_ENGINE_SOURCE_ROOT}/bgame/bg_misc.cpp")
    target_include_directories(iw3_sp_bgame_misc_full_compile PRIVATE
        "${CMAKE_CURRENT_SOURCE_DIR}"
        "${IW3_ENGINE_SOURCE_ROOT}"
        "${IW3_ENGINE_SOURCE_ROOT}/client"
        "${IW3_ENGINE_SOURCE_ROOT}/qcommon"
        "${IW3_ENGINE_SOURCE_ROOT}/universal"
        "${IW3_ENGINE_SOURCE_ROOT}/ui"
        "${IW3_ENGINE_SOURCE_ROOT}/devgui"
        "${IW3_ENGINE_SOURCE_ROOT}/gfx_d3d"
        "${IW3_ENGINE_SOURCE_ROOT}/game"
        "${IW3_ENGINE_SOURCE_ROOT}/cgame"
        "${IW3_ENGINE_SOURCE_ROOT}/server"
        "${IW3_ENGINE_SOURCE_ROOT}/bgame"
        "${IW3_ENGINE_SOURCE_ROOT}/sound"
        "${IW3_ENGINE_SOURCE_ROOT}/script"
        "${IW3_ENGINE_SOURCE_ROOT}/xanim"
        "${IW3_ENGINE_SOURCE_ROOT}/database"
        "${IW3_ENGINE_SOURCE_ROOT}/aim_assist"
        "${IW3_ENGINE_SOURCE_ROOT}/win32"
        "${IW3_ENGINE_SOURCE_ROOT}/../deps")
    target_compile_definitions(iw3_sp_bgame_misc_full_compile PRIVATE
        KISAK_SP=1 KISAK_OPENAL=1)
    target_compile_options(iw3_sp_bgame_misc_full_compile PRIVATE
        -fms-extensions -Wall -Wextra -fsigned-char
        -frounding-math -fno-fast-math)
endif()

# Compile the complete original Com_Init/Com_Frame translation unit for Android
# ARM64. This is the core bootstrap TU, not an extracted body or test harness.
# Keep it object-only until its real platform/service graph and renderer are
# linked; it is intentionally NOT linked into the JNI diagnostic APK.
if(ANDROID)
    add_library(iw3_sp_common_full_compile OBJECT
        "${IW3_ENGINE_SOURCE_ROOT}/qcommon/common.cpp")
    target_include_directories(iw3_sp_common_full_compile PRIVATE
        "${CMAKE_CURRENT_SOURCE_DIR}/common_compat"
        "${CMAKE_CURRENT_SOURCE_DIR}"
        "${IW3_ENGINE_SOURCE_ROOT}"
        "${IW3_ENGINE_SOURCE_ROOT}/../deps")
    target_compile_definitions(iw3_sp_common_full_compile PRIVATE
        KISAK_SP=1 KISAK_OPENAL=1 IW3_ANDROID_DISABLE_SCRIPT_DEBUGGER=1
        IW3_ANDROID_COMMON_HEADER_ONLY_OPENAL=1)
    target_compile_options(iw3_sp_common_full_compile PRIVATE
        -fms-extensions -Wall -Wextra -fsigned-char
        -frounding-math -fno-fast-math)
endif()

# Compile the complete original command-system translation unit for Android ARM64.
# This includes the real Cmd_Init, command registry/dispatch, Cbuf and tokenizer
# implementations. It is an explicit OBJECT-only portability gate, excluded
# from default JNI/math builds until real OpenAL headers are supplied.
# The dedicated ARM64 workflow compiles this same authentic source with real
# OpenAL Soft API headers. No command runtime is initialized by this target.
if(ANDROID)
    add_library(iw3_sp_cmd_full_compile OBJECT EXCLUDE_FROM_ALL
        "${IW3_ENGINE_SOURCE_ROOT}/qcommon/cmd.cpp")
    target_include_directories(iw3_sp_cmd_full_compile PRIVATE
        "${CMAKE_CURRENT_SOURCE_DIR}"
        "${IW3_ENGINE_SOURCE_ROOT}"
        "${IW3_ENGINE_SOURCE_ROOT}/qcommon"
        "${IW3_ENGINE_SOURCE_ROOT}/universal"
        "${IW3_ENGINE_SOURCE_ROOT}/database"
        "${IW3_ENGINE_SOURCE_ROOT}/win32"
        "${IW3_ENGINE_SOURCE_ROOT}/script"
        "${IW3_ENGINE_SOURCE_ROOT}/server"
        "${IW3_ENGINE_SOURCE_ROOT}/game"
        "${IW3_ENGINE_SOURCE_ROOT}/bgame"
        "${IW3_ENGINE_SOURCE_ROOT}/cgame"
        "${IW3_ENGINE_SOURCE_ROOT}/client"
        "${IW3_ENGINE_SOURCE_ROOT}/ui"
        "${IW3_ENGINE_SOURCE_ROOT}/sound"
        "${IW3_ENGINE_SOURCE_ROOT}/gfx_d3d"
        "${IW3_ENGINE_SOURCE_ROOT}/devgui"
        "${IW3_ENGINE_SOURCE_ROOT}/xanim"
        "${IW3_ENGINE_SOURCE_ROOT}/aim_assist"
        "${IW3_ENGINE_SOURCE_ROOT}/../deps")
    if(IW3_OPENAL_HEADERS_ROOT)
        if(NOT EXISTS "${IW3_OPENAL_HEADERS_ROOT}/AL/al.h" OR
           NOT EXISTS "${IW3_OPENAL_HEADERS_ROOT}/AL/alc.h" OR
           NOT EXISTS "${IW3_OPENAL_HEADERS_ROOT}/AL/efx.h")
            message(FATAL_ERROR "Original IW3 command target requires real OpenAL API headers")
        endif()
        target_include_directories(iw3_sp_cmd_full_compile PRIVATE
            "${IW3_OPENAL_HEADERS_ROOT}")
    endif()
    target_compile_definitions(iw3_sp_cmd_full_compile PRIVATE
        KISAK_SP=1 KISAK_OPENAL=1)
    target_compile_options(iw3_sp_cmd_full_compile PRIVATE
        -fms-extensions -Wall -Wextra -fsigned-char
        -frounding-math -fno-fast-math)
endif()

# Compile an ABI fixture against the original script parser header. These
# pointer-bearing structs are live runtime bookkeeping, not serialized assets.
# This gate also protects TRACK_scr_parser from reverting to Win32 byte counts.
if(ANDROID)
    add_library(iw3_sp_script_parser_layout_full_compile OBJECT
        "${CMAKE_CURRENT_SOURCE_DIR}/script_parser_layout_native_test.cpp")
    target_include_directories(iw3_sp_script_parser_layout_full_compile PRIVATE
        "${CMAKE_CURRENT_SOURCE_DIR}"
        "${IW3_ENGINE_SOURCE_ROOT}"
        "${IW3_ENGINE_SOURCE_ROOT}/qcommon"
        "${IW3_ENGINE_SOURCE_ROOT}/universal"
        "${IW3_ENGINE_SOURCE_ROOT}/script"
        "${IW3_ENGINE_SOURCE_ROOT}/../deps")
    target_compile_definitions(iw3_sp_script_parser_layout_full_compile PRIVATE KISAK_SP=1)
    target_compile_options(iw3_sp_script_parser_layout_full_compile PRIVATE
        -fms-extensions -Wall -Wextra -fsigned-char -frounding-math -fno-fast-math)
endif()

# Compile the complete original IW3 SP script VM translation unit for Android
# ARM64. This is a portability gate only: the VM's real scheduler/services are
# not linked into the JNI diagnostic package or claimed as running gameplay.
if(ANDROID)
    add_library(iw3_sp_script_vm_full_compile OBJECT
        "${IW3_ENGINE_SOURCE_ROOT}/script/scr_vm.cpp")
    target_include_directories(iw3_sp_script_vm_full_compile PRIVATE
        "${CMAKE_CURRENT_SOURCE_DIR}"
        "${IW3_ENGINE_SOURCE_ROOT}"
        "${IW3_ENGINE_SOURCE_ROOT}/qcommon"
        "${IW3_ENGINE_SOURCE_ROOT}/universal"
        "${IW3_ENGINE_SOURCE_ROOT}/script"
        "${IW3_ENGINE_SOURCE_ROOT}/game"
        "${IW3_ENGINE_SOURCE_ROOT}/bgame"
        "${IW3_ENGINE_SOURCE_ROOT}/database"
        "${IW3_ENGINE_SOURCE_ROOT}/client"
        "${IW3_ENGINE_SOURCE_ROOT}/gfx_d3d"
        "${IW3_ENGINE_SOURCE_ROOT}/ui"
        "${IW3_ENGINE_SOURCE_ROOT}/server"
        "${IW3_ENGINE_SOURCE_ROOT}/devgui"
        "${IW3_ENGINE_SOURCE_ROOT}/sound"
        "${IW3_ENGINE_SOURCE_ROOT}/aim_assist"
        "${IW3_ENGINE_SOURCE_ROOT}/win32"
        "${IW3_ENGINE_SOURCE_ROOT}/../deps")
    target_compile_definitions(iw3_sp_script_vm_full_compile PRIVATE KISAK_SP=1)
    target_compile_options(iw3_sp_script_vm_full_compile PRIVATE
        -fms-extensions -fno-inline -ferror-limit=0 -Wall -Wextra -fsigned-char
        -frounding-math -fno-fast-math)
endif()

# Compile the authentic parser/session routines when the source-audit workflow
# supplies the extracted file. The JNI diagnostic shares this CMakeLists but does
# not stage/link this audit archive, so absence is not a configure-time failure.
if(IW3_EXTRACTED_Q_PARSE)
    if(NOT EXISTS "${IW3_EXTRACTED_Q_PARSE}")
        message(FATAL_ERROR "Configured original KisakCOD q_parse.cpp extraction path does not exist")
    endif()
    add_library(iw3_sp_q_parse STATIC "${IW3_EXTRACTED_Q_PARSE}")
    target_include_directories(iw3_sp_q_parse PRIVATE
        "${CMAKE_CURRENT_SOURCE_DIR}"
        "${IW3_REAL_HEADER_ROOT}"
        "${IW3_ENGINE_SOURCE_ROOT}"
        "${IW3_ENGINE_SOURCE_ROOT}/qcommon"
        "${IW3_ENGINE_SOURCE_ROOT}/../deps")
    target_compile_definitions(iw3_sp_q_parse PRIVATE KISAK_SP=1)
    target_compile_options(iw3_sp_q_parse PRIVATE
        -Wall -Wextra -fsigned-char -frounding-math -fno-fast-math)

    if(NOT ANDROID)
        add_executable(iw3_q_parse_native_test parser_native_test.cpp)
        target_include_directories(iw3_q_parse_native_test PRIVATE
            "${CMAKE_CURRENT_SOURCE_DIR}"
            "${IW3_REAL_HEADER_ROOT}"
            "${IW3_ENGINE_SOURCE_ROOT}"
            "${IW3_ENGINE_SOURCE_ROOT}/qcommon"
            "${IW3_ENGINE_SOURCE_ROOT}/../deps")
        target_compile_definitions(iw3_q_parse_native_test PRIVATE KISAK_SP=1)
        target_link_libraries(iw3_q_parse_native_test PRIVATE iw3_sp_q_parse)
        target_compile_options(iw3_q_parse_native_test PRIVATE -UNDEBUG -Wall -Wextra)
        add_test(NAME iw3_original_q_parse_host_runtime COMMAND iw3_q_parse_native_test)
    endif()
endif()

# Compile the original cmd_args storage declaration and Cmd_Argc/Cmd_Argv
# accessors extracted from cmd.cpp for the filesystem-startup dependency audit.
# The original tokenizer core is staged in a separate archive below; command
# initialization/registration/dispatch are still absent. Neither archive is
# linked into the JNI diagnostic APK or treated as a complete command runtime.
if(IW3_EXTRACTED_CMD_ARGS)
    if(NOT EXISTS "${IW3_EXTRACTED_CMD_ARGS}")
        message(FATAL_ERROR "Configured original Cmd_Argc/Cmd_Argv extraction path does not exist")
    endif()
    add_library(iw3_sp_cmd_args STATIC "${IW3_EXTRACTED_CMD_ARGS}")
    target_include_directories(iw3_sp_cmd_args PRIVATE
        "${CMAKE_CURRENT_SOURCE_DIR}"
        "${IW3_REAL_HEADER_ROOT}"
        "${IW3_ENGINE_SOURCE_ROOT}"
        "${IW3_ENGINE_SOURCE_ROOT}/qcommon"
        "${IW3_ENGINE_SOURCE_ROOT}/../deps")
    target_compile_definitions(iw3_sp_cmd_args PRIVATE KISAK_SP=1)
    target_compile_options(iw3_sp_cmd_args PRIVATE
        -Wall -Wextra -fsigned-char -frounding-math -fno-fast-math)

    if(NOT ANDROID)
        add_executable(iw3_cmd_args_native_test cmd_args_native_test.cpp)
        target_include_directories(iw3_cmd_args_native_test PRIVATE
            "${CMAKE_CURRENT_SOURCE_DIR}"
            "${IW3_REAL_HEADER_ROOT}"
            "${IW3_ENGINE_SOURCE_ROOT}"
            "${IW3_ENGINE_SOURCE_ROOT}/qcommon"
            "${IW3_ENGINE_SOURCE_ROOT}/../deps")
        target_compile_definitions(iw3_cmd_args_native_test PRIVATE KISAK_SP=1)
        target_link_libraries(iw3_cmd_args_native_test PRIVATE iw3_sp_cmd_args)
        target_compile_options(iw3_cmd_args_native_test PRIVATE -UNDEBUG -Wall -Wextra)
        add_test(NAME iw3_original_cmd_arg_accessors_host_runtime
                 COMMAND iw3_cmd_args_native_test)
    endif()
endif()

# Stage the exact original command tokenizer core and its private pool state.
# This resolves the FS startup command-tokenization link edge without pulling
# the Win32-bound command dispatcher/registration code into Android.
if(IW3_EXTRACTED_CMD_TOKENIZER)
    if(NOT EXISTS "${IW3_EXTRACTED_CMD_TOKENIZER}")
        message(FATAL_ERROR "Original command tokenizer extraction path does not exist")
    endif()
    add_library(iw3_sp_cmd_tokenizer STATIC "${IW3_EXTRACTED_CMD_TOKENIZER}")
    target_include_directories(iw3_sp_cmd_tokenizer PRIVATE
        "${CMAKE_CURRENT_SOURCE_DIR}"
        "${IW3_REAL_HEADER_ROOT}"
        "${IW3_ENGINE_SOURCE_ROOT}"
        "${IW3_ENGINE_SOURCE_ROOT}/qcommon"
        "${IW3_ENGINE_SOURCE_ROOT}/../deps")
    target_compile_definitions(iw3_sp_cmd_tokenizer PRIVATE KISAK_SP=1)
    target_compile_options(iw3_sp_cmd_tokenizer PRIVATE
        -ffunction-sections -fdata-sections
        -Wall -Wextra -fsigned-char -frounding-math -fno-fast-math)
endif()

if(IW3_EXTRACTED_COM_PRINT_WARNING)
    if(NOT EXISTS "${IW3_EXTRACTED_COM_PRINT_WARNING}")
        message(FATAL_ERROR
            "Original KisakCOD Com_PrintWarning extraction path does not exist")
    endif()
    add_library(iw3_sp_com_print_warning STATIC
        "${IW3_EXTRACTED_COM_PRINT_WARNING}"
        "${CMAKE_CURRENT_SOURCE_DIR}/iw3_android_com_print_message.cpp")
    target_include_directories(iw3_sp_com_print_warning PRIVATE
        "${CMAKE_CURRENT_SOURCE_DIR}"
        "${IW3_REAL_HEADER_ROOT}"
        "${IW3_ENGINE_SOURCE_ROOT}"
        "${IW3_ENGINE_SOURCE_ROOT}/qcommon"
        "${IW3_ENGINE_SOURCE_ROOT}/../deps")
    target_compile_definitions(iw3_sp_com_print_warning PRIVATE KISAK_SP=1)
    target_compile_options(iw3_sp_com_print_warning PRIVATE
        -Wall -Wextra -fsigned-char -frounding-math -fno-fast-math)
    if(ANDROID)
        target_link_libraries(iw3_sp_com_print_warning PUBLIC log)
    endif()
endif()

if(IW3_EXTRACTED_COM_PRINT_PRINTF)
    if(NOT EXISTS "${IW3_EXTRACTED_COM_PRINT_PRINTF}")
        message(FATAL_ERROR
            "Original KisakCOD Com_Printf extraction path does not exist")
    endif()
    add_library(iw3_sp_com_print_printf STATIC "${IW3_EXTRACTED_COM_PRINT_PRINTF}")
    target_include_directories(iw3_sp_com_print_printf PRIVATE
        "${CMAKE_CURRENT_SOURCE_DIR}"
        "${IW3_REAL_HEADER_ROOT}"
        "${IW3_ENGINE_SOURCE_ROOT}"
        "${IW3_ENGINE_SOURCE_ROOT}/qcommon"
        "${IW3_ENGINE_SOURCE_ROOT}/../deps")
    target_compile_definitions(iw3_sp_com_print_printf PRIVATE KISAK_SP=1)
    target_compile_options(iw3_sp_com_print_printf PRIVATE
        -Wall -Wextra -fsigned-char -frounding-math -fno-fast-math)
endif()

add_library(iw3_sp_frame STATIC "${IW3_ENGINE_SOURCE_ROOT}/game/g_runframe.cpp")
target_include_directories(iw3_sp_frame PRIVATE "${IW3_ENGINE_SOURCE_ROOT}")
target_compile_definitions(iw3_sp_frame PRIVATE KISAK_SP=1)
target_compile_options(iw3_sp_frame PRIVATE -fsigned-char -frounding-math -fno-fast-math)

# Compile the exact original FS_LoadZipFile function with native-width engine
# structures. This archive deliberately retains unresolved allocator/checksum
# services and is not linked into the JNI diagnostic/game target.
add_library(iw3_sp_iwd_mount STATIC "${IW3_EXTRACTED_IWD_MOUNT}")
target_include_directories(iw3_sp_iwd_mount PRIVATE
    "${CMAKE_CURRENT_SOURCE_DIR}"
    "${IW3_REAL_HEADER_ROOT}"
    "${IW3_ENGINE_SOURCE_ROOT}"
    "${IW3_ENGINE_SOURCE_ROOT}/qcommon"
    "${IW3_ENGINE_SOURCE_ROOT}/../deps")
target_compile_definitions(iw3_sp_iwd_mount PRIVATE KISAK_SP=1)
target_compile_options(iw3_sp_iwd_mount PRIVATE
    -Wall -Wextra -fsigned-char -frounding-math -fno-fast-math)

# Separate ARM64 audit archives for the authentic IWD language/sort/allocator
# helpers and ZIP parser. They are not added to the diagnostic APK; they let
# the relocatable link audit resolve real dependencies without hiding the
# remaining platform and language-service edges.
if(NOT IW3_EXTRACTED_IWD_SERVICES OR NOT EXISTS "${IW3_EXTRACTED_IWD_SERVICES}")
    message(FATAL_ERROR "Original IWD language/sort/allocator service extraction required")
endif()
add_library(iw3_sp_iwd_services STATIC "${IW3_EXTRACTED_IWD_SERVICES}" "${IW3_EXTRACTED_IWD_NAMES}")
target_include_directories(iw3_sp_iwd_services PRIVATE
    "${CMAKE_CURRENT_SOURCE_DIR}"
    "${IW3_REAL_HEADER_ROOT}"
    "${IW3_ENGINE_SOURCE_ROOT}"
    "${IW3_ENGINE_SOURCE_ROOT}/qcommon"
    "${IW3_ENGINE_SOURCE_ROOT}/../deps")
target_compile_definitions(iw3_sp_iwd_services PRIVATE KISAK_SP=1)
target_compile_options(iw3_sp_iwd_services PRIVATE
    -Wall -Wextra -fsigned-char -frounding-math -fno-fast-math)

if(NOT IW3_EXTRACTED_UNZIP OR NOT EXISTS "${IW3_EXTRACTED_UNZIP}")
    message(FATAL_ERROR "Original ZIP parser extraction required for IWD link audit")
endif()
add_library(iw3_sp_unzip STATIC "${IW3_EXTRACTED_UNZIP}")
target_include_directories(iw3_sp_unzip PRIVATE
    "${CMAKE_CURRENT_SOURCE_DIR}"
    "${IW3_REAL_HEADER_ROOT}"
    "${IW3_ENGINE_SOURCE_ROOT}"
    "${IW3_ENGINE_SOURCE_ROOT}/qcommon"
    "${IW3_ENGINE_SOURCE_ROOT}/../deps")
target_compile_definitions(iw3_sp_unzip PRIVATE KISAK_SP=1)
target_compile_options(iw3_sp_unzip PRIVATE
    -Wall -Wextra -fsigned-char -frounding-math -fno-fast-math)

if(IW3_EXTRACTED_IWD_DIRECTORY_SERVICES)
    # Link the original IWD directory-scanner helpers with the Android rooted
    # directory adapter. The full AddIwdFiles/AddGameDirectory bodies remain in
    # the startup archive, avoiding duplicate definitions. This archive is for
    # dependency auditing only and is not linked into the diagnostic APK.
    add_library(iw3_sp_iwd_directory_services STATIC
        "${IW3_EXTRACTED_IWD_DIRECTORY_SERVICES}"
        "${CMAKE_CURRENT_SOURCE_DIR}/iw3_android_iwd_directory_io.cpp"
        "${CMAKE_CURRENT_SOURCE_DIR}/iw3_android_iwd_lookup_io.cpp"
        "${CMAKE_CURRENT_SOURCE_DIR}/iw3_android_unzip_io.cpp"
        "${CMAKE_CURRENT_SOURCE_DIR}/iw3_android_platform.cpp")
    target_include_directories(iw3_sp_iwd_directory_services PRIVATE
        "${CMAKE_CURRENT_SOURCE_DIR}"
        "${IW3_REAL_HEADER_ROOT}"
        "${IW3_ENGINE_SOURCE_ROOT}"
        "${IW3_ENGINE_SOURCE_ROOT}/qcommon"
        "${IW3_ENGINE_SOURCE_ROOT}/../deps")
    target_compile_definitions(iw3_sp_iwd_directory_services PRIVATE
        KISAK_SP=1 IW3_IWD_DIRECTORY_LINK_AUDIT=1)
    target_compile_options(iw3_sp_iwd_directory_services PRIVATE
        -Wall -Wextra -fsigned-char -frounding-math -fno-fast-math)

endif()

# Compile the authentic language initializer and registry helpers from the
# original StringEd hooks. This archive is consumed by the combined ARM64
# startup/Dvar/IWD audit; it is deliberately not linked into the JNI diagnostic.
if(IW3_EXTRACTED_LANGUAGE)
    if(NOT EXISTS "${IW3_EXTRACTED_LANGUAGE}")
        message(FATAL_ERROR "Original KisakCOD language source extraction path does not exist")
    endif()
    add_library(iw3_sp_language STATIC "${IW3_EXTRACTED_LANGUAGE}")
    target_include_directories(iw3_sp_language PRIVATE
        "${CMAKE_CURRENT_SOURCE_DIR}"
        "${IW3_REAL_HEADER_ROOT}"
        "${IW3_ENGINE_SOURCE_ROOT}"
        "${IW3_ENGINE_SOURCE_ROOT}/qcommon"
        "${IW3_ENGINE_SOURCE_ROOT}/../deps")
    target_compile_definitions(iw3_sp_language PRIVATE KISAK_SP=1)
    target_compile_options(iw3_sp_language PRIVATE
        -Wall -Wextra -fsigned-char -frounding-math -fno-fast-math)

    # Compile only the original StringEd package-loader bodies needed by
    # FS_InitFilesystem -> SEH_Init_StringEd / SEH_UpdateLanguageInfo. The
    # upstream TU also imports D3D database entry points; the source-hash-checked
    # slice omits those unrelated functions without replacing the loader logic.
    if(NOT IW3_EXTRACTED_STRINGED_INGAME OR NOT EXISTS "${IW3_EXTRACTED_STRINGED_INGAME}")
        message(FATAL_ERROR "Original KisakCOD StringEd loader extraction required")
    endif()
    add_library(iw3_sp_stringed_ingame STATIC
        "${IW3_EXTRACTED_STRINGED_INGAME}")
    target_include_directories(iw3_sp_stringed_ingame PRIVATE
        "${CMAKE_CURRENT_SOURCE_DIR}"
        "${IW3_REAL_HEADER_ROOT}"
        "${IW3_ENGINE_SOURCE_ROOT}"
        "${IW3_ENGINE_SOURCE_ROOT}/qcommon"
        "${IW3_ENGINE_SOURCE_ROOT}/../deps")
    target_compile_definitions(iw3_sp_stringed_ingame PRIVATE KISAK_SP=1)
    target_compile_options(iw3_sp_stringed_ingame PRIVATE
        -ffunction-sections -fdata-sections -Wall -Wextra
        -fsigned-char -frounding-math -fno-fast-math)

    if(IW3_EXTRACTED_HUNK_USER)
        add_library(iw3_sp_hunk_user STATIC
            "${IW3_EXTRACTED_HUNK_USER}"
            "${CMAKE_CURRENT_SOURCE_DIR}/iw3_android_hunk_virtual.cpp")
        target_include_directories(iw3_sp_hunk_user PRIVATE
            "${CMAKE_CURRENT_SOURCE_DIR}"
            "${IW3_REAL_HEADER_ROOT}"
            "${IW3_ENGINE_SOURCE_ROOT}"
            "${IW3_ENGINE_SOURCE_ROOT}/qcommon"
            "${IW3_ENGINE_SOURCE_ROOT}/../deps")
        target_compile_definitions(iw3_sp_hunk_user PRIVATE KISAK_SP=1)
        target_compile_options(iw3_sp_hunk_user PRIVATE
            -ffunction-sections -fdata-sections -Wall -Wextra
            -fsigned-char -frounding-math -fno-fast-math)

        if(NOT ANDROID)
            add_executable(iw3_hunk_user_native_test
                "${CMAKE_CURRENT_SOURCE_DIR}/tests/hunk_user_native_test.cpp")
            target_include_directories(iw3_hunk_user_native_test PRIVATE
                "${CMAKE_CURRENT_SOURCE_DIR}"
                "${IW3_REAL_HEADER_ROOT}"
                "${IW3_ENGINE_SOURCE_ROOT}"
                "${IW3_ENGINE_SOURCE_ROOT}/qcommon"
                "${IW3_ENGINE_SOURCE_ROOT}/../deps")
            target_link_libraries(iw3_hunk_user_native_test PRIVATE iw3_sp_hunk_user)
            target_compile_options(iw3_hunk_user_native_test PRIVATE
                -UNDEBUG -ffunction-sections -fdata-sections -Wall -Wextra)
            target_link_options(iw3_hunk_user_native_test PRIVATE -Wl,--gc-sections)
            add_test(NAME iw3_hunk_user_native_test COMMAND iw3_hunk_user_native_test)
        endif()
    endif()

    if(NOT ANDROID)
        add_executable(iw3_language_native_test
            "${CMAKE_CURRENT_SOURCE_DIR}/language_native_test.cpp"
            "${IW3_EXTRACTED_LANGUAGE}")
        target_include_directories(iw3_language_native_test PRIVATE
            "${CMAKE_CURRENT_SOURCE_DIR}"
            "${IW3_REAL_HEADER_ROOT}"
            "${IW3_ENGINE_SOURCE_ROOT}"
            "${IW3_ENGINE_SOURCE_ROOT}/qcommon"
            "${IW3_ENGINE_SOURCE_ROOT}/../deps")
        target_compile_options(iw3_language_native_test PRIVATE
            -UNDEBUG -ffunction-sections -fdata-sections -Wall -Wextra)
        target_link_options(iw3_language_native_test PRIVATE -Wl,--gc-sections)
        add_test(NAME iw3_original_language_registry_and_lookup
                 COMMAND iw3_language_native_test)
    endif()
endif()

# The vendored q_shared.h declares the engine wildcard service, but the
# source slice has no provider. This portable id Tech 3-compatible provider is
# linked only as an engine service; it is not a filesystem or gameplay stand-in.
add_library(iw3_sp_filter STATIC "${CMAKE_CURRENT_SOURCE_DIR}/iw3_android_filter.cpp")
target_include_directories(iw3_sp_filter PRIVATE
    "${CMAKE_CURRENT_SOURCE_DIR}"
    "${IW3_ENGINE_SOURCE_ROOT}"
    "${IW3_ENGINE_SOURCE_ROOT}/universal"
    "${IW3_ENGINE_SOURCE_ROOT}/qcommon"
    "${IW3_ENGINE_SOURCE_ROOT}/../deps")
target_compile_definitions(iw3_sp_filter PRIVATE KISAK_SP=1)
target_compile_options(iw3_sp_filter PRIVATE
    -Wall -Wextra -fsigned-char -frounding-math -fno-fast-math)

# Stage original q_shared string/format helpers as a separate dependency provider.
# This archive is for the native source/link audit only and is not linked into
# the JNI diagnostic APK unless a future runtime target explicitly consumes it.
if(IW3_EXTRACTED_Q_SHARED_STRINGS)
    if(NOT EXISTS "${IW3_EXTRACTED_Q_SHARED_STRINGS}")
        message(FATAL_ERROR "Original q_shared string service extraction path does not exist")
    endif()
    add_library(iw3_sp_q_shared_strings STATIC "${IW3_EXTRACTED_Q_SHARED_STRINGS}")
    target_include_directories(iw3_sp_q_shared_strings PRIVATE
        "${CMAKE_CURRENT_SOURCE_DIR}"
        "${IW3_REAL_HEADER_ROOT}"
        "${IW3_ENGINE_SOURCE_ROOT}"
        "${IW3_ENGINE_SOURCE_ROOT}/qcommon"
        "${IW3_ENGINE_SOURCE_ROOT}/../deps")
    target_compile_definitions(iw3_sp_q_shared_strings PRIVATE KISAK_SP=1)
    target_compile_options(iw3_sp_q_shared_strings PRIVATE
        -Wall -Wextra -fsigned-char -frounding-math -fno-fast-math
        -ffunction-sections -fdata-sections)
endif()

# Compile the complete original location-filter function with native-width
# searchpath_s size/alignment. Its real Hunk/list services remain unresolved in
# this audit archive; it is intentionally not linked into the JNI diagnostic.
if(IW3_EXTRACTED_FILTERED_FILES)
    if(NOT EXISTS "${IW3_EXTRACTED_FILTERED_FILES}")
        message(FATAL_ERROR "Original FS_ListFilteredFilesInLocation source extraction required")
    endif()
    add_library(iw3_sp_filtered_files STATIC "${IW3_EXTRACTED_FILTERED_FILES}")
    target_include_directories(iw3_sp_filtered_files PRIVATE
        "${CMAKE_CURRENT_SOURCE_DIR}"
        "${IW3_REAL_HEADER_ROOT}"
        "${IW3_ENGINE_SOURCE_ROOT}"
        "${IW3_ENGINE_SOURCE_ROOT}/qcommon"
        "${IW3_ENGINE_SOURCE_ROOT}/../deps")
    target_compile_definitions(iw3_sp_filtered_files PRIVATE KISAK_SP=1)
    target_compile_options(iw3_sp_filtered_files PRIVATE
        -Wall -Wextra -fsigned-char -frounding-math -fno-fast-math)
endif()

# Compile the verbatim original read helpers into a separate ABI/dependency
# archive with the same engine-owned native-width handle table used by
# com_files.cpp. Other platform/service references remain visible in this audit.
add_library(iw3_sp_fs_read STATIC
    "${IW3_EXTRACTED_FS_READ}"
    "${IW3_ENGINE_SOURCE_ROOT}/universal/com_files_handle_table.cpp"
    "${IW3_ENGINE_SOURCE_ROOT}/universal/com_files_state.cpp")
target_include_directories(iw3_sp_fs_read PRIVATE
    "${CMAKE_CURRENT_SOURCE_DIR}"
    "${IW3_REAL_HEADER_ROOT}"
    "${IW3_ENGINE_SOURCE_ROOT}"
    "${IW3_ENGINE_SOURCE_ROOT}/qcommon"
    "${IW3_ENGINE_SOURCE_ROOT}/../deps")
target_compile_definitions(iw3_sp_fs_read PRIVATE KISAK_SP=1)
target_compile_options(iw3_sp_fs_read PRIVATE
    -Wall -Wextra -fsigned-char -frounding-math -fno-fast-math)

if(IW3_EXTRACTED_FS_READFILE)
    if(NOT EXISTS "${IW3_EXTRACTED_FS_READFILE}")
        message(FATAL_ERROR "Original FS_ReadFile lifecycle extraction path does not exist")
    endif()
    if(NOT IW3_EXTRACTED_COM_LOGFILE_OPEN OR NOT EXISTS "${IW3_EXTRACTED_COM_LOGFILE_OPEN}")
        message(FATAL_ERROR "Original Com_LogFileOpen state/query extraction is required")
    endif()
    add_library(iw3_sp_fs_readfile STATIC
        "${IW3_EXTRACTED_FS_READFILE}"
        "${IW3_EXTRACTED_COM_LOGFILE_OPEN}"
        "${CMAKE_CURRENT_SOURCE_DIR}/iw3_android_fs_lock_io.cpp")
    target_include_directories(iw3_sp_fs_readfile PRIVATE
        "${CMAKE_CURRENT_SOURCE_DIR}"
        "${IW3_REAL_HEADER_ROOT}"
        "${IW3_ENGINE_SOURCE_ROOT}"
        "${IW3_ENGINE_SOURCE_ROOT}/qcommon"
        "${IW3_ENGINE_SOURCE_ROOT}/../deps")
    target_compile_definitions(iw3_sp_fs_readfile PRIVATE KISAK_SP=1)
    target_compile_options(iw3_sp_fs_readfile PRIVATE
        -Wall -Wextra -fsigned-char -frounding-math -fno-fast-math)
endif()

# Compile the authentic Hunk temporary allocator bodies after correcting their
# original 32-bit pointer masks and sharing the engine-owned Hunk state. This
# archive is used only by the combined ARM64 dependency audit, not the JNI APK.
if(IW3_EXTRACTED_HUNK_TEMP)
    if(NOT EXISTS "${IW3_EXTRACTED_HUNK_TEMP}")
        message(FATAL_ERROR "Original Hunk temporary allocator extraction path does not exist")
    endif()
    add_library(iw3_sp_hunk_temp STATIC
        "${IW3_EXTRACTED_HUNK_TEMP}"
        "${IW3_ENGINE_SOURCE_ROOT}/universal/com_memory_state.cpp")
    target_include_directories(iw3_sp_hunk_temp PRIVATE
        "${CMAKE_CURRENT_SOURCE_DIR}"
        "${IW3_REAL_HEADER_ROOT}"
        "${IW3_ENGINE_SOURCE_ROOT}"
        "${IW3_ENGINE_SOURCE_ROOT}/qcommon"
        "${IW3_ENGINE_SOURCE_ROOT}/../deps")
    target_compile_definitions(iw3_sp_hunk_temp PRIVATE KISAK_SP=1)
    target_compile_options(iw3_sp_hunk_temp PRIVATE
        -Wall -Wextra -fsigned-char -frounding-math -fno-fast-math)
endif()

# Compile the corrected original dvar string/enum pointer paths and callback ABI
# as an LP64 source audit. This archive is not linked into the JNI diagnostic.
if(IW3_EXTRACTED_DVAR_POINTER_ABI)
    if(NOT EXISTS "${IW3_EXTRACTED_DVAR_POINTER_ABI}")
        message(FATAL_ERROR "Authentic corrected KisakCOD dvar pointer source required")
    endif()
    add_library(iw3_sp_dvar_pointer_abi STATIC "${IW3_EXTRACTED_DVAR_POINTER_ABI}")
    target_include_directories(iw3_sp_dvar_pointer_abi PRIVATE
        "${CMAKE_CURRENT_SOURCE_DIR}"
        "${IW3_REAL_HEADER_ROOT}"
        "${IW3_ENGINE_SOURCE_ROOT}"
        "${IW3_ENGINE_SOURCE_ROOT}/qcommon"
        "${IW3_ENGINE_SOURCE_ROOT}/../deps")
    target_compile_definitions(iw3_sp_dvar_pointer_abi PRIVATE KISAK_SP=1)
    target_compile_options(iw3_sp_dvar_pointer_abi PRIVATE
        -Wall -Wextra -fsigned-char -frounding-math -fno-fast-math)
endif()

# The diagnostic shared library compiles exact original handle allocator/open/
# read/close bodies against the shared engine-owned native-width fsh table. The
# IWD fixture opens one member twice to exercise the original unzReOpen clone
# branch and verifies both original close paths. The full com_files.cpp runtime
# and its remaining platform services are not linked into this diagnostic.
add_library(iw3_sp_math SHARED
    "${IW3_ENGINE_SOURCE_ROOT}/universal/com_files_handle_table.cpp"
    "${IW3_ENGINE_SOURCE_ROOT}/universal/com_files_state.cpp"
    "${IW3_EXTRACTED_FS_READ}"
    "${CMAKE_CURRENT_SOURCE_DIR}/iw3_android_fs_read_io.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/iw3_android_fs_startup_io.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/iw3_android_directory_has_contents.cpp"
    "${IW3_EXTRACTED_MATH}"
    "${IW3_EXTRACTED_SURFACE}"
    "${IW3_EXTRACTED_CONSTANTS}"
    "${IW3_EXTRACTED_FRAME_MEMCPY}"
    "${IW3_EXTRACTED_POOL}"
    "${IW3_EXTRACTED_HITLOC}"
    "${IW3_EXTRACTED_IWD_NAMES}"
    "${IW3_EXTRACTED_IWD_SERVICES}"
    "${IW3_EXTRACTED_IWD_MOUNT}"
    "${IW3_EXTRACTED_IWD_SEARCHPATH}"
    "${IW3_EXTRACTED_IWD_DIRECTORY}"
    "${IW3_EXTRACTED_IWD_LOOKUP}"
    "${IW3_EXTRACTED_UNZIP}"
    "${CMAKE_CURRENT_SOURCE_DIR}/iw3_android_unzip_io.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/iw3_android_iwd_directory_io.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/iw3_android_iwd_lookup_io.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/iw3_unzip_native_smoke.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/native_math_abi.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/iw3_android_platform.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/iw3_android_filter.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/snap_float_abi.cpp"
)
target_include_directories(iw3_sp_math PRIVATE
    "${CMAKE_CURRENT_SOURCE_DIR}"
    "${IW3_REAL_HEADER_ROOT}"
    "${IW3_ENGINE_SOURCE_ROOT}"
    "${IW3_ENGINE_SOURCE_ROOT}/qcommon"
    "${IW3_ENGINE_SOURCE_ROOT}/../deps")
find_library(IW3_Z_LIBRARY z REQUIRED)
target_link_libraries(iw3_sp_math PRIVATE "${IW3_Z_LIBRARY}")
set_target_properties(iw3_sp_math PROPERTIES
    CXX_VISIBILITY_PRESET hidden
    VISIBILITY_INLINES_HIDDEN YES
    OUTPUT_NAME "iw3_sp_math"
)
target_compile_options(iw3_sp_math PRIVATE
    -ffunction-sections -fdata-sections -Wall -Wextra -fsigned-char
    -frounding-math -fno-fast-math
)
target_link_options(iw3_sp_math PRIVATE
    -Wl,--gc-sections
    -Wl,--no-undefined
)
if(ANDROID)
    # Compile the entire original filesystem translation unit for Android.
    # Keep this as an object-only port gate until its remaining engine services
    # are wired into the runtime; never substitute extracted diagnostic bodies.
    add_library(iw3_sp_full_filesystem OBJECT
        "${IW3_ENGINE_SOURCE_ROOT}/universal/com_files.cpp"
        "${IW3_ENGINE_SOURCE_ROOT}/universal/com_files_state.cpp"
        "${IW3_ENGINE_SOURCE_ROOT}/universal/com_files_handle_table.cpp")
    target_include_directories(iw3_sp_full_filesystem PRIVATE
        "${CMAKE_CURRENT_SOURCE_DIR}"
        "${IW3_REAL_HEADER_ROOT}"
        "${IW3_ENGINE_SOURCE_ROOT}"
        "${IW3_ENGINE_SOURCE_ROOT}/qcommon"
        "${IW3_ENGINE_SOURCE_ROOT}/../deps")
    target_compile_definitions(iw3_sp_full_filesystem PRIVATE KISAK_SP=1)
    target_compile_options(iw3_sp_full_filesystem PRIVATE
        -Wall -Wextra -fsigned-char -frounding-math -fno-fast-math)

    # The full qcommon/files.cpp translation unit imports Windows/D3D renderer
    # headers, so compiling that entire TU as an Android object is not a valid
    # portability gate. Compile only the two original server-file comparison
    # bodies, extracted verbatim with declarations-only ABI glue.
    if(IW3_EXTRACTED_FILE_COMPARISONS)
        if(NOT EXISTS "${IW3_EXTRACTED_FILE_COMPARISONS}")
            message(FATAL_ERROR "Original FS_CompareIwds/FS_CompareFFs extraction path does not exist")
        endif()
        add_library(iw3_sp_file_comparisons STATIC
            "${IW3_EXTRACTED_FILE_COMPARISONS}")
        target_include_directories(iw3_sp_file_comparisons PRIVATE
            "${CMAKE_CURRENT_SOURCE_DIR}"
            "${IW3_REAL_HEADER_ROOT}"
            "${IW3_ENGINE_SOURCE_ROOT}"
            "${IW3_ENGINE_SOURCE_ROOT}/qcommon"
            "${IW3_ENGINE_SOURCE_ROOT}/../deps")
        target_compile_definitions(iw3_sp_file_comparisons PRIVATE KISAK_SP=1)
        target_compile_options(iw3_sp_file_comparisons PRIVATE
            -Wall -Wextra -fsigned-char -frounding-math -fno-fast-math)
    endif()

    # Compile the complete authentic dvar translation unit for Android ARM64.
    # This is an object-only portability gate: it is not linked into the JNI
    # diagnostic until its original synchronization and service graph is wired.
    add_library(iw3_sp_full_dvar OBJECT
        "${IW3_ENGINE_SOURCE_ROOT}/universal/dvar.cpp")
    # NET_Sleep is the one platform service used by the original dvar spin
    # waits. Compile the POSIX equivalent beside the untouched original TU.
    target_sources(iw3_sp_full_dvar PRIVATE
        "${CMAKE_CURRENT_SOURCE_DIR}/iw3_android_dvar_io.cpp"
        "${CMAKE_CURRENT_SOURCE_DIR}/iw3_android_dvar_log.cpp")
    if(IW3_EXTRACTED_DVAR_VEC4_COMPARE)
        if(NOT EXISTS "${IW3_EXTRACTED_DVAR_VEC4_COMPARE}")
            message(FATAL_ERROR "Original Vec4Compare source extraction required")
        endif()
        target_sources(iw3_sp_full_dvar PRIVATE "${IW3_EXTRACTED_DVAR_VEC4_COMPARE}")
    endif()
    target_include_directories(iw3_sp_full_dvar PRIVATE
        "${CMAKE_CURRENT_SOURCE_DIR}"
        "${IW3_REAL_HEADER_ROOT}"
        "${IW3_ENGINE_SOURCE_ROOT}"
        "${IW3_ENGINE_SOURCE_ROOT}/qcommon"
        "${IW3_ENGINE_SOURCE_ROOT}/../deps")
    target_compile_definitions(iw3_sp_full_dvar PRIVATE KISAK_SP=1)
    if(IW3_EXTRACTED_COM_PRINT_PRINTF)
        # Use the authentic Com_Printf body in combined audits; retain the
        # local log sink only for standalone dvar dependency checks.
        target_compile_definitions(iw3_sp_full_dvar PRIVATE IW3_ORIGINAL_COM_PRINT_PRINTF_LINK_AUDIT=1)
    endif()
    target_compile_options(iw3_sp_full_dvar PRIVATE
        -Wall -Wextra -fsigned-char -frounding-math -fno-fast-math)
    # Preserve all original dvar code and the real Android sleep provider in
    # one archive. It is still not linked into the JNI diagnostic/game runtime.
    add_library(iw3_sp_dvar_android STATIC $<TARGET_OBJECTS:iw3_sp_full_dvar>)

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
    # Compile the same portable FastFile parser probe as an AArch64 object.
    # It is intentionally not linked into the diagnostic APK or called a loader.
    add_library(iw3_fastfile_header_aarch64_compile OBJECT
        "${CMAKE_CURRENT_SOURCE_DIR}/db_fastfile_header_native_test.cpp")
    target_include_directories(iw3_fastfile_header_aarch64_compile PRIVATE
        "${IW3_ENGINE_SOURCE_ROOT}/database")
    target_compile_options(iw3_fastfile_header_aarch64_compile PRIVATE
        -Wall -Wextra -Werror)
else()
    enable_testing()

    add_executable(iw3_android_assert_host_test
        "${CMAKE_CURRENT_SOURCE_DIR}/assert_native_test.cpp")
    target_link_libraries(iw3_android_assert_host_test PRIVATE iw3_sp_android_assert)
    target_compile_options(iw3_android_assert_host_test PRIVATE -UNDEBUG -Wall -Wextra -Werror)
    add_test(NAME iw3_android_assert_provider_abort_semantics
             COMMAND iw3_android_assert_host_test)

    add_executable(iw3_fastfile_header_native_test
        "${CMAKE_CURRENT_SOURCE_DIR}/db_fastfile_header_native_test.cpp")
    target_include_directories(iw3_fastfile_header_native_test PRIVATE
        "${IW3_ENGINE_SOURCE_ROOT}/database")
    target_compile_options(iw3_fastfile_header_native_test PRIVATE
        -UNDEBUG -Wall -Wextra -Werror)
    add_test(NAME iw3_original_fastfile_header_alignment
             COMMAND iw3_fastfile_header_native_test)

    if(IW3_EXTRACTED_COM_PRINT_WARNING)
        add_executable(iw3_com_print_warning_host_test
            "${CMAKE_CURRENT_SOURCE_DIR}/com_print_warning_native_test.cpp")
        target_compile_options(iw3_com_print_warning_host_test PRIVATE -UNDEBUG -Wall -Wextra)
        target_link_libraries(iw3_com_print_warning_host_test PRIVATE iw3_sp_com_print_warning)
        add_test(NAME iw3_original_com_print_warning_android_sink
                 COMMAND iw3_com_print_warning_host_test)
        set_tests_properties(iw3_original_com_print_warning_android_sink
            PROPERTIES PASS_REGULAR_EXPRESSION "IW3_WARNING_PROBE_7")
    endif()

    if(IW3_EXTRACTED_COM_PRINT_PRINTF AND IW3_EXTRACTED_COM_PRINT_WARNING)
        add_executable(iw3_com_print_printf_host_test
            "${CMAKE_CURRENT_SOURCE_DIR}/com_print_printf_native_test.cpp")
        target_compile_options(iw3_com_print_printf_host_test PRIVATE -UNDEBUG -Wall -Wextra)
        target_link_libraries(iw3_com_print_printf_host_test PRIVATE
            iw3_sp_com_print_printf iw3_sp_com_print_warning)
        add_test(NAME iw3_original_com_print_printf_android_sink
                 COMMAND iw3_com_print_printf_host_test)
        set_tests_properties(iw3_original_com_print_printf_android_sink
            PROPERTIES PASS_REGULAR_EXPRESSION "IW3_PRINTF_PROBE_7")
    endif()

    add_executable(iw3_filter_host_test
        "${CMAKE_CURRENT_SOURCE_DIR}/filter_native_test.cpp")
    target_include_directories(iw3_filter_host_test PRIVATE
        "${CMAKE_CURRENT_SOURCE_DIR}"
        "${IW3_ENGINE_SOURCE_ROOT}"
        "${IW3_ENGINE_SOURCE_ROOT}/universal"
        "${IW3_ENGINE_SOURCE_ROOT}/qcommon"
        "${IW3_ENGINE_SOURCE_ROOT}/../deps")
    target_compile_definitions(iw3_filter_host_test PRIVATE KISAK_SP=1)
    target_compile_options(iw3_filter_host_test PRIVATE -UNDEBUG -Wall -Wextra)
    target_link_libraries(iw3_filter_host_test PRIVATE iw3_sp_filter)
    add_test(NAME iw3_original_filter_path_semantics COMMAND iw3_filter_host_test)

    if(IW3_EXTRACTED_Q_SHARED_STRINGS)
        add_executable(iw3_q_shared_strings_host_test
            "${CMAKE_CURRENT_SOURCE_DIR}/q_shared_strings_native_test.cpp")
        target_include_directories(iw3_q_shared_strings_host_test PRIVATE
            "${CMAKE_CURRENT_SOURCE_DIR}"
            "${IW3_REAL_HEADER_ROOT}"
            "${IW3_ENGINE_SOURCE_ROOT}"
            "${IW3_ENGINE_SOURCE_ROOT}/qcommon"
            "${IW3_ENGINE_SOURCE_ROOT}/../deps")
        target_compile_definitions(iw3_q_shared_strings_host_test PRIVATE KISAK_SP=1)
        target_compile_options(iw3_q_shared_strings_host_test PRIVATE
            -UNDEBUG -Wall -Wextra -ffunction-sections -fdata-sections)
        target_link_options(iw3_q_shared_strings_host_test PRIVATE -Wl,--gc-sections)
        target_link_libraries(iw3_q_shared_strings_host_test PRIVATE iw3_sp_q_shared_strings)
        add_test(NAME iw3_original_q_shared_string_services COMMAND iw3_q_shared_strings_host_test)
        set_tests_properties(iw3_original_q_shared_string_services
            PROPERTIES PASS_REGULAR_EXPRESSION "IW3_ORIGINAL_Q_SHARED_STRING_SERVICES_HOST_TEST_PASS")
    endif()

    add_executable(iw3_dvar_sleep_host_test
        "${CMAKE_CURRENT_SOURCE_DIR}/dvar_sleep_native_test.cpp"
        "${CMAKE_CURRENT_SOURCE_DIR}/iw3_android_dvar_io.cpp")
    target_compile_options(iw3_dvar_sleep_host_test PRIVATE -UNDEBUG -Wall -Wextra)
    add_test(NAME iw3_android_dvar_net_sleep_semantics COMMAND iw3_dvar_sleep_host_test)

    # Exercise the Android FS startup directory probe's root confinement and
    # fail-closed behavior using the exact platform adapter.
    add_executable(iw3_fs_startup_directory_adapter_host_test
        "${CMAKE_CURRENT_SOURCE_DIR}/fs_startup_directory_native_test.cpp"
        "${CMAKE_CURRENT_SOURCE_DIR}/iw3_android_directory_has_contents.cpp")
    target_include_directories(iw3_fs_startup_directory_adapter_host_test PRIVATE
        "${CMAKE_CURRENT_SOURCE_DIR}")
    target_compile_options(iw3_fs_startup_directory_adapter_host_test PRIVATE -UNDEBUG -Wall -Wextra)
    add_test(NAME iw3_original_fs_directory_probe_rooted COMMAND iw3_fs_startup_directory_adapter_host_test)

    # Exercise the real Android dvar log sink's formatting and channel prefix
    # on host; the Android build routes the same formatted message to logcat.
    add_executable(iw3_dvar_log_host_test
        "${CMAKE_CURRENT_SOURCE_DIR}/dvar_log_native_test.cpp"
        "${CMAKE_CURRENT_SOURCE_DIR}/iw3_android_dvar_log.cpp")
    target_include_directories(iw3_dvar_log_host_test PRIVATE
        "${IW3_ENGINE_SOURCE_ROOT}")
    target_compile_options(iw3_dvar_log_host_test PRIVATE -UNDEBUG -Wall -Wextra)
    add_test(NAME iw3_android_dvar_com_printf_format_and_channel COMMAND iw3_dvar_log_host_test)

    if(IW3_EXTRACTED_DVAR_VEC4_COMPARE)
        add_executable(iw3_dvar_vec4_host_test
            "${CMAKE_CURRENT_SOURCE_DIR}/dvar_vec4_native_test.cpp"
            "${IW3_EXTRACTED_DVAR_VEC4_COMPARE}")
        target_include_directories(iw3_dvar_vec4_host_test PRIVATE
            "${IW3_ENGINE_SOURCE_ROOT}"
            "${IW3_REAL_HEADER_ROOT}"
            "${IW3_ENGINE_SOURCE_ROOT}/qcommon"
            "${IW3_ENGINE_SOURCE_ROOT}/../deps")
        target_compile_options(iw3_dvar_vec4_host_test PRIVATE -UNDEBUG -Wall -Wextra)
        add_test(NAME iw3_original_dvar_vec4_compare COMMAND iw3_dvar_vec4_host_test)
    endif()

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
    add_executable(iw3_real_unzip_host_test
        "${CMAKE_CURRENT_SOURCE_DIR}/iw3_unzip_host_test.cpp")
    target_compile_options(iw3_real_unzip_host_test PRIVATE -UNDEBUG)
    target_link_libraries(iw3_real_unzip_host_test PRIVATE iw3_sp_math)
    add_test(NAME iw3_original_iw3_zip32_archive_reader COMMAND iw3_real_unzip_host_test)
    add_executable(iw3_platform_host_test
        "${CMAKE_CURRENT_SOURCE_DIR}/platform_native_test.cpp")
    target_include_directories(iw3_platform_host_test PRIVATE
        "${CMAKE_CURRENT_SOURCE_DIR}"
        "${IW3_ENGINE_SOURCE_ROOT}/qcommon"
        "${IW3_ENGINE_SOURCE_ROOT}/database")
    target_compile_options(iw3_platform_host_test PRIVATE -UNDEBUG)
    target_link_libraries(iw3_platform_host_test PRIVATE iw3_sp_math)
    add_test(NAME iw3_portable_platform COMMAND iw3_platform_host_test)
    if(NOT IW3_ENTITY_LOOP_INC OR NOT EXISTS "${IW3_ENTITY_LOOP_INC}")
        message(FATAL_ERROR "Original G_RunFrame typed entity source extraction required for ABI fixture")
    endif()
    if(IW3_EXTRACTED_DVAR_POINTER_SMOKE)
        if(NOT EXISTS "${IW3_EXTRACTED_DVAR_POINTER_SMOKE}")
            message(FATAL_ERROR "Original dvar pointer smoke source required")
        endif()
        add_executable(iw3_dvar_pointer_native_test
            "${CMAKE_CURRENT_SOURCE_DIR}/dvar_pointer_native_test.cpp"
            "${IW3_EXTRACTED_DVAR_POINTER_SMOKE}")
        target_include_directories(iw3_dvar_pointer_native_test PRIVATE
            "${CMAKE_CURRENT_SOURCE_DIR}"
            "${IW3_REAL_HEADER_ROOT}"
            "${IW3_ENGINE_SOURCE_ROOT}"
            "${IW3_ENGINE_SOURCE_ROOT}/qcommon"
            "${IW3_ENGINE_SOURCE_ROOT}/../deps")
        target_compile_definitions(iw3_dvar_pointer_native_test PRIVATE KISAK_SP=1)
        target_compile_options(iw3_dvar_pointer_native_test PRIVATE -UNDEBUG)
        # Exercise the same signed-char hazard present on Android ARM64 even
        # when this host's default char signedness differs.
        if(CMAKE_CXX_COMPILER_ID MATCHES "Clang|GNU")
            target_compile_options(iw3_dvar_pointer_native_test PRIVATE -fsigned-char)
        endif()
        add_test(NAME iw3_original_dvar_pointer_width COMMAND iw3_dvar_pointer_native_test)
    endif()
    add_executable(iw3_real_frame_loop_abi_test
        "${CMAKE_CURRENT_SOURCE_DIR}/frame_loop_abi_test.cpp")
    get_filename_component(IW3_ENTITY_LOOP_DIR "${IW3_ENTITY_LOOP_INC}" DIRECTORY)
    target_include_directories(iw3_real_frame_loop_abi_test PRIVATE "${IW3_ENTITY_LOOP_DIR}")
    target_compile_options(iw3_real_frame_loop_abi_test PRIVATE -UNDEBUG)
    add_test(NAME iw3_real_g_runframe_typed_entity_64bit COMMAND iw3_real_frame_loop_abi_test)

    # Execute the original localized directory setup with only platform service
    # stubs. This catches empty-language names aliasing the parent game folder.
    if(IW3_EXTRACTED_FS_STARTUP AND EXISTS "${IW3_EXTRACTED_FS_STARTUP}")
        add_executable(iw3_fs_localized_path_host_test
            "${CMAKE_CURRENT_SOURCE_DIR}/fs_localized_path_native_test.cpp"
            "${IW3_EXTRACTED_FS_STARTUP}")
        target_include_directories(iw3_fs_localized_path_host_test PRIVATE
            "${CMAKE_CURRENT_SOURCE_DIR}"
            "${IW3_REAL_HEADER_ROOT}"
            "${IW3_ENGINE_SOURCE_ROOT}"
            "${IW3_ENGINE_SOURCE_ROOT}/qcommon"
            "${IW3_ENGINE_SOURCE_ROOT}/../deps")
        target_compile_definitions(iw3_fs_localized_path_host_test PRIVATE KISAK_SP=1 IW3_FS_STARTUP_HOST_TEST=1)
        target_compile_options(iw3_fs_localized_path_host_test PRIVATE
            -UNDEBUG -ffunction-sections -fdata-sections -Wall -Wextra)
        target_link_options(iw3_fs_localized_path_host_test PRIVATE -Wl,--gc-sections)
        add_test(NAME iw3_original_fs_localized_paths_fail_closed
                 COMMAND iw3_fs_localized_path_host_test)
    endif()
    # Execute the original Com_LogFileOpen state query and the Android port of
    # KisakCOD's writer gate under real thread contention. The full FS_ReadFile
    # object stays a separate archive member and is not pulled into this test.
    if(IW3_EXTRACTED_FS_READFILE AND IW3_EXTRACTED_COM_LOGFILE_OPEN)
        find_package(Threads REQUIRED)
        add_executable(iw3_fs_readfile_services_host_test
            "${CMAKE_CURRENT_SOURCE_DIR}/fs_readfile_services_native_test.cpp")
        target_include_directories(iw3_fs_readfile_services_host_test PRIVATE
            "${CMAKE_CURRENT_SOURCE_DIR}"
            "${IW3_REAL_HEADER_ROOT}"
            "${IW3_ENGINE_SOURCE_ROOT}"
            "${IW3_ENGINE_SOURCE_ROOT}/qcommon"
            "${IW3_ENGINE_SOURCE_ROOT}/../deps")
        target_compile_definitions(iw3_fs_readfile_services_host_test PRIVATE KISAK_SP=1)
        target_compile_options(iw3_fs_readfile_services_host_test PRIVATE -UNDEBUG -Wall -Wextra)
        target_link_libraries(iw3_fs_readfile_services_host_test PRIVATE
            iw3_sp_fs_readfile Threads::Threads)
        add_test(NAME iw3_original_fs_logfile_state_and_writer_lock
                 COMMAND iw3_fs_readfile_services_host_test)
    endif()

endif()
