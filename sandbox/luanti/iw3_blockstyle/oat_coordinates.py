"""Match XANIM root tracks to OpenAssetTools v0.34.0's glTF export frame.

OAT GltfWriter.cpp premultiplies GLOBAL joint frames by Rx(-90 degrees),
then computes child locals. Consequently child local XANIM tracks stay in
IW3 coordinates; only skeleton roots need C*t and C*q. Applying C to every
joint, or conjugating every local quaternion, would convert the rig twice.
"""
from copy import deepcopy
import math


def multiply_quaternions(a, b):
    x, y, z, w = a
    X, Y, Z, W = b
    return (w*X+x*W+y*Z-z*Y, w*Y-x*Z+y*W+z*X,
            w*Z+x*Y-y*X+z*W, w*W-x*X-y*Y-z*Z)


def oat_root_tracks(doc, animation):
    """Copy a native IW3 animation; convert only exported skeleton roots."""
    joints = {i for skin in doc.get("skins", []) for i in skin["joints"]}
    parents = {c: i for i, n in enumerate(doc.get("nodes", []))
               for c in n.get("children", [])}
    roots = {doc["nodes"][i].get("name", "").casefold()
             for i in joints if parents.get(i) not in joints}
    converted = deepcopy(animation)
    rotation = (-math.sqrt(.5), 0., 0., math.sqrt(.5))
    changed = []
    for bone in converted.bones:
        if bone.name.casefold() not in roots:
            continue
        if bone.translations is not None:
            bone.translations.values = [(x, z, -y)
                                        for x, y, z in bone.translations.values]
        if bone.rotations is not None:
            bone.rotations.values = [multiply_quaternions(rotation, q)
                                    for q in bone.rotations.values]
        if bone.translations is not None or bone.rotations is not None:
            changed.append(bone.name)
    return converted, sorted(changed)
