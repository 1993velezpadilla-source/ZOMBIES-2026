"""Match XANIM root tracks to OpenAssetTools v0.34.0's glTF export frame.

OAT GltfWriter.cpp premultiplies GLOBAL joint frames by Rx(-90 degrees),
then computes child locals. Consequently child local XANIM tracks stay in
IW3 coordinates; only skeleton roots need C*t and C*q. Applying C to every
joint, or conjugating every local quaternion, would convert the rig twice.
"""
from copy import deepcopy
import math
from iw3_xanim_v17 import Track


def multiply_quaternions(a, b):
    x, y, z, w = a
    X, Y, Z, W = b
    return (w*X+x*W+y*Z-z*Y, w*Y-x*Z+y*W+z*X,
            w*Z+x*Y-y*X+z*W, w*W-x*X-y*Y-z*Z)


def oat_animation_tracks(doc, animation):
    """Convert IW3 absolute rotations + bind-relative translation offsets.

    DObjCalcNonRootBones adds model->trans to evaluated XANIM translation.
    XAnimCalcParts writes identity for NO_QUAT, not the model's bind rotation.
    These semantics apply to named animation bones, not absent bones.
    """
    joints = {i for skin in doc.get("skins", []) for i in skin["joints"]}
    parents = {c: i for i, n in enumerate(doc.get("nodes", []))
               for c in n.get("children", [])}
    roots = {doc["nodes"][i].get("name", "").casefold()
             for i in joints if parents.get(i) not in joints}
    nodes = {doc["nodes"][i].get("name", "").casefold():doc["nodes"][i]
             for i in joints}
    converted = deepcopy(animation)
    rotation = (-math.sqrt(.5), 0., 0., math.sqrt(.5))
    changed = [];translations=[];identities=[]
    for bone in converted.bones:
        name=bone.name.casefold()
        if name not in nodes:
            continue
        if bone.rotations is None:
            bone.rotations=Track([0],[(0.,0.,0.,1.)])
            identities.append(bone.name)
        if name not in roots:
            if bone.translations is not None:
                bind=nodes[name].get("translation",[0.,0.,0.])
                bone.translations.values=[tuple(b+d for b,d in zip(bind,t))
                                          for t in bone.translations.values]
                translations.append(bone.name)
            continue
        if bone.translations is not None:
            bone.translations.values = [(x, z, -y)
                                        for x, y, z in bone.translations.values]
        if bone.rotations is not None:
            bone.rotations.values = [multiply_quaternions(rotation, q)
                                    for q in bone.rotations.values]
        if bone.translations is not None or bone.rotations is not None:
            changed.append(bone.name)
    return converted, {"oat_root_tracks_converted":sorted(changed),
        "bind_offsets_added_to_translation_tracks":sorted(translations),
        "no_quat_identity_tracks":sorted(identities)}
