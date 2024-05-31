from math import ceil, sqrt
import bpy
import os

name = "test"
save_dir = f"/home/luo/Picture/bld_svg/"
opt = True


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


path = save_dir + name + ".html"

os.system("rm " + path)

frame_count = scene.frame_end - scene.frame_start + 1

row = ceil(sqrt(frame_count))
col = ceil((frame_count) / row)

t = open(path, "a")
t.write(
    f"""<!DOCTYPE html>
<html>
<style>
    html,body{{
        margin: 0;
    }}
    body{{
        display: grid;
        position: absolute;
        left: 0;
        right: 0;
        top: 0;
        bottom: 0;
        grid-template-columns: repeat({col},1fr);
        grid-template-rows: repeat({row},1fr);
    }}
    svg{{
        width: 100%;
        height: 100%;
        border: 1px solid;
    }}
</style>
<body>"""
)

for i in range(scene.frame_start, scene.frame_end + 1):
    scene.frame_set(i)
    tmp_path = path + ".tmp." + str(i) + ".svg"
    bpy.ops.wm.gpencil_export_svg(
        filepath=tmp_path, use_fill=False, use_normalized_thickness=False
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
        t.write(f_opt.read())

    os.system("rm " + tmp_path + " " + tmp_path + ".opt.svg")

t.write(
    """</body>
</html>"""
)
t.close()
print("saved: " + path)
