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

from math import degrees
import random
from typing import Any, Self
from src.collision_type_constants import CollisionTypes

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
    def __init__(self) -> None:
        super().__init__()
        self.damage_taken : float
        self.damage_taken_uisprite : TextSprite
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
        if pymunk.version[0] == "6":
            handler = element.sim_body.space.add_collision_handler(CollisionTypes.PLAYER_BALL, CollisionTypes.ENEMY_BALL)
            handler._data = {}
            handler.begin = element.on_collision_with_enemy
            handler.separate = element.post_collision_with_enemy

            handler = element.sim_body.space.add_collision_handler(CollisionTypes.PLAYER_BALL, CollisionTypes.ENEMY_PROJECTILE)
            handler._data = {}
            handler.begin = element.on_collision_with_proj_enemy
            handler.separate = element.post_collision_with_proj_enemy
        else:
            element.sim_body.space.on_collision(CollisionTypes.PLAYER_BALL, CollisionTypes.ENEMY_BALL, 
                                                element.on_collision_with_enemy, separate=element.post_collision_with_enemy, data={})
            element.sim_body.space.on_collision(CollisionTypes.PLAYER_BALL, CollisionTypes.ENEMY_PROJECTILE, 
                                                element.on_collision_with_proj_enemy, separate=element.post_collision_with_proj_enemy, data={})
            
        element.damage_taken_uisprite = TextSprite(pygame.Vector2(950, 10), "topright", 0, "0%", 
                                                   text_settings=(core_object.game.font_40, "Red", False), text_stroke_settings=("Black", 2))
        core_object.main_ui.add_multiple([element.damage_taken_uisprite])
        cls.unpool(element)
        return element
    
    def on_collision_with_enemy(self, arbiter : pymunk.Arbiter, space : pymunk.Space, data : Any, invert_shapes : bool = False) -> bool:
        data['pre_solve_damage'] = self.damage_taken
        data['enemy_data'] = {}
        player_ball, enemy_ball = arbiter.shapes if not invert_shapes else (arbiter.shapes[1], arbiter.shapes[0])
        enemy_sprite : EnemyPhysicsObject = EnemyPhysicsObject.get_instance_by_shape(enemy_ball)
        if not isinstance(enemy_sprite, EnemyPhysicsObject):
            print("error")
            return True
        data['enemy_sprite'] = enemy_sprite
        enemy_sprite.on_collision_with_opposant(arbiter, space, data['enemy_data'], invert_shapes=True)
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
            damage_taken = abs_enemy_velocity.get_length_sqrd() * dot_product_taken * dot_product_taken2 * 0.01 * 0.4

        if damage_taken < 5:
            print("Not enough damage taken (player)")
        else:
            self.damage_taken += damage_taken
            print("Damage taken (player):", damage_taken, f"({self.damage_taken})")

        data['player_speed_pre_solve'] = abs_player_velocity
        return True
    
    def post_collision_with_enemy(self, arbiter : pymunk.Arbiter, space : pymunk.Space, data : Any, invert_shapes : bool = False) -> None:
        player_ball, _ = arbiter.shapes if not invert_shapes else (arbiter.shapes[1], arbiter.shapes[0])
        knockback_mult_player : float = 0.5 * (0.5 + (data['pre_solve_damage'] / 100))

        before_player_speed = player_ball.body.velocity

        player_speed_diff = before_player_speed - data['player_speed_pre_solve']

        player_ball.body.velocity = data['player_speed_pre_solve'] + (player_speed_diff * knockback_mult_player)
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
            self.damage_taken += damage_taken
            print("Damage taken (projectile, to player):", damage_taken, f"({self.damage_taken})")

        data['player_speed_pre_solve'] = abs_player_velocity
        return True
    
    def post_collision_with_proj_enemy(self, arbiter : pymunk.Arbiter, space : pymunk.Space, data : Any) -> None:
        player_ball, _ = arbiter.shapes
        knockback_mult_player : float = 0.4 * (0.5 + (data['pre_solve_damage'] / 100))

        before_player_speed = player_ball.body.velocity
        player_speed_diff = before_player_speed - data['player_speed_pre_solve']

        player_ball.body.velocity = data['player_speed_pre_solve'] + (player_speed_diff * knockback_mult_player)
        print("Player speed:", before_player_speed.length, "-->", player_ball.body.velocity.length)
        print("----")
        self.damage_taken_uisprite.text = f"{self.damage_taken:.0f}%"
    
    
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

        shot_origin : pymunk.Vec2d = self.sim_body.local_to_world((0, -19))
        shot_end : pymunk.Vec2d = self.sim_body.local_to_world((0, -2000))
        src.level_geometry.make_projectile(shot_origin, (shot_end - shot_origin).scale_to_length(120), self.sim_body.space, False)

    def post_sim(self, delta : float):
        self.position = pygame.Vector2(self.sim_body.position)
        self.angle = degrees(self.sim_body.angle)
    
    def update(self, delta: float):
        pass

    def clean_instance(self):
        super().clean_instance()
        self.damage_taken = None
        self.damage_taken_uisprite = None
    
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
        self.damage_taken : float
        self.damage_taken_uisprite : TextSprite
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

        element.damage_taken = 0
        if pymunk.version[0] == "6":
            """
            handler = element.sim_body.space.add_collision_handler(CollisionTypes.ENEMY_BALL, CollisionTypes.PLAYER_BALL)
            handler._data = {}
            handler.begin = element.on_collision_with_opposant
            handler.separate = element.post_collision_with_opposant
            """
            handler = element.sim_body.space.add_collision_handler(CollisionTypes.ENEMY_BALL, CollisionTypes.PLAYER_PROJECTILE)
            handler._data = {}
            handler.begin = element.on_collision_with_proj_opposant
            handler.separate = element.post_collision_with_proj_opposant
        else:
            """
            element.sim_body.space.on_collision(CollisionTypes.ENEMY_BALL, CollisionTypes.PLAYER_BALL, 
                                                element.on_collision_with_opposant, separate=element.post_collision_with_opposant, data={})
            """
            element.sim_body.space.on_collision(CollisionTypes.ENEMY_BALL, CollisionTypes.PLAYER_PROJECTILE, 
                                                element.on_collision_with_proj_opposant, separate=element.post_collision_with_proj_opposant, data={})
        element.damage_taken_uisprite = TextSprite(pygame.Vector2(700, 10), "topright", 0, "0%", 
                                                   text_settings=(core_object.game.font_40, "White", False), text_stroke_settings=("Black", 2))
        core_object.main_ui.add_multiple([element.damage_taken_uisprite])

        cls.unpool(element)
        return element
    
    def on_collision_with_opposant(self, arbiter : pymunk.Arbiter, space : pymunk.Space, data : Any, invert_shapes : bool = False) -> bool:
        data['pre_solve_damage'] = self.damage_taken
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
            damage_taken = abs_opposant_velocity.get_length_sqrd() * dot_product_taken * dot_product_taken2 * 0.01 * 0.4

        if damage_taken < 5:
            print(f"Not enough damage taken (enemy) ({abs_opposant_velocity.length, dot_product_taken, dot_product_taken2})")
            print(vec_to_this_norm, abs_opposant_velocity.normalized(), neg_velocity_diff.normalized())
        else:
            self.damage_taken += damage_taken
            print("Damage taken (enemy):", damage_taken, f"({self.damage_taken})")
        data['this_speed_pre_solve'] = abs_this_velocity
        return True
    
    def post_collision_with_opposant(self, arbiter : pymunk.Arbiter, space : pymunk.Space, data : Any, invert_shapes : bool = False) -> None:
        this_ball, opposant_ball = arbiter.shapes if not invert_shapes else (arbiter.shapes[1], arbiter.shapes[0])
        knockback_mult_this : float = 0.5 * (0.5 + (data['pre_solve_damage'] / 100))

        before_this_speed = this_ball.body.velocity

        this_speed_diff = before_this_speed - data['this_speed_pre_solve']

        this_ball.body.velocity = data['this_speed_pre_solve'] + (this_speed_diff * knockback_mult_this)
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
            self.damage_taken += damage_taken
            print("Damage taken (projectile, to enemy):", damage_taken, f"({self.damage_taken})")

        data['this_speed_pre_solve'] = abs_this_velocity
        return True
    
    def post_collision_with_proj_opposant(self, arbiter : pymunk.Arbiter, space : pymunk.Space, data : Any) -> None:
        this_ball, _ = arbiter.shapes
        knockback_mult_this : float = 0.4 * (0.5 + (data['pre_solve_damage'] / 200))

        before_this_speed = this_ball.body.velocity
        this_speed_diff = before_this_speed - data['this_speed_pre_solve']

        this_ball.body.velocity = data['this_speed_pre_solve'] + (this_speed_diff * knockback_mult_this)
        print("Enemy speed:", before_this_speed.length, "-->", this_ball.body.velocity.length)
        print("----")
        self.damage_taken_uisprite.text = f"{self.damage_taken:.0f}%"
    
    
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

        shot_origin : pymunk.Vec2d = self.sim_body.local_to_world((0, -19))
        shot_end : pymunk.Vec2d = self.sim_body.local_to_world((0, -2000))
        src.level_geometry.make_projectile(shot_origin, (shot_end - shot_origin).scale_to_length(120), self.sim_body.space, True)

    def post_sim(self, delta : float):
        self.position = pygame.Vector2(self.sim_body.position)
        self.angle = degrees(self.sim_body.angle)
    
    def update(self, delta: float):
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
                if hit.shape.collision_type == CollisionTypes.PLAYER_BALL:
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
    
    def draw(self, display : pygame.Surface):
        super().draw(display)

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
    
    def clean_instance(self):
        super().clean_instance()
    
    def draw(self, display : pygame.Surface):
        super().draw(display)

def runtime_imports():
    global src
    import src.level_geometry