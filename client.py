import pygame 
import json
import os
import sys
import threading
import socket

pygame.init()

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 100, 255)
GRAY = (100, 100, 100)
GOLD = (255, 215, 0)

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
        
        self.p1_x = 300
        self.p1_y = 400
        self.p1_direction = "down"
        self.p1_health = 100
        self.p1_max_health = 100
        self.p1_action = "idle"
        self.p1_character = None
        
        self.p2_x = 500
        self.p2_y = 400
        self.p2_direction = "down"
        self.p2_health = 100
        self.p2_max_health = 100
        self.p2_action = "idle"
        self.p2_character = None
        
        self.character_animations = {}
        self.current_animation_frame = 0
        self.animation_speed = 0.15
        self.last_animation_update = 0
        
        self.attack_cooldown_p1 = 0
        self.attack_cooldown_p2 = 0
        self.local_attack_timer = 0
        self.special_cooldown = 0
        
        self.available_characters = self.scan_characters()
        self.selected_character_index = 0
        
        self.sounds = self.load_sounds()
        self.backgrounds = self.load_backgrounds()
        self.selected_background = 0
        self.current_background = None
        
        self.menu_state = "main"
        self.selected_player = None
        self.confirmed_character_p1 = None
        self.confirmed_character_p2 = None
        self.confirmed_background = 0
        
        try:
            self.font = pygame.font.Font("assets/fonts/medieval.ttf", 24)
            self.big_font = pygame.font.Font("assets/fonts/medieval.ttf", 48)
            
        except:
            self.font = pygame.font.Font(None, 24)
            self.big_font = pygame.font.Font(None, 48)
            
        
        self.last_position_send = 0
        self.position_send_delay = 0.05
    
    def draw_main_menu(self):
        """Draw the main menu with 3 options"""
        self.screen.fill(BLACK)
        
        title_font_path = "assets/fonts/second.otf"
        
        try:
            title_img = pygame.image.load(title_font_path).convert_alpha()
            title_img = pygame.transform.scale(title_img, (400, 100))
            title_rect = title_img.get_rect(center=(SCREEN_WIDTH//2, 80))
            self.screen.blit(title_img, title_rect)
        except:
            try: 
                title = self.big_font.render("PHANTOM FEUD", True, GOLD)
            except:
                title = self.font.render("PHANTOM FEUD", True, GOLD)
            title_rect = title.get_rect(center=(SCREEN_WIDTH//2, 80))
            self.screen.blit(title, title_rect)
                
        subtitle = self.font.render("Choose Your Option", True, WHITE)
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH//2, 140))
        self.screen.blit(subtitle, subtitle_rect)
        
        button_width = 250
        button_height = 50
        spacing = 20
        start_y = 220
        
        self.p1_button_rect = pygame.Rect(SCREEN_WIDTH//2 - button_width//2, start_y, button_width, button_height)
        self.p2_button_rect = pygame.Rect(SCREEN_WIDTH//2 - button_width//2, start_y + button_height + spacing, button_width, button_height)
        self.bg_button_rect = pygame.Rect(SCREEN_WIDTH//2 - button_width//2, start_y + (button_height + spacing)*2, button_width, button_height)
        
        self.play_button_rect = pygame.Rect(SCREEN_WIDTH//2 - button_width//2, start_y + (button_height + spacing)*3, button_width, button_height)
        
        mouse_pos = pygame.mouse.get_pos() 
        
        p1_color = (80, 80, 200) if self.p1_button_rect.collidepoint(mouse_pos) else (50, 50, 150)
        pygame.draw.rect(self.screen, p1_color, self.p1_button_rect)
        pygame.draw.rect(self.screen, WHITE, self.p1_button_rect, 2)
        p1_text = self.font.render("PLAYER 1 (Arrow Keys)", True, WHITE)
        p1_text_rect = p1_text.get_rect(center=self.p1_button_rect.center)
        self.screen.blit(p1_text, p1_text_rect)
        
        p2_color = (80,200,80) if self.p2_button_rect.collidepoint(mouse_pos) else (50,150,50)
        pygame.draw.rect(self.screen, p2_color, self.p2_button_rect)
        pygame.draw.rect(self.screen, WHITE, self.p2_button_rect, 2)
        p2_text = self.font.render("PLAYER 2 (WASD)", True, WHITE)
        p2_text_rect = p2_text.get_rect(center=self.p2_button_rect.center)
        self.screen.blit(p2_text, p2_text_rect)
        
        bg_color = (200, 150, 80) if self.bg_button_rect.collidepoint(mouse_pos) else (150, 100, 50)
        pygame.draw.rect(self.screen, bg_color, self.bg_button_rect)
        pygame.draw.rect(self.screen, WHITE, self.bg_button_rect, 2)
        bg_text = self.font.render("BACKGROUND", True, WHITE)
        bg_text_rect = bg_text.get_rect(center=self.bg_button_rect.center)
        self.screen.blit(bg_text, bg_text_rect)
        
        play_color = (0, 150, 0) if self.play_button_rect.collidepoint(mouse_pos) else (0, 100, 0)
        pygame.draw.rect(self.screen, play_color, self.play_button_rect)
        pygame.draw.rect(self.screen, WHITE, self.play_button_rect, 2)
        play_text = self.font.render("PLAY", True, WHITE)
        play_text_rect = play_text.get_rect(center=self.play_button_rect.center)
        self.screen.blit(play_text, play_text_rect)
        
        y_offset = SCREEN_HEIGHT - 100
        if self.confirmed_character_p1:
            p1_display = self.font.render(f"P1: {self.confirmed_character_p1}", True, GRAY)
            self.screen.blit(p1_display, (20, y_offset))
            y_offset += 30
        if self.confirmed_character_p2:
            p2_display = self.font.render(f"P2: {self.confirmed_character_p2}", True, GRAY)
            self.screen.blit(p2_display, (20, y_offset))
            y_offset += 30
        if self.confirmed_background:
            bg_display = self.font.render(f"Arena: Battleground {self.confirmed_background}", True, GRAY)
            self.screen.blit(bg_display, (20, y_offset))
            y_offset += 30
        if self.confirmed_character_p1 and self.confirmed_character_p2 and self.confirmed_background:
            ready_text = self.font.render("READY! Press ENTER to start", True, GREEN)
            ready_rect = ready_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 30))
            self.screen.blit(ready_text, ready_rect)

    def draw_character_select_screen(self):
        """Separate screen for choosing character only"""
        self.screen.fill(BLACK)
        
        title = self.big_font.render(f"{self.selected_player.upper()} SELECT YOUR WARRIOR", True, GOLD)
        title_rect = title.get_rect(center=(SCREEN_WIDTH//2, 60))
        self.screen.blit(title, title_rect)
        
        char_name = self.available_characters[self.selected_character_index]
        
        char_path =  f"assets/characters/{char_name}/main.png"
        if os.path.exists(char_path):
            img = pygame.image.load(char_path).convert_alpha()
            img = pygame.transform.scale(img, (200, 200))
            rect = img.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            self.screen.blit(img, rect)
            
        name_text = self.big_font.render(char_name.upper().replace('_', ' '), True, WHITE)
        name_rect = name_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 130))
        self.screen.blit(name_text, name_rect)
        
        mouse_pos = pygame.mouse.get_pos()
        
        left_rect = pygame.Rect(SCREEN_WIDTH//2 - 150, SCREEN_HEIGHT//2 - 40, 50, 50)
        pygame.draw.rect(self.screen, (100,100,100), left_rect)
        pygame.draw.rect(self.screen, WHITE, left_rect, 2)
        left_text = self.big_font.render("<", True, WHITE)
        self.screen.blit(left_text, left_text.get_rect(center=left_rect.center))
        self.left_arrow_rect = left_rect
        
        right_rect = pygame.Rect(SCREEN_WIDTH//2 + 100, SCREEN_HEIGHT//2 - 40, 50, 50)
        pygame.draw.rect(self.screen, (100,100,100), right_rect)
        pygame.draw.rect(self.screen, WHITE, right_rect, 2)
        right_text = self.big_font.render(">", True, WHITE)
        self.screen.blit(right_text, right_text.get_rect(center=right_rect.center))
        self.right_arrow_rect = right_rect
        
        if self.selected_player == "p1":
            controls_text = self.font.render("Controls: ARROW KEYS", True, GOLD)
        else:
            controls_text = self.font.render("Controls: WASD", True, GOLD)
        controls_rect = controls_text.get_rect(bottomright=(SCREEN_WIDTH - 20, SCREEN_HEIGHT - 20))
        self.screen.blit(controls_text, controls_rect)
        
        ok_rect = pygame.Rect(SCREEN_WIDTH//2 - 60, SCREEN_HEIGHT - 70, 120, 40)
        pygame.draw.rect(self.screen, (0,100,0), ok_rect)
        pygame.draw.rect(self.screen, WHITE, ok_rect, 2)
        ok_text = self.font.render("OK", True, WHITE)
        self.screen.blit(ok_text, ok_text.get_rect(center=ok_rect.center))
        self.ok_rect = ok_rect
        
    def draw_background_select_screen(self):
        """Separate screen for choosing background only"""
        if self.backgrounds:
            self.screen.blit(self.backgrounds[self.selected_background], (0,0))
            
        title = self.big_font.render("SELECT ARENA", True, GOLD)
        title_rect = title.get_rect(center=(SCREEN_WIDTH//2, 60))
        self.screen.blit(title, title_rect)
        
        preview = pygame.transform.scale(self.backgrounds[self.selected_background], (500, 350))
        preview_rect = preview.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
        self.screen.blit(preview, preview_rect)
        
        bg_name = f"BATTLEGROUND {self.selected_background + 1}"
        name_text = self.big_font.render(bg_name, True, WHITE)
        name_rect = name_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 120))
        self.screen.blit(name_text, name_rect)
        
        mouse_pos = pygame.mouse.get_pos()
            
        up_rect = pygame.Rect(SCREEN_WIDTH//2 - 180, SCREEN_HEIGHT//2 - 30, 50, 50)
        pygame.draw.rect(self.screen, (100,100,100), up_rect)
        pygame.draw.rect(self.screen, WHITE, up_rect, 2)
        up_text = self.big_font.render("↑", True, WHITE)
        self.screen.blit(up_text, up_text.get_rect(center=up_rect.center))
        self.up_arrow_rect = up_rect
        
        down_rect = pygame.Rect(SCREEN_WIDTH//2 + 130, SCREEN_HEIGHT//2 - 30, 50, 50)
        pygame.draw.rect(self.screen, (100,100,100), down_rect)
        pygame.draw.rect(self.screen, WHITE, down_rect, 2)
        down_text = self.big_font.render("↓", True, WHITE)
        self.screen.blit(down_text, down_text.get_rect(center=down_rect.center))
        self.down_arrow_rect = down_rect
        
        ok_rect = pygame.Rect(SCREEN_WIDTH//2 - 60, SCREEN_HEIGHT - 70, 120, 40)
        pygame.draw.rect(self.screen, (0,100,0), ok_rect)
        pygame.draw.rect(self.screen, WHITE, ok_rect, 2)
        ok_text = self.font.render("OK", True, WHITE)
        self.screen.blit(ok_text, ok_text.get_rect(center=ok_rect.center))
        self.ok_rect = ok_rect
        
    def handle_menu(self):
        """Main menu loop"""
        while self.menu_state != "done":
            if self.menu_state == "main":
                self.draw_main_menu()
            elif self.menu_state == "character_select":
                self.draw_character_select_screen()
            elif self.menu_state == "background_select":
                self.draw_background_select_screen()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    return None, None, None
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.menu_state == "main":
                        if self.p1_button_rect.collidepoint(event.pos):
                            self.menu_state = "character_select"
                            self.selected_player = "p1"
                        elif self.p2_button_rect.collidepoint(event.pos):
                            self.menu_state = "character_select"
                            self.selected_player = "p2"
                        elif self.bg_button_rect.collidepoint(event.pos):
                            self.menu_state = "background_select"
                        elif self.play_button_rect.collidepoint(event.pos):
                            if self.confirmed_character_p1 and self.confirmed_character_p2 and self.confirmed_background:
                                self.menu_state = "done"
                    elif self.menu_state == "character_select":
                        if hasattr(self, 'ok_rect') and self.ok_rect.collidepoint(event.pos):
                            if self.selected_player == "p1":
                                self.confirmed_character_p1 = self.available_characters[self.selected_character_index]
                                print(f"Saved P1 character: {self.confirmed_character_p1}")
                            else:
                                self.confirmed_character_p2 = self.available_characters[self.selected_character_index]
                                print(f"Saved P2 character: {self.confirmed_character_p2}")
                            self.menu_state = "main"
                        elif hasattr(self, 'left_arrow_rect') and self.left_arrow_rect.collidepoint(event.pos):
                            self.selected_character_index = (self.selected_character_index - 1) % len(self.available_characters)
                        elif hasattr(self, 'right_arrow_rect') and self.right_arrow_rect.collidepoint(event.pos):
                            self.selected_character_index = (self.selected_character_index + 1) % len(self.available_characters)
                    elif self.menu_state == "background_select":
                        if hasattr(self, 'ok_rect') and self.ok_rect.collidepoint(event.pos):
                            self.confirmed_background = self.selected_background + 1
                            self.menu_state = "main"
                        elif hasattr(self, 'up_arrow_rect') and self.up_arrow_rect.collidepoint(event.pos):
                            self.selected_background = (self.selected_background - 1) % len(self.backgrounds)
                        elif hasattr(self, 'down_arrow_rect') and self.down_arrow_rect.collidepoint(event.pos):
                            self.selected_background = (self.selected_background + 1) % len(self.backgrounds)
                
                if event.type == pygame.KEYDOWN:
                    if self.menu_state == "character_select":
                        if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                            self.selected_character_index = (self.selected_character_index - 1) % len(self.available_characters)
                        elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                            self.selected_character_index = (self.selected_character_index + 1) % len(self.available_characters)
                        elif event.key == pygame.K_RETURN:
                            if self.selected_player == "p1":
                                self.confirmed_character_p1 = self.available_characters[self.selected_character_index]
                            else:
                                self.confirmed_character_p2 = self.available_characters[self.selected_character_index]
                            self.menu_state = "main"
                    elif self.menu_state == "background_select":
                        if event.key == pygame.K_UP:
                            self.selected_background = (self.selected_background - 1) % len(self.backgrounds)
                        elif event.key == pygame.K_DOWN:
                            self.selected_background = (self.selected_background + 1) % len(self.backgrounds)
                        elif event.key == pygame.K_RETURN:
                            self.confirmed_background = self.selected_background + 1
                            self.menu_state = "main"
                    elif self.menu_state == "main" and event.key == pygame.K_RETURN:
                        if self.confirmed_character_p1 and self.confirmed_character_p2 and self.confirmed_background:
                            self.menu_state = "done"
            
            pygame.display.flip()
            self.clock.tick(FPS)
    
        return self.confirmed_character_p1, self.confirmed_character_p2, self.confirmed_background
        
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
    
    def load_backgrounds(self):
        """Load all background images from assets/background folder"""
        backgrounds = []
        bg_path = "assets/background"
        
        if os.path.exists(bg_path):
            for i in range(1, 5):
                filename = f"Battleground{i}.png"
                file_path = os.path.join(bg_path, filename)
                if os.path.exists(file_path):
                    try:
                        img = pygame.image.load(file_path).convert()
                        img = pygame.transform.scale(img, (SCREEN_WIDTH, SCREEN_HEIGHT))
                        
                        backgrounds.append(img)
                        print(f"loaded background: {filename}")
                    except Exception as e:
                        print(f"Could not load {filename}: {e}")
        if not backgrounds:
            print("No backgrounds found, using fallback")
            fallback = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            fallback.fill((30, 30, 50))
            backgrounds.append(fallback)
            
        return backgrounds
        
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
            self.socket.send((message + "\n").encode())
        except Exception as e:
            print(f"Send error: {e}")
            self.connected = False
            
    def receive_messages(self):
        """Background thread to receive messages from server"""
        while self.connected:
            try:
                data = self.socket.recv(4096)
                if not data:
                    break
                for line in data.decode().strip().split('\n'):
                    if line:
                        message = json.loads(line)
                        self.handle_server_message(message)
            except Exception as e:
                print(f"Receive error: {e}")
                break
            
    def handle_server_message(self, message):
        """Process messages from server"""
        msg_type = message.get("type")
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
        
    
    def run_game(self):
        """Main game loop"""
        p1_char, p2_char, bg_num = self.handle_menu()
        
        if not p1_char or not p2_char or not bg_num:
            print("Game setup cancelled")
            return
        
        if not self.connect_to_server():
            print("Failed to connect to server. Make sure server.py is running.")
            return
        
        self.current_background = self.backgrounds[bg_num - 1] if self.backgrounds else None
        self.my_character = p1_char
        print(f"Using character: {self.my_character}")
        self.send_message("character_select", {"character": p1_char})
        
        receive_thread = threading.Thread(target=self.receive_messages)
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
        self.p1_character = p1_char
        self.p2_character = p2_char

        if p1_char not in self.character_animations:
            self.character_animations[p1_char] = self.load_character_animations(p1_char)
        if p2_char not in self.character_animations:
            self.character_animations[p2_char] = self.load_character_animations(p2_char)
        
        while game_running and self.running:
            current_time = pygame.time.get_ticks() / 1000.0
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    game_running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:  # Player 1 attack
                        if self.attack_cooldown_p1 <= 0 and self.p1_action != "dead":
                            self.p1_action = "attack"
                            self.attack_cooldown_p1 = 30
                            self.play_sound('hit')
                    elif event.key == pygame.K_f:  # Player 2 attack
                        if self.attack_cooldown_p2 <= 0 and self.p2_action != "dead":
                            self.p2_action = "attack"
                            self.attack_cooldown_p2 = 30
                            self.play_sound('hit')
                    elif event.key == pygame.K_e:
                        if self.special_cooldown <= 0 and self.p1_action != "dead":
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
            move_speed = 5
            
            if keys[pygame.K_UP]:
                self.p1_y -= move_speed
                self.p1_direction = "up"
                self.p1_action = "walk"
            if keys[pygame.K_DOWN]:
                self.p1_y += move_speed
                self.p1_direction = "down"
                self.p1_action = "walk"
            if keys[pygame.K_LEFT]:
                self.p1_x -= move_speed
                self.p1_direction = "left"
                self.p1_action = "walk"
            if keys[pygame.K_RIGHT]:
                self.p1_x += move_speed
                self.p1_direction = "right"
                self.p1_action = "walk"
                
                
            if keys[pygame.K_w]:
                self.p2_y -= move_speed
                self.p2_direction = "up"
                self.p2_action = "walk"
            if keys[pygame.K_s]:
                self.p2_y += move_speed
                self.p2_direction = "down"
                self.p2_action = "walk"
            if keys[pygame.K_a]:
                self.p2_x -= move_speed
                self.p2_direction = "left"
                self.p2_action = "walk"
            if keys[pygame.K_d]:
                self.p2_x += move_speed
                self.p2_direction = "right"
                self.p2_action = "walk"
                
            self.p1_x = max(50, min(SCREEN_WIDTH - 50, self.p1_x))
            self.p1_y = max(50, min(SCREEN_HEIGHT - 50, self.p1_y))
            self.p2_x = max(50, min(SCREEN_WIDTH - 50, self.p2_x))
            self.p2_y = max(50, min(SCREEN_HEIGHT - 50, self.p2_y))
                        
            if self.attack_cooldown_p1 > 0:
                self.attack_cooldown_p1 -= 1
                if self.attack_cooldown_p1 == 0 and self.p1_action == "attack":
                    self.p1_action = "idle"

            if self.attack_cooldown_p2 > 0:
                self.attack_cooldown_p2 -= 1
                if self.attack_cooldown_p2 == 0 and self.p2_action == "attack":
                    self.p2_action = "idle"
                        
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
            
    def draw_game(self):
        """Draw all game elements"""
        if self.current_background:
            self.screen.blit(self.current_background, (0,0))
        else:
            self.screen.fill(BLACK)
        
        self.draw_character(self.p1_x, self.p1_y, self.p1_character, self.p1_action, self.p1_direction)
        self.draw_health_bar(self.p1_x, self.p1_y -60, self.p1_health, self.p1_max_health)
        
        self.draw_character(self.p2_x, self.p2_y, self.p2_character, self.p2_action, self.p2_direction)
        self.draw_health_bar(self.p2_x, self.p2_y - 60, self.p2_health, self.p2_max_health)
        
        p1_label = self.font.render("PLAYER 1", True, WHITE)
        p1_label_rect = p1_label.get_rect(center=(self.p1_x, self.p1_y - 75))
        self.screen.blit(p1_label, p1_label_rect)
        
        p2_label = self.font.render("PLAYER 2", True, WHITE)
        p2_label_rect = p2_label.get_rect(center=(self.p2_x, self.p2_y - 75))
        self.screen.blit(p2_label, p2_label_rect)
        
        try: 
            controls = self.font.render("P1: Arrow Keys | SPACE Attack | P2: WASD | F Attack", True, WHITE)
            controls_rect = controls.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 20))
            self.screen.blit(controls, controls_rect)
        except:
            pass
        
    def draw_character(self, x, y, character_name, action, direction):
        """Draw a character with current animation"""
        if character_name in self.character_animations:
            animations = self.character_animations[character_name]
            
            anim_key = action if action in animations else "idle"
            
            if action in ['shield', 'protect', 'scream', 'flight', 'charge', 'blood_charge']:
                if action in animations:
                    anim_key = action
                elif 'shield' in animations:
                    anim_key = 'shield'
                elif 'protect' in animations:
                    anim_key = 'protect'
                    
            frames = animations.get(anim_key, animations.get('idle', []))
            
            if frames:
                frame_index = self.current_animation_frame % len(frames)
                
                img = frames[frame_index].copy()
                
                if direction == "left":
                    img = pygame.transform.flip(img, True, False)
                    
                rect = img.get_rect(center=(int(x), int(y)))
                self.screen.blit(img, rect)
                
                try:
                    name_text = self.font.render(character_name.replace('_', ' ')[:12], True, WHITE)
                    name_rect = name_text.get_rect(center=(int(x), int(y) - 45))
                    self.screen.blit(name_text, name_rect)
                except:
                    pass
                
                return
            
        color = BLUE if character_name == self.p1_character or character_name == self.p2_character else RED
        pygame.draw.rect(self.screen, color, (int(x) - 25, int(y) - 25, 50, 50))
        pygame.draw.circle(self.screen, WHITE, (int(x), int(y)), 5)
            
        
    def draw_health_bar(self, x, y, current, maximum):
        """Draw health bar above character"""
        bar_width = 70
        bar_height = 8
        health_percent = current / maximum if maximum > 0 else 0
        
        pygame.draw.rect(self.screen, RED, (int(x - bar_width//2), int(y), bar_width, bar_height))
        pygame.draw.rect(self.screen, GREEN, (int(x - bar_width//2), int(y), int(bar_width * health_percent), bar_height))
        
        try: 
            health_text = self.font.render(f"{current}/{maximum}", True, WHITE)
            text_rect = health_text.get_rect(center=(int(x), int(y - 12)))
            self.screen.blit(health_text, text_rect)
        except:
            pass
        
    def draw_large_health_bar(self, x, y, current, maximum):
        """Draw large health bar at screen corner"""
        bar_width = 300
        bar_height = 25
        health_percent = current / maximum if maximum > 0 else 0
        
        pygame.draw.rect(self.screen, RED, (x, y, bar_width, bar_height))
        
        pygame.draw.rect(self.screen, GREEN, (x, y, int(bar_width * health_percent), bar_height))
        
        pygame.draw.rect(self.screen, WHITE, (x, y, bar_width, bar_height), 2)
        
        try:
            health_text = self.font.render(f"HEALTH: {current}/{maximum}", True, WHITE)
            self.screen.blit(health_text, (x+10, y+3))
        except:
            pass
        
def main():
    server_ip = "127.0.0.1"
    if len(sys.argv) > 1:
        server_ip = sys.argv[1]
            
    print(f"Starting Phantom Feud client, connecting to {server_ip}:5555")
        
    client = PhantomFeudClient(server_ip)
    client.run_game()
        
    pygame.quit()
    sys.exit()
        
if __name__ == "__main__":
    main()