"""
Camera integration for AppStream
"""

import logging
import cv2
import numpy as np
from typing import Optional, List, Tuple

logger = logging.getLogger(__name__)

class Camera:
    """Class for camera integration"""

    def __init__(self):
        """Initialize the camera handler"""
        self.camera = None
        self.camera_index = -1
        self.available_cameras = []
        self._scan_cameras()
        logger.info(f"Camera handler initialized with {len(self.available_cameras)} available cameras")

    def _scan_cameras(self) -> None:
        """Scan for available cameras"""
        self.available_cameras = []
        # Try the first 10 camera indices (this is a common approach)
        for i in range(10):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                # Get camera information
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = cap.get(cv2.CAP_PROP_FPS)

                self.available_cameras.append({
                    'index': i,
                    'resolution': (width, height),
                    'fps': fps
                })

                # Release the camera
                cap.release()

        logger.info(f"Found {len(self.available_cameras)} cameras")

    def get_available_cameras(self) -> List[dict]:
        """
        Get a list of available cameras

        Returns:
            List[dict]: List of camera information dictionaries
        """
        # Refresh the camera list
        self._scan_cameras()
        return self.available_cameras

    def open_camera(self, camera_index: int = 0) -> bool:
        """
        Open a camera

        Args:
            camera_index (int): Index of the camera to open

        Returns:
            bool: True if camera opened successfully, False otherwise
        """
        # Close any existing camera
        self.close_camera()

        try:
            self.camera = cv2.VideoCapture(camera_index)
            if not self.camera.isOpened():
                logger.error(f"Failed to open camera {camera_index}")
                return False

            self.camera_index = camera_index
            width = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = self.camera.get(cv2.CAP_PROP_FPS)

            logger.info(f"Opened camera {camera_index} with resolution {width}x{height} at {fps} FPS")
            return True
        except Exception as e:
            logger.error(f"Error opening camera {camera_index}: {e}")
            return False

    def close_camera(self) -> None:
        """Close the current camera"""
        if self.camera is not None:
            try:
                self.camera.release()
                logger.info(f"Closed camera {self.camera_index}")
            except Exception as e:
                logger.error(f"Error closing camera: {e}")
            finally:
                self.camera = None
                self.camera_index = -1

    def capture_frame(self) -> Optional[np.ndarray]:
        """
        Capture a frame from the camera

        Returns:
            Optional[np.ndarray]: Captured frame as a numpy array or None if failed
        """
        if self.camera is None:
            logger.error("No camera is open")
            return None

        try:
            ret, frame = self.camera.read()
            if not ret:
                logger.error("Failed to capture frame")
                return None

            return frame
        except Exception as e:
            logger.error(f"Error capturing frame: {e}")
            return None

    def set_resolution(self, width: int, height: int) -> bool:
        """
        Set the camera resolution

        Args:
            width (int): Width in pixels
            height (int): Height in pixels

        Returns:
            bool: True if resolution set successfully, False otherwise
        """
        if self.camera is None:
            logger.error("No camera is open")
            return False

        try:
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

            # Verify the resolution was set
            actual_width = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))

            if actual_width != width or actual_height != height:
                logger.warning(f"Requested resolution {width}x{height} but got {actual_width}x{actual_height}")

            logger.info(f"Set camera resolution to {actual_width}x{actual_height}")
            return True
        except Exception as e:
            logger.error(f"Error setting resolution: {e}")
            return False

    def get_resolution(self) -> Tuple[int, int]:
        """
        Get the current camera resolution

        Returns:
            Tuple[int, int]: Width and height in pixels
        """
        if self.camera is None:
            logger.error("No camera is open")
            return (0, 0)

        try:
            width = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
            return (width, height)
        except Exception as e:
            logger.error(f"Error getting resolution: {e}")
            return (0, 0)