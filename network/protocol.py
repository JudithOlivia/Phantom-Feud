import json 
import struct

class MessageType:
    JOIN = 0
    LEAVE = 1
    INIT = 2
    
    PLAYER_MOVED = 3
    PLAYER_ATTACKED = 4
    PLAYER_HIT = 5
    PLAYER_DIED = 6
    
    PLAYER_JOINED = 7
    PLAYER_LEFT = 8
    
    CHARACTER_SELECT = 9
    SPECIAL_ABILITY = 10
    
class protocol:
    @staticmethod
    def encode(msg_type, data):
        """Convert message to bytes for sending"""
        packet = {"type": msg_type, "data": data}
        json_str = json.dumps(packet)
        header = struck.pack("!I". len(json_str))
        return header + json_str.encode()
    
    @staticmethod
    def decode(data):
        """Convert bytes back to message"""
        size = struct.unpack("!I", data[:4][0])
        json_str = data[4:4+size].decode()
        return json.loads(json_str)
    