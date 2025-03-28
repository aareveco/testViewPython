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
from typing import Tuple, Callable

from app.core.screen_capture import ScreenCapture

logger = logging.getLogger(__name__)

class StreamServer:
    """Class for streaming screen content to clients"""

    def __init__(self, host: str = '', port: int = 5000):
        """
        Initialize the stream server

        Args:
            host (str): Host address to bind to (empty string means all interfaces)
            port (int): Port number to listen on
        """
        self.host = host
        self.port = port
        self.server_socket = None
        self.connections = []
        self.running = False
        self.screen_capture = ScreenCapture()
        self.quality = 50  # JPEG compression quality (0-100)
        self.fps_limit = 30  # Maximum frames per second
        self.frame_time = 1.0 / self.fps_limit
        self.last_frame_time = 0

        logger.info(f"Stream server initialized with host={host}, port={port}")

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
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.running = True

            # Start the connection acceptance thread
            self.accept_thread = threading.Thread(target=self._accept_connections)
            self.accept_thread.daemon = True
            self.accept_thread.start()

            logger.info(f"Stream server started on {self.host or 'all interfaces'}:{self.port}")
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
        """Thread function to accept client connections"""
        logger.info("Starting connection acceptance thread")

        while self.running:
            try:
                client_socket, addr = self.server_socket.accept()
                logger.info(f"New connection from {addr}")

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
                    logger.error(f"Error accepting connection: {e}")
                time.sleep(0.1)

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
        self.running = False
        self.data = b""
        self.payload_size = struct.calcsize("L")

        logger.info("Stream client initialized")

    def connect(self, host: str, port: int = 5000) -> bool:
        """
        Connect to a streaming server

        Args:
            host (str): Server host address
            port (int): Server port number

        Returns:
            bool: True if connected successfully, False otherwise
        """
        if self.running:
            logger.warning("Client is already connected")
            return False

        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((host, port))
            self.running = True

            # Start the frame receiving thread
            self.receive_thread = threading.Thread(target=self._receive_frames)
            self.receive_thread.daemon = True
            self.receive_thread.start()

            logger.info(f"Connected to stream server at {host}:{port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to stream server: {e}")
            return False

    def disconnect(self) -> None:
        """Disconnect from the streaming server"""
        self.running = False

        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
            self.client_socket = None

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