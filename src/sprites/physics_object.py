import pygame
from framework.game.sprite import Sprite
from framework.core.core import core_object

from framework.utils.animation import Animation
from framework.utils.pivot_2d import Pivot2D
from framework.utils.helpers import ColorType
from framework.utils.my_timer import Timer
import pymunk

from math import degrees
import random
from typing import Any

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
    
    def update(self, delta: float):
        self.position = pygame.Vector2(self.sim_body.position)
        self.angle = degrees(self.sim_body.angle)
    
    def clean_instance(self):
        super().clean_instance()
    
    def draw(self, display : pygame.Surface):
        super().draw(display)

class PlayerPhysicsObject(BasePhysicsObject, sprite_count = 5):
    def __init__(self) -> None:
        super().__init__()
        self.damage_dealt : float
        self.damage_taken : float
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

        element.damage_dealt = 0
        element.damage_taken = 0
        if pymunk.version[0] == "6":
            handler = element.sim_body.space.add_collision_handler(2, 1)
            handler.data = {}
            handler.begin = element.on_collision_with_enemy
            handler.separate = element.post_collision_with_enemy
        else:
            element.sim_body.space.on_collision(2, 1, element.on_collision_with_enemy, separate=element.post_collision_with_enemy, data={})

        cls.unpool(element)
        return element
    
    def on_collision_with_enemy(self, arbiter : pymunk.Arbiter, space : pymunk.Space, data : Any) -> bool:
        data['pre_solve_damage'] = (self.damage_dealt, self.damage_taken)
        player_ball, enemy_ball = arbiter.shapes
        vec_to_enemy_norm : pymunk.Vec2d = (enemy_ball.body.position - player_ball.body.position).normalized()
        velocity_diff = (player_ball.body.velocity - enemy_ball.body.velocity)
        abs_player_velocity = player_ball.body.velocity
        dot_product_dealt = vec_to_enemy_norm.dot(velocity_diff.normalized())
        dot_product_dealt2 = vec_to_enemy_norm.dot(abs_player_velocity.normalized())
        if dot_product_dealt < 0 or dot_product_dealt2 < 0:
            damage_dealt = 0
        else:
            damage_dealt = abs_player_velocity.length_squared * dot_product_dealt * dot_product_dealt2 * 0.01

        vec_to_player_norm : pymunk.Vec2d = -vec_to_enemy_norm
        neg_velocity_diff = -velocity_diff
        abs_enemy_velocity = enemy_ball.body.velocity
        dot_product_taken = vec_to_player_norm.dot(neg_velocity_diff.normalized())
        dot_product_taken2 = vec_to_player_norm.dot(abs_enemy_velocity.normalized())
        if dot_product_taken < 0 or dot_product_taken2 < 0:
            damage_taken = 0
        else:
            damage_taken = abs_enemy_velocity.length_squared * dot_product_taken * dot_product_taken2 * 0.01

        if damage_dealt < 5:
            print("Not enough damage dealt")
        else:
            self.damage_dealt += damage_dealt
            print("Damage dealt:", damage_dealt, f"({self.damage_dealt})")
        if damage_taken < 5:
            print("Not enough damage taken")
        else:
            self.damage_taken += damage_taken
            print("Damage taken:", damage_taken, f"({self.damage_taken})")

        data['enemy_speed_pre_solve'] = abs_enemy_velocity
        data['player_speed_pre_solve'] = abs_player_velocity
        return True
    
    def post_collision_with_enemy(self, arbiter : pymunk.Arbiter, space : pymunk.Space, data : Any) -> None:
        player_ball, enemy_ball = arbiter.shapes
        knockback_mult_player : float = 0.5 * (1 + (data['pre_solve_damage'][1] / 100))
        knockback_mult_enemy : float = 0.5 * (1 + (data['pre_solve_damage'][0] / 100))

        before_enemy_speed = enemy_ball.body.velocity
        before_player_speed = player_ball.body.velocity

        enemy_speed_diff = before_enemy_speed - data['enemy_speed_pre_solve']
        player_speed_diff = before_player_speed - data['player_speed_pre_solve']

        enemy_ball.body.velocity = data['enemy_speed_pre_solve'] + (enemy_speed_diff * knockback_mult_enemy)
        player_ball.body.velocity = data['player_speed_pre_solve'] + (player_speed_diff * knockback_mult_player)
        print(before_enemy_speed.length, "-->", enemy_ball.body.velocity.length)
        print(before_player_speed.length, "-->", player_ball.body.velocity.length)
        print("----")
    
    def before_step(self, delta : float, step_index : int, step_count : int):
        keyboard_map = pygame.key.get_pressed()
        move_vector : pygame.Vector2 = pygame.Vector2(0,0)
        speed : int = 500
        angular_velocity : float = 0
        if keyboard_map[pygame.K_a]:
            move_vector += pygame.Vector2(-1, 0)
        if keyboard_map[pygame.K_d]:
            move_vector += pygame.Vector2(1, 0)
        if keyboard_map[pygame.K_s]:
            move_vector += pygame.Vector2(0, 2.5)
        if keyboard_map[pygame.K_w]:
            move_vector += pygame.Vector2(0, -2.5)
        if keyboard_map[pygame.K_q]:
            angular_velocity += -1
        if keyboard_map[pygame.K_e]:
            angular_velocity += 1
        if move_vector:
            self.sim_body.apply_force_at_world_point(tuple(move_vector * speed), self.sim_body.position) # Force is applied over time in the sim step, so no need to muliply by delta
        if angular_velocity:
            self.sim_body.angular_velocity = angular_velocity * 0.5
        else:
            pass
            self.sim_body.angular_velocity = 0
    
    def apply_propulsion(self):
        force : float = 2500
        direction : pygame.Vector2 = pygame.Vector2(0, 1).rotate(self.angle)
        self.sim_body.apply_impulse_at_world_point(tuple(direction * force), self.sim_body.position) # An impulse is instatenous, so no need to multiply it by delta
        space = self.sim_body.space

        shot_origin : pymunk.Vec2d = self.sim_body.local_to_world((0, -25))
        shot_end : pymunk.Vec2d = self.sim_body.local_to_world((0, -2000))
        hits = space.segment_query(shot_origin, shot_end, 25, pymunk.ShapeFilter())
        for hit in hits:
            if not hit.shape:
                continue
            if hit.shape.collision_type == 1:
                hit.shape.body.apply_impulse_at_world_point(tuple(-direction * force), hit.point)
    def post_sim(self, delta : float):
        self.position = pygame.Vector2(self.sim_body.position)
        self.angle = degrees(self.sim_body.angle)
    
    def update(self, delta: float):
        pass

    def clean_instance(self):
        super().clean_instance()
    
    def draw(self, display : pygame.Surface):
        super().draw(display)
    
    def handle_keydown_event(self, event : pygame.Event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.apply_propulsion()
    
    @classmethod
    def receive_keydown_event(cls, event : pygame.Event):
        for element in cls.active_elements:
            element.handle_keydown_event(event)

def make_connections():
    core_object.event_manager.bind(pygame.KEYDOWN, PlayerPhysicsObject.receive_keydown_event)

def remove_connections():
    core_object.event_manager.unbind(pygame.KEYDOWN, PlayerPhysicsObject.receive_keydown_event)


class EnemyPhysicsObject(BasePhysicsObject, sprite_count = 5):
    def __init__(self) -> None:
        super().__init__()
        self.current_direction : int
        self.shot_timer : Timer
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

        cls.unpool(element)
        return element
    
    def before_step(self, delta : float, step_index : int, step_count : int):
        move_vector : pygame.Vector2 = pygame.Vector2(0,0)
        speed : int = 500
        if self.position.x < 480 - 100:
            move_vector += pygame.Vector2(1, 0)
        elif self.position.x > 480 + 100:
            move_vector += pygame.Vector2(-1, 0)
        if self.position.y < 300:
            move_vector += pygame.Vector2(0, 1)
        if move_vector:
            self.sim_body.apply_force_at_world_point(tuple(move_vector * speed), self.sim_body.position) # Force is applied over time in the sim step, so no need to muliply by delta
        self.sim_body.angular_velocity = 0.2 * self.current_direction

    
    def apply_propulsion(self):
        self.current_direction *= -1
        force : float = 2500
        direction : pygame.Vector2 = pygame.Vector2(0, 1).rotate(self.angle)
        self.sim_body.apply_impulse_at_world_point(tuple(direction * force * 0.65), self.sim_body.position) # An impulse is instatenous, so no need to multiply it by delta

        shot_origin : pymunk.Vec2d = self.sim_body.local_to_world((0, -25))
        shot_end : pymunk.Vec2d = self.sim_body.local_to_world((0, -2000))
        hits = self.sim_body.space.segment_query(shot_origin, shot_end, 25, pymunk.ShapeFilter())
        for hit in hits:
            if not hit.shape:
                continue
            if hit.shape.collision_type == 2:
                hit.shape.body.apply_impulse_at_world_point(tuple(-direction * force * 2), hit.point)

    def post_sim(self, delta : float):
        self.position = pygame.Vector2(self.sim_body.position)
        self.angle = degrees(self.sim_body.angle)
    
    def update(self, delta: float):
        if self.shot_timer.duration < 0 and self.shot_timer.get_time() > 0.5:
            shot_origin : pymunk.Vec2d = self.sim_body.local_to_world((0, -25))
            shot_end : pymunk.Vec2d = self.sim_body.local_to_world((0, -2000))
            hits = self.sim_body.space.segment_query(shot_origin, shot_end, 25, pymunk.ShapeFilter())
            for hit in hits:
                if not hit.shape:
                    continue
                if hit.shape.collision_type == 2:
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
    
    def draw(self, display : pygame.Surface):
        super().draw(display)