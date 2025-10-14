"""
FastAPI Control Tower integration with eufy-security-ws v1.9.x
Demonstrates correct WebSocket command format and event handling
"""

import asyncio
import json
from typing import Dict, Optional
import websockets

class EufySecurityClient:
    def __init__(self, ws_url: str = "ws://localhost:3000"):
        self.ws_url = ws_url
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.stations: Dict[str, dict] = {}
        self.devices: Dict[str, dict] = {}
        self.message_id_counter = 0
        
    def _next_message_id(self) -> str:
        """Generate unique message ID"""
        self.message_id_counter += 1
        return f"msg_{self.message_id_counter}"
    
    async def connect(self):
        """Connect to eufy-security-ws WebSocket server"""
        self.ws = await websockets.connect(self.ws_url)
        print(f"✓ Connected to {self.ws_url}")
        
        # Start listening to events (REQUIRED!)
        await self.send_command("start_listening")
        
        # Connect to Eufy cloud
        await self.send_command("driver.connect")
        
    async def send_command(self, command: str, **params):
        """Send a command to eufy-security-ws"""
        message = {
            "messageId": self._next_message_id(),
            "command": command,
            **params
        }
        print(f"→ Sending: {json.dumps(message, indent=2)}")
        await self.ws.send(json.dumps(message))
        
    async def get_station_properties(self, serial_number: str):
        """
        Get station properties
        IMPORTANT: Parameter is 'serialNumber' NOT 'stationSerialNumber'
        """
        await self.send_command(
            "station.get_properties",
            serialNumber=serial_number  # Correct parameter name!
        )
        
    async def get_station_devices(self, serial_number: str):
        """
        NOTE: There is NO 'station.get_devices' command!
        Devices are discovered via 'device added' events after driver.connect
        This method is here to show what NOT to do.
        """
        raise NotImplementedError(
            "station.get_devices does not exist! "
            "Devices are exposed via 'device added' events."
        )
        
    async def listen(self):
        """Listen for messages from eufy-security-ws"""
        async for message_str in self.ws:
            message = json.loads(message_str)
            print(f"← Received: {json.dumps(message, indent=2)}")
            
            # Handle result messages
            if message.get("type") == "result":
                if not message.get("success"):
                    print(f"✗ Command failed: {message.get('error')}")
                    
            # Handle event messages
            elif message.get("type") == "event":
                await self._handle_event(message["event"])
                
    async def _handle_event(self, event: dict):
        """Handle incoming events"""
        source = event.get("source")
        event_type = event.get("event")
        
        # Station added event
        if source == "station" and event_type == "station added":
            station_serial = event.get("station")
            self.stations[station_serial] = event
            print(f"\n✓ Station discovered: {station_serial}")
            
            # Query station properties
            await self.get_station_properties(station_serial)
            
        # Device added event
        elif source == "device" and event_type == "device added":
            device_serial = event.get("device")
            self.devices[device_serial] = event
            print(f"\n✓ Device discovered: {device_serial}")
            
    async def run(self):
        """Main run loop"""
        await self.connect()
        await self.listen()


# Example usage
async def main():
    client = EufySecurityClient("ws://localhost:3000")
    
    try:
        await client.run()
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
