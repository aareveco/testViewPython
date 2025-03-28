"""
Remote control command protocol for AppStream
"""

import logging
import json
from enum import Enum
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class CommandType(Enum):
    """Types of remote control commands"""
    MOUSE_MOVE = 1
    MOUSE_CLICK = 2
    MOUSE_DOWN = 3
    MOUSE_UP = 4
    MOUSE_SCROLL = 5
    KEY_PRESS = 6
    KEY_DOWN = 7
    KEY_UP = 8
    TYPE_TEXT = 9
    HOTKEY = 10

class RemoteCommand:
    """Class representing a remote control command"""
    
    def __init__(self, command_type: CommandType, params: Dict[str, Any]):
        """
        Initialize a remote command
        
        Args:
            command_type (CommandType): Type of command
            params (Dict[str, Any]): Command parameters
        """
        self.command_type = command_type
        self.params = params
    
    def to_json(self) -> str:
        """
        Convert the command to JSON
        
        Returns:
            str: JSON representation of the command
        """
        data = {
            'type': self.command_type.value,
            'params': self.params
        }
        return json.dumps(data)
    
    @classmethod
    def from_json(cls, json_str: str) -> Optional['RemoteCommand']:
        """
        Create a command from JSON
        
        Args:
            json_str (str): JSON representation of the command
            
        Returns:
            Optional[RemoteCommand]: The command, or None if parsing failed
        """
        try:
            data = json.loads(json_str)
            command_type = CommandType(data['type'])
            params = data['params']
            return cls(command_type, params)
        except Exception as e:
            logger.error(f"Error parsing remote command: {e}")
            return None
    
    @classmethod
    def create_mouse_move(cls, x: int, y: int, relative: bool = False) -> 'RemoteCommand':
        """
        Create a mouse move command
        
        Args:
            x (int): X coordinate
            y (int): Y coordinate
            relative (bool): If True, move relative to current position
            
        Returns:
            RemoteCommand: The command
        """
        params = {
            'x': x,
            'y': y,
            'relative': relative
        }
        return cls(CommandType.MOUSE_MOVE, params)
    
    @classmethod
    def create_mouse_click(cls, button: str = 'left', double: bool = False) -> 'RemoteCommand':
        """
        Create a mouse click command
        
        Args:
            button (str): Mouse button ('left', 'right', 'middle')
            double (bool): If True, perform a double-click
            
        Returns:
            RemoteCommand: The command
        """
        params = {
            'button': button,
            'double': double
        }
        return cls(CommandType.MOUSE_CLICK, params)
    
    @classmethod
    def create_mouse_down(cls, button: str = 'left') -> 'RemoteCommand':
        """
        Create a mouse down command
        
        Args:
            button (str): Mouse button ('left', 'right', 'middle')
            
        Returns:
            RemoteCommand: The command
        """
        params = {
            'button': button
        }
        return cls(CommandType.MOUSE_DOWN, params)
    
    @classmethod
    def create_mouse_up(cls, button: str = 'left') -> 'RemoteCommand':
        """
        Create a mouse up command
        
        Args:
            button (str): Mouse button ('left', 'right', 'middle')
            
        Returns:
            RemoteCommand: The command
        """
        params = {
            'button': button
        }
        return cls(CommandType.MOUSE_UP, params)
    
    @classmethod
    def create_mouse_scroll(cls, clicks: int) -> 'RemoteCommand':
        """
        Create a mouse scroll command
        
        Args:
            clicks (int): Number of clicks to scroll (positive for up, negative for down)
            
        Returns:
            RemoteCommand: The command
        """
        params = {
            'clicks': clicks
        }
        return cls(CommandType.MOUSE_SCROLL, params)
    
    @classmethod
    def create_key_press(cls, key: str) -> 'RemoteCommand':
        """
        Create a key press command
        
        Args:
            key (str): Key to press
            
        Returns:
            RemoteCommand: The command
        """
        params = {
            'key': key
        }
        return cls(CommandType.KEY_PRESS, params)
    
    @classmethod
    def create_key_down(cls, key: str) -> 'RemoteCommand':
        """
        Create a key down command
        
        Args:
            key (str): Key to press
            
        Returns:
            RemoteCommand: The command
        """
        params = {
            'key': key
        }
        return cls(CommandType.KEY_DOWN, params)
    
    @classmethod
    def create_key_up(cls, key: str) -> 'RemoteCommand':
        """
        Create a key up command
        
        Args:
            key (str): Key to release
            
        Returns:
            RemoteCommand: The command
        """
        params = {
            'key': key
        }
        return cls(CommandType.KEY_UP, params)
    
    @classmethod
    def create_type_text(cls, text: str) -> 'RemoteCommand':
        """
        Create a type text command
        
        Args:
            text (str): Text to type
            
        Returns:
            RemoteCommand: The command
        """
        params = {
            'text': text
        }
        return cls(CommandType.TYPE_TEXT, params)
    
    @classmethod
    def create_hotkey(cls, keys: list) -> 'RemoteCommand':
        """
        Create a hotkey command
        
        Args:
            keys (list): Keys to press together
            
        Returns:
            RemoteCommand: The command
        """
        params = {
            'keys': keys
        }
        return cls(CommandType.HOTKEY, params)
