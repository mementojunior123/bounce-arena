import pygame
import pymunk
from typing import Callable, Any, TypedDict

from src.sprites.physics_object import BasePhysicsObject

CollisionCallbackBool = Callable[[pymunk.Arbiter, pymunk.Space, Any|dict], bool]
CollisionCallbackNoReturn = Callable[[pymunk.Arbiter, pymunk.Space, Any|dict], None]

class CollisionCallbackDict(TypedDict, total=False):
    begin : CollisionCallbackBool
    pre_solve : CollisionCallbackBool
    post_solve : CollisionCallbackNoReturn
    separate : CollisionCallbackNoReturn
    data : Callable[[], dict]


class CentralCollisionHandler:
    def __init__(self, space : pymunk.Space):
        self.space : pymunk.Space = space
        self.registered_callbacks : dict[tuple[int, int], dict[CollisionCallbackBool, CollisionCallbackDict]] = {}
    
    def register(self, t1 : int, t2 : int, callback_condition : CollisionCallbackBool, callback_dict : CollisionCallbackDict):
        """
        Note: This does not support ignoring collision by returning False from the begin/pre_solve callback.

        Additionnally, if you register a callback with (t1, t2) then another one with (t2, t1), 
        don't expect the shapes to be in a consistent order or the callbacks to be done in the order they were registered.
        """
        is_mirror : bool = (t2, t1) in self.registered_callbacks
        
        if (t1, t2) not in self.registered_callbacks:
            self.registered_callbacks[(t1, t2)] = {}
            if not is_mirror:
                if pymunk.version[0] == "6":
                    handler = self.space.add_collision_handler(t1, t2)
                    handler._data = {'types' : (t1, t2)}
                    handler.begin = self.handle_begin
                    handler.pre_solve = self.handle_pre_solve
                    handler.post_solve = self.handle_post_solve
                    handler.separate = self.handle_separate
                else:
                    self.space.on_collision(t1, t2, self.handle_begin, self.handle_pre_solve, self.handle_post_solve, self.handle_separate, data={'types' : (t1, t2)})
        self.registered_callbacks[(t1, t2)][callback_condition] = callback_dict
    
    def unregister(self, callback_dict : CollisionCallbackDict):
        for d in self.registered_callbacks.values():
            conditions_found : list[CollisionCallbackBool] = []
            for callback_condition_it, callback_dict_it in d.items():
                if callback_dict_it == callback_dict:
                    conditions_found.append(callback_condition_it)
            for condition in conditions_found:
                del d[condition]
    
    def handle_begin(self, arbiter : pymunk.Arbiter, space : pymunk.Space, data : dict) -> bool:
        t1, t2 = arbiter.shapes[0].collision_type, arbiter.shapes[1].collision_type
        callbacks : dict[CollisionCallbackBool, CollisionCallbackDict] = self.registered_callbacks[(t1, t2)]
        mirrored_callbacks : dict[CollisionCallbackBool, CollisionCallbackDict] = self.registered_callbacks.get((t2, t1), {})
        activation_list : list[tuple[CollisionCallbackDict, dict]] = []
        for condition in callbacks:
            if condition(arbiter, space, {'types' : (t1, t2)}):
                activation_list.append((callbacks[condition], {}))

        for condition in mirrored_callbacks:
            if condition(arbiter, space, {'types' : (t1, t2)}):
                activation_list.append((mirrored_callbacks[condition], {}))

        activated : CollisionCallbackDict
        ac_data : dict
        for activated, ac_data in activation_list:
            if not activated.get('begin', None): continue
            ac_data.update(   ( activated.get('data', (lambda : {})) )()   )
            activated['begin'](arbiter, space, ac_data)
        data['activation_list'] = activation_list
        return True
    
    def handle_pre_solve(self, arbiter : pymunk.Arbiter, space : pymunk.Space, data : dict) -> bool:
        activation_list : list[tuple[CollisionCallbackDict, dict]] = data['activation_list']
        for activated, ac_data in activation_list:
            if not activated.get('pre_solve', None): continue
            activated['pre_solve'](arbiter, space, ac_data)
        return True
    
    def handle_post_solve(self, arbiter : pymunk.Arbiter, space : pymunk.Space, data : dict) -> None:
        activation_list : list[tuple[CollisionCallbackDict, dict]] = data['activation_list']
        for activated, ac_data in activation_list:
            if not activated.get('post_solve', None): continue
            activated['post_solve'](arbiter, space, ac_data)
    
    def handle_separate(self, arbiter : pymunk.Arbiter, space : pymunk.Space, data : dict) -> None:
        activation_list : list[tuple[CollisionCallbackDict, dict]] = data['activation_list']
        for activated, ac_data in activation_list:
            if not activated.get('separate', None): continue
            activated['separate'](arbiter, space, ac_data)