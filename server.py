import socket 
import threading 
import json
import time
from collections import OrderedDict

class GameServer:
    def __init__(self, host='0.0.0.0', port=5555):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        self.server.bind((host, port))
        self.server.listen(4)

        self.players = OrderedDict()
        self.player_id_counter = 0
        self.game_loop_running = True
        self.arena_width = 1200
        self.arena_height = 800

        print(f"Server running on port {port}")

    def broadcast(self, message_type, data, exclude_socket=None):
        """Send message to all connected players"""
        message = json.dumps({"type": message_type, "data": data}).encode()
        for player_id, player_info in list(self.players.items()):
            if exclude_socket != player_info['socket']:
                try:
                    player_info['socket'].send(message)
                except:
                    pass

    def handle_client(self, client_socket, address):
        """Handle a single client connection"""
        player_id = self.player_id_counter
        self.player_id_counter += 1

        try:
            data = client_socket.recv(4096).decode()
            selection = json.loads(data)
            character = selection.get('character', 'Default')
        except:
            character = 'Default'

        player_info = {
            'id': player_id,
            'socket': client_socket,
            'address': address,
            'character': character,
            'x': 400 + (player_id * 200),
            'y': 400,
            'health': 100,
            'max_health': 100,
            'attack_cooldown': 0,
            'is_attacking': False,
            'attack_frame': 0,
            'direction': 'down',
            'last_update': time.time()
        }

        self.players[player_id] = player_info

        client_socket.send(json.dumps({
            "type": "init",
            "data": {"id": player_id, "character": character}
        }).encode())

        self.broadcast("player_joined", {
            "id": player_id,
            "character": character,
            "x": player_info['x'],
            "y": player_info['y']
        })

        print(f"Player {player_id} ({character}) connected from {address}")

        try:
            while True:
                data = client_socket.recv(4096)
                if not data:
                    break
                    
                message = json.loads(data.decode())
                msg_type = message.get("type")
                msg_data = message.get("data", {})
                
                if msg_type == "movement":
                    player_info['x'] = msg_data.get('x', player_info['x'])
                    player_info['y'] = msg_data.get('y', player_info['y'])
                    player_info['direction'] = msg_data.get('direction', player_info['direction'])
                    
                    self.broadcast("player_moved", {
                        "id": player_id,
                        "x": player_info['x'],
                        "y": player_info['y'],
                        "direction": player_info['direction']
                    }, exclude_socket=client_socket)
                    
                elif msg_type == "attack":
                    if player_info['attack_cooldown'] <= 0:
                        player_info['attack_cooldown'] = 30
                        player_info['is_attacking'] = True
                        player_info['attack_frame'] = 0
                        
                        self.broadcast("player_attacked", {
                            "id": player_id,
                            "direction": player_info['direction']
                        })
                        
                        self.check_hits(player_id)
                        
                elif msg_type == "special":
                    ability = msg_data.get('ability')
                    self.handle_special_ability(player_id, ability)
                    
        except Exception as e:
            print(f"Error with player {player_id}: {e}")
        finally:
            del self.players[player_id]
            self.broadcast("player_left", {"id": player_id})
            client_socket.close()
            print(f"Player {player_id} disconnected")
    
    def check_hits(self, attacker_id):
        """Check if attacker hit any other player"""
        attacker = self.players[attacker_id]
        attack_range = 70
        damage = 20
        
        hitbox = {
            'x': attacker['x'],
            'y': attacker['y'],
            'width': attack_range,
            'height': attack_range
        }
        
        if attacker['direction'] == 'right':
            hitbox['x'] = attacker['x']
            hitbox['y'] = attacker['y'] - 30
            hitbox['width'] = attack_range
            hitbox['height'] = 60
        elif attacker['direction'] == 'left':
            hitbox['x'] = attacker['x'] - attack_range
            hitbox['y'] = attacker['y'] - 30
            hitbox['width'] = attack_range
            hitbox['height'] = 60
        elif attacker['direction'] == 'down':
            hitbox['x'] = attacker['x'] - 30
            hitbox['y'] = attacker['y']
            hitbox['width'] = 60
            hitbox['height'] = attack_range
        else:
            hitbox['x'] = attacker['x'] - 30
            hitbox['y'] = attacker['y'] - attack_range
            hitbox['width'] = 60
            hitbox['height'] = attack_range
        
        for victim_id, victim in self.players.items():
            if victim_id == attacker_id:
                continue
                
            victim_center_x = victim['x']
            victim_center_y = victim['y']
            
            in_range = (hitbox['x'] < victim_center_x < hitbox['x'] + hitbox['width'] and
                       hitbox['y'] < victim_center_y < hitbox['y'] + hitbox['height'])
            
            if in_range:
                new_health = victim['health'] - damage
                victim['health'] = max(0, new_health)
                
                self.broadcast("player_hit", {
                    "target_id": victim_id,
                    "damage": damage,
                    "new_health": victim['health'],
                    "attacker_id": attacker_id
                })
                
                if victim['health'] <= 0:
                    self.broadcast("player_died", {"id": victim_id, "killer_id": attacker_id})
    
    def handle_special_ability(self, player_id, ability):
        """Handle special abilities unique to each character"""
        player = self.players[player_id]
        
        if ability == "shield" or ability == "protect":
            self.broadcast("player_ability", {
                "id": player_id,
                "ability": "shield",
                "active": True
            })
            
        elif ability == "scream":
            self.broadcast("player_ability", {
                "id": player_id,
                "ability": "scream"
            })
            
        elif ability == "flight":
            self.broadcast("player_ability", {
                "id": player_id,
                "ability": "flight"
            })
            
        elif ability == "charge":
            self.broadcast("player_ability", {
                "id": player_id,
                "ability": "charge"
            })
    
    def run(self):
        """Main server loop - accept connections"""
        print("Phantom Feud Server Running...")
        print("Waiting for players...")
        
        while self.game_loop_running:
            try:
                client_socket, address = self.server.accept()
                thread = threading.Thread(target=self.handle_client, args=(client_socket, address))
                thread.daemon = True
                thread.start()
            except:
                pass

if __name__ == "__main__":
    server = GameServer()
    try:
        server.run()
    except KeyboardInterrupt:
        print("\nServer shutting down...")
