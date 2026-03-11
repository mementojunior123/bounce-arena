import pygame
from framework.utils.ui.ui_sprite import UiSprite
from framework.utils.helpers import make_circle

class MobileJoystick:
    def __init__(self, size : int, outer_radius : int, position : pygame.Vector2, deadzone_percent : float = 0, emulate_touch : bool = False):
        if not peformed_runtime_imports: runtime_imports()
        self.grab_id : int = -1
        self.size : int = size
        self.movement_range : int = outer_radius
        self.center : pygame.Vector2 = position
        self.deadzone : float = deadzone_percent
        self.display_size : tuple[int, int] = core_object.main_display.get_size()

        circle1 : pygame.Surface = make_circle(self.size, (200, 200, 200))
        circle1.set_alpha(225)

        circle2 : pygame.Surface = make_circle(self.movement_range, (125, 125, 125))
        circle2.set_alpha(140)

        self.visual_joystick : UiSprite = UiSprite(circle1, circle1.get_rect(center=position), -1, "joystick_movable")
        self.visual_joy_background : UiSprite = UiSprite(circle2, circle2.get_rect(center=position), -1, "joystick_background", zindex=-1)
        self.emulate_touch : bool = emulate_touch
    

    @property
    def visuals(self) -> list[UiSprite]:
        return [self.visual_joystick, self.visual_joy_background]
    
    @property
    def current_grab_offset(self):
        if not self.is_grabbed():
            return pygame.Vector2(0, 0)
        result : pygame.Vector2 = core_object.active_fingers[self.grab_id] - self.center
        if result.length() > self.movement_range:
            result.scale_to_length(self.movement_range)
        return result
    
    def is_grabbed(self) -> bool:
        return self.grab_id != -1 and self.grab_id in core_object.active_fingers

    def get_pos(self, normalize : bool = False) -> pygame.Vector2:
        """
        Gets x and y normalized to the [0, 1] range
        Optionally you can normalize the result vector
        """
        if not self.is_grabbed():
            return pygame.Vector2(0, 0)
        offset : pygame.Vector2 = self.current_grab_offset
        if offset.magnitude() < self.deadzone * self.movement_range:
            return pygame.Vector2(0, 0)
        if not normalize:
            return pygame.Vector2(offset.x / self.movement_range, offset.y / self.movement_range)
        else:
            return pygame.Vector2(offset.x / self.movement_range, offset.y / self.movement_range).normalize()
    
    def get_abs_pos(self) -> pygame.Vector2:
        """
        Gets x and y in terms of pixels
        """
        if not self.is_grabbed():
            return pygame.Vector2(0, 0)
        offset : pygame.Vector2 = self.current_grab_offset
        if offset.magnitude() < self.deadzone * self.movement_range:
            return pygame.Vector2(0, 0)
        return offset
    
    def get_lock8_pos(self) -> pygame.Vector2:
        """
        Gets the direction in terms of an 8 direction joystick. Isn't normalized
        """
        if not self.is_grabbed():
            return pygame.Vector2(0, 0)
        offset : pygame.Vector2 = self.current_grab_offset
        if offset.magnitude() < self.deadzone * self.movement_range:
            return pygame.Vector2(0, 0)
        result : pygame.Vector2 = pygame.Vector2(0, 0)
        for direction in (pygame.Vector2(1, 0), pygame.Vector2(0, 1), pygame.Vector2(-1, 0), pygame.Vector2(0, -1)):
            angle_diff : float = abs(offset.angle_to(direction))
            if angle_diff > 180: angle_diff -= 2 * abs(180 - angle_diff)
            if angle_diff < 67.5:
                result += direction
        return result
    
    def grab(self, finger_id : int):
        self.grab_id = finger_id
        self.visual_joystick.rect.center = round(self.center + self.current_grab_offset)
    
    def release(self):
        self.grab_id = -1
        self.visual_joystick.rect.center = round(self.center + self.current_grab_offset)
    
    def process_touch_event(self, event : pygame.Event):
        if event.type == pygame.FINGERDOWN:
            if self.is_grabbed():
                return
            x : float = event.x * self.display_size[0]
            y : float = event.y * self.display_size[1]
            if (self.center - (x, y)).magnitude() < self.size:
                self.grab(event.finger_id)
        elif event.type == pygame.FINGERMOTION:
            if not self.is_grabbed():
                return
            if event.finger_id != self.grab_id:
                return
            self.visual_joystick.rect.center = round(self.center + self.current_grab_offset)
        elif event.type == pygame.FINGERUP:
            if event.finger_id == self.grab_id:
                self.release()
    
    def emulate_process_mouse_event(self, event : pygame.Event):
        # button 1 = left
        # button 2 = middle
        # button 3 = right
        # button 6 = side button backwards
        # button 7 = side button forwards
        if not self.emulate_touch: return
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button != 1:
                return
            if self.is_grabbed():
                return
            x, y = event.pos
            if (self.center - (x, y)).magnitude() < self.size:
                self.grab(10)
        elif event.type == pygame.MOUSEMOTION:
            if not self.is_grabbed():
                return
            self.visual_joystick.rect.center = round(self.center + self.current_grab_offset)
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.grab_id == 10:
                self.release()
    
    def make_connections(self):
        core_object.event_manager.bind(pygame.FINGERDOWN, self.process_touch_event)
        core_object.event_manager.bind(pygame.FINGERMOTION, self.process_touch_event)
        core_object.event_manager.bind(pygame.FINGERUP, self.process_touch_event)

        core_object.event_manager.bind(pygame.MOUSEBUTTONDOWN, self.emulate_process_mouse_event)
        core_object.event_manager.bind(pygame.MOUSEMOTION, self.emulate_process_mouse_event)
        core_object.event_manager.bind(pygame.MOUSEBUTTONUP, self.emulate_process_mouse_event)
    
    def remove_connections(self):
        core_object.event_manager.unbind(pygame.FINGERDOWN, self.process_touch_event)
        core_object.event_manager.unbind(pygame.FINGERMOTION, self.process_touch_event)
        core_object.event_manager.unbind(pygame.FINGERUP, self.process_touch_event)

        core_object.event_manager.unbind(pygame.MOUSEBUTTONDOWN, self.emulate_process_mouse_event)
        core_object.event_manager.unbind(pygame.MOUSEMOTION, self.emulate_process_mouse_event)
        core_object.event_manager.unbind(pygame.MOUSEBUTTONUP, self.emulate_process_mouse_event)
    
    def add_to_ui(self):
        core_object.main_ui.add_multiple(self.visuals)
    
    def remove_from_ui(self):
        for sprite in self.visuals:
            core_object.main_ui.remove(sprite, True)

peformed_runtime_imports : bool = False
def runtime_imports():
    global peformed_runtime_imports, core_object
    from framework.core.core import core_object
    peformed_runtime_imports = True