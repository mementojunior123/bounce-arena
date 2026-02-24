import pygame
from framework.game.sprite import Sprite
from framework.core.core import core_object

from framework.utils.animation import Animation
from framework.utils.pivot_2d import Pivot2D
from framework.utils.helpers import ColorType
import pymunk

from math import degrees

class BasePhysicsObject(Sprite, sprite_count = 0):
    IMAGE_SIZE : tuple[int, int]|list[int] = (20, 60)
    
    test_image : pygame.Surface = pygame.surface.Surface(IMAGE_SIZE)
    pygame.draw.rect(test_image, "Red", (0,0, *IMAGE_SIZE))

    def __init__(self) -> None:
        super().__init__()
        self.sim_body : pymunk.Body
        pass

    @classmethod
    def spawn(cls, obj : pymunk.Body, image : pygame.Surface|None = None,
              pivot_offest : pygame.Vector2|None = None):
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
        self.angle = degrees(self.sim_body.angle)
    
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
    def spawn(cls, obj : pymunk.Body, image : pygame.Surface|None = None,
              pivot_offest : pygame.Vector2|None = None):
        element = cls.inactive_elements[0]
        element.sim_body = obj
        element.image = image or cls.test_image
        element.rect = element.image.get_rect()

        element.position = pygame.Vector2(element.sim_body.position)
        element.align_rect()
        element.zindex = 0

        element.pivot = Pivot2D(element._position, element.image, element.image.get_colorkey() or (0, 255, 0))
        element.pivot.pivot_offset = pygame.Vector2(element.sim_body.center_of_gravity) + (pivot_offest or pygame.Vector2(0,0))
        element.current_camera = core_object.game.main_camera
        cls.unpool(element)
        return element
    
    def update(self, delta: float):
        self.position = pygame.Vector2(self.sim_body.position)
        self.angle = degrees(self.sim_body.angle)
    
    def clean_instance(self):
        super().clean_instance()
    
    def draw(self, display : pygame.Surface):
        super().draw(display)

class PlayerPhysicsObject(BasePhysicsObject, sprite_count = 5):
    def __init__(self) -> None:
        super().__init__()
        pass

    @classmethod
    def spawn(cls, obj : pymunk.Body, image : pygame.Surface|None = None,
              pivot_offest : pygame.Vector2|None = None):
        element = cls.inactive_elements[0]
        element.sim_body = obj
        element.image = image or cls.test_image
        element.rect = element.image.get_rect()

        element.position = pygame.Vector2(element.sim_body.position)
        element.align_rect()
        element.zindex = 0

        element.pivot = Pivot2D(element._position, element.image, element.image.get_colorkey() or (0, 255, 0))
        element.pivot.pivot_offset = pygame.Vector2(element.sim_body.center_of_gravity) + (pivot_offest or pygame.Vector2(0,0))
        element.current_camera = core_object.game.main_camera
        cls.unpool(element)
        return element
    
    def before_step(self, delta : float, step_index : int, step_count : int):
        keyboard_map = pygame.key.get_pressed()
        move_vector : pygame.Vector2 = pygame.Vector2(0,0)
        speed : int = 500
        angular_velocity : float = 0
        if keyboard_map[pygame.K_a]:
            move_vector += pygame.Vector2(-1, 0)
        if keyboard_map[pygame.K_d]:
            move_vector += pygame.Vector2(1, 0)
        if keyboard_map[pygame.K_s]:
            move_vector += pygame.Vector2(0, 2.5)
        if keyboard_map[pygame.K_w]:
            move_vector += pygame.Vector2(0, -2.5)
        if keyboard_map[pygame.K_q]:
            angular_velocity += -1
        if keyboard_map[pygame.K_e]:
            angular_velocity += 1
        if move_vector:
            self.sim_body.apply_force_at_world_point(tuple(move_vector * speed), self.sim_body.position) # Force is applied over time in the sim step, so no need to muliply by delta
        if angular_velocity:
            self.sim_body.angular_velocity = angular_velocity * 0.5
        else:
            pass
            self.sim_body.angular_velocity = 0
    
    def apply_propulsion(self):
        force : float = 2500
        direction : pygame.Vector2 = pygame.Vector2(0, 1).rotate(self.angle)
        self.sim_body.apply_impulse_at_world_point(tuple(direction * force), self.sim_body.position) # An impulse is instatenous, so no need to multiply it by delta
        space = self.sim_body.space

        shot_origin : pymunk.Vec2d = self.sim_body.local_to_world((0, -25))
        shot_end : pymunk.Vec2d = self.sim_body.local_to_world((0, -2000))
        hits = space.segment_query(shot_origin, shot_end, 25, pymunk.ShapeFilter())
        for hit in hits:
            if not hit.shape:
                continue
            if hit.shape.collision_type == 1:
                hit.shape.body.apply_impulse_at_world_point(tuple(-direction * force), hit.point)
    def post_sim(self, delta : float):
        self.position = pygame.Vector2(self.sim_body.position)
        self.angle = degrees(self.sim_body.angle)
    
    def update(self, delta: float):
        pass

    def clean_instance(self):
        super().clean_instance()
    
    def draw(self, display : pygame.Surface):
        super().draw(display)
    
    def handle_keydown_event(self, event : pygame.Event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.apply_propulsion()
    
    @classmethod
    def receive_keydown_event(cls, event : pygame.Event):
        for element in cls.active_elements:
            element.handle_keydown_event(event)

def make_connections():
    core_object.event_manager.bind(pygame.KEYDOWN, PlayerPhysicsObject.receive_keydown_event)

def remove_connections():
    core_object.event_manager.unbind(pygame.KEYDOWN, PlayerPhysicsObject.receive_keydown_event)


class EnemyPhysicsObject(BasePhysicsObject, sprite_count = 5):
    def __init__(self) -> None:
        super().__init__()
        pass

    @classmethod
    def spawn(cls, obj : pymunk.Body, image : pygame.Surface|None = None,
              pivot_offest : pygame.Vector2|None = None):
        element = cls.inactive_elements[0]
        element.sim_body = obj
        element.image = image or cls.test_image
        element.rect = element.image.get_rect()

        element.position = pygame.Vector2(element.sim_body.position)
        element.align_rect()
        element.zindex = 0

        element.pivot = Pivot2D(element._position, element.image, element.image.get_colorkey() or (0, 255, 0))
        element.pivot.pivot_offset = pygame.Vector2(element.sim_body.center_of_gravity) + (pivot_offest or pygame.Vector2(0,0))
        element.current_camera = core_object.game.main_camera
        cls.unpool(element)
        return element
    
    def before_step(self, delta : float, step_index : int, step_count : int):
        return
        keyboard_map = pygame.key.get_pressed()
        move_vector : pygame.Vector2 = pygame.Vector2(0,0)
        speed : int = 500
        angular_velocity : float = 0
        if keyboard_map[pygame.K_a]:
            move_vector += pygame.Vector2(-1, 0)
        if keyboard_map[pygame.K_d]:
            move_vector += pygame.Vector2(1, 0)
        if keyboard_map[pygame.K_s]:
            move_vector += pygame.Vector2(0, 2.5)
        if keyboard_map[pygame.K_w]:
            move_vector += pygame.Vector2(0, -2.5)
        if keyboard_map[pygame.K_q]:
            angular_velocity += -1
        if keyboard_map[pygame.K_e]:
            angular_velocity += 1
        if move_vector:
            self.sim_body.apply_force_at_world_point(tuple(move_vector * speed), self.sim_body.position) # Force is applied over time in the sim step, so no need to muliply by delta
        if angular_velocity:
            self.sim_body.angular_velocity = angular_velocity * 2
        else:
            pass
            self.sim_body.angular_velocity = 0
    
    def apply_propulsion(self):
        force : float = 2500
        direction : pygame.Vector2 = pygame.Vector2(0, 1).rotate(self.angle)
        self.sim_body.apply_impulse_at_world_point(tuple(direction * force), self.sim_body.position) # An impulse is instatenous, so no need to multiply it by delta

    def post_sim(self, delta : float):
        self.position = pygame.Vector2(self.sim_body.position)
        self.angle = degrees(self.sim_body.angle)
    
    def update(self, delta: float):
        pass

    def clean_instance(self):
        super().clean_instance()
    
    def draw(self, display : pygame.Surface):
        super().draw(display)