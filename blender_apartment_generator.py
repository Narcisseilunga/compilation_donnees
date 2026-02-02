"""Blender script to generate a small apartment building.

- R+1 or R+2 (configurable floors)
- Two apartments per level
- Each apartment with 3 bedrooms
- Doors, windows, and simple glass panes

Usage (inside Blender Scripting tab):
1) Open this file.
2) Adjust CONFIG if needed.
3) Run Script.
"""

import math
import bpy


CONFIG = {
    "floors": 2,  # R+1 -> 2 floors, R+2 -> 3 floors
    "floor_height": 3.0,
    "building_length": 18.0,
    "building_width": 12.0,
    "wall_thickness": 0.15,
    "slab_thickness": 0.2,
    "door_height": 2.1,
    "door_width": 0.9,
    "window_height": 1.2,
    "window_width": 1.4,
    "window_sill_height": 0.9,
}


# ---------------------------
# Helpers
# ---------------------------

def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def ensure_material(name, base_color, alpha=1.0, transmission=0.0, roughness=0.4):
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    principled = nodes.get("Principled BSDF")
    if principled:
        principled.inputs["Base Color"].default_value = (*base_color, 1)
        principled.inputs["Alpha"].default_value = alpha
        principled.inputs["Transmission"].default_value = transmission
        principled.inputs["Roughness"].default_value = roughness
    mat.blend_method = "BLEND" if alpha < 1.0 or transmission > 0.0 else "OPAQUE"
    return mat


def add_cube(name, size, location, rotation=(0, 0, 0), material=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location, rotation=rotation)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    if material is not None:
        if obj.data.materials:
            obj.data.materials[0] = material
        else:
            obj.data.materials.append(material)
    return obj


def add_wall(name, start, end, height, thickness, material=None):
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length = math.hypot(dx, dy)
    angle = math.atan2(dy, dx)
    center = ((start[0] + end[0]) / 2, (start[1] + end[1]) / 2, height / 2)
    return add_cube(
        name=name,
        size=(length, thickness, height),
        location=center,
        rotation=(0, 0, angle),
        material=material,
    )


def add_door(name, center, width, height, thickness, material=None):
    return add_cube(
        name,
        size=(width, thickness, height),
        location=(center[0], center[1], height / 2),
        material=material,
    )


def add_window(name, center, width, height, thickness, sill_height, glass_mat=None, frame_mat=None):
    frame_depth = thickness
    frame_thickness = 0.06
    window_center_z = sill_height + height / 2

    # Frame
    frame = add_cube(
        f"{name}_frame",
        size=(width, frame_depth, height),
        location=(center[0], center[1], window_center_z),
        material=frame_mat,
    )

    # Glass
    glass = add_cube(
        f"{name}_glass",
        size=(width - frame_thickness, frame_thickness, height - frame_thickness),
        location=(center[0], center[1], window_center_z),
        material=glass_mat,
    )
    return frame, glass


# ---------------------------
# Building generation
# ---------------------------

def generate_floor(level_index, config, materials):
    floor_height = config["floor_height"]
    slab_thickness = config["slab_thickness"]
    length = config["building_length"]
    width = config["building_width"]
    wall_thickness = config["wall_thickness"]

    z_offset = level_index * floor_height

    # Floor slab
    add_cube(
        f"Slab_{level_index}",
        size=(length, width, slab_thickness),
        location=(0, 0, z_offset + slab_thickness / 2),
        material=materials["concrete"],
    )

    # Exterior walls (rectangle)
    half_len = length / 2
    half_wid = width / 2
    wall_z = z_offset
    wall_height = floor_height

    # Perimeter walls
    add_wall(
        f"Wall_N_{level_index}",
        (-half_len, half_wid, wall_z),
        (half_len, half_wid, wall_z),
        wall_height,
        wall_thickness,
        materials["wall"],
    )
    add_wall(
        f"Wall_S_{level_index}",
        (-half_len, -half_wid, wall_z),
        (half_len, -half_wid, wall_z),
        wall_height,
        wall_thickness,
        materials["wall"],
    )
    add_wall(
        f"Wall_W_{level_index}",
        (-half_len, -half_wid, wall_z),
        (-half_len, half_wid, wall_z),
        wall_height,
        wall_thickness,
        materials["wall"],
    )
    add_wall(
        f"Wall_E_{level_index}",
        (half_len, -half_wid, wall_z),
        (half_len, half_wid, wall_z),
        wall_height,
        wall_thickness,
        materials["wall"],
    )

    # Split into two apartments along width
    add_wall(
        f"Core_Split_{level_index}",
        (-half_len, 0, wall_z),
        (half_len, 0, wall_z),
        wall_height,
        wall_thickness,
        materials["wall"],
    )

    # Apartment layout per half (3 bedrooms + living)
    room_depth = width / 2
    bedroom_depth = room_depth / 3
    bedroom_width = length / 3

    for side in (1, -1):
        y_base = side * (room_depth / 2)
        # Vertical partitions (3 bedrooms along length)
        for i in range(1, 3):
            x_pos = -half_len + i * bedroom_width
            add_wall(
                f"Apt{side}_Partition_{i}_{level_index}",
                (x_pos, y_base - room_depth / 2, wall_z),
                (x_pos, y_base + room_depth / 2, wall_z),
                wall_height,
                wall_thickness,
                materials["wall"],
            )

        # Horizontal partition to separate bedrooms from living zone
        y_split = y_base + side * (room_depth / 2 - bedroom_depth)
        add_wall(
            f"Apt{side}_LivingSplit_{level_index}",
            (-half_len, y_split, wall_z),
            (half_len, y_split, wall_z),
            wall_height,
            wall_thickness,
            materials["wall"],
        )

        # Doors for bedrooms (simple placeholders)
        for i in range(3):
            x_center = -half_len + (i + 0.5) * bedroom_width
            y_center = y_split + side * (wall_thickness / 2)
            add_door(
                f"Apt{side}_Door_{i}_{level_index}",
                center=(x_center, y_center, 0),
                width=config["door_width"],
                height=config["door_height"],
                thickness=wall_thickness * 0.7,
                material=materials["door"],
            )

        # Main entrance doors for each apartment
        entrance_x = -half_len + bedroom_width / 2
        entrance_y = 0
        add_door(
            f"Apt{side}_Entrance_{level_index}",
            center=(entrance_x, entrance_y, 0),
            width=config["door_width"],
            height=config["door_height"],
            thickness=wall_thickness * 0.9,
            material=materials["door"],
        )

        # Windows for bedrooms (exterior wall)
        for i in range(3):
            x_center = -half_len + (i + 0.5) * bedroom_width
            y_wall = side * half_wid
            add_window(
                f"Apt{side}_Window_{i}_{level_index}",
                center=(x_center, y_wall, 0),
                width=config["window_width"],
                height=config["window_height"],
                thickness=wall_thickness,
                sill_height=config["window_sill_height"],
                glass_mat=materials["glass"],
                frame_mat=materials["frame"],
            )


def generate_building():
    clear_scene()

    materials = {
        "wall": ensure_material("Wall", (0.8, 0.8, 0.8)),
        "concrete": ensure_material("Concrete", (0.6, 0.6, 0.6), roughness=0.7),
        "door": ensure_material("Door", (0.4, 0.2, 0.1), roughness=0.5),
        "frame": ensure_material("Frame", (0.1, 0.1, 0.1), roughness=0.3),
        "glass": ensure_material(
            "Glass",
            (0.7, 0.9, 1.0),
            alpha=0.2,
            transmission=0.9,
            roughness=0.05,
        ),
    }

    for level in range(CONFIG["floors"]):
        generate_floor(level, CONFIG, materials)


if __name__ == "__main__":
    generate_building()
