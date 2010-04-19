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

# <pep8 compliant>

import bpy
from rigify import RigifyError
from rigify_utils import copy_bone_simple
from rna_prop_ui import rna_idprop_ui_prop_get

#METARIG_NAMES = ("cpy",)
RIG_TYPE = "shape_key_control"


def addget_shape_key(obj, name="Key"):
    """ Fetches a shape key, or creates it if it doesn't exist
    """
    # Create a shapekey set if it doesn't already exist
    if obj.data.shape_keys is None:
        shape = obj.add_shape_key(name="Basis", from_mix=False)
        obj.active_shape_key_index = 0

    # Get the shapekey, or create it if it doesn't already exist
    if name in obj.data.shape_keys.keys:
        shape_key = obj.data.shape_keys.keys[name]
    else:
        shape_key = obj.add_shape_key(name=name, from_mix=False)

    return shape_key


def addget_shape_key_driver(obj, name="Key"):
    """ Fetches the driver for the shape key, or creates it if it doesn't
        already exist.
    """
    driver_path = 'keys["' + name + '"].value'
    fcurve = None
    driver = None
    new = False
    if obj.data.shape_keys.animation_data is not None:
        for driver_s in obj.data.shape_keys.animation_data.drivers:
            if driver_s.data_path == driver_path:
                fcurve = driver_s
    if fcurve == None:
        fcurve = obj.data.shape_keys.keys[name].driver_add("value")
        fcurve.driver.type = 'AVERAGE'
        new = True

    return fcurve, new


# TODO:
def metarig_template():
    # generated by rigify.write_meta_rig
    #bpy.ops.object.mode_set(mode='EDIT')
    #obj = bpy.context.active_object
    #arm = obj.data
    #bone = arm.edit_bones.new('Bone')
    #bone.head[:] = 0.0000, 0.0000, 0.0000
    #bone.tail[:] = 0.0000, 0.0000, 1.0000
    #bone.roll = 0.0000
    #bone.connected = False
    #
    #bpy.ops.object.mode_set(mode='OBJECT')
    #pbone = obj.pose.bones['Bone']
    #pbone['type'] = 'copy'
    pass


def metarig_definition(obj, orig_bone_name):
    bone = obj.data.bones[orig_bone_name]
    return [bone.name]


def main(obj, definitions, base_names, options):
    """ A rig that drives shape keys with the local transforms and/or custom
        properties of a single bone.
        A different shape can be driven by the negative value of a transform as
        well by giving a comma-separated list of two shapes.

        Required options:
            mesh:  name of mesh object(s) to add/get shapekeys to/from
                   (if multiple objects, make a comma-separated list)
        Optional options:
            loc_<x/y/z>:       name of the shape key to tie to translation of the bone
            loc_<x/y/z>_fac:   default multiplier of the bone influence on the shape key
            rot_<x/y/z>:       name of the shape key to tie to rotation of the bone
            rot_<x/y/z>_fac:   default multiplier of the bone influence on the shape key
            scale_<x/y/z>:     name of the shape key to tie to scale of the bone
            scale_<x/y/z>_fac: default multiplier of the bone influence on the shape key
            shape_key_sliders:     comma-separated list of custom properties to create sliders out of for driving shape keys
            <custom_prop>:         for each property listed in shape_key_sliders, specify a shape key for it to drive

    """

    bpy.ops.object.mode_set(mode='EDIT')
    eb = obj.data.edit_bones
    pb = obj.pose.bones

    org_bone = definitions[0]

    # Options
    req_options = ["mesh"]
    for option in req_options:
        if option not in options:
            raise RigifyError("'%s' rig type requires a '%s' option (bone: %s)" % (RIG_TYPE, option, base_names[definitions[0]]))

    meshes = options["mesh"].replace(" ", "").split(",")

    bone = copy_bone_simple(obj.data, org_bone, base_names[org_bone], parent=True).name

    bpy.ops.object.mode_set(mode='OBJECT')

    # Set rotation mode and axis locks
    pb[bone].rotation_mode = pb[org_bone].rotation_mode
    pb[bone].lock_location = tuple(pb[org_bone].lock_location)
    pb[bone].lock_rotation = tuple(pb[org_bone].lock_rotation)
    pb[bone].lock_rotation_w = pb[org_bone].lock_rotation_w
    pb[bone].lock_rotations_4d = pb[org_bone].lock_rotations_4d
    pb[bone].lock_scale = tuple(pb[org_bone].lock_scale)

    # List of rig options for specifying shape keys
    # Append '_fac' to the end for the name of the corresponding 'factor
    # default' option for that shape
    shape_key_options = ["loc_x",
                         "loc_y",
                         "loc_z",
                         "rot_x",
                         "rot_y",
                         "rot_z",
                         "scale_x",
                         "scale_y",
                         "scale_z"]

    driver_paths = {"loc_x":".location[0]",
                    "loc_y":".location[1]",
                    "loc_z":".location[2]",
                    "rot_x":".rotation_euler[0]",
                    "rot_y":".rotation_euler[1]",
                    "rot_z":".rotation_euler[2]",
                    "qrot_x":".rotation_quaternion[1]",
                    "qrot_y":".rotation_quaternion[2]",
                    "qrot_z":".rotation_quaternion[3]",
                    "scale_x":".scale[0]",
                    "scale_y":".scale[1]",
                    "scale_z":".scale[2]"}

    # Create the shape keys and drivers for transforms
    shape_info = []
    for option in shape_key_options:
        if option in options:
            shape_names = options[option].replace(" ", "").split(",")

            var_name = bone.replace(".","").replace("-","_") + "_" + option
            # Different RNA paths for euler vs quat
            if option in (shape_key_options[3:6]+shape_key_options[12:15]) \
            and pb[bone].rotation_mode == 'QUATERNION':
                var_path = driver_paths['q' + option]
            else:
                var_path = driver_paths[option]

            if (option+"_fac") in options:
                fac = options[option+"_fac"]
            else:
                fac = 1.0

            # Positive
            if shape_names[0] != "":
                # Different expressions for loc/rot/scale and positive/negative
                if option in shape_key_options[:3]:
                    # Location
                    expression = var_name + " * " + str(fac)
                elif option in shape_key_options[3:6]:
                    # Rotation
                    # Different expressions for euler vs quats
                    if pb[bone].rotation_mode == 'QUATERNION':
                        expression = "2 * asin(" + var_name + ") * " + str(fac)
                    else:
                        expression = var_name + " * " + str(fac)
                elif option in shape_key_options[6:9]:
                    # Scale
                    expression = "(1.0 - " + var_name + ") * " + str(fac) + " * -2"
                shape_name = shape_names[0]
                create_shape_and_driver(obj, bone, meshes, shape_name, var_name, var_path, expression)

            # Negative
            if shape_names[0] != "" and len(shape_names) > 1:
                # Different expressions for loc/rot/scale and positive/negative
                if option in shape_key_options[:3]:
                    # Location
                    expression = var_name + " * " + str(fac) + " * -1"
                elif option in shape_key_options[3:6]:
                    # Rotation
                    # Different expressions for euler vs quats
                    if pb[bone].rotation_mode == 'QUATERNION':
                        expression = "-2 * asin(" + var_name + ") * " + str(fac)
                    else:
                        expression = var_name + " * " + str(fac) + " * -1"
                elif option in shape_key_options[6:9]:
                    # Scale
                    expression = "(1.0 - " + var_name + ") * " + str(fac) + " * 2"
                shape_name = shape_names[1]
                create_shape_and_driver(obj, bone, meshes, shape_name, var_name, var_path, expression)

    # Create the shape keys and drivers for custom-property sliders
    if "shape_key_sliders" in options:
        # Get the slider names
        slider_names = options["shape_key_sliders"].replace(" ", "").split(",")
        if slider_names[0] != "":
            # Loop through the slider names and check if they have
            # shape keys specified for them, and if so, set them up.
            for slider_name in slider_names:
                if slider_name in options:
                    shape_names = options[slider_name].replace(" ", "").split(",")

                    # Set up the custom property on the bone
                    prop = rna_idprop_ui_prop_get(pb[bone], slider_name, create=True)
                    pb[bone][slider_name] = 0.0
                    prop["min"] = 0.0
                    prop["max"] = 1.0
                    prop["soft_min"] = 0.0
                    prop["soft_max"] = 1.0
                    if len(shape_names) > 1:
                        prop["min"] = -1.0
                        prop["soft_min"] = -1.0

                    # Add the shape drivers
                    # Positive
                    if shape_names[0] != "":
                        # Set up the variables for creating the shape key driver
                        shape_name = shape_names[0]
                        var_name = slider_name.replace(".", "_").replace("-", "_")
                        var_path = '["' + slider_name + '"]'
                        if slider_name + "_fac" in options:
                            fac = options[slider_name + "_fac"]
                        else:
                            fac = 1.0
                        expression = var_name + " * " + str(fac)
                        # Create the shape key driver
                        create_shape_and_driver(obj, bone, meshes, shape_name, var_name, var_path, expression)
                    # Negative
                    if shape_names[0] != "" and len(shape_names) > 1:
                        # Set up the variables for creating the shape key driver
                        shape_name = shape_names[1]
                        var_name = slider_name.replace(".", "_").replace("-", "_")
                        var_path = '["' + slider_name + '"]'
                        if slider_name + "_fac" in options:
                            fac = options[slider_name + "_fac"]
                        else:
                            fac = 1.0
                        expression = var_name + " * " + str(fac) + " * -1"
                        # Create the shape key driver
                        create_shape_and_driver(obj, bone, meshes, shape_name, var_name, var_path, expression)


    # Org bone copy transforms of control bone
    con = pb[org_bone].constraints.new('COPY_TRANSFORMS')
    con.target = obj
    con.subtarget = bone

    return (None,)


def create_shape_and_driver(obj, bone, meshes, shape_name, var_name, var_path, expression):
    """ Creates/gets a shape key and sets up a driver for it.

        obj = armature object
        bone = driving bone name
        meshes = list of meshes to create the shapekey/driver on
        shape_name = name of the shape key
        var_name = name of the driving variable
        var_path = path to the property on the bone to drive with
        expression = python expression for the driver
    """
    pb = obj.pose.bones
    bpy.ops.object.mode_set(mode='OBJECT')

    for mesh_name in meshes:
        mesh_obj = bpy.data.objects[mesh_name]

        # Add/get the shape key
        shape = addget_shape_key(mesh_obj, name=shape_name)

        # Add/get the shape key driver
        fcurve, a = addget_shape_key_driver(mesh_obj, name=shape_name)

        # Set up the driver
        driver = fcurve.driver
        driver.type = 'SCRIPTED'
        driver.expression = expression

        # Get the variable, or create it if it doesn't already exist
        if var_name in driver.variables:
            var = driver.variables[var_name]
        else:
            var = driver.variables.new()
            var.name = var_name

        # Set up the variable
        var.type = "SINGLE_PROP"
        var.targets[0].id_type = 'OBJECT'
        var.targets[0].id = obj
        var.targets[0].data_path = 'pose.bones["' + bone + '"]' + var_path


