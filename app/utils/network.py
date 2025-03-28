"""
Network utilities for AppStream
"""

import socket
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def get_local_ip() -> str:
    """
    Get the local IP address of the machine

    Returns:
        str: Local IP address
    """
    try:
        # Create a socket to determine the local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Doesn't need to be reachable
        s.connect(('8.8.8.8', 1))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception as e:
        logger.error(f"Error getting local IP: {e}")
        return "127.0.0.1"

def setup_network() -> None:
    """
    Initialize network settings for the application
    """
    logger.info(f"Local IP address: {get_local_ip()}")
    # Additional network setup can be added here

def create_server_socket(port: int = 5000, host: str = '') -> Optional[socket.socket]:
    """
    Create a server socket for listening to incoming connections

    Args:
        port (int): Port number to listen on
        host (str): Host address to bind to (empty string means all interfaces)

    Returns:
        Optional[socket.socket]: Server socket or None if creation failed
    """
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((host, port))
        server_socket.listen(5)
        logger.info(f"Server socket created on {host or 'all interfaces'}:{port}")
        return server_socket
    except Exception as e:
        logger.error(f"Failed to create server socket: {e}")
        return None

def connect_to_remote(host: str, port: int = 5000) -> Optional[socket.socket]:
    """
    Connect to a remote host

    Args:
        host (str): Remote host address
        port (int): Remote port number

    Returns:
        Optional[socket.socket]: Client socket or None if connection failed
    """
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((host, port))
        logger.info(f"Connected to remote host {host}:{port}")
        return client_socket
    except Exception as e:
        logger.error(f"Failed to connect to {host}:{port}: {e}")
        return None