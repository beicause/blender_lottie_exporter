import base64
import json
from math import ceil, sqrt
import re
import bpy
import os

name = "test"
save_dir = f"/home/luo/Picture/bld_svg/"
opt = True


scene = bpy.context.scene

os.system("mkdir -p " + save_dir)

print("Save dir: ", save_dir)


def print(*data):
    for window in bpy.context.window_manager.windows:
        screen = window.screen
        for area in screen.areas:
            if area.type == "CONSOLE":
                override = {"window": window, "screen": screen, "area": area}
                with bpy.context.temp_override(**override):
                    bpy.ops.console.scrollback_append(
                        text=str(" ".join([str(x) for x in data])), type="OUTPUT"
                    )


path = save_dir + name + ".json"

os.system("rm " + path)

frame_count = scene.frame_end - scene.frame_start + 1

row = ceil(sqrt(frame_count))
col = ceil((frame_count) / row)

lottie = {
    "v": "5.5.2",
    "fr": 60,
    "ip": 0,
    "op": frame_count - 1,
    "w": -1,
    "h": -1,
    "ddd": 0,
    "assets": [],
    # "fonts": {"list": []},
    "layers": [],
}
t = open(path, "w")


for i in range(scene.frame_start, scene.frame_end + 1):
    scene.frame_set(i)
    tmp_path = path + ".tmp." + str(i) + ".svg"
    bpy.ops.wm.gpencil_export_svg(
        filepath=tmp_path, use_fill=True, use_normalized_thickness=True
    )
    f = open(tmp_path, "r+")
    svg = f.read()
    svg = (
        svg.replace("<?:anonymous?>\n", "")
        .replace(
            "<!-- Generator: Blender, SVG Export for Grease Pencil - v1.0 -->\n", ""
        )
        .replace("<?xml?>\n", "")
    )
    f.seek(0)
    f.truncate()
    f.write(svg)
    f.close()

    if opt:
        cmd = f"/home/luo/micromamba/bin/scour -i {tmp_path} -o {tmp_path}.opt.svg --enable-id-stripping --enable-comment-stripping --shorten-ids --indent=none --strip-xml-prolog --remove-descriptive-elements --no-line-breaks --strip-xml-space"
        os.system(cmd)

    with open(tmp_path + (".opt.svg" if opt else ""), "r") as f_opt:
        svg = f_opt.read()
    view_box = re.search(r"viewBox=\"\d+ \d+ \d+ \d+\"", svg).span()
    size = [int(x) for x in (svg[view_box[0] : view_box[1]].split('"')[-2].split(" "))]

    asset = {
        "id": f"svg_{i}",  # string
        # Unique identifier used by layers when referencing this asset
        "nm": f"svg_{i}",  # string
        # Human readable name
        "u": "",  # string
        # Path to the directory containing a file
        "p": f"data:image/svg+xml;base64,{base64.b64encode(svg.encode()).decode()}",  # string
        # Filename or data url
        "e": 1,  # integer
        # Whether the file is embedded
        "w": size[2] - size[0],  # number
        # Width of the image
        "h": size[3] - size[1],  # number
        # Height of the image
        "t": "seq",  # string = 'seq'
        # Marks as part of an image sequence if present
        # "sid": "",  # string
        # One of the ID in the file's slots
    }
    lottie["assets"].append(asset)
    layer = {
        "nm": f"frame_{i}",  # string
        # Name
        # Name, as seen from editors and the like
        "hd": False,  # boolean
        # Hidden
        # Whether the layer is hidden
        "ty": 2,  # integer = 2
        # Type
        # Layer type
        # "ind": i,  # integer
        # Index
        # Index that can be used for parenting and referenced in expressions
        # "parent": i - 1 if i >= 1 else None,  # integer
        # Parent Index
        # Must be the ind property of another layer
        # "sr": 1,  # number
        # Time Stretch
        # Time Stretch
        "ip": i,  # number
        # In Point
        # Frame when the layer becomes visible
        "op": i + 1,  # number
        # Out Point
        # Frame when the layer becomes invisible
        "st": i / 60,  # number
        # Start Time
        # Start Time
        "ks": {},  # Transform
        # Transform
        # Layer transform
        "ao": 0,  # integer
        # Auto Orient
        # If 1, The layer will rotate itself to match its animated position path
        "refId": f"svg_{i}",  # string
        # Reference Id
        # ID of the image as specified in the assets
    }
    if asset["w"] > lottie["w"]:
        lottie["w"] = asset["w"]
    if asset["h"] > lottie["h"]:
        lottie["h"] = asset["h"]

    lottie["layers"].append(layer)
    os.system("rm " + tmp_path + " " + tmp_path + ".opt.svg")

json.dump(lottie, t)
t.close()
print("Saved: " + path)
