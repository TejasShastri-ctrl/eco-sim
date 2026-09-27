"""
EcoSim Grid Module
Defines terrain biomes, individual Cell state, and the main 2D Grid data structure.
"""

from enum import Enum, auto
import random
import math
from typing import List, Tuple, Optional, Dict, Any


class TerrainType(Enum):
    WATER = "water"
    SOIL = "soil"
    GRASS = "grass"
    ROCK = "rock"


# Aesthetic color scheme for terrain biomes (RGB tuples)
TERRAIN_COLORS: Dict[TerrainType, Tuple[int, int, int]] = {
    TerrainType.WATER: (45, 112, 179),    # Deep river/lake blue
    TerrainType.SOIL: (139, 94, 60),      # Rich earth brown
    TerrainType.GRASS: (46, 125, 50),     # Lush forest green
    TerrainType.ROCK: (100, 110, 120),    # Slate grey mountain rock
}


class Cell:
    """Represents a single discrete square cell in the simulation grid."""

    __slots__ = ('x', 'y', 'terrain_type', 'elevation', 'moisture', 'fertility', 'occupant')

    def __init__(
        self,
        x: int,
        y: int,
        terrain_type: TerrainType = TerrainType.GRASS,
        elevation: float = 0.5,
        moisture: float = 0.5,
        fertility: float = 0.5
    ):
        self.x = x
        self.y = y
        self.terrain_type = terrain_type
        self.elevation = elevation
        self.moisture = moisture
        self.fertility = fertility
        self.occupant: Optional[Any] = None  # Reserved for Agents/Plants in future phases

    @property
    def is_passable(self) -> bool:
        """Determines if an agent can walk onto this cell."""
        return self.terrain_type != TerrainType.ROCK and self.terrain_type != TerrainType.WATER

    def to_dict(self) -> Dict[str, Any]:
        """Returns cell state dictionary for inspection UI and debugging."""
        return {
            "coords": (self.x, self.y),
            "terrain": self.terrain_type.value.capitalize(),
            "elevation": round(self.elevation, 2),
            "moisture": round(self.moisture, 2),
            "fertility": round(self.fertility, 2),
            "occupant": str(self.occupant) if self.occupant else "Empty"
        }


class Grid:
    """Represents the 2D spatial environment for the ecosystem simulation."""

    def __init__(self, width: int = 40, height: int = 30):
        self.width = width
        self.height = height
        self.matrix: List[List[Cell]] = [
            [Cell(x, y) for x in range(width)]
            for y in range(height)
        ]

    def in_bounds(self, x: int, y: int) -> bool:
        """Checks whether coordinates lie within the grid boundaries."""
        return 0 <= x < self.width and 0 <= y < self.height

    def resize(self, new_width: int, new_height: int, seed: Optional[int] = None) -> None:
        """Resizes the grid matrix dimensions and regenerates procedural terrain."""
        self.width = new_width
        self.height = new_height
        self.matrix = [
            [Cell(x, y) for x in range(new_width)]
            for y in range(new_height)
        ]
        self.generate_procedural_terrain(seed=seed)

    def get_cell(self, x: int, y: int) -> Optional[Cell]:
        """Retrieves cell at (x, y) or None if out of bounds."""
        if self.in_bounds(x, y):
            return self.matrix[y][x]
        return None

    def get_neighbors(
        self,
        x: int,
        y: int,
        radius: int = 1,
        include_diagonals: bool = True
    ) -> List[Cell]:
        """Returns adjacent cells within specified radius."""
        neighbors = []
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if dx == 0 and dy == 0:
                    continue
                if not include_diagonals and abs(dx) + abs(dy) > radius:
                    continue
                
                nx, ny = x + dx, y + dy
                cell = self.get_cell(nx, ny)
                if cell:
                    neighbors.append(cell)
        return neighbors

    def generate_procedural_terrain(
        self,
        seed: Optional[int] = None,
        water_ratio: float = 0.15,
        rock_ratio: float = 0.10,
        smoothing_passes: int = 3
    ) -> None:
        """
        Generates rich procedural forest biomes using distance-based noise 
        and cellular automata smoothing.
        """
        if seed is not None:
            random.seed(seed)
        else:
            seed = random.randint(0, 999999)

        # Step 1: Assign initial random elevation & moisture gradient
        center_x, center_y = self.width / 2.0, self.height / 2.0
        max_dist = math.sqrt(center_x**2 + center_y**2)

        for y in range(self.height):
            for x in range(self.width):
                # Calculate distance from center for subtle biome clustering
                dist = math.sqrt((x - center_x)**2 + (y - center_y)**2) / max_dist
                
                # Base random noise with frequency variation
                noise_elev = random.random() * 0.7 + (1.0 - dist) * 0.3
                noise_moist = random.random() * 0.8 + (1.0 - dist) * 0.2

                cell = self.matrix[y][x]
                cell.elevation = max(0.0, min(1.0, noise_elev))
                cell.moisture = max(0.0, min(1.0, noise_moist))

                # Primary terrain classification
                if noise_moist < water_ratio:
                    cell.terrain_type = TerrainType.WATER
                    cell.fertility = 0.1
                elif noise_elev > (1.0 - rock_ratio):
                    cell.terrain_type = TerrainType.ROCK
                    cell.fertility = 0.05
                elif noise_moist > 0.4:
                    cell.terrain_type = TerrainType.GRASS
                    cell.fertility = round(0.6 + 0.4 * noise_moist, 2)
                else:
                    cell.terrain_type = TerrainType.SOIL
                    cell.fertility = round(0.3 + 0.3 * noise_moist, 2)

        # Step 2: Smooth terrain using cellular automata (majority rule for natural biomes)
        for _ in range(smoothing_passes):
            new_types = [[self.matrix[y][x].terrain_type for x in range(self.width)] for y in range(self.height)]
            for y in range(self.height):
                for x in range(self.width):
                    neighbors = self.get_neighbors(x, y, radius=1, include_diagonals=True)
                    if not neighbors:
                        continue
                    
                    # Count neighbor terrain types
                    counts: Dict[TerrainType, int] = {}
                    for n in neighbors:
                        counts[n.terrain_type] = counts.get(n.terrain_type, 0) + 1

                    # Most common neighbor
                    majority_terrain = max(counts.items(), key=lambda item: item[1])[0]
                    # Smooth water/rock features if surrounded by majority
                    if counts.get(majority_terrain, 0) >= 5:
                        new_types[y][x] = majority_terrain

            # Apply smoothed types back
            for y in range(self.height):
                for x in range(self.width):
                    self.matrix[y][x].terrain_type = new_types[y][x]

    def get_terrain_stats(self) -> Dict[str, Any]:
        """Calculates terrain breakdown across the grid."""
        total = self.width * self.height
        counts: Dict[TerrainType, int] = {t: 0 for t in TerrainType}

        for y in range(self.height):
            for x in range(self.width):
                counts[self.matrix[y][x].terrain_type] += 1

        stats = {
            "total_cells": total,
            "counts": {t.value: counts[t] for t in TerrainType},
            "percentages": {t.value: round((counts[t] / total) * 100, 1) for t in TerrainType}
        }
        return stats
