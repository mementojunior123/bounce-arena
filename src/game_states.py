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
    SIMULATION_STEP_COUNT : int = 1
    def __init__(self, game_object : 'Game'):
        self.game = game_object
        self.simulation_space : pymunk.Space = pymunk.Space()
        self.simulation_space.gravity = (0, 10)

        new_body, shapes, new_image = src.sprites.physics_object.create_test_ball(20, (480, 270), "Blue")        
        self.simulation_space.add(new_body, *shapes)
        PlayerPhysicsObject.spawn(new_body, new_image)

        ground_body, shapes, ground_image = src.sprites.physics_object.create_test_ground(960, 20, (480, 500), "Black")    
        self.simulation_space.add(ground_body, *shapes)
        BasicPhysicsObject.spawn(ground_body, ground_image)

        roof_body, shapes, roof_image = src.sprites.physics_object.create_test_ground(960, 20, (480, -20), "Black")
        self.simulation_space.add(roof_body, *shapes)
        BasicPhysicsObject.spawn(roof_body, roof_image)

        for x in (0, 960):
            wall_body, shapes, wall_image = src.sprites.physics_object.create_test_ground(20, 540, (x, 270), "Black")
            self.simulation_space.add(wall_body, *shapes)
            BasicPhysicsObject.spawn(wall_body, wall_image)
            
        src.sprites.physics_object.make_connections()

    @staticmethod
    def on_collision(arbiter : pymunk.Arbiter, sim_space : pymunk.Space, data : Any):
        pass

    def main_logic(self, delta : float):
        for sprite in BasePhysicsObject.active_elements:
            sprite.before_sim(delta)
        step_count : int = round(self.SIMULATION_STEP_COUNT * delta * 2)
        for i in range(step_count):
            for sprite in BasePhysicsObject.active_elements:
                sprite.before_step(delta, i, step_count)

            self.simulation_space.step(delta / 5 / step_count)

            for sprite in BasePhysicsObject.active_elements:
                sprite.after_step(delta, i, step_count)

        for sprite in BasePhysicsObject.active_elements:
            sprite.post_sim(delta)
        
        Sprite.update_all_sprites(delta)
        Sprite.update_all_registered_classes(delta)
    
    def cleanup(self):
        src.sprites.physics_object.remove_connections()


class NetworkTestGameState(NormalGameState):
    def __init__(self, game_object : 'Game'):
        self.game = game_object
        self.player : TestPlayer = TestPlayer.spawn(pygame.Vector2(random.randint(0, 960),random.randint(0, 540)))
        self.particle_effect : ParticleEffect = ParticleEffect.load_effect('test2', persistance=False)
        self.particle_effect.play(pygame.Vector2(480, 270), time_source=self.game.game_timer.get_time)
        src.sprites.test_player.make_connections()
        self.test_pattern : NetworkTestPattern = NetworkTestPattern()
        host_arg : str = "true" if pygame.key.get_pressed()[pygame.K_f] else "false"
        core_object.log("Hosting : ", host_arg.capitalize())
        peer_id : int = "fsafgasg12345abcsss5"
        self.network_key : str = "tmp_" + peer_id + host_arg
        core_object.networker.create_peer(peer_id, host_arg, self.network_key)
        for event_type in [core_object.networker.NETWORK_CLOSE_EVENT, core_object.networker.NETWORK_CONNECTION_EVENT, core_object.networker.NETWORK_DISCONNECT_EVENT,
                           core_object.networker.NETWORK_ERROR_EVENT, core_object.networker.NETWORK_RECEIVE_EVENT]:
            core_object.event_manager.bind(event_type, self.network_event_handler)
        self.test_pattern.initialize(self.game.game_timer.get_time, self.network_key)
        

    def main_logic(self, delta : float):
        super().main_logic(delta)
        self.test_pattern.process_frame()
    
    def cleanup(self):
        src.sprites.test_player.remove_connections()
        for event_type in [core_object.networker.NETWORK_CLOSE_EVENT, core_object.networker.NETWORK_CONNECTION_EVENT, core_object.networker.NETWORK_DISCONNECT_EVENT,
                           core_object.networker.NETWORK_ERROR_EVENT, core_object.networker.NETWORK_RECEIVE_EVENT]:
            core_object.event_manager.unbind(event_type, self.network_event_handler)
        core_object.networker.destroy_peer(self.network_key)
        
    
    def network_event_handler(self, event : pygame.Event):
        if event.type == core_object.networker.NETWORK_RECEIVE_EVENT:
            self.game.alert_player(f"Received data {event.data}")
            core_object.log(f"pygame : Received data {event.data}")
        elif event.type == core_object.networker.NETWORK_ERROR_EVENT:
            self.game.alert_player(f"Network error occured : {event.info}")
            core_object.log(f"pygame : Network error occured : {event.info}")
        elif event.type == core_object.networker.NETWORK_CLOSE_EVENT:
            self.game.alert_player("Network connection closed")
            core_object.log(f"pygame : Network connection closed")
        elif event.type == core_object.networker.NETWORK_DISCONNECT_EVENT:
            self.game.alert_player("Network disconnected")
            core_object.log("pygame : Network disconnected")
        elif event.type == core_object.networker.NETWORK_CONNECTION_EVENT:
            self.game.alert_player("Network connected")
            core_object.log("pygame : Network connected")

class NetworkTestPattern(CoroutineScript):
    def initialize(self, time_source : TimeSource, net_key : str):
        return super().initialize(time_source, net_key)
    
    def type_hints(self):
        self.coro_attributes = ['timer', 'cooldown', 'curr_angle']
        self.timer : Timer
        self.cooldown : Timer
        self.curr_angle : float
    
    @staticmethod
    def corou(time_source : TimeSource, net_key : str) -> Generator[None, None, str]:
        textsprite_font : pygame.Font = core_object.menu.font_50

        new_textsprite : TextSprite = TextSprite((480, 10), "midtop", None, "Waiting...", "Progress",
        text_settings=(textsprite_font, "White", False), text_stroke_settings=("Black", 2))
        core_object.main_ui.add(new_textsprite)
        timer : Timer = Timer(0.5, time_source)
        percentage : float = 0
        yield
        while not timer.isover():
            yield
        timer.set_duration(3, restart=True)
        while not timer.isover():
            percentage = pygame.math.lerp(0, 100, timer.get_time() / timer.duration)
            zoom : float = pygame.math.lerp(1, 0.25, interpolation.quad_ease_out(timer.get_time() / timer.duration))
            angle : float = pygame.math.lerp(0, 25, sin(timer.get_time() / timer.duration * 2 * pi * 10), False)
            core_object.game.main_camera.zoom = zoom
            #core_object.game.main_camera.rotation = angle
            new_textsprite.text = f"{percentage:.2f}%"
            yield
        new_textsprite.text = f"{100}% - Done!"
        timer.set_duration(1, restart=True)
        core_object.networker.send_network_message("DONE!!!", net_key)
        while not timer.isover():
            yield
        core_object.main_ui.remove(new_textsprite)
        return 'Done'

class TestGameState(NormalGameState):
    def __init__(self, game_object : 'Game'):
        self.game = game_object
        self.player : TestPlayer = TestPlayer.spawn(pygame.Vector2(random.randint(0, 960),random.randint(0, 540)))
        self.particle_effect : ParticleEffect = ParticleEffect.load_effect('test2', persistance=False)
        self.particle_effect.play(pygame.Vector2(480, 270), time_source=self.game.game_timer.get_time)
        src.sprites.test_player.make_connections()
        self.test_pattern : TestPattern = TestPattern()
        self.test_pattern.initialize(self.game.game_timer.get_time)
        core_object.bg_manager.play('test_music', 1.0)

    def main_logic(self, delta : float):
        super().main_logic(delta)
        self.test_pattern.process_frame()
    
    def cleanup(self):
        src.sprites.test_player.remove_connections()
        core_object.bg_manager.stop_all_music()
        core_object.bg_manager.play_sfx('test_sfx', 1.0)

class TestPattern(CoroutineScript):
    def initialize(self, time_source : TimeSource):
        return super().initialize(time_source)
    
    def type_hints(self):
        self.coro_attributes = ['timer', 'cooldown', 'curr_angle']
        self.timer : Timer
        self.cooldown : Timer
        self.curr_angle : float
    
    @staticmethod
    def corou(time_source : TimeSource) -> Generator[None, None, str]:
        textsprite_font : pygame.Font = core_object.menu.font_50

        new_textsprite : TextSprite = TextSprite((480, 10), "midtop", None, "Waiting...", "Progress",
        text_settings=(textsprite_font, "White", False), text_stroke_settings=("Black", 2))
        core_object.main_ui.add(new_textsprite)
        timer : Timer = Timer(0.5, time_source)
        percentage : float = 0
        yield
        while not timer.isover():
            yield
        timer.set_duration(3, restart=True)
        while not timer.isover():
            percentage = pygame.math.lerp(0, 100, timer.get_time() / timer.duration)
            zoom : float = pygame.math.lerp(1, 0.25, interpolation.quad_ease_out(timer.get_time() / timer.duration))
            angle : float = pygame.math.lerp(0, 25, sin(timer.get_time() / timer.duration * 2 * pi * 10), False)
            core_object.game.main_camera.zoom = zoom
            #core_object.game.main_camera.rotation = angle
            new_textsprite.text = f"{percentage:.2f}%"
            yield
        new_textsprite.text = f"{100}% - Done!"
        timer.set_duration(1, restart=True)
        while not timer.isover():
            yield
        core_object.main_ui.remove(new_textsprite)
        return 'Done'

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


class GameStates:
    NormalGameState = NormalGameState
    TestGameState = TestGameState
    NetworkTestGameState = NetworkTestGameState
    PausedGameState = PausedGameState
    PhysicsTestGameState = PhysicsTestGameState


def initialise_game(game_object : 'Game', event : pygame.Event):
    if event.mode == 'test' and (False):
        game_object.state = game_object.STATES.NetworkTestGameState(game_object)
    else:
        game_object.state = game_object.STATES.PhysicsTestGameState(game_object)
