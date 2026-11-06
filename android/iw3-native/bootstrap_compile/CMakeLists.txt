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
original_tu(iw3_db_load database/db_file_load.cpp)
original_tu(iw3_db_registry database/db_registry.cpp)
original_tu(iw3_client_input client/cl_input.cpp)
original_tu(iw3_screen client/screen_placement.cpp)
add_custom_target(iw3_sp_bootstrap_compile DEPENDS iw3_common iw3_cmd iw3_math iw3_files iw3_db_load iw3_db_registry iw3_client_input iw3_screen)

# Explicit, opt-in genuine link probe. This target deliberately fails until all
# original engine dependencies are provided; it must NEVER be packaged as an APK.
# Build with: cmake --build <build-dir> --target iw3_sp_link_probe
add_library(iw3_sp_link_probe SHARED
  $<TARGET_OBJECTS:iw3_common>
  $<TARGET_OBJECTS:iw3_cmd>
  $<TARGET_OBJECTS:iw3_math>
  $<TARGET_OBJECTS:iw3_files>
  $<TARGET_OBJECTS:iw3_db_load>
  $<TARGET_OBJECTS:iw3_db_registry>
  $<TARGET_OBJECTS:iw3_client_input>
  $<TARGET_OBJECTS:iw3_screen>
)
set_target_properties(iw3_sp_link_probe PROPERTIES EXCLUDE_FROM_ALL TRUE)
target_link_options(iw3_sp_link_probe PRIVATE "LINKER:--no-undefined")
