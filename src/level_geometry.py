"""
Team 1 ball : 1
Team 2 ball : 2
Static geometry : 3
Team 1 projectile : 4
Team 2 projectile : 5
"""

import pygame
from framework.game.sprite import Sprite
from framework.core.core import core_object

from framework.utils.animation import Animation
from framework.utils.helpers import value_to_bitmask
from framework.utils.pivot_2d import Pivot2D
from framework.utils.helpers import ColorType
import pymunk

from typing import TypedDict, Literal, Callable, TypeAlias, NotRequired
from src.sprites.physics_object import BasePhysicsObject, ProjectilePhysicsObject, BasicPhysicsObject
from math import ceil
from src.collision_type_constants import CollisionTypes

PhysicsObjetConstructor : TypeAlias = Callable[[pymunk.Body, pygame.Surface, pygame.Vector2|None], BasePhysicsObject]

# create a struct that represents a piece of level geometry
class BaseLevelGeometry(TypedDict):
    object_type : Literal['static_rect', 'dynamic_ball', 'static_poly']
    collision_category : NotRequired[int|list[int]]
    collision_mask : NotRequired[int|list[int]]
    collision_type : NotRequired[int|list[int]]

class StaticRect(BaseLevelGeometry):
    width : int
    height : int
    pos : list[int, int]

    color : list[int, int, int]|str
    colorkey : NotRequired[list[int, int, int]|str|None]

    friction : NotRequired[float]
    bounciness : NotRequired[float]

class StaticPoly(BaseLevelGeometry):
    points : list[tuple[int, int]]
    pos : list[int, int]

    color : list[int, int, int]|str
    colorkey : NotRequired[list[int, int, int]|str|None]

    friction : NotRequired[float]
    bounciness : NotRequired[float]


class DynamicBall(BaseLevelGeometry):
    radius : int
    pos : list[int, int]

    color : list[int, int, int]|str
    colorkey : NotRequired[list[int, int, int]|str|None]

    friction : NotRequired[float]
    bounciness : NotRequired[float]
    tracer : NotRequired[bool]

LevelGeometry : TypeAlias = StaticRect|StaticPoly|DynamicBall

def make_level_geometry_object(obj : BaseLevelGeometry, sim_space : pymunk.Space, constructor : PhysicsObjetConstructor = BasicPhysicsObject.spawn) -> BasePhysicsObject:
    match obj["object_type"]:
        case "static_rect":
            obj : StaticRect = obj
            body, shapes, surf = create_static_rect(obj["width"], obj["height"], obj["pos"], obj["color"], 
                                                    obj.get('colorkey', (0, 255, 0)), obj.get("friction", 0.5), obj.get("bounciness", 0.8))
            for shape in shapes:
                shape.collision_type = value_to_bitmask(obj.get("collision_type", 0))
                collision_category = value_to_bitmask(obj.get("collision_category", pymunk.ShapeFilter.ALL_CATEGORIES()))
                collision_mask = value_to_bitmask(obj.get("collision_mask", pymunk.ShapeFilter.ALL_MASKS()))
                shape.filter = pymunk.ShapeFilter(categories=collision_category, mask=collision_mask)

            sim_space.add(body, *shapes)
            return constructor(body, surf)
        case "dynamic_ball":
            obj : DynamicBall = obj
            body, shapes, surf = create_dynamic_ball(obj["radius"], obj["pos"], obj["color"], 
                                                     obj.get('colorkey', (0, 255, 0)), obj.get("friction", 0.5), obj.get("bounciness", 0.8), obj.get("tracer", True))
            for shape in shapes:
                shape.collision_type = value_to_bitmask(obj.get("collision_type", 0))
                collision_category = value_to_bitmask(obj.get("collision_category", pymunk.ShapeFilter.ALL_CATEGORIES()))
                collision_mask = value_to_bitmask(obj.get("collision_mask", pymunk.ShapeFilter.ALL_MASKS()))
                shape.filter = pymunk.ShapeFilter(categories=collision_category, mask=collision_mask)

            sim_space.add(body, *shapes)
            return constructor(body, surf)
        case "static_poly":
            obj : StaticPoly = obj
            body, shapes, surf, cog = create_static_poly(obj["points"], obj["pos"], obj["color"], 
                                                    obj.get('colorkey', (0, 255, 0)), obj.get("friction", 0.5), obj.get("bounciness", 0.8))
            for shape in shapes:
                shape.collision_type = value_to_bitmask(obj.get("collision_type", 0))
                collision_category = value_to_bitmask(obj.get("collision_category", pymunk.ShapeFilter.ALL_CATEGORIES()))
                collision_mask = value_to_bitmask(obj.get("collision_mask", pymunk.ShapeFilter.ALL_MASKS()))
                shape.filter = pymunk.ShapeFilter(categories=collision_category, mask=collision_mask)
                
            sim_space.add(body, *shapes)
            return constructor(body, surf, cog)
        case _:
            raise ValueError

def calculate_cog(points : list[tuple[int, int]]) -> pygame.Vector2:
    return pymunk.Poly(None, points).center_of_gravity

def create_dynamic_ball(r : int, pos : pygame.Vector2, color = "Red", colorkey : ColorType|None=(0, 255, 0),
                     friction : float = 0.5, bounce : float = 0.8, tracer : bool = True) -> tuple[pymunk.Body, list[pymunk.Shape], pygame.Surface]:
    new_body : pymunk.Body = pymunk.Body(50, 30)
    new_body.moment = pymunk.moment_for_circle(new_body.mass, 0, r)
    new_shape = pymunk.shapes.Circle(new_body, r)
    new_shape.elasticity = bounce
    new_shape.friction = friction
    new_body.position = tuple(pos)
    for s in new_body.shapes:
        s.cache_bb()
    new_surf = pygame.Surface((r * 2, r * 2))
    new_surf.set_colorkey(colorkey)
    new_surf.fill(colorkey)
    pygame.draw.circle(new_surf, color, (r, r), r)
    if tracer:
        pygame.draw.line(new_surf, "Red" if color != "Red" else "Blue", (r, r), (r, 0), width=r // 4 if r // 4 > 0 else 1)

    return new_body, [new_shape], new_surf

def ignore_gravity(body, gravity, damping, dt):
    pymunk.Body.update_velocity(body, (0, 0), damping, dt)

def create_static_poly(points : list[tuple[int, int]], pos : list[int, int], color = "Red", colorkey : ColorType|None=(0, 255, 0),
                     friction : float = 0.5, bounce : float = 0.8) -> tuple[pymunk.Body, list[pymunk.Shape], pygame.Surface, pygame.Vector2]:
    left, right = min(point[0] for point in points), max(point[0] for point in points)
    top, bottom = min(point[1] for point in points), max(point[1] for point in points)
    centerx = left + (right - left) // 2
    centry = top + (bottom - top) // 2
    new_shape = pymunk.shapes.Poly(None, points)
    center_of_gravity = new_shape.center_of_gravity
    t = pymunk.transform.Transform(tx=-center_of_gravity.x, ty=-center_of_gravity.y)
    new_shape = pymunk.shapes.Poly(None, points, transform=t)

    new_body : pymunk.Body = pymunk.Body(500, 30, pymunk.Body.STATIC)
    new_body.moment = pymunk.moment_for_poly(new_body.mass, points)

    new_shape.body = new_body
    new_body.shapes

    new_shape.elasticity = bounce
    new_shape.friction = friction
    
    new_body.position = (pos[0], pos[1])
    new_body.velocity_func = ignore_gravity
    for s in new_body.shapes:
        s.cache_bb()

    new_surf = pygame.Surface((abs(right - left) + 1, abs(bottom - top) + 1))

    new_surf.set_colorkey(colorkey)
    new_surf.fill(colorkey)

    pygame.draw.polygon(new_surf, color, list(point - pygame.Vector2(left, top) for point in points))
    cog_offset = center_of_gravity - (centerx, centry)
    return new_body, [new_shape], new_surf, cog_offset


def create_static_rect(w : int, h : int, pos : pygame.Vector2, color = "Black", colorkey : ColorType|None=(0, 255, 0),
                     friction : float = 0.5, bounce : float = 0.8) -> tuple[pymunk.Body, list[pymunk.Shape], pygame.Surface]:
    hw, hh = w // 2, h // 2
    new_body : pymunk.Body = pymunk.Body(500, 30, pymunk.Body.STATIC)
    points = [(-hw, -hh), (-hw, hh), (hw, hh), (hw, -hh)]
    new_body.moment = pymunk.moment_for_poly(new_body.mass, points)
    new_shape = pymunk.shapes.Poly(new_body, points)
    new_shape.elasticity = bounce
    new_shape.friction = friction
    
    new_body.position = (pos[0], pos[1])
    new_body.velocity_func = ignore_gravity
    for s in new_body.shapes:
        s.cache_bb()
    new_surf = pygame.Surface((w, h))

    new_surf.set_colorkey(colorkey)
    new_surf.fill(colorkey)

    new_surf.fill(color)

    return new_body, [new_shape], new_surf

def make_projectile(spawn_pos : list[int, int], velocity : list[int, int], sim_space : pymunk.Space, is_team2 : bool = False) -> ProjectilePhysicsObject:
    body, shapes, surf = create_dynamic_ball(10, spawn_pos, tracer=False)
    for shape in shapes:
        shape.collision_type = value_to_bitmask(CollisionTypes.TEAM2_PROJECTILE if is_team2 else CollisionTypes.TEAM1_PROJECTILE)
        collision_category = value_to_bitmask([CollisionTypes.TEAM2_PROJECTILE] if is_team2 else [CollisionTypes.TEAM1_PROJECTILE])
        collision_mask = value_to_bitmask([CollisionTypes.TEAM1_BALL] if is_team2 else [CollisionTypes.TEAM2_BALL])
        shape.filter = pymunk.ShapeFilter(categories=collision_category, mask=collision_mask)
    body.velocity = velocity
    body.velocity_func = ignore_gravity
    sim_space.add(body, *shapes)
    return ProjectilePhysicsObject.spawn(body, surf)

test_level_geometry : list[LevelGeometry] = [
    {"object_type" : "static_rect", "pos" : [480, 500], "width" : 960, "height" : 20, "color" : "Black", 
     "collision_category" : [CollisionTypes.STATIC_GEOMETRY], "collision_mask" : [CollisionTypes.TEAM1_BALL, CollisionTypes.TEAM2_BALL]},

    {"object_type" : "static_rect", "pos" : [10, 450], "width" : 20, "height" : 100, "color" : "Black", 
     "collision_category" : [CollisionTypes.STATIC_GEOMETRY], "collision_mask" : [CollisionTypes.TEAM1_BALL, CollisionTypes.TEAM2_BALL]},

    {"object_type" : "static_rect", "pos" : [950, 450], "width" : 20, "height" : 100, "color" : "Black", 
     "collision_category" : [CollisionTypes.STATIC_GEOMETRY], "collision_mask" : [CollisionTypes.TEAM1_BALL, CollisionTypes.TEAM2_BALL]},

    {"object_type" : "static_rect", "pos" : [10, 250], "width" : 20, "height" : 100, "color" : "Black", 
     "collision_category" : [CollisionTypes.STATIC_GEOMETRY], "collision_mask" : [CollisionTypes.TEAM1_BALL, CollisionTypes.TEAM2_BALL]},

    {"object_type" : "static_rect", "pos" : [950, 250], "width" : 20, "height" : 100, "color" : "Black", 
     "collision_category" : [CollisionTypes.STATIC_GEOMETRY], "collision_mask" : [CollisionTypes.TEAM1_BALL, CollisionTypes.TEAM2_BALL]},

    {"object_type" : "static_rect", "pos" : [10, 50], "width" : 20, "height" : 100, "color" : "Black", 
     "collision_category" : [CollisionTypes.STATIC_GEOMETRY], "collision_mask" : [CollisionTypes.TEAM1_BALL, CollisionTypes.TEAM2_BALL]},

    {"object_type" : "static_rect", "pos" : [950, 50], "width" : 20, "height" : 100, "color" : "Black", 
     "collision_category" : [CollisionTypes.STATIC_GEOMETRY], "collision_mask" : [CollisionTypes.TEAM1_BALL, CollisionTypes.TEAM2_BALL]},

    {"object_type" : "static_poly", "pos" : [480, 270], "color" : "Black", "points" : [(-50, 50), (50, 50), (50, -50)], 
     "collision_category" : [CollisionTypes.STATIC_GEOMETRY], "collision_mask" : [CollisionTypes.TEAM1_BALL, CollisionTypes.TEAM2_BALL]},
    {"object_type" : "static_poly", "pos" : [200, 270], "color" : "Black", "points" : [(-50, 0), (0, 50), (100, -50), (50, -100)], "bounciness" : 2, 
     "collision_category" : [CollisionTypes.STATIC_GEOMETRY], "collision_mask" : [CollisionTypes.TEAM1_BALL, CollisionTypes.TEAM2_BALL]},
]