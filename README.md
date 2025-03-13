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

### HTTP API ("/sync" endpoint)

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
- `calibrateZoomFocus`: Calibrate zoom/focus
- `setSecurity`: Modify security configuration
- `setup`: Internal factory setup command
- `testFTP`: Test FTP server accessibility
- `testNTP`: Test NTP server accessibility
- `update`: Update request
- `updateWebFirmware`: Update firmware from a web URL

### WebSocket API ("/async" endpoint)

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
- `video`: Video stream

## Detailed Message Reference

### Client Synchronous Requests

These messages can be sent by the client to the device via HTTP POST to the `/sync` endpoint. The device will respond with a corresponding answer.

#### Requests That Can Be Sent Without Sensor Lock

- **getConfig**: Get the device configuration
- **getCurrentLog**: Get the current recognition
- **getDatabase**: Get the list of plates in the internal database
- **getDate**: Get the current date and time
- **getImage**: Get a video stream image
- **getInfos**: Get device information
- **getLog**: Get a specific recognition log
- **getTraces**: Get traces
- **getXSD**: Get the XSD file
- **lock**: Lock the device
- **openBarrier**: Open the connected barrier
- **resetCounters**: Reset counters
- **resetEngine**: Reset recognition engine
- **setConfig**: Change configuration
- **editDatabase**: Edit the plate database
- **resetConfig**: Reset configuration to default
- **allowSetConfig**: Allow configuration changes
- **forbidSetConfig**: Forbid configuration changes
- **calibrateZoomFocus**: Calibrate zoom/focus
- **setSecurity**: Modify security configuration
- **setup**: Internal factory setup command
- **testFTP**: Test FTP server accessibility
- **testNTP**: Test NTP server accessibility
- **update**: Update request
- **updateWebFirmware**: Update firmware from a web URL
- **triggerOn**: Start a trigger session
- **triggerOff**: End a trigger session
- **unlock**: Unlock the device

#### Requests That Need Sensor Lock

A `lock` message must be sent before these messages can be processed by the server:

- **allowSetConfig**: Allows config changes
- **calibrateZoomFocus**: Calibrate zoom/focus
- **editDatabase**: Modify the plate database
- **eraseDatabase**: Erase the internal database
- **forbidSetConfig**: Forbid config changes
- **reboot**: Reboot the device
- **resetConfig**: Reset configuration to default
- **setConfig**: Modify the equipment configuration

### Server Synchronous Answers

These messages are sent by the server in response to client synchronous requests:

- **answer**: Standard response to a client request, containing status information and optional error text.

- **config**: Contains the sensor configuration, sent in response to `getConfig` or asynchronously if enabled.

- **database**: Contains the list of plates in the internal database.

- **date**: Contains the current date and time.

- **image**: Contains a video stream image.

- **infos**: Contains information about the device, sent in response to `getInfos` or asynchronously if enabled.

- **traces**: Contains the history of traces.

- **triggerAnswer**: Response to a `triggerOn` or `triggerOff` message.

- **xsd**: Contains the XSD file as binary data.

### Client Asynchronous Messages

These messages can be sent by the client via WebSocket to the `/async` endpoint:

- **setEnableStreams**: Activates or deactivates the reception of data streams. This message is managed by the server and will be resent each time it reconnects.

### Server Asynchronous Messages

These messages are sent by the server when specific events occur:

- **anpr**: License plate messages. Each sub-element represents an event that can occur on the sensor:
  - `noPlate`: Sent when there is no plate visible
  - `new`: Sent when a new plate is detected
  - `end`: Sent when a plate is no longer visible
  - `decision`: Sent when the sensor has made a recognition decision
  - `speed`: Sent when the sensor has calculated vehicle speed

- **config**: Sensor configuration, sent asynchronously if enabled.

- **dgpr**: Dangerous goods plate messages.

- **infos**: Information message, sent asynchronously if enabled.

- **ioState**: IO state message, received when the state on the input IO changes.

- **traces**: History of traces.

- **triggerResult**: Trigger result message.

- **video**: Video stream compressed image.

### Message Format Details

#### ANPR Message

The `anpr` message contains license plate recognition results:

```json
{
  "anpr": {
    "@date": "1581217555554",
    "@session": "12345",
    "@id": "67890",
    "decision": {
      "@plate": "ABC123",
      "@x": "320",
      "@y": "240",
      "@width": "100",
      "@height": "30",
      "@sinus": "0.0",
      "@reliability": "95",
      "@direction": "front",
      "@context": "F",
      "@context_isoAlpha2": "FR",
      "@context_isoAlpha3": "FRA",
      "@plateOccurences": "5",
      "jpeg": {
        "#text": "[Base64 encoded JPEG]"
      }
    }
  }
}
```

#### Trigger Messages

The trigger system allows synchronization with external systems:

1. Client sends `triggerOn` to start a trigger session:
```json
{
  "triggerOn": {
    "@cameraId": "0",
    "@timeout": "5000"
  }
}
```

2. Server responds with `triggerAnswer`:
```json
{
  "triggerAnswer": {
    "@status": "ok",
    "@triggerId": "12345"
  }
}
```

3. When a plate is recognized or the trigger times out, server sends `triggerResult`:
```json
{
  "triggerResult": {
    "@date": "1581217555554",
    "@triggerResultTimestamp": "1581217556000",
    "@triggerOnTimestamp": "1581217550000",
    "@triggerOffTimestamp": "1581217555000",
    "@triggerId": "12345",
    "decision": {
      "@plate": "ABC123",
      "@reliability": "95",
      "jpeg": {
        "#text": "[Base64 encoded JPEG]"
      }
    }
  }
}
```

## HTTP and WebSocket Server Logic

### HTTP Server

The HTTP server handles synchronous requests:

1. Client sends a POST request to `/sync` with a JSON payload containing a CDK message
2. Server validates and processes the message
4. Server sends the json response back to the client

The request must include a `Password` header for operations that require locking the device.

### WebSocket Server

The WebSocket server handles asynchronous communication:

1. Client establishes a WebSocket connection to `/async`
2. Client can send messages to configure what events to receive (using `setEnableStreams`)
3. Server sends asynchronous events (ANPR decisions, IO state changes, etc.) as they occur
4. Server sends ping frames to ensure the client is still connected

The WebSocket connection allows real-time updates without polling, making it ideal for receiving plate recognition events as they happen.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

This simulator is based on the Survision device specification document. 