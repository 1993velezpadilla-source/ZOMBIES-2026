#!/usr/bin/env python3
"""Generate a FIRST-PERSON-only version of our ORIGINAL AK-47 model.

The existing original GLB (47 parts) remains for editable source/third-person
reference. The new FPS GLB excludes the stock that physically occupies the
camera lens when aiming through the sights. It retains magazine, bolt and hand
bones for per-part reload motion; uses no TaCZ or Project Aether art.

Runs the already committed, self-contained V3 original generator in a temp
directory with just the *four* behind-the-camera stock boxes omitted.
"""
import ast
import json
import shutil
import struct
import sys
import tempfile
from pathlib import Path

REPO=Path(__file__).resolve().parents[3]
SOURCE=REPO/"sandbox/luanti/v3/build_ak47_assets.py"
OMIT={"wood_stock_neck","wood_stock_middle","wood_stock_butt","butt_plate"}
SCREEN_WIDTH=1536
SCREEN_HEIGHT=794
VERTICAL_FOV_DEG=72.0
SCALE=3.10
ADS_POS=(0.0,-2.70,31.5)
HIP_POS=(8.0,-6.5,31.0)

def output_model(dest):
    tree=ast.parse(SOURCE.read_text(encoding="utf8"))
    removed=[]
    # Only remove literal source box calls by their named identifiers; retain
    # all other source lines unchanged, including 3D generator assertions.
    for node in ast.walk(tree):
        if not isinstance(node,ast.Expr) or not isinstance(node.value,ast.Call):
            continue
        call=node.value
        if not isinstance(call.func,ast.Name) or call.func.id!="box" or not call.args:
            continue
        if isinstance(call.args[0],ast.Constant) and call.args[0].value in OMIT:
            removed.append(node)
    names=[x.value.args[0].value for x in removed]
    if set(names)!=OMIT or len(names)!=4:
        raise RuntimeError(f"Expected to hide exactly four stock boxes, got {names}")
    class RemoveStock(ast.NodeTransformer):
        def visit_Expr(self,node):
            return None if node in removed else self.generic_visit(node)
    tree=RemoveStock().visit(tree)
    ast.fix_missing_locations(tree)
    with tempfile.TemporaryDirectory(prefix="ak47-fps-") as d:
        old_argv=sys.argv[:]
        try:
            sys.argv=[str(SOURCE),d]
            exec(compile(tree,str(SOURCE),"exec"),{"__name__":"__main__",
                                                   "__file__":str(SOURCE)})
        finally:
            sys.argv=old_argv
        source=Path(d)
        glb=(source/"models/ak47dev_animated.glb").read_bytes()
        if not glb.startswith(b"glTF"):
            raise RuntimeError("Original GLB generator did not produce a GLB")
        (dest/"models").mkdir(parents=True,exist_ok=True)
        (dest/"models/ak47dev_fp.glb").write_bytes(glb)
        shutil.copyfile(source/"AK47_EDITABLE.bbmodel",
                        dest/"AK47_FP_EDITABLE.bbmodel")
        # File contains five original bones and a real 3.75s reload timeline.
        chunk_len,chunk_type=struct.unpack_from("<I4s",glb,12)
        assert chunk_type==b"JSON"
        doc=json.loads(glb[20:20+chunk_len])
        assert len(doc["skins"][0]["joints"])==5
        assert len(doc["animations"][0]["channels"])==10
        assert len(doc["meshes"][0]["primitives"])==4
        bb=json.loads((dest/"AK47_FP_EDITABLE.bbmodel").read_text())
        model_names={e["name"] for e in bb["elements"]}
        assert len(model_names)==43,len(model_names)
        assert not (OMIT & model_names)
        for part in ("receiver","mag_top","bolt","rear_sight_notch",
                     "front_sight_post","left_glove","right_glove"):
            assert part in model_names,part
        print("AK FPS GLB generated: 43 original components, zero stock "
              "obstruction, five bones and preserved magazine/bolt/hand motion")

def sight_projection():
    # Analytical screen-space validation of both iron sights with the exact
    # transform values used in Luanti's camera-only ADS pose. This will catch
    # oversized guns whose sights miss the center before distributing an APK.
    import math
    focal=SCREEN_HEIGHT/(2*math.tan(math.radians(VERTICAL_FOV_DEG/2)))
    def project(x,y,z):
        X=ADS_POS[0]+x*SCALE
        Y=ADS_POS[1]+y*SCALE
        Z=ADS_POS[2]+z*SCALE
        return SCREEN_WIDTH/2+focal*X/Z,SCREEN_HEIGHT/2-focal*Y/Z
    front=project(0,.96,8.88)
    rear=project(0,.82,2.25)
    center=(SCREEN_WIDTH/2,SCREEN_HEIGHT/2)
    for x,y in (front,rear):
        assert abs(x-center[0])<3,(x,center)
        assert abs(y-center[1])<8,(y,center)
    assert abs(front[1]-rear[1])<9,(front,rear)
    print(f"AK sight preflight: front={front}, rear={rear}, crosshair={center}, "
          "both within 8 px of center in 1536x794 at 72deg vertical FOV")
    return dict(front=front,rear=rear,crosshair=center)

def main():
    if len(sys.argv)!=2:
        raise SystemExit("build_fp_viewmodel.py <ak47_mod_root>")
    dest=Path(sys.argv[1])
    output_model(dest)
    sight_projection()

if __name__=="__main__":
    main()
