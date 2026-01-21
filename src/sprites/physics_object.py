import pygame
from framework.game.sprite import Sprite
from framework.core.core import core_object

from framework.utils.animation import Animation
from framework.utils.pivot_2d import Pivot2D
from framework.utils.helpers import ColorType
import pymunk

def create_test_rect(w : int, h : int, pos : pygame.Vector2, color = "Red") -> tuple[pymunk.Body, pygame.Surface]:
    hw, hh = w // 2, h // 2
    new_body : pymunk.Body = pymunk.Body(50, 30)
    points = [(-hw, -hh), (-hw, hh), (hw, hh), (hw, -hh)]
    new_body.moment = pymunk.moment_for_poly(new_body.mass, points)
    new_shape = pymunk.shapes.Poly(new_body, ((-hw, -hh), (-hw, hh), (hw, hh), (hw, -hh)))
    new_body.position = tuple(pos)
    for s in new_body.shapes:
        s.cache_bb()
    new_surf = pygame.Surface((w, h))
    new_surf.fill(color)

    return new_body, new_surf

def create_test_player(w : int, h : int, pos : pygame.Vector2, color = "Red") -> tuple[pymunk.Body, pygame.Surface]:
    hw, hh = w // 2, h // 2
    new_body : pymunk.Body = pymunk.Body(50, 30)
    points = [(-hw, -hh), (-hw, hh), (hw, hh), (hw, -hh)]
    new_body.moment = pymunk.moment_for_poly(new_body.mass, points)
    new_shape = pymunk.shapes.Poly(new_body, ((-hw, -hh), (-hw, hh), (hw, hh), (hw, -hh)))
    new_shape.elasticity = 0.8
    new_shape.friction = 0.5
    new_body.position = tuple(pos)
    for s in new_body.shapes:
        s.cache_bb()
    new_surf = pygame.Surface((w, h))
    new_surf.fill(color)

    return new_body, new_surf

def create_test_ball(r : int, pos : pygame.Vector2, color = "Red", colorkey : ColorType|None=(0, 255, 0)) -> tuple[pymunk.Body, pygame.Surface]:
    new_body : pymunk.Body = pymunk.Body(50, 30)
    new_body.moment = pymunk.moment_for_circle(new_body.mass, 0, r)
    new_shape = pymunk.shapes.Circle(new_body, r)
    new_shape.elasticity = 0.8
    new_shape.friction = 0.5
    new_body.position = tuple(pos)
    for s in new_body.shapes:
        s.cache_bb()
    new_surf = pygame.Surface((r * 2, r * 2))

    new_surf.set_colorkey(colorkey)
    new_surf.fill(colorkey)
    pygame.draw.circle(new_surf, color, (r, r), r)
    pygame.draw.line(new_surf, "Red" if color != "Red" else "Blue", (r, r), (r, 0), width=r // 4 if r // 4 > 0 else 1)

    return new_body, new_surf

def ignore_gravity(body, gravity, damping, dt):
    pymunk.Body.update_velocity(body, (0, 0), damping, dt)


def create_test_ground(w : int, h : int, pos : pygame.Vector2, color = "Black") -> tuple[pymunk.Body, pygame.Surface]:
    hw, hh = w // 2, h // 2
    new_body : pymunk.Body = pymunk.Body(500, 30, pymunk.Body.STATIC)
    points = [(-hw, -hh), (-hw, hh), (hw, hh), (hw, -hh)]
    new_body.moment = pymunk.moment_for_poly(new_body.mass, points)
    new_shape = pymunk.shapes.Poly(new_body, points)
    new_shape.elasticity = 0.8
    new_shape.friction = 0.5
    
    new_body.position = (pos[0], pos[1])
    new_body.velocity_func = ignore_gravity
    for s in new_body.shapes:
        s.cache_bb()

    new_surf = pygame.Surface((w, h))
    new_surf.fill(color)

    return new_body, new_surf

class BasePhysicsObject(Sprite, sprite_count = 0):
    IMAGE_SIZE : tuple[int, int]|list[int] = (20, 60)
    
    test_image : pygame.Surface = pygame.surface.Surface(IMAGE_SIZE)
    pygame.draw.rect(test_image, "Red", (0,0, *IMAGE_SIZE))

    def __init__(self) -> None:
        super().__init__()
        self.sim_body : pymunk.Body
        pass

    @classmethod
    def spawn(cls, obj : pymunk.Body, image : pygame.Surface|None = None):
        raise NotImplementedError("Cannot instanciate a base-class")
        element = cls.inactive_elements[0]
        element.sim_body = obj
        element.image = image or cls.test_image
        element.rect = element.image.get_rect()

        element.position = pygame.Vector2(element.sim_body.position)
        element.align_rect()
        element.zindex = 0

        element.pivot = Pivot2D(element._position, element.image, (0, 255, 0))
        element.pivot.pivot_offset = pygame.Vector2(element.sim_body.center_of_gravity)
        element.current_camera = core_object.game.main_camera
        cls.unpool(element)
        return element
    
    def before_sim(self, delta : float):
        pass

    def before_step(self, delta : float, step_index : int, step_count : int):
        pass

    def after_step(self, delta : float, step_index : int, step_count : int):
        pass

    def post_sim(self, delta : float):
        self.position = pygame.Vector2(self.sim_body.position)
        self.angle = self.sim_body.angle
    
    def update(self, delta: float):
        pass
    
    def clean_instance(self):
        super().clean_instance()
        self.sim_body = None
    
    def draw(self, display : pygame.Surface):
        super().draw(display)

class BasicPhysicsObject(BasePhysicsObject, sprite_count = 20):
    IMAGE_SIZE : tuple[int, int]|list[int] = (20, 60)
    
    test_image : pygame.Surface = pygame.surface.Surface(IMAGE_SIZE)
    pygame.draw.rect(test_image, "Red", (0,0, *IMAGE_SIZE))

    def __init__(self) -> None:
        super().__init__()
        pass

    @classmethod
    def spawn(cls, obj : pymunk.Body, image : pygame.Surface|None = None):
        element = cls.inactive_elements[0]
        element.sim_body = obj
        element.image = image or cls.test_image
        element.rect = element.image.get_rect()

        element.position = pygame.Vector2(element.sim_body.position)
        element.align_rect()
        element.zindex = 0

        element.pivot = Pivot2D(element._position, element.image, (0, 255, 0))
        element.pivot.pivot_offset = pygame.Vector2(element.sim_body.center_of_gravity)
        element.current_camera = core_object.game.main_camera
        cls.unpool(element)
        return element
    
    def update(self, delta: float):
        self.position = pygame.Vector2(self.sim_body.position)
        self.angle = self.sim_body.angle
    
    def clean_instance(self):
        super().clean_instance()
    
    def draw(self, display : pygame.Surface):
        super().draw(display)

class PlayerPhysicsObject(BasePhysicsObject, sprite_count = 5):
    def __init__(self) -> None:
        super().__init__()
        pass

    @classmethod
    def spawn(cls, obj : pymunk.Body, image : pygame.Surface|None = None):
        element = cls.inactive_elements[0]
        element.sim_body = obj
        element.image = image or cls.test_image
        element.rect = element.image.get_rect()

        element.position = pygame.Vector2(element.sim_body.position)
        element.align_rect()
        element.zindex = 0

        element.pivot = Pivot2D(element._position, element.image, (0, 255, 0))
        element.pivot.pivot_offset = pygame.Vector2(element.sim_body.center_of_gravity)
        element.current_camera = core_object.game.main_camera
        cls.unpool(element)
        return element
    
    def before_sim(self, delta : float):
        keyboard_map = pygame.key.get_pressed()
        move_vector : pygame.Vector2 = pygame.Vector2(0,0)
        speed : int = 500
        angular_velocity : float = 0
        if keyboard_map[pygame.K_a]:
            move_vector += pygame.Vector2(-1, 0)
        if keyboard_map[pygame.K_d]:
            move_vector += pygame.Vector2(1, 0)
        if keyboard_map[pygame.K_s]:
            move_vector += pygame.Vector2(0, 5)
        if keyboard_map[pygame.K_w]:
            move_vector += pygame.Vector2(0, -5)
        if keyboard_map[pygame.K_q]:
            angular_velocity += -5
        if keyboard_map[pygame.K_e]:
            angular_velocity += 5
        if move_vector:
            self.sim_body.apply_force_at_world_point(tuple(move_vector * speed * delta), self.sim_body.position)
        if angular_velocity:
            self.sim_body.angular_velocity = angular_velocity * 1
        else:
            pass
            #self.sim_body.angular_velocity = 0

    def post_sim(self, delta : float):
        self.position = pygame.Vector2(self.sim_body.position)
        self.angle = self.sim_body.angle
    
    def update(self, delta: float):
        pass

    def clean_instance(self):
        super().clean_instance()
    
    def draw(self, display : pygame.Surface):
        super().draw(display)