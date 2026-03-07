from framework.core.core import core_object
from framework.utils.pivot_2d import Pivot2D
from src.sprites.physics_object import BasePhysicsObject

import pygame
import pymunk


from math import degrees


class ProjectilePhysicsObject(BasePhysicsObject, sprite_count = 20):
    IMAGE_SIZE : tuple[int, int]|list[int] = (20, 60)

    test_image : pygame.Surface = pygame.surface.Surface(IMAGE_SIZE)
    pygame.draw.rect(test_image, "Purple", (0,0, *IMAGE_SIZE))

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

    def update(self, delta):
        if not self.rect.colliderect(pygame.Rect(0, 0, 960, 540)):
            self.destroy_safe()

    def clean_instance(self):
        super().clean_instance()

    def draw(self, display : pygame.Surface):
        super().draw(display)