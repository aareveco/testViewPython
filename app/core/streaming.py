"""
Streaming functionality for AppStream
"""

import logging
import cv2
import numpy as np
import socket
import threading
import time
import pickle
import struct
import json
from typing import Tuple, Callable, Dict, Any, Optional

from app.core.screen_capture import ScreenCapture
from app.core.remote_control import RemoteControl
from app.core.remote_command import RemoteCommand, CommandType
from app.utils.ngrok_service import NgrokService

logger = logging.getLogger(__name__)

class StreamServer:
    """Class for streaming screen content to clients"""

    def __init__(self, host: str = '', port: int = 5000, use_ngrok: bool = False):
        """
        Initialize the stream server

        Args:
            host (str): Host address to bind to (empty string means all interfaces)
            port (int): Port number to listen on
            use_ngrok (bool): Whether to use ngrok for public access
        """
        self.host = host
        self.port = port
        self.server_socket = None
        self.connections = []
        self.running = False
        self.screen_capture = ScreenCapture()
        self.remote_control = RemoteControl()
        self.quality = 50  # JPEG compression quality (0-100)
        self.fps_limit = 30  # Maximum frames per second
        self.frame_time = 1.0 / self.fps_limit
        self.last_frame_time = 0

        # Command socket for remote control
        self.command_socket = None
        self.command_port = port + 1  # Use the next port for commands

        # ngrok settings
        self.use_ngrok = use_ngrok
        self.ngrok_service = NgrokService() if use_ngrok else None
        self.public_url = None
        self.public_command_url = None

        logger.info(f"Stream server initialized with host={host}, port={port}, command_port={self.command_port}, use_ngrok={use_ngrok}")

    def start(self) -> bool:
        """
        Start the streaming server

        Returns:
            bool: True if server started successfully, False otherwise
        """
        if self.running:
            logger.warning("Server is already running")
            return False

        try:
            # Start the video streaming socket
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)

            # Start the command socket for remote control
            self.command_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.command_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.command_socket.bind((self.host, self.command_port))
            self.command_socket.listen(5)

            self.running = True

            # Start ngrok tunnels if enabled
            if self.use_ngrok and self.ngrok_service:
                # Start tunnel for video streaming
                self.public_url = self.ngrok_service.start_tunnel(
                    self.port, "video", "tcp", fallback_to_http=True
                )

                # Start tunnel for commands
                self.public_command_url = self.ngrok_service.start_tunnel(
                    self.command_port, "command", "tcp", fallback_to_http=True
                )

                if not self.public_url or not self.public_command_url:
                    logger.error("Failed to start ngrok tunnels")
                    self.stop()
                    return False

                # Check if we're using HTTP or TCP
                video_protocol = "HTTP" if "http" in str(self.public_url).lower() else "TCP"
                command_protocol = "HTTP" if "http" in str(self.public_command_url).lower() else "TCP"

                logger.info(f"ngrok tunnels established: {self.public_url} ({video_protocol}) and {self.public_command_url} ({command_protocol})")

            # Start the connection acceptance thread for video streaming
            self.accept_thread = threading.Thread(target=self._accept_connections)
            self.accept_thread.daemon = True
            self.accept_thread.start()

            # Start the command acceptance thread for remote control
            self.command_thread = threading.Thread(target=self._accept_commands)
            self.command_thread.daemon = True
            self.command_thread.start()

            logger.info(f"Stream server started on {self.host or 'all interfaces'}:{self.port} (video) and {self.command_port} (commands)")
            return True
        except Exception as e:
            logger.error(f"Failed to start stream server: {e}")
            return False

    def stop(self) -> None:
        """Stop the streaming server"""
        self.running = False

        # Close all client connections
        for conn in self.connections:
            try:
                conn.close()
            except:
                pass
        self.connections = []

        # Close the server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
            self.server_socket = None

        # Close the command socket
        if self.command_socket:
            try:
                self.command_socket.close()
            except:
                pass
            self.command_socket = None

        # Stop ngrok tunnels if they were started
        if self.use_ngrok and self.ngrok_service:
            self.ngrok_service.stop_all_tunnels()
            self.public_url = None
            self.public_command_url = None
            logger.info("ngrok tunnels stopped")

        logger.info("Stream server stopped")

    def set_quality(self, quality: int) -> None:
        """
        Set the streaming quality

        Args:
            quality (int): JPEG compression quality (0-100)
        """
        self.quality = max(0, min(100, quality))
        logger.info(f"Stream quality set to {self.quality}")

    def set_fps_limit(self, fps: int) -> None:
        """
        Set the maximum frames per second

        Args:
            fps (int): Maximum frames per second
        """
        self.fps_limit = max(1, fps)
        self.frame_time = 1.0 / self.fps_limit
        logger.info(f"FPS limit set to {self.fps_limit}")

    def _accept_connections(self) -> None:
        """Thread function to accept client connections for video streaming"""
        logger.info("Starting video connection acceptance thread")

        while self.running:
            try:
                client_socket, addr = self.server_socket.accept()
                logger.info(f"New video connection from {addr}")

                # Start a new thread to handle this client
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, addr)
                )
                client_thread.daemon = True
                client_thread.start()

                self.connections.append(client_socket)
            except Exception as e:
                if self.running:
                    logger.error(f"Error accepting video connection: {e}")
                time.sleep(0.1)

    def _accept_commands(self) -> None:
        """Thread function to accept client connections for remote control commands"""
        logger.info("Starting command acceptance thread")

        while self.running:
            try:
                client_socket, addr = self.command_socket.accept()
                logger.info(f"New command connection from {addr}")

                # Start a new thread to handle this client's commands
                command_thread = threading.Thread(
                    target=self._handle_commands,
                    args=(client_socket, addr)
                )
                command_thread.daemon = True
                command_thread.start()
            except Exception as e:
                if self.running:
                    logger.error(f"Error accepting command connection: {e}")
                time.sleep(0.1)

    def _handle_commands(self, client_socket: socket.socket, address: Tuple[str, int]) -> None:
        """Thread function to handle remote control commands from a client"""
        logger.info(f"Starting command handler for {address}")

        try:
            buffer = ""
            while self.running:
                # Receive data
                data = client_socket.recv(4096).decode('utf-8')
                if not data:
                    break

                # Add to buffer and process complete commands
                buffer += data

                # Process commands (assuming each command ends with a newline)
                while '\n' in buffer:
                    # Extract a command
                    command_str, buffer = buffer.split('\n', 1)

                    # Parse the command
                    try:
                        command = RemoteCommand.from_json(command_str)
                        if command:
                            self._execute_command(command)
                    except Exception as e:
                        logger.error(f"Error processing command: {e}")
        except Exception as e:
            logger.error(f"Error handling commands from {address}: {e}")
        finally:
            try:
                client_socket.close()
            except:
                pass
            logger.info(f"Command connection from {address} closed")

    def _execute_command(self, command: RemoteCommand) -> None:
        """Execute a remote control command"""
        try:
            if command.command_type == CommandType.MOUSE_MOVE:
                self.remote_control.move_mouse(
                    command.params['x'],
                    command.params['y'],
                    command.params.get('relative', False)
                )
            elif command.command_type == CommandType.MOUSE_CLICK:
                self.remote_control.click_mouse(
                    command.params.get('button', 'left'),
                    command.params.get('double', False)
                )
            elif command.command_type == CommandType.MOUSE_DOWN:
                self.remote_control.mouse_down(
                    command.params.get('button', 'left')
                )
            elif command.command_type == CommandType.MOUSE_UP:
                self.remote_control.mouse_up(
                    command.params.get('button', 'left')
                )
            elif command.command_type == CommandType.MOUSE_SCROLL:
                self.remote_control.scroll_mouse(
                    command.params['clicks']
                )
            elif command.command_type == CommandType.KEY_PRESS:
                self.remote_control.press_key(
                    command.params['key']
                )
            elif command.command_type == CommandType.KEY_DOWN:
                self.remote_control.key_down(
                    command.params['key']
                )
            elif command.command_type == CommandType.KEY_UP:
                self.remote_control.key_up(
                    command.params['key']
                )
            elif command.command_type == CommandType.TYPE_TEXT:
                self.remote_control.type_text(
                    command.params['text']
                )
            elif command.command_type == CommandType.HOTKEY:
                self.remote_control.hotkey(
                    *command.params['keys']
                )
            else:
                logger.warning(f"Unknown command type: {command.command_type}")
        except Exception as e:
            logger.error(f"Error executing command: {e}")

    def _handle_client(self, client_socket: socket.socket, address: Tuple[str, int]) -> None:
        """
        Thread function to handle a client connection

        Args:
            client_socket (socket.socket): Client socket
            address (Tuple[str, int]): Client address
        """
        logger.info(f"Starting client handler for {address}")

        try:
            while self.running:
                # Limit the frame rate
                current_time = time.time()
                if current_time - self.last_frame_time < self.frame_time:
                    time.sleep(0.001)  # Small sleep to prevent CPU hogging
                    continue

                # Capture the screen
                frame = self.screen_capture.capture_screen()
                if frame is None:
                    logger.warning("Failed to capture screen")
                    time.sleep(0.1)
                    continue

                # Convert to BGR format (if not already)
                if frame.shape[2] == 4:  # RGBA
                    frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)

                # Compress the frame
                _, encoded_frame = cv2.imencode(
                    '.jpg',
                    frame,
                    [cv2.IMWRITE_JPEG_QUALITY, self.quality]
                )

                # Serialize the frame
                data = pickle.dumps(encoded_frame)

                # Send the frame size followed by the frame data
                message_size = struct.pack("L", len(data))
                client_socket.sendall(message_size + data)

                self.last_frame_time = current_time
        except Exception as e:
            logger.error(f"Error handling client {address}: {e}")
        finally:
            # Clean up
            try:
                client_socket.close()
                if client_socket in self.connections:
                    self.connections.remove(client_socket)
            except:
                pass
            logger.info(f"Client {address} disconnected")


class StreamClient:
    """Class for receiving and displaying streamed screen content"""

    def __init__(self, callback: Callable[[np.ndarray], None]):
        """
        Initialize the stream client

        Args:
            callback (Callable[[np.ndarray], None]): Function to call with received frames
        """
        self.callback = callback
        self.client_socket = None
        self.command_socket = None
        self.running = False
        self.data = b""
        self.payload_size = struct.calcsize("L")
        self.host = None
        self.port = None

        logger.info("Stream client initialized")

    def connect(self, host: str, port: int = 5000, command_port: Optional[int] = None) -> bool:
        """
        Connect to a streaming server

        Args:
            host (str): Server host address or ngrok URL
            port (int): Server port number (ignored if host is an ngrok URL with port)
            command_port (Optional[int]): Command port number (if None, port+1 is used)

        Returns:
            bool: True if connected successfully, False otherwise
        """
        if self.running:
            logger.warning("Client is already connected")
            return False

        try:
            # Parse the host if it's an ngrok URL
            if '://' in host:
                # Extract host and port from ngrok URL
                ngrok_host, ngrok_port = self._parse_ngrok_url(host)
                if ngrok_host and ngrok_port:
                    host = ngrok_host
                    port = ngrok_port
                    logger.info(f"Parsed ngrok URL: {host}:{port}")

            # If command_port is not specified, use port+1
            if command_port is None:
                command_port = port + 1

            # Store host and ports for later use
            self.host = host
            self.port = port

            # Connect to the video streaming socket
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((host, port))

            # Connect to the command socket
            self.command_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.command_socket.connect((host, command_port))

            self.running = True

            # Start the frame receiving thread
            self.receive_thread = threading.Thread(target=self._receive_frames)
            self.receive_thread.daemon = True
            self.receive_thread.start()

            logger.info(f"Connected to stream server at {host}:{port} (video) and {host}:{command_port} (commands)")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to stream server: {e}")
            # Clean up any sockets that were created
            if self.client_socket:
                try:
                    self.client_socket.close()
                except:
                    pass
                self.client_socket = None
            if self.command_socket:
                try:
                    self.command_socket.close()
                except:
                    pass
                self.command_socket = None
            return False

    def _parse_ngrok_url(self, url: str) -> Tuple[Optional[str], Optional[int]]:
        """
        Parse an ngrok URL to extract host and port

        Args:
            url (str): The ngrok URL (e.g., tcp://0.tcp.ngrok.io:12345 or http://abcd1234.ngrok.io)

        Returns:
            Tuple[Optional[str], Optional[int]]: (host, port) or (None, None) if parsing failed
        """
        try:
            # Check if this is an HTTP or TCP URL
            is_http = 'http://' in url.lower() or 'https://' in url.lower()

            # Remove the protocol if present
            if '://' in url:
                url = url.split('://', 1)[1]

            # For HTTP URLs, we need to use a different approach
            if is_http:
                # For HTTP URLs, we don't need to extract a port
                # Just use the host as is and a default port (80 for HTTP)
                if ':' in url:
                    # If there's a port specified, extract it
                    host, port_str = url.rsplit(':', 1)
                    port = int(port_str)
                else:
                    # Otherwise use the default HTTP port
                    host = url
                    port = 80
                return host, port
            else:
                # For TCP URLs, extract host and port as before
                if ':' in url:
                    host, port_str = url.rsplit(':', 1)
                    port = int(port_str)
                    return host, port
                else:
                    # TCP URLs should always have a port
                    logger.error(f"Invalid TCP URL format (no port): {url}")
                    return None, None
        except Exception as e:
            logger.error(f"Failed to parse ngrok URL: {e}")
            return None, None

    def send_command(self, command: RemoteCommand) -> bool:
        """
        Send a remote control command to the server

        Args:
            command (RemoteCommand): The command to send

        Returns:
            bool: True if the command was sent successfully, False otherwise
        """
        if not self.running or not self.command_socket:
            logger.error("Cannot send command: not connected")
            return False

        try:
            # Convert the command to JSON and add a newline
            command_str = command.to_json() + '\n'
            # Send the command
            self.command_socket.sendall(command_str.encode('utf-8'))
            return True
        except Exception as e:
            logger.error(f"Error sending command: {e}")
            return False

    def disconnect(self) -> None:
        """Disconnect from the streaming server"""
        self.running = False

        # Close the video socket
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
            self.client_socket = None

        # Close the command socket
        if self.command_socket:
            try:
                self.command_socket.close()
            except:
                pass
            self.command_socket = None

        logger.info("Disconnected from stream server")

    def _receive_frames(self) -> None:
        """Thread function to receive frames from the server"""
        logger.info("Starting frame receiving thread")

        while self.running:
            try:
                # Receive data until we have the message size
                while len(self.data) < self.payload_size:
                    packet = self.client_socket.recv(4096)
                    if not packet:
                        raise ConnectionError("Connection closed by server")
                    self.data += packet

                # Extract the message size
                packed_msg_size = self.data[:self.payload_size]
                self.data = self.data[self.payload_size:]
                msg_size = struct.unpack("L", packed_msg_size)[0]

                # Receive the rest of the data
                while len(self.data) < msg_size:
                    packet = self.client_socket.recv(4096)
                    if not packet:
                        raise ConnectionError("Connection closed by server")
                    self.data += packet

                # Extract the frame data
                frame_data = self.data[:msg_size]
                self.data = self.data[msg_size:]

                # Deserialize and decode the frame
                encoded_frame = pickle.loads(frame_data)
                frame = cv2.imdecode(encoded_frame, cv2.IMREAD_COLOR)

                # Call the callback with the received frame
                if self.callback:
                    self.callback(frame)
            except ConnectionError as e:
                logger.error(f"Connection error: {e}")
                break
            except Exception as e:
                logger.error(f"Error receiving frame: {e}")
                time.sleep(0.1)

        # Clean up
        self.disconnect()
        logger.info("Frame receiving thread stopped")