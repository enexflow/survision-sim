## Survision Device Simulator - Specification Document

**Version:** 1.0
**Date:** October 26, 2023
**Author:** Gemini

### 1. Introduction

This document specifies the requirements for a simulator that emulates a Survision device (Micropak3 or later) used for License Plate Recognition (LPR). The simulator aims to provide a functional equivalent of the real device for testing and development purposes, without requiring access to the actual hardware.  The simulator will expose the same HTTP and Websocket APIs as a real Survision device, enabling developers to build and test integrations against a controlled environment. It will also include a simple web UI for basic interaction and monitoring.

### 2. Goals

*   **API Compatibility:** Emulate the Survision device's HTTP and Websocket APIs as closely as possible, including message formats and expected behavior.
*   **Controllable Environment:** Allow users to simulate various scenarios by manually inputting license plates and controlling the device's state.
*   **Web UI for Basic Interaction:** Provide a simple web UI for basic device control, state monitoring, and manual triggering of events.
*   **Simplified Configuration:** Offer a mechanism to configure key aspects of the device behavior (e.g., recognition rate, common contexts).
*   **Reproducibility:** Ensure simulator behavior is consistent and predictable, allowing for reproducible testing.

### 3. Architectural Overview

The simulator will consist of the following components:

*   **HTTP Server:** Handles synchronous requests via HTTP POST.
*   **Websocket Server:** Handles asynchronous communication via Websocket.
*   **Device Logic:** Emulates the core logic of the Survision device, including plate recognition, state management, and event generation.
*   **Web UI:** Provides a user interface for interacting with the simulator.
*   **Configuration Manager:**  Loads and stores simulator configuration.
*   **Data Store:** Stores the device state (e.g. configuration, historical recognitions)

### 4. Functional Requirements

#### 4.1. Device Logic

The device logic will emulate the following behaviors:

*   **Plate Recognition:**  When prompted (either manually or via trigger), attempt to "recognize" a license plate based on configurable success rate. Recognition results will be based on the manually inputted plate, with some configurable variability (e.g., confidence level). The simulator will also emulate DGPR.
*   **Database Functionality:** Implement a simplified database that can be manually populated via a specific message. The database enables the device to emit 'database' messages.
*   **Barrier Control:** Implement barrier state management (open/closed). The state can be controlled manually through the web UI or via specific CDK messages.
*   **State Management:** Maintain the device state (e.g., locked/unlocked, configuration parameters) and correctly reflect state changes based on API calls.
*   **Event Generation:** Generate asynchronous messages (e.g., ANPR decisions, DGPR decisions, IO state changes) based on the internal device logic and configurable parameters.  The logic for generating an 'anpr' message should include simulating the 'new', 'decision', 'speed', and 'end' events. The 'decision' event should have configurable reliability.
*   **Date Emulation:** The simulator needs to be able to produce different dates to properly emulate different states.

#### 4.2. HTTP Server

*   **Handles Synchronous Requests:** Accepts HTTP POST requests at the `/sync` endpoint.
*   **JSON Parsing:** Parses the request body as a JSON object representing a CDK message.
*   **Message Processing:** Processes the received CDK message based on the device logic.
*   **Response Generation:** Generates a JSON object representing the response CDK message.
*   **Error Handling:** Returns appropriate HTTP error codes (e.g., 400 Bad Request, 500 Internal Server Error) and corresponding error messages in JSON format for invalid requests.
*   **Locking Emulation:** Emulates implicit locking and unlocking for each request.
*   **Password Authentication (Simulated):** If a "Password" header is present in the request, use this as an indication of lock success or failure (see 5.1.5 for details).

#### 4.3. Websocket Server

*   **Handles Asynchronous Communication:**  Accepts Websocket connections at the `/async` endpoint.
*   **JSON Messaging:** Sends and receives CDK messages as JSON objects.
*   **Message Filtering:** Filters asynchronous messages based on the active `setEnableStreams` configuration (see 5.2.4).
*   **Pings:** Pings clients using Websocket ping frames to maintain the connection.
*   **Date emulation:** The date of the simulator may be changed.

#### 4.4. Web UI

The web UI will provide the following functionalities:

*   **Device Status Display:** Display the current status of the simulated device (e.g., IP address, connection state, barrier state, lock status).
*   **Plate Input:**  Provide a text field for manually entering a license plate.
*   **Trigger Recognition:**  A button to trigger a license plate recognition event using the entered plate.
*   **Barrier Control:**  Buttons to open and close the barrier manually.
*   **Configuration Settings:**
    *   Recognition Success Rate:  A slider or text field to configure the probability of a successful plate read (percentage).
    *   Default Context: A dropdown to select the default license plate context (country).
    *   Plate Reliability: Configurable reliability (0-100).
*   **Log Display:** Display a log of recent events and messages.

#### 4.5. Configuration Manager

*   **Load Configuration:** Loads initial configuration parameters from a file (e.g., `config.json`).
*   **Store Configuration:** Stores configuration changes made through the Web UI.
*   **Default Configuration:** Provides default values for all configuration parameters.

#### 4.6. Data Store

*   **In-Memory Storage:** All data, including the plate database and configuration, will be stored in-memory. This simplifies the simulator and avoids external dependencies. No data persistance is required.

### 5. API Specification

#### 5.1. HTTP API (`/sync` endpoint)

##### 5.1.1. General Request Structure

*   **Method:** POST
*   **Content-Type:** `application/json`
*   **Body:**  A JSON object representing a CDK message (see 5.1.2 for supported messages).

##### 5.1.2. Supported Messages (CDK Messages)

The simulator will support a subset of the CDK messages, focused on common use cases. The JSON format for each message is based on the described XML to JSON conversion.
Note the the base64 encoding for binary message elements such as JPEG.

**5.1.2.1. `getConfig` (Request)**

*   **Description:** Requests the simulator configuration.
*   **Input:**
    ```json
    {"getConfig": null}
    ```
*   **Output:** (See 5.1.3.1 for `config` message format)
    *   Success: `config` message.
    *   Failure: `answer` message with `status` = `"failed"` and appropriate `errorText`.

**5.1.2.2. `getCurrentLog` (Request)**

*   **Description:** Requests the current recognition.
*   **Input:**
    ```json
    {"getCurrentLog": null}
    ```
*   **Output:** (See 5.1.3.2 for `anpr` message format)
    *   Success: `anpr` message.
    *   Failure: `answer` message with `status` = `"failed"` and appropriate `errorText`.

**5.1.2.3. `getDatabase` (Request)**

*   **Description:** Requests the list of plates in the internal database.
*   **Input:**
    ```json
    {"getDatabase": null}
    ```
*   **Output:** (See 5.1.3.3 for `database` message format)
    *   Success: `database` message.
    *   Failure: `answer` message with `status` = `"failed"` and appropriate `errorText`.

**5.1.2.4. `getDate` (Request)**

*   **Description:** Requests the current date and time.
*   **Input:**
    ```json
    {"getDate": null}
    ```
*   **Output:** (See 5.1.3.4 for `date` message format)
    *   Success: `date` message.

**5.1.2.5. `getImage` (Request)**

*   **Description:** Requests a video stream image from the camera.
*   **Input:**

    ```json
    {"getImage": { "@type": "jpeg" }} //type will not be validated.
    ```
*   **Output:** (See 5.1.3.5 for `image` message format)
    *   Success: `image` message.
    *   Failure: `answer` message with `status` = `"failed"` and appropriate `errorText`.

**5.1.2.6. `getInfos` (Request)**

*   **Description:** Requests the simulator information.
*   **Input:**
    ```json
    {"getInfos": null}
    ```
*   **Output:** (See 5.1.3.6 for `infos` message format)
    *   Success: `infos` message.
    *   Failure: `answer` message with `status` = `"failed"` and appropriate `errorText`.

**5.1.2.7. `getLog` (Request)**

*   **Description:** Requests the anpr message with a specific ID (or the most recent one).
*   **Input:**

    ```json
    {"getLog": { "@id": "12345" }}
    ```
*   **Output:** (See 5.1.3.2 for `anpr` message format)
    *   Success: `anpr` message.
    *   Failure: `answer` message with `status` = `"failed"` and appropriate `errorText`.

**5.1.2.8. `getTraces` (Request)**

*   **Description:** Requests traces.
*   **Input:**

    ```json
    {"getTraces": null }
    ```
*   **Output:** (See 5.1.3.7 for `traces` message format)
    *   Success: `traces` message.
    *   Failure: `answer` message with `status` = `"failed"` and appropriate `errorText`.

**5.1.2.9. `getXSD` (Request)**

*   **Description:** Requests the XSD file. The simulator will simply return a predefined XSD (see appendix).
*   **Input:**

    ```json
    {"getXSD": null }
    ```
*   **Output:** (See 5.1.3.8 for `xsd` message format)
    *   Success: `xsd` message.
    *   Failure: `answer` message with `status` = `"failed"` and appropriate `errorText`.

**5.1.2.10. `openBarrier` (Request)**

*   **Description:** Opens the barrier.
*   **Input:**
    ```json
    {"openBarrier": null}
    ```
*   **Output:**
    *   Success: `answer` message with `status` = `"ok"`.
    *   Failure: `answer` message with `status` = `"failed"` and appropriate `errorText` (e.g., if device is locked).

**5.1.2.11. `triggerOn` (Request)**

*   **Description:** Starts a trigger session.
*   **Input:**

    ```json
    {"triggerOn": { "@cameraId": "0", "@timeout": "1000" }}
    ```
*   **Output:** (See 5.1.3.9 for `triggerAnswer` message format)
    *   Success: `triggerAnswer` message.
    *   Failure: `answer` message with `status` = `"failed"` and appropriate `errorText`.

**5.1.2.12. `triggerOff` (Request)**

*   **Description:** Ends a trigger session.
*   **Input:**

    ```json
    {"triggerOff": { "@cameraId": "0"}}
    ```
*   **Output:** (See 5.1.3.9 for `triggerAnswer` message format)
    *   Success: `triggerAnswer` message.
    *   Failure: `answer` message with `status` = `"failed"` and appropriate `errorText`.

**5.1.2.13. `lock` (Request)**

*   **Description:** Locks the device.  The simulator will only support locking and not persistant password checking, ie after each restart it is unlocked.
*   **Input:**

    ```json
    {"lock": { "@password": "password" }}
    ```
*   **Output:**
    *   Success: `answer` message with `status` = `"ok"`.
    *   Failure: `answer` message with `status` = `"failed"` and appropriate `errorText`.

**5.1.2.14. `unlock` (Request)**

*   **Description:** Unlocks the device.
*   **Input:**

    ```json
    {"unlock": null }
    ```
*   **Output:**
    *   Success: `answer` message with `status` = `"ok"`.
    *   Failure: `answer` message with `status` = `"failed"` and appropriate `errorText`.

**5.1.2.15. `resetConfig` (Request, requires lock)**

*   **Description:** Resets config to default.
*   **Input:**

    ```json
    {"resetConfig": null }
    ```
*   **Output:**
    *   Success: `answer` message with `status` = `"ok"`.
    *   Failure: `answer` message with `status` = `"failed"` and appropriate `errorText`.

**5.1.2.16. `resetEngine` (Request)**

*   **Description:** Resets recognition engine.
*   **Input:**

    ```json
    {"resetEngine": null }
    ```
*   **Output:**
    *   Success: `answer` message with `status` = `"ok"`.
    *   Failure: `answer` message with `status` = `"failed"` and appropriate `errorText`.

**5.1.2.17. `setConfig` (Request, requires lock)**

*   **Description:** Changes the configuration. In the simulator it may only change the plate reliability using config/cameras/camera/anpr. The config path will be validated.
*   **Input:**

    ```json
    {"setConfig": { "config" : { "cameras" : {"camera" : { "anpr" : {"@plateReliability" : "80"}} } } } }
    ```
*   **Output:**
    *   Success: `answer` message with `status` = `"ok"`.
    *   Failure: `answer` message with `status` = `"failed"` and appropriate `errorText`.

**5.1.2.18. `editDatabase` (Request, requires lock)**

*   **Description:** Edits the plate database. Only one action can be made by message.
*   **Input:**

    ```json
        {
            "editDatabase": {
                "addPlate": {
                    "@value": "AA123AA"
                }
            }
        }
    ```

    ```json
        {
            "editDatabase": {
                "delPlate": {
                    "@value": "AA123AA"
                }
            }
        }
    ```
*   **Output:**
    *   Success: `answer` message with `status` = `"ok"`.
    *   Failure: `answer` message with `status` = `"failed"` and appropriate `errorText`.

**5.1.2.19. `resetCounters` (Request)**

*   **Description:** resetCounters .
*   **Input:**

    ```json
        { "resetCounters": null }
    ```
*   **Output:**
    *   Success: `answer` message with `status` = `"ok"`.
    *   Failure: `answer` message with `status` = `"failed"` and appropriate `errorText`.

**5.1.2.20. `allowSetConfig` (Request, requires lock)**

*   **Description:** allows setConfig .
*   **Input:**

    ```json
        { "allowSetConfig": null }
    ```
*   **Output:**
    *   Success: `answer` message with `status` = `"ok"`.
    *   Failure: `answer` message with `status` = `"failed"` and appropriate `errorText`.

**5.1.2.21. `forbidSetConfig` (Request, requires lock)**

*   **Description:** forbids setConfig .
*   **Input:**

    ```json
        { "forbidSetConfig": null }
    ```
*   **Output:**
    *   Success: `answer` message with `status` = `"ok"`.
    *   Failure: `answer` message with `status` = `"failed"` and appropriate `errorText`.

**5.1.2.22. `calibrateZoomFocus` (Request, requires lock)**

*   **Description:** calibrates zoom focus .
*   **Input:**

    ```json
        { "calibrateZoomFocus": null }
    ```
*   **Output:**
    *   Success: `answer` message with `status` = `"ok"`.
    *   Failure: `answer` message with `status` = `"failed"` and appropriate `errorText`.

##### 5.1.3. Response Messages (CDK Messages)

**5.1.3.1. `config` (Response)**

*   **Description:** Simulator configuration (subset of the actual Survision device config).
*   **Output:**

    ```json
    {
      "config": {
        "device": {
          "@name": "Simulator Device",
          "@installationHeight_cm": "100"
        },
        "network": {
          "interface": {
            "@ipAddress": "127.0.0.1",
            "@ipMask": "255.255.255.0"
          },
          "clp": {
            "@port": "10001"
          },
          "ssws": {
            "@httpPort": "8080"
          }
        },
        "cameras": {
          "camera": {
            "anpr": {
              "@context": "F>OTHERS",
              "@squarePlates": "0",
              "@plateReliability": "50"
            }
          }
        },
        "database": {
          "@enabled": "0",
          "@openForAll": "0"
        },
        "io":{
           "defaultImpulse":{
              "@pulseMode":"rising",
              "@duration_ms":"500"
           }
        }
      }
    }
    ```

**5.1.3.2. `anpr` (Response)**

*   **Description:** License plate recognition result.
*   **Output:**

    ```json
    {
      "anpr": {
        "@date": "1672531200000",
        "decision": {
          "@plate": "AA123AA",
          "@reliability": "80",
          "@context": "F",
          "jpeg": "#BASE64_ENCODED_IMAGE_DATA#"
        }
      }
    }
    ```

**5.1.3.3. `database` (Response)**

*   **Description:** List of plates in the internal database.
*   **Output:**

    ```json
    {
      "database": {
        "plate": [
          { "@value": "AA123AA" },
          { "@value": "BB456BB" }
        ]
      }
    }
    ```

**5.1.3.4. `date` (Response)**

*   **Description:** Current date and time.
*   **Output:**

    ```json
    {
      "date": {
        "@date": "1672531200000"
      }
    }
    ```

**5.1.3.5. `image` (Response)**

*   **Description:** Video stream image.
*   **Output:**

    ```json
    {
      "image": {
        "@date": "1672531200000",
        "jpeg": "#BASE64_ENCODED_IMAGE_DATA#"
      }
    }
    ```

**5.1.3.6. `infos` (Response)**

*   **Description:** Simulator information.
*   **Output:**

    ```json
    {
      "infos": {
        "sensor": {
          "@type": "Simulator",
          "@firmwareVersion": "1.0",
          "@serial": "SIM12345",
          "@macAddress": "00:11:22:33:44:55",
          "@status": "RUNNING",
          "@locked": "0"
        },
        "cameras": {
          "camera": {
            "@id": "0",
            "enabledAlgorithms": {
              "anpr": null,
              "trigger": null
            }
          }
        },
        "network":{
            "interfaceWifi":{
              "@macAddress":"00:22:55:00:aa:cc",
              "@connected":"0"
            }
        },
        "security":{
           "@lockPasswordNeeded":"0",
           "@rsaCrypted":"0"
        },
         "anpr":{
            "@version":"1.0",
            "@possibleContexts":"F>OTHERS"
         }
      }
    }
    ```

**5.1.3.7. `traces` (Response)**

*   **Description:** Last traces data.
*   **Output:**
    ```json
    {
      "traces": {
        "currentExecution_old": "BASE64_TRACES_OLD",
        "currentExecution_current": "BASE64_TRACES_NEW"
      }
    }
    ```

**5.1.3.8. `xsd` (Response)**

*   **Description:** XSD definition file.
*   **Output:**
    ```json
    {
      "xsd": "#BASE64_ENCODED_XSD_DATA#"
    }
    ```

**5.1.3.9. `triggerAnswer` (Response)**

*   **Description:** Answer to triggerOn and triggerOff.
*   **Output:**
    ```json
    {
      "triggerAnswer": {
        "@status": "ok",
        "@triggerId": "123"
      }
    }
    ```

**5.1.3.10. `answer` (Response)**

*   **Description:** Standard answer to a client request.
*   **Output:**

    ```json
    {
      "answer": {
        "@status": "ok"
      }
    }
    ```

    ```json
    {
      "answer": {
        "@status": "failed",
        "@errorText": "Invalid request"
      }
    }
    ```

##### 5.1.4. Example HTTP Request/Response

**Request:**

```
POST /sync HTTP/1.1
Content-Type: application/json

{"getCurrentLog": null}
```

**Response (Success):**

```
HTTP/1.1 200 OK
Content-Type: application/json

{"anpr":{"@date":"1672531200000","decision":{"@plate":"AA123AA","@reliability":"80","@context":"F","jpeg":"#BASE64_ENCODED_IMAGE_DATA#"}}}
```

**Response (Failure):**

```
HTTP/1.1 400 Bad Request
Content-Type: application/json

{"answer":{"@status":"failed","@errorText":"Invalid request format"}}
```

##### 5.1.5. Lock Emulation

*   The simulator will maintain a flag indicating whether the device is locked.  The device is initially unlocked on startup.
*   The `lock` API will change the flag's value to lock or unlock the device.
*   All requests needing a lock ( marked as *requires lock*) will be checked for the flag state and fail if the device is locked. All other will continue.
*   If a "Password" header is present, the `lock` API will lock the device only if the password matches a stored password. If there isn't a stored password, the device will be locked regardless of the supplied password. When unlocking the device, the supplied password will be checked against the stored password, but only if there is a stored password, otherwise will unlock.

#### 5.2. Websocket API (`/async` endpoint)

##### 5.2.1. General

*   **Protocol:** Websocket (ws://)
*   **Message Format:** JSON objects representing CDK messages.

##### 5.2.2. Messages Sent by Simulator (Asynchronous CDK Messages)

The simulator will send the following asynchronous messages:

*   **`anpr`:**  License plate recognition results (see 5.1.3.2 for format). The rate at which these are sent is configurable through the UI, but if a trigerrer session is active, the messages should not be sent.
*   **`dgpr`:**  DGPR results. The rate at which these are sent is configurable through the UI. The device may have ANPR active, and DGPR disabled and viceversa.
*   **`ioState`:**  Simulated IO state changes.
*   **`triggerResult`:** Trigger results which consist of a license plate recognition, with the triggeID .
*   **`config` :** Sent when the configuration changes using the `setConfig` endpoing.
*   **`infos` :** Sent when the state changes and the `infoChanges` flag is active.
*   **`traces`:** Always empty.

##### 5.2.3. Messages Received by Simulator (Asynchronous CDK Messages)

*   **`setEnableStreams`:** Used to subscribe to different streams. (see 5.2.4 for format).

##### 5.2.4. `setEnableStreams` Message Format

*   **Description:**  Enables or disables the transmission of asynchronous events.
*   **Request:**

    ```json
    {
      "setEnableStreams": {
        "@configChanges": "1",
        "@infoChanges": "0",
        "@traces": "0",
        "cameras": {
          "camera": {
            "@id": "0",
            "@enabled": "0"
          }
        }
      }
    }
    ```

    *   `configChanges`:  If set to "1", the simulator will send `config` messages when the configuration changes.
    *   `infoChanges`:  If set to "1", the simulator will send `infos` messages when the device state changes.
    *   `traces`: If set to "1", the simulator will attempt to send traces, and will contain no useful data.
    *   `cameras/camera/@enabled`: Will not be used.

##### 5.2.5. Example Websocket Communication

**Client sends:**

```json
{
  "setEnableStreams": {
    "@configChanges": "1",
    "@infoChanges": "1"
  }
}
```

**Simulator sends:**

```json
{ "anpr": { "@date": "1672531200000", "decision": { "@plate": "AA123AA", "@reliability": "80", "@context": "F" } } }
```

### 6. Web UI Specification

#### 6.1. Technology (Unspecified - Recommendation to use an in process technology, for example: a library to embed the web server in the same process)

#### 6.2. Structure

The Web UI will consist of a single HTML page with JavaScript for dynamic updates.

#### 6.3. Elements

*   **Device Status Display:**
    *   IP Address: Display the simulator's IP address.
    *   Connection State: Indicate if the simulator is connected to a Websocket client.
    *   Barrier State: Display whether the barrier is open or closed.
    *   Lock State: Indicates if the device is locked or unlocked.
*   **Plate Input:**
    *   Text Field:  For entering the license plate to be recognized.
*   **Trigger Recognition:**
    *   Button: "Trigger Recognition" button to manually trigger a license plate recognition.
*   **Barrier Control:**
    *   "Open Barrier" button.
    *   "Close Barrier" button.
*   **Configuration Settings:**
    *   Recognition Success Rate: Slider (0-100) labeled "Recognition Success Rate (%)".
    *   Default Context: Dropdown menu labeled "Default Context" with options for various countries (e.g., "F", "GB", "US").
    *    Plate Reliability: Slider (0-100) labeled "Plate Reliability (0-100)".
*   **Log Display:**
    *   Text Area:  A read-only text area to display recent events and messages (e.g., "Plate recognized: AA123AA", "Barrier opened", "Configuration changed"). The simulator should limit the length.

### 7. Configuration

The simulator will load its initial configuration from a JSON file (e.g., `config.json`). This file will contain default values for the following parameters:

```json
{
  "ipAddress": "127.0.0.1",
  "httpPort": 8080,
  "wsPort": 10001,
  "recognitionSuccessRate": 75,
  "defaultContext": "F",
  "plateReliability": 80
}
```

The Web UI will allow users to modify these parameters, and the changes will be saved back to the configuration file.

### 8. Error Handling

The simulator will implement robust error handling to provide informative error messages to clients.

*   **HTTP API:**
    *   **Invalid Request Format:** Return a 400 Bad Request with a JSON body describing the error.  Example: `{"answer":{"@status":"failed","@errorText":"Invalid JSON format"}}`
    *   **Unsupported Message:** Return a 400 Bad Request with an appropriate error message. Example: `{"answer":{"@status":"failed","@errorText":"Unsupported message type"}}`
    *   **Device Locked:** Return a 403 Forbidden with an appropriate error message.  Example: `{"answer":{"@status":"failed","@errorText":"Device is locked"}}`
    *   **Internal Server Error:** Return a 500 Internal Server Error with an appropriate error message for unexpected errors. Example: `{"answer":{"@status":"failed","@errorText":"Internal server error"}}`
*   **Websocket API:**
    *   **Invalid JSON:** Close the connection with a 1002 Protocol Error (see [https://www.rfc-editor.org/rfc/rfc6455#section-7.4](https://www.rfc-editor.org/rfc/rfc6455#section-7.4)).
    *   **Unsupported Message:** Send an `answer` message back to the client indicating that the message type is not supported. (same as HTTP)

### 9. Security Considerations

*   **No Real Authentication:** The simulator does not need to implement actual user authentication. The lock state will be in memory and resetted at restart.
*   **Data Sensitivity:**  The simulator handles simulated license plate data. This data is for development purposes only, but implementers should avoid logging or storing this data unnecessarily.

### 10. Appendix: Predefined XSD

This is an example XSD that should be used by the simulator to answer `getXSD` queries:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" elementFormDefault="qualified">
  <xs:element name="msg">
    <xs:complexType>
      <xs:choice>
        <xs:element name="getConfig" type="xs:complexType"/>
        <xs:element name="getCurrentLog" type="xs:complexType"/>
        <xs:element name="getDatabase" type="xs:complexType"/>
        <xs:element name="getDate" type="xs:complexType"/>
        <xs:element name="getImage">
          <xs:complexType>
            <xs:attribute name="type" type="xs:string" use="optional"/>
          </xs:complexType>
        </xs:element>
        <xs:element name="getInfos" type="xs:complexType"/>
        <xs:element name="getLog">
          <xs:complexType>
            <xs:attribute name="id" type="xs:integer" use="required"/>
          </xs:complexType>
        </xs:element>
        <xs:element name="getXSD" type="xs:complexType"/>
        <xs:element name="openBarrier" type="xs:complexType"/>
        <xs:element name="triggerOn">
          <xs:complexType>
            <xs:attribute name="cameraId" type="xs:integer" use="optional"/>
            <xs:attribute name="forceTriggerId" type="xs:integer" use="optional"/>
            <xs:attribute name="timeout" type="xs:integer" use="optional"/>
          </xs:complexType>
        </xs:element>
        <xs:element name="triggerOff">
          <xs:complexType>
            <xs:attribute name="cameraId" type="xs:integer" use="optional"/>
          </xs:complexType>
        </xs:element>
        <xs:element name="lock">
          <xs:complexType>
            <xs:attribute name="password" type="xs:string" use="optional"/>
          </xs:complexType>
        </xs:element>
        <xs:element name="unlock" type="xs:complexType"/>
        <xs:element name="setEnableStreams">
            <xs:complexType>
                <xs:attribute name="configChanges" type="xs:string" use="optional"/>
                <xs:attribute name="infoChanges" type="xs:string" use="optional"/>
                <xs:attribute name="traces" type="xs:string" use="optional"/>
                <xs:element name="cameras">
                    <xs:complexType>
                        <xs:element name="camera">
                            <xs:complexType>
                                <xs:attribute name="id" type="xs:integer" use="required"/>
                                <xs:attribute name="enabled" type="xs:string" use="optional"/>
                            </xs:complexType>
                        </xs:element>
                    </xs:complexType>
                </xs:element>
            </xs:complexType>
        </xs:element>
        <xs:element name="resetConfig" type="xs:complexType" />
        <xs:element name="resetEngine" type="xs:complexType" />
        <xs:element name="setConfig">
            <xs:complexType>
                <xs:element name="config">
                    <xs:complexType>
                        <xs:element name="cameras">
                            <xs:complexType>
                                <xs:element name="camera">
                                    <xs:complexType>
                                        <xs:element name="anpr">
                                            <xs:complexType>
                                                <xs:element name="ocr">
                                                    <xs:complexType>
                                                        <xs:attribute name="minPlateWidth" type="xs:string" use="optional"/>
                                                        <xs:attribute name="maxPlateWidth" type="xs:string" use="optional"/>
                                                        <xs:attribute name="minPlateHeight" type="xs:string" use="optional"/>
                                                        <xs:attribute name="maxPlateHeight" type="xs:string" use="optional"/>
                                                        <xs:attribute name="zoomPlateWidth" type="xs:string" use="optional"/>
                                                        <xs:attribute name="minReliability" type="xs:string" use="optional"/>
                                                        <xs:attribute name="minCharWidthStatic" type="xs:string" use="optional"/>
                                                        <xs:attribute name="minPlateWidthStatic8Char" type="xs:string" use="optional"/>
                                                        <xs:attribute name="minRecognitionStatic" type="xs:string" use="optional"/>
                                                        <xs:attribute name="minRecognition" type="xs:string" use="optional"/>
                                                        <xs:attribute name="maxNoPlateBeforeDecision" type="xs:string" use="optional"/>
                                                    </xs:complexType>
                                                </xs:element>
                                            </xs:complexType>
                                        </xs:element>
                                    </xs:complexType>
                                </xs:element>
                            </xs:complexType>
                        </xs:element>
                    </xs:complexType>
                </xs:element>
            </xs:complexType>
        </xs:element>
        <xs:element name="editDatabase">
          <xs:complexType>
            <xs:choice>
                <xs:element name="addPlate" type="plateType"/>
                <xs:element name="delPlate" type="plateType"/>
            </xs:choice>
          </xs:complexType>
        </xs:element>
        <xs:element name="resetCounters" type="xs:complexType" />
          <xs:element name="allowSetConfig" type="xs:complexType" />
          <xs:element name="forbidSetConfig" type="xs:complexType" />
          <xs:element name="calibrateZoomFocus" type="xs:complexType" />
      </xs:choice>
    </xs:complexType>
  </xs:element>
  <xs:complexType name="plateType">
      <xs:attribute name="value" type="xs:string" use="required"/>
  </xs:complexType>
</xs:schema>
```

### 11. Future Enhancements

*   **More Complete CDK Message Support:** Implement support for a wider range of CDK messages.
*   **More Realistic Simulation:** Improve the realism of the device logic, including more accurate plate recognition, environmental factors, and sensor behavior.
*   **Configuration GUI with Validation** Implement a proper GUI validation in each configuration parameter to avoid entering invalid data.
*   **API logging** Implement logs to track all the messages received and sent in http and Websocket endpoinst.
*   **Multi-Camera Support:** Extend the simulator to support multiple simulated cameras.
*   **Video Streaming:** Implement support for video streaming, sending simulated video data.
*   **Cloud integration simulation:** Implement the simulation of the comunication to external services like CST and MOOBYL and to manage possible errors and warnings in those communications.
*   **Multi Threading** Use threads to properly emulate background processes.

### 12. Conclusion

This specification provides a detailed blueprint for building a Survision device simulator. By adhering to this document, developers can create a valuable tool for testing and developing integrations with Survision devices, improving the overall quality and reliability of their solutions.
