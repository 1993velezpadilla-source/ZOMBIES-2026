#!/usr/bin/env python3
"""Assert only actually verified Lavapipe Android execution conditions.

This gate checks native renderer/process visibility and input delivery, NOT
game mechanics or commercial game data completeness.
"""
from pathlib import Path
import json

ROOT=Path("smoke-out/real-data-test")
main=json.loads((ROOT/"result.json").read_text())
renders=json.loads((ROOT/"renderer-diagnostic.json").read_text())
touch=json.loads((ROOT/"touch-control-report.json").read_text())
last=renders["snapshots"][-1]["regions"]["center_scene"]
mean=last["mean_rgb"]
seen_color=last["red_dominant_percent"]<15 and sum(mean)/3>40
events=touch["tests"]
all_delivered=(len(events)==7 and all(e["adb_input_exit_code"]==0 for e in events))
checks={
    "original_asset_subset_imported":bool(main["import_banner_observed"]),
    "native_cod4_campaign_launched":bool(main["campaign_button_clicked"]),
    "native_android_process_alive_after_touch":bool(touch["campaign_process_alive_after_input"]),
    "seven_adb_events_delivered":all_delivered,
    "latest_rendered_frame_has_non_red_luminance":seen_color,
}
out={
    "test":"Real COD4 Android Lavapipe renderer + touch input delivery",
    "backend":"lavapipe",
    "checks":checks,
    "latest_center_rgb":mean,
    "latest_center_red_dominant_percent":last["red_dominant_percent"],
    "gesture_names":[e["name"] for e in events],
    "source_data_complete":False,
    "touch_controls_gameplay_functionally_verified":False,
    "fps_acceptable_on_emulator":False,
    "native_physical_arm64_device_tested":False,
    "result":"EXECUTION_PASS" if all(checks.values()) else "EXECUTION_FAIL",
    "caution":"No test here confirms bullet firing, ammo changes, ADS FOV, player coordinates, reload animation, or stable FPS."
}
target=ROOT/"lavapipe-touch-gate.json"
target.write_text(json.dumps(out,indent=2)+"\n")
print("LAVAPIPE_TOUCH_GATE",json.dumps(out))
if not all(checks.values()):
    raise SystemExit("Lavapipe execution requirements not met")
