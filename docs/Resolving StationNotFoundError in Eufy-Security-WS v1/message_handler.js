import { UnknownCommandError } from "../error.js";
import { StationCommand } from "./command.js";
import { dumpStationProperties, dumpStationPropertiesMetadata } from "./properties.js";
export class StationMessageHandler {
    static async handle(message, driver, client) {
        const { serialNumber, command } = message;
        const station = await driver.getStation(serialNumber);
        switch (command) {
            case StationCommand.reboot:
                station.rebootHUB();
                return client.schemaVersion >= 13 ? { async: true } : {};
            case StationCommand.setGuardMode:
                if (client.schemaVersion <= 12) {
                    station.setGuardMode(message.mode);
                    return {};
                }
                else {
                    throw new UnknownCommandError(command);
                }
            case StationCommand.isConnected:
                {
                    const result = station.isConnected();
                    if (client.schemaVersion <= 3) {
                        return { connected: result };
                    }
                    else if (client.schemaVersion >= 4) {
                        return {
                            serialNumber: station.getSerial(),
                            connected: result
                        };
                    }
                    else {
                        throw new UnknownCommandError(command);
                    }
                }
            case StationCommand.isConnectedLegacy:
                {
                    if (client.schemaVersion <= 12) {
                        const result = station.isConnected();
                        return { connected: result };
                    }
                    else {
                        throw new UnknownCommandError(command);
                    }
                }
            /*case StationCommand.getCameraInfo:
                await station.getCameraInfo().catch((error) => {
                    throw error;
                });
                return client.schemaVersion >= 13 ? { async: true } : {};
            case StationCommand.getStorageInfo:
                await station.getStorageInfo().catch((error) => {
                    throw error;
                });
                return client.schemaVersion >= 13 ? { async: true } : {};*/
            case StationCommand.connect:
                await station.connect().catch((error) => {
                    throw error;
                });
                return {};
            case StationCommand.disconnect:
                station.close();
                return {};
            case StationCommand.getPropertiesMetadata:
                {
                    const properties = station.getPropertiesMetadata();
                    if (client.schemaVersion <= 3) {
                        return { properties: properties };
                    }
                    else if (client.schemaVersion >= 4) {
                        return {
                            serialNumber: station.getSerial(),
                            properties: properties
                        };
                    }
                    else {
                        return {
                            serialNumber: station.getSerial(),
                            properties: dumpStationPropertiesMetadata(station, client.schemaVersion)
                        };
                    }
                }
            case StationCommand.getProperties:
                {
                    const properties = station.getProperties();
                    if (client.schemaVersion <= 3) {
                        return { properties: properties };
                    }
                    else if (client.schemaVersion >= 4) {
                        return {
                            serialNumber: station.getSerial(),
                            properties: properties
                        };
                    }
                    else {
                        return {
                            serialNumber: station.getSerial(),
                            properties: dumpStationProperties(station, client.schemaVersion)
                        };