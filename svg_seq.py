import bpy
import os

name = "test"

save_dir = f"/home/luo/Picture/bld_svg/{name}/"

scene = bpy.context.scene

os.system("mkdir -p " + save_dir)

print(save_dir)


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

def write_seq():
    for i in range(scene.frame_start, scene.frame_end + 1):
        scene.frame_set(i)
        path = save_dir + name + "_" + str(i) + ".svg"
        bpy.ops.wm.gpencil_export_svg(
            filepath=path,
            use_fill=True,
            use_normalized_thickness=False,
            use_clip_camera=True,
        )
        with open(path, "r+") as f:
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
