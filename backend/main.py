"""
EcoSim - Ecosystem Simulation Entry Point
Initializes the grid environment and launches the interactive Pygame window.
"""

import sys
import pygame
from src.grid import Grid, TerrainType
from src.renderer import GridRenderer


def main():
    # 1. Create Grid Environment (40 cols x 30 rows)
    grid = Grid(width=40, height=30)
    grid.generate_procedural_terrain(seed=12345)

    # 2. Create Renderer Window (Fullscreen option supported, default resizable 1280x768)
    renderer = GridRenderer(grid=grid, window_width=1280, window_height=768, sidebar_width=340, fullscreen=False)

    print("==================================================")
    print("       EcoSim Forest Grid Environment Launched     ")
    print("==================================================")
    print("Controls:")
    print("  [F / F11]  : Toggle Fullscreen Mode")
    print("  [G]        : Toggle Gridlines")
    print("  [R]        : Regenerate Map with new seed")
    print("  [1, 2, 3, 4]: Select Paint Brush (1:Grass, 2:Water, 3:Soil, 4:Rock)")
    print("  Left Click  : Paint cell terrain (or click and drag)")
    print("  Right Click : Select / Inspect cell")
    print("  Window Drag : Resize window dynamically (cells auto-scale)")
    print("==================================================")

    mouse_painting = False

    # 3. Main Loop
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.VIDEORESIZE:
                renderer.handle_resize(event.w, event.h)

            elif event.type == pygame.KEYDOWN:
                # Toggle Fullscreen
                if event.key in (pygame.K_f, pygame.K_F11):
                    renderer.toggle_fullscreen()

                # Cycle Grid Resolution
                elif event.key == pygame.K_z:
                    renderer.cycle_resolution()

                # Toggle gridlines
                elif event.key == pygame.K_g:
                    renderer.show_gridlines = not renderer.show_gridlines

                # Regenerate terrain
                elif event.key == pygame.K_r:
                    grid.generate_procedural_terrain()

                # Brush selection
                elif event.key == pygame.K_1:
                    renderer.active_brush = TerrainType.GRASS
                elif event.key == pygame.K_2:
                    renderer.active_brush = TerrainType.WATER
                elif event.key == pygame.K_3:
                    renderer.active_brush = TerrainType.SOIL
                elif event.key == pygame.K_4:
                    renderer.active_brush = TerrainType.ROCK

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left Click
                    mouse_painting = True
                    coords = renderer.get_grid_coords_at_pixel(*event.pos)
                    if coords:
                        grid.matrix[coords[1]][coords[0]].terrain_type = renderer.active_brush

                elif event.button == 3:  # Right Click
                    coords = renderer.get_grid_coords_at_pixel(*event.pos)
                    if coords:
                        renderer.selected_cell = grid.get_cell(*coords)
                    else:
                        renderer.selected_cell = None

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    mouse_painting = False

            elif event.type == pygame.MOUSEMOTION:
                if mouse_painting:
                    coords = renderer.get_grid_coords_at_pixel(*event.pos)
                    if coords:
                        grid.matrix[coords[1]][coords[0]].terrain_type = renderer.active_brush

        # Render frame
        renderer.render()

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
