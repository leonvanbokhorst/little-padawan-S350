// Example WebSocket client for eufy-security-ws v1.9.x
// This demonstrates the correct command format and workflow

const WebSocket = require('ws');

// Configuration
const WS_URL = 'ws://localhost:3000';

// Create WebSocket connection
const ws = new WebSocket(WS_URL);

// Track received events
const stations = new Map();
const devices = new Map();

ws.on('open', () => {
    console.log('Connected to eufy-security-ws');
    
    // Step 1: Start listening to events
    // This is REQUIRED to receive station_added and device_added events
    const startListening = {
        messageId: 'start_listening_1',
        command: 'start_listening'
    };
    console.log('Sending:', JSON.stringify(startListening, null, 2));
    ws.send(JSON.stringify(startListening));
    
    // Step 2: Connect to driver (cloud and push notifications)
    setTimeout(() => {
        const connectDriver = {
            messageId: 'connect_driver_1',
            command: 'driver.connect'
        };
        console.log('Sending:', JSON.stringify(connectDriver, null, 2));
        ws.send(JSON.stringify(connectDriver));
    }, 1000);
});

ws.on('message', (data) => {
    const message = JSON.parse(data.toString());
    console.log('Received:', JSON.stringify(message, null, 2));
    
    // Handle different message types
    if (message.type === 'result') {
        console.log(`Result for ${message.messageId}:`, message.success ? 'SUCCESS' : 'FAILED');
        if (!message.success) {
            console.error('Error:', message.error);
        }
    } else if (message.type === 'event') {
        const { source, event } = message.event;
        
        // Handle station added event
        if (source === 'station' && event === 'station added') {
            const stationSerial = message.event.station;
            stations.set(stationSerial, message.event);
            console.log(`\n✓ Station discovered: ${stationSerial}`);
            
            // Now we can query this station's properties
            setTimeout(() => {
                const getProps = {
                    messageId: `get_station_props_${stationSerial}`,
                    command: 'station.get_properties',
                    serialNumber: stationSerial  // NOTE: serialNumber, NOT stationSerialNumber!
                };
                console.log('Querying station properties:', JSON.stringify(getProps, null, 2));
                ws.send(JSON.stringify(getProps));
            }, 500);
        }
        
        // Handle device added event
        if (source === 'device' && event === 'device added') {
            const deviceSerial = message.event.device;
            devices.set(deviceSerial, message.event);
            console.log(`\n✓ Device discovered: ${deviceSerial}`);
        }
    }
});

ws.on('error', (error) => {
    console.error('WebSocket error:', error);
});

ws.on('close', () => {
    console.log('Disconnected from eufy-security-ws');
    console.log(`\nDiscovered ${stations.size} stations and ${devices.size} devices`);
});

// Graceful shutdown
process.on('SIGINT', () => {
    console.log('\nShutting down...');
    ws.close();
    process.exit(0);
});
