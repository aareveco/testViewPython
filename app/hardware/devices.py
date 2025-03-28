"""
External device integration for AppStream
"""

import logging
import os
import platform
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class DeviceManager:
    """Class for managing external devices"""

    def __init__(self):
        """Initialize the device manager"""
        self.system = platform.system()
        logger.info(f"Device manager initialized on {self.system}")

    def get_system_info(self) -> Dict[str, str]:
        """
        Get system information

        Returns:
            Dict[str, str]: Dictionary of system information
        """
        info = {
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor()
        }
        return info

    def get_video_devices(self) -> List[Dict[str, Any]]:
        """
        Get a list of video devices (capture cards, etc.)

        Returns:
            List[Dict[str, Any]]: List of video device information
        """
        devices = []

        if self.system == 'Linux':
            # On Linux, video devices are typically in /dev/video*
            try:
                for dev in os.listdir('/dev'):
                    if dev.startswith('video'):
                        devices.append({
                            'name': f'/dev/{dev}',
                            'type': 'video',
                            'path': f'/dev/{dev}'
                        })
            except Exception as e:
                logger.error(f"Error listing video devices: {e}")

        elif self.system == 'Darwin':  # macOS
            # macOS doesn't have a standard way to list video devices
            # We could use system_profiler, but it's more complex
            logger.info("Video device detection on macOS is limited")

        elif self.system == 'Windows':
            # On Windows, this would require more complex code using DirectShow or similar
            logger.info("Video device detection on Windows is limited")

        return devices

    def get_audio_devices(self) -> List[Dict[str, Any]]:
        """
        Get a list of audio devices

        Returns:
            List[Dict[str, Any]]: List of audio device information
        """
        devices = []

        # This is a simplified implementation
        # A real implementation would use platform-specific APIs

        if self.system == 'Linux':
            # On Linux, audio devices are typically in /dev/snd/*
            try:
                if os.path.exists('/dev/snd'):
                    for dev in os.listdir('/dev/snd'):
                        if dev.startswith('pcm'):
                            devices.append({
                                'name': f'/dev/snd/{dev}',
                                'type': 'audio',
                                'path': f'/dev/snd/{dev}'
                            })
            except Exception as e:
                logger.error(f"Error listing audio devices: {e}")

        elif self.system == 'Darwin':  # macOS
            # macOS doesn't have a standard way to list audio devices from the file system
            logger.info("Audio device detection on macOS is limited")

        elif self.system == 'Windows':
            # On Windows, this would require more complex code
            logger.info("Audio device detection on Windows is limited")

        return devices

    def get_usb_devices(self) -> List[Dict[str, Any]]:
        """
        Get a list of USB devices

        Returns:
            List[Dict[str, Any]]: List of USB device information
        """
        devices = []

        # This is a simplified implementation
        # A real implementation would use platform-specific APIs or pyusb

        if self.system == 'Linux':
            # On Linux, USB devices can be found in /sys/bus/usb/devices/
            try:
                if os.path.exists('/sys/bus/usb/devices/'):
                    for dev in os.listdir('/sys/bus/usb/devices/'):
                        if ':' in dev:  # Filter out non-device entries
                            try:
                                # Try to read the manufacturer and product
                                manufacturer_path = f'/sys/bus/usb/devices/{dev}/manufacturer'
                                product_path = f'/sys/bus/usb/devices/{dev}/product'

                                manufacturer = ''
                                product = ''

                                if os.path.exists(manufacturer_path):
                                    with open(manufacturer_path, 'r') as f:
                                        manufacturer = f.read().strip()

                                if os.path.exists(product_path):
                                    with open(product_path, 'r') as f:
                                        product = f.read().strip()

                                devices.append({
                                    'name': product or dev,
                                    'manufacturer': manufacturer,
                                    'product': product,
                                    'path': f'/sys/bus/usb/devices/{dev}'
                                })
                            except Exception as e:
                                logger.error(f"Error reading USB device {dev}: {e}")
            except Exception as e:
                logger.error(f"Error listing USB devices: {e}")

        elif self.system == 'Darwin':  # macOS
            # macOS requires system_profiler to list USB devices
            logger.info("USB device detection on macOS is limited")

        elif self.system == 'Windows':
            # On Windows, this would require more complex code
            logger.info("USB device detection on Windows is limited")

        return devices

    def get_capture_cards(self) -> List[Dict[str, Any]]:
        """
        Get a list of capture cards

        Returns:
            List[Dict[str, Any]]: List of capture card information
        """
        # Capture cards are typically specialized video devices
        # This is a simplified implementation that just looks for known capture card names

        video_devices = self.get_video_devices()
        capture_cards = []

        # Known capture card manufacturers/keywords
        capture_card_keywords = [
            'elgato', 'blackmagic', 'avermedia', 'magewell', 'capture'
        ]

        for device in video_devices:
            name = device.get('name', '').lower()
            for keyword in capture_card_keywords:
                if keyword in name:
                    capture_cards.append(device)
                    break

        return capture_cards