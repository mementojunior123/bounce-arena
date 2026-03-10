import pygame
from framework.utils.ui.ui_sprite import UiSprite
from framework.utils.helpers import make_circle
from framework.core.core import core_object

class MobileJoystick:
    def __init__(self, size : float, outer_radius : float, position : pygame.Vector2, deadzone_percent : float = 0):
        self.grab_id : int = -1
        self.current_grab_offset : pygame.Vector2
        self.size : float = size
        self.movement_range : float = outer_radius
        self.center : pygame.Vector2 = position
        self.deadzone : float = deadzone_percent
        self.lock : bool = False
    
    def is_grabbing(self) -> bool:
        return self.grab_id != -1 and self.grab_id in core_object.active_fingers

    def get_pos(self) -> pygame.Vector2:
        if not self.is_grabbing():
            return pygame.Vector2(0, 0)
        grab_pos : tuple[int, int] = core_object.active_fingers[self.grab_id]
        offset : pygame.Vector2 = grab_pos - self.center
        if offset.magnitude() < self.deadzone * self.movement_range:
            return pygame.Vector2(0, 0)
        return pygame.Vector2(offset.x / self.movement_range, offset.y / self.movement_range)
    
    def get_abs_pos(self) -> pygame.Vector2:
        if not self.is_grabbing():
            return pygame.Vector2(0, 0)
        grab_pos : tuple[int, int] = core_object.active_fingers[self.grab_id]
        offset : pygame.Vector2 = grab_pos - self.center
        if offset.magnitude() < self.deadzone * self.movement_range:
            return pygame.Vector2(0, 0)
        return offset
    
    def get_lock8_pos(self) -> pygame.Vector2:
        if not self.is_grabbing():
            return pygame.Vector2(0, 0)
        grab_pos : tuple[int, int] = core_object.active_fingers[self.grab_id]
        offset : pygame.Vector2 = grab_pos - self.center
        result : pygame.Vector2 = pygame.Vector2(0, 0)
        for direction in (pygame.Vector2(1, 0), pygame.Vector2(0, 1), pygame.Vector2(-1, 0), pygame.Vector2(0, -1)):
            if abs(offset.angle_to(direction)) < 60:
                result += direction
        return result

    
    def process_touch_event(self, event : pygame.Event):
        if event.type == pygame.FINGERDOWN:
            ...
        elif event.type == pygame.FINGERMOTION:
            ...
        elif event.type == pygame.FINGERUP:
            ...
    
    def make_connections(self):
        core_object.event_manager.bind(pygame.FINGERDOWN, self.process_touch_event)
        core_object.event_manager.bind(pygame.FINGERMOTION, self.process_touch_event)
        core_object.event_manager.bind(pygame.FINGERUP, self.process_touch_event)
    
    def remove_connections(self):
        core_object.event_manager.unbind(pygame.FINGERDOWN, self.process_touch_event)
        core_object.event_manager.unbind(pygame.FINGERMOTION, self.process_touch_event)
        core_object.event_manager.unbind(pygame.FINGERUP, self.process_touch_event)