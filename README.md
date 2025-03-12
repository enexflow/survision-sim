Okay, here's a detailed specification document for a Survision Device Simulator. This document aims for clarity and completeness, leaving minimal room for interpretation during implementation.

## Survision Device Simulator: Specification Document

**1. Introduction**

This document outlines the specifications for a simulator designed to emulate the behavior of a Survision license plate recognition (LPR) device. The simulator will provide the same communication interfaces (HTTP and WebSocket) and a simple web-based UI for basic interaction and status viewing.  The goal is to provide a tool for testing and development of client applications without requiring a physical Survision device.

**2. Goals**

*   Emulate core functionalities of a Survision device: LPR, barrier control.
*   Expose identical HTTP and WebSocket APIs for seamless client integration.
*   Provide a basic web UI for:
    *   Manually entering license plates.
    *   Viewing the barrier status (open/closed).
    *   Viewing recent LPR events.
*   Be configurable to simulate different operating scenarios and error conditions.
*   Support realistic data structures for communication.

**3. System Architecture**

The simulator will consist of the following components:

*   **API Server:** Handles HTTP and WebSocket communication, manages simulated device state, and processes requests.
*   **LPR Engine (Simulated):**  A software component that simulates the license plate recognition process, responsible for generating simulated LPR data (license plate number, confidence, etc.). It can be manually triggered or run continuously.
*   **Barrier Controller (Simulated):** Manages the simulated barrier status (open/closed), reacting to commands from the API server or LPR Engine.
*   **Data Storage:** Holds configuration data, LPR history, and other persistent information.
*   **Web UI:** Provides a user interface for interaction and status monitoring.

**4. Functional Requirements**

**4.1. LPR Engine (Simulated)**

*   **Manual Triggering:** The web UI should allow manual triggering of the LPR engine, simulating a single license plate reading attempt.
*   **Automatic Mode:**  The simulator should have an automatic LPR mode, where it generates random or predefined license plates at a configurable rate (e.g., plates/second).
*   **Plate Generation:**
    *   **Random:** Generate license plates following a configurable format (e.g., a combination of letters and numbers, a country context).
    *   **Predefined:** Use a list of license plates from a configuration file.
*   **Confidence Level:** Assign a simulated confidence level (0-100) to each generated license plate.
*   **Context Simulation:** Simulate country context based on a configurable probability distribution.
*   **Error Simulation:** Introduce errors in plate reading with a configurable probability (e.g., misreading characters).

**4.2. Barrier Controller (Simulated)**

*   **Status:** The barrier can be in one of two states: `OPEN` or `CLOSED`.
*   **Open Command:** An `openBarrier` command received through the API will change the barrier state to `OPEN`.
*   **Automatic Closure:** A configurable timer will automatically close the barrier after a configurable duration when opened.
*   **Database Integration (Simulated):** The barrier should simulate integration with a license plate database. If a recognized plate is in the database, the barrier opens automatically (if configured).

**4.3. Web UI**

*   **License Plate Input:** A text field to manually enter a license plate for simulated recognition.
*   **Trigger Button:** A button to trigger the simulated LPR engine with the manually entered plate.
*   **Barrier Status:** A visual indicator showing the current barrier status (e.g., an icon or text).
*   **Event Log:** A display area showing recent LPR events (timestamp, license plate, confidence, context, and action taken - barrier opened/closed).
*   **Configuration Options:** Ability to configure:
    *   Automatic LPR mode (on/off, rate).
    *   License plate generation method (random/predefined).
    *   Closure timer duration.
    *   Database integration (on/off).
    *   Simulated country context.
    *   Error probability.

**5. API Specification**

The simulator will expose both HTTP and WebSocket APIs using the JSON-serialized CDK messages.
All data structures will adhere to the Micropak3 XSD documentation (or a compatible subset).

**5.1. HTTP API (Synchronous Requests)**

*   **Endpoint:** `http://<simulator_ip>:<http_port>/sync` (or `https://<simulator_ip>:<https_port>/sync` for HTTPS)
*   **Method:** `POST`
*   **Content-Type:** `application/json`
*   **Input Data:** JSON-serialized CDK message.  (See section 6 for data structures).
*   **Output Data:**  JSON-serialized CDK message (answer to the request).
*   **Error Handling:**
    *   **HTTP Status Codes:**
        *   `200 OK`: Request successful. The response body contains the JSON-serialized answer message.
        *   `400 Bad Request`: Invalid JSON, unknown message type, or message validation failed against the XSD. The response body may contain a JSON-serialized `answer` message with a `failed` status and an `errorText` field.
        *   `500 Internal Server Error`:  An unexpected error occurred within the simulator. The response body may contain a JSON-serialized `answer` message with a `failed` status and an `errorText` field.
    *   **CDK Message Errors:**  The `answer` message will have a `status` attribute set to `failed` and an `errorText` attribute providing a description of the error.

**5.1.1. Supported Synchronous Requests**
All Client Synchronous Requests, listed in the Micropak3 XSD documentation should be implemented.
Specific support and behavior for relevant messages are detailed below:

*   **`getConfig`:** Returns a `config` message representing the current simulated device configuration.
*   **`getCurrentLog`:** Returns an `anpr` message representing the last simulated recognition event.
*   **`getDatabase`:** Returns a `database` message representing a predefined list of "approved" license plates.
*   **`getDate`:** Returns the current simulated date and time (using the simulator's internal clock).
*   **`getImage`:**  Returns a `image` message containing a placeholder JPEG image.  (The image content doesn't need to be a real LPR image; it can be a simple test pattern).  This simulates retrieving a still image.
*   **`getInfos`:**  Returns an `infos` message with simulated device information (serial number, firmware version, capabilities).
*   **`getLog`:** Returns an `anpr` message from a simulated log based on ID.
*   **`getXSD`:**  Returns an `xsd` message containing a string representing a simplified XSD structure for basic validation testing.  A full, accurate XSD is not required for the core functionality of the simulator.
*   **`lock`:** Sets a "locked" state in the simulator, returns answer ok if password is correct, or answer error if not.
*   **`openBarrier`:** Sets the barrier state to "OPEN" and starts the closure timer. Returns an `answer` message with `status="ok"`.
*   **`resetCounters`**, **`resetEngine`**, **`resetConfig`**: returns an `answer` message with `status="ok"` and has no functional effect on the simulator.
*   **`setConfig`:** Applies the new config, returning answer ok on success, or answer error on failure.
*   **`allowSetConfig`, `forbidSetConfig`**: returns an `answer` ok, simulating a permission status on the configuration.
*   **`reboot`**: returns an `answer` ok, simulates the reboot.
*   **`editDatabase`:** adds or removes a plate from the internal simulated database, returning `answer` ok on success, `answer` error if failure.
*   **`eraseDatabase`:** clears the internal simulated database, returns answer ok on success.
*   **`testFTP`, `testNTP`, `setSecurity`, `update`, `updateWebFirmware`, `setConnectionMode`, `setup`, `getTraces`**: returns `answer` ok and does not perform any actions.
*   **`triggerOn`:** Starts a trigger session returning a triggerId in the answer.
*   **`triggerOff`:** Stops a trigger session based on the trigger id.

**5.2. WebSocket API (Asynchronous Communication)**

*   **Endpoint:** `ws://<simulator_ip>:<http_port>/async` (or `wss://<simulator_ip>:<https_port>/async` for secure connections)
*   **Protocol:** WebSocket (RFC 6455)
*   **Data Format:** JSON-serialized CDK messages (UTF-8 encoding).
*   **Direction:** Bi-directional (Simulator can send and receive messages).
*   **Keep-Alive:** The simulator should send WebSocket Ping frames periodically (e.g., every 30 seconds) to check the connection. The client should respond with a Pong frame.

**5.2.1 Supported Asynchronous Messages:**

All Server Asynchronous Messages, listed in the Micropak3 XSD documentation should be implemented.
Specific support and behavior for relevant messages are detailed below:
*   **`anpr`:** The simulator will send `anpr` messages based on the simulated LPR engine output.
    *   The `date` attribute should represent the time of the simulated recognition.
    *   The `plate` attribute should contain the generated license plate.
    *   The `reliability` attribute should contain the simulated confidence level.
    *   The `context` attribute should contain the simulated country context.
    *   A `jpeg` element with a placeholder image should be included if JPEG image output is enabled.
*   **`config`, `dgpr`, `infos`, `ioState`, `traces`, `video`**: The simulator can send these messages without functional effect.
*   **`triggerResult`:** Should send a trigger result after trigger is triggered.
*   **`setEnableStreams`:**
    *   The simulator should support `configChanges`, `infoChanges`, and `traces`, in setEnableStreams.
        When changes are made, it will send these messages in the websocket.

**5.2.2. Client Handling:**

*   **Receiving setEnableStreams:** the simulator must respond to setEnableStreams, turning on configChanges, infoChanges, and traces.
*   **Ignoring others messages:** The server will not send any other synchronous message.

**6. Data Structures (JSON-Serialized CDK Messages)**

Below are examples of data structures for the most relevant CDK messages, represented in JSON format.  These examples are based on the Micropak3 XSD structure. *Note that #text entries are Base64 encoded binary data, which may not be printable.*

**6.1. Synchronous Requests**

*   **`getConfig`:**

```json
{
  "getConfig": null
}
```

*   **`getCurrentLog`:**

```json
{
  "getCurrentLog": null
}
```

*   **`openBarrier`:**

```json
{
  "openBarrier": null
}
```

*   **`lock`:**

```json
{
  "lock": {
    "@password": "TrustNo1"
  }
}
```

**6.2. Synchronous Responses**

*   **`answer` (Success):**

```json
{
  "answer": {
    "@status": "ok"
  }
}
```

*   **`answer` (Failure):**

```json
{
  "answer": {
    "@status": "failed",
    "@errorText": "Invalid request."
  }
}
```

*   **`config`:**

```json
{
  "config": {
    "device": {
      "@name": "Simulator Device",
      "@installationHeight_cm": "150"
    },
    "network": {
      "interface": {
        "@dhcp": "true"
      }
    },
  "cameras": {
        "camera": {
          "@id": "0",
          "anpr": {
            "@direction": "both",
            "@reemitDecision": "false"
          }
        }
      }
  }
}
```

*   **`image`:**

```json
{
  "image": {
    "@date": "1678886400000",
    "jpeg": {
      "#text": "iVBORw0KGgoAAAANSUhEUgAAAAUAAAAFCAYAAACNbyblAAAAHElEQVQI12P4//8/w+r8jAwMDADnZ96ZcI6BFAAAAAElFTkSuQmCC"
    }
  }
}
```

*   **`infos`:**

```json
{
  "infos": {
    "sensor": {
      "@type": "Simulator",
      "@firmwareVersion": "1.0",
      "@serial": "SIM12345",
      "@macAddress": "00:11:22:33:44:55",
      "@status": "RUNNING"
    },
    "cameras":{
        "camera": {
          "@id": "0",
          "cameraModel": "SIM_CAM_MODEL_1",
          "size": "640X480"
        }
    }
  }
}
```

**6.3. Asynchronous Messages**

*   **`anpr`:**

```json
{
  "anpr": {
    "@date": "1678886400000",
    "decision": {
      "@plate": "AB123CD",
      "@reliability": "95",
      "@context": "F"
    }
  }
}
```

*   **`triggerResult`**:

```json
{
  "triggerResult": {
    "@date": "1678886400000",
    "@triggerId": "42",
    "decision": {
      "@plate": "AB123CD",
      "@reliability": "95",
      "@context": "F"
    }
  }
}
```

*   **`video`:**

```json
{
  "video": {
    "@cameraId": "0",
    "@date": "1678886400000",
    "@key": "true",
    "@codec": "jpeg",
    "data": {
      "#text": "iVBORw0KGgoAAAANSUhEUgAAAAUAAAAFCAYAAACNbyblAAAAHElEQVQI12P4//8/w+r8jAwMDADnZ96ZcI6BFAAAAAElFTkSuQmCC"
    }
  }
}
```

**7. Error Handling**

*   **Invalid JSON:** The simulator will reject requests with invalid JSON and return a `400 Bad Request` HTTP status code.
*   **Message Validation:** The simulator will validate incoming CDK messages against a (simplified) XSD structure.  If the message is invalid, a `400 Bad Request` will be returned with a descriptive error message.
*   **Simulated Device Errors:** The simulator can be configured to simulate device errors (e.g., camera failure, network connectivity issues).  These errors will be reflected in the `infos` message.
*   **Barrier Operation Errors:** If an attempt is made to open the barrier when it's already open, a simulated error can be returned.

**8. Configuration**

The simulator should be configurable through a configuration file (e.g., JSON, YAML). The configuration should allow setting the following parameters:

*   **HTTP/HTTPS Ports:**  Listening ports for the HTTP and HTTPS API servers.
*   **LPR Settings:**
    *   Enable/disable automatic LPR mode.
    *   Automatic LPR rate (plates/second).
    *   License plate generation method (random/predefined).
    *   License plate format (regular expression or pattern).
    *   Context probabilities (e.g., 80% F, 10% D, 10% Other).
    *   Error probability (percentage of plates with misread characters).
*   **Barrier Settings:**
    *   Automatic closure timer duration (in seconds).
    *   Database integration (enable/disable).
    *   "Approved" license plate list (for database lookup).
*   **Simulator Info**:
    *  Device type, Firmware version, Serial number.

**9. Deployment**

The simulator should be deployable as a standalone application.

**10. Security Considerations**

*   **HTTPS:** Support for HTTPS should be implemented using self-signed certificates for testing.

**11. Technology Considerations (Guidance, not mandatory)**

While specific technologies are not mandated, consider:

*   **API Server:** A framework like Flask (Python), Spring Boot (Java), or Node.js (JavaScript) for easy API development.
*   **Web UI:** HTML, CSS, JavaScript, and a framework like React, Angular, or Vue.js.
*   **Data Storage:** In-memory data structures or a simple file-based database (JSON, SQLite) for configuration and LPR history.

**12. Detailed API Data Structures**

The following examples are exhaustive, and include every possible field and possible data type, according to MicroPack3 XSD, but should be treated as a guideline.
(Note that #text entries are Base64 encoded binary data, which may not be printable.)

*   **Example config Request**

```json
{
    "setConfig": {
        "config": {
            "device": {
                "@name": "string",
                "@installationValidation": "true",
                "@installationHeight_cm": "12345",
                "@distanceToDetectionLoop_cm": "12345",
                "@distanceToBarrier_cm": "12345"
            },
            "network": {
                "interface": {
                    "@id": "12345",
                    "@dhcp": "true",
                    "@ipAddress": "127.0.0.1",
                    "@ipMask": "255.255.255.0",
                    "@ipGateway": "127.0.0.1"
                },
                "interfaceVLAN1": {
                    "@enable": "true",
                    "@idVLAN": "1234",
                    "@ipAddress": "127.0.0.1",
                    "@ipMask": "255.255.255.0",
                    "@ipGateway": "127.0.0.1"
                },
                "interfaceVLAN2": {
                    "@enable": "true",
                    "@idVLAN": "1234",
                    "@ipAddress": "127.0.0.1",
                    "@ipMask": "255.255.255.0",
                    "@ipGateway": "127.0.0.1"
                },
                "routes": {
                    "@size": "1234",
                    "route": {
                        "@id": "1234",
                        "@destination": "string",
                        "@interface": "string",
                        "@gateway": "127.0.0.1"
                    }
                },
                "dns": {
                    "@dns0": "127.0.0.1",
                    "@dns1": "127.0.0.1",
                    "@dns2": "127.0.0.1"
                },
                "ntp": {
                    "@ntp0": "string",
                    "@ntp1": "string",
                    "@ntp2": "string"
                },
                "clp": {
                    "@port": "12345",
                    "@enableUnsecuredConnections": "true",
                    "@portSsl": "12345"
                },
                "rtsp": {
                    "@port": "12345"
                },
                "ftp": {
                    "@enabled": "true",
                    "servers": {
                        "server0": {
                            "@enabled": "true",
                            "@address": "string",
                            "@port": "12345",
                            "@login": "string",
                            "@password": "string",
                            "@protocol": "ftp",
                            "@retryCount": "1234",
                            "@retryDelay_ms": "1234",
                            "@fileName": "string",
                            "@exportContext": "true",
                            "@contextFileName": "string"
                        },
                        "server1": {
                            "@enabled": "true",
                            "@address": "string",
                            "@port": "12345",
                            "@login": "string",
                            "@password": "string",
                            "@protocol": "ftp",
                            "@retryCount": "1234",
                            "@retryDelay_ms": "1234",
                            "@fileName": "string",
                            "@exportContext": "true",
                            "@contextFileName": "string"
                        },
                        "server2": {
                            "@enabled": "true",
                            "@address": "string",
                            "@port": "12345",
                            "@login": "string",
                            "@password": "string",
                            "@protocol": "ftp",
                            "@retryCount": "1234",
                            "@retryDelay_ms": "1234",
                            "@fileName": "string",
                            "@exportContext": "true",
                            "@contextFileName": "string"
                        },
                        "server3": {
                            "@enabled": "true",
                            "@address": "string",
                            "@port": "12345",
                            "@login": "string",
                            "@password": "string",
                            "@protocol": "ftp",
                            "@retryCount": "1234",
                            "@retryDelay_ms": "1234",
                            "@fileName": "string",
                            "@exportContext": "true",
                            "@contextFileName": "string"
                        }
                    }
                },
                "ssws": {
                    "@enableHttp": "true",
                    "@httpPort": "12345",
                    "@enableHttps": "true",
                    "@httpsPort": "12345"
                },
                "protocols": {
                    "nedapGenericBadge": {
                        "@enabled": "true",
                        "@address": "string",
                        "@port": "12345",
                        "@maxRetry": "1234"
                    },
                    "moobyl": {
                        "@enabled": "true",
                        "@zone": "string"
                    },
                    "SBFreeFlow": {
                        "@enabled": "true",
                        "@url": "string",
                        "@username": "string",
                        "@password": "string"
                    },
                    "amanoOne": {
                        "@enabled": "true",
                        "@url": "string",
                        "@username": "string",
                        "@password": "string",
                        "@ignoreSSLErrors": "true"
                    },
                    "tiba": {
                        "@enabled": "true",
                        "@url": "string",
                        "@username": "string",
                        "@password": "string",
                        "@guid": "string",
                        "@laneId": "1234",
                        "@ignoreSSLErrors": "true"
                    },
                    "httpPush": {
                        "servers": {
                            "server": {
                                "@id": "1234",
                                "@enable": "true",
                                "@url": "string",
                                "@filter": "string",
                                "@timeout": "1234",
                                "certificate": "string"
                            }
                        }
                    }
                }
            },
            "cameras": {
                "camera": {
                    "@id": "1234",
                    "anpr": {
                        "@squarePlates": "true",
                        "@reemitDecision": "true",
                        "@reemitDecisionTimeout": "1234",
                        "@context": "string",
                        "@direction": "both",
                        "@duplicateFilter": "true",
                        "@trailerPlates": "true",
                        "@counting": "true",
                        "@vehicleDetection": "true",
                        "@recognitionStorage": "true",
                        "avar": {
                            "@enabled": "true",
                            "@timeout_ms": "1234",
                            "sensors": {
                                "sensor0": {
                                    "@address": "string",
                                    "@port": "12345",
                                    "@useSecuredConnection": "true",
                                    "@ignoreSSLErrors": "true",
                                    "@timeout_ms": "1234"
                                }
                            }
                        },
                        "ocr": {
                            "@minPlateWidth": "1234",
                            "@maxPlateWidth": "1234",
                            "@minPlateHeight": "1234",
                            "@maxPlateHeight": "1234",
                            "@zoomPlateWidth": "1234",
                            "@minReliability": "1234",
                            "@minReliabilityForCharacters": "1234",
                            "@minCharWidthStatic": "1234",
                            "@minPlateWidthStatic8Char": "1234",
                            "@minRecognitionStatic": "1234",
                            "@minRecognition": "1234",
                            "@maxNoPlateBeforeDecision": "1234"
                        },
                        "trigger": {
                            "@reliabilityThreshold": "1234",
                            "@endPlateTimeout_ms": "1234",
                            "@activateOnIOIn": "true",
                            "@triggerIOTimeout": "1234",
                            "@triggerIOPulseMode": "falling"
                        },
                        "serial": {
                            "@export": "off",
                            "osdp": {
                                "@address": "1234"
                            }
                        }
                    },
                    "dgpr": {
                        "@direction": "both",
                        "@emptyPlatesDetection": "true",
                        "@emptyPlatesDetectionRatio": "low",
                        "@recognitionStorage": "true",
                        "ocr": {
                            "@minPlateWidth": "1234",
                            "@maxPlateWidth": "1234",
                            "@minPlateHeight": "1234",
                            "@maxPlateHeight": "1234",
                            "@zoomPlateWidth": "1234",
                            "@minReliability": "1234",
                            "@minReliabilityForCharacters": "1234",
                            "@minCharWidthStatic": "1234",
                            "@minPlateWidthStatic8Char": "1234",
                            "@minRecognitionStatic": "1234",
                            "@minRecognition": "1234",
                            "@maxNoPlateBeforeDecision": "1234"
                        },
                        "serial": {
                            "@export": "off",
                            "osdp": {
                                "@address": "1234"
                            }
                        },
                        "trigger": {
                            "@reliabilityThreshold": "1234",
                            "@endPlateTimeout_ms": "1234",
                            "@activateOnIOIn": "true",
                            "@triggerIOTimeout": "1234",
                            "@triggerIOPulseMode": "falling"
                        }
                    },
                    "speed": {
                        "@fieldOfViewY_cm": "1234",
                        "@installationHeight_cm": "1234",
                        "@installationAngle_degrees": "1234"
                    },
                    "areaOfInterest": {
                        "@enabled": "true",
                        "@excludingZone": "true",
                        "point1": {
                            "@x": "1234",
                            "@y": "1234"
                        },
                        "point2": {
                            "@x": "1234",
                            "@y": "1234"
                        },
                        "point3": {
                            "@x": "1234",
                            "@y": "1234"
                        },
                        "point4": {
                            "@x": "1234",
                            "@y": "1234"
                        },
                        "point5": {
                            "@x": "1234",
                            "@y": "1234"
                        },
                        "point6": {
                            "@x": "1234",
                            "@y": "1234"
                        }
                    },
                    "optics": {
                        "@zoom": "1234",
                        "@focus": "1234",
                        "@focusIRCutOff": "1234",
                        "@focusIRCutOn": "1234",
                        "@shutter": "string",
                        "@brightness": "1234",
                        "@sharpness": "1234",
                        "@contrast": "1234",
                        "@ISO": "string",
                        "@saturation": "1234",
                        "@expComp": "1234",
                        "@exposure": "string",
                        "@whiteBalance": "string",
                        "@metering": "string",
                        "@iris": "string",
                        "@gain": "string",
                        "@flip": "true",
                        "@autofocus": "true",
                        "@macro": "true",
                        "@irCutFilter": "on",
                        "@infoDisplay": "true"
                    },
                    "stream": {
                        "@enabled": "true",
                        "@codec": "h264",
                        "@fps": "1234",
                        "@bitrate": "1234"
                    },
                    "enslavement": {
                        "@enabled": "true",
                        "@mode": "freeFlow"
                    },
                    "stillPicture": {
                        "@quality": "1234",
                        "@enabled": "true",
                        "@plateCropped": "full"
                    },
                    "autoExposure": {
                        "@shutterPriority": "true"
                    }
                }
            },
            "database": {
                "@enabled": "true",
                "@openForAll": "true",
                "@matchTolerance": "1234"
            },
            "io": {
                "input": {
                    "@minDuration_ms": "1234"
                },
                "defaultImpulse": {
                    "@pulseMode": "falling",
                    "@duration_ms": "1234"
                }
            },
            "lightings": {
                "led": {
                    "@id": "1234",
                    "@bracketing": "true",
                    "@power": "1234",
                    "@powerLowBracketing": "1234"
                },
                "projector": {
                    "@id": "1234",
                    "@enabled": "true",
                    "@synchronizedWithCamera": "1234",
                    "@bracketing": "true",
                    "@delay": "1234",
                    "@delayLowBracketing": "1234"
                }
            },
            "services": {
                "cst": {
                    "@enabled": "true",
                    "@zone": "europe",
                    "@address": "string",
                    "@ignoreSSLErrors": "true"
                }
            }
        }
    }
}
```

*   **Example anpr asynchronous message with all possibilities**

```json
{
    "anpr": {
        "@date": "123456789",
        "@session": "1234",
        "@id": "1234",
        "new": {
            "@continue": "true",
            "@x": "1234",
            "@y": "1234",
            "@width": "1234",
            "@height": "1234",
            "@sinus": "1234"
        },
        "end": {
            "@x": "1234",
            "@y": "1234",
            "@width": "1234",
            "@height": "1234",
            "@sinus": "1234",
            "@plateOccurences": "1234",
            "@countingTrajectory": "standard"
        },
        "decision": {
            "@plate": "string",
            "@x": "1234",
            "@y": "1234",
            "@xOrigin": "1234",
            "@yOrigin": "1234",
            "@width": "1234",
            "@height": "1234",
            "@sinus": "1234",
            "@reliability": "1234",
            "@direction": "front",
            "@context": "string",
            "@context_isoAlpha2": "string",
            "@context_isoAlpha3": "string",
            "@plateOccurences": "1234",
            "@plateFrom": "master",
            "@plateBackground": "white",
            "@contrast": "1234",
            "@squarePlate": "true",
            "database": {
                "@plate": "string",
                "@distance": "1234"
            },
            "reliabilityPerCharacter": {
                "char": {
                    "@index": "1234",
                    "@reliability": "1234"
                }
            },
            "jpeg": "string",
            "contextJpeg": "string"
        },
        "speed": {
            "@instantSpeed_km_h": "1234",
            "@interdistance_ms": "1234",
            "@reliability_speed": "1234",
            "@plateFrom": "master"
        }
    }
}
```
