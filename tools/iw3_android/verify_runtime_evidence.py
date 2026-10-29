#!/usr/bin/env python3
"""Verify actual diagnostic logcat evidence, never infer gameplay from it."""
from __future__ import annotations

import argparse
import math
import re
from pathlib import Path

REQUIRED = (
    "IW3_JNI_LIFECYCLE_1",
    "IW3_JNI_DATA_ROOT_READY",
    "IW3_JNI_UNZIP_PARSER_PASS",
    "IW3_JNI_Q_SHARED_CASEFOLD_PASS",
    "IW3_JNI_IWD_MOUNT_PASS",
    "IW3_JNI_IWD_SEARCHPATH_PASS",
    "IW3_JNI_IWD_DIRECTORY_SCAN_PASS",
    "IW3_JNI_IWD_GAME_DIRECTORY_PASS",
    "IW3_JNI_IWD_LOOKUP_PASS",
    "IW3_JNI_IWD_FS_READ_PASS",
    "IW3_JNI_IWD_FS_OPEN_READ_CLOSE_PASS",
    "IW3_JNI_IWD_FS_CLONE_PASS",
    "IW3_JNI_FS_DIRECTORY_OPEN_READ_CLOSE_PASS",
    "IW3_JNI_SNAP_FLOAT_PASS",
    "IW3_JNI_IWD_NAMES_PASS",
    "IW3_JNI_FS_STARTUP_PATH_PASS",
    "IW3_JNI_SANDBOX_IO_PASS",
    "IW3_JNI_USERCMD_ADAPTER_READY",
    "JNI_NATIVE_ENGINE_PROBE_PASS",
    "IW3_JNI_ACTIVITY_STARTED PASS",
)
ERRORS = (
    "JNI_NATIVE_ENGINE_PROBE_FAIL", "IW3_JNI_ACTIVITY_FAILED",
    "IW3_JNI_Q_SHARED_CASEFOLD_FAIL",
    "IW3_JNI_ACTIVITY_STARTED FAIL", "IW3_JNI_DATA_ROOT_FAIL",
    "IW3_JNI_UNZIP_PARSER_FAIL", "IW3_JNI_IWD_MOUNT_FAIL", "IW3_JNI_IWD_SEARCHPATH_FAIL",
    "IW3_JNI_IWD_DIRECTORY_SCAN_FAIL", "IW3_JNI_IWD_GAME_DIRECTORY_FAIL",
    "IW3_JNI_IWD_LOOKUP_FAIL", "IW3_JNI_IWD_FS_READ_FAIL",
    "IW3_JNI_IWD_FS_OPEN_READ_CLOSE_FAIL", "IW3_JNI_IWD_FS_CLONE_FAIL",
    "IW3_JNI_FS_DIRECTORY_OPEN_READ_CLOSE_FAIL",
    "IW3_JNI_SNAP_FLOAT_FAIL",
    "IW3_JNI_IWD_NAMES_FAIL", "IW3_JNI_FS_STARTUP_PATH_FAIL", "IW3_JNI_SANDBOX_IO_FAIL",
    "IW3_JNI_USERCMD_ADAPTER_FAIL", "IW3_JNI_USERCMD_SNAPSHOT_FAILED",
    "IW3_JNI_TOUCH_FAILED", "TOUCH_NATIVE_REJECTED",
    "JNI_RESUME_FAILED", "JNI_PAUSE_FAILED", "JNI_DESTROY_FAILED",
    "FATAL EXCEPTION", "Fatal signal", "ANR in org.z2026.iw3nativeprobe",
)
TOUCH = re.compile(
    r"IW3_JNI_TOUCH id=(-?\d+) pressed=(-?\d+) coords=([^,\s]+),([^\s]+)")
USERCMD = re.compile(
    r"IW3_JNI_USERCMD attack=(\d+) buttons=(\d+) forward=(-?\d+) right=(-?\d+) pitch=(-?\d+) yaw=(-?\d+)")


def verify(log: str) -> dict:
    for error in ERRORS:
        if error in log:
            raise ValueError("Android runtime failure: " + error)
    # Android may recreate the Activity during initial landscape rotation.
    # Validate the latest instance's own native report and input/lifecycle;
    # never mistake a prior instance's orientation pause for the tested Home.
    latest_create = log.rfind("IW3_JNI_LIFECYCLE_1")
    if latest_create < 0:
        raise ValueError("Actual Android Activity creation missing")
    log = log[latest_create:]
    cursor = 0
    for marker in REQUIRED:
        offset = log.find(marker, cursor)
        if offset < 0:
            raise ValueError("Missing/incorrectly ordered native evidence: " + marker)
        cursor = offset + len(marker)
    resumed = log.find("IW3_JNI_LIFECYCLE_2", cursor)
    paused = log.find("IW3_JNI_LIFECYCLE_3", resumed + 1)
    resumed_again = log.find("IW3_JNI_LIFECYCLE_2", paused + 1)
    if resumed < 0 or paused < 0 or resumed_again < 0:
        raise ValueError("Actual Android resume/pause/resume lifecycle missing")
    downs: set[int] = set()
    completed: set[int] = set()
    for match in TOUCH.finditer(log, resumed, paused):
        identifier, pressed = int(match[1]), int(match[2])
        x, y = float(match[3]), float(match[4])
        if not 0 <= identifier < 32 or pressed not in (0, 1) or not (
            math.isfinite(x) and math.isfinite(y) and 0 <= x <= 1 and 0 <= y <= 1
        ):
            raise ValueError("Invalid native touch readback (Android pointer ID must be 0..31)")
        if pressed:
            downs.add(identifier)
        elif identifier in downs:
            downs.remove(identifier)
            completed.add(identifier)
        else:
            raise ValueError("Native touch release without matching press")
    if not completed or downs:
        raise ValueError("Native touch must return both DOWN and UP for the same pointer")
    attack_command_observed = False
    sprint_command_observed = False
    slide_chord_command_observed = False
    for command in USERCMD.finditer(log, resumed, paused):
        attack, buttons = int(command[1]), int(command[2])
        if attack not in (0, 1):
            raise ValueError("Invalid native usercmd attack flag")
        if attack == 1 and (buttons & 1):
            attack_command_observed = True
        if attack == 0 and (buttons & (1 << 1)) and not (buttons & (1 << 9)):
            sprint_command_observed = True
        if attack == 0 and (buttons & ((1 << 1) | (1 << 9))) == ((1 << 1) | (1 << 9)):
            slide_chord_command_observed = True
    if not attack_command_observed:
        raise ValueError("Real Android attack touch did not reach the original IW3 usercmd_s button layout")
    if not sprint_command_observed:
        raise ValueError("Real Android sprint touch did not set the original IW3 BUTTON_SPRINT bit")
    if not slide_chord_command_observed:
        raise ValueError("Real Android slide touch did not set the original IW3 sprint+crouch command chord")
    return {
        "android_jni_components_executed": True,
        "original_iw3_zip32_stored_and_deflate_parser_executed": True,
        "original_fs_loadzipfile_indexed_fixture_executed": True,
        "original_fs_addsearchpath_inserted_fixture_executed": True,
        "original_fs_addiwdfiles_directory_scan_executed": True,
        "original_fs_add_game_directory_registered_fixture_executed": True,
        "original_fs_fopenfileread_searchpath_lookup_branch_executed": True,
        "original_fs_read_iwd_zip_branch_executed": True,
        "original_fs_read_handle_path_executed": True,
        "original_fs_open_read_close_lifecycle_executed": True,
        "original_fs_iwd_clone_handle_path_executed": True,
        "original_fs_directory_open_read_close_lifecycle_executed": True,
        "original_fs_directory_fallback_read_executed": True,
        "original_fs_startup_path_bound_to_android_filesdir": True,
        "original_upstream_fsh_table_integrated": False,
        "touch_down_and_up_read_back_from_native": True,
        "touch_translated_to_original_iw3_usercmd_s": True,
        "sprint_touch_reached_original_usercmd_s": True,
        "slide_chord_touch_reached_original_usercmd_s": True,
        "android_pause_and_resume_observed": True,
        "arm64_device_execution_proven": False,
        "gameplay_proven": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("logcat", type=Path)
    args = parser.parse_args()
    print("IW3_ANDROID_NATIVE_DIAGNOSTIC_EVIDENCE_VALIDATED", verify(
        args.logcat.read_text(encoding="utf-8")))


if __name__ == "__main__":
    main()
