import pygame
from typing import Any, Generator
from math import floor, sin, pi
from random import shuffle, choice
import random
import framework.game.coroutine_scripts
from framework.game.coroutine_scripts import CoroutineScript
import framework.utils.tween_module as TweenModule
from framework.utils.ui.ui_sprite import UiSprite
from framework.utils.ui.textbox import TextBox
from framework.utils.ui.textsprite import TextSprite
from framework.utils.ui.base_ui_elements import BaseUiElements
import framework.utils.interpolation as interpolation
from framework.utils.my_timer import Timer, TimeSource
from framework.game.sprite import Sprite
from framework.utils.helpers import average, random_float
from framework.utils.ui.brightness_overlay import BrightnessOverlay
from framework.utils.particle_effects import ParticleEffect

import pymunk

class GameState:
    def __init__(self, game_object : 'Game'):
        self.game = game_object

    def main_logic(self, delta : float):
        pass

    def pause(self):
        pass

    def unpause(self):
        pass

    def handle_key_event(self, event : pygame.Event):
        pass

    def handle_mouse_event(self, event : pygame.Event):
        pass

    def cleanup(self):
        pass

class NormalGameState(GameState):
    def main_logic(self, delta : float):
        Sprite.update_all_sprites(delta)
        Sprite.update_all_registered_classes(delta)

    def pause(self):
        if not self.game.active: return
        self.game.game_timer.pause()
        window_size = core_object.main_display.get_size()
        pause_ui1 = BrightnessOverlay(-60, pygame.Rect(0,0, *window_size), 0, 'pause_overlay', zindex=999)
        pause_ui2 = TextSprite(pygame.Vector2(window_size[0] // 2, window_size[1] // 2), 'center', 0, 'Paused', 'pause_text', None, None, 1000,
                               (self.game.font_70, 'White', False), ('Black', 2), colorkey=(0, 255, 0))
        core_object.main_ui.add(pause_ui1)
        core_object.main_ui.add(pause_ui2)
        self.game.state = PausedGameState(self.game, self)
    
    def handle_key_event(self, event : pygame.Event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                self.pause()

class PhysicsTestGameState(NormalGameState):
    SIMULATION_STEP_COUNT : int = 5
    def __init__(self, game_object : 'Game'):
        self.game = game_object
        self.simulation_space : pymunk.Space = pymunk.Space()
        self.simulation_space.gravity = (0, 7.5)

        new_body, shapes, new_image = src.level_geometry.create_dynamic_ball(20, (480, 270), "Blue")        
        self.simulation_space.add(new_body, *shapes)
        self.player : PlayerPhysicsObject = PlayerPhysicsObject.spawn(new_body, new_image)

        for level_geomerty in src.level_geometry.test_level_geometry:
            src.level_geometry.create_level_geometry_object(level_geomerty, self.simulation_space)

        src.sprites.physics_object.make_connections()

    @staticmethod
    def on_collision(arbiter : pymunk.Arbiter, sim_space : pymunk.Space, data : Any):
        pass

    def main_logic(self, delta : float):
        TIMESCALE_FACTOR : float = 0.2
        for sprite in BasePhysicsObject.active_elements:
            sprite.before_sim(delta)
        step_count : int = max(round(self.SIMULATION_STEP_COUNT * delta), 1)
        for i in range(step_count):
            for sprite in BasePhysicsObject.active_elements:
                sprite.before_step(delta, i, step_count)
            self.simulation_space.step((delta * TIMESCALE_FACTOR) / step_count)

            for sprite in BasePhysicsObject.active_elements:
                sprite.after_step(delta, i, step_count)

        for sprite in BasePhysicsObject.active_elements:
            sprite.post_sim(delta)
        
        Sprite.update_all_sprites(delta)
        Sprite.update_all_registered_classes(delta)

        if not pygame.Rect(-200, -200, 960 + 400, 540 + 400).collidepoint(self.player.position):
            self.switch_to_gameover("You lose!")

    def switch_to_gameover(self, message : str):
        self.game.state = GameOverState(self.game, self, message)
    
    def cleanup(self):
        src.sprites.physics_object.remove_connections()

class GameOverState(GameState):
    def __init__(self, game_object : 'Game', previous : GameState, message : str = "You lose!"):
        self.game = game_object
        self.prev = previous
        self.game.alert_player(message)
        self.timer = Timer(3, self.game.game_timer.get_time)
    
    def main_logic(self, delta):
        if self.timer.isover():
            core_object.end_game()
    
    def cleanup(self):
        self.prev.cleanup()

class PausedGameState(GameState):
    def __init__(self, game_object : 'Game', previous : GameState):
        super().__init__(game_object)
        self.previous_state = previous
    
    def unpause(self):
        if not self.game.active: return
        self.game.game_timer.unpause()
        pause_ui1 = core_object.main_ui.get_sprite('pause_overlay')
        pause_ui2 = core_object.main_ui.get_sprite('pause_text')
        if pause_ui1: core_object.main_ui.remove(pause_ui1)
        if pause_ui2: core_object.main_ui.remove(pause_ui2)
        self.game.state = self.previous_state

    def handle_key_event(self, event : pygame.Event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                self.unpause()

def runtime_imports():
    global Game
    from framework.game.game_module import Game
    global core_object
    from framework.core.core import core_object

    #runtime imports for game classes
    global src, TestPlayer      
    import src.sprites.test_player
    from src.sprites.test_player import TestPlayer

    global BasicPhysicsObject, BasePhysicsObject, PlayerPhysicsObject
    import src.sprites.physics_object
    from src.sprites.physics_object import BasicPhysicsObject, BasePhysicsObject, PlayerPhysicsObject

    import src.level_geometry


class GameStates:
    NormalGameState = NormalGameState
    PausedGameState = PausedGameState
    PhysicsTestGameState = PhysicsTestGameState


def initialise_game(game_object : 'Game', event : pygame.Event):
    game_object.state = game_object.STATES.PhysicsTestGameState(game_object)
