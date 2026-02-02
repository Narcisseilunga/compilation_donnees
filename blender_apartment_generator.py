"""Blender script to generate a small apartment building.

- R+1 or R+2 (configurable floors)
- Two apartments per level
- Each apartment follows a plan inspired by the provided sketch
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
    # Plan dimensions from the provided sketch (meters, approximated)
    "apartment_length": 11.30,
    "apartment_width": 9.00,
    "wall_thickness": 0.15,
    "slab_thickness": 0.2,
    "door_height": 2.1,
    "door_width": 0.9,
    "window_height": 1.2,
    "window_width": 1.4,
    "window_sill_height": 0.9,
}

APARTMENT_PLAN = [
    # name, width, depth, offset_x, offset_y (origin is bottom-left)
    ("Sejour", 4.60, 3.20, 3.60, 0.00),
    ("Coin_Manger", 2.88, 1.90, 4.10, 3.20),
    ("Cuisine", 2.88, 2.20, 4.10, 5.10),
    ("Depot", 2.70, 2.20, 8.60, 5.10),
    ("Chambre_P", 3.60, 3.20, 0.00, 0.00),
    ("Chambre_E", 3.20, 2.20, 0.72, 5.10),
    ("SDB", 1.80, 1.90, 0.72, 3.20),
    ("WC", 2.38, 1.20, 7.10, 3.20),
]

WINDOWS = [
    # x, y, width, orientation ("N", "S", "E", "W")
    (2.20, 0.0, 1.40, "S"),
    (6.30, 0.0, 1.40, "S"),
    (1.60, 9.00, 1.40, "N"),
    (6.20, 9.00, 1.40, "N"),
    (11.30, 5.80, 1.20, "E"),
    (11.30, 2.20, 1.20, "E"),
]

INTERIOR_DOORS = [
    # x, y, orientation ("N", "S", "E", "W")
    (3.60, 3.20, "N"),
    (4.10, 5.10, "N"),
    (7.10, 3.20, "E"),
    (0.72, 3.20, "N"),
]


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


def add_door(name, center, width, height, thickness, material=None, z_offset=0.0):
    return add_cube(
        name,
        size=(width, thickness, height),
        location=(center[0], center[1], z_offset + height / 2),
        material=material,
    )


def add_room_walls(name_prefix, origin, width, depth, height, thickness, material=None, z_offset=0.0):
    ox, oy = origin
    add_wall(
        f"{name_prefix}_S",
        (ox, oy, z_offset),
        (ox + width, oy, z_offset),
        height,
        thickness,
        material,
    )
    add_wall(
        f"{name_prefix}_N",
        (ox, oy + depth, z_offset),
        (ox + width, oy + depth, z_offset),
        height,
        thickness,
        material,
    )
    add_wall(
        f"{name_prefix}_W",
        (ox, oy, z_offset),
        (ox, oy + depth, z_offset),
        height,
        thickness,
        material,
    )
    add_wall(
        f"{name_prefix}_E",
        (ox + width, oy, z_offset),
        (ox + width, oy + depth, z_offset),
        height,
        thickness,
        material,
    )


def add_window_on_wall(
    name,
    center,
    window_width,
    height,
    thickness,
    sill_height,
    orientation,
    glass_mat,
    frame_mat,
    z_offset=0.0,
):
    cx, cy = center
    if orientation == "N":
        add_window(name, (cx, cy, 0), window_width, height, thickness, sill_height, glass_mat, frame_mat, z_offset)
    elif orientation == "S":
        add_window(name, (cx, cy, 0), window_width, height, thickness, sill_height, glass_mat, frame_mat, z_offset)
    elif orientation == "E":
        add_window(name, (cx, cy, 0), window_width, height, thickness, sill_height, glass_mat, frame_mat, z_offset)
    elif orientation == "W":
        add_window(name, (cx, cy, 0), window_width, height, thickness, sill_height, glass_mat, frame_mat, z_offset)


def add_window(name, center, width, height, thickness, sill_height, glass_mat=None, frame_mat=None, z_offset=0.0):
    frame_depth = thickness
    frame_thickness = 0.06
    window_center_z = z_offset + sill_height + height / 2

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

def generate_apartment(origin, config, materials, name_prefix, z_offset):
    apt_len = config["apartment_length"]
    apt_wid = config["apartment_width"]
    wall_height = config["floor_height"]
    wall_thickness = config["wall_thickness"]

    for room_name, width, depth, offset_x, offset_y in APARTMENT_PLAN:
        add_room_walls(
            f"{name_prefix}_{room_name}",
            (origin[0] + offset_x, origin[1] + offset_y),
            width,
            depth,
            wall_height,
            wall_thickness,
            materials["wall"],
            z_offset=z_offset,
        )

    for index, (x, y, width, orientation) in enumerate(WINDOWS, start=1):
        if orientation == "N":
            center = (origin[0] + x, origin[1] + apt_wid)
        elif orientation == "S":
            center = (origin[0] + x, origin[1])
        elif orientation == "E":
            center = (origin[0] + apt_len, origin[1] + y)
        else:
            center = (origin[0], origin[1] + y)
        add_window_on_wall(
            f"{name_prefix}_Window_{index}",
            center,
            width,
            config["window_height"],
            wall_thickness,
            config["window_sill_height"],
            orientation,
            materials["glass"],
            materials["frame"],
            z_offset=z_offset,
        )

    for index, (x, y, orientation) in enumerate(INTERIOR_DOORS, start=1):
        door_center = (origin[0] + x, origin[1] + y)
        add_door(
            f"{name_prefix}_Door_{index}",
            center=door_center,
            width=config["door_width"],
            height=config["door_height"],
            thickness=wall_thickness * 0.7,
            material=materials["door"],
            z_offset=z_offset,
        )

    # Exterior apartment outline
    add_room_walls(
        f"{name_prefix}_Outline",
        origin,
        apt_len,
        apt_wid,
        wall_height,
        wall_thickness,
        materials["wall"],
        z_offset=z_offset,
    )


def generate_floor(level_index, config, materials):
    floor_height = config["floor_height"]
    slab_thickness = config["slab_thickness"]
    apt_len = config["apartment_length"]
    apt_wid = config["apartment_width"]
    wall_thickness = config["wall_thickness"]

    building_length = apt_len * 2
    building_width = apt_wid

    z_offset = level_index * floor_height

    add_cube(
        f"Slab_{level_index}",
        size=(building_length, building_width, slab_thickness),
        location=(building_length / 2, building_width / 2, z_offset + slab_thickness / 2),
        material=materials["concrete"],
    )

    # Two apartments per level
    generate_apartment((0, 0), config, materials, f"AptA_{level_index}", z_offset)
    generate_apartment((apt_len, 0), config, materials, f"AptB_{level_index}", z_offset)

    # Central separating wall between apartments
    add_wall(
        f"Core_Split_{level_index}",
        (apt_len, 0, z_offset),
        (apt_len, building_width, z_offset),
        floor_height,
        wall_thickness,
        materials["wall"],
    )


def build_materials(preset="classic"):
    if preset == "modern":
        return {
            "wall": ensure_material("Wall_Modern", (0.85, 0.85, 0.9), roughness=0.25),
            "concrete": ensure_material("Concrete_Modern", (0.5, 0.52, 0.55), roughness=0.5),
            "door": ensure_material("Door_Modern", (0.15, 0.15, 0.15), roughness=0.4),
            "frame": ensure_material("Frame_Modern", (0.05, 0.05, 0.05), roughness=0.2),
            "glass": ensure_material(
                "Glass_Modern",
                (0.6, 0.8, 1.0),
                alpha=0.15,
                transmission=0.95,
                roughness=0.02,
            ),
        }
    if preset == "warm":
        return {
            "wall": ensure_material("Wall_Warm", (0.9, 0.85, 0.75), roughness=0.35),
            "concrete": ensure_material("Concrete_Warm", (0.65, 0.6, 0.55), roughness=0.6),
            "door": ensure_material("Door_Warm", (0.5, 0.25, 0.1), roughness=0.5),
            "frame": ensure_material("Frame_Warm", (0.2, 0.1, 0.05), roughness=0.4),
            "glass": ensure_material(
                "Glass_Warm",
                (0.75, 0.9, 1.0),
                alpha=0.2,
                transmission=0.9,
                roughness=0.06,
            ),
        }
    return {
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


def generate_building(preset="classic"):
    clear_scene()

    materials = build_materials(preset)

    for level in range(CONFIG["floors"]):
        generate_floor(level, CONFIG, materials)


if __name__ == "__main__":
    generate_building()
