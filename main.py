#!/usr/bin/env python3
"""
AppStream - Cross-platform remote desktop application with streaming capabilities
Main entry point for the application
"""

import sys
import logging
from PyQt6.QtWidgets import QApplication

from app.ui.main_window import MainWindow
from app.utils.network import setup_network

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('appstream.log')
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Main application entry point"""
    logger.info("Starting AppStream application")

    # Initialize the application
    app = QApplication(sys.argv)
    app.setApplicationName("AppStream")
    app.setOrganizationName("AppStream")
    app.setOrganizationDomain("appstream.example.com")

    # Setup network
    setup_network()

    # Create and show the main window
    window = MainWindow()
    window.show()

    # Start the application event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()