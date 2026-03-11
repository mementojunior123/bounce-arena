import pygame
from framework.utils.ui.ui_sprite import UiSprite
from framework.utils.ui.textsprite import TextSprite
from framework.utils.helpers import make_circle

layout : dict[str, tuple[float, float]] = {
    "1" : (0, 0), "2" : (0.1, 0), "3" : (0.2, 0), "4" : (0.3, 0), "5" : (0.4, 0), "6" : (0.5, 0), "7" : (0.6, 0), "8" : (0.7, 0), "9" : (0.8, 0), "0" : (0.9, 0),

    "q" : (0.05, 0.25), "w" : (0.15, 0.25), "e" : (0.25, 0.25), "r" : (0.35, 0.25), "t" : (0.45, 0.25), "y" : (0.55, 0.25),
        "u" : (0.65, 0.25), "i" : (0.75, 0.25), "o" : (0.85, 0.25), "p" : (0.95, 0.25),

    "a" : (0.08, 0.50), "s" : (0.18, 0.50), "d" : (0.28, 0.50), "f" : (0.38, 0.50), "g" : (0.48, 0.50), 
        "h" : (0.58, 0.50), "j" : (0.68, 0.50), "k" : (0.78, 0.50), "l" : (0.88, 0.50), "DEL" : (0.98, 0.50),
    
    "z" : (0.12, 0.75), "x" : (0.22, 0.75), "c" : (0.32, 0.75), "v" : (0.42, 0.75), "b" : (0.52, 0.75), "n" : (0.62, 0.75), "m" : (0.72, 0.75), "ENTER" : (0.88, 0.75)
}

class MobileKeyboard:
    def __init__(self, size : tuple[float, float], center : pygame.Vector2, font : pygame.Font|int = 60, emulate_touch : bool = False):
        if not peformed_runtime_imports: runtime_imports()

        if isinstance(font, int):
            if font in font_dict:
                font = font_dict[font]
            else:
                font_dict[font] = pygame.Font("assets/fonts/Pixeltype.ttf", font)
                font = font_dict[font]

        self.characters : list[TextSprite] = []
        for char in layout:
            rel_x, rel_y = layout[char]
            rel_x -= 0.5
            rel_y -= 0.5
            abs_pos = center + (rel_x * size[0], rel_y * size[1])
            new_sprite : TextSprite = TextSprite(pygame.Vector2(abs_pos), "center", -1, char, None, text_settings=(font, "White", False), colorkey=(0, 255, 0))
            self.characters.append(new_sprite)
        self.emulate_touch : bool = emulate_touch
            

    @property
    def visuals(self) -> list[UiSprite]:
        return self.characters
    
    def when_clicked(self, x : float, y : float):
        hits : list[TextSprite] = []
        for char in self.characters:
            if char.rect.scale_by(4).collidepoint(x, y):
                hits.append(char)
        if not hits: return
        hits.sort(key = lambda s : (pygame.Vector2(s.rect.center) - (x, y)).magnitude())
        self.on_key_clicked(hits[0].text)
    
    @staticmethod
    def on_key_clicked(key : str):
        print(key, "hit")

    
    def process_touch_event(self, event : pygame.Event):
        if event.type == pygame.FINGERDOWN:
            display_size = core_object.main_display.get_size()
            x : float = event.x * display_size[0]
            y : float = event.y * display_size[1]
            self.when_clicked(x, y)
    
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
            x, y = event.pos
            self.when_clicked(x, y)
    
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
    global peformed_runtime_imports, core_object, font_dict
    from framework.core.core import core_object
    peformed_runtime_imports = True
    font_dict = {
            40 : core_object.game.font_40,
            50 : core_object.game.font_50,
            60 : core_object.game.font_60,
            70 : core_object.game.font_70,
        }