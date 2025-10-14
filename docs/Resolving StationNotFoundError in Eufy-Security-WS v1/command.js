export var StationCommand;
(function (StationCommand) {
    StationCommand["reboot"] = "station.reboot";
    StationCommand["isConnected"] = "station.is_connected";
    StationCommand["connect"] = "station.connect";
    StationCommand["disconnect"] = "station.disconnect";
    StationCommand["getPropertiesMetadata"] = "station.get_properties_metadata";
    StationCommand["getProperties"] = "station.get_properties";
    StationCommand["setProperty"] = "station.set_property";
    StationCommand["hasProperty"] = "station.has_property";
    StationCommand["triggerAlarm"] = "station.trigger_alarm";
    StationCommand["resetAlarm"] = "station.reset_alarm";
    StationCommand["getCommands"] = "station.get_commands";
    StationCommand["hasCommand"] = "station.has_command";
    StationCommand["chime"] = "station.chime";
    StationCommand["downloadImage"] = "station.download_image";
    StationCommand["databaseQueryLatestInfo"] = "station.database_query_latest_info";
    StationCommand["databaseQueryLocal"] = "station.database_query_local";
    StationCommand["databaseCountByDate"] = "station.database_count_by_date";
    StationCommand["databaseDelete"] = "station.database_delete";
    //Deprecated
    StationCommand["setGuardMode"] = "station.set_guard_mode";
    //Legacy
    StationCommand["isConnectedLegacy"] = "station.isConnected";
})(StationCommand || (StationCommand = {}));
//# sourceMappingURL=command.js.map