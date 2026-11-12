#!/usr/bin/env python3
"""Port actual NZ:P v0.26 Quake IDPO model to Luanti OBJ, one native model frame per plank count.

NOT a replacement mesh or newly designed barricade. Reads the original v26
common/models/misc/window.mdl (IDPO v6, 89 frames), preserves its triangles,
UVs, and source texture, and exports the original health frames (0,6,...41).
NZ:P Team model CC BY-SA 4.0. Original QuakeC: server/entities/window.qc.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import struct
import json

FRAMES = {6: 0, 5: 6, 4: 13, 3: 20, 2: 27, 1: 34, 0: 41}
# Quake unit -> Luanti node conversion only, no geometry redesign.
UNIT = 100.0

def i32(data, offset):
    return struct.unpack_from("<i", data, offset)[0]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mdl", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    data = args.mdl.read_bytes()
    if len(data) < 84 or data[:4] != b"IDPO" or i32(data,4)!=6:
        raise SystemExit("Expected exact NZ:P Quake IDPO v6 model")
    sx,sy,sz,ox,oy,oz = struct.unpack_from("<6f",data,8)
    numskins,w,h,nverts,ntris,nframes=struct.unpack_from("<6i",data,48)
    if (numskins,w,h,nverts,ntris,nframes)!=(1,128,16,132,72,89):
        raise SystemExit("Original NZ:P window mesh header has changed")
    cursor=84
    for _ in range(numskins):
        skintype=i32(data,cursor)
        cursor+=4
        if skintype!=0:raise SystemExit("Grouped skins unsupported")
        cursor+=w*h
    stverts=[]
    for i in range(nverts):
        stverts.append(struct.unpack_from("<3i",data,cursor))
        cursor+=12
    faces=[]
    for i in range(ntris):
        faces.append(struct.unpack_from("<4i",data,cursor))
        cursor+=16
    outputs={}
    args.output.mkdir(parents=True, exist_ok=True)
    for frame_idx in range(nframes):
        if i32(data,cursor)!=0:raise SystemExit("Frame grouping changed")
        cursor+=4+8
        frame_name=data[cursor:cursor+16].split(b"\0")[0].decode("ascii")
        cursor+=16
        vertices=[]
        for j in range(nverts):
            vx,vy,vz,normal=struct.unpack_from("<4B",data,cursor)
            cursor+=4
            x=vx*sx+ox
            y=vy*sy+oy
            z=vz*sz+oz
            vertices.append((x,y,z))
        if frame_idx not in FRAMES.values():
            continue
        stage=next(stage for stage,f in FRAMES.items() if frame_idx==f)
        path=args.output/f"nzp_v26_window_{stage}.obj"
        out=[
            "# NZ:P Team original window.mdl frame "+str(frame_idx)+" ("+frame_name+")",
            "# CC BY-SA 4.0; converted for Luanti coordinates only",
            "mtllib nzp_v26_window.mtl",
            "o nzp_v26_window_"+str(stage),
            "usemtl nzp_v26_window",
        ]
        for (x,y,z) in vertices:
            # Quake Y = horizontal plank direction; Quake Z = height;
            # Quake X = thin window depth. Center only for voxel placement.
            out.append("v %.6f %.6f %.6f"%(y/UNIT,(z-8)/UNIT,-(x+2.5)/UNIT))
        # Generate UV per triangle corner, preserving Quake backside seam.
        uv_idx=0
        tris_kept=0
        face_lines=[]
        for facesfront,a,b,c in faces:
            if any(i<0 or i>=nverts for i in (a,b,c)):
                raise SystemExit("Invalid original triangle")
            coords=[vertices[i] for i in (a,b,c)]
            # The v26 model moves removed planks to -100 units offscreen.
            # Do not draw invisible thrown-away planks in Luanti.
            if any(x < -60 or z < -60 for x,y,z in coords):
                continue
            vts=[]
            for idx in (a,b,c):
                onseam,s,t=stverts[idx]
                if not facesfront and onseam:
                    s+=w//2
                u=(s+0.5)/w
                v=1-(t+0.5)/h
                out.append(f"vt {u:.6f} {v:.6f}")
                uv_idx+=1
                vts.append(uv_idx)
            face_lines.append("f %d/%d %d/%d %d/%d"%(a+1,vts[0],b+1,vts[1],c+1,vts[2]))
            tris_kept+=1
        # Quake triangles winding can differ after axis conversion; double-sided
        # material is selected on the Lua side. Preserve face index ordering.
        out+=face_lines
        path.write_text("\n".join(out)+"\n")
        outputs[stage]={"model":path.name,"original_frame":frame_idx,"triangles":tris_kept}
    if cursor!=len(data):
        raise SystemExit(f"Unexpected trailing model data: {cursor}/{len(data)}")
    (args.output/"nzp_v26_window.mtl").write_text(
        "newmtl nzp_v26_window\nKd 1.0 1.0 1.0\nmap_Kd nzp_v26_window.png\n"
    )
    (args.output/"nzp_v26_window_manifest.json").write_text(json.dumps(outputs,indent=2))
    for stage in sorted(outputs):
        print(f"NZ:P original planks {stage}: frame {outputs[stage]['original_frame']} triangles {outputs[stage]['triangles']}",flush=True)
    assert outputs[6]["triangles"]>outputs[0]["triangles"],"plank disappearance not detected"
    print("PASS: 89-frame NZ:P model converted to real 7-state Luanti OBJ meshes")
if __name__=="__main__":
    main()
