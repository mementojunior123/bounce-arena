from enum import IntEnum

class CollisionTypes(IntEnum):
    TEAM1_BALL = 1
    TEAM2_BALL = 2
    STATIC_GEOMETRY = 3
    TEAM1_PROJECTILE = 4
    TEAM2_PROJECTILE = 5