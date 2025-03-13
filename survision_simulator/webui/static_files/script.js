// DOM Elements
const elements = {
    ipAddress: document.getElementById('ip-address'),
    connectionStatus: document.getElementById('connection-status'),
    barrierStatus: document.getElementById('barrier-status'),
    lockStatus: document.getElementById('lock-status'),
    plateInput: document.getElementById('plate-input'),
    triggerRecognition: document.getElementById('trigger-recognition'),
    openBarrier: document.getElementById('open-barrier'),
    closeBarrier: document.getElementById('close-barrier'),
    recognitionRate: document.getElementById('recognition-rate'),
    recognitionRateValue: document.getElementById('recognition-rate-value'),
    contextSelect: document.getElementById('context-select'),
    plateReliability: document.getElementById('plate-reliability'),
    plateReliabilityValue: document.getElementById('plate-reliability-value'),
    saveConfig: document.getElementById('save-config'),
    eventTimeline: document.getElementById('event-timeline'),
    clearLog: document.getElementById('clear-log')
};

// WebSocket connection
let ws = null;
let wsConnected = false;

// Initialize the UI
function initUI() {
    // Load initial configuration
    fetchConfig();
    
    // Set up event listeners
    setupEventListeners();
    
    // Connect to WebSocket
    connectWebSocket();
    
    // Update IP address
    updateIPAddress();
}

function setupEventListeners() {
    elements.triggerRecognition.addEventListener('click', triggerRecognition);
    elements.openBarrier.addEventListener('click', openBarrier);
    elements.closeBarrier.addEventListener('click', closeBarrier);
    elements.saveConfig.addEventListener('click', saveConfig);
    elements.clearLog.addEventListener('click', clearEventTimeline);
    
    elements.recognitionRate.addEventListener('input', () => {
        elements.recognitionRateValue.textContent = `${elements.recognitionRate.value}%`;
    });
    
    elements.plateReliability.addEventListener('input', () => {
        elements.plateReliabilityValue.textContent = `${elements.plateReliability.value}%`;
    });
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
        addEvent('success', 'WebSocket connected');
        enableStreams();
    };
    
    ws.onclose = () => {
        wsConnected = false;
        updateConnectionStatus(false);
        addEvent('error', 'WebSocket disconnected');
        setTimeout(connectWebSocket, 5000);
    };
    
    ws.onerror = (error) => {
        addEvent('error', `WebSocket error: ${error.message}`);
    };
    
    ws.onmessage = (event) => {
        try {
            const message = JSON.parse(event.data);
            handleWebSocketMessage(message);
        } catch (error) {
            addEvent('error', `Error parsing WebSocket message: ${error.message}`);
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
    if (message.anpr) {
        const plate = message.anpr.decision ? message.anpr.decision['@plate'] : 'Unknown';
        const reliability = message.anpr.decision ? message.anpr.decision['@reliability'] : 'Unknown';
        addEvent('success', `Plate recognized: ${plate} (Reliability: ${reliability})`, message.anpr);
    } else if (message.infos) {
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
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ getConfig: null })
    })
    .then(response => response.json())
    .then(data => {
        if (data.config) {
            updateConfigUI(data.config);
        }
    })
    .catch(error => {
        addEvent('error', `Error fetching config: ${error.message}`);
    });
}

// Update UI with configuration values
function updateConfigUI(config) {
    try {
        // Update recognition rate
        const plateReliability = config.cameras.camera.anpr['@plateReliability'];
        if (plateReliability) {
            elements.plateReliability.value = plateReliability;
            elements.plateReliabilityValue.textContent = `${plateReliability}%`;
        }
        
        // Update context
        const context = config.cameras.camera.anpr['@context'];
        if (context) {
            const mainContext = context.split('>')[0];
            elements.contextSelect.value = mainContext;
        }
    } catch (error) {
        addEvent('error', `Error updating config UI: ${error.message}`);
    }
}

// Trigger plate recognition
function triggerRecognition() {
    const plate = elements.plateInput.value.trim();
    
    if (!plate) {
        addEvent('warning', 'Please enter a license plate');
        return;
    }
    
    fetch('/sync', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
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
            addEvent('success', `Recognition started for plate: ${plate}`);
            simulateRecognition(plate, triggerId);
        } else {
            addEvent('error', 'Failed to start recognition');
        }
    })
    .catch(error => {
        addEvent('error', `Error triggering recognition: ${error.message}`);
    });
}

// Simulate recognition with a specific plate
function simulateRecognition(plate, triggerId) {
    setTimeout(() => {
        fetch('/sync', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                triggerOff: { 
                    "@cameraId": "0"
                } 
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.triggerAnswer && data.triggerAnswer['@status'] === 'ok') {
                addEvent('success', `Recognition completed for plate: ${plate}`);
                
                fetch('/sync', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ getCurrentLog: null })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.anpr) {
                        addEvent('success', 'Recognition result:', data.anpr);
                    } else if (data.answer && data.answer['@status'] === 'failed') {
                        addEvent('error', 'Recognition failed', data.answer);
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
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ openBarrier: null })
    })
    .then(response => response.json())
    .then(data => {
        if (data.answer && data.answer['@status'] === 'ok') {
            updateBarrierStatus(true);
            addEvent('success', 'Barrier opened');
        } else {
            addEvent('error', 'Failed to open barrier', data);
        }
    })
    .catch(error => {
        addEvent('error', 'Error opening barrier', error);
    });
}

// Close barrier
function closeBarrier() {
    updateBarrierStatus(false);
    addEvent('success', 'Barrier closed');
}

// Save configuration
function saveConfig() {
    const plateReliability = elements.plateReliability.value;
    const context = elements.contextSelect.value;
    const recognitionRate = elements.recognitionRate.value;
    
    // Update plate reliability
    fetch('/sync', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
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
            addEvent('success', 'Configuration updated successfully');
        } else {
            addEvent('error', `Failed to update configuration: ${data.answer ? data.answer['@errorText'] : 'Unknown error'}`);
        }
    })
    .catch(error => {
        addEvent('error', `Error updating configuration: ${error.message}`);
    });
}

// Update IP address
function updateIPAddress() {
    fetch('/sync', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ getInfos: null })
    })
    .then(response => response.json())
    .then(data => {
        const ipAddress = data.infos?.network?.interface?.['@ipAddress'];
        if (ipAddress) {
            elements.ipAddress.textContent = ipAddress;
        }
    })
    .catch(error => {
        addEvent('error', `Error fetching IP address: ${error.message}`);
    });
}

function addEvent(type, message, jsonData = null) {
    const event = document.createElement('div');
    event.className = `event ${type}-event`;
    
    const time = document.createElement('div');
    time.className = 'event-time';
    time.textContent = new Date().toLocaleTimeString();
    
    const messageEl = document.createElement('div');
    messageEl.className = 'event-message';
    messageEl.textContent = message;
    
    event.appendChild(time);
    event.appendChild(messageEl);
    
    if (jsonData) {
        const jsonEl = document.createElement('div');
        jsonEl.className = 'event-json';
        jsonEl.textContent = typeof jsonData === 'string' ? jsonData : JSON.stringify(jsonData, null, 2);
        event.appendChild(jsonEl);
    }
    
    elements.eventTimeline.insertBefore(event, elements.eventTimeline.firstChild);
    
    if (elements.eventTimeline.children.length > 100) {
        elements.eventTimeline.removeChild(elements.eventTimeline.lastChild);
    }
}

function clearEventTimeline() {
    elements.eventTimeline.innerHTML = '';
    addEvent('success', 'Event timeline cleared');
}

function updateConnectionStatus(connected) {
    elements.connectionStatus.textContent = connected ? 'Connected' : 'Disconnected';
    elements.connectionStatus.className = connected ? 'value connected' : 'value disconnected';
}

function updateBarrierStatus(isOpen) {
    elements.barrierStatus.textContent = isOpen ? 'Open' : 'Closed';
    elements.barrierStatus.className = isOpen ? 'value connected' : 'value disconnected';
}

function updateLockStatus(isLocked) {
    elements.lockStatus.textContent = isLocked ? 'Locked' : 'Unlocked';
    elements.lockStatus.className = isLocked ? 'value disconnected' : 'value connected';
}

// Initialize when the page loads
document.addEventListener('DOMContentLoaded', initUI);
