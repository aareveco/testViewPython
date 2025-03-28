"""
Screen capture functionality for AppStream
"""

import logging
import numpy as np
from typing import Tuple, Optional, List
import mss
from PIL import Image

logger = logging.getLogger(__name__)

class ScreenCapture:
    """Class for capturing screen content"""

    def __init__(self):
        """Initialize the screen capture"""
        self.sct = mss.mss()
        self.monitors = self.sct.monitors
        self.current_monitor = 1  # Default to the first monitor (index 1 in mss)
        logger.info(f"Screen capture initialized with {len(self.monitors) - 1} monitors")

    def get_monitors(self) -> List[dict]:
        """
        Get a list of available monitors

        Returns:
            List[dict]: List of monitor information dictionaries
        """
        # Skip the first monitor (index 0) as it represents the "all monitors" virtual display
        return self.monitors[1:]

    def set_monitor(self, monitor_index: int) -> bool:
        """
        Set the current monitor to capture

        Args:
            monitor_index (int): Index of the monitor to capture (0-based)

        Returns:
            bool: True if successful, False otherwise
        """
        # Convert to mss monitor index (1-based)
        mss_index = monitor_index + 1

        if mss_index < 1 or mss_index >= len(self.monitors):
            logger.error(f"Invalid monitor index: {monitor_index}")
            return False

        self.current_monitor = mss_index
        logger.info(f"Set current monitor to {monitor_index} (mss index: {mss_index})")
        return True

    def capture_screen(self, region: Optional[Tuple[int, int, int, int]] = None) -> Optional[np.ndarray]:
        """
        Capture the current screen or a region of it

        Args:
            region (Optional[Tuple[int, int, int, int]]): Region to capture (left, top, width, height)
                                                         If None, captures the entire monitor

        Returns:
            Optional[np.ndarray]: Captured screen as a numpy array (BGR format) or None if failed
        """
        try:
            if region:
                left, top, width, height = region
                monitor = {
                    "left": left,
                    "top": top,
                    "width": width,
                    "height": height
                }
            else:
                monitor = self.monitors[self.current_monitor]

            # Capture the screen
            sct_img = self.sct.grab(monitor)

            # Convert to numpy array
            img = np.array(sct_img)

            return img
        except Exception as e:
            logger.error(f"Error capturing screen: {e}")
            return None

    def capture_to_pil(self, region: Optional[Tuple[int, int, int, int]] = None) -> Optional[Image.Image]:
        """
        Capture the screen and return as a PIL Image

        Args:
            region (Optional[Tuple[int, int, int, int]]): Region to capture (left, top, width, height)
                                                         If None, captures the entire monitor

        Returns:
            Optional[Image.Image]: Captured screen as a PIL Image or None if failed
        """
        img_array = self.capture_screen(region)
        if img_array is None:
            return None

        # Convert from BGR to RGB
        img_array_rgb = img_array[:, :, :3]  # Remove alpha channel if present

        # Create PIL Image
        return Image.fromarray(img_array_rgb)

    def get_monitor_size(self, monitor_index: Optional[int] = None) -> Tuple[int, int]:
        """
        Get the size of a monitor

        Args:
            monitor_index (Optional[int]): Index of the monitor (0-based), or None for current monitor

        Returns:
            Tuple[int, int]: Width and height of the monitor
        """
        if monitor_index is None:
            monitor = self.monitors[self.current_monitor]
        else:
            # Convert to mss monitor index (1-based)
            mss_index = monitor_index + 1
            if mss_index < 1 or mss_index >= len(self.monitors):
                logger.error(f"Invalid monitor index: {monitor_index}")
                return (0, 0)
            monitor = self.monitors[mss_index]

        return monitor["width"], monitor["height"]