"""
Tests for the remote control functionality
"""

import unittest
from unittest.mock import patch
from app.core.remote_control import RemoteControl

class TestRemoteControl(unittest.TestCase):
    """Test cases for the RemoteControl class"""

    def setUp(self):
        """Set up the test environment"""
        # Use patch to avoid actual mouse/keyboard control during tests
        with patch('pyautogui.size', return_value=(1920, 1080)):
            self.remote_control = RemoteControl()

    @patch('pyautogui.moveTo')
    def test_move_mouse(self, mock_moveto):
        """Test moving the mouse"""
        # Test absolute movement
        result = self.remote_control.move_mouse(100, 200)
        self.assertTrue(result)
        mock_moveto.assert_called_once_with(100, 200)

    @patch('pyautogui.moveRel')
    @patch('pyautogui.position', return_value=(50, 50))
    def test_move_mouse_relative(self, mock_position, mock_moverel):
        """Test moving the mouse relatively"""
        # Test relative movement
        result = self.remote_control.move_mouse(10, 20, relative=True)
        self.assertTrue(result)
        mock_position.assert_called_once()
        mock_moverel.assert_called_once_with(10, 20)

    @patch('pyautogui.click')
    def test_click_mouse(self, mock_click):
        """Test clicking the mouse"""
        # Test left click
        result = self.remote_control.click_mouse()
        self.assertTrue(result)
        mock_click.assert_called_once_with(button='left')

        # Test right click
        mock_click.reset_mock()
        result = self.remote_control.click_mouse(button='right')
        self.assertTrue(result)
        mock_click.assert_called_once_with(button='right')

    @patch('pyautogui.doubleClick')
    def test_double_click_mouse(self, mock_doubleclick):
        """Test double-clicking the mouse"""
        result = self.remote_control.click_mouse(double=True)
        self.assertTrue(result)
        mock_doubleclick.assert_called_once_with(button='left')

    @patch('pyautogui.mouseDown')
    def test_mouse_down(self, mock_mousedown):
        """Test pressing a mouse button"""
        result = self.remote_control.mouse_down()
        self.assertTrue(result)
        mock_mousedown.assert_called_once_with(button='left')

    @patch('pyautogui.mouseUp')
    def test_mouse_up(self, mock_mouseup):
        """Test releasing a mouse button"""
        result = self.remote_control.mouse_up()
        self.assertTrue(result)
        mock_mouseup.assert_called_once_with(button='left')

    @patch('pyautogui.scroll')
    def test_scroll_mouse(self, mock_scroll):
        """Test scrolling the mouse wheel"""
        result = self.remote_control.scroll_mouse(10)
        self.assertTrue(result)
        mock_scroll.assert_called_once_with(10)

    @patch('pyautogui.press')
    def test_press_key(self, mock_press):
        """Test pressing a key"""
        result = self.remote_control.press_key('a')
        self.assertTrue(result)
        mock_press.assert_called_once_with('a')

    @patch('pyautogui.keyDown')
    def test_key_down(self, mock_keydown):
        """Test pressing and holding a key"""
        result = self.remote_control.key_down('shift')
        self.assertTrue(result)
        mock_keydown.assert_called_once_with('shift')

    @patch('pyautogui.keyUp')
    def test_key_up(self, mock_keyup):
        """Test releasing a key"""
        result = self.remote_control.key_up('shift')
        self.assertTrue(result)
        mock_keyup.assert_called_once_with('shift')

    @patch('pyautogui.write')
    def test_type_text(self, mock_write):
        """Test typing text"""
        result = self.remote_control.type_text('Hello, world!')
        self.assertTrue(result)
        mock_write.assert_called_once_with('Hello, world!')

    @patch('pyautogui.hotkey')
    def test_hotkey(self, mock_hotkey):
        """Test pressing a hotkey combination"""
        result = self.remote_control.hotkey('ctrl', 'c')
        self.assertTrue(result)
        mock_hotkey.assert_called_once_with('ctrl', 'c')

if __name__ == '__main__':
    unittest.main()