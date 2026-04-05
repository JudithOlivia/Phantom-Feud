import pygame 
import json
import os
import sys
import threading
import socket

pygame.init()

SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 100, 255)
GRAY = (100, 100, 100)

class PhantomFeudClient:
    def __init__(self, server_ip="127.0.0.1", server_port=5555):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        
        pygame.display.set_caption("Phantom Feud")
        self.clock = pygame.time.Clock()
        self.running = True
        
        self.players = {}
        self.other_players = {}
        
        self.socket = None
        self.server_ip = server_ip
        self.server_port = server_port
        self.connected = False
        self.my_id = None
        self.my_character = None
        
        self.local_x = 400
        self.local_y = 400
        self.local_direction = "down"
        self.local_health = 100
        self.local_max_health
        self.local_action = "idle"
        self.local_attack_timer = 0
        
        self.character_animations = {}
        self.current_animation_frame = 0
        self.animation_speed = 0.15
        self.last_animation_update = 0
        
        self.attack_cooldown = 0
        self.special_cooldown = 0
        
        self.available_characters = self.scan_characters()
        self.selected_character_index = 0
        
        try:
            self.font = pygame.font.Font("assets/fonts/medieval.ttf", 24)
            self.big_font = pygame.font.Font("assets/fonts/medieval.ttf", 48)
            
        except:
            self.font = pygame.font.Font(None, 24)
            self.big_font = pygame.font.Font(None, 48)
            
        self.sounds = self.load_sounds()
        
        self.last_position_send = 0
        self.position_send_delay = 0.05
        
    def scan_characters(self):
        """Scan the assets/characters folder for available characters"""
        characters_path = "assets/characters"
        characters = []
        
        if os.path.exists(characters_path):
            for item in os.listdir(characters_path):
                item_path = os.path.join(characters_path, item)
                if os.path.isdir(item_path):
                    characters.append(item)
        
        if not characters:
            characters = ["Default", "Samurai", "Shinobi", "Vampire_Girl", 
                         "Gotoku", "Onre", "Yurei", "Converted_Vampire", "Countess_Vampire"]
        
        return sorted(characters)
    
    def load_sounds(self):
        """Load sound effects from assets/audio folder"""
        sounds = {}
        
        sound_files = {
            'hit': ['female_hurt1.mp3', 'male_hurt3.mp3'],
            'jump': ['jump.mp3'],
            'run': ['running.mp3'],
            'walk': ['walk.mp3'],
            'dead': ['dead.mp3'],
            'protect': ['female_protect.mp3', 'male_protect.mp3'],
        }
        
        audio_path = "assets/audio"
        
        for sound_name, file_names in sound_files.items():
            for file_name in file_names:
                file_path = os.path.join(audio_path, file_name)
                if os.path.exists(file_path):
                    try:
                        sounds[sound_name] = pygame.mixer.Sound(file_path)
                        print(f"Loaded sound: {file_name}")
                        break
                    except Exception as e:
                        print(f"Could not load {file_path}: {e}")
        
        print(f"Loaded {len(sounds)} sounds")
        return sounds
    
    
    def play_sound(self, sound_name):
        """Play a sound effect"""
        if sound_name in self.sounds:
            try:
                self.sounds[sound_name].play()
            except:
                pass
    
    def load_character_animations(self, character_name):
        """Load all animation frames for a character"""
        animations = {}
        character_path = f"assets/characters/{character_name}"
        
        if not os.path.exists(character_path):
            print(f"Character path not found: {character_path}")
            character_path = "assets/characters/Default"
            
            animation_types = {
                'idle': ['Idle.png'],
                'walk': ['Walk.png'],
                'run': ['Run.png'],
                'attack': ['Attack_1.png', 'Attack_2.png', 'Attack_3.png'],
                'hurt': ['Hurt.png'],
                'dead': ['Dead.png'],
                'jump': ['Jump.png'],
                'shield': ['Shield.png'],
                'scream': ['Scream.png'],
                'flight': ['Flight.png'],
                'protect': ['Protect.png'],
                'charge': ['Charge_1.png', 'Charge_2.png', 'Charge_3.png', 'Charge_4.png'],
                'blood_charge': ['Blood_Charge_1.png', 'Blood_Charge_2.png', 'Blood_Charge_3.png', 'Blood_Charge_4.png'],
            }
            
            for anim_name, files in animation_types.items():
                frames = []
            for file in files:
                file_path = os.path.join(character_path, file)
                if os.path.exists(file_path):
                    try:
                        img = pygame.image.load(file_path).convert_alpha()
                        # Scale to reasonable size
                        img = pygame.transform.scale(img, (80, 80))
                        frames.append(img)
                    except Exception as e:
                        pass
                    
                if frames:
                    animations[anim_name] = frames
                    
            if not animations:
                animations['idle'] = [self.create_fallback_surface(character_name)]
                animations['walk'] = [self.create_fallback_surface(character_name)]
                animations['attack'] = [self.create_fallback_surface(character_name)]
            
            print(f"Loaded {len(animations)} animations for {character_name}")
            return animations
        
    def create_fallback_surface(self, character_name):
        """Create a colored rectangle if images can't be loaded"""
        surface = pygame.Surface((60, 60))
        colors = {
            'Samurai': (200, 50, 50),
            'Shinobi': (50, 50, 200),
            'Vampire_Girl': (150, 50, 150),
            'Gotoku': (200, 150, 50),
            'Onre': (100, 50, 100),
            'Yurei': (50, 200, 150),
            'Converted_Vampire': (150, 50, 50),
            'Countess_Vampire': (200, 50, 200),
            'Default': (100, 100, 100)
        }
        color = colors.get(character_name, (100, 100, 150))
        surface.fill(color)
        pygame.draw.rect(surface, WHITE, surface.get_rect(), 2)
        return surface
    
    def connect_to_server(self):
        """Connect to the game server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.server_ip, self.server_port))
            self.connected = True
            print(f"Connected to server at {self.server_ip}:{self.server_port}")
            return True
        except Exception as e:
            print(f"Could not connect to server: {e}")
            return False
        
    def send_message(self, msg_type, data):
        """Send a message to the server"""
        if not self.connected or not self.socket:
            return 
        try:
            message = json.dumps({"type": msg_type, "data": data})
            self.socket.send(message.encode())
        except Exception as e:
            print(f"Send error: {e}")
            self.connected = False
            
    def recieve_messages(self):
        """Background thread to receive messages from server"""
        while self.connected:
            try:
                data = self.socket.recv(4096)
                if not data:
                    break
                message = json.loads(data.decode())
                self.handle_server_message(message)
            except Exception as e:
                print(f"Recieve error: {e}")
                break