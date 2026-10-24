#!/usr/bin/env python3
"""Real Android COD4 onscreen-control smoke probe.

Runs only after the engine has displayed a 3D scene. Sends single-touch ADB
gestures and records images + measurable changes. This script does NOT assume
that pixel differences alone prove the player moved or a bullet was fired.
"""
from __future__ import annotations
from PIL import Image, ImageChops, ImageStat
import json
import math
from pathlib import Path
import subprocess
import time

OUTPUT = Path("smoke-out/real-data-test")
OUTPUT.mkdir(parents=True, exist_ok=True)
APP = "com.cod4.firstmission"
# Control centers are given as fractions of the verified 2340x1080 screenshot.
CONTROL = {
    "joystick": (.148, .735),
    "aim": (.109, .38),
    "fire": (.903, .49),
    "reload": (.758, .397),
    "sprint": (.30, .81),
    "jump": (.910, .840),
    "crouch": (.798, .726),
}
def adb(*argv, timeout=45):
    p = subprocess.run(["adb",*argv],text=True,stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT,timeout=timeout)
    if p.returncode:
        print("ADB_ERROR",argv,p.returncode,p.stdout[:500],flush=True)
    return p.stdout, p.returncode
def screenshot(name):
    dest = OUTPUT / (name+".png")
    with dest.open("wb") as f:
        subprocess.run(["adb","exec-out","screencap","-p"],stdout=f,
                       stderr=subprocess.DEVNULL,timeout=45,check=True)
    with Image.open(dest) as original:
        img=original.convert("RGB")
    return dest,img
def coord(norm,width,height):
    return round(width*norm[0]),round(height*norm[1])
def tap(name, width, height):
    x,y = coord(CONTROL[name],width,height)
    print("TOUCH_TAP",name,x,y,flush=True)
    return adb("shell","input","tap",str(x),str(y))
def swipe(p1,p2,width,height,ms):
    x,y=coord(p1,width,height);a,b=coord(p2,width,height)
    print("TOUCH_SWIPE",(x,y),"->",(a,b),ms,flush=True)
    return adb("shell","input","swipe",str(x),str(y),str(a),str(b),str(ms),timeout=ms/1000+40)
def image_stats(before,after):
    # Central-world crop deliberately excludes most HUD buttons and
    # fps widget, though dynamic scene animations can still change it.
    width,height=before.size
    box=(int(width*.32),int(height*.3),int(width*.68),int(height*.74))
    baseline=before.crop(box).resize((180,100))
    new=after.crop(box).resize((180,100))
    delta=ImageChops.difference(baseline,new)
    values=list(delta.getdata())
    changed=sum(1 for rgb in values if max(rgb)>25)
    dist=sum(sum(v)/3 for v in values)/len(values)
    mean=ImageStat.Stat(new).mean
    return {
        "world_center_changed_pixel_pct_gt25":round(100*changed/len(values),2),
        "world_center_mean_rgb_absolute_delta":round(dist,2),
        "world_center_mean_rgb":[round(v,1) for v in mean],
        "confirms_functional_action":False,
        "reason":"Changes may be caused by game animation or post-processing; inspect side-by-side frames and game logs."
    }
def main():
    baseline_path,baseline=screenshot("09-control-baseline")
    width,height=baseline.size
    print("DEVICE_FRAME_SIZE",width,height,flush=True)
    sequence=[
       ("look_right","swipe",(.53,.53),(.68,.53),800),
       ("move_right","swipe",CONTROL["joystick"],(.23,.735),1800),
       ("fire","tap","fire"),
       ("aim","tap","aim"),
       ("reload","tap","reload"),
       ("jump","tap","jump"),
       ("crouch","tap","crouch")
    ]
    tests=[]
    before=baseline
    for event in sequence:
        name=event[0]
        if event[1]=="tap":
            output,rc=tap(event[2],width,height)
        else:
            output,rc=swipe(event[2],event[3],width,height,event[4])
        time.sleep(3.5)
        filename,after=screenshot("10-control-"+name)
        stat=image_stats(before,after)
        tests.append({
          "name":name,"adb_input_exit_code":rc,
          "screenshot":filename.name,"comparison_vs_previous_frame":stat
        })
        print("CONTROL_OBSERVATION",name,json.dumps(stat),flush=True)
        before=after
    activity,rc=adb("shell","dumpsys","activity","activities")
    mem,rc=adb("shell","dumpsys","meminfo",APP+":sp")
    procs,rc=adb("shell","pidof",APP+":sp")
    report={
      "test":"Native engine touchscreen control smoke",
      "game_screenshot_before_controls":baseline_path.name,
      "game_screenshot_size":[width,height],
      "tests":tests,
      "campaign_process_alive_after_input":bool(procs.strip()),
      "campaign_process_id":procs.strip(),
      "app_still_in_activity_dump":APP in activity,
      "memory_dump_first_lines":mem.splitlines()[:28],
      "verified_gameplay_controls":False,
      "claimed_fps_improvement":False,
      "notes":"The test records sequential touches; it cannot simulate true simultaneous multitouch via adb input commands or validate hit damage without engine state instrumentation. Emulator performance is not representative of physical ARM64 device."
    }
    target=OUTPUT/"touch-control-report.json"
    target.write_text(json.dumps(report,indent=2)+"\n",encoding="utf8")
    print("TOUCH_REPORT",json.dumps({k:v for k,v in report.items() if k!="memory_dump_first_lines"},ensure_ascii=False),flush=True)
    return report
if __name__=="__main__":
    main()
