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
    plateReliability: document.getElementById('plate-reliability'),
    plateReliabilityValue: document.getElementById('plate-reliability-value'),
    saveConfig: document.getElementById('save-config'),
    eventTimeline: document.getElementById('event-timeline'),
    clearLog: document.getElementById('clear-log'),
    
    // New elements
    configChanges: document.getElementById('config-changes'),
    infoChanges: document.getElementById('info-changes'),
    traces: document.getElementById('traces'),
    enableStreams: document.getElementById('enable-streams'),
    dbPlateInput: document.getElementById('db-plate-input'),
    addPlate: document.getElementById('add-plate'),
    refreshDatabase: document.getElementById('refresh-database'),
    platesList: document.getElementById('plates-list'),
    getInfos: document.getElementById('get-infos'),
    getLog: document.getElementById('get-log'),
    getTraces: document.getElementById('get-traces'),
    triggerOn: document.getElementById('trigger-on'),
    triggerOff: document.getElementById('trigger-off')
};

// WebSocket connection
let ws = null;
let wsConnected = false;
let activeTrigger = null;

// Initialize the UI
async function initUI() {
    // Load initial configuration
    await fetchConfig();
    
    // Set up event listeners
    setupEventListeners();
    
    // Connect to WebSocket
    connectWebSocket();
    
    // Update IP address
    await updateIPAddress();
    
    // Load database plates
    await fetchDatabasePlates();
}

function setupEventListeners() {
    elements.triggerRecognition.addEventListener('click', triggerRecognition);
    elements.openBarrier.addEventListener('click', openBarrier);
    elements.closeBarrier.addEventListener('click', closeBarrier);
    elements.saveConfig.addEventListener('click', saveConfig);
    elements.clearLog.addEventListener('click', clearEventTimeline);
    
    elements.plateReliability.addEventListener('input', () => {
        elements.plateReliabilityValue.textContent = `${elements.plateReliability.value}%`;
    });
    
    // New event listeners
    elements.enableStreams.addEventListener('click', enableStreams);
    elements.addPlate.addEventListener('click', addPlateToDatabase);
    elements.refreshDatabase.addEventListener('click', fetchDatabasePlates);
    elements.getInfos.addEventListener('click', getInfos);
    elements.getLog.addEventListener('click', getLog);
    elements.getTraces.addEventListener('click', getTraces);
    elements.triggerOn.addEventListener('click', manualTriggerOn);
    elements.triggerOff.addEventListener('click', manualTriggerOff);
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
            addEvent('error', `Error handling WebSocket message: ${error.message}`, event.data);
        }
    };
}

// Enable WebSocket streams
function enableStreams() {
    if (!wsConnected) return;
    
    const message = {
        setEnableStreams: {
            "@configChanges": elements.configChanges.checked ? "1" : "0",
            "@infoChanges": elements.infoChanges.checked ? "1" : "0",
            "@traces": elements.traces.checked ? "1" : "0"
        }
    };
    
    ws.send(JSON.stringify(message));
    addEvent('success', 'Updating WebSocket stream settings', message);
}

// Handle WebSocket messages
function handleWebSocketMessage(message) {
    if (message.anpr) {
        const plate = message.anpr.decision ? message.anpr.decision['@plate'] : 'Unknown';
        const reliability = message.anpr.decision ? message.anpr.decision['@reliability'] : 'Unknown';
        addEvent('success', `Plate recognized: ${plate} (Reliability: ${reliability})`, message.anpr);
        
        // Auto-refresh database after recognition
        fetchDatabasePlates();
    } else if (message.infos) {
        updateDeviceStatus(message.infos);
    } else if (message.answer?.subscriptions) {
        addEvent('success', 'WebSocket streams enabled', message.answer.subscriptions);
    } else if (message.database) {
        updateDatabaseUI(message.database);
    } else {
        addEvent('info', 'Received message', message);
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
async function fetchConfig() {
    try {
        const response = await fetch('/sync', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ getConfig: null })
        });
        const data = await response.json();
        
        if (data.config) {
            updateConfigUI(data.config);
        }
    } catch (error) {
        addEvent('error', `Error fetching config: ${error.message}`);
    }
}

// Update UI with configuration values
function updateConfigUI(config) {
    try {
        // Update plate reliability
        const plateReliability = config.cameras.camera.anpr['@plateReliability'];
        if (plateReliability) {
            elements.plateReliability.value = plateReliability;
            elements.plateReliabilityValue.textContent = `${plateReliability}%`;
        }
    } catch (error) {
        addEvent('error', `Error updating config UI: ${error.message}`);
    }
}

// Trigger plate recognition
async function triggerRecognition() {
    const plate = elements.plateInput.value.trim();
    
    if (!plate) {
        addEvent('warning', 'Please enter a license plate');
        return;
    }
    
    try {
        const response = await fetch('/sync', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                triggerOn: { 
                    "@cameraId": "0",
                    "@timeout": "1000"
                } 
            })
        });
        const data = await response.json();
        
        if (data.triggerAnswer && data.triggerAnswer['@status'] === 'ok') {
            const triggerId = data.triggerAnswer['@triggerId'];
            addEvent('success', `Recognition started for plate: ${plate}`);
            await simulateRecognition(plate, triggerId);
        } else {
            addEvent('error', 'Failed to start recognition');
        }
    } catch (error) {
        addEvent('error', `Error triggering recognition: ${error.message}`);
    }
}

// Simulate recognition with a specific plate
async function simulateRecognition(plate, triggerId) {
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    try {
        const response = await fetch('/sync', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                triggerOff: { 
                    "@cameraId": "0"
                } 
            })
        });
        const data = await response.json();
        
        if (data.triggerAnswer && data.triggerAnswer['@status'] === 'ok') {
            addEvent('success', `Recognition completed for plate: ${plate}`);
            
            const logResponse = await fetch('/sync', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ getCurrentLog: null })
            });
            const logData = await logResponse.json();
            
            if (logData.anpr) {
                addEvent('success', 'Recognition result:', logData.anpr);
                // Auto-refresh database after recognition
                await fetchDatabasePlates();
            } else if (logData.answer && logData.answer['@status'] === 'failed') {
                addEvent('error', 'Recognition failed', logData.answer);
            }
        }
    } catch (error) {
        addEvent('error', `Error in recognition simulation: ${error.message}`);
    }
}

// Manual trigger on
async function manualTriggerOn() {
    try {
        const response = await fetch('/sync', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                triggerOn: { 
                    "@cameraId": "0",
                    "@timeout": "5000"
                } 
            })
        });
        const data = await response.json();
        
        if (data.triggerAnswer && data.triggerAnswer['@status'] === 'ok') {
            const triggerId = data.triggerAnswer['@triggerId'];
            activeTrigger = triggerId;
            addEvent('success', `Manual trigger started with ID: ${triggerId}`);
        } else {
            addEvent('error', 'Failed to start manual trigger');
        }
    } catch (error) {
        addEvent('error', `Error starting manual trigger: ${error.message}`);
    }
}

// Manual trigger off
async function manualTriggerOff() {
    if (!activeTrigger) {
        addEvent('warning', 'No active trigger to stop');
        return;
    }
    
    try {
        const response = await fetch('/sync', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                triggerOff: { 
                    "@cameraId": "0"
                } 
            })
        });
        const data = await response.json();
        
        if (data.triggerAnswer && data.triggerAnswer['@status'] === 'ok') {
            addEvent('success', `Manual trigger stopped with ID: ${activeTrigger}`);
            activeTrigger = null;
        } else {
            addEvent('error', 'Failed to stop manual trigger');
        }
    } catch (error) {
        addEvent('error', `Error stopping manual trigger: ${error.message}`);
    }
}

// Open barrier
async function openBarrier() {
    try {
        const response = await fetch('/sync', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ openBarrier: null })
        });
        const data = await response.json();
        
        if (data.answer && data.answer['@status'] === 'ok') {
            updateBarrierStatus(true);
            addEvent('success', 'Barrier opened');
        } else {
            addEvent('error', 'Failed to open barrier', data);
        }
    } catch (error) {
        addEvent('error', 'Error opening barrier', error);
    }
}

// Close barrier
function closeBarrier() {
    updateBarrierStatus(false);
    addEvent('success', 'Barrier closed');
}

// Save configuration
async function saveConfig() {
    const plateReliability = elements.plateReliability.value;
    
    try {
        const response = await fetch('/sync', {
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
        });
        const data = await response.json();
        
        if (data.answer && data.answer['@status'] === 'ok') {
            addEvent('success', 'Configuration updated successfully');
        } else {
            addEvent('error', `Failed to update configuration: ${data.answer ? data.answer['@errorText'] : 'Unknown error'}`);
        }
    } catch (error) {
        addEvent('error', `Error updating configuration: ${error.message}`);
    }
}

// Fetch database plates
async function fetchDatabasePlates() {
    try {
        const response = await fetch('/sync', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ getDatabase: null })
        });
        const data = await response.json();
        
        if (data.database) {
            updateDatabaseUI(data.database);
        } else {
            addEvent('error', 'Failed to fetch database plates', data);
        }
    } catch (error) {
        addEvent('error', `Error fetching database plates: ${error.message}`);
    }
}

// Update database UI
function updateDatabaseUI(database) {
    elements.platesList.innerHTML = '';
    
    if (!Array.isArray(database)) {
        addEvent('warning', 'Invalid database format');
        return;
    }
    
    if (database.length === 0) {
        const emptyMessage = document.createElement('div');
        emptyMessage.className = 'plate-item';
        emptyMessage.textContent = 'No plates in database';
        elements.platesList.appendChild(emptyMessage);
        return;
    }
    
    for (const plate of database) {
        const plateValue = plate.value || plate['@value'];
        if (!plateValue) continue;
        
        const plateItem = document.createElement('div');
        plateItem.className = 'plate-item';
        
        const plateText = document.createElement('span');
        plateText.className = 'plate-value';
        plateText.textContent = plateValue;
        
        const deleteButton = document.createElement('button');
        deleteButton.className = 'delete-plate';
        deleteButton.innerHTML = '<i class="fas fa-trash"></i>';
        deleteButton.addEventListener('click', () => deletePlate(plateValue));
        
        plateItem.appendChild(plateText);
        plateItem.appendChild(deleteButton);
        elements.platesList.appendChild(plateItem);
    }
}

// Add plate to database
async function addPlateToDatabase() {
    const plate = elements.dbPlateInput.value.trim();
    
    if (!plate) {
        addEvent('warning', 'Please enter a license plate');
        return;
    }
    
    try {
        const response = await fetch('/sync', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                editDatabase: {
                    addPlate: {
                        "@value": plate
                    }
                }
            })
        });
        const data = await response.json();
        
        if (data.answer && data.answer['@status'] === 'ok') {
            addEvent('success', `Plate ${plate} added to database`);
            elements.dbPlateInput.value = '';
            await fetchDatabasePlates();
        } else {
            addEvent('error', `Failed to add plate: ${data.answer ? data.answer['@errorText'] : 'Unknown error'}`);
        }
    } catch (error) {
        addEvent('error', `Error adding plate: ${error.message}`);
    }
}

// Delete plate from database
async function deletePlate(plate) {
    try {
        const response = await fetch('/sync', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                editDatabase: {
                    delPlate: {
                        "@value": plate
                    }
                }
            })
        });
        const data = await response.json();
        
        if (data.answer && data.answer['@status'] === 'ok') {
            addEvent('success', `Plate ${plate} removed from database`);
            await fetchDatabasePlates();
        } else {
            addEvent('error', `Failed to remove plate: ${data.answer ? data.answer['@errorText'] : 'Unknown error'}`);
        }
    } catch (error) {
        addEvent('error', `Error removing plate: ${error.message}`);
    }
}

// Get device infos
async function getInfos() {
    try {
        const response = await fetch('/sync', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ getInfos: null })
        });
        const data = await response.json();
        
        if (data.infos) {
            addEvent('success', 'Device information retrieved', data.infos);
            updateDeviceStatus(data.infos);
        } else {
            addEvent('error', 'Failed to get device information');
        }
    } catch (error) {
        addEvent('error', `Error getting device information: ${error.message}`);
    }
}

// Get log
async function getLog() {
    try {
        const response = await fetch('/sync', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ getLog: null })
        });
        const data = await response.json();
        
        if (data.anpr) {
            addEvent('success', 'Log retrieved', data.anpr);
        } else {
            addEvent('warning', 'No log data available');
        }
    } catch (error) {
        addEvent('error', `Error getting log: ${error.message}`);
    }
}

// Get traces
async function getTraces() {
    try {
        const response = await fetch('/sync', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ getTraces: null })
        });
        const data = await response.json();
        
        if (data.traces) {
            addEvent('success', 'Traces retrieved', data.traces);
        } else {
            addEvent('warning', 'No trace data available');
        }
    } catch (error) {
        addEvent('error', `Error getting traces: ${error.message}`);
    }
}

// Update IP address
async function updateIPAddress() {
    try {
        const response = await fetch('/sync', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ getInfos: null })
        });
        const data = await response.json();
        
        const ipAddress = data.infos?.network?.interface?.['@ipAddress'];
        if (ipAddress) {
            elements.ipAddress.textContent = ipAddress;
        }
    } catch (error) {
        addEvent('error', `Error fetching IP address: ${error.message}`);
    }
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
