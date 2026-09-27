"""
EcoSim Grid Renderer Module
Pygame-based graphical interface for displaying the simulation grid,
rendering biome statistics, inspecting cells, and interactive terrain editing.
"""

import sys
import pygame
from typing import Optional, Tuple
from src.grid import Grid, Cell, TerrainType, TERRAIN_COLORS


# Aesthetic Theme Palette (Dark Modern UI)
COLOR_BG = (18, 22, 28)           # Main dark window background
COLOR_PANEL_BG = (26, 32, 44)     # Sidebar panel background
COLOR_CARD_BG = (36, 45, 61)      # Card / container background
COLOR_TEXT_MAIN = (240, 246, 252)# Bright primary text
COLOR_TEXT_MUTED = (148, 163, 184)# Muted secondary text
COLOR_ACCENT = (56, 189, 248)    # Cyan accent blue
COLOR_BORDER = (51, 65, 85)       # Divider border line
COLOR_HOVER = (245, 158, 11, 180) # Gold amber hover glow
COLOR_SELECT = (239, 68, 68)      # Red border selection


class GridRenderer:
    """Manages Pygame window creation, grid rendering loop, and sidebar UI."""

    def __init__(
        self,
        grid: Grid,
        window_width: int = 1280,
        window_height: int = 768,
        sidebar_width: int = 340,
        fullscreen: bool = False
    ):
        pygame.init()
        pygame.font.init()
        pygame.display.set_caption("EcoSim - Forest Grid Environment")

        self.grid = grid
        self.sidebar_width = sidebar_width
        self.is_fullscreen = fullscreen

        # Get display info for initial setup if fullscreen or auto-scaling
        flags = pygame.RESIZABLE
        if fullscreen:
            flags |= pygame.FULLSCREEN
            info = pygame.display.Info()
            window_width, window_height = info.current_w, info.current_h

        self.window_width = window_width
        self.window_height = window_height

        self.screen = pygame.display.set_mode((window_width, window_height), flags)
        self.clock = pygame.time.Clock()

        # Fonts
        self.font_title = pygame.font.SysFont("Segoe UI", 20, bold=True)
        self.font_header = pygame.font.SysFont("Segoe UI", 16, bold=True)
        self.font_body = pygame.font.SysFont("Segoe UI", 14)
        self.font_mono = pygame.font.SysFont("Consolas", 13)

        # State flags
        self.show_gridlines = True
        self.selected_cell: Optional[Cell] = None
        self.active_brush: TerrainType = TerrainType.GRASS

        # Grid Resolution Presets (cols, rows)
        self.resolution_presets = [(40, 30), (80, 60), (120, 90), (160, 120)]
        self.preset_idx = 0

        # Calculate cell dimensions
        self.handle_resize(window_width, window_height)

    def cycle_resolution(self, forward: bool = True) -> None:
        """Cycles grid resolution between 40x30, 80x60, 120x90, 160x120."""
        if forward:
            self.preset_idx = (self.preset_idx + 1) % len(self.resolution_presets)
        else:
            self.preset_idx = (self.preset_idx - 1) % len(self.resolution_presets)
        
        cols, rows = self.resolution_presets[self.preset_idx]
        self.grid.resize(cols, rows)
        self.selected_cell = None
        self.update_cell_dimensions()

    def handle_resize(self, new_width: int, new_height: int) -> None:
        """Dynamically resizes viewport and recalculates cell block sizes."""
        self.window_width = max(600, new_width)
        self.window_height = max(400, new_height)
        self.grid_view_width = max(100, self.window_width - self.sidebar_width)
        self.grid_view_height = self.window_height
        self.update_cell_dimensions()

    def toggle_fullscreen(self) -> None:
        """Toggles windowed vs borderless fullscreen mode."""
        self.is_fullscreen = not self.is_fullscreen
        if self.is_fullscreen:
            pygame.display.set_mode((0, 0), pygame.FULLSCREEN | pygame.RESIZABLE)
            info = pygame.display.Info()
            self.handle_resize(info.current_w, info.current_h)
        else:
            pygame.display.set_mode((1280, 768), pygame.RESIZABLE)
            self.handle_resize(1280, 768)

    def update_cell_dimensions(self) -> None:
        """Calculates exact pixel dimensions per cell to fit the view surface cleanly."""
        self.cell_width = self.grid_view_width / self.grid.width
        self.cell_height = self.grid_view_height / self.grid.height

    def get_grid_coords_at_pixel(self, px: int, py: int) -> Optional[Tuple[int, int]]:
        """Converts mouse screen coordinates (px, py) into grid coordinates (x, y)."""
        if px < 0 or px >= self.grid_view_width or py < 0 or py >= self.grid_view_height:
            return None
        gx = int(px // self.cell_width)
        gy = int(py // self.cell_height)
        if self.grid.in_bounds(gx, gy):
            return (gx, gy)
        return None

    def draw_cell(self, cell: Cell, hover: bool = False, selected: bool = False) -> None:
        """Renders an individual cell, scaling precisely with no subpixel gaps."""
        px = int(cell.x * self.cell_width)
        py = int(cell.y * self.cell_height)
        next_px = int((cell.x + 1) * self.cell_width)
        next_py = int((cell.y + 1) * self.cell_height)
        cw = max(1, next_px - px)
        ch = max(1, next_py - py)

        # Base color with subtle depth modulation based on elevation and moisture
        base_r, base_g, base_b = TERRAIN_COLORS[cell.terrain_type]
        shade_factor = 0.85 + (cell.elevation * 0.3)
        if cell.terrain_type == TerrainType.GRASS:
            # Shift green brightness with moisture
            g_val = min(255, int(base_g * (0.8 + cell.moisture * 0.4)))
            r_val = int(base_r * shade_factor)
            b_val = int(base_b * shade_factor)
            color = (max(0, min(255, r_val)), g_val, max(0, min(255, b_val)))
        else:
            color = (
                max(0, min(255, int(base_r * shade_factor))),
                max(0, min(255, int(base_g * shade_factor))),
                max(0, min(255, int(base_b * shade_factor)))
            )

        rect = pygame.Rect(px, py, cw, ch)
        pygame.draw.rect(self.screen, color, rect)

        # Draw gridlines if enabled
        if self.show_gridlines:
            pygame.draw.rect(self.screen, (20, 25, 33), rect, width=1)

        # Hover highlight
        if hover:
            s = pygame.Surface((cw, ch), pygame.SRCALPHA)
            s.fill(COLOR_HOVER)
            self.screen.blit(s, (px, py))
            pygame.draw.rect(self.screen, (245, 158, 11), rect, width=2)

        # Selected highlight
        if selected:
            pygame.draw.rect(self.screen, COLOR_SELECT, rect, width=3)

    def draw_grid_view(self, hover_coords: Optional[Tuple[int, int]]) -> None:
        """Renders the entire grid surface."""
        for y in range(self.grid.height):
            for x in range(self.grid.width):
                cell = self.grid.matrix[y][x]
                is_hover = (hover_coords == (x, y))
                is_selected = (self.selected_cell is not None and self.selected_cell.x == x and self.selected_cell.y == y)
                self.draw_cell(cell, hover=is_hover, selected=is_selected)

    def draw_sidebar(self, hover_coords: Optional[Tuple[int, int]]) -> None:
        """Renders the right dashboard panel with stats, inspector, and help."""
        panel_x = self.grid_view_width
        panel_rect = pygame.Rect(panel_x, 0, self.sidebar_width, self.window_height)
        pygame.draw.rect(self.screen, COLOR_PANEL_BG, panel_rect)

        # Left border line of panel
        pygame.draw.line(self.screen, COLOR_BORDER, (panel_x, 0), (panel_x, self.window_height), 2)

        curr_y = 20

        # --- Section 1: Header ---
        title_surface = self.font_title.render("EcoSim Forest Grid", True, COLOR_TEXT_MAIN)
        self.screen.blit(title_surface, (panel_x + 20, curr_y))
        curr_y += 30

        sub_surface = self.font_body.render("Grid & Environment Sandbox", True, COLOR_ACCENT)
        self.screen.blit(sub_surface, (panel_x + 20, curr_y))
        curr_y += 35

        pygame.draw.line(self.screen, COLOR_BORDER, (panel_x + 20, curr_y), (panel_x + self.sidebar_width - 20, curr_y), 1)
        curr_y += 15

        # --- Section 2: Biome Breakdown Card ---
        card1_rect = pygame.Rect(panel_x + 15, curr_y, self.sidebar_width - 30, 160)
        pygame.draw.rect(self.screen, COLOR_CARD_BG, card1_rect, border_radius=8)
        pygame.draw.rect(self.screen, COLOR_BORDER, card1_rect, width=1, border_radius=8)

        lbl1 = self.font_header.render("ENVIRONMENT STATS", True, COLOR_TEXT_MAIN)
        self.screen.blit(lbl1, (panel_x + 25, curr_y + 12))

        dim_str = f"Dimensions: {self.grid.width} x {self.grid.height} ({self.grid.width * self.grid.height} cells)"
        lbl_dim = self.font_mono.render(dim_str, True, COLOR_TEXT_MUTED)
        self.screen.blit(lbl_dim, (panel_x + 25, curr_y + 35))

        stats = self.grid.get_terrain_stats()
        bar_y = curr_y + 60
        for terrain_type in TerrainType:
            t_name = terrain_type.value.capitalize()
            t_pct = stats["percentages"][terrain_type.value]
            t_count = stats["counts"][terrain_type.value]
            color = TERRAIN_COLORS[terrain_type]

            # Label text
            txt = self.font_mono.render(f"{t_name:<6} {t_pct:4.1f}% ({t_count})", True, COLOR_TEXT_MAIN)
            self.screen.blit(txt, (panel_x + 25, bar_y))

            # Progress bar background
            bar_bg = pygame.Rect(panel_x + 200, bar_y + 2, 100, 12)
            pygame.draw.rect(self.screen, (20, 25, 33), bar_bg, border_radius=3)
            
            # Fill bar
            fill_w = int(100 * (t_pct / 100.0))
            if fill_w > 0:
                bar_fill = pygame.Rect(panel_x + 200, bar_y + 2, fill_w, 12)
                pygame.draw.rect(self.screen, color, bar_fill, border_radius=3)

            bar_y += 22

        curr_y += 180

        # --- Section 3: Cell Inspector Card ---
        card2_rect = pygame.Rect(panel_x + 15, curr_y, self.sidebar_width - 30, 210)
        pygame.draw.rect(self.screen, COLOR_CARD_BG, card2_rect, border_radius=8)
        pygame.draw.rect(self.screen, COLOR_BORDER, card2_rect, width=1, border_radius=8)

        lbl2 = self.font_header.render("CELL INSPECTOR", True, COLOR_TEXT_MAIN)
        self.screen.blit(lbl2, (panel_x + 25, curr_y + 12))

        # Determine target cell for inspection (selected cell or currently hovered)
        target_cell: Optional[Cell] = self.selected_cell
        if not target_cell and hover_coords:
            target_cell = self.grid.get_cell(*hover_coords)

        insp_y = curr_y + 40
        if target_cell:
            info = target_cell.to_dict()
            lines = [
                f"Coordinates:  ({info['coords'][0]}, {info['coords'][1]})",
                f"Terrain Type: {info['terrain']}",
                f"Passable:     {'Yes' if target_cell.is_passable else 'No (Obstacle)'}",
                f"Elevation:    {info['elevation']}",
                f"Moisture:     {info['moisture']}",
                f"Fertility:    {info['fertility']}",
                f"Occupant:     {info['occupant']}"
            ]
            for line in lines:
                c_val = COLOR_ACCENT if "Coordinates" in line or "Terrain" in line else COLOR_TEXT_MAIN
                t_surf = self.font_mono.render(line, True, c_val)
                self.screen.blit(t_surf, (panel_x + 25, insp_y))
                insp_y += 22
        else:
            msg = self.font_body.render("Hover or click a cell to inspect.", True, COLOR_TEXT_MUTED)
            self.screen.blit(msg, (panel_x + 25, insp_y + 20))

        curr_y += 230

        # --- Section 4: Controls & Paint Brush Card ---
        card3_rect = pygame.Rect(panel_x + 15, curr_y, self.sidebar_width - 30, 250)
        pygame.draw.rect(self.screen, COLOR_CARD_BG, card3_rect, border_radius=8)
        pygame.draw.rect(self.screen, COLOR_BORDER, card3_rect, width=1, border_radius=8)

        lbl3 = self.font_header.render("CONTROLS & TOOLS", True, COLOR_TEXT_MAIN)
        self.screen.blit(lbl3, (panel_x + 25, curr_y + 12))

        brush_name = self.active_brush.value.capitalize()
        b_surf = self.font_body.render(f"Active Brush: {brush_name} (Keys 1-4)", True, COLOR_ACCENT)
        self.screen.blit(b_surf, (panel_x + 25, curr_y + 36))

        controls_list = [
            "[F / F11] Toggle Fullscreen Mode",
            "[Z]       Cycle Grid Res (40x30..)",
            "[G]       Toggle Gridlines",
            "[R]       Regenerate Grid Map",
            "[1] Grass | [2] Water | [3] Soil | [4] Rock",
            "Left-Click Drag : Paint Terrain",
            "Right-Click     : Inspect Cell"
        ]
        ctrl_y = curr_y + 64
        for ctrl in controls_list:
            t_ctrl = self.font_mono.render(ctrl, True, COLOR_TEXT_MUTED)
            self.screen.blit(t_ctrl, (panel_x + 25, ctrl_y))
            ctrl_y += 23

    def render(self) -> None:
        """Main rendering tick frame."""
        mouse_px, mouse_py = pygame.mouse.get_pos()
        hover_coords = self.get_grid_coords_at_pixel(mouse_px, mouse_py)

        # Clear background
        self.screen.fill(COLOR_BG)

        # Draw grid surface & sidebar
        self.draw_grid_view(hover_coords)
        self.draw_sidebar(hover_coords)

        # Flip screen buffer
        pygame.display.flip()
        self.clock.tick(60)  # Smooth 60 FPS
