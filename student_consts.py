from enum import IntFlag


class TileState(IntFlag):
    EMPTY = 0b0000  # 0
    WALL = 0b0001  # 1
    ROCK = 0b0010  # 2
    POOKA = 0b0100  # 4
    FYGAR = 0b1100  # 12


class Expressions(IntFlag):
    BLOCKED = (
        0b0011  # 3, do & with this to return if if it's blocked with a rock or a wall
    )
    ENEMY_TYPE = 0b1100  # 4, do & with this to return if it has an enemy (pooka or fygars) or 0 for no enemy
