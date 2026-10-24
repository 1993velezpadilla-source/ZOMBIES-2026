#!/usr/bin/env python3
"""Read-only diagnosis: red-tinted scene vs HUD and Android renderer memory.

No game binaries or game data are changed. The measurements do not infer
root cause from color alone.
"""
from __future__ import annotations
import json
from pathlib import Path
import subprocess
import time
from PIL import Image,ImageStat

ROOT=Path("smoke-out/real-data-test")
ROOT.mkdir(parents=True,exist_ok=True)
PACKAGE="com.cod4.firstmission:sp"

def command(*parts,timeout=35):
    r=subprocess.run(["adb",*parts],capture_output=True,text=True,timeout=timeout)
    return (r.stdout + "\n" + r.stderr).strip()

def region(img, xyxy):
    w,h=img.size
    return img.crop((round(xyxy[0]*w),round(xyxy[1]*h),round(xyxy[2]*w),round(xyxy[3]*h))).resize((180,90)).convert("RGB")
REGIONS={
    "center_scene":(.32,.22,.68,.70),
    "top_left_scene":(.08,.16,.32,.41),
    "upper_right_scene":(.64,.13,.89,.38),
    "bottom_right_hud":(.78,.68,.98,.97),
}
def rgb_stats(img):
    arr=list(img.getdata())
    n=len(arr)
    red=sum(1 for r,g,b in arr if r>=35 and r>max(2*g,2*b,15))
    magenta=sum(1 for r,g,b in arr if r>=35 and b>=25 and r>1.6*g)
    black=sum(1 for r,g,b in arr if max(r,g,b)<16)
    stat=ImageStat.Stat(img).mean
    return {"mean_rgb":[round(x,2) for x in stat],
            "red_dominant_percent":round(red*100/n,2),
            "magenta_percent":round(magenta*100/n,2),
            "near_black_percent":round(black*100/n,2)}
def analyze_images():
    sources=sorted(ROOT.glob("08-loading-observe-*.png"))+sorted(ROOT.glob("10-control-*.png"))
    rows=[]
    for file in sources:
        with Image.open(file) as opened:
            image=opened.convert("RGB")
            metrics={name:rgb_stats(region(image,box)) for name,box in REGIONS.items()}
            rows.append({"screenshot":file.name,"size":image.size,"regions":metrics})
    return rows
def sample_mem(stage):
    mem=command("shell","dumpsys","meminfo",PACKAGE,timeout=40)
    proc=command("shell","pidof",PACKAGE)
    gfx=command("shell","dumpsys","gfxinfo",PACKAGE,"framestats",timeout=40)
    surface=command("shell","dumpsys","SurfaceFlinger",timeout=40)
    (ROOT/("renderer-mem-"+stage+".txt")).write_text(mem[:9500]+"\n")
    (ROOT/("renderer-gfxinfo-"+stage+".txt")).write_text(gfx[:8500]+"\n")
    # No raw SurfaceFlinger dump artifact; pick only generic backend lines.
    print("RENDERER_SAMPLE",stage,"pid",proc.strip(),"\n",mem[:2000],flush=True)
    return {"stage":stage,"pid":proc.strip(),"meminfo_head":mem.splitlines()[:60],
            "gfxinfo_head":gfx.splitlines()[:25],
            "surface_backend_samples":[x.strip() for x in surface.splitlines()
                 if any(t in x.lower() for t in ("gles","egl","vulkan","gpu", "renderengine"))][:35]}
def main():
    observations=analyze_images()
    props={k:command("shell","getprop",k) for k in (
        "ro.hardware.egl","ro.hardware.vulkan","ro.product.cpu.abilist",
        "ro.dalvik.vm.native.bridge","ro.build.version.release","ro.opengles.version")}
    report={
        "scope":"Software renderer color measurements and process memory; not source-level shader diagnostics",
        "gpu_backend_intent":"See paired workflow argument -gpu; emulator guest properties may not uniquely reveal backend.",
        "android_properties":props,
        "snapshots":observations,
        "single_final_mem_sample":sample_mem("last"),
        "red_root_cause_proven":False,
        "fps_increased_proven":False,
        "note":"Red pixel dominance alone cannot distinguish GL texture/shader bugs from in-game post-processing, overlays or red illumination."
    }
    (ROOT/"renderer-diagnostic.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print("RENDER_DIAGNOSTIC_SUMMARY",json.dumps({
        "android":props,
        "frames":[{"name":r["screenshot"],"scene":r["regions"]["center_scene"],"hud":r["regions"]["bottom_right_hud"]} for r in observations]
    },ensure_ascii=False),flush=True)
if __name__=="__main__":
    main()
