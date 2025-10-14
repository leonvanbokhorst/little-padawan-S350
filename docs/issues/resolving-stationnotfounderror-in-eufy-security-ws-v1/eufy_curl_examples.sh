#!/bin/bash
# eufy-security-ws v1.9.x WebSocket Command Examples
# These can be adapted for use with wscat, websocat, or any WebSocket client

echo "=== eufy-security-ws v1.9.x Command Reference ==="
echo ""
echo "Note: WebSocket commands, not HTTP. Use wscat or websocat to test:"
echo "  npm install -g wscat"
echo "  wscat -c ws://localhost:3000"
echo ""

echo "1. Start Listening (REQUIRED first step)"
cat << 'JSON'
{
  "messageId": "start_1",
  "command": "start_listening"
}
JSON

echo ""
echo "2. Connect to Eufy Cloud"
cat << 'JSON'
{
  "messageId": "connect_1",
  "command": "driver.connect"
}
JSON

echo ""
echo "3. Get Station Properties (CORRECT - uses 'serialNumber')"
cat << 'JSON'
{
  "messageId": "get_props_1",
  "command": "station.get_properties",
  "serialNumber": "T8416P5025170891"
}
JSON

echo ""
echo "4. WRONG - This causes StationNotFoundError"
cat << 'JSON'
{
  "messageId": "wrong_1",
  "command": "station.get_devices",
  "stationSerialNumber": "T8416P5025170891"
}
JSON
echo "ERROR: 'station.get_devices' does not exist!"
echo "ERROR: Parameter should be 'serialNumber' not 'stationSerialNumber'"

echo ""
echo "5. Get Station Metadata"
cat << 'JSON'
{
  "messageId": "get_meta_1",
  "command": "station.get_properties_metadata",
  "serialNumber": "T8416P5025170891"
}
JSON

echo ""
echo "6. Check Station Connection Status"
cat << 'JSON'
{
  "messageId": "check_conn_1",
  "command": "station.is_connected",
  "serialNumber": "T8416P5025170891"
}
JSON

echo ""
echo "7. Connect to Station (P2P)"
cat << 'JSON'
{
  "messageId": "connect_station_1",
  "command": "station.connect",
  "serialNumber": "T8416P5025170891"
}
JSON

echo ""
echo "8. Poll Refresh (Update station/device info)"
cat << 'JSON'
{
  "messageId": "refresh_1",
  "command": "driver.poll_refresh"
}
JSON

echo ""
echo "=== Expected Event Flow ==="
echo "After 'driver.connect', you will receive:"
echo "  1. 'station added' events for each station"
echo "  2. 'device added' events for each device"
echo ""
echo "Example 'station added' event (schema v13+):"
cat << 'JSON'
{
  "type": "event",
  "event": {
    "source": "station",
    "event": "station added",
    "station": "T8416P5025170891"
  }
}
JSON

echo ""
echo "Example 'device added' event (schema v13+):"
cat << 'JSON'
{
  "type": "event",
  "event": {
    "source": "device",
    "event": "device added",
    "device": "T8410P1234567890"
  }
}
JSON
