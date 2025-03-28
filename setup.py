from setuptools import setup, find_packages

setup(
    name="appstream",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "PyQt6>=6.4.0",
        "pyautogui>=0.9.53",
        "pillow>=9.3.0",
        "mss>=7.0.1",
        "keyboard>=0.13.5",
        "mouse>=0.7.1",
        "opencv-python>=4.6.0",
        "numpy>=1.23.5",
        "websockets>=10.4",
        "protobuf>=4.21.9",
        "grpcio>=1.50.0",
        "pyzmq>=24.0.1",
        "pyserial>=3.5",
        "pyusb>=1.2.1",
        "pycryptodome>=3.16.0",
        "psutil>=5.9.4",
        "loguru>=0.6.0",
    ],
    entry_points={
        "console_scripts": [
            "appstream=main:main",
        ],
    },
    author="Ariel Reveco",
    author_email="aareveco1",
    description="Cross-platform remote desktop application with streaming capabilities",
    keywords="remote desktop, streaming, screen sharing",
    python_requires=">=3.8",
)
