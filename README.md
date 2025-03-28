# AppStream

A cross-platform desktop application for remote desktop control and high-quality streaming.

## Features

- **Remote Desktop Control**: Control remote machines similar to TeamViewer or AnyDesk
- **Real-time High-Quality Streaming**: Transmit high-quality images with low latency
- **Multi-Screen Navigation**: Switch between multiple monitors of the remote machine
- **Hardware Integration**: Connect and stream content from external devices (cameras, capture cards)

## Requirements

- Python 3.8 or higher
- Dependencies listed in `requirements.txt`

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd appStreamPython
   ```

2. Create a virtual environment (recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

Run the application:
```
python main.py
```

## Development

### Project Structure

```
appStreamPython/
├── app/                    # Main application code
│   ├── core/               # Core functionality
│   ├── hardware/           # Hardware integration
│   ├── ui/                 # User interface
│   └── utils/              # Utility functions
├── tests/                  # Unit tests
├── resources/              # Application resources
├── docs/                   # Documentation
└── main.py                 # Application entry point
```

### Running Tests

```
python -m unittest discover tests
```

## License

[Specify your license here]

## Contributing

[Contribution guidelines]
