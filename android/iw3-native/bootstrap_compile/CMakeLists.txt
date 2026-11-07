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
original_tu(iw3_files universal/com_files.cpp)
# Original filesystem runtime provider, not a diagnostic substitute.
original_tu(iw3_filesystem qcommon/files.cpp)
# Genuine IW3 IWD/ZIP reader; expose original unz* providers to strict link.
original_tu(iw3_unzip qcommon/unzip.cpp)
# Genuine IW3 Hunk/PMem provider: expose original memory services to strict link.
original_tu(iw3_com_memory universal/com_memory.cpp)
# Compile audit only: declare Win32 memory imports without faking their behavior.
# The strict link must still report unresolved VirtualAlloc/VirtualFree.
target_compile_options(iw3_com_memory PRIVATE
  "-include" "${CMAKE_CURRENT_LIST_DIR}/win32_virtual_memory_declarations.h")
original_tu(iw3_db_load database/db_file_load.cpp)
original_tu(iw3_db_registry database/db_registry.cpp)
original_tu(iw3_client_input client/cl_input.cpp)
original_tu(iw3_screen client/screen_placement.cpp)
# Original server command provider: advance beyond compile-only client/common closure.
original_tu(iw3_sv_ccmds server/sv_ccmds.cpp)
# Authentic server/game bridge; advances real gameplay dependency closure.
original_tu(iw3_sv_game server/sv_game.cpp)
# Original SP server initialization provider; compile/link its real dependencies.
original_tu(iw3_sv_init server/sv_init.cpp)
# Genuine collision/map loader; compile gate only until its full providers link.
original_tu(iw3_cm_load qcommon/cm_load.cpp)
# Original collision BSP object reader: map data provider, not a substitute loader.
original_tu(iw3_cm_load_obj qcommon/cm_load_obj.cpp)
# Authentic client lifecycle and renderer-registration caller, already validated
# as a standalone AArch64 TU by the original-client-full compile workflow.
original_tu(iw3_client_main client/cl_main.cpp)
target_include_directories(iw3_client_main BEFORE PRIVATE "${PORT}/common_compat")
target_compile_definitions(iw3_client_main PRIVATE IW3_ANDROID_DISABLE_SCRIPT_DEBUGGER=1 IW3_ANDROID_COMMON_HEADER_ONLY_OPENAL=1)
add_custom_target(iw3_sp_bootstrap_compile DEPENDS iw3_common iw3_cmd iw3_math iw3_files iw3_filesystem iw3_unzip iw3_com_memory iw3_db_load iw3_db_registry iw3_client_input iw3_screen iw3_sv_ccmds iw3_sv_game iw3_sv_init iw3_cm_load iw3_cm_load_obj iw3_client_main)

# Explicit, opt-in genuine link probe. This target deliberately fails until all
# original engine dependencies are provided; it must NEVER be packaged as an APK.
# Build with: cmake --build <build-dir> --target iw3_sp_link_probe
add_library(iw3_sp_link_probe SHARED
  $<TARGET_OBJECTS:iw3_common>
  $<TARGET_OBJECTS:iw3_cmd>
  $<TARGET_OBJECTS:iw3_math>
  $<TARGET_OBJECTS:iw3_files>
  $<TARGET_OBJECTS:iw3_filesystem>
  $<TARGET_OBJECTS:iw3_unzip>
  $<TARGET_OBJECTS:iw3_com_memory>
  $<TARGET_OBJECTS:iw3_db_load>
  $<TARGET_OBJECTS:iw3_db_registry>
  $<TARGET_OBJECTS:iw3_client_input>
  $<TARGET_OBJECTS:iw3_screen>
  $<TARGET_OBJECTS:iw3_sv_ccmds>
  $<TARGET_OBJECTS:iw3_sv_game>
  $<TARGET_OBJECTS:iw3_sv_init>
  $<TARGET_OBJECTS:iw3_cm_load>
  $<TARGET_OBJECTS:iw3_cm_load_obj>
  $<TARGET_OBJECTS:iw3_client_main>
)
target_link_libraries(iw3_sp_link_probe PRIVATE z)
set_target_properties(iw3_sp_link_probe PROPERTIES EXCLUDE_FROM_ALL TRUE)
# Capture the complete genuine dependency closure instead of lld's first 20 errors.
# The probe is intentionally expected to fail until original providers are linked.
target_link_options(iw3_sp_link_probe PRIVATE "LINKER:--no-undefined" "LINKER:--error-limit=0")
