# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8-80 compliant>

import os
script_file = os.path.realpath(__file__)
directory = os.path.dirname(script_file)

bl_info = {
    "name": "EXOR Mesh format",
    "author": "lukaasm",
    "version": (1, 0, 0),
    "blender": (2, 81, 6),
    "location": "File > Export",
    "description": "Export EXOR Mesh",
    "warning": "",
    "wiki_url": "https://docs.blender.org/manual/en/latest/addons/io_scene_obj.html",
    "support": '',
    "category": "Export"}

if "bpy" in locals():
    import importlib
    if "export_mesh" in locals():
        importlib.reload(export_mesh)

import logging
logger = logging.getLogger(__name__)

import bpy
from bpy.props import (
        BoolProperty,
        FloatProperty,
        StringProperty,
        EnumProperty,
        )
from bpy_extras.io_utils import (
        ExportHelper,
        orientation_helper,
        path_reference_mode,
        axis_conversion,
        )

from io_scene_fbx import ExportFBX

class MESH_PT_export_main(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = ""
    bl_parent_id = "FILE_PT_operator"
    bl_options = {'HIDE_HEADER'}

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "EXPORT_SCENE_OT_mesh"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        row = layout.row(align=True)
        row.prop(operator, "path_mode")
        sub = row.row(align=True)
        sub.enabled = (operator.path_mode == 'COPY')
        sub.prop(operator, "embed_textures", text="", icon='PACKAGE' if operator.embed_textures else 'UGLYPACKAGE')
        row = layout.row(align=True)
        row.prop(operator, "batch_mode")
        sub = row.row(align=True)
        sub.prop(operator, "use_batch_own_dir", text="", icon='NEWFOLDER')


class MESH_PT_export_include(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Include"
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "EXPORT_SCENE_OT_mesh"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        sublayout = layout.column()
        sublayout.enabled = (operator.batch_mode == 'OFF')
        sublayout.prop(operator, "use_selection")
        sublayout.prop(operator, "use_active_collection")

        layout.column().prop(operator, "object_types")
        layout.prop(operator, "use_custom_props")


class MESH_PT_export_transform(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Transform"
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "EXPORT_SCENE_OT_mesh"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator, "global_scale")
        layout.prop(operator, "apply_scale_options")

        layout.prop(operator, "axis_forward")
        layout.prop(operator, "axis_up")

        layout.prop(operator, "apply_unit_scale")
        layout.prop(operator, "bake_space_transform")


class MESH_PT_export_geometry(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Geometry"
    bl_parent_id = "FILE_PT_operator"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "EXPORT_SCENE_OT_mesh"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator, "mesh_smooth_type")
        layout.prop(operator, "use_subsurf")
        layout.prop(operator, "use_mesh_modifiers")
        #sub = layout.row()
        #sub.enabled = operator.use_mesh_modifiers and False  # disabled in 2.8...
        #sub.prop(operator, "use_mesh_modifiers_render")
        layout.prop(operator, "use_mesh_edges")
        sub = layout.row()
        #~ sub.enabled = operator.mesh_smooth_type in {'OFF'}
        sub.prop(operator, "use_tspace")


class MESH_PT_export_armature(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Armature"
    bl_parent_id = "FILE_PT_operator"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "EXPORT_SCENE_OT_mesh"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator, "primary_bone_axis")
        layout.prop(operator, "secondary_bone_axis")
        layout.prop(operator, "armature_nodetype")
        layout.prop(operator, "use_armature_deform_only")
        layout.prop(operator, "add_leaf_bones")


class MESH_PT_export_bake_animation(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Bake Animation"
    bl_parent_id = "FILE_PT_operator"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "EXPORT_SCENE_OT_mesh"

    def draw_header(self, context):
        sfile = context.space_data
        operator = sfile.active_operator

        self.layout.prop(operator, "bake_anim", text="")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        layout.enabled = operator.bake_anim
        layout.prop(operator, "bake_anim_use_all_bones")
        layout.prop(operator, "bake_anim_use_nla_strips")
        layout.prop(operator, "bake_anim_use_all_actions")
        layout.prop(operator, "bake_anim_force_startend_keying")
        layout.prop(operator, "bake_anim_step")
        layout.prop(operator, "bake_anim_simplify_factor")


@orientation_helper(axis_forward='X', axis_up='Y')
class ExportMESH(bpy.types.Operator, ExportHelper):
    """Save a EXOR Mesh File"""

    bl_idname = "export_scene.mesh"
    bl_label = 'Export EXOR Mesh'
    bl_options = {'PRESET'}

    filename_ext = ".mesh"
    filter_glob: StringProperty(
            default="*.mesh",
            options={'HIDDEN'},
            )

 # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.

    use_selection: BoolProperty(
            name="Selected Objects",
            description="Export selected and visible objects only",
            default=True,
            )
    use_active_collection: BoolProperty(
            name="Active Collection",
            description="Export only objects from the active collection (and its children)",
            default=False,
            )
    global_scale: FloatProperty(
            name="Scale",
            description="Scale all data (Some importers do not support scaled armatures!)",
            min=0.001, max=1000.0,
            soft_min=0.01, soft_max=1000.0,
            default=0.01,
            )
    apply_unit_scale: BoolProperty(
            name="Apply Unit",
            description="Take into account current Blender units settings (if unset, raw Blender Units values are used as-is)",
            default=True,
            )
    apply_scale_options: EnumProperty(
            items=(('FBX_SCALE_NONE', "All Local",
                    "Apply custom scaling and units scaling to each object transformation, FBX scale remains at 1.0"),
                   ('FBX_SCALE_UNITS', "FBX Units Scale",
                    "Apply custom scaling to each object transformation, and units scaling to FBX scale"),
                   ('FBX_SCALE_CUSTOM', "FBX Custom Scale",
                    "Apply custom scaling to FBX scale, and units scaling to each object transformation"),
                   ('FBX_SCALE_ALL', "FBX All",
                    "Apply custom scaling and units scaling to FBX scale"),
                   ),
            name="Apply Scalings",
            description="How to apply custom and units scalings in generated FBX file "
                        "(Blender uses FBX scale to detect units on import, "
                        "but many other applications do not handle the same way)",
            )
    bake_space_transform: BoolProperty(
            name="!EXPERIMENTAL! Apply Transform",
            description="Bake space transform into object data, avoids getting unwanted rotations to objects when "
                        "target space is not aligned with Blender's space "
                        "(WARNING! experimental option, use at own risks, known broken with armatures/animations)",
            default=True,
            )

    object_types: EnumProperty(
            name="Object Types",
            options={'ENUM_FLAG'},
            items=(('EMPTY', "Empty", ""),
                   ('CAMERA', "Camera", ""),
                   ('LIGHT', "Lamp", ""),
                   ('ARMATURE', "Armature", "WARNING: not supported in dupli/group instances"),
                   ('MESH', "Mesh", ""),
                   ('OTHER', "Other", "Other geometry types, like curve, metaball, etc. (converted to meshes)"),
                   ),
            description="Which kind of object to export",
            default={'EMPTY', 'CAMERA', 'LIGHT', 'ARMATURE', 'MESH', 'OTHER'},
            )

    use_mesh_modifiers: BoolProperty(
            name="Apply Modifiers",
            description="Apply modifiers to mesh objects (except Armature ones) - "
                        "WARNING: prevents exporting shape keys",
            default=True,
            )
    use_mesh_modifiers_render: BoolProperty(
            name="Use Modifiers Render Setting",
            description="Use render settings when applying modifiers to mesh objects (DISABLED in Blender 2.8)",
            default=True,
            )
    mesh_smooth_type: EnumProperty(
            name="Smoothing",
            items=(('OFF', "Normals Only", "Export only normals instead of writing edge or face smoothing data"),
                   ('FACE', "Face", "Write face smoothing"),
                   ('EDGE', "Edge", "Write edge smoothing"),
                   ),
            description="Export smoothing information "
                        "(prefer 'Normals Only' option if your target importer understand split normals)",
            default='OFF',
            )
    use_subsurf: BoolProperty(
            name="Export Subdivision Surface",
            description="Export the last Catmull-Rom subidivion modifier as FBX subdivision "
                        "(Does not apply the modifier even if 'Apply Modifiers' is enabled)",
            default=False,
            )
    use_mesh_edges: BoolProperty(
            name="Loose Edges",
            description="Export loose edges (as two-vertices polygons)",
            default=False,
            )
    use_tspace: BoolProperty(
            name="Tangent Space",
            description="Add binormal and tangent vectors, together with normal they form the tangent space "
                        "(will only work correctly with tris/quads only meshes!)",
            default=False,
            )
    use_custom_props: BoolProperty(
            name="Custom Properties",
            description="Export custom properties",
            default=False,
            )
    add_leaf_bones: BoolProperty(
            name="Add Leaf Bones",
            description="Append a final bone to the end of each chain to specify last bone length "
                        "(use this when you intend to edit the armature from exported data)",
            default=True # False for commit!
            )
    primary_bone_axis: EnumProperty(
            name="Primary Bone Axis",
            items=(('X', "X Axis", ""),
                   ('Y', "Y Axis", ""),
                   ('Z', "Z Axis", ""),
                   ('-X', "-X Axis", ""),
                   ('-Y', "-Y Axis", ""),
                   ('-Z', "-Z Axis", ""),
                   ),
            default='Y',
            )
    secondary_bone_axis: EnumProperty(
            name="Secondary Bone Axis",
            items=(('X', "X Axis", ""),
                   ('Y', "Y Axis", ""),
                   ('Z', "Z Axis", ""),
                   ('-X', "-X Axis", ""),
                   ('-Y', "-Y Axis", ""),
                   ('-Z', "-Z Axis", ""),
                   ),
            default='X',
            )
    use_armature_deform_only: BoolProperty(
            name="Only Deform Bones",
            description="Only write deforming bones (and non-deforming ones when they have deforming children)",
            default=False,
            )
    armature_nodetype: EnumProperty(
            name="Armature FBXNode Type",
            items=(('NULL', "Null", "'Null' FBX node, similar to Blender's Empty (default)"),
                   ('ROOT', "Root", "'Root' FBX node, supposed to be the root of chains of bones..."),
                   ('LIMBNODE', "LimbNode", "'LimbNode' FBX node, a regular joint between two bones..."),
                  ),
            description="FBX type of node (object) used to represent Blender's armatures "
                        "(use Null one unless you experience issues with other app, other choices may no import back "
                        "perfectly in Blender...)",
            default='NULL',
            )
    bake_anim: BoolProperty(
            name="Baked Animation",
            description="Export baked keyframe animation",
            default=True,
            )
    bake_anim_use_all_bones: BoolProperty(
            name="Key All Bones",
            description="Force exporting at least one key of animation for all bones "
                        "(needed with some target applications, like UE4)",
            default=True,
            )
    bake_anim_use_nla_strips: BoolProperty(
            name="NLA Strips",
            description="Export each non-muted NLA strip as a separated FBX's AnimStack, if any, "
                        "instead of global scene animation",
            default=True,
            )
    bake_anim_use_all_actions: BoolProperty(
            name="All Actions",
            description="Export each action as a separated FBX's AnimStack, instead of global scene animation "
                        "(note that animated objects will get all actions compatible with them, "
                        "others will get no animation at all)",
            default=True,
            )
    bake_anim_force_startend_keying: BoolProperty(
            name="Force Start/End Keying",
            description="Always add a keyframe at start and end of actions for animated channels",
            default=True,
            )
    bake_anim_step: FloatProperty(
            name="Sampling Rate",
            description="How often to evaluate animated values (in frames)",
            min=0.01, max=100.0,
            soft_min=0.1, soft_max=10.0,
            default=1.0,
            )
    bake_anim_simplify_factor: FloatProperty(
            name="Simplify",
            description="How much to simplify baked values (0.0 to disable, the higher the more simplified)",
            min=0.0, max=100.0,  # No simplification to up to 10% of current magnitude tolerance.
            soft_min=0.0, soft_max=10.0,
            default=1.0,  # default: min slope: 0.005, max frame step: 10.
            )
    path_mode: path_reference_mode
    embed_textures: BoolProperty(
            name="Embed Textures",
            description="Embed textures in FBX binary file (only for \"Copy\" path mode!)",
            default=False,
            )
    batch_mode: EnumProperty(
            name="Batch Mode",
            items=(('OFF', "Off", "Active scene to file"),
                   ('SCENE', "Scene", "Each scene as a file"),
                   ('COLLECTION', "Collection",
                    "Each collection (data-block ones) as a file, does not include content of children collections"),
                   ('SCENE_COLLECTION', "Scene Collections",
                    "Each collection (including master, non-data-block ones) of each scene as a file, "
                    "including content from children collections"),
                   ('ACTIVE_SCENE_COLLECTION', "Active Scene Collections",
                    "Each collection (including master, non-data-block one) of the active scene as a file, "
                    "including content from children collections"),
                   ),
            )
    use_batch_own_dir: BoolProperty(
            name="Batch Own Dir",
            description="Create a dir for each exported file",
            default=True,
            )
    use_metadata: BoolProperty(
            name="Use Metadata",
            default=True,
            options={'HIDDEN'},
            )

    def draw(self, context):
        pass

    @property
    def check_extension(self):
        return self.batch_mode == 'OFF'

    def execute(self, context):
        from mathutils import Matrix
        if not self.filepath:
            raise Exception("filepath not set")

        global_matrix = (axis_conversion(to_forward=self.axis_forward,
                                         to_up=self.axis_up,
                                         ).to_4x4())

        keywords = self.as_keywords(ignore=("check_existing",
                                            "filter_glob",
                                            "ui_tab",
                                            ))

        keywords["global_matrix"] = global_matrix
        keywords["filepath"] = keywords["filepath"].replace(".mesh", ".fbx")

        from io_scene_fbx import export_fbx_bin
        result = export_fbx_bin.save(self, context, **keywords)

        removeBones = "1"
        if self.use_armature_deform_only:
            removeBones = "0"

        try:
            import subprocess
            subprocess.run([directory + "/fbx_tool_win_release.exe", keywords["filepath"], "1", "1", "1", "0", removeBones ], shell=True)
        finally:
            import os
            os.remove(keywords["filepath"]) 

        return result

def menu_func_export(self, context):
    self.layout.operator(ExportMESH.bl_idname, text="EXOR Mesh (.mesh)")

classes = (
    ExportMESH,
    MESH_PT_export_main,
    MESH_PT_export_include,
    MESH_PT_export_transform,
    MESH_PT_export_geometry,
    MESH_PT_export_armature,
    MESH_PT_export_bake_animation,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
