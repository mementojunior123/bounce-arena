import pygame
from framework.game.sprite import Sprite
from framework.core.core import core_object

from framework.utils.animation import Animation
from framework.utils.pivot_2d import Pivot2D
from framework.utils.helpers import ColorType
from framework.utils.my_timer import Timer
from framework.utils.ui.ui_sprite import UiSprite
from framework.utils.ui.textsprite import TextSprite
import pymunk

from math import degrees, acos
import random
from typing import Any, Self
from src.collision_type_constants import CollisionTypes
from enum import IntEnum

class ControlSchemes:
    NONE = 0
    AI = 1
    LEFT_SIDE = 2
    RIGHT_SIDE = 3
    BOTH_SIDES = 4

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

class PlayerPhysicsObject(BasePhysicsObject, sprite_count = 5):
    CONTROL_SCHEME : int = ControlSchemes.BOTH_SIDES
    def __init__(self) -> None:
        super().__init__()
        self.damage_taken : float
        self.damage_taken_uisprite : TextSprite
        self.damage_cooldown_timer : Timer
        self.current_direction : int
        self.shot_timer : Timer
        self.registered_inputs : list
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

        element.damage_taken = 0
        element.damage_cooldown_timer = Timer(0.1, core_object.game.game_timer.get_time)
        element.current_direction = 1
        element.shot_timer = Timer(-1, core_object.game.game_timer.get_time)
        element.registered_inputs = []

        if pymunk.version[0] == "6":
            handler = element.sim_body.space.add_collision_handler(CollisionTypes.TEAM1_BALL, CollisionTypes.TEAM2_BALL)
            handler._data = {}
            handler.begin = element.on_collision_with_enemy
            handler.separate = element.post_collision_with_enemy

            handler = element.sim_body.space.add_collision_handler(CollisionTypes.TEAM1_BALL, CollisionTypes.TEAM2_PROJECTILE)
            handler._data = {}
            handler.begin = element.on_collision_with_proj_enemy
            handler.separate = element.post_collision_with_proj_enemy
        else:
            element.sim_body.space.on_collision(CollisionTypes.TEAM1_BALL, CollisionTypes.TEAM2_BALL, 
                                                element.on_collision_with_enemy, separate=element.post_collision_with_enemy, data={})
            element.sim_body.space.on_collision(CollisionTypes.TEAM1_BALL, CollisionTypes.TEAM2_PROJECTILE, 
                                                element.on_collision_with_proj_enemy, separate=element.post_collision_with_proj_enemy, data={})
            
        element.damage_taken_uisprite = TextSprite(pygame.Vector2(700, 10), "topright", 0, "0%", 
                                                   text_settings=(core_object.game.font_40, "Blue", False), text_stroke_settings=("Black", 2))
        core_object.main_ui.add_multiple([element.damage_taken_uisprite])
        cls.unpool(element)
        return element

    def sync_info(self, position : tuple[float, float], velocity : tuple[float, float], angle : float,
                  margins : tuple[float, float, float] = (8, 4, 0.03)):
        if (self.position - position).magnitude() > margins[0] or (self.sim_body.velocity - velocity).length > margins[1]:
            self.sim_body.position = pymunk.Vec2d(position[0], position[1])
            self.position = pygame.Vector2(self.sim_body.position)
            self.sim_body.velocity = pymunk.Vec2d(velocity[0], velocity[1])
        if abs(self.sim_body.angle - angle) > margins[2]:
            self.sim_body.angle = angle
            self.angle = degrees(angle)
    
    def receive_input(self, input_data : str):
        if len(self.registered_inputs) >= 2:
            self.registered_inputs = self.registered_inputs[-1:]
        self.registered_inputs.append(input_data)

    def apply_input_before_step(self, delta : float, step_index : int, step_count : int):
        move_vector : pygame.Vector2 = pygame.Vector2(0,0)
        speed : int = 500
        angular_velocity : float = 0
        input_this_frame : str = self.registered_inputs[0] if self.registered_inputs else "00000"
        if input_this_frame[0] == "1":
            move_vector += pygame.Vector2(-1, 0)
        if input_this_frame[1] == "1":
            move_vector += pygame.Vector2(1, 0)
        if input_this_frame[2] == "1":
            move_vector += pygame.Vector2(0, 1.5)
        if input_this_frame[3] == "1":
            move_vector += pygame.Vector2(0, -1.5)
        angular_velocity = self.current_direction * 0.5
        if move_vector:
            self.sim_body.apply_force_at_world_point(tuple(move_vector * speed), self.sim_body.position) # Force is applied over time in the sim step, so no need to muliply by delta
        if angular_velocity:
            self.sim_body.angular_velocity = angular_velocity * 0.5
        else:
            pass
            self.sim_body.angular_velocity = 0

    
    def take_damage(self, damage : float, ignore_cooldown : bool = False, trigger_cooldown : bool = True):
        if not ignore_cooldown and not self.damage_cooldown_timer.isover():
            return
        self.damage_taken += damage
        if self.damage_taken > 500: self.damage_taken = 500.0
        if trigger_cooldown: self.damage_cooldown_timer.restart()
    
    def calculate_damage_from_enemy(self, arbiter : pymunk.Arbiter, space : pymunk.Space, invert_shapes : bool = False) -> tuple[float, str]:
        player_ball, enemy_ball = arbiter.shapes if not invert_shapes else (arbiter.shapes[1], arbiter.shapes[0])
        vec_to_enemy_norm : pymunk.Vec2d = (enemy_ball.body.position - player_ball.body.position).normalized()
        velocity_diff = (player_ball.body.velocity - enemy_ball.body.velocity)
        abs_player_velocity = player_ball.body.velocity

        vec_to_player_norm : pymunk.Vec2d = -vec_to_enemy_norm
        neg_velocity_diff = -velocity_diff
        abs_enemy_velocity = enemy_ball.body.velocity
        dot_product_taken = vec_to_player_norm.dot(neg_velocity_diff.normalized())
        dot_product_taken2 = vec_to_player_norm.dot(abs_enemy_velocity.normalized())
        if dot_product_taken < 0 or dot_product_taken2 < 0:
            damage_taken = 0
        else:
            damage_taken = (abs_enemy_velocity.length + 10) ** 2 * dot_product_taken * dot_product_taken2 * 0.01 * 0.6
        
        if damage_taken < 5:
            log = f"Not enough damage taken (player) ({abs_enemy_velocity.length, dot_product_taken, dot_product_taken2})\n"
            log += f"{vec_to_player_norm, abs_enemy_velocity.normalized(), neg_velocity_diff.normalized()}"
        else:
            log = f"Damage taken (player): {damage_taken} ({min(self.damage_taken + damage_taken, 500)})"
        return damage_taken, log

    def on_collision_with_enemy(self, arbiter : pymunk.Arbiter, space : pymunk.Space, data : Any, invert_shapes : bool = False) -> bool:
        data['pre_solve_damage'] = self.damage_taken
        data['enemy_data'] = {'player_sprite' : self}
        player_ball, enemy_ball = arbiter.shapes if not invert_shapes else (arbiter.shapes[1], arbiter.shapes[0])
        enemy_sprite : EnemyPhysicsObject = EnemyPhysicsObject.get_instance_by_shape(enemy_ball)
        if not isinstance(enemy_sprite, EnemyPhysicsObject):
            print("error")
            return True
        data['enemy_sprite'] = enemy_sprite
        
        abs_player_velocity = player_ball.body.velocity

        projected_damage_taken, log_player = self.calculate_damage_from_enemy(arbiter, space, invert_shapes=False)
        projected_damage_dealt, log_enemy = enemy_sprite.calculate_damage_from_opposant(arbiter, space, invert_shapes=True)

        if projected_damage_taken < 5:
            print(log_player)
        elif projected_damage_taken < projected_damage_dealt:
            print(f"Player won clash ({projected_damage_dealt:.3f} > {projected_damage_taken:.3f})")
        else:
            self.take_damage(projected_damage_taken)
            enemy_sprite.damage_cooldown_timer.restart()
            print(log_player)

        data['enemy_data'].update({'this_won_clash' : projected_damage_taken > projected_damage_dealt, "this_log" : log_enemy, 
                                   "this_projected_damage_taken" : projected_damage_dealt, "this_projected_damage_dealt" : projected_damage_taken})
        data['player_speed_pre_solve'] = abs_player_velocity
        enemy_sprite.on_collision_with_opposant(arbiter, space, data['enemy_data'], invert_shapes=True)

        return True
    
    def post_collision_with_enemy(self, arbiter : pymunk.Arbiter, space : pymunk.Space, data : Any, invert_shapes : bool = False) -> None:
        player_ball, _ = arbiter.shapes if not invert_shapes else (arbiter.shapes[1], arbiter.shapes[0])
        knockback_mult_player : float = 0.5 * (0.5 + (data['pre_solve_damage'] / 100))

        before_player_speed = player_ball.body.velocity

        player_speed_diff : pymunk.Vec2d = before_player_speed - data['player_speed_pre_solve']
        angle_to_ground : float = degrees(acos(player_speed_diff.normalized().dot((0, 1))))
        lift : float
        if angle_to_ground < 55 or data['pre_solve_damage'] < 100:
            lift = 0
        elif player_speed_diff.y > 15:
            lift = 0
        else:
            lift = (data['pre_solve_damage'] - 100) / 5
        player_ball.body.velocity = data['player_speed_pre_solve'] + (player_speed_diff * knockback_mult_player) + pymunk.Vec2d(0, -lift)
        print("Player speed:", before_player_speed.length, "-->", player_ball.body.velocity.length)
        print("----")
        self.damage_taken_uisprite.text = f"{self.damage_taken:.0f}%"
        data['enemy_sprite'].post_collision_with_opposant(arbiter, space, data['enemy_data'], invert_shapes=True)
    
    def on_collision_with_proj_enemy(self, arbiter : pymunk.Arbiter, space : pymunk.Space, data : Any) -> bool:
        data['pre_solve_damage'] = self.damage_taken
        player_ball, proj_ball = arbiter.shapes
        proj_sprite : ProjectilePhysicsObject = ProjectilePhysicsObject.get_instance_by_shape(proj_ball)
        
        vec_to_enemy_norm : pymunk.Vec2d = (proj_ball.body.position - player_ball.body.position).normalized()
        velocity_diff = (player_ball.body.velocity - proj_ball.body.velocity)
        abs_player_velocity = player_ball.body.velocity

        vec_to_player_norm : pymunk.Vec2d = -vec_to_enemy_norm
        neg_velocity_diff = -velocity_diff
        abs_enemy_velocity = proj_ball.body.velocity
        dot_product_taken = vec_to_player_norm.dot(neg_velocity_diff.normalized())
        dot_product_taken2 = vec_to_player_norm.dot(abs_enemy_velocity.normalized())
        if dot_product_taken < 0 or dot_product_taken2 < 0:
            damage_taken = 0
        else:
            damage_taken = abs_enemy_velocity.get_length_sqrd() * dot_product_taken * dot_product_taken2 * 0.01 * 0.2

        if proj_sprite:
            proj_sprite.destroy_safe()

        if damage_taken < 5:
            print("Not enough damage taken (projectile, to player):")
        else:
            self.take_damage(damage_taken, ignore_cooldown=True, trigger_cooldown=False)
            print("Damage taken (projectile, to player):", damage_taken, f"({self.damage_taken})")

        data['player_speed_pre_solve'] = abs_player_velocity
        return True
    
    def post_collision_with_proj_enemy(self, arbiter : pymunk.Arbiter, space : pymunk.Space, data : Any) -> None:
        player_ball, _ = arbiter.shapes
        knockback_mult_player : float = 0.5 * (0.8 + (data['pre_solve_damage'] / 100))

        before_player_speed = player_ball.body.velocity
        player_speed_diff = before_player_speed - data['player_speed_pre_solve']

        player_ball.body.velocity = data['player_speed_pre_solve'] + (player_speed_diff * knockback_mult_player)
        print("Player speed:", before_player_speed.length, "-->", player_ball.body.velocity.length)
        print("----")
        self.damage_taken_uisprite.text = f"{self.damage_taken:.0f}%"
    
    
    def before_step(self, delta : float, step_index : int, step_count : int):
        if self.CONTROL_SCHEME == ControlSchemes.NONE:
            self.apply_input_before_step(delta, step_index, step_count)
            return
        left_side_usable : bool = self.CONTROL_SCHEME in (ControlSchemes.LEFT_SIDE, ControlSchemes.BOTH_SIDES)
        right_side_usable : bool = self.CONTROL_SCHEME in (ControlSchemes.RIGHT_SIDE, ControlSchemes.BOTH_SIDES)
        keyboard_map = pygame.key.get_pressed()
        move_vector : pygame.Vector2 = pygame.Vector2(0,0)
        speed : int = 500
        angular_velocity : float = 0
        if self.CONTROL_SCHEME == ControlSchemes.AI:
            if self.position.x < 480 - 100:
                move_vector += pygame.Vector2(1, 0)
            elif self.position.x > 480 + 100:
                move_vector += pygame.Vector2(-1, 0)
            if self.position.y < 300:
                move_vector += pygame.Vector2(0, 1)
        else:
            if (left_side_usable and keyboard_map[pygame.K_a]) or (keyboard_map[pygame.K_LEFT] and right_side_usable):
                move_vector += pygame.Vector2(-1, 0)
            if (left_side_usable and keyboard_map[pygame.K_d]) or (keyboard_map[pygame.K_RIGHT] and right_side_usable):
                move_vector += pygame.Vector2(1, 0)
            if (left_side_usable and keyboard_map[pygame.K_s]) or (keyboard_map[pygame.K_DOWN] and right_side_usable):
                move_vector += pygame.Vector2(0, 1.5)
            if (left_side_usable and keyboard_map[pygame.K_w]) or (keyboard_map[pygame.K_UP] and right_side_usable):
                move_vector += pygame.Vector2(0, -1.5)
        angular_velocity = self.current_direction * 0.5
        if move_vector:
            self.sim_body.apply_force_at_world_point(tuple(move_vector * speed), self.sim_body.position) # Force is applied over time in the sim step, so no need to muliply by delta
        if angular_velocity:
            self.sim_body.angular_velocity = angular_velocity * 0.5
        else:
            pass
            self.sim_body.angular_velocity = 0
    
    def update(self, delta : float):
        if self.CONTROL_SCHEME != ControlSchemes.AI: return
        if self.shot_timer.duration < 0 and self.shot_timer.get_time() > 0.5:
            shot_origin : pymunk.Vec2d = self.sim_body.local_to_world((0, -10))
            shot_end : pymunk.Vec2d = self.sim_body.local_to_world((0, -2000))
            shot_direction : pymunk.Vec2d = (shot_end - shot_origin).normalized()
            hits = self.sim_body.space.segment_query(shot_origin, shot_end, 2, pymunk.ShapeFilter())
            for hit in hits:
                if not hit.shape:
                    continue
                distance : float = (self.sim_body.position - hit.point).length
                hit_to_center : pymunk.Vec2d = (hit.shape.body.position - hit.point).normalized()
                if distance > 25:
                    if not hit_to_center.dot(shot_direction) > 0.95:
                        continue
                elif not hit_to_center.dot(shot_direction) > 0.60:
                    continue
                if hit.shape.collision_type == CollisionTypes.TEAM2_BALL:
                    self.apply_propulsion()
                    self.shot_timer.set_duration(random.uniform(2, 3))
                    break
        elif self.shot_timer.isover():
            self.apply_propulsion()
            self.shot_timer.set_duration(-1)
    
    def apply_propulsion(self, shot_direction : pymunk.Vec2d|None = None):
        force : float = 1000
        direction : pygame.Vector2 = pygame.Vector2(0, 1).rotate(self.angle)
        self.sim_body.apply_impulse_at_world_point(tuple(direction * force), self.sim_body.position) # An impulse is instatenous, so no need to multiply it by delta
        space = self.sim_body.space

        shot_origin : pymunk.Vec2d = self.sim_body.local_to_world((0, -19))
        shot_end : pymunk.Vec2d = self.sim_body.local_to_world((0, -2000))
        shot_direction = shot_direction or (shot_end - shot_origin).normalized()
        src.level_geometry.make_projectile(shot_origin, shot_direction * 120, self.sim_body.space, False)
        self.current_direction *= -1

    def post_sim(self, delta : float):
        self.position = pygame.Vector2(self.sim_body.position)
        self.angle = degrees(self.sim_body.angle)
        if self.registered_inputs:
            self.registered_inputs.pop(0)
    
    def update(self, delta: float):
        pass

    def clean_instance(self):
        super().clean_instance()
        self.damage_taken = None
        self.damage_taken_uisprite = None
        self.damage_cooldown_timer = None
        self.current_direction = None
        self.shot_timer = None
        self.registered_inputs = None
    
    def draw(self, display : pygame.Surface):
        super().draw(display)
    
    def handle_keydown_event(self, event : pygame.Event):
        left_side_usable : bool = self.CONTROL_SCHEME in (ControlSchemes.LEFT_SIDE, ControlSchemes.BOTH_SIDES)
        right_side_usable : bool = self.CONTROL_SCHEME in (ControlSchemes.RIGHT_SIDE, ControlSchemes.BOTH_SIDES)
        if not isinstance(core_object.game.state, core_object.game.STATES.NormalGameState):
            return
        if event.type == pygame.KEYDOWN:
            if ((event.key == pygame.K_SPACE and left_side_usable) 
                or (event.key in (pygame.K_RETURN, pygame.K_l) and right_side_usable)):
                self.apply_propulsion()
    
    @classmethod
    def receive_keydown_event(cls, event : pygame.Event):
        for element in cls.active_elements:
            element.handle_keydown_event(event)


class EnemyPhysicsObject(BasePhysicsObject, sprite_count = 5):
    CONTROL_SCHEME = ControlSchemes.AI
    def __init__(self) -> None:
        super().__init__()
        self.current_direction : int
        self.shot_timer : Timer
        self.damage_taken : float
        self.damage_taken_uisprite : TextSprite
        self.damage_cooldown_timer : Timer
        self.registered_inputs : list
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

        element.current_direction = 1
        element.shot_timer = Timer(-1, core_object.game.game_timer.get_time)
        element.damage_cooldown_timer = Timer(0.1, core_object.game.game_timer.get_time)
        element.registered_inputs = []

        element.damage_taken = 0
        if pymunk.version[0] == "6":
            """
            handler = element.sim_body.space.add_collision_handler(CollisionTypes.ENEMY_BALL, CollisionTypes.PLAYER_BALL)
            handler._data = {}
            handler.begin = element.on_collision_with_opposant
            handler.separate = element.post_collision_with_opposant
            """
            handler = element.sim_body.space.add_collision_handler(CollisionTypes.TEAM2_BALL, CollisionTypes.TEAM1_PROJECTILE)
            handler._data = {}
            handler.begin = element.on_collision_with_proj_opposant
            handler.separate = element.post_collision_with_proj_opposant
        else:
            """
            element.sim_body.space.on_collision(CollisionTypes.ENEMY_BALL, CollisionTypes.PLAYER_BALL, 
                                                element.on_collision_with_opposant, separate=element.post_collision_with_opposant, data={})
            """
            element.sim_body.space.on_collision(CollisionTypes.TEAM2_BALL, CollisionTypes.TEAM1_PROJECTILE, 
                                                element.on_collision_with_proj_opposant, separate=element.post_collision_with_proj_opposant, data={})
        element.damage_taken_uisprite = TextSprite(pygame.Vector2(950, 10), "topright", 0, "0%", 
                                                   text_settings=(core_object.game.font_40, "Green", False), text_stroke_settings=("Black", 2))
        core_object.main_ui.add_multiple([element.damage_taken_uisprite])

        cls.unpool(element)
        return element

    def sync_info(self, position : tuple[float, float], velocity : tuple[float, float], angle : float,
                  margins : tuple[float, float, float] = (8, 4, 0.03)):
        if (self.position - position).magnitude() > margins[0] or (self.sim_body.velocity - velocity).length > margins[1]:
            self.sim_body.position = pymunk.Vec2d(position[0], position[1])
            self.position = pygame.Vector2(self.sim_body.position)
            self.sim_body.velocity = pymunk.Vec2d(velocity[0], velocity[1])
        if abs(self.sim_body.angle - angle) > margins[2]:
            self.sim_body.angle = angle
            self.angle = degrees(angle)
    
    def receive_input(self, input_data : str):
        if len(self.registered_inputs) >= 2:
            self.registered_inputs = self.registered_inputs[-1:]
        self.registered_inputs.append(input_data)

    def apply_input_before_step(self, delta : float, step_index : int, step_count : int):
        move_vector : pygame.Vector2 = pygame.Vector2(0,0)
        speed : int = 500
        angular_velocity : float = 0
        input_this_frame : str = self.registered_inputs[0] if self.registered_inputs else "00000"
        if input_this_frame[0] == "1":
            move_vector += pygame.Vector2(-1, 0)
        if input_this_frame[1] == "1":
            move_vector += pygame.Vector2(1, 0)
        if input_this_frame[2] == "1":
            move_vector += pygame.Vector2(0, 1.5)
        if input_this_frame[3] == "1":
            move_vector += pygame.Vector2(0, -1.5)
        angular_velocity = self.current_direction * 0.5
        if move_vector:
            self.sim_body.apply_force_at_world_point(tuple(move_vector * speed), self.sim_body.position) # Force is applied over time in the sim step, so no need to muliply by delta
        if angular_velocity:
            self.sim_body.angular_velocity = angular_velocity * 0.5
        else:
            pass
            self.sim_body.angular_velocity = 0

    def take_damage(self, damage : float, ignore_cooldown : bool = False, trigger_cooldown : bool = True):
        if not ignore_cooldown and not self.damage_cooldown_timer.isover():
            return
        self.damage_taken += damage
        if self.damage_taken > 500: self.damage_taken = 500.0
        if trigger_cooldown: self.damage_cooldown_timer.restart()
    
    def calculate_damage_from_opposant(self, arbiter : pymunk.Arbiter, space : pymunk.Space, invert_shapes : bool = False) -> tuple[float, str]:
        this_ball, opposant_ball = arbiter.shapes if not invert_shapes else (arbiter.shapes[1], arbiter.shapes[0])
        vec_to_opposant_norm : pymunk.Vec2d = (opposant_ball.body.position - this_ball.body.position).normalized()
        velocity_diff = (this_ball.body.velocity - opposant_ball.body.velocity)
        abs_this_velocity = this_ball.body.velocity

        vec_to_this_norm : pymunk.Vec2d = -vec_to_opposant_norm
        neg_velocity_diff = -velocity_diff
        abs_opposant_velocity = opposant_ball.body.velocity
        dot_product_taken = vec_to_this_norm.dot(neg_velocity_diff.normalized())
        dot_product_taken2 = vec_to_this_norm.dot(abs_opposant_velocity.normalized())
        if dot_product_taken < 0 or dot_product_taken2 < 0:
            damage_taken = 0
        else:
            damage_taken = (abs_opposant_velocity.length + 10) ** 2 * dot_product_taken * dot_product_taken2 * 0.01 * 0.6
        if damage_taken >= 5:
            return damage_taken, f"Damage taken (player): {damage_taken} ({min(self.damage_taken + damage_taken, 500)})"
        else:
            log = f"Not enough damage taken (enemy) ({abs_opposant_velocity.length, dot_product_taken, dot_product_taken2})\n"
            log += f"{vec_to_this_norm, abs_opposant_velocity.normalized(), neg_velocity_diff.normalized()}"
            return damage_taken, log
    
    def on_collision_with_opposant(self, arbiter : pymunk.Arbiter, space : pymunk.Space, data : Any, invert_shapes : bool = False) -> bool:
        this_ball, opposant_ball = arbiter.shapes if not invert_shapes else (arbiter.shapes[1], arbiter.shapes[0])
        abs_this_velocity = this_ball.body.velocity
        
        data['pre_solve_damage'] = self.damage_taken
        damage_taken : float = data['this_projected_damage_taken']
        logs : str = data['this_log']
        won_clash : bool = data['this_won_clash']

        if damage_taken < 5:
            print(logs)
        elif won_clash:
            print(f"Enemy won clash ({data['this_projected_damage_dealt']:.3f} > {data['this_projected_damage_taken']:.3f})")
        else:
            self.take_damage(damage_taken)
            data['player_sprite'].damage_cooldown_timer.restart()
            print(logs)
        data['this_speed_pre_solve'] = abs_this_velocity
        return True
    
    def post_collision_with_opposant(self, arbiter : pymunk.Arbiter, space : pymunk.Space, data : Any, invert_shapes : bool = False) -> None:
        this_ball, opposant_ball = arbiter.shapes if not invert_shapes else (arbiter.shapes[1], arbiter.shapes[0])
        knockback_mult_this : float = 0.5 * (0.5 + (data['pre_solve_damage'] / 100))

        before_this_speed = this_ball.body.velocity

        this_speed_diff = before_this_speed - data['this_speed_pre_solve']

        angle_to_ground : float = degrees(acos(this_speed_diff.normalized().dot((0, 1))))
        lift : float
        if angle_to_ground < 55 or data['pre_solve_damage'] < 100:
            lift = 0
        elif this_speed_diff.y > 15:
            lift = 0
        else:
            lift = (data['pre_solve_damage'] - 100) / 5

        this_ball.body.velocity = data['this_speed_pre_solve'] + (this_speed_diff * knockback_mult_this) + pymunk.Vec2d(0, -lift)
        print("Enemy speed:", before_this_speed.length, "-->", this_ball.body.velocity.length)
        print("----")
        self.damage_taken_uisprite.text = f"{self.damage_taken:.0f}%"
    
    def on_collision_with_proj_opposant(self, arbiter : pymunk.Arbiter, space : pymunk.Space, data : Any) -> bool:
        data['pre_solve_damage'] = self.damage_taken
        this_ball, proj_ball = arbiter.shapes
        proj_sprite : ProjectilePhysicsObject = ProjectilePhysicsObject.get_instance_by_shape(proj_ball)
        
        vec_to_opposant_norm : pymunk.Vec2d = (proj_ball.body.position - this_ball.body.position).normalized()
        velocity_diff = (this_ball.body.velocity - proj_ball.body.velocity)
        abs_this_velocity = this_ball.body.velocity

        vec_to_this_norm : pymunk.Vec2d = -vec_to_opposant_norm
        neg_velocity_diff = -velocity_diff
        abs_opposant_velocity = proj_ball.body.velocity
        dot_product_taken = vec_to_this_norm.dot(neg_velocity_diff.normalized())
        dot_product_taken2 = vec_to_this_norm.dot(abs_opposant_velocity.normalized())
        if dot_product_taken < 0 or dot_product_taken2 < 0:
            damage_taken = 0
        else:
            damage_taken = abs_opposant_velocity.get_length_sqrd() * dot_product_taken * dot_product_taken2 * 0.01 * 0.2

        if proj_sprite:
            proj_sprite.destroy_safe()

        if damage_taken < 5:
            print("Not enough damage taken (projectile, to enemy):")
        else:
            self.take_damage(damage_taken, ignore_cooldown=True, trigger_cooldown=False)
            print("Damage taken (projectile, to enemy):", damage_taken, f"({self.damage_taken})")

        data['this_speed_pre_solve'] = abs_this_velocity
        return True
    
    def post_collision_with_proj_opposant(self, arbiter : pymunk.Arbiter, space : pymunk.Space, data : Any) -> None:
        this_ball, _ = arbiter.shapes
        knockback_mult_this : float = 0.5 * (0.8 + (data['pre_solve_damage'] / 200))

        before_this_speed = this_ball.body.velocity
        this_speed_diff = before_this_speed - data['this_speed_pre_solve']

        this_ball.body.velocity = data['this_speed_pre_solve'] + (this_speed_diff * knockback_mult_this)
        print("Enemy speed:", before_this_speed.length, "-->", this_ball.body.velocity.length)
        print("----")
        self.damage_taken_uisprite.text = f"{self.damage_taken:.0f}%"
    
    

    def before_step(self, delta : float, step_index : int, step_count : int):
        if self.CONTROL_SCHEME == ControlSchemes.NONE:
            self.apply_input_before_step(delta, step_index, step_count)
            return
        left_side_usable : bool = self.CONTROL_SCHEME in (ControlSchemes.LEFT_SIDE, ControlSchemes.BOTH_SIDES)
        right_side_usable : bool = self.CONTROL_SCHEME in (ControlSchemes.RIGHT_SIDE, ControlSchemes.BOTH_SIDES)
        keyboard_map = pygame.key.get_pressed()
        move_vector : pygame.Vector2 = pygame.Vector2(0,0)
        speed : int = 500
        angular_velocity : float = 0
        if self.CONTROL_SCHEME == ControlSchemes.AI:
            if self.position.x < 480 - 100:
                move_vector += pygame.Vector2(1, 0)
            elif self.position.x > 480 + 100:
                move_vector += pygame.Vector2(-1, 0)
            if self.position.y < 300:
                move_vector += pygame.Vector2(0, 1)
        else:
            if (left_side_usable and keyboard_map[pygame.K_a]) or (keyboard_map[pygame.K_LEFT] and right_side_usable):
                move_vector += pygame.Vector2(-1, 0)
            if (left_side_usable and keyboard_map[pygame.K_d]) or (keyboard_map[pygame.K_RIGHT] and right_side_usable):
                move_vector += pygame.Vector2(1, 0)
            if (left_side_usable and keyboard_map[pygame.K_s]) or (keyboard_map[pygame.K_DOWN] and right_side_usable):
                move_vector += pygame.Vector2(0, 1.5)
            if (left_side_usable and keyboard_map[pygame.K_w]) or (keyboard_map[pygame.K_UP] and right_side_usable):
                move_vector += pygame.Vector2(0, -1.5)
        angular_velocity = self.current_direction * 0.5
        if move_vector:
            self.sim_body.apply_force_at_world_point(tuple(move_vector * speed), self.sim_body.position) # Force is applied over time in the sim step, so no need to muliply by delta
        if angular_velocity:
            self.sim_body.angular_velocity = angular_velocity * 0.5
        else:
            pass
            self.sim_body.angular_velocity = 0

    
    def apply_propulsion(self, shot_direction : pymunk.Vec2d|None = None):
        self.current_direction *= -1
        force : float = 2500 * 0.65 if self.CONTROL_SCHEME == ControlSchemes.AI else 1000
        direction : pygame.Vector2 = pygame.Vector2(0, 1).rotate(self.angle)
        self.sim_body.apply_impulse_at_world_point(tuple(direction * force), self.sim_body.position) # An impulse is instatenous, so no need to multiply it by delta

        shot_origin : pymunk.Vec2d = self.sim_body.local_to_world((0, -19))
        shot_end : pymunk.Vec2d = self.sim_body.local_to_world((0, -2000))
        shot_direction = shot_direction or (shot_end - shot_origin).normalized()
        src.level_geometry.make_projectile(shot_origin, shot_direction * 120, self.sim_body.space, True)

    def post_sim(self, delta : float):
        self.position = pygame.Vector2(self.sim_body.position)
        self.angle = degrees(self.sim_body.angle)
        if self.registered_inputs:
            self.registered_inputs.pop(0)
    
    def update(self, delta: float):
        if self.CONTROL_SCHEME != ControlSchemes.AI: return
        if self.shot_timer.duration < 0 and self.shot_timer.get_time() > 0.5:
            shot_origin : pymunk.Vec2d = self.sim_body.local_to_world((0, -10))
            shot_end : pymunk.Vec2d = self.sim_body.local_to_world((0, -2000))
            shot_direction : pymunk.Vec2d = (shot_end - shot_origin).normalized()
            hits = self.sim_body.space.segment_query(shot_origin, shot_end, 2, pymunk.ShapeFilter())
            for hit in hits:
                if not hit.shape:
                    continue
                distance : float = (self.sim_body.position - hit.point).length
                hit_to_center : pymunk.Vec2d = (hit.shape.body.position - hit.point).normalized()
                if distance > 25:
                    if not hit_to_center.dot(shot_direction) > 0.95:
                        continue
                elif not hit_to_center.dot(shot_direction) > 0.60:
                    continue
                if hit.shape.collision_type == CollisionTypes.TEAM1_BALL:
                    self.apply_propulsion()
                    self.shot_timer.set_duration(random.uniform(2, 3))
                    break
        elif self.shot_timer.isover():
            self.apply_propulsion()
            self.shot_timer.set_duration(-1)

    def clean_instance(self):
        super().clean_instance()
        self.current_direction = None
        self.shot_timer = None
        self.damage_taken = None
        self.damage_taken_uisprite = None
        self.damage_cooldown_timer = None
        self.registered_inputs = None
    
    def draw(self, display : pygame.Surface):
        super().draw(display)
    
    def handle_keydown_event(self, event : pygame.Event):
        left_side_usable : bool = self.CONTROL_SCHEME in (ControlSchemes.LEFT_SIDE, ControlSchemes.BOTH_SIDES)
        right_side_usable : bool = self.CONTROL_SCHEME in (ControlSchemes.RIGHT_SIDE, ControlSchemes.BOTH_SIDES)
        if not isinstance(core_object.game.state, core_object.game.STATES.NormalGameState):
            return
        if event.type == pygame.KEYDOWN:
            if ((event.key == pygame.K_SPACE and left_side_usable) 
                or (event.key in (pygame.K_RETURN, pygame.K_l) and right_side_usable)):
                self.apply_propulsion()
    
    @classmethod
    def receive_keydown_event(cls, event : pygame.Event):
        for element in cls.active_elements:
            element.handle_keydown_event(event)

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

def make_connections():
    core_object.event_manager.bind(pygame.KEYDOWN, PlayerPhysicsObject.receive_keydown_event)
    core_object.event_manager.bind(pygame.KEYDOWN, EnemyPhysicsObject.receive_keydown_event)

def remove_connections():
    core_object.event_manager.unbind(pygame.KEYDOWN, PlayerPhysicsObject.receive_keydown_event)
    core_object.event_manager.unbind(pygame.KEYDOWN, EnemyPhysicsObject.receive_keydown_event)

def runtime_imports():
    global src
    import src.level_geometry