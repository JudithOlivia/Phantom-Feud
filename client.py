import pygame 
import json
import os
import sys
import threading

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
        