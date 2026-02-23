import pygame
from framework.game.sprite import Sprite
from framework.core.core import core_object

from framework.utils.animation import Animation
from framework.utils.pivot_2d import Pivot2D
from framework.utils.helpers import ColorType
import pymunk

from typing import TypedDict, Literal, Callable, TypeAlias, NotRequired
from src.sprites.physics_object import BasePhysicsObject, PlayerPhysicsObject, BasicPhysicsObject

PhysicsObjetConstructor : TypeAlias = Callable[[pymunk.Body, pygame.Surface], BasePhysicsObject]

# create a struct that represents a piece of level geometry
class LevelGeometry(TypedDict):
    object_type : Literal['static_rect', 'dynamic_ball']

class StaticRect(LevelGeometry):
    width : int
    height : int
    pos : list[int, int]

    color : list[int, int, int]|str
    colorkey : NotRequired[list[int, int, int]|str|None]

    friction : NotRequired[float]
    bounciness : NotRequired[float]

class DynamicBall(LevelGeometry):
    radius : int
    pos : list[int, int]

    color : list[int, int, int]|str
    colorkey : NotRequired[list[int, int, int]|str|None]

    friction : NotRequired[float]
    bounciness : NotRequired[float]

# create functions that convert the struct into Body, Shape and Surface components

def create_level_geometry_object(obj : LevelGeometry, sim_space : pymunk.Space, constructor : PhysicsObjetConstructor = BasicPhysicsObject.spawn) -> BasePhysicsObject:
    match obj["object_type"]:
        case "static_rect":
            #obj : StaticRect = obj
            body, shapes, surf = create_static_rect(obj["width"], obj["height"], obj["pos"], obj["color"], 
                                                    obj.get('colorkey', (0, 255, 0)), obj.get("friction", 0.5), obj.get("bounciness", 0.8))
            sim_space.add(body, *shapes)
            return constructor(body, surf)
        case "dynamic_ball":
            obj : DynamicBall = obj
            body, shapes, surf = create_dynamic_ball(obj["radius"], obj["pos"], obj["color"], 
                                                     obj.get('colorkey', (0, 255, 0)), obj.get("friction", 0.5), obj.get("bounciness", 0.8))
            sim_space.add(body, *shapes)
            return constructor(body, surf)
        case _:
            raise ValueError

def create_dynamic_ball(r : int, pos : pygame.Vector2, color = "Red", colorkey : ColorType|None=(0, 255, 0),
                     friction : float = 0.5, bounce : float = 0.8) -> tuple[pymunk.Body, list[pymunk.Shape], pygame.Surface]:
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
    pygame.draw.line(new_surf, "Red" if color != "Red" else "Blue", (r, r), (r, 0), width=r // 4 if r // 4 > 0 else 1)

    return new_body, [new_shape], new_surf

def ignore_gravity(body, gravity, damping, dt):
    pymunk.Body.update_velocity(body, (0, 0), damping, dt)


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

test_level_geometry : list[DynamicBall|StaticRect] = [
    {"object_type" : "static_rect", "pos" : [480, 500], "width" : 960, "height" : 20, "color" : "Black"},
    {"object_type" : "static_rect", "pos" : [480, -20], "width" : 960, "height" : 20, "color" : "Black"},

    {"object_type" : "static_rect", "pos" : [0, 270], "width" : 20, "height" : 540, "color" : "Black", "bounciness" : 2},
    {"object_type" : "static_rect", "pos" : [960, 270], "width" : 20, "height" : 540, "color" : "Black"},
]