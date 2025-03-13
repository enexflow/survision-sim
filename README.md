# Survision Device Simulator

A simulator for Survision devices (Micropak3 or later) used for License Plate Recognition (LPR). The simulator emulates the HTTP and WebSocket APIs of a real Survision device, allowing developers to build and test integrations without requiring access to the actual hardware.

## Features

- **API Compatibility**: Emulates the Survision device's HTTP and WebSocket APIs, including message formats and expected behavior.
- **Controllable Environment**: Allows users to simulate various scenarios by manually inputting license plates and controlling the device's state.
- **Web UI for Basic Interaction**: Provides a simple web UI for basic device control, state monitoring, and manual triggering of events.
- **Simplified Configuration**: Offers a mechanism to configure key aspects of the device behavior (e.g., recognition rate, common contexts).
- **Modern Python**: Uses Pydantic for data validation and uv for dependency management.

## Installation

### Using uv (Recommended)

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/survision-simulator.git
   cd survision-simulator

   uv run run_simulator.py
   ```

## Usage

1. Run the simulator:
   ```
   survision-sim
   ```
   or
   ```
   python -m survision_simulator.main
   ```

2. Access the web UI:
   Open your browser and navigate to `http://127.0.0.1:8080`

3. Connect to the WebSocket API:
   WebSocket endpoint is available at `ws://127.0.0.1:10001/async`

4. Use the HTTP API:
   HTTP endpoint is available at `http://127.0.0.1:8080/sync`

## Configuration

The simulator can be configured by editing the `config.json` file or through the web UI. The following configuration options are available:

- `ipAddress`: IP address to bind the server to (default: "127.0.0.1")
- `httpPort`: Port for the HTTP server (default: 8080)
- `wsPort`: Port for the WebSocket server (default: 10001)
- `recognitionSuccessRate`: Probability of a successful plate read (default: 75)
- `defaultContext`: Default license plate context (default: "F")
- `plateReliability`: Reliability of plate recognition (default: 80)

## Development

This project uses:
- **uv**: Fast Python package installer and resolver
- **Pydantic**: Data validation and settings management
- **pyproject.toml**: Modern Python packaging

To set up a development environment:

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create a virtual environment and install dependencies
uv venv
source .venv/bin/activate
uv pip install -e .
```

## API Documentation

### HTTP API (`/sync` endpoint)

The HTTP API accepts POST requests with JSON payloads representing CDK messages. The following message types are supported:

- `getConfig`: Get the device configuration
- `getCurrentLog`: Get the current recognition
- `getDatabase`: Get the list of plates in the internal database
- `getDate`: Get the current date and time
- `getImage`: Get a video stream image
- `getInfos`: Get device information
- `getLog`: Get a specific recognition log
- `getTraces`: Get traces
- `getXSD`: Get the XSD file
- `openBarrier`: Open the barrier
- `triggerOn`: Start a trigger session
- `triggerOff`: End a trigger session
- `lock`: Lock the device
- `unlock`: Unlock the device
- `resetConfig`: Reset configuration to default
- `resetEngine`: Reset recognition engine
- `setConfig`: Change configuration
- `editDatabase`: Edit the plate database
- `resetCounters`: Reset counters
- `allowSetConfig`: Allow configuration changes
- `forbidSetConfig`: Forbid configuration changes
- `calibrateZoomFocus`: Calibrate zoom focus

### WebSocket API (`/async` endpoint)

The WebSocket API allows for asynchronous communication with the device. The following message types are supported:

- `setEnableStreams`: Enable or disable the transmission of asynchronous events

The simulator will send the following asynchronous messages:

- `anpr`: License plate recognition results
- `dgpr`: DGPR results
- `ioState`: IO state changes
- `triggerResult`: Trigger results
- `config`: Configuration changes
- `infos`: State changes
- `traces`: Traces

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

This simulator is based on the Survision device specification document. 