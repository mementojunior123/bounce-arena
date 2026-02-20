import pygame
import json
import platform
from typing import Union, TypeAlias

class SoundTypes:
    music = 'Music'
    sfx = 'SFX'

class WebChannel:
    CHANNELS : dict[int, 'WebChannel'] = {}

    @classmethod
    def _get_unused_channel(cls, force : bool = False) -> int|None:
        for i in range(core_object.bg_manager.MAX_CHANNEL_COUNT):
            if i not in cls.CHANNELS:
                return i
            if not cls.CHANNELS[i].get_busy():
                return i
        if force:
            return 0
        return None
    
    def __new__(cls, channel_id : int):
        if channel_id in WebChannel.CHANNELS:
            return WebChannel.CHANNELS[channel_id]
        else:
            new = super(WebChannel, cls).__new__(WebChannel)
            WebChannel.CHANNELS[channel_id] = new

        return new

    def __init__(self, channel_id : int):
        if hasattr(self, '_id'): return
        self._id = channel_id
        self.bg_manager : BgManager = core_object.bg_manager
        self._volume : float = 0
        self._sound_name : str|None = None
        self._sound_ref : pygame.mixer.Sound|None = None
        self._sound_path : str|None = None
        self._actual_vol : float = -1
    
    @property
    def id(self) -> int|None:
        return self._id

    def play(self, sound_name : str, loops : int = 0, maxtime : float = 0, fade_ms : float = 0, volume : float = 1.0):
        if self._id is None: return
        if sound_name not in self.bg_manager.SOUNDS:
            core_object.log(f"Sound {sound_name} not found!")
            return
        if fade_ms:
            core_object.log(f"Warning : WebChannels do not support fade_ms")
        if maxtime:
            core_object.log(f"Warning : WebChannels do not support maxtime")
        self._volume = volume
        sound_obj, path = self.bg_manager.SOUNDS[sound_name]
        self._sound_name = sound_name
        self._sound_ref : pygame.mixer.Sound = sound_obj
        self._sound_path : str = path
        self._actual_vol : float = sound_obj.get_volume() * self._volume * self.bg_manager.web_mult
        core_object.run_js_source_file('dispatch_event', {
            "EVENT_TYPE" : "StartAudio",
            "EVENT_ARGS" : json.dumps({'id' : self._id, 'path' : self._sound_path, 'volume' : self._actual_vol, 'target_loop_count' : loops})
        })
    
    def pause(self):
        if self._id is None: return
        core_object.run_js_source_file('dispatch_event', {
            "EVENT_TYPE" : "PauseAudio",
            "EVENT_ARGS" : json.dumps({'id' : self._id})
        })
    
    def unpause(self):
        if self._id is None: return
        core_object.run_js_source_file('dispatch_event', {
            "EVENT_TYPE" : "ResumeAudio",
            "EVENT_ARGS" : json.dumps({'id' : self._id})
        })
    
    def stop(self):
        core_object.run_js_source_file('dispatch_event', {
            "EVENT_TYPE" : "StopAudio",
            "EVENT_ARGS" : json.dumps({'id' : self._id})
        })
        self._sound_ref = None
        self._sound_path = None
        self._sound_name = None

    def get_volume(self) -> float:
        return self._volume
    
    def set_volume(self, new_vol : float, arg2 : float|None=None):
        if arg2 is not None:
            core_object.log("Stereo sound not supported in the browser!")
        if self._id is None: return
        if new_vol != self._volume:
            self._actual_vol : float = self._sound_ref.get_volume() * self._volume * self.bg_manager.web_mult
            self._volume = new_vol
            core_object.run_js_source_file('dispatch_event', {
                "EVENT_TYPE" : "UpdateVolume",
                "EVENT_ARGS" : json.dumps({'id' : self._id, 'volume' : self._actual_vol})
            })

    def _update_volume(self):
        if self._id is None: return
        new_vol : float = self._sound_ref.get_volume() * self._volume * self.bg_manager.web_mult
        if new_vol != self._actual_vol:
            self._actual_vol = new_vol
            core_object.run_js_source_file('dispatch_event', {
                "EVENT_TYPE" : "UpdateVolume",
                "EVENT_ARGS" : json.dumps({'id' : self._id, 'volume' : self._actual_vol})
            })
    
    def _update(self):
        if self._id is None: return
        self._update_volume()
        core_object.run_js_source_file('dispatch_event', {
            "EVENT_TYPE" : "UpdateAudioChannel",
            "EVENT_ARGS" : json.dumps({'id' : self._id})
        })
        if not self.get_busy():
            self._sound_ref = None
            self._sound_path = None
            self._sound_name = None
        
    
    def get_sound(self) -> pygame.mixer.Sound|None:
        return self._sound_ref
    
    def get_busy(self) -> bool:
        if self._sound_ref is None: return False
        k : str = 'WebAudioChannel' + str(self._id) + "_" + 'busy'
        return (platform.window.localStorage.getItem(k) == "true")
    
    def queue(self, arg1):
        core_object.log("Webchannel.queue is not implemented!")
    
    def get_queue(self) -> None:
        core_object.log("Webchannel.get_queue is not implemented!")
    
    def set_endevent(self, t=None) -> None:
        core_object.log("Webchannel.set_endevent is not implemented!")
    
    def get_endevent(self) -> None:
        core_object.log("Webchannel.get_endevent is not implemented!")
    
AnyChannel : TypeAlias = Union[pygame.mixer.Channel, WebChannel]

class BgManager:
    MAX_CHANNEL_COUNT : int = pygame.mixer.get_num_channels()
    def __init__(self, core_refrence : "Core") -> None:
        global core_object
        core_object = core_refrence
        self.core : "Core" = core_refrence
        self.current : dict[AnyChannel, TrackInfo] = {}
        self.global_volume = 1
        self.web_mult : float = 1.0
        self.USE_WEB_ENGINE : bool = False
        self.sound_types = SoundTypes
        if 'make_web_channel' not in self.core.js_source:
            self.core.load_js_source_file('framework/core/web_audio/web_audio.js', 'make_web_channel', {
                "CHANNEL_COUNT" : None,
                "PATH_LIST" : None
            })
        self.SOUNDS : dict[str, tuple[pygame.mixer.Sound, str]] = {}
        sound_list : list[tuple[str, str, float]] = [
            ('test_music', 'assets/audio/music/test_music.ogg', 1.0),
            ('test_sfx', 'assets/audio/sfx/test_sfx.ogg', 1.0),
            ('PLACEHOLDER_DO_NOT_TOUCH', 'assets/audio/NOTHING.ogg', 1.0)
        ]
        path_list : list[str] = []
        for name, path, vol in sound_list:
            self.load_sound(path, vol, name)
            path_list.append(path)
        if self.core.is_web() and self.USE_WEB_ENGINE:
            self.core.run_js_source_file('make_web_channel', {
                "CHANNEL_COUNT" : str(BgManager.MAX_CHANNEL_COUNT),
                "PATH_LIST" : str(path_list)
            })

    def find_unused_channel(force : bool = False) -> pygame.mixer.Channel|WebChannel|None:
        WebChannel._get_unused_channel(force) if core_object.is_web() else pygame.mixer.find_channel(force)

    def load_sound(self, path : str, vol : float, name : str):
        sound = pygame.mixer.Sound(path)
        sound.set_volume(vol)
        self.SOUNDS[name] = (sound, path)
    
    def get_sound_obj(self, sound_name : str) -> pygame.mixer.Sound|None:
        return self.SOUNDS.get(sound_name, (None, None))[0]
    
    
    def test_play_web(self, name : str):
        if not self.core.is_web(): return
        channel : WebChannel = WebChannel(WebChannel._get_unused_channel(True))
        channel.play(name)

    def set_global_volume(self, new_volume):
        self.global_volume = new_volume
        for channel in self.current:
            info : TrackInfo = self.current[channel]
            channel.set_volume(self.global_volume * info.volume)

    def _play_web(self, track_name : str, volume : float, loops = -1, maxtime = 0, fade_ms = 0, 
                  sound_type : str|None = 'Music'):
        channel : WebChannel = WebChannel(WebChannel._get_unused_channel(True))
        channel.play(track_name, loops, maxtime, fade_ms, volume)
        channel.set_volume(volume * self.global_volume)
        self.current[channel] = TrackInfo(volume, sound_type)

    def play(self, track_name : str, volume, loops = -1, maxtime = 0, fade_ms = 0, sound_type : str|None = 'Music'):
        """Used for playing music."""
        if core_object.is_web() and self.USE_WEB_ENGINE:
            self._play_web(track_name, volume, loops, maxtime, fade_ms, sound_type)
            return
        else:
            track = self.get_sound_obj(track_name)
        channel = track.play(loops, maxtime, fade_ms)
        if not channel:
            core_object.log("Attempted to play track, but ran out of audio channels!")
            return
        if volume < 1 or volume > 1:
            channel.set_volume(volume * self.global_volume)
            print('hello world')
        self.current[channel] = TrackInfo(volume, sound_type)
        return channel
    
    def play_sfx(self, sfx_name : str, volume, loops = 0, maxtime = 0, fade_ms = 0, sound_type : str|None = 'SFX'):
        """Used for playing short sound effects."""
        if core_object.is_web() and self.USE_WEB_ENGINE:
            self._play_web(sfx_name, volume, loops, maxtime, fade_ms, sound_type)
            return
        else:
            sfx = self.get_sound_obj(sfx_name)
        channel = sfx.play(loops, maxtime, fade_ms)
        if not channel:
            core_object.log("Attempted to play sfx, but ran out of audio channels!")
            return
        channel = sfx.play(loops, maxtime, fade_ms)
        channel.set_volume(volume * self.global_volume)
        self.current[channel] = TrackInfo(volume, sound_type)
        return channel
        
    def get_channels(self, sound : pygame.mixer.Sound) -> list[pygame.mixer.Channel]:
        """Gets all the channels that are playing a specific sound."""
        channels : list[pygame.mixer.Channel] = []
        for channel in self.current:
            if channel.get_sound() == sound:
                channels.append(channel)
        return channels
    
    def get_all_type(self, t : str) -> list[pygame.mixer.Channel]:
        """Get all channels that are playing a sound of a specific type."""
        channels : list[AnyChannel] = []
        for channel in self.current:
            info = self.current[channel]
            if info.type == t:
                channels.append(channel)
        
        return channels

    def stop_channel(self, channel : pygame.mixer.Channel):
        """Stop a currently playing channel."""
        channel.stop()
        if channel in self.current:
            self.current.pop(channel)
    
    def stop_sound(self, sound : pygame.mixer.Sound):
        """Stop a currently playing track."""
        to_remove : list[pygame.mixer.Channel] = []
        for channel in self.current:
            if channel.get_sound() == sound:
                to_remove.append(channel)
        
        for channel in to_remove:
            self.current.pop(channel)
            channel.stop()
        
        sound.stop()
    
    def stop_all_type(self, t : str):
        """Stop all sounds of a specific type."""
        to_remove : list[AnyChannel] = []
        for channel in self.current:
            info = self.current[channel]
            if info.type == t:
                to_remove.append(channel)
        
        for channel in to_remove:
            self.stop_channel(channel)
    
    def stop_all_music(self):
        """Stop all sounds of type "Music".
        Equivalent to stop_all_type("Music")."""
        self.stop_all_type(self.sound_types.music)

    def stop_all(self):
        """Stops all currently playing sounds."""
        for channel in self.current:
            channel.stop()
        self.current.clear()
            

    def update(self):
        to_remove : list[AnyChannel] = []
        for channel in self.current:
            if isinstance(channel, WebChannel):
                channel._update()
            if not channel.get_busy():
                to_remove.append(channel)
        for channel in to_remove:
            self.current.pop(channel)   


class TrackInfo:
    def __init__(self, volume : float, sound_type : str|None = None) -> None:
        self.volume : float = volume
        self.type : str|None = sound_type



def _runtime_hints():
    global Core
    from framework.core.core import Core