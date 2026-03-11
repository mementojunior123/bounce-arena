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

    def player_team1_constructor(self, body : pymunk.Body, image : pygame.Surface, cog : pygame.Vector2|None = None) -> "GenericPlayerPhysicsObject":
        if self.player_count == 1:
            return GenericPlayerPhysicsObject.spawn(body, image, cog, (ControlSchemes.MOBILE if core_object.used_touch else ControlSchemes.BOTH_SIDES), 
                                                    Teams.TEAM_1, self.main_collision_handler, (700, 10), "Blue")
        else:
            return GenericPlayerPhysicsObject.spawn(body, image, cog, (ControlSchemes.MOBILE if core_object.used_touch else ControlSchemes.LEFT_SIDE),
                                                     Teams.TEAM_1, self.main_collision_handler, (700, 10), "Blue")
    
    def player_team2_constructor(self, body : pymunk.Body, image : pygame.Surface, cog : pygame.Vector2|None = None) -> "GenericPlayerPhysicsObject":
        if self.player_count == 1:
            return GenericPlayerPhysicsObject.spawn(body, image, cog, ControlSchemes.AI, Teams.TEAM_2, self.main_collision_handler, (950, 10), "Green")
        else:
            return GenericPlayerPhysicsObject.spawn(body, image, cog, ControlSchemes.RIGHT_SIDE, Teams.TEAM_2, self.main_collision_handler, (950, 10), "Green")
    

    def __init__(self, game_object : 'Game', player_count : int = 1):
        self.game = game_object
        self.simulation_space : pymunk.Space = pymunk.Space()
        self.simulation_space.gravity = (0, 7.5)
        self.main_collision_handler : CentralCollisionHandler = CentralCollisionHandler(self.simulation_space)
        self.player_count : int = player_count
        if player_count > 1 and core_object.used_touch:
            self.game.alert_player("2 players is not properly supported on mobile!")

        player_ball_geo : LevelGeometry = {"object_type" : "dynamic_ball", "pos" : [480, 270], "color" : "Blue", "radius" : 20, "bounciness" : 0.9,
                                           "collision_type" : CollisionTypes.TEAM1_BALL, "collision_category" : [CollisionTypes.TEAM1_BALL], 
                                           "collision_mask" : [CollisionTypes.TEAM2_BALL, CollisionTypes.STATIC_GEOMETRY, CollisionTypes.TEAM2_PROJECTILE]}

        self.player : GenericPlayerPhysicsObject = src.level_geometry.make_level_geometry_object(player_ball_geo, self.simulation_space, self.player_team1_constructor)

        enemy_ball_geo : LevelGeometry = {"object_type" : "dynamic_ball", "pos" : [600, 60], "color" : "Green", "colorkey" : (255, 255, 0), "radius" : 20, "bounciness" : 0.9,
                                          "collision_type" : CollisionTypes.TEAM2_BALL, "collision_category" : [CollisionTypes.TEAM2_BALL], 
                                          "collision_mask" : [CollisionTypes.TEAM1_BALL, CollisionTypes.STATIC_GEOMETRY, CollisionTypes.TEAM1_PROJECTILE]}
        self.enemy_ball : GenericPlayerPhysicsObject = src.level_geometry.make_level_geometry_object(enemy_ball_geo, self.simulation_space, self.player_team2_constructor)

        for level_geomerty in src.level_geometry.test_level_geometry:
            src.level_geometry.make_level_geometry_object(level_geomerty, self.simulation_space)

        src.sprites.player.make_connections()

        self.steps_taken : int = 0

    @staticmethod
    def on_collision(arbiter : pymunk.Arbiter, sim_space : pymunk.Space, data : Any):
        pass

    def main_logic(self, delta : float):
        target_step_count : int = (self.game.game_timer.get_time() / (1 / 60) * self.SIMULATION_STEP_COUNT)
        TIMESCALE_FACTOR : float = 0.2
        for sprite in BasePhysicsObject.active_elements:
            sprite.before_sim(delta)
        step_count : int = min(max(round(target_step_count - self.steps_taken), 1), 100)
        self.steps_taken += step_count
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
        margin : int = 50
        inbound_rect : pygame.Rect = pygame.Rect(-margin, -margin, 960 + 2 * margin, 540 + 2 * margin)
        if not inbound_rect.collidepoint(self.player.position):
            self.switch_to_gameover("You lose!")
        elif not inbound_rect.collidepoint(self.enemy_ball.position):
            self.switch_to_gameover("You win!")

    def switch_to_gameover(self, message : str):
        self.game.state = GameOverState(self.game, self, message)
    
    def cleanup(self):
        src.sprites.player.remove_connections()

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

class NetworkEnterCodeGameState(GameState):
    def __init__(self, game_object : 'Game'):
        self.game = game_object
        self.textsprite1 = TextSprite(pygame.Vector2(480, 20), "midtop", 0, "Roomcode:", "roomcode_title", 
                                      text_settings=(Game.font_50, "White", False), text_stroke_settings=("Black", 2))
        self.text_entry = TextSprite(pygame.Vector2(480, 70), "midtop", 0, "", text_settings=(Game.font_40, "White", False), text_stroke_settings=("Black", 2))
        self.textsprite2 = TextSprite(pygame.Vector2(480, 430), "midtop", 0, "Backspace to erase\nEnter to confirm\nEscape to exit", "misc_text", 
                                      text_settings=(Game.font_40, "Black", False))
        self.flashing_text = TextSprite(pygame.Vector2(480, 120), "midtop", 0, "_", text_settings=(Game.font_40, "White", False), text_stroke_settings=("Black", 2))
        self.flash_timer : Timer = Timer(1, self.game.game_timer.get_time)
        window_size = core_object.main_display.get_size()
        self.back_button : UiSprite = BaseUiElements.new_button('BlueButton', 'Back', 1, 'topright', 
                                            (window_size[0] - 15, 15), (0.5, 1.4), 
                                    {'name' : 'quit_button'}, (self.game.font_40, 'Black', False))
        if core_object.used_touch:
            self.mobile_keyboard : MobileKeyboard = MobileKeyboard((900, 300), pygame.Vector2(480, 400), 60, False)
            self.mobile_keyboard.add_to_ui()
            self.mobile_keyboard.make_connections()
            self.mobile_keyboard.on_key_clicked = self.handle_mobile_keyboard_click
            self.textsprite2.visible = False
        else:
            self.mobile_keyboard = None
        core_object.main_ui.add_multiple([self.textsprite1, self.text_entry, self.textsprite2, self.flashing_text, self.back_button])
        pygame.key.start_text_input()
        core_object.event_manager.bind(pygame.TEXTEDITING, self.handle_textinput_event)
        core_object.event_manager.bind(pygame.TEXTINPUT, self.handle_textinput_event)
    
    def main_logic(self, delta):
        if int(self.flash_timer.get_time() // 0.5) % 2 == 0:
            self.flashing_text.visible = True
        else:
            self.flashing_text.visible = False
        if self.flash_timer.isover(): self.flash_timer.restart()
    
    def when_backspace(self):
        if self.text_entry.text: 
            self.text_entry.text = self.text_entry.text[:-1]
        if not self.text_entry.text:
            self.text_entry.visible = False
    
    def when_enter(self):
        room_code : str = self.text_entry.text
        if not NetworkWaitingGameState.validate_roomcode(room_code):
            self.game.alert_player("This code is not valid!")
        else:
            self.tranisition_to_wait(room_code)
    
    def when_text_typed(self, text : str):
        self.text_entry.text += text.lower()
        self.text_entry.visible = True

    def handle_key_event(self, event : pygame.Event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                core_object.end_game()
            elif event.key == pygame.K_BACKSPACE:
                self.when_backspace()
            elif event.key == pygame.K_RETURN:
                self.when_enter()
    
    def handle_textinput_event(self, event : pygame.Event):
        if event.type == pygame.TEXTEDITING:
            pass
        elif event.type == pygame.TEXTINPUT:
            self.when_text_typed(event.text)

    def handle_mouse_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.back_button.rect.collidepoint(event.pos):
                core_object.end_game()
    
    def handle_mobile_keyboard_click(self, key : str):
        print('Tapped', key)
        if key.lower() == "enter":
            self.when_enter()
        elif key.lower() == "del":
            self.when_backspace()
        else:
            self.when_text_typed(key)
        
    
    def tranisition_to_wait(self, room_code : str):
        core_object.event_manager.bind(pygame.TEXTEDITING, self.handle_textinput_event)
        core_object.event_manager.bind(pygame.TEXTINPUT, self.handle_textinput_event)
        pygame.key.stop_text_input()
        for sprite in (self.textsprite1, self.text_entry, self.textsprite2, self.flashing_text, self.back_button):
            core_object.main_ui.remove(sprite)
        self.mobile_keyboard.remove_from_ui()
        self.mobile_keyboard.remove_connections()

        self.game.state = NetworkWaitingGameState(self.game, False, "tmp_" + room_code + "false", NetworkWaitingGameState.PREFIX + room_code)
    
    def cleanup(self):
        core_object.event_manager.bind(pygame.TEXTEDITING, self.handle_textinput_event)
        core_object.event_manager.bind(pygame.TEXTINPUT, self.handle_textinput_event)
        self.mobile_keyboard.remove_connections()
        pygame.key.stop_text_input()
            
class NetworkWaitingGameState(GameState):
    PREFIX = "BOUNCE_ARENA_TEST"
    VALID_CHARACTERS : str = "abcdefghijklmnopqrstuvwxyz1234567890"
    CODE_LENTGH : int = 6
    @staticmethod
    def generate_roomcode() -> str:
        return "".join(random.choices(NetworkWaitingGameState.VALID_CHARACTERS, k=NetworkWaitingGameState.CODE_LENTGH))
    
    @staticmethod
    def validate_roomcode(code : str) -> bool:
        if len(code) != NetworkWaitingGameState.CODE_LENTGH:
            return False
        if any(c not in NetworkWaitingGameState.VALID_CHARACTERS for c in code):
            return False
        return True
    
    def __init__(self, game_object : 'Game', is_host : bool, network_key : str, peer_id : str):
        self.game = game_object
        self.is_host : bool = is_host
        host_arg : str = "true" if self.is_host else "false"
        core_object.log("Hosting :", host_arg.capitalize())
        self.peer_id : str = peer_id
        self.network_key : str = network_key
        core_object.networker.create_peer(self.peer_id, host_arg, self.network_key, debug_level=1)
        for event_type in [core_object.networker.NETWORK_CLOSE_EVENT, core_object.networker.NETWORK_CONNECTION_EVENT, core_object.networker.NETWORK_DISCONNECT_EVENT,
                           core_object.networker.NETWORK_ERROR_EVENT, core_object.networker.NETWORK_RECEIVE_EVENT]:
            core_object.event_manager.bind(event_type, self.network_event_handler)
        self.ui_message : TextSprite = TextSprite(pygame.Vector2(480, 10), "midtop", 0, 
                        f"Waiting for connection...\nHosting: {host_arg.capitalize()}\nRoom code: {self.peer_id.removeprefix(NetworkWaitingGameState.PREFIX)}",
                        "waiting_message", text_settings=(self.game.font_40, "White", False),
                        text_stroke_settings=("Black", 2), colorkey=(0, 255, 0))
        core_object.main_ui.add(self.ui_message)
        window_size = core_object.main_display.get_size()
        self.back_button : UiSprite = BaseUiElements.new_button('BlueButton', 'Back', 1, 'topright', 
                                            (window_size[0] - 15, 15), (0.5, 1.4), 
                                    {'name' : 'quit_button'}, (self.game.font_40, 'Black', False))
        core_object.main_ui.add(self.back_button)
        

    def main_logic(self, delta : float):
        pass

    def transition_to_play(self):
        for event_type in [core_object.networker.NETWORK_CLOSE_EVENT, core_object.networker.NETWORK_CONNECTION_EVENT, core_object.networker.NETWORK_DISCONNECT_EVENT,
                           core_object.networker.NETWORK_ERROR_EVENT, core_object.networker.NETWORK_RECEIVE_EVENT]:
            core_object.event_manager.unbind(event_type, self.network_event_handler)
        core_object.main_ui.remove(self.ui_message)
        core_object.main_ui.remove(self.back_button)
        core_object.networker.send_network_message("hello", self.network_key)
        self.game.state = PhysicsNetworkedTestGameState(self.game, self.network_key, self.peer_id, self.is_host)
    
    def cleanup(self):
        for event_type in [core_object.networker.NETWORK_CLOSE_EVENT, core_object.networker.NETWORK_CONNECTION_EVENT, core_object.networker.NETWORK_DISCONNECT_EVENT,
                           core_object.networker.NETWORK_ERROR_EVENT, core_object.networker.NETWORK_RECEIVE_EVENT]:
            core_object.event_manager.unbind(event_type, self.network_event_handler)
        core_object.networker.destroy_peer(self.network_key)
        
    
    def network_event_handler(self, event : pygame.Event):
        if event.type == core_object.networker.NETWORK_RECEIVE_EVENT:
            self.game.alert_player(f"Received data {event.data}")
            core_object.log(f"pygame : Received data {event.data}")
            if event.data == "hello":
                self.transition_to_play()
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
            if not self.is_host:
                self.transition_to_play()
        
    def handle_key_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                core_object.end_game()
    
    def handle_mouse_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.back_button.rect.collidepoint(event.pos):
                core_object.end_game()

class Network2PlayerTestGameState(NormalGameState):
    def __init__(self, game_object : 'Game', network_key : str, peer_id : str, is_host : bool):
        self.game = game_object
        self.ping_timer : Timer = Timer(1, core_object.game.game_timer.get_time)
        host_pos, client_pos = pygame.Vector2(200, 100), pygame.Vector2(760, 440)
        host_color, client_color = "Red", "Blue"
        
        this_pos, other_pos = (host_pos, client_pos) if is_host else (client_pos, host_pos)
        this_color, other_color = (host_color, client_color) if is_host else (client_color, host_color)

        self.player : NetworkTestPlayer = NetworkTestPlayer.spawn(this_pos, is_host, this_color)
        self.other_player : NetworkSyncTestPlayer = NetworkSyncTestPlayer.spawn(other_pos, not is_host, other_color)
        core_object.log("Hosting:", str(is_host))
        src.sprites.test_player.make_connections()
        self.is_host : bool = is_host
        self.network_key : str = network_key
        self.peer_id : str = peer_id
        self.recent_messages : list[str] = []
        for event_type in [core_object.networker.NETWORK_CLOSE_EVENT, core_object.networker.NETWORK_CONNECTION_EVENT, core_object.networker.NETWORK_DISCONNECT_EVENT,
                           core_object.networker.NETWORK_ERROR_EVENT, core_object.networker.NETWORK_RECEIVE_EVENT]:
            core_object.event_manager.bind(event_type, self.network_event_handler)
        

    def main_logic(self, delta : float):
        if self.ping_timer.isover():
            self.ping_timer.restart()
            core_object.networker.send_network_message("!!!ping!!!", self.network_key)

        for message in self.recent_messages:
            if self.is_host:
                self.parse_and_react_as_host(message)
            else:
                self.parse_and_react_as_client(message)
        self.recent_messages.clear()

        Sprite.update_all_sprites(delta)
        Sprite.update_all_registered_classes(delta)
        if self.is_host:
            core_object.networker.send_network_message(
                  f"{self.player.x};{self.player.y};{self.player.angle};" 
                + f"{self.other_player.x};{self.other_player.y};{self.other_player.angle}", self.network_key
            )
        else:
            if self.player.attempted_move or self.player.attempted_rotate:
                core_object.networker.send_network_message(
                    f"{self.player.attempted_move.x};{self.player.attempted_move.y};{self.player.attempted_rotate};{delta}", self.network_key
                )
        
    
    def parse_and_react_as_host(self, data : str):
        args = data.split(";")
        if not (len(args) == 4):
            return
        self.other_player.sync_other_is_client(pygame.Vector2(float(args[0]), float(args[1])), float(args[2]), float(args[3]))
    
    def parse_and_react_as_client(self, data : str):
        args = data.split(";")
        if not (len(args) == 6):
            return
        self.other_player.sync_other_is_host(pygame.Vector2(float(args[0]), float(args[1])), float(args[2]))
        sync_position : pygame.Vector2 = pygame.Vector2(float(args[3]), float(args[4]))
        sync_angle : float = float(args[5])
        if (self.player.position - sync_position).magnitude() > 2:
            self.player.position = sync_position
        if abs(self.player.angle - sync_angle) > 2:
            self.player.angle = sync_angle
    
    def cleanup(self):
        src.sprites.test_player.remove_connections()
        for event_type in [core_object.networker.NETWORK_CLOSE_EVENT, core_object.networker.NETWORK_CONNECTION_EVENT, core_object.networker.NETWORK_DISCONNECT_EVENT,
                           core_object.networker.NETWORK_ERROR_EVENT, core_object.networker.NETWORK_RECEIVE_EVENT]:
            core_object.event_manager.unbind(event_type, self.network_event_handler)
        core_object.networker.destroy_peer(self.network_key)
        
    
    def network_event_handler(self, event : pygame.Event):
        if event.type == core_object.networker.NETWORK_RECEIVE_EVENT:
            ...
            #self.game.alert_player(f"Received data {event.data}")
            #core_object.log(f"pygame : Received data {event.data}")
            self.recent_messages.append(event.data)
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
    
    def handle_key_event(self, event : pygame.Event):
        pass

class PhysicsNetworkedTestGameState(NormalGameState):

    def player_team1_constructor(self, body : pymunk.Body, image : pygame.Surface, cog : pygame.Vector2|None = None) -> "GenericPlayerPhysicsObject":
        if self.is_host:
            return GenericPlayerPhysicsObject.spawn(body, image, cog, (ControlSchemes.MOBILE if core_object.used_touch else ControlSchemes.BOTH_SIDES),
                                                     Teams.TEAM_1, self.main_collision_handler, (700, 10), "Blue")
        else:
            return GenericPlayerPhysicsObject.spawn(body, image, cog, ControlSchemes.NETWORK, Teams.TEAM_1, self.main_collision_handler, (700, 10), "Blue")
    
    def player_team2_constructor(self, body : pymunk.Body, image : pygame.Surface, cog : pygame.Vector2|None = None) -> "GenericPlayerPhysicsObject":
        if self.is_host:
            return GenericPlayerPhysicsObject.spawn(body, image, cog, ControlSchemes.NETWORK, Teams.TEAM_2, self.main_collision_handler, (950, 10), "Green")
        else:
            return GenericPlayerPhysicsObject.spawn(body, image, cog, (ControlSchemes.MOBILE if core_object.used_touch else ControlSchemes.BOTH_SIDES),
                                                     Teams.TEAM_2, self.main_collision_handler, (950, 10), "Green")
    
    SIMULATION_STEP_COUNT : int = 5
    def __init__(self, game_object : 'Game', network_key : str, peer_id : str, is_host : bool):
        self.recent_messages : list[str] = []
        self.ping_timer : Timer = Timer(1, core_object.game.game_timer.get_time)
        self.response_timer : Timer = Timer(5, core_object.game.game_timer.get_time)
        self.is_host : bool = is_host
        self.network_key : str = network_key
        self.peer_id : str = peer_id

        self.game = game_object
        self.simulation_space : pymunk.Space = pymunk.Space()
        self.simulation_space.gravity = (0, 7.5)
        self.main_collision_handler : CentralCollisionHandler = CentralCollisionHandler(self.simulation_space)

        player_ball_geo : LevelGeometry = {"object_type" : "dynamic_ball", "pos" : [480, 270], "color" : "Blue", "radius" : 20, "bounciness" : 0.9,
                                           "collision_type" : CollisionTypes.TEAM1_BALL, "collision_category" : [CollisionTypes.TEAM1_BALL], 
                                           "collision_mask" : [CollisionTypes.TEAM2_BALL, CollisionTypes.STATIC_GEOMETRY, CollisionTypes.TEAM2_PROJECTILE]}
        self.host : GenericPlayerPhysicsObject = src.level_geometry.make_level_geometry_object(player_ball_geo, self.simulation_space, self.player_team1_constructor)

        enemy_ball_geo : LevelGeometry = {"object_type" : "dynamic_ball", "pos" : [600, 60], "color" : "Green", "colorkey" : (255, 255, 0), "radius" : 20, "bounciness" : 0.9,
                                          "collision_type" : CollisionTypes.TEAM2_BALL, "collision_category" : [CollisionTypes.TEAM2_BALL], 
                                          "collision_mask" : [CollisionTypes.TEAM1_BALL, CollisionTypes.STATIC_GEOMETRY, CollisionTypes.TEAM1_PROJECTILE]}
        self.client : GenericPlayerPhysicsObject = src.level_geometry.make_level_geometry_object(enemy_ball_geo, self.simulation_space, self.player_team2_constructor)

        for level_geomerty in src.level_geometry.test_level_geometry:
            src.level_geometry.make_level_geometry_object(level_geomerty, self.simulation_space)

        src.sprites.player.make_connections()

        for event_type in [core_object.networker.NETWORK_CLOSE_EVENT, core_object.networker.NETWORK_CONNECTION_EVENT, core_object.networker.NETWORK_DISCONNECT_EVENT,
                           core_object.networker.NETWORK_ERROR_EVENT, core_object.networker.NETWORK_RECEIVE_EVENT]:
            core_object.event_manager.bind(event_type, self.network_event_handler)

        self.steps_taken : int = 0
        core_object.main_ui.add(core_object.fps_sprite)

    @staticmethod
    def on_collision(arbiter : pymunk.Arbiter, sim_space : pymunk.Space, data : Any):
        pass

    def main_logic(self, delta : float):
        if self.ping_timer.isover():
            self.ping_timer.restart()
            core_object.networker.send_network_message("!!!ping!!!", self.network_key)

        for message in self.recent_messages:
            if self.is_host:
                self.parse_and_react_as_host(message, delta)
            else:
                self.parse_and_react_as_client(message)
        self.recent_messages.clear()

        target_step_count : int = (self.game.game_timer.get_time() / (1 / 60) * self.SIMULATION_STEP_COUNT)
        TIMESCALE_FACTOR : float = 0.2
        for sprite in BasePhysicsObject.active_elements:
            sprite.before_sim(delta)
        step_count : int = min(max(round(target_step_count - self.steps_taken), 1), 100)
        self.steps_taken += step_count
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
        
        # Implement sync logic
        if self.is_host:
            # Sync host ball info
            if self.host.fired_this_frame:
                shot_angle : float = self.host.sim_body.angle if self.is_host else self.client.sim_body.angle
                core_object.networker.send_network_message(f"SHOT_ACTION|{shot_angle}", self.network_key)
                self.host.fired_this_frame = False
            host_sync_message : str = f"SYNC:HOST|{self.host.position.x};{self.host.position.y};"
            host_sync_message += f"{self.host.sim_body.velocity.x};{self.host.sim_body.velocity.y};"
            host_sync_message += f"{self.host.sim_body.angle}"

            core_object.networker.send_network_message(host_sync_message, self.network_key)

            # Sync client ball info
            client_sync_message : str = f"SYNC:CLIENT|{self.client.position.x};{self.client.position.y};"
            client_sync_message += f"{self.client.sim_body.velocity.x};{self.client.sim_body.velocity.y};"
            client_sync_message += f"{self.client.sim_body.angle}"

            core_object.networker.send_network_message(client_sync_message, self.network_key)

            # Damage sync
            damage_sync_message : str = f"SYNC:DAMAGE|{self.host.damage_taken};{self.client.damage_taken}"

            core_object.networker.send_network_message(damage_sync_message, self.network_key)

            # Loosing or winning
            margin : int = 50
            inbound_rect : pygame.Rect = pygame.Rect(-margin, -margin, 960 + 2 * margin, 540 + 2 * margin)
            if not inbound_rect.collidepoint(self.host.position):
                self.switch_to_gameover("You lose!")
                core_object.networker.send_network_message("VICTORY:CLIENT", self.network_key)
            elif not inbound_rect.collidepoint(self.client.position):
                self.switch_to_gameover("You win!")
                core_object.networker.send_network_message("VICTORY:HOST", self.network_key)
        else:
            # Client only sends inputs
            if self.client.fired_this_frame:
                shot_angle : float = self.host.sim_body.angle if self.is_host else self.client.sim_body.angle
                core_object.networker.send_network_message(f"SHOT_ACTION|{shot_angle}", self.network_key)
                self.client.fired_this_frame = False
            inputs : list[bool]
            if self.client.control_scheme != ControlSchemes.MOBILE:
                pressed = pygame.key.get_pressed()
                left_input : bool = pressed[pygame.K_a] or pressed[pygame.K_LEFT]
                right_input : bool = pressed[pygame.K_d] or pressed[pygame.K_RIGHT]
                down_input : bool = pressed[pygame.K_s] or pressed[pygame.K_DOWN]
                up_input : bool = pressed[pygame.K_w] or pressed[pygame.K_UP]
                shoot_input : bool = False
                inputs = [left_input, right_input, down_input, up_input, shoot_input]
            else:
                if not self.client.joystick: 
                    inputs = [False for _ in range(5)]
                else:
                    lock8_direction : pygame.Vector2 = self.client.joystick.get_lock8_pos()
                    inputs = [lock8_direction.x == -1, lock8_direction.x == 1, lock8_direction.y == 1, lock8_direction.y == -1, False]
            message : str = "CLIENT_INPUT|"
            for singular_input in inputs: message += str(int(singular_input))
            message += f";{delta}"
            core_object.networker.send_network_message(message, self.network_key)

        if self.response_timer.isover():
            core_object.end_game()
            core_object.menu.alert_player("Other player disconnected!")
    
    def parse_and_react_as_host(self, message : str, delta : float = 1):
        if message.startswith("Quitting"):
            core_object.end_game()
            core_object.menu.alert_player("Other player disconnected!")
        elif message.startswith("LOG_THIS"):
            parts : list[str] = message.split("|")
            if len(parts) != 2:
                return
            arg : str = parts[1]
            core_object.log(f"Received message from peer: {arg}")
        elif message.startswith("CLIENT_INPUT"):
            parts : list[str] = message.split("|")
            if len(parts) != 2:
                return
            args : list[str] = parts[1].split(";")
            if len(args) != 2:
                return
            self.client.receive_input(args[0], delta, float(args[1]))
        elif message.startswith("SHOT_ACTION"):
            parts : list[str] = message.split("|")
            if len(parts) != 2:
                return
            args : list[str] = parts[1].split(";")
            if len(args) != 1:
                return
            self.client.apply_propulsion(pymunk.Vec2d(0, -1).rotated(float(args[0])))

    def parse_and_react_as_client(self, message : str):
        if message.startswith("Quitting"):
            core_object.end_game()
            core_object.menu.alert_player("Other player disconnected!")
        elif message.startswith("LOG_THIS"):
            parts : list[str] = message.split("|")
            if len(parts) != 2:
                return
            arg : str = parts[1]
            core_object.log(f"Received message from peer: {arg}")
        elif message.startswith("VICTORY"):
            self.switch_to_gameover("You win!" if message.endswith("CLIENT") else "You lose!")
        elif message.startswith("SYNC:HOST") or message.startswith("SYNC:CLIENT"):
            parts : list[str] = message.split("|")
            if len(parts) != 2:
                return
            args : list[str] = parts[1].split(";")
            if len(args) != 5:
                return
            if "HOST" in message:
                self.host.sync_info((float(args[0]), float(args[1])), (float(args[2]), float(args[3])), float(args[4]))
            elif "CLIENT" in message:
                self.client.sync_info((float(args[0]), float(args[1])), (float(args[2]), float(args[3])), float(args[4]))
        elif message.startswith("SYNC:DAMAGE"):
            parts : list[str] = message.split("|")
            if len(parts) != 2:
                return
            args : list[str] = parts[1].split(";")
            if len(args) != 2:
                return
            self.host.damage_taken = float(args[0])
            self.host.damage_taken_uisprite.text = f"{self.host.damage_taken:.0f}%"
            self.client.damage_taken = float(args[1])
            self.client.damage_taken_uisprite.text = f"{self.client.damage_taken:.0f}%"
        elif message.startswith("SHOT_ACTION"):
            parts : list[str] = message.split("|")
            if len(parts) != 2:
                return
            args : list[str] = parts[1].split(";")
            if len(args) != 1:
                return
            self.host.apply_propulsion(pymunk.Vec2d(0, -1).rotated(float(args[0])))   

    def switch_to_gameover(self, message : str):
        src.sprites.player.remove_connections()
        for event_type in [core_object.networker.NETWORK_CLOSE_EVENT, core_object.networker.NETWORK_CONNECTION_EVENT, core_object.networker.NETWORK_DISCONNECT_EVENT,
                           core_object.networker.NETWORK_ERROR_EVENT, core_object.networker.NETWORK_RECEIVE_EVENT]:
            core_object.event_manager.unbind(event_type, self.network_event_handler)
        self.game.state = NetworkedGameOverState(self.game, self, message)
    
    def cleanup(self):
        src.sprites.player.remove_connections()
        for event_type in [core_object.networker.NETWORK_CLOSE_EVENT, core_object.networker.NETWORK_CONNECTION_EVENT, core_object.networker.NETWORK_DISCONNECT_EVENT,
                           core_object.networker.NETWORK_ERROR_EVENT, core_object.networker.NETWORK_RECEIVE_EVENT]:
            core_object.event_manager.unbind(event_type, self.network_event_handler)
        core_object.networker.send_network_message("Quitting", self.network_key)
        core_object.networker.destroy_peer(self.network_key)
    
    def network_event_handler(self, event : pygame.Event):
        if event.type == core_object.networker.NETWORK_RECEIVE_EVENT:
            ...
            #self.game.alert_player(f"Received data {event.data}")
            #core_object.log(f"pygame : Received data {event.data}")
            self.recent_messages.append(event.data)
            self.response_timer.restart()
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
    
    def handle_key_event(self, event : pygame.Event):
        pass

    def pause(self): # disable pausing/unpausing
        pass

class NetworkedGameOverState(GameState):
    def __init__(self, game_object : 'Game', previous : PhysicsNetworkedTestGameState, message : str = "You lose!"):
        self.game = game_object
        self.prev = previous
        self.game.alert_player(message)
        self.timer = Timer(3, self.game.game_timer.get_time)
    
    def main_logic(self, delta):
        if self.timer.isover():
            self.switch_to_rematch()
    
    def switch_to_rematch(self):
        Sprite.kill_all_sprites()
        core_object.main_ui.clear_all()
        self.game.state = NetworkedRematchState(self.game, self.prev)
    
    def cleanup(self):
        self.prev.cleanup()

class NetworkedRematchState(GameState):
    MAX_REPONSE_TIME : float = 1
    def __init__(self, game_object : 'Game', previous : PhysicsNetworkedTestGameState):
        self.game = game_object
        self.is_host : bool = previous.is_host
        self.prev = previous

        self.game = game_object
        self.is_host : bool = self.prev.is_host
        self.peer_id : str = self.prev.peer_id
        self.network_key : str = self.prev.network_key
        for event_type in [core_object.networker.NETWORK_CLOSE_EVENT, core_object.networker.NETWORK_CONNECTION_EVENT, core_object.networker.NETWORK_DISCONNECT_EVENT,
                           core_object.networker.NETWORK_ERROR_EVENT, core_object.networker.NETWORK_RECEIVE_EVENT]:
            core_object.event_manager.bind(event_type, self.network_event_handler)

        window_size = core_object.main_display.get_size()
        self.ui_message : TextSprite = TextSprite(pygame.Vector2(480, 10), "midtop", 0, 
                        f"Rematch?", text_settings=(self.game.font_50, "White", False),
                        text_stroke_settings=("Black", 2), colorkey=(0, 255, 0))
        self.ready_button : UiSprite = BaseUiElements.new_button('BlueButton', 'Ready', 1, 'midright', 
                                            (window_size[0] // 2 - 30, window_size[1] // 2), (0.5, 1.4), 
                                    {'name' : 'ready_button'}, (self.game.font_40, 'Black', False))
        self.unready_button : UiSprite = BaseUiElements.new_button('BlueButton', 'Cancel', 1, 'midright', 
                                            (window_size[0] // 2 - 30, window_size[1] // 2), (0.5, 1.4), 
                                    {'name' : 'unready_button'}, (self.game.font_40, 'Black', False))
        self.quit_button : UiSprite = BaseUiElements.new_button('BlueButton', 'Quit', 1, 'midleft', 
                                            (window_size[0] // 2 + 30, window_size[1] // 2), (0.5, 1.4), 
                                    {'name' : 'quit_button'}, (self.game.font_40, 'Black', False))
        core_object.main_ui.add_multiple([self.ui_message, self.ready_button, self.unready_button, self.quit_button])
        self.unready_button.visible = False

        self.is_ready : bool = False
        self.response_timer : Timer = Timer(-1, time_source=core_object.game.game_timer.get_time)
        

    def main_logic(self, delta : float):
        if self.response_timer.isover():
            core_object.menu.alert_player("Other player disconnected!")
            core_object.end_game()

    def handle_mouse_event(self, event : pygame.Event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            click_pos : tuple[int, int] = event.pos
            if self.ready_button.rect.collidepoint(click_pos):
                if self.is_ready:
                    self.when_unready_clicked()
                else:
                    self.when_ready_clicked()
            elif self.quit_button.rect.collidepoint(click_pos):
                self.when_quit_clicked()
    
    def when_ready_clicked(self):
        self.is_ready = True
        self.ready_button.visible = False
        self.unready_button.visible = True
        core_object.networker.send_network_message("ready?", self.network_key)
        if self.response_timer.duration < 0: self.response_timer.set_duration(self.MAX_REPONSE_TIME)
        self.ui_message.text = "Waiting for other player..."
    
    def when_unready_clicked(self):
        self.is_ready = False
        self.unready_button.visible = False
        self.ready_button.visible = True
        self.ui_message.text = "Do you want a rematch?"
        self.game.alert_player("Rematch cancelled...", 1.5)
    
    def when_quit_clicked(self):
        core_object.end_game()

    def transition_to_play(self):
        for event_type in [core_object.networker.NETWORK_CLOSE_EVENT, core_object.networker.NETWORK_CONNECTION_EVENT, core_object.networker.NETWORK_DISCONNECT_EVENT,
                           core_object.networker.NETWORK_ERROR_EVENT, core_object.networker.NETWORK_RECEIVE_EVENT]:
            core_object.event_manager.unbind(event_type, self.network_event_handler)
        core_object.main_ui.clear_all()
        self.game.state = PhysicsNetworkedTestGameState(self.game, self.network_key, self.peer_id, self.is_host)
    
    def cleanup(self):
        for event_type in [core_object.networker.NETWORK_CLOSE_EVENT, core_object.networker.NETWORK_CONNECTION_EVENT, core_object.networker.NETWORK_DISCONNECT_EVENT,
                           core_object.networker.NETWORK_ERROR_EVENT, core_object.networker.NETWORK_RECEIVE_EVENT]:
            core_object.event_manager.unbind(event_type, self.network_event_handler)
        core_object.networker.send_network_message("Quitting", self.network_key)
        core_object.networker.destroy_peer(self.network_key)
        
    
    def network_event_handler(self, event : pygame.Event):
        if event.type == core_object.networker.NETWORK_RECEIVE_EVENT:
            self.game.alert_player(f"Received data {event.data}")
            core_object.log(f"pygame : Received data {event.data}")
            if event.data == "yes_ready":
                self.transition_to_play()
            elif event.data == "Quitting":
                core_object.end_game()
                core_object.menu.alert_player("Other player quit!")
            elif event.data == "ready?":
                if self.is_ready:
                    core_object.networker.send_network_message("yes_ready", self.network_key)
                    self.transition_to_play()
                else:
                    core_object.networker.send_network_message("not_ready", self.network_key)
            elif event.data == "not_ready":
                self.response_timer.set_duration(-1)

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

        
    def handle_key_event(self, event):
        return
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                core_object.end_game()


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
    global src, TestPlayer, NetworkTestPlayer, NetworkSyncTestPlayer
    import src.sprites.test_player
    from src.sprites.test_player import TestPlayer, NetworkTestPlayer, NetworkSyncTestPlayer

    global BasicPhysicsObject, BasePhysicsObject
    import src.sprites.physics_object
    from src.sprites.physics_object import BasicPhysicsObject, BasePhysicsObject

    global ControlSchemes, GenericPlayerPhysicsObject, Teams
    import src.sprites.player
    from src.sprites.player import ControlSchemes, GenericPlayerPhysicsObject, Teams

    global LevelGeometry
    import src.level_geometry
    from src.level_geometry import LevelGeometry

    global CentralCollisionHandler
    import src.central_collision_handler
    from src.central_collision_handler import CentralCollisionHandler

    global CollisionTypes
    from src.collision_type_constants import CollisionTypes

    global MobileJoystick
    from framework.utils.mobile_joystick import MobileJoystick

    global MobileKeyboard
    from framework.utils.mobile_keyboard import MobileKeyboard

    src.sprites.player.runtime_imports()
    

class GameStates:
    NormalGameState = NormalGameState
    PausedGameState = PausedGameState
    PhysicsTestGameState = PhysicsTestGameState


def initialise_game(game_object : 'Game', event : pygame.Event):
    if event.mode == "test":
        player_count : int = 1
        if event.playcount == 2:
            player_count = 2
        game_object.state = PhysicsTestGameState(game_object, player_count)
    elif event.mode == "net_test":
        if event.hosting:
            host_arg : str = "true"
            room_code = NetworkWaitingGameState.generate_roomcode()
            network_key : str = "tmp_" + room_code + host_arg
            game_object.state = NetworkWaitingGameState(game_object, True, network_key, NetworkWaitingGameState.PREFIX + room_code)
        else:
            game_object.state = NetworkEnterCodeGameState(game_object)
