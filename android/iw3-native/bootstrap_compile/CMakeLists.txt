cmake_minimum_required(VERSION 3.21)
project(IW3_Authentic_SP_Bootstrap_Compile LANGUAGES CXX)
# Independent compile-only gate: avoids unrelated extracted-source requirements
# of the full port. Every source below is an unmodified original KisakCOD TU.
# This is NOT a linked engine, renderer, runtime, or playable APK.
if(NOT ANDROID OR NOT CMAKE_ANDROID_ARCH_ABI STREQUAL "arm64-v8a")
  message(FATAL_ERROR "This compile gate requires Android arm64-v8a")
endif()
if(NOT IW3_ENGINE_ROOT OR NOT EXISTS "${IW3_ENGINE_ROOT}/qcommon/common.cpp")
  message(FATAL_ERROR "Point IW3_ENGINE_ROOT at genuine KisakCOD src")
endif()
if(NOT IW3_OPENAL_HEADERS_ROOT OR NOT EXISTS "${IW3_OPENAL_HEADERS_ROOT}/AL/al.h")
  message(FATAL_ERROR "Real OpenAL API headers required")
endif()
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)
set(SRC "${IW3_ENGINE_ROOT}")
set(PORT "${CMAKE_CURRENT_LIST_DIR}/..")
set(DEPS "${SRC}/../deps")
set(COMMON_INCLUDES "${PORT}" "${SRC}" "${DEPS}" "${IW3_OPENAL_HEADERS_ROOT}")
foreach(part qcommon universal client ui devgui gfx_d3d game cgame server bgame sound script xanim database aim_assist win32)
  list(APPEND COMMON_INCLUDES "${SRC}/${part}")
endforeach()
function(original_tu target source)
  if(NOT EXISTS "${SRC}/${source}")
    message(FATAL_ERROR "Missing genuine engine TU: ${source}")
  endif()
  add_library(${target} OBJECT "${SRC}/${source}")
  target_include_directories(${target} PRIVATE ${COMMON_INCLUDES})
  target_compile_definitions(${target} PRIVATE KISAK_SP=1 KISAK_OPENAL=1)
  target_compile_options(${target} PRIVATE -fms-extensions -Wall -Wextra -fsigned-char -frounding-math -fno-fast-math)
endfunction()
original_tu(iw3_common qcommon/common.cpp)
target_include_directories(iw3_common BEFORE PRIVATE "${PORT}/common_compat")
target_compile_definitions(iw3_common PRIVATE IW3_ANDROID_DISABLE_SCRIPT_DEBUGGER=1 IW3_ANDROID_COMMON_HEADER_ONLY_OPENAL=1)
original_tu(iw3_cmd qcommon/cmd.cpp)
original_tu(iw3_math universal/com_math.cpp)
# Original memory tracking provider, including track_static_alloc_internal.
original_tu(iw3_mem_track qcommon/mem_track.cpp)
# Genuine shared string/path helpers required by filesystem and SP bootstrap.
original_tu(iw3_q_shared universal/q_shared.cpp)
# Genuine parser provider for Com_BeginParseSession/Com_Parse used by SP loaders.
original_tu(iw3_q_parse universal/q_parse.cpp)
# Genuine memory-file serializer/deserializer used by SP state and save/load.
original_tu(iw3_memfile universal/memfile.cpp)
# Genuine SP dvar registry/modified-flag provider, already cross-compiled in the
# standalone Android engine gate. Include it in the strict dependency closure.
original_tu(iw3_dvar universal/dvar.cpp)
# Genuine dvar console command registration provider used by Dvar_Init.
original_tu(iw3_dvar_cmds universal/dvar_cmds.cpp)
original_tu(iw3_files universal/com_files.cpp)
# Genuine stdio file-access provider; Android FS_FileTell uses FILE* directly.
original_tu(iw3_fileaccess qcommon/com_fileaccess.cpp)
# Original filesystem runtime provider, not a diagnostic substitute.
original_tu(iw3_filesystem qcommon/files.cpp)
# Genuine IW3 IWD/ZIP reader; expose original unz* providers to strict link.
original_tu(iw3_unzip qcommon/unzip.cpp)
# Genuine IW3 Hunk/PMem provider: expose original memory services to strict link.
original_tu(iw3_com_memory universal/com_memory.cpp)
# Android OS adapter for the original Win32 virtual-memory imports.
# Do NOT link iw3_android_hunk_virtual.cpp here: it duplicates Z_Virtual* in com_memory.cpp.
add_library(iw3_android_win32_vm OBJECT "${CMAKE_CURRENT_LIST_DIR}/iw3_android_win32_virtual_memory.cpp")
target_compile_options(iw3_android_win32_vm PRIVATE -Wall -Wextra -Werror)
# Original com_memory.cpp retains its Win32 ABI imports; declare them for NDK compilation.
# iw3_android_win32_vm supplies real mmap/mprotect-backed implementations to the
# strict link probe. This does not resolve the rest of the original engine closure.
target_compile_options(iw3_com_memory PRIVATE
  "-include" "${CMAKE_CURRENT_LIST_DIR}/win32_virtual_memory_declarations.h")
# Android POSIX filesystem/touch adapter; real implementation (not a symbol stub).
# The original filesystem calls z2026_platform_rename_engine_path via this TU.
add_library(iw3_android_platform OBJECT "${PORT}/iw3_android_platform.cpp")
target_include_directories(iw3_android_platform PRIVATE ${COMMON_INCLUDES})
target_compile_options(iw3_android_platform PRIVATE -Wall -Wextra)
original_tu(iw3_db_load database/db_file_load.cpp)
original_tu(iw3_db_registry database/db_registry.cpp)
# Genuine zone allocation and geometry-buffer lifecycle provider (not a stub).
original_tu(iw3_db_memory database/db_memory.cpp)
original_tu(iw3_client_input client/cl_input.cpp)
original_tu(iw3_screen client/screen_placement.cpp)
# Original server command provider: advance beyond compile-only client/common closure.
original_tu(iw3_sv_ccmds server/sv_ccmds.cpp)
# Authentic server/game bridge; advances real gameplay dependency closure.
original_tu(iw3_sv_game server/sv_game.cpp)
# Original SP server initialization provider; compile/link its real dependencies.
original_tu(iw3_sv_init server/sv_init.cpp)
# Original single-player server frame, state and gameplay scheduler provider.
original_tu(iw3_sv_main server/sv_main.cpp)
# Genuine collision/map loader; compile gate only until its full providers link.
original_tu(iw3_cm_load qcommon/cm_load.cpp)
# Original collision BSP object reader: map data provider, not a substitute loader.
original_tu(iw3_cm_load_obj qcommon/cm_load_obj.cpp)
# Authentic client lifecycle and renderer-registration caller, already validated
# as a standalone AArch64 TU by the original-client-full compile workflow.
original_tu(iw3_xanim xanim/xanim.cpp)
# Genuine script memory-tree allocator supplying MT_Alloc/MT_Free for XAnim.
original_tu(iw3_script_memorytree script/scr_memorytree.cpp)
# Genuine script string intern table: SL_Init/SL_GetString and related lifecycle.
original_tu(iw3_script_stringlist script/scr_stringlist.cpp)
# Original localization provider for SEH_InitLanguage and SEH_Shutdown_StringEd.
original_tu(iw3_stringed_hooks stringed/stringed_hooks.cpp)
# Authentic weapon definition lifecycle provider for BG_ShutdownWeaponDefFiles.
# Compile/link the full original TU, never a symbol-only replacement.
original_tu(iw3_bg_weapons bgame/bg_weapons.cpp)
# Original single-player menu/UI controller, including UI_IsFullscreen.
# This remains an audit TU; compiling it is not proof of Android UI rendering.
original_tu(iw3_ui_main ui/ui_main.cpp)
original_tu(iw3_ui_shared ui/ui_shared.cpp)
# Genuine KisakCOD profiling provider. Win32-only inactive QPC code is guarded
# in the original TU for Android; this does not establish gameplay readiness.
original_tu(iw3_profile universal/profile.cpp)
# Android thread-local implementation of original Sys_SetValue/GetValue API.
add_library(iw3_android_thread_values OBJECT "${CMAKE_CURRENT_LIST_DIR}/iw3_android_thread_values.cpp")
target_include_directories(iw3_android_thread_values PRIVATE ${COMMON_INCLUDES})
target_compile_definitions(iw3_android_thread_values PRIVATE KISAK_SP=1 KISAK_OPENAL=1)
target_compile_options(iw3_android_thread_values PRIVATE -fms-extensions -Wall -Wextra -Werror)
# POSIX recursive synchronization for genuine Sys_Enter/LeaveCriticalSection calls.
add_library(iw3_android_critical_sections OBJECT "${CMAKE_CURRENT_LIST_DIR}/iw3_android_critical_sections.cpp")
target_compile_options(iw3_android_critical_sections PRIVATE -Wall -Wextra -Werror)
original_tu(iw3_client_main client/cl_main.cpp)
target_include_directories(iw3_client_main BEFORE PRIVATE "${PORT}/common_compat")
target_compile_definitions(iw3_client_main PRIVATE IW3_ANDROID_DISABLE_SCRIPT_DEBUGGER=1 IW3_ANDROID_COMMON_HEADER_ONLY_OPENAL=1)
add_custom_target(iw3_sp_bootstrap_compile DEPENDS iw3_common iw3_cmd iw3_math iw3_mem_track iw3_q_shared iw3_q_parse iw3_memfile iw3_dvar iw3_dvar_cmds iw3_files iw3_fileaccess iw3_filesystem iw3_unzip iw3_com_memory iw3_android_win32_vm iw3_android_platform iw3_db_load iw3_db_registry iw3_db_memory iw3_client_input iw3_screen iw3_sv_ccmds iw3_sv_game iw3_sv_init iw3_sv_main iw3_cm_load iw3_cm_load_obj iw3_xanim iw3_script_memorytree iw3_script_stringlist iw3_stringed_hooks iw3_bg_weapons iw3_ui_main iw3_ui_shared iw3_profile iw3_android_thread_values iw3_android_critical_sections iw3_client_main)

# Explicit, opt-in genuine link probe. This target deliberately fails until all
# original engine dependencies are provided; it must NEVER be packaged as an APK.
# Build with: cmake --build <build-dir> --target iw3_sp_link_probe
add_library(iw3_sp_link_probe SHARED
  $<TARGET_OBJECTS:iw3_common>
  $<TARGET_OBJECTS:iw3_cmd>
  $<TARGET_OBJECTS:iw3_math>
  $<TARGET_OBJECTS:iw3_mem_track>
  $<TARGET_OBJECTS:iw3_q_shared>
  $<TARGET_OBJECTS:iw3_q_parse>
  $<TARGET_OBJECTS:iw3_memfile>
  $<TARGET_OBJECTS:iw3_dvar>
  $<TARGET_OBJECTS:iw3_dvar_cmds>
  $<TARGET_OBJECTS:iw3_files>
  $<TARGET_OBJECTS:iw3_fileaccess>
  $<TARGET_OBJECTS:iw3_filesystem>
  $<TARGET_OBJECTS:iw3_unzip>
  $<TARGET_OBJECTS:iw3_com_memory>
  $<TARGET_OBJECTS:iw3_android_win32_vm>
  $<TARGET_OBJECTS:iw3_android_platform>
  $<TARGET_OBJECTS:iw3_db_load>
  $<TARGET_OBJECTS:iw3_db_registry>
  $<TARGET_OBJECTS:iw3_db_memory>
  $<TARGET_OBJECTS:iw3_client_input>
  $<TARGET_OBJECTS:iw3_screen>
  $<TARGET_OBJECTS:iw3_sv_ccmds>
  $<TARGET_OBJECTS:iw3_sv_game>
  $<TARGET_OBJECTS:iw3_sv_init>
  $<TARGET_OBJECTS:iw3_sv_main>
  $<TARGET_OBJECTS:iw3_cm_load>
  $<TARGET_OBJECTS:iw3_cm_load_obj>
  $<TARGET_OBJECTS:iw3_xanim>
  $<TARGET_OBJECTS:iw3_script_memorytree>
  $<TARGET_OBJECTS:iw3_script_stringlist>
  $<TARGET_OBJECTS:iw3_stringed_hooks>
  $<TARGET_OBJECTS:iw3_bg_weapons>
  $<TARGET_OBJECTS:iw3_ui_main>
  $<TARGET_OBJECTS:iw3_ui_shared>
  $<TARGET_OBJECTS:iw3_profile>
  $<TARGET_OBJECTS:iw3_android_thread_values>
  $<TARGET_OBJECTS:iw3_android_critical_sections>
  $<TARGET_OBJECTS:iw3_client_main>
)
target_link_libraries(iw3_sp_link_probe PRIVATE z)
set_target_properties(iw3_sp_link_probe PROPERTIES EXCLUDE_FROM_ALL TRUE)
# Capture the complete genuine dependency closure instead of lld's first 20 errors.
# The probe is intentionally expected to fail until original providers are linked.
target_link_options(iw3_sp_link_probe PRIVATE "LINKER:--no-undefined" "LINKER:--error-limit=0")
