"""
Tests for the screen capture functionality
"""

import unittest
import numpy as np
from app.core.screen_capture import ScreenCapture

class TestScreenCapture(unittest.TestCase):
    """Test cases for the ScreenCapture class"""

    def setUp(self):
        """Set up the test environment"""
        self.screen_capture = ScreenCapture()

    def test_get_monitors(self):
        """Test getting the list of monitors"""
        monitors = self.screen_capture.get_monitors()
        # There should be at least one monitor
        self.assertGreaterEqual(len(monitors), 1)

        # Each monitor should have width and height
        for monitor in monitors:
            self.assertIn('width', monitor)
            self.assertIn('height', monitor)
            self.assertGreater(monitor['width'], 0)
            self.assertGreater(monitor['height'], 0)

    def test_capture_screen(self):
        """Test capturing the screen"""
        # Capture the screen
        frame = self.screen_capture.capture_screen()

        # The frame should not be None
        self.assertIsNotNone(frame)

        # The frame should be a numpy array
        self.assertIsInstance(frame, np.ndarray)

        # The frame should have 3 or 4 channels (RGB or RGBA)
        self.assertIn(frame.shape[2], [3, 4])

        # The frame dimensions should match the monitor size
        width, height = self.screen_capture.get_monitor_size()
        self.assertEqual(frame.shape[1], width)
        self.assertEqual(frame.shape[0], height)

    def test_capture_to_pil(self):
        """Test capturing the screen as a PIL Image"""
        # Capture the screen as a PIL Image
        image = self.screen_capture.capture_to_pil()

        # The image should not be None
        self.assertIsNotNone(image)

        # The image dimensions should match the monitor size
        width, height = self.screen_capture.get_monitor_size()
        self.assertEqual(image.width, width)
        self.assertEqual(image.height, height)

    def test_set_monitor(self):
        """Test setting the current monitor"""
        # Get the number of monitors
        monitors = self.screen_capture.get_monitors()

        if len(monitors) > 1:
            # If there are multiple monitors, test switching between them
            # Try to set to the second monitor (index 1)
            result = self.screen_capture.set_monitor(1)
            self.assertTrue(result)

            # The current monitor should now be 2 (mss index is 1-based)
            self.assertEqual(self.screen_capture.current_monitor, 2)

        # Test setting to an invalid monitor index
        result = self.screen_capture.set_monitor(999)
        self.assertFalse(result)

    def test_get_monitor_size(self):
        """Test getting the monitor size"""
        # Get the size of the current monitor
        width, height = self.screen_capture.get_monitor_size()

        # The dimensions should be positive
        self.assertGreater(width, 0)
        self.assertGreater(height, 0)

        # Get the monitors
        monitors = self.screen_capture.get_monitors()

        if len(monitors) > 1:
            # If there are multiple monitors, test getting the size of a specific monitor
            width, height = self.screen_capture.get_monitor_size(1)
            self.assertGreater(width, 0)
            self.assertGreater(height, 0)

        # Test getting the size of an invalid monitor
        width, height = self.screen_capture.get_monitor_size(999)
        self.assertEqual(width, 0)
        self.assertEqual(height, 0)

if __name__ == '__main__':
    unittest.main()