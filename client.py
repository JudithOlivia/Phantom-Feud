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
            
    def handle_server_message(self, message):
        """Process messages from server"""
        msg_type = message.ger("type")
        data = message.get("data", {})
        
        if msg_type == "init":
            self.my_id = data.get("id")
            self.my_character = data.get("character", self.my_character)
            print(f"Initialized as player {self.my_id} with character {self.my_character}")
            
            if self.my_character not in self.character_animations:
                self.character_animations[self.my_character] = self.load_character_animations(self.my_character)
                
        elif msg_type == "player_joined":
            player_id = data.get("id")
            character = data.get("character", "Default")
            
            if character not in self.character_animations:
                self.character_animations[character] = self.load_character_animations(character)
                
            self.other_players[player_id] = {
                'id': player_id,
                'character': character,
                'x': data.get('x', 400),
                'y': data.get('y', 400),
                'health': 100,
                'max_health': 100,
                'direction': 'down',
                'action': 'idle'
            }
            print(f"Player {player_id} ({character}) joined")
            
        elif msg_type == "player_left":
            player_id = data.get("id")
            if player_id in self.other_players:
                del self.other_players[player_id]
                print(f"Player {player_id} left")
                
        elif msg_type == "player_moved":
            player_id = data.get("id")
            if player_id in self.other_players:
                self.other_players[player_id]['x'] = data.get('x')
                self.other_players[player_id]['y'] = data.get('y')
                self.other_players[player_id]['direction'] = data.get('direction')
                
        elif msg_type == "player_attacked":
            player_id = data.get("id")
            if player_id in self.other_players:
                self.other_players[player_id]['action'] = 'attack'
                
        elif msg_type == "player_hit":
            target_id = data.get("target_id")
            damage = data.get("damage")
            new_health = data.get("new_health")
            
            if target_id == self.my_id:
                self.local_health = new_health 
                self.local_action = "hurt"
                self.play_sound('hit')
            elif target_id in self.other_players:
                self.other_players[target_id]['health'] = new_health
                self.other_players[target_id]['action'] = 'hurt'
                
        elif msg_type == "player_died":
            player_id = data.get("id")
            if player_id == self.my_id:
                self.local_action = "dead"
                self.play_sound('dead')
            elif player_id in self.other_players:
                self.other_players[player_id]['action'] = 'dead'
                
        elif msg_type == "player_died":
            player_id = data.get("id")
            if player_id == self.my_id:
                self.local_action = "dead"
                self.play_sound('dead')
            elif player_id in self.other_players:
                self.other_players[player_id]['action'] = 'dead'
                
    def character_select_screen(self):
        """Show character selection menu"""
        selecting = True
        
        while selecting and self.running:
            self.screen.fill(BLACK)
            
            try:
                title = self.big_font.render("PHANTOM FEUD", True, WHITE)
            except:
                title = self.font.render("PHANTOM FEUD", True, WHITE)
            title_rect = title.get_rect(center=(SCREEN_WIDTH//2, 100))
            self.screen.blit(title, title_rect)
            
            instr = self.font.render("Select Your Warrior", True, GRAY)
            instr_rect = instr.get_rect(center=(SCREEN_WIDTH//2, 180))
            self.screen.blit(instr, instr_rect)
            
            char_name = self.available_characters[self.selected_character_index]
            
            if char_name not in self.character_animations:
                self.character_animations[char_name] = self.load_character_animations(char_name)
                
            preview_anim = self.character_animations[char_name]
            if 'idle' in preview_anim and preview_anim['idle']:
                preview_img = preview_anim['idle'][0]
                preview_rect = preview_img.get_rect(center=(SCREEN_WIDTH//2, 350))
                self.screen.blit(preview_img, preview_rect)
                
            name_text = self.font.render(char_name.upper().replace('_', ' '), True, WHITE)
            name_rect = name_text.get_rect(center=(SCREEN_WIDTH//2, 450))
            self.screen.blit(name_text, name_rect)
            
            controls = self.font.render("LEFT / RIGHT to change     ENTER to fight", True, GRAY)
            controls_rect = controls.get_rect(center=(SCREEN_WIDTH//2, 650))
            self.screen.blit(controls, controls_rect)
            
            server_text = self.font.render(f"Connecting to: {self.server_ip}:{self.server_port}", True, BLUE)
            server_rect = server_text.get_rect(center=(SCREEN_WIDTH//2, 720))
            self.screen.blit(server_text, server_rect)
            
            pygame.display.flip()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    return None
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        self.selected_character_index = (self.selected_character_index - 1) % len(self.available_characters)
                    elif event.key == pygame.K_RIGHT:
                        self.selected_character_index = (self.selected_character_index + 1) % len(self.available_characters)
                    elif event.key == pygame.K_RETURN:
                        selecting = False
            
            self.clock.tick(FPS)
        
        return self.available_characters[self.selected_character_index]
    
    def run_game(self):
        """Main game loop"""
        # Connect to server
        if not self.connect_to_server():
            print("Failed to connect to server. Make sure server.py is running.")
            return
        
        selected_character = self.character_select_screen()
        if not selected_character:
            return
        
        self.send_message("character_select", {"character": selected_character})
        self.my_character = selected_character
        
        receive_thread = threading.thread(target=self.recieve_messages)
        receive_thread.daemon = True
        receive_thread.start()
        
        timeout = 50
        while self.my_id is None and timeout > 0 and self.running:
            pygame.time.wait(100)
            timeout -= 1
            
        if self.my_id is None:
            print("Failed to get player ID from server")
            return 
        
        print("Game starting!")
        
        game_running = True
        current_time = 0
        
        while game_running and self.running:
            current_time = pygame.time.get_ticks() / 1000.0
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    game_running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE or event.key == pygame.K_f:
                        if self.attack_cooldown <= 0 and self.local_action != "dead":
                            self.local_action = "attack"
                            self.attack_cooldown = 30
                            self.send_message("attack", {})
                            self.play_sound('hit')
                        elif event.key == pygame.K_e:
                            if self.special_cooldown <= 0 and self.local_action != "dead":
                                ability = None
                            if self.my_character in ["Samurai", "Shinobi", "Default"]:
                                ability = "shield"
                            elif self.my_character in ["Converted_Vampire"]:
                                ability = "protect"
                            elif self.my_character in ["Gotoku", "Onre", "Yurei"]:
                                ability = "scream"
                            elif self.my_character in ["Onre"]:
                                ability = "flight"
                            elif self.my_character in ["Countess_Vampire", "Yurei"]:
                                ability = "charge"
                            elif self.my_character in ["Countess_Vampire"]:
                                ability = "blood_charge"
                            if ability:
                                self.local_action = ability
                                self.special_cooldown = 120
                                self.send_message("special", {"ability": ability})
                                if ability in ['protect', 'shield']:
                                    self.play_sound('protect')
            
            keys = pygame.key.get_pressed()
            dx = 0
            dy = 0
            move_speed = 5
            
            if keys[pygame.K_w] or keys[pygame.K_UP]:
                dy = -move_speed
                self.local_direction = "up"
            if keys[pygame.K_s] or keys[pygame.K_DOWN]:
                dy = move_speed
                self.local_direction = "down"
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                dx = -move_speed
                self.local_direction = "left"
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                dx = move_speed
                self.local_direction = "right"
                
            if (dx != 0 or dy != 0) and self.local_action not in ["attack", "hurt", "dead"]:
                if abs(dx) + abs(dy) > move_speed:
                    if self.local_action != "run":
                        self.local_action = "run"
                else:
                    if self.local_action != "walk":
                        self.local_action = "walk"
                        
                if current_time - self.last_position_send > self.position_send_delay:
                    self.send_message("movement", {
                        "x": self.local_x,
                        "y": self.local_y,
                        "direction": self.local_direction
                    })
                    self.last_position_send = current_time
                    
            else:
                if self.local_action not in ["attack", "hurt", "dead"] and self.local_action not in ["run", "walk"]:
                    self.local_action = "idle"
                    
            if dx != 0 or dy != 0:
                self.local_x += dx
                self.local_y += dy
                self.local_x = max(50, min(SCREEN_WIDTH - 50, self.local_x))
                self.local_y = max(50, min(SCREEN_HEIGHT - 50, self.local_y))
                
            if self.attack_cooldown > 0:
                self.attack_cooldown -= 1
                if self.attack_cooldown == 0 and self.local_action == "attack":
                    self.local_action = "idle"
                    
            if self.special_cooldown > 0:
                self.special_cooldown -= 1
                
            if current_time - self.last_animation_update > self.animation_speed:
                self.last_animation_update = current_time
                self.current_animation_frame = (self.current_animation_frame + 1) % 6
                
            self.draw_game()
            
            pygame.display.flip()
            self.clock.tick(FPS)
            
        self.connected = False
        if self.socket:
            self.socket.close()
                                    