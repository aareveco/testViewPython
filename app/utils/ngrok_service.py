"""
ngrok integration for AppStream
"""

import logging
import threading
import time
from typing import Optional, Dict, Any
from pyngrok import ngrok, conf

logger = logging.getLogger(__name__)

class NgrokService:
    """Class for managing ngrok tunnels"""

    def __init__(self):
        """Initialize the ngrok service"""
        self.tunnels = {}
        self.running = False
        self.ngrok_thread = None

        # Configure ngrok
        conf.get_default().monitor_thread = False

        logger.info("NgrokService initialized")

    def start_tunnel(self, port: int, name: str = "default", protocol: str = "tcp", fallback_to_http: bool = True) -> Optional[str]:
        """
        Start an ngrok tunnel for the specified port

        Args:
            port (int): The local port to tunnel
            name (str): A name for the tunnel
            protocol (str): The protocol to use (tcp or http)
            fallback_to_http (bool): Whether to try HTTP if TCP fails

        Returns:
            Optional[str]: The public URL for the tunnel, or None if failed
        """
        try:
            # Check if tunnel already exists
            if name in self.tunnels:
                logger.warning(f"Tunnel '{name}' already exists, stopping it first")
                self.stop_tunnel(name)

            # Start the tunnel
            try:
                tunnel = ngrok.connect(port, protocol)
                # Extract the URL string from the NgrokTunnel object
                if hasattr(tunnel, 'public_url'):
                    public_url = tunnel.public_url
                else:
                    # If it's already a string, use it directly
                    public_url = str(tunnel)
            except Exception as e:
                # If TCP fails and fallback is enabled, try HTTP
                if protocol == "tcp" and fallback_to_http and "TCP endpoints" in str(e):
                    logger.warning(f"TCP tunnel failed due to account limitations. Trying HTTP instead.")
                    protocol = "http"
                    tunnel = ngrok.connect(port, protocol)
                    # Extract the URL string
                    if hasattr(tunnel, 'public_url'):
                        public_url = tunnel.public_url
                    else:
                        public_url = str(tunnel)
                else:
                    raise e

            # Store the tunnel information
            self.tunnels[name] = {
                "tunnel": tunnel,  # Store the original tunnel object
                "url": public_url,  # Store the URL as a string
                "port": port,
                "protocol": protocol
            }

            logger.info(f"Started ngrok tunnel '{name}' for port {port} using {protocol}: {public_url}")
            return public_url
        except Exception as e:
            logger.error(f"Failed to start ngrok tunnel: {e}")
            return None

    def stop_tunnel(self, name: str = "default") -> bool:
        """
        Stop an ngrok tunnel

        Args:
            name (str): The name of the tunnel to stop

        Returns:
            bool: True if the tunnel was stopped, False otherwise
        """
        try:
            if name in self.tunnels:
                # Get the tunnel object or URL
                tunnel_info = self.tunnels[name]

                # Check if we have the tunnel object
                if "tunnel" in tunnel_info:
                    # Use the tunnel object directly
                    ngrok.disconnect(tunnel_info["tunnel"])
                else:
                    # Fall back to using the URL
                    ngrok.disconnect(tunnel_info["url"])

                # Remove from our tunnels dict
                del self.tunnels[name]

                logger.info(f"Stopped ngrok tunnel '{name}'")
                return True
            else:
                logger.warning(f"No tunnel found with name '{name}'")
                return False
        except Exception as e:
            logger.error(f"Failed to stop ngrok tunnel: {e}")
            return False

    def stop_all_tunnels(self) -> None:
        """Stop all ngrok tunnels"""
        try:
            # Get a list of tunnel names (to avoid modifying dict during iteration)
            tunnel_names = list(self.tunnels.keys())

            # Stop each tunnel
            for name in tunnel_names:
                self.stop_tunnel(name)

            logger.info("Stopped all ngrok tunnels")
        except Exception as e:
            logger.error(f"Failed to stop all ngrok tunnels: {e}")

    def get_tunnel_info(self, name: str = "default") -> Optional[Dict[str, Any]]:
        """
        Get information about a tunnel

        Args:
            name (str): The name of the tunnel

        Returns:
            Optional[Dict[str, Any]]: Information about the tunnel, or None if not found
        """
        return self.tunnels.get(name)

    def get_public_url(self, name: str = "default") -> Optional[str]:
        """
        Get the public URL for a tunnel

        Args:
            name (str): The name of the tunnel

        Returns:
            Optional[str]: The public URL, or None if not found
        """
        tunnel = self.tunnels.get(name)
        if tunnel:
            return tunnel["url"]
        return None

    def extract_host_port(self, url: str) -> tuple:
        """
        Extract host and port from an ngrok URL

        Args:
            url (str): The ngrok URL (e.g., tcp://0.tcp.ngrok.io:12345)

        Returns:
            tuple: (host, port) or (None, None) if parsing failed
        """
        try:
            # Parse the URL
            if "://" in url:
                # Remove the protocol
                url = url.split("://")[1]

            # Split host and port
            if ":" in url:
                host, port_str = url.split(":")
                port = int(port_str)
                return host, port

            return url, None
        except Exception as e:
            logger.error(f"Failed to parse ngrok URL: {e}")
            return None, None

    def __del__(self):
        """Clean up when the object is destroyed"""
        self.stop_all_tunnels()
