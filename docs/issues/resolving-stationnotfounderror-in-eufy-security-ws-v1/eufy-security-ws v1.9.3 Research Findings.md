# eufy-security-ws v1.9.3 Research Findings

## Source
Documentation: https://bropat.github.io/eufy-security-ws/#/api_cmds

## Key Findings So Far

### Command Structure
All commands follow this format:
```json
{
  "messageId": "string",
  "command": "command_name"
}
```

### Station Level Commands Found
1. **station.reboot** - Reboot station
   - Parameter: `serialNumber: string`

2. **station.is_connected** - Get station connection status
   - Parameter: `serialNumber: string`
   - Returns: `{ serialNumber: string, connected: boolean }`

3. **station.connect** - Connect to station
   - Parameter: `serialNumber: string`

4. **station.disconnect** - Disconnect from station
   - No parameters shown

5. **station.get_properties_metadata** - Get properties metadata
   - Parameter: `serialNumber: string`
   - Returns: `{ properties: { [index: string]: PropertyMetadataAny } }`

6. **station.get_properties** - Get property values
   - Parameter: `serialNumber: string`
   - Returns: `{ serialNumber: string, properties: { [index: string]: PropertyValue } }`

### Driver Level Commands Found
1. **driver.set_verify_code** - Set 2FA verify code
2. **driver.set_captcha** - Set captcha
3. **driver.poll_refresh** - Update station and device information
4. **driver.is_connected** - Get cloud connection status
5. **driver.is_push_connected** - Get push notification connection status
6. **driver.connect** - Connect to cloud and push notifications
7. **driver.disconnect** - Disconnect from cloud and push notifications
8. **driver.get_video_events** - Get video events

### Important Observations
- The parameter key for stations is `serialNumber` (NOT `stationSerialNumber`, `stationSn`, or `device_sn`)
- No `station.get_devices` command found yet in documentation
- Need to check Events section and look for how devices are exposed
- The user's error mentions `StationNotFoundError` when using `stationSerialNumber` - should be `serialNumber`

## Next Steps
1. Check Events section to see how stations/devices are initially provided
2. Search GitHub issues for v1.9.x changes
3. Look for device listing commands
4. Check if devices are returned via events after connection




## Events Discovery

### Station Added Event
**Event**: `station added`
**Source**: `station`
**Schema Version**: 0+

This event is sent when a new station is found. The event contains the full station object with:
- `station: string` (starting with schema version 13+)
- Previously included full station object with properties like:
  - name, model, serialNumber, hardwareVersion, softwareVersion
  - lanIpAddress, macAddress, currentMode, guardMode
  - connected, type, timeFormat, alarmVolume, etc.

**Important**: Stations and devices are exposed via EVENTS, not via commands. When the driver connects, it emits `station added` events for each station.

### Station Removed Event
**Event**: `station removed`
**Source**: `station`
Similar structure to station added

### Other Station Events Found
- `guard mode changed` - When guard mode of a station is changed

### Key Insight
**There is NO `station.get_devices` or `driver.get_stations` command!**
- Stations are discovered via `station added` events after connecting
- Devices are likely discovered via `device added` events
- The user's error is likely because:
  1. They're using wrong parameter key (`stationSerialNumber` instead of `serialNumber`)
  2. They're trying to call commands before receiving the station/device events
  3. They need to listen for events first to get the station/device list





### Device Added Event
**Event**: `device added`
**Source**: `device`
**Schema Version**: 0+

This event is sent when a new device is found. The event contains:
- `device: string` (starting with schema version 13+)
- Previously included full device object with properties like:
  - name, model, serialNumber, hardwareVersion, softwareVersion
  - stationSerialNumber, enabled, state, battery, batteryTemperature
  - batteryLow, lastChargingDays, motionDetected, personDetected, etc.

**Critical Understanding**: Devices are also exposed via events, not commands!





## WebSocket Command Format Examples

### From Home Assistant Community Discussion
Source: https://community.home-assistant.io/t/eufy-security-integration/318353/878?page=44

**Start Listening Command**:
```json
{
  "messageId": "start_listening",
  "command": "start_listening"
}
```

**Poll Refresh Command**:
```json
{
  "messageId": "poll_refresh",
  "command": "driver.poll_refresh"
}
```

### Key Observations
1. All commands require a `messageId` field (unique identifier for the request)
2. The `command` field specifies the action
3. Additional parameters go at the same level as `command` and `messageId`





## Complete Station Command List (from source code)

Source: `/node_modules/eufy-security-ws/dist/lib/station/command.js`

All station commands require `serialNumber` parameter (NOT `stationSerialNumber`):

1. `station.reboot` - Reboot the station
2. `station.is_connected` - Check if station is connected
3. `station.connect` - Connect to station
4. `station.disconnect` - Disconnect from station
5. `station.get_properties_metadata` - Get properties metadata
6. `station.get_properties` - Get all property values
7. `station.set_property` - Set a property value
8. `station.has_property` - Check if property exists
9. `station.trigger_alarm` - Trigger alarm
10. `station.reset_alarm` - Reset alarm
11. `station.get_commands` - Get available commands
12. `station.has_command` - Check if command is supported
13. `station.chime` - Trigger chime
14. `station.download_image` - Download image
15. `station.database_query_latest_info` - Query latest database info
16. `station.database_query_local` - Query local database
17. `station.database_count_by_date` - Count database entries by date
18. `station.database_delete` - Delete database entries

**IMPORTANT**: There is NO `station.get_devices` command!

### How the Message Handler Works

From `message_handler.js` line 7-8:
```javascript
const { serialNumber, command } = message;
const station = await driver.getStation(serialNumber);
```

The handler:
1. Extracts `serialNumber` and `command` from the message
2. Calls `driver.getStation(serialNumber)` to retrieve the station
3. If the station doesn't exist, throws `StationNotFoundError`

**Root Cause of User's Error**:
- User is sending `stationSerialNumber` instead of `serialNumber`
- The handler cannot find the `serialNumber` field, so it's undefined
- `driver.getStation(undefined)` throws `StationNotFoundError`





## Complete Driver Command List (from source code)

Source: `/node_modules/eufy-security-ws/dist/lib/driver/command.js`

1. `driver.set_verify_code` - Set 2FA verification code
2. `driver.set_captcha` - Set captcha
3. `driver.poll_refresh` - Refresh station and device information
4. `driver.is_connected` - Check if connected to cloud
5. `driver.is_push_connected` - Check if push notifications connected
6. `driver.connect` - Connect to cloud and push notifications
7. `driver.disconnect` - Disconnect from cloud and push notifications
8. `driver.get_alarm_events` - Get alarm events
9. `driver.get_video_events` - Get video events
10. `driver.get_history_events` - Get history events
11. `driver.set_log_level` - Set logging level
12. `driver.get_log_level` - Get current log level
13. `driver.start_listening_logs` - Start listening to logs
14. `driver.stop_listening_logs` - Stop listening to logs
15. `driver.is_listening_logs` - Check if listening to logs
16. `driver.is_mqtt_connected` - Check if MQTT connected

**IMPORTANT**: There is NO `driver.get_stations` or `driver.get_devices` command!





## Version History and Schema Changes

### Version 1.9.x Series (Current)
- **1.9.3** (Aug 4, 2025): Updated eufy-security-client to 3.4.0
- **1.9.2** (Apr 8, 2025): Maintenance release
- **1.9.1** (Sep 29, 2024): Updated eufy-security-client to 3.1.1
- **1.9.0** (Aug 27, 2024): 
  - Requires node version >= 20
  - Migrated to tsx (removed ts-node)
  - Updated eufy-security-client to 3.1.0
  - **No schema version change mentioned**

### Version 1.8.0 (Mar 7, 2024)
- **Incremented schema version to 21**
- **Migrated to ESM (ECMAScript Modules)**
- Added many new device properties and events
- Updated eufy-security-client to 3.0.0

### Version 1.7.0 (Nov 4, 2023)
- **Incremented schema version to 20**
- Requires node version >= 18
- Added new device properties for trackers

### Key Insight
The current v1.9.x series is using **schema version 21** (inherited from v1.8.0). The schema version controls how events and responses are formatted.


