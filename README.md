# compilation_donnees

## Blender apartment generator

This repository includes Blender Python scripts that generate an apartment building:

- R+1 or R+2 (configurable floors)
- Two apartments per level
- Each apartment follows the provided plan layout (3 bedrooms, living, kitchen, WC, etc.)
- Doors and windows with glass panes
- Multiple facade/material presets (classic, modern, warm)

### Usage

1. Open Blender.
2. Go to the **Scripting** workspace.
3. Open one of the scripts:
   - `blender_apartment_generator.py` (classic facade)
   - `blender_apartment_generator_facade_modern.py`
   - `blender_apartment_generator_facade_warm.py`
4. Adjust the `CONFIG` dictionary in `blender_apartment_generator.py` if needed (floors, sizes, etc.).
5. Click **Run Script**.

The scene will be cleared and replaced by the generated building.
