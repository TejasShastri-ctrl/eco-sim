"""
Unit tests for EcoSim Grid and Cell implementation
"""

import pytest
from src.grid import Grid, Cell, TerrainType


def test_grid_initialization():
    grid = Grid(width=20, height=15)
    assert grid.width == 20
    assert grid.height == 15
    assert len(grid.matrix) == 15
    assert len(grid.matrix[0]) == 20

    # Test top-left cell coordinates
    cell_0_0 = grid.get_cell(0, 0)
    assert cell_0_0 is not None
    assert cell_0_0.x == 0
    assert cell_0_0.y == 0

    # Test bottom-right cell coordinates
    cell_19_14 = grid.get_cell(19, 14)
    assert cell_19_14 is not None
    assert cell_19_14.x == 19
    assert cell_19_14.y == 14


def test_out_of_bounds():
    grid = Grid(width=10, height=10)
    assert grid.in_bounds(-1, 0) is False
    assert grid.in_bounds(0, -1) is False
    assert grid.in_bounds(10, 5) is False
    assert grid.in_bounds(5, 10) is False
    assert grid.get_cell(-1, 5) is None
    assert grid.get_cell(10, 10) is None


def test_get_neighbors():
    grid = Grid(width=5, height=5)
    
    # Center cell (2, 2) has 8 neighbors with diagonals
    neighbors_center = grid.get_neighbors(2, 2, radius=1, include_diagonals=True)
    assert len(neighbors_center) == 8

    # Corner cell (0, 0) has 3 neighbors
    neighbors_corner = grid.get_neighbors(0, 0, radius=1, include_diagonals=True)
    assert len(neighbors_corner) == 3

    # Cardinal only (no diagonals) for center cell -> 4 neighbors
    cardinal_center = grid.get_neighbors(2, 2, radius=1, include_diagonals=False)
    assert len(cardinal_center) == 4


def test_procedural_terrain_generation():
    grid = Grid(width=30, height=30)
    grid.generate_procedural_terrain(seed=42)

    stats = grid.get_terrain_stats()
    assert stats["total_cells"] == 900
    
    # Ensure all terrain percentages sum to 100%
    total_pct = sum(stats["percentages"].values())
    assert abs(total_pct - 100.0) < 0.2

    # Check that terrain types were assigned properly
    assert stats["counts"]["grass"] > 0
    assert stats["counts"]["water"] > 0 or stats["counts"]["soil"] > 0


def test_cell_passability():
    rock_cell = Cell(0, 0, terrain_type=TerrainType.ROCK)
    water_cell = Cell(1, 0, terrain_type=TerrainType.WATER)
    grass_cell = Cell(2, 0, terrain_type=TerrainType.GRASS)
    soil_cell = Cell(3, 0, terrain_type=TerrainType.SOIL)

    assert rock_cell.is_passable is False
    assert water_cell.is_passable is False
    assert grass_cell.is_passable is True
    assert soil_cell.is_passable is True
