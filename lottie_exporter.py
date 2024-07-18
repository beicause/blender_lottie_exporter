import shutil
import bpy
import os
import base64
import json
import re
from bpy_extras.io_utils import ExportHelper
import sys

# debug
# def print(*data):
#     for window in bpy.context.window_manager.windows:
#         screen = window.screen
#         for area in screen.areas:
#             if area.type == "CONSOLE":
#                 override = {"window": window, "screen": screen, "area": area}
#                 with bpy.context.temp_override(**override):
#                     bpy.ops.console.scrollback_append(
#                         text=str(" ".join([str(x) for x in data])), type="OUTPUT"
#                     )


def write_seq(filepath: str, frame_start, frame_end, opt: bool, scene: bpy.types.Scene):
    os.mkdir(f"{filepath}_seq_dir")
    for i in range(frame_start, frame_end + 1):
        scene.frame_set(i)
        path = f"{filepath}_seq_dir/{str(i)}.svg"
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
                    "<!-- Generator: Blender, SVG Export for Grease Pencil - v1.0 -->\n",
                    "",
                )
                .replace("<?xml?>\n", "")
            )
            f.seek(0)
            f.truncate()
            if opt:
                from scour.scour import scourString

                svg = scourString(
                    svg,
                    {
                        "enable_id_stripping": 1,
                        "enable_comment_stripping": 1,
                        "shorten_ids": 1,
                        "indent": None,
                        "strip_xml_prolog": 1,
                        "remove_descriptive_elements": 1,
                        "no_line_breaks": 1,
                        "strip_xml_space": 1,
                    },
                )
            f.write(svg)


def export_lottie(
    filepath: str,
    frame_rate: int,
    frame_start: int,
    frame_end: int,
    opt: bool,
    scene: bpy.types.Scene,
):
    frame_count = frame_end - frame_start + 1
    lottie = {
        "v": "5.5.2",
        "fr": frame_rate,
        "ip": 0,
        "op": frame_count - 1,
        "w": -1,  # init later
        "h": -1,  # init later
        "assets": [],
        # "fonts": {"list": []},
        "layers": [],
    }
    write_seq(filepath, frame_start, frame_end, opt, scene)
    for i in range(frame_start, frame_end + 1):
        f = open(
            f"{filepath}_seq_dir/{str(i)}.svg",
            "r",
        )
        svg = f.read()
        f.close()
        width_span = re.search(r"width=\"\d+\"", svg).span()
        height_span = re.search(r"height=\"\d+\"", svg).span()
        width = int(svg[width_span[0] : width_span[1]].split('"')[-2])
        height = int(svg[height_span[0] : height_span[1]].split('"')[-2])
        if lottie["w"] < width:
            lottie["w"] = width
        if lottie["h"] < height:
            lottie["h"] = height
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
            "w": width,  # number
            # Width of the image
            "h": height,  # number
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
            "st": i / frame_rate,  # number
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
    shutil.rmtree(f"{filepath}_seq_dir")
    with open(filepath, "w") as t:
        json.dump(lottie, t)


bl_info = {
    "name": "Grease Pencil Lottie Exporter",
    "description": "grease pencil lottie exporter",
    "author": "Luo Zhihao",
    "version": (1, 0),
    "blender": (4, 0, 0),
    "location": "File > Export > Grease Pencil as Lottie",
    # "warning": "", # used for warning icon and text in addons panel
    # "doc_url": "http://archive.blender.org/wiki/2015/index.php/Extensions:2.6/Py/Scripts/My_Script",
    "tracker_url": "https://github.com/beicause/grease-pencil-lottie/issues",
    "support": "COMMUNITY",
    "category": "Import-Export",
}


class LottieExporter(bpy.types.Operator, ExportHelper):
    """Export Lottie"""

    bl_idname = "lottie_exporter.exporter"
    bl_label = "Export Lottie"

    filename_ext = ".json"
    filter_glob: bpy.props.StringProperty(default="*.json", options={"HIDDEN"})

    optimize_svg: bpy.props.BoolProperty(
        name="Optimize SVG",
        description="Optimize/clean SVG using Scour",
        default=True,
    )
    frame_rate: bpy.props.IntProperty(
        name="Frame Rate",
        description="Lottie frame rate for export",
        default=24,
        min=1,
        max=1000,
    )

    frame_start: bpy.props.IntProperty(
        name="Start Frame",
        description="Start frame for export",
        default=1,
        min=0,
        max=10000,
    )

    frame_end: bpy.props.IntProperty(
        name="End Frame",
        description="End frame for export",
        default=250,
        min=0,
        max=10000,
    )

    def execute(self, context):
        export_lottie(
            self.filepath,
            self.frame_rate,
            self.frame_start,
            self.frame_end,
            self.optimize_svg,
            context.scene,
        )
        return {"FINISHED"}

    def invoke(self, context, event):
        self.frame_start = context.scene.frame_start
        self.frame_end = context.scene.frame_end
        self.frame_rate = context.scene.render.fps

        wm = context.window_manager
        wm.fileselect_add(self)
        return {"RUNNING_MODAL"}


def log_append(str):
    bpy.context.preferences.addons[__name__].preferences.captured_logs.append(str)


def run_command(commands=[], output_log=True, return_full_result=False):
    from subprocess import Popen, PIPE

    texts = []
    with Popen(commands, stdout=PIPE, shell=False) as p:
        while p.poll() is None:
            text = p.stdout.readline().decode("utf-8")
            if len(text) > 0:
                texts.append(text)
                print(text)
                if output_log:
                    log_append(text)
                    bpy.context.region.tag_redraw()
        return texts if return_full_result else p.returncode


def modify_package(command, option, name):
    """
    Install or remove a Python package through pip
    """
    python_exe = sys.executable

    res = run_command([python_exe, "-m", "ensurepip", "--upgrade"])
    if res > 0:
        return False
    # Use an alternative source for triangle in MacOS with Apple Silicon
    # import platform
    # if name == 'triangle' and command == 'install' and platform.machine() == 'arm64':
    # res = run_command([python_exe, '-m', 'pip', command, option, 'triangle2'])
    # else:
    res = run_command([python_exe, "-m", "pip", command, option, name])
    if res > 0:
        return False
    bpy.ops.lottie_exporter.check_dependencies(output_log=False)
    return True


class ClearLogs(bpy.types.Operator):
    """
    Clear the captured logs from the Preferences panel
    """

    bl_idname = "lottie_exporter.clear_logs"
    bl_label = "Clear Logs"
    bl_description = "Clear the captured logs from the Preferences panel"
    bl_options = {"REGISTER", "INTERNAL"}

    def execute(self, context):
        bpy.context.preferences.addons[__name__].preferences.captured_logs.clear()
        return {"FINISHED"}


class ApplyCustomLibPath(bpy.types.Operator):
    """
    Add the custom site-package path to the package search path
    """

    bl_idname = "lottie_exporter.apply_custom_lib_path"
    bl_label = "Apply Custom Package Path"
    bl_description = "Add the custom site-package path to the package search path"
    bl_options = {"REGISTER", "INTERNAL"}

    output_log: bpy.props.BoolProperty(default=True)

    def execute(self, context):
        custom_lib_path = bpy.context.preferences.addons[
            __name__
        ].preferences.custom_lib_path
        if len(custom_lib_path) > 0 and custom_lib_path not in sys.path:
            sys.path.append(custom_lib_path)
        if self.output_log:
            log_append("[LottieExporter Info] Package Search Paths Updated:")
            for path in sys.path:
                log_append(path)
        return {"FINISHED"}


class DetectDependencies(bpy.types.Operator):
    """
    Check if required Python packages are installed
    """

    bl_idname = "lottie_exporter.check_dependencies"
    bl_label = "Check Dependencies"
    bl_description = "Check if required Python packages are installed"
    bl_options = {"REGISTER", "INTERNAL"}

    output_log: bpy.props.BoolProperty(default=True)

    def execute(self, context):
        preferences = context.preferences.addons[__name__].preferences
        preferences.package_scour = True
        try:
            import scour

            if self.output_log:
                log_append("[LottieExporter Info] Package Scour:")
                log_append("  Version: " + str(scour.__version__))
                log_append("  Location: " + str(scour.__file__))
        except:
            preferences.package_scour = False
        return {"FINISHED"}


class InstallDependency(bpy.types.Operator):
    bl_idname = "lottie_exporter.dependencies_install"
    bl_label = "Install"
    bl_description = "Manage packages through pip"
    bl_options = {"REGISTER", "INTERNAL"}

    package_name: bpy.props.StringProperty()

    def execute(self, context):
        res = modify_package("install", "--no-input", self.package_name)
        if res:
            self.report({"INFO"}, "Python package installed successfully.")
            log_append("[LottieExporter Info] Python package installed successfully.")

            # Check if the custom site-package path needs to be updated
            installed_package_info = run_command(
                [sys.executable, "-m", "pip", "show", self.package_name],
                output_log=False,
                return_full_result=True,
            )
            custom_lib_path = bpy.context.preferences.addons[
                __name__
            ].preferences.custom_lib_path
            for str in installed_package_info:
                if str.startswith("Location:"):
                    site_packages_path = str[9:].strip()
                    if site_packages_path not in sys.path:
                        bpy.context.preferences.addons[
                            __name__
                        ].preferences.custom_lib_path = site_packages_path
                        bpy.ops.lottie_exporter.apply_custom_lib_path(output_log=False)
                        log_append(
                            "[LottieExporter Info] Package Search Path Updated Automatically."
                        )
                        return {"FINISHED"}

        else:
            self.report({"ERROR"}, "Cannot install the required package.")
            log_append("[LottieExporter Error] Cannot install the required package.")

        return {"FINISHED"}


class RemoveDependency(bpy.types.Operator):
    bl_idname = "lottie_exporter.dependencies_remove"
    bl_label = "Remove"
    bl_description = "Manage packages through pip"
    bl_options = {"REGISTER", "INTERNAL"}

    package_name: bpy.props.StringProperty()

    def execute(self, context):
        res = modify_package("uninstall", "-y", self.package_name)
        self.report({"INFO"}, "Please restart Blender to apply the changes.")
        log_append("[LottieExporter Info] Please restart Blender to apply the changes.")
        return {"FINISHED"}


class LottieExporterAddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    custom_lib_path: bpy.props.StringProperty(
        name="Custom Site-Packages Path",
        subtype="DIR_PATH",
        description="An additional directory that the add-on will try to load packages from",
        default="",
    )
    cache_folder: bpy.props.StringProperty(
        name="Cache Folder",
        subtype="DIR_PATH",
        description="Location storing temporary files. Use the default temporary folder when empty",
        default="",
    )
    package_scour: bpy.props.BoolProperty(name="Scour Installed", default=False)
    show_full_logs: bpy.props.BoolProperty(name="Show Full Logs", default=True)
    captured_logs = []

    def draw(self, context):
        layout = self.layout
        # wiki_url = "https://github.com/chsh2/nijiGPen/wiki/Dependency-Installation"
        # wiki_url = "https://chsh2.github.io/nijigp/docs/get_started/installation/"

        # Dependency manager
        row = layout.row()
        row.label(text="Dependency Management", icon="PREFERENCES")
        row.separator()
        # row.operator("wm.url_open", text="Help", icon="HELP").url = wiki_url
        box1 = layout.box()

        # Custom package path
        row = box1.row()
        row.label(text="Custom Package Path:", icon="DECORATE_KEYFRAME")
        row.separator()
        row.operator(
            "lottie_exporter.apply_custom_lib_path", text="Apply", icon="FILE_REFRESH"
        )
        column = box1.box().column(align=True)
        column.prop(self, "custom_lib_path", text="Site-Packages")

        # Summary table
        row = box1.row()
        row.label(text="Summary:", icon="DECORATE_KEYFRAME")
        row.separator()
        row.operator(
            "lottie_exporter.check_dependencies", text="Check", icon="FILE_REFRESH"
        )
        table_key = ["[Package]", "[Status]", "[Actions]", ""]
        packages = [
            {
                "name": "Scour",
                "signal": self.package_scour,
                "package": "scour",
            }
        ]
        column = box1.box().column(align=True)
        row = column.row()
        for key in table_key:
            row.label(text=key)
        for p in packages:
            row = column.row()
            row.label(text=p["name"])
            if p["signal"]:
                row.label(text="OK")
            else:
                row.label(text="Not Installed")
            row.operator("lottie_exporter.dependencies_install").package_name = p[
                "package"
            ]
            row.operator("lottie_exporter.dependencies_remove").package_name = p[
                "package"
            ]

        # Show captured logs
        row = box1.row()
        row.label(text="Logs:", icon="DECORATE_KEYFRAME")
        row.separator()
        row.prop(self, "show_full_logs")
        row.operator("lottie_exporter.clear_logs", text="Clear", icon="TRASH")
        column = box1.box().column(align=True)
        oldest_log = 0 if self.show_full_logs else max(0, len(self.captured_logs) - 5)
        if oldest_log > 0:
            column.label(text="...")
        for i in range(oldest_log, len(self.captured_logs)):
            column.label(text=self.captured_logs[i])


def menu_func(self, context):
    default_path = os.path.splitext(bpy.data.filepath)[0] + ".json"
    self.layout.operator(
        LottieExporter.bl_idname, text="Grease Pencil as Lottie (.json)"
    ).filepath = default_path


def register():
    bpy.utils.register_class(ApplyCustomLibPath)
    bpy.utils.register_class(DetectDependencies)
    bpy.utils.register_class(InstallDependency)
    bpy.utils.register_class(RemoveDependency)
    bpy.utils.register_class(ClearLogs)
    bpy.utils.register_class(LottieExporter)
    bpy.utils.register_class(LottieExporterAddonPreferences)
    bpy.types.TOPBAR_MT_file_export.append(menu_func)


def unregister():
    bpy.utils.unregister_class(ApplyCustomLibPath)
    bpy.utils.unregister_class(DetectDependencies)
    bpy.utils.unregister_class(InstallDependency)
    bpy.utils.unregister_class(RemoveDependency)
    bpy.utils.unregister_class(ClearLogs)
    bpy.utils.unregister_class(LottieExporter)
    bpy.utils.unregister_class(LottieExporterAddonPreferences)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func)


if __name__ == "__main__":
    register()
