from __future__ import annotations
import random
from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import List, Tuple, Optional, Dict, Callable, Any


class CellState(Enum):
    EMPTY = auto()   
    SHIP = auto()    
    HIT = auto()     
    MISS = auto()   

class ShotResult(Enum):
    MISS = auto()
    HIT = auto()
    SUNK = auto()

class Cell:
    def __init__(self, state: CellState = CellState.EMPTY):
        self._state = state

    @property
    def state(self) -> CellState:
        return self._state

    @state.setter
    def state(self, value: CellState):
        self._state = value

    def __str__(self) -> str:
        symbols = {
            CellState.EMPTY: '·',
            CellState.SHIP: '■',
            CellState.HIT: 'X',
            CellState.MISS: '○'
        }
        return symbols[self._state]

class Ship:
    def __init__(self, coordinates: List[Tuple[int, int]]):
        self.coordinates = coordinates
        self._hits = 0

    @property
    def size(self) -> int:
        return len(self.coordinates)

    def hit(self) -> bool:
        self._hits += 1
        return self.is_sunk()

    def is_sunk(self) -> bool:
        return self._hits >= self.size

class Board:
    def __init__(self, size: int = 10):
        self.size = size
        self.grid: List[List[Cell]] = [[Cell() for _ in range(size)] for _ in range(size)]
        self.ships: List[Ship] = []

    def is_valid_coordinate(self, x: int, y: int) -> bool:
        return 0 <= x < self.size and 0 <= y < self.size

    def place_ship(self, coordinates: List[Tuple[int, int]]) -> bool:
        for x, y in coordinates:
            if not self.is_valid_coordinate(x, y):
                return False
            if self.grid[y][x].state != CellState.EMPTY:
                return False
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    nx, ny = x + dx, y + dy
                    if self.is_valid_coordinate(nx, ny) and self.grid[ny][nx].state == CellState.SHIP:
                        return False

        ship = Ship(coordinates)
        for x, y in coordinates:
            self.grid[y][x].state = CellState.SHIP
        self.ships.append(ship)
        return True

    def receive_shot(self, x: int, y: int) -> ShotResult:
        if not self.is_valid_coordinate(x, y):
            raise ValueError(f"Invalid coordinates: ({x}, {y})")

        cell = self.grid[y][x]
        if cell.state == CellState.HIT or cell.state == CellState.MISS:
            raise ValueError("Already shot at this cell")

        if cell.state == CellState.SHIP:
            cell.state = CellState.HIT
            for ship in self.ships:
                if (x, y) in ship.coordinates:
                    sunk = ship.hit()
                    return ShotResult.SUNK if sunk else ShotResult.HIT
        else:
            cell.state = CellState.MISS
            return ShotResult.MISS

        return ShotResult.MISS  

    def all_ships_sunk(self) -> bool:
        return all(ship.is_sunk() for ship in self.ships)