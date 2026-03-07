import pygame
import pymunk

from framework.game.sprite import Sprite
from framework.core.core import core_object
from framework.utils.animation import Animation
from framework.utils.pivot_2d import Pivot2D
from framework.utils.helpers import ColorType
from framework.utils.ui.ui_sprite import UiSprite

from math import degrees
from typing import Self

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
    
    @classmethod
    def get_instance_by_body(cls, body : pymunk.Body) -> Self|None:
        for instance in cls.active_elements:
            if instance.sim_body == body:
                return instance
        return None
    
    @classmethod
    def get_instance_by_shape(cls, shape : pymunk.Shape) -> Self|None:
        for instance in cls.active_elements:
            if shape in instance.sim_body.shapes:
                return instance
        return None
    
    def shape_belongs_to_this(self, shape : pymunk.Shape) -> bool:
        return shape in self.sim_body.shapes
    
    def body_belongs_to_this(self, body : pymunk.Body) -> bool:
        return body == self.sim_body
    
    """@classmethod
    def get_instances_by_collision_info(cls, collision_type : int|None = None, collision_category : int|list[int]|None = None, 
                                        collision_mask : int|list[int]|None = None) -> list[Self]:
        result = []
        for instance in cls.active_elements:
            """
    
    def remove_from_space(self):
        self.sim_body.space.remove(self.sim_body, *self.sim_body.shapes)
    
    def destroy(self):
        self.remove_from_space()
        self.kill_instance()
    
    def destroy_safe(self):
        self.remove_from_space()
        self.kill_instance_safe()

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
    
    def post_sim(self, delta: float):
        self.position = pygame.Vector2(self.sim_body.position)
        self.angle = degrees(self.sim_body.angle)
    
    def clean_instance(self):
        super().clean_instance()
    
    def draw(self, display : pygame.Surface):
        super().draw(display)

