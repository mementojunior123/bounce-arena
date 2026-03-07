from enum import IntEnum

from src.collision_type_constants import CollisionTypes
from framework.core.core import core_object
from framework.utils.my_timer import Timer
from framework.utils.pivot_2d import Pivot2D
from framework.utils.ui.textsprite import TextSprite
from framework.utils.helpers import ColorType
from src.sprites.physics_object import BasePhysicsObject
from src.sprites.projectiles import ProjectilePhysicsObject


import pygame
import pymunk


import random
from math import acos, degrees
from typing import Any, Union


def print_if_not_web(*args, **kwargs):
    if core_object.is_web():
        return
    print(*args, **kwargs)


class ControlSchemes(IntEnum):
    NONE = 0
    AI = 1
    LEFT_SIDE = 2
    RIGHT_SIDE = 3
    BOTH_SIDES = 4


class Teams(IntEnum):
    NONE = 0
    TEAM_1 = 1
    TEAM_2 = 2


class GenericPlayerPhysicsObject(BasePhysicsObject, sprite_count = 5):
    def __init__(self) -> None:
        super().__init__()
        self.current_direction : int
        self.shot_timer : Timer
        self.damage_taken : float
        self.damage_taken_uisprite : TextSprite
        self.damage_cooldown_timer : Timer
        self.registered_inputs : list

        self.control_scheme : ControlSchemes
        self.team : Teams
        pass

    @classmethod
    def spawn(cls, obj : pymunk.Body, image : pygame.Surface|None = None,
              pivot_offest : pygame.Vector2|None = None,
              control_scheme : ControlSchemes = ControlSchemes.NONE, team : Teams = Teams.NONE,
              main_collison_handler : Union['CentralCollisionHandler', None] = None,
              text_position : tuple[int, int] = (950, 10), text_color : ColorType = "Blue"):
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

        element.control_scheme = control_scheme
        element.team = team

        element.damage_taken = 0
        element.register_collisions(main_collison_handler)
        element.damage_taken_uisprite = TextSprite(pygame.Vector2(text_position), "topright", 0, "0%",
                                                   text_settings=(core_object.game.font_40, text_color, False), text_stroke_settings=("Black", 2))
        core_object.main_ui.add_multiple([element.damage_taken_uisprite])

        cls.unpool(element)
        return element

    def concerned_by_collision(self, arbiter : pymunk.Arbiter, space : pymunk.Space, data : dict) -> bool:
        return self.shape_belongs_to_this(arbiter.shapes[0]) and self.active

    def concerned_by_collision_2way(self, arbiter : pymunk.Arbiter, space : pymunk.Space, data : dict) -> bool:
        return (self.shape_belongs_to_this(arbiter.shapes[0]) or self.shape_belongs_to_this(arbiter.shapes[1])) and self.active

    def register_collisions(self, main_collision_handler : Union['CentralCollisionHandler', None]  = None):
        if hasattr(core_object.game.state, 'main_collision_handler') and not main_collision_handler:
            main_collision_handler : src.central_collision_handler.CentralCollisionHandler = core_object.game.state.main_collision_handler
        elif not main_collision_handler:
            core_object.log("Player collisions could not be registered")
            return
        callback_dict_enemy : src.central_collision_handler.CollisionCallbackDict = {
            'begin' : self.on_collision_with_opposant,
            'separate' : self.post_collision_with_opposant
        }
        callback_dict_proj : src.central_collision_handler.CollisionCallbackDict = {
            'begin' : self.on_collision_with_proj_opposant,
            'separate' : self.post_collision_with_proj_opposant
        }
        if self.team == Teams.TEAM_1:
            main_collision_handler.register(CollisionTypes.TEAM1_BALL, CollisionTypes.TEAM2_BALL, self.concerned_by_collision_2way, callback_dict_enemy)
            main_collision_handler.register(CollisionTypes.TEAM1_BALL, CollisionTypes.TEAM2_PROJECTILE, self.concerned_by_collision, callback_dict_proj)
        elif self.team == Teams.TEAM_2:
            main_collision_handler.register(CollisionTypes.TEAM2_BALL, CollisionTypes.TEAM1_BALL, self.concerned_by_collision_2way, callback_dict_enemy)
            main_collision_handler.register(CollisionTypes.TEAM2_BALL, CollisionTypes.TEAM1_PROJECTILE, self.concerned_by_collision, callback_dict_proj)

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
        buffer_len : int = 2
        if not self.registered_inputs:
            self.registered_inputs.append(input_data)
        elif not buffer_len:
            self.registered_inputs.append(input_data)
            self.registered_inputs = [self.combine_inputs_OR(self.registered_inputs)]
        if len(self.registered_inputs) >= buffer_len:
            final_index : int = len(self.registered_inputs) - 1
            overload_inputs : list[str] = self.registered_inputs[:final_index - buffer_len + 1]
            tmp = self.registered_inputs[final_index - buffer_len + 1:]
            self.registered_inputs = [self.combine_inputs_OR(overload_inputs)] if overload_inputs else []
            self.registered_inputs.extend(tmp)
        else:
            self.registered_inputs.append(input_data)

    def combine_inputs_OR(self, inputs : list[str]) -> str:
        if not inputs: return "00000"
        result : str = ""
        input_len = len(inputs[0])
        for i in range(input_len):
            if any(input[i] == "1" for input in inputs):
                result += "1"
            else:
                result += "0"
        return result

    def combine_inputs_AND(self, inputs : list[str]) -> str:
        if not inputs: return "00000"
        result : str = ""
        input_len = len(inputs[0])
        for i in range(input_len):
            if all(input[i] == "1" for input in inputs):
                result += "1"
            else:
                result += "0"
        return result


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

    def calculate_damage_from_opposant(self, arbiter : pymunk.Arbiter, space : pymunk.Space) -> tuple[float, str]:
        this_ball, opposant_ball = (arbiter.shapes
                        if self.shape_belongs_to_this(arbiter.shapes[0])
                        else (arbiter.shapes[1], arbiter.shapes[0]))
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
            return damage_taken, f"Damage taken {Teams(self.team).name} player: {damage_taken} ({min(self.damage_taken + damage_taken, 500)})"
        else:
            log = f"Not enough damage taken {Teams(self.team).name} player ({abs_opposant_velocity.length, dot_product_taken, dot_product_taken2})\n"
            log += f"{vec_to_this_norm, abs_opposant_velocity.normalized(), neg_velocity_diff.normalized()}"
            return damage_taken, log

    def on_collision_with_opposant(self, arbiter : pymunk.Arbiter, space : pymunk.Space, data : Any) -> bool:
        data['pre_solve_damage'] = self.damage_taken
        this_ball, opposant_ball = (arbiter.shapes
                        if self.shape_belongs_to_this(arbiter.shapes[0])
                        else (arbiter.shapes[1], arbiter.shapes[0]))
        opposant_sprite : GenericPlayerPhysicsObject = GenericPlayerPhysicsObject.get_instance_by_shape(opposant_ball)
        if not isinstance(opposant_sprite, GenericPlayerPhysicsObject):
            print_if_not_web("error")
            return True
        data['opposant_sprite'] = opposant_sprite

        abs_this_velocity = this_ball.body.velocity

        projected_damage_taken, log_this = self.calculate_damage_from_opposant(arbiter, space)
        projected_damage_dealt, log_opposant = opposant_sprite.calculate_damage_from_opposant(arbiter, space)

        if projected_damage_taken < 5:
            print_if_not_web(log_this)
        elif projected_damage_taken < projected_damage_dealt:
            print_if_not_web(f"{Teams(self.team).name} player won clash ({projected_damage_dealt:.3f} > {projected_damage_taken:.3f})")
        else:
            self.take_damage(projected_damage_taken)
            opposant_sprite.damage_cooldown_timer.restart()
            print_if_not_web(log_this)

        data['this_speed_pre_solve'] = abs_this_velocity

        return True

    def post_collision_with_opposant(self, arbiter : pymunk.Arbiter, space : pymunk.Space, data : Any) -> None:
        this_ball, _ = (arbiter.shapes
                        if self.shape_belongs_to_this(arbiter.shapes[0])
                        else (arbiter.shapes[1], arbiter.shapes[0]))
        knockback_mult_this : float = 0.5 * (0.5 + (data['pre_solve_damage'] / 100))

        before_this_speed = this_ball.body.velocity

        this_speed_diff : pymunk.Vec2d = before_this_speed - data['this_speed_pre_solve']
        angle_to_ground : float = degrees(acos(this_speed_diff.normalized().dot((0, 1))))
        lift : float
        if angle_to_ground < 55 or data['pre_solve_damage'] < 100:
            lift = 0
        elif this_speed_diff.y > 15:
            lift = 0
        else:
            lift = (data['pre_solve_damage'] - 100) / 5
        this_ball.body.velocity = data['this_speed_pre_solve'] + (this_speed_diff * knockback_mult_this) + pymunk.Vec2d(0, -lift)
        print_if_not_web(f"{Teams(self.team).name} player speed:", before_this_speed.length, "-->", this_ball.body.velocity.length)
        print_if_not_web("----")
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
            print_if_not_web(f"Not enough damage taken (projectile, to {Teams(self.team).name} player):")
        else:
            self.take_damage(damage_taken, ignore_cooldown=True, trigger_cooldown=False)
            print_if_not_web(f"Damage taken (projectile, to {Teams(self.team).name} player):", damage_taken, f"({self.damage_taken})")

        data['this_speed_pre_solve'] = abs_this_velocity
        return True

    def post_collision_with_proj_opposant(self, arbiter : pymunk.Arbiter, space : pymunk.Space, data : Any) -> None:
        this_ball, _ = arbiter.shapes
        knockback_mult_this : float = 0.5 * (0.8 + (data['pre_solve_damage'] / 200))

        before_this_speed = this_ball.body.velocity
        this_speed_diff = before_this_speed - data['this_speed_pre_solve']

        this_ball.body.velocity = data['this_speed_pre_solve'] + (this_speed_diff * knockback_mult_this)
        print_if_not_web(f"{Teams(self.team).name} player speed:", before_this_speed.length, "-->", this_ball.body.velocity.length)
        print_if_not_web("----")
        self.damage_taken_uisprite.text = f"{self.damage_taken:.0f}%"



    def before_step(self, delta : float, step_index : int, step_count : int):
        if self.control_scheme == ControlSchemes.NONE:
            self.apply_input_before_step(delta, step_index, step_count)
            return
        left_side_usable : bool = self.control_scheme in (ControlSchemes.LEFT_SIDE, ControlSchemes.BOTH_SIDES)
        right_side_usable : bool = self.control_scheme in (ControlSchemes.RIGHT_SIDE, ControlSchemes.BOTH_SIDES)
        keyboard_map = pygame.key.get_pressed()
        move_vector : pygame.Vector2 = pygame.Vector2(0,0)
        speed : int = 500
        angular_velocity : float = 0
        if self.control_scheme == ControlSchemes.AI:
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
        force : float = 2500 * 0.65 if self.control_scheme == ControlSchemes.AI else 1000
        direction : pygame.Vector2 = pygame.Vector2(0, 1).rotate(self.angle)
        self.sim_body.apply_impulse_at_world_point(tuple(direction * force), self.sim_body.position) # An impulse is instatenous, so no need to multiply it by delta

        shot_origin : pymunk.Vec2d = self.sim_body.local_to_world((0, -19))
        shot_end : pymunk.Vec2d = self.sim_body.local_to_world((0, -2000))
        shot_direction = shot_direction or (shot_end - shot_origin).normalized()
        src.level_geometry.make_projectile(shot_origin, shot_direction * 120, self.sim_body.space, True if self.team == Teams.TEAM_2 else False)

    def post_sim(self, delta : float):
        self.position = pygame.Vector2(self.sim_body.position)
        self.angle = degrees(self.sim_body.angle)
        if self.registered_inputs:
            self.registered_inputs.pop(0)

    def update(self, delta: float):
        if self.control_scheme != ControlSchemes.AI: return
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

        self.team = None
        self.control_scheme = None

    def draw(self, display : pygame.Surface):
        super().draw(display)

    def handle_keydown_event(self, event : pygame.Event):
        left_side_usable : bool = self.control_scheme in (ControlSchemes.LEFT_SIDE, ControlSchemes.BOTH_SIDES)
        right_side_usable : bool = self.control_scheme in (ControlSchemes.RIGHT_SIDE, ControlSchemes.BOTH_SIDES)
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


def make_connections():
    core_object.event_manager.bind(pygame.KEYDOWN, GenericPlayerPhysicsObject.receive_keydown_event)


def remove_connections():
    core_object.event_manager.unbind(pygame.KEYDOWN, GenericPlayerPhysicsObject.receive_keydown_event)


def runtime_imports():
    global src

    global CentralCollisionHandler
    from src.central_collision_handler import CentralCollisionHandler
    import src.level_geometry
    import src.central_collision_handler