from enum import IntEnum

class CollisionTypes(IntEnum):
    ENEMY_BALL = 1
    PLAYER_BALL = 2
    STATIC_GEOMETRY = 3
    ENEMY_PROJECTILE = 4
    PLAYER_PROJECTILE = 5