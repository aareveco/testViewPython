"""
Main window for the AppStream application
"""

import logging
import platform
import psutil
import cv2
import numpy as np
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QComboBox,
    QTabWidget, QGroupBox, QStatusBar, QMessageBox,
    QCheckBox
)
from PyQt6.QtCore import QSize, Qt, QTimer, QEvent, QPoint
from PyQt6.QtGui import QImage, QPixmap, QMouseEvent, QKeyEvent

from app.core.streaming import StreamServer, StreamClient
from app.core.remote_command import RemoteCommand
from app.utils.network import get_local_ip

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    """Main application window"""

    def __init__(self):
        super().__init__()

        self.setWindowTitle("AppStream")
        self.setMinimumSize(QSize(800, 600))

        # Set up the central widget and main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # Create the tab widget for different modes
        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget)

        # Initialize streaming components
        self.stream_server = None
        self.stream_client = None
        self.is_hosting = False
        self.is_connected = False
        self.current_frame = None

        # Remote control state
        self.remote_control_enabled = False

        # Get local IP for hosting (do this before setting up tabs)
        self.local_ip = get_local_ip()

        # Create tabs for different functionality
        self.setup_connect_tab()
        self.setup_host_tab()
        self.setup_settings_tab()

        # Set up status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

        # Set up timer for UI updates
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_ui)
        self.update_timer.start(100)  # Update every 100ms

        logger.info("Main window initialized")

    def update_ui(self):
        """Update UI elements periodically"""
        # Update system information in the settings tab
        if hasattr(self, 'system_info_label'):
            # Get system information
            system_info = f"OS: {platform.system()} {platform.release()}\n"
            system_info += f"CPU: {psutil.cpu_percent()}% used\n"
            system_info += f"Memory: {psutil.virtual_memory().percent}% used\n"
            system_info += f"Disk: {psutil.disk_usage('/').percent}% used"

            self.system_info_label.setText(system_info)

    def closeEvent(self, event):
        """Handle window close event"""
        # Clean up resources when the window is closed
        if self.stream_server:
            self.stream_server.stop()

        if self.stream_client and self.stream_client.running:
            self.stream_client.disconnect()

        # Accept the close event
        event.accept()

    def setup_connect_tab(self):
        """Set up the Connect tab for connecting to remote hosts"""
        connect_tab = QWidget()
        layout = QVBoxLayout(connect_tab)

        # Connection details group
        connection_group = QGroupBox("Connection Details")
        connection_layout = QVBoxLayout(connection_group)

        # Host input
        host_layout = QHBoxLayout()
        host_label = QLabel("Host:")
        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText("Enter IP address, hostname, or ngrok URL")
        host_layout.addWidget(host_label)
        host_layout.addWidget(self.host_input)
        connection_layout.addLayout(host_layout)

        # Port input
        port_layout = QHBoxLayout()
        port_label = QLabel("Port:")
        self.port_input = QLineEdit("5000")
        port_layout.addWidget(port_label)
        port_layout.addWidget(self.port_input)
        connection_layout.addLayout(port_layout)

        # Connect/Disconnect buttons
        button_layout = QHBoxLayout()
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.on_connect_clicked)
        self.disconnect_button = QPushButton("Disconnect")
        self.disconnect_button.clicked.connect(self.on_disconnect_clicked)
        self.disconnect_button.setEnabled(False)
        button_layout.addWidget(self.connect_button)
        button_layout.addWidget(self.disconnect_button)
        connection_layout.addLayout(button_layout)

        # Remote control toggle
        control_layout = QHBoxLayout()
        self.remote_control_checkbox = QComboBox()
        self.remote_control_checkbox.addItems(["View Only", "Remote Control"])
        self.remote_control_checkbox.setCurrentIndex(0)  # View Only by default
        self.remote_control_checkbox.currentIndexChanged.connect(self.on_remote_control_changed)
        control_layout.addWidget(QLabel("Mode:"))
        control_layout.addWidget(self.remote_control_checkbox)
        connection_layout.addLayout(control_layout)

        layout.addWidget(connection_group)

        # Recent connections group
        recent_group = QGroupBox("Recent Connections")
        recent_layout = QVBoxLayout(recent_group)
        self.recent_list = QComboBox()
        recent_layout.addWidget(self.recent_list)
        layout.addWidget(recent_group)

        # Remote screen display
        display_group = QGroupBox("Remote Screen")
        display_layout = QVBoxLayout(display_group)

        # Create a label to display the remote screen
        self.remote_screen_label = QLabel("Not connected")
        self.remote_screen_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.remote_screen_label.setMinimumSize(640, 480)
        self.remote_screen_label.setStyleSheet("background-color: #222; color: #aaa;")
        self.remote_screen_label.setMouseTracking(True)  # Track mouse movements
        self.remote_screen_label.setFocusPolicy(Qt.FocusPolicy.StrongFocus)  # Allow keyboard focus

        # Install event filter to capture mouse and keyboard events
        self.remote_screen_label.installEventFilter(self)

        # Variables to track mouse state
        self.last_mouse_pos = None
        self.mouse_buttons_pressed = set()

        display_layout.addWidget(self.remote_screen_label)

        layout.addWidget(display_group)

        self.tab_widget.addTab(connect_tab, "Connect")

    def setup_host_tab(self):
        """Set up the Host tab for hosting a session"""
        host_tab = QWidget()
        layout = QVBoxLayout(host_tab)

        # Host settings group
        host_group = QGroupBox("Host Settings")
        host_layout = QVBoxLayout(host_group)

        # IP address display
        ip_layout = QHBoxLayout()
        ip_label = QLabel("Your IP:")
        self.ip_display = QLineEdit(self.local_ip)
        self.ip_display.setReadOnly(True)
        ip_layout.addWidget(ip_label)
        ip_layout.addWidget(self.ip_display)
        host_layout.addLayout(ip_layout)

        # Port setting
        port_layout = QHBoxLayout()
        port_label = QLabel("Port:")
        self.host_port_input = QLineEdit("5000")
        port_layout.addWidget(port_label)
        port_layout.addWidget(self.host_port_input)
        host_layout.addLayout(port_layout)

        # ngrok option
        ngrok_layout = QVBoxLayout()
        ngrok_header_layout = QHBoxLayout()
        self.use_ngrok_checkbox = QCheckBox("Use ngrok for public access")
        self.use_ngrok_checkbox.setToolTip("Enable this to make your stream accessible from the internet")
        ngrok_header_layout.addWidget(self.use_ngrok_checkbox)
        ngrok_layout.addLayout(ngrok_header_layout)

        # Add a note about ngrok limitations
        ngrok_note = QLabel("Note: Free ngrok accounts have limitations. If TCP tunnels fail, HTTP will be used as a fallback.")
        ngrok_note.setWordWrap(True)
        ngrok_note.setStyleSheet("color: #666; font-size: 10px;")
        ngrok_layout.addWidget(ngrok_note)

        host_layout.addLayout(ngrok_layout)

        # ngrok URL display (initially hidden)
        self.ngrok_group = QGroupBox("ngrok Public URLs")
        self.ngrok_group.setVisible(False)
        ngrok_group_layout = QVBoxLayout(self.ngrok_group)

        # Video URL
        video_url_layout = QHBoxLayout()
        video_url_label = QLabel("Video URL:")
        self.video_url_display = QLineEdit()
        self.video_url_display.setReadOnly(True)
        video_url_layout.addWidget(video_url_label)
        video_url_layout.addWidget(self.video_url_display)
        ngrok_group_layout.addLayout(video_url_layout)

        # Command URL
        command_url_layout = QHBoxLayout()
        command_url_label = QLabel("Command URL:")
        self.command_url_display = QLineEdit()
        self.command_url_display.setReadOnly(True)
        command_url_layout.addWidget(command_url_label)
        command_url_layout.addWidget(self.command_url_display)
        ngrok_group_layout.addLayout(command_url_layout)

        host_layout.addWidget(self.ngrok_group)

        # Start/Stop hosting buttons
        button_layout = QHBoxLayout()
        self.start_hosting_button = QPushButton("Start Hosting")
        self.start_hosting_button.clicked.connect(self.on_start_hosting_clicked)
        self.stop_hosting_button = QPushButton("Stop Hosting")
        self.stop_hosting_button.clicked.connect(self.on_stop_hosting_clicked)
        self.stop_hosting_button.setEnabled(False)
        button_layout.addWidget(self.start_hosting_button)
        button_layout.addWidget(self.stop_hosting_button)
        host_layout.addLayout(button_layout)

        layout.addWidget(host_group)

        # Connection status group
        status_group = QGroupBox("Connection Status")
        status_layout = QVBoxLayout(status_group)
        self.status_label = QLabel("Not hosting")
        status_layout.addWidget(self.status_label)

        # Add client list
        self.client_list = QLabel("No clients connected")
        status_layout.addWidget(self.client_list)

        layout.addWidget(status_group)

        # Preview group
        preview_group = QGroupBox("Screen Preview")
        preview_layout = QVBoxLayout(preview_group)

        # Create a label to display the screen preview
        self.preview_label = QLabel("Preview not available")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumSize(640, 480)
        self.preview_label.setStyleSheet("background-color: #222; color: #aaa;")
        preview_layout.addWidget(self.preview_label)

        layout.addWidget(preview_group)

        self.tab_widget.addTab(host_tab, "Host")

    def setup_settings_tab(self):
        """Set up the Settings tab for application settings"""
        settings_tab = QWidget()
        layout = QVBoxLayout(settings_tab)

        # Display settings group
        display_group = QGroupBox("Display Settings")
        display_layout = QVBoxLayout(display_group)

        # Quality settings
        quality_layout = QHBoxLayout()
        quality_label = QLabel("Streaming Quality:")
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["Low", "Medium", "High", "Ultra"])
        self.quality_combo.setCurrentIndex(1)  # Medium by default
        self.quality_combo.currentIndexChanged.connect(self.on_quality_changed)
        quality_layout.addWidget(quality_label)
        quality_layout.addWidget(self.quality_combo)
        display_layout.addLayout(quality_layout)

        # FPS settings
        fps_layout = QHBoxLayout()
        fps_label = QLabel("FPS Limit:")
        self.fps_combo = QComboBox()
        self.fps_combo.addItems(["15", "30", "60"])
        self.fps_combo.setCurrentIndex(1)  # 30 FPS by default
        self.fps_combo.currentIndexChanged.connect(self.on_fps_changed)
        fps_layout.addWidget(fps_label)
        fps_layout.addWidget(self.fps_combo)
        display_layout.addLayout(fps_layout)

        layout.addWidget(display_group)

        # Security settings group
        security_group = QGroupBox("Security Settings")
        security_layout = QVBoxLayout(security_group)

        # Password protection
        password_layout = QHBoxLayout()
        password_label = QLabel("Password:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        password_layout.addWidget(password_label)
        password_layout.addWidget(self.password_input)
        security_layout.addLayout(password_layout)

        layout.addWidget(security_group)

        # System information group
        system_group = QGroupBox("System Information")
        system_layout = QVBoxLayout(system_group)

        # System info display
        self.system_info_label = QLabel("System information will be displayed here")
        system_layout.addWidget(self.system_info_label)

        layout.addWidget(system_group)

        # Add stretch to push everything to the top
        layout.addStretch()

        self.tab_widget.addTab(settings_tab, "Settings")

    def on_quality_changed(self, index):
        """Handle quality setting change"""
        quality_values = [25, 50, 75, 95]  # Low, Medium, High, Ultra
        quality = quality_values[index]

        logger.info(f"Streaming quality set to {quality}")

        # Update server quality if it exists
        if self.stream_server:
            self.stream_server.set_quality(quality)

    def on_fps_changed(self, index):
        """Handle FPS setting change"""
        fps_values = [15, 30, 60]
        fps = fps_values[index]

        logger.info(f"FPS limit set to {fps}")

        # Update server FPS if it exists
        if self.stream_server:
            self.stream_server.set_fps_limit(fps)

    def on_connect_clicked(self):
        """Handle connect button click"""
        host = self.host_input.text()
        port = self.port_input.text()

        if not host:
            QMessageBox.warning(self, "Connection Error", "Please enter a host address or ngrok URL")
            return

        # Check if this is an ngrok URL
        is_ngrok_url = '://' in host or '.ngrok.io' in host

        # Only validate port if not an ngrok URL
        if not is_ngrok_url:
            try:
                port_num = int(port)
                if port_num < 1 or port_num > 65535:
                    raise ValueError("Port out of range")
            except ValueError:
                QMessageBox.warning(self, "Connection Error", "Please enter a valid port number (1-65535)")
                return
        else:
            # For ngrok URLs, we'll use the port from the URL
            port_num = 0  # This will be ignored
            logger.info(f"Connecting to ngrok URL: {host}")

        self.status_bar.showMessage(f"Connecting to {host}...")

        # Disable connect button during connection attempt
        self.connect_button.setEnabled(False)

        # Create a stream client with a callback for received frames
        self.stream_client = StreamClient(self.handle_received_frame)

        # Try to connect
        if self.stream_client.connect(host, port_num):
            # Connection successful
            self.is_connected = True
            self.status_bar.showMessage(f"Connected to {host}")
            self.disconnect_button.setEnabled(True)

            # Add to recent connections if not already there
            if self.recent_list.findText(host) == -1:
                self.recent_list.addItem(host)
        else:
            # Connection failed
            self.stream_client = None
            self.connect_button.setEnabled(True)
            self.status_bar.showMessage(f"Failed to connect to {host}")
            QMessageBox.warning(self, "Connection Error", f"Failed to connect to {host}")

    def on_disconnect_clicked(self):
        """Handle disconnect button click"""
        if self.stream_client and self.is_connected:
            self.stream_client.disconnect()
            self.stream_client = None
            self.is_connected = False

            # Update UI
            self.connect_button.setEnabled(True)
            self.disconnect_button.setEnabled(False)
            self.remote_screen_label.setText("Not connected")
            self.status_bar.showMessage("Disconnected")

            logger.info("Disconnected from remote host")

    def handle_received_frame(self, frame):
        """Handle a frame received from the remote host"""
        if frame is not None:
            # Convert the OpenCV frame (BGR) to QImage (RGB)
            height, width, channels = frame.shape
            bytes_per_line = channels * width

            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Create QImage from the frame
            image = QImage(frame_rgb.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)

            # Create a pixmap from the image and set it to the label
            pixmap = QPixmap.fromImage(image)
            pixmap = pixmap.scaled(self.remote_screen_label.width(), self.remote_screen_label.height(),
                                  Qt.AspectRatioMode.KeepAspectRatio)
            self.remote_screen_label.setPixmap(pixmap)

            # Store the current frame and its dimensions
            self.current_frame = frame
            self.remote_frame_width = width
            self.remote_frame_height = height

    def on_remote_control_changed(self, index):
        """Handle remote control mode change"""
        self.remote_control_enabled = (index == 1)  # 1 = Remote Control, 0 = View Only

        if self.remote_control_enabled:
            self.status_bar.showMessage("Remote control enabled")
            # Set focus to the remote screen label to receive keyboard events
            self.remote_screen_label.setFocus()
        else:
            self.status_bar.showMessage("View only mode")

        logger.info(f"Remote control {'enabled' if self.remote_control_enabled else 'disabled'}")

    def eventFilter(self, obj, event):
        """Filter events for remote control"""
        if obj is self.remote_screen_label and self.is_connected and self.stream_client and self.remote_control_enabled:
            # Handle mouse events
            if event.type() == QEvent.Type.MouseMove:
                return self._handle_mouse_move(event)
            elif event.type() == QEvent.Type.MouseButtonPress:
                return self._handle_mouse_press(event)
            elif event.type() == QEvent.Type.MouseButtonRelease:
                return self._handle_mouse_release(event)
            elif event.type() == QEvent.Type.Wheel:
                return self._handle_mouse_wheel(event)
            # Handle keyboard events
            elif event.type() == QEvent.Type.KeyPress:
                return self._handle_key_press(event)
            elif event.type() == QEvent.Type.KeyRelease:
                return self._handle_key_release(event)

        # Let the event propagate
        return super().eventFilter(obj, event)

    def _handle_mouse_move(self, event):
        """Handle mouse move events"""
        if not hasattr(self, 'remote_frame_width') or not hasattr(self, 'remote_frame_height'):
            return False

        # Get the position relative to the label
        pos = event.position()
        label_width = self.remote_screen_label.width()
        label_height = self.remote_screen_label.height()

        # Calculate the scaling factor
        scale_x = self.remote_frame_width / label_width
        scale_y = self.remote_frame_height / label_height

        # Calculate the position on the remote screen
        remote_x = int(pos.x() * scale_x)
        remote_y = int(pos.y() * scale_y)

        # Create and send the mouse move command
        if self.last_mouse_pos:
            # Calculate relative movement if needed
            # For now, we'll use absolute positioning
            pass

        self.last_mouse_pos = (remote_x, remote_y)

        # Send the command to the server
        command = RemoteCommand.create_mouse_move(remote_x, remote_y)
        self.stream_client.send_command(command)

        return True

    def _handle_mouse_press(self, event):
        """Handle mouse press events"""
        button = self._qt_button_to_pyautogui(event.button())
        if button:
            # Add to pressed buttons set
            self.mouse_buttons_pressed.add(button)

            # Send mouse down command
            command = RemoteCommand.create_mouse_down(button)
            self.stream_client.send_command(command)

        return True

    def _handle_mouse_release(self, event):
        """Handle mouse release events"""
        button = self._qt_button_to_pyautogui(event.button())
        if button and button in self.mouse_buttons_pressed:
            # Remove from pressed buttons set
            self.mouse_buttons_pressed.remove(button)

            # Send mouse up command
            command = RemoteCommand.create_mouse_up(button)
            self.stream_client.send_command(command)

        return True

    def _handle_mouse_wheel(self, event):
        """Handle mouse wheel events"""
        # PyQt6 wheel events use angleDelta
        delta = event.angleDelta().y()

        # Convert to scroll clicks (positive for up, negative for down)
        clicks = delta // 120  # 120 is the standard delta for one click

        if clicks != 0:
            # Send scroll command
            command = RemoteCommand.create_mouse_scroll(clicks)
            self.stream_client.send_command(command)

        return True

    def _handle_key_press(self, event):
        """Handle key press events"""
        key = self._qt_key_to_pyautogui(event.key())
        if key:
            # Send key down command
            command = RemoteCommand.create_key_down(key)
            self.stream_client.send_command(command)

        return True

    def _handle_key_release(self, event):
        """Handle key release events"""
        key = self._qt_key_to_pyautogui(event.key())
        if key:
            # Send key up command
            command = RemoteCommand.create_key_up(key)
            self.stream_client.send_command(command)

        return True

    def _qt_button_to_pyautogui(self, qt_button):
        """Convert Qt mouse button to PyAutoGUI button name"""
        if qt_button == Qt.MouseButton.LeftButton:
            return 'left'
        elif qt_button == Qt.MouseButton.RightButton:
            return 'right'
        elif qt_button == Qt.MouseButton.MiddleButton:
            return 'middle'
        return None

    def _qt_key_to_pyautogui(self, qt_key):
        """Convert Qt key code to PyAutoGUI key name"""
        # This is a simplified mapping, you may need to expand it
        key_map = {
            Qt.Key.Key_A: 'a', Qt.Key.Key_B: 'b', Qt.Key.Key_C: 'c',
            Qt.Key.Key_D: 'd', Qt.Key.Key_E: 'e', Qt.Key.Key_F: 'f',
            Qt.Key.Key_G: 'g', Qt.Key.Key_H: 'h', Qt.Key.Key_I: 'i',
            Qt.Key.Key_J: 'j', Qt.Key.Key_K: 'k', Qt.Key.Key_L: 'l',
            Qt.Key.Key_M: 'm', Qt.Key.Key_N: 'n', Qt.Key.Key_O: 'o',
            Qt.Key.Key_P: 'p', Qt.Key.Key_Q: 'q', Qt.Key.Key_R: 'r',
            Qt.Key.Key_S: 's', Qt.Key.Key_T: 't', Qt.Key.Key_U: 'u',
            Qt.Key.Key_V: 'v', Qt.Key.Key_W: 'w', Qt.Key.Key_X: 'x',
            Qt.Key.Key_Y: 'y', Qt.Key.Key_Z: 'z',
            Qt.Key.Key_0: '0', Qt.Key.Key_1: '1', Qt.Key.Key_2: '2',
            Qt.Key.Key_3: '3', Qt.Key.Key_4: '4', Qt.Key.Key_5: '5',
            Qt.Key.Key_6: '6', Qt.Key.Key_7: '7', Qt.Key.Key_8: '8',
            Qt.Key.Key_9: '9',
            Qt.Key.Key_Space: 'space', Qt.Key.Key_Return: 'enter',
            Qt.Key.Key_Tab: 'tab', Qt.Key.Key_Escape: 'esc',
            Qt.Key.Key_Backspace: 'backspace', Qt.Key.Key_Delete: 'delete',
            Qt.Key.Key_Shift: 'shift', Qt.Key.Key_Control: 'ctrl',
            Qt.Key.Key_Alt: 'alt', Qt.Key.Key_Up: 'up',
            Qt.Key.Key_Down: 'down', Qt.Key.Key_Left: 'left',
            Qt.Key.Key_Right: 'right'
        }
        return key_map.get(qt_key)

    def on_start_hosting_clicked(self):
        """Handle start hosting button click"""
        port = self.host_port_input.text()
        use_ngrok = self.use_ngrok_checkbox.isChecked()

        try:
            port_num = int(port)
            if port_num < 1 or port_num > 65535:
                raise ValueError("Port out of range")
        except ValueError:
            QMessageBox.warning(self, "Hosting Error", "Please enter a valid port number (1-65535)")
            return

        logger.info(f"Starting hosting on port {port} (ngrok: {use_ngrok})")
        self.status_bar.showMessage(f"Starting hosting on port {port}...")

        # Create a stream server
        self.stream_server = StreamServer(host='', port=port_num, use_ngrok=use_ngrok)

        # Set quality and FPS based on current settings
        quality_values = [25, 50, 75, 95]  # Low, Medium, High, Ultra
        quality = quality_values[self.quality_combo.currentIndex()]
        self.stream_server.set_quality(quality)

        fps_values = [15, 30, 60]
        fps = fps_values[self.fps_combo.currentIndex()]
        self.stream_server.set_fps_limit(fps)

        # Start the server
        if self.stream_server.start():
            # Hosting started successfully
            self.is_hosting = True
            self.status_label.setText(f"Hosting on port {port}")
            self.start_hosting_button.setEnabled(False)
            self.stop_hosting_button.setEnabled(True)
            self.status_bar.showMessage(f"Hosting on port {port}")

            # Update ngrok URLs if using ngrok
            if use_ngrok and self.stream_server.public_url and self.stream_server.public_command_url:
                self.ngrok_group.setVisible(True)
                self.video_url_display.setText(str(self.stream_server.public_url))
                self.command_url_display.setText(str(self.stream_server.public_command_url))

                # Determine if we're using HTTP or TCP
                using_http = "http" in str(self.stream_server.public_url).lower()
                protocol_type = "HTTP" if using_http else "TCP"

                # Show a message with connection instructions
                connection_msg = (
                    f"ngrok {protocol_type} tunnels established. To connect from another computer:\n\n"
                    f"1. Enter the Video URL in the 'Host' field: {str(self.stream_server.public_url)}\n"
                    f"2. Leave the port field as is (it will be ignored)\n"
                    f"3. Click Connect\n\n"
                )

                if using_http:
                    connection_msg += (
                        "Note: Using HTTP tunnels instead of TCP due to ngrok free account limitations.\n"
                        "This may affect performance. For better performance, consider upgrading your ngrok account."
                    )

                QMessageBox.information(self, "ngrok Connection Info", connection_msg)
            else:
                self.ngrok_group.setVisible(False)

                if use_ngrok:
                    # Show error message if ngrok was enabled but failed
                    error_msg = (
                        "Failed to establish ngrok tunnels. This could be due to:\n\n"
                        "1. ngrok account limitations (free accounts have restrictions on TCP tunnels)\n"
                        "2. Network connectivity issues\n"
                        "3. ngrok service being temporarily unavailable\n\n"
                        "You can still use the application on your local network using your IP address."
                    )
                    QMessageBox.warning(self, "ngrok Error", error_msg)

            # Start a timer to update the preview
            self.update_preview_timer = QTimer()
            self.update_preview_timer.timeout.connect(self.update_preview)
            self.update_preview_timer.start(1000)  # Update every second
        else:
            # Hosting failed to start
            self.stream_server = None
            self.status_bar.showMessage(f"Failed to start hosting on port {port}")
            QMessageBox.warning(self, "Hosting Error", f"Failed to start hosting on port {port}")

    def on_stop_hosting_clicked(self):
        """Handle stop hosting button click"""
        logger.info("Stopping hosting")
        self.status_bar.showMessage("Stopping hosting...")

        if self.stream_server:
            # Check if ngrok was used
            was_using_ngrok = self.stream_server.use_ngrok

            # Stop the server
            self.stream_server.stop()
            self.stream_server = None
            self.is_hosting = False

            # Stop the preview timer
            if hasattr(self, 'update_preview_timer'):
                self.update_preview_timer.stop()

            # Update UI
            self.status_label.setText("Not hosting")
            self.client_list.setText("No clients connected")
            self.preview_label.setText("Preview not available")
            self.start_hosting_button.setEnabled(True)
            self.stop_hosting_button.setEnabled(False)

            # Hide ngrok group if it was visible
            if was_using_ngrok:
                self.ngrok_group.setVisible(False)
                self.video_url_display.clear()
                self.command_url_display.clear()

            self.status_bar.showMessage("Hosting stopped", 3000)

    def update_preview(self):
        """Update the screen preview"""
        if self.is_hosting and self.stream_server:
            # Get a screen capture
            frame = self.stream_server.screen_capture.capture_screen()
            if frame is not None:
                # Convert the OpenCV frame (BGR) to QImage (RGB)
                height, width, channels = frame.shape
                bytes_per_line = channels * width

                # Convert BGR to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # Create QImage from the frame
                image = QImage(frame_rgb.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)

                # Create a pixmap from the image and set it to the label
                pixmap = QPixmap.fromImage(image)
                pixmap = pixmap.scaled(self.preview_label.width(), self.preview_label.height(),
                                      Qt.AspectRatioMode.KeepAspectRatio)
                self.preview_label.setPixmap(pixmap)

                # Update client count
                client_count = len(self.stream_server.connections)
                if client_count == 0:
                    self.client_list.setText("No clients connected")
                elif client_count == 1:
                    self.client_list.setText("1 client connected")
                else:
                    self.client_list.setText(f"{client_count} clients connected")