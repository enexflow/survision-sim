// DOM Elements
const ipAddressElement = document.getElementById('ip-address');
const connectionStatusElement = document.getElementById('connection-status');
const barrierStatusElement = document.getElementById('barrier-status');
const lockStatusElement = document.getElementById('lock-status');
const plateInputElement = document.getElementById('plate-input');
const triggerRecognitionButton = document.getElementById('trigger-recognition');
const openBarrierButton = document.getElementById('open-barrier');
const closeBarrierButton = document.getElementById('close-barrier');
const recognitionRateElement = document.getElementById('recognition-rate');
const recognitionRateValueElement = document.getElementById('recognition-rate-value');
const contextSelectElement = document.getElementById('context-select');
const plateReliabilityElement = document.getElementById('plate-reliability');
const plateReliabilityValueElement = document.getElementById('plate-reliability-value');
const saveConfigButton = document.getElementById('save-config');
const logDisplayElement = document.getElementById('log-display');
const clearLogButton = document.getElementById('clear-log');

// WebSocket connection
let ws = null;
let wsConnected = false;

// Initialize the UI
function initUI() {
    // Load initial configuration
    fetchConfig();
    
    // Set up event listeners
    triggerRecognitionButton.addEventListener('click', triggerRecognition);
    openBarrierButton.addEventListener('click', openBarrier);
    closeBarrierButton.addEventListener('click', closeBarrier);
    saveConfigButton.addEventListener('click', saveConfig);
    clearLogButton.addEventListener('click', clearLog);
    
    // Set up range input listeners
    recognitionRateElement.addEventListener('input', () => {
        recognitionRateValueElement.textContent = recognitionRateElement.value;
    });
    
    plateReliabilityElement.addEventListener('input', () => {
        plateReliabilityValueElement.textContent = plateReliabilityElement.value;
    });
    
    // Connect to WebSocket
    connectWebSocket();
    
    // Update IP address
    updateIPAddress();
}

// Connect to WebSocket server
function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.hostname;
    const port = 10001; // WebSocket port
    
    ws = new WebSocket(`${protocol}//${host}:${port}/async`);
    
    ws.onopen = () => {
        wsConnected = true;
        updateConnectionStatus(true);
        logToUI('WebSocket connected');
        enableStreams();
    };
    
    ws.onclose = () => {
        wsConnected = false;
        updateConnectionStatus(false);
        logToUI('WebSocket disconnected');
        setTimeout(connectWebSocket, 5000);
    };
    
    ws.onerror = (error) => {
        logToUI(`WebSocket error: ${error.message}`);
    };
    
    ws.onmessage = (event) => {
        try {
            const message = JSON.parse(event.data);
            handleWebSocketMessage(message);
        } catch (error) {
            logToUI(`Error parsing WebSocket message: ${error.message}`);
        }
    };
}

// Enable WebSocket streams
function enableStreams() {
    if (!wsConnected) return;
    
    const message = {
        setEnableStreams: {
            "@configChanges": "1",
            "@infoChanges": "1",
            "@traces": "0"
        }
    };
    
    ws.send(JSON.stringify(message));
}

// Handle WebSocket messages
function handleWebSocketMessage(message) {
    // Log the message
    logToUI(`Received: ${JSON.stringify(message)}`);
    
    // Handle specific message types
    if (message.anpr) {
        // Handle ANPR message
        const plate = message.anpr.decision ? message.anpr.decision['@plate'] : 'Unknown';
        const reliability = message.anpr.decision ? message.anpr.decision['@reliability'] : 'Unknown';
        logToUI(`Plate recognized: ${plate} (Reliability: ${reliability})`);
    } else if (message.infos) {
        // Handle infos message
        updateDeviceStatus(message.infos);
    }
}

// Update device status from infos message
function updateDeviceStatus(infos) {
    if (infos.sensor) {
        const locked = infos.sensor['@locked'] === '1';
        updateLockStatus(locked);
    }
}

// Fetch device configuration
function fetchConfig() {
    fetch('/sync', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ getConfig: null })
    })
    .then(response => response.json())
    .then(data => {
        if (data.config) {
            updateConfigUI(data.config);
        }
    })
    .catch(error => {
        logToUI(`Error fetching config: ${error.message}`);
    });
}

// Update UI with configuration values
function updateConfigUI(config) {
    try {
        // Update recognition rate
        const plateReliability = config.cameras.camera.anpr['@plateReliability'];
        if (plateReliability) {
            plateReliabilityElement.value = plateReliability;
            plateReliabilityValueElement.textContent = plateReliability;
        }
        
        // Update context
        const context = config.cameras.camera.anpr['@context'];
        if (context) {
            const mainContext = context.split('>')[0];
            contextSelectElement.value = mainContext;
        }
    } catch (error) {
        logToUI(`Error updating config UI: ${error.message}`);
    }
}

// Trigger plate recognition
function triggerRecognition() {
    const plate = plateInputElement.value.trim();
    
    if (!plate) {
        alert('Please enter a license plate');
        return;
    }
    
    fetch('/sync', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
            triggerOn: { 
                "@cameraId": "0",
                "@timeout": "1000"
            } 
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.triggerAnswer && data.triggerAnswer['@status'] === 'ok') {
            const triggerId = data.triggerAnswer['@triggerId'];
            logToUI(`Trigger started with ID: ${triggerId}`);
            
            // Simulate recognition with the entered plate
            simulateRecognition(plate, triggerId);
        } else {
            logToUI('Failed to start trigger');
        }
    })
    .catch(error => {
        logToUI(`Error triggering recognition: ${error.message}`);
    });
}

// Simulate recognition with a specific plate
function simulateRecognition(plate, triggerId) {
    // Wait a short time to simulate processing
    setTimeout(() => {
        // End the trigger
        fetch('/sync', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                triggerOff: { 
                    "@cameraId": "0"
                } 
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.triggerAnswer && data.triggerAnswer['@status'] === 'ok') {
                logToUI(`Trigger ended with ID: ${triggerId}`);
                
                // Get the current log to see the recognition
                fetch('/sync', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ getCurrentLog: null })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.anpr) {
                        logToUI(`Recognition result: ${JSON.stringify(data.anpr)}`);
                    } else if (data.answer && data.answer['@status'] === 'failed') {
                        logToUI(`Recognition failed: ${data.answer['@errorText']}`);
                    }
                });
            }
        });
    }, 1000);
}

// Open barrier
function openBarrier() {
    fetch('/sync', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ openBarrier: null })
    })
    .then(response => response.json())
    .then(data => {
        if (data.answer?.status === 'ok') {
            updateBarrierStatus(true);
            logToUI('Barrier opened');
        } else {
            logToUI(`Failed to open barrier: ${data.answer?.errorText ?? 'Unknown error'}`);
        }
    })
    .catch(error => {
        logToUI(`Error opening barrier: ${error.message}`);
    });
}

// Close barrier
function closeBarrier() {
    updateBarrierStatus(false);
    logToUI('Barrier closed');
}

// Save configuration
function saveConfig() {
    const plateReliability = plateReliabilityElement.value;
    const context = contextSelectElement.value;
    const recognitionRate = recognitionRateElement.value;
    
    // Update plate reliability
    fetch('/sync', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            setConfig: {
                config: {
                    cameras: {
                        camera: {
                            anpr: {
                                "@plateReliability": plateReliability
                            }
                        }
                    }
                }
            }
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.answer && data.answer['@status'] === 'ok') {
            logToUI('Configuration updated successfully');
        } else {
            logToUI(`Failed to update configuration: ${data.answer ? data.answer['@errorText'] : 'Unknown error'}`);
        }
    })
    .catch(error => {
        logToUI(`Error updating configuration: ${error.message}`);
    });
}

// Update IP address
function updateIPAddress() {
    fetch('/sync', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ getInfos: null })
    })
    .then(response => response.json())
    .then(data => {
        const ipAddress = data.infos?.network?.interface?.['@ipAddress'];
        if (ipAddress) {
            ipAddressElement.textContent = ipAddress;
        }
    })
    .catch(error => {
        logToUI(`Error fetching IP address: ${error.message}`);
    });
}

// Log message to UI
function logToUI(message) {
    const timestamp = new Date().toLocaleTimeString();
    const formattedMessage = `[${timestamp}] ${message}`;
    logDisplayElement.value = `${formattedMessage}\n${logDisplayElement.value}`;
    logDisplayElement.scrollTop = 0;
}

// Clear log
function clearLog() {
    logDisplayElement.value = '';
}

function updateConnectionStatus(connected) {
    connectionStatusElement.textContent = connected ? 'Connected' : 'Disconnected';
    connectionStatusElement.className = `status-value ${connected ? 'connected' : 'disconnected'}`;
}

function updateBarrierStatus(isOpen) {
    barrierStatusElement.textContent = isOpen ? 'Open' : 'Closed';
    barrierStatusElement.className = `status-value ${isOpen ? 'connected' : 'disconnected'}`;
}

function updateLockStatus(isLocked) {
    lockStatusElement.textContent = isLocked ? 'Locked' : 'Unlocked';
    lockStatusElement.className = `status-value ${isLocked ? 'disconnected' : 'connected'}`;
}

// Initialize when the page loads
document.addEventListener('DOMContentLoaded', initUI);
