<!--
# license: Licensed to the Apache Software Foundation (ASF) under one
#         or more contributor license agreements.  See the NOTICE file
#         distributed with this work for additional information
#         regarding copyright ownership.  The ASF licenses this file
#         to you under the Apache License, Version 2.0 (the
#         "License"); you may not use this file except in compliance
#         with the License.  You may obtain a copy of the License at
#
#           http://www.apache.org/licenses/LICENSE-2.0
#
#         Unless required by applicable law or agreed to in writing,
#         software distributed under the License is distributed on an
#         "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
#         KIND, either express or implied.  See the License for the
#         specific language governing permissions and limitations
#         under the License.
-->

[![Build Status](https://travis-ci.org/apache/cordova-plugin-network-information.svg?branch=master)](https://travis-ci.org/apache/cordova-plugin-network-information)

# cordova-plugin-network-information


This plugin provides an implementation of an old version of the
[Network Information API](http://www.w3.org/TR/2011/WD-netinfo-api-20110607/).
It provides information about the device's cellular and
wifi connection, and whether the device has an internet connection.

Report issues with this plugin on the [Apache Cordova issue tracker][Apache Cordova issue tracker].

## Installation

    cordova plugin add cordova-plugin-network-information

## Supported Platforms

- Amazon Fire OS
- Android
- BlackBerry 10
- Browser
- iOS
- Windows Phone 7 and 8
- Tizen
- Windows
- Firefox OS

# Connection

> The `connection` object, exposed via `navigator.connection`,  provides information about the device's cellular and wifi connection.

## Properties

- connection.type

## Constants

- Connection.UNKNOWN
- Connection.ETHERNET
- Connection.WIFI
- Connection.CELL_2G
- Connection.CELL_3G
- Connection.CELL_4G
- Connection.CELL
- Connection.NONE

## connection.type

This property offers a fast way to determine the device's network
connection state, and type of connection.

### Quick Example

    function checkConnection() {
        var networkState = navigator.connection.type;

        var states = {};
        states[Connection.UNKNOWN]  = 'Unknown connection';
        states[Connection.ETHERNET] = 'Ethernet connection';
        states[Connection.WIFI]     = 'WiFi connection';
        states[Connection.CELL_2G]  = 'Cell 2G connection';
        states[Connection.CELL_3G]  = 'Cell 3G connection';
        states[Connection.CELL_4G]  = 'Cell 4G connection';
        states[Connection.CELL]     = 'Cell generic connection';
        states[Connection.NONE]     = 'No network connection';

        alert('Connection type: ' + states[networkState]);
    }

    checkConnection();


### API Change

Until Cordova 2.3.0, the `Connection` object was accessed via
`navigator.network.connection`, after which it was changed to
`navigator.connection` to match the W3C specification.  It's still
available at its original location, but is deprecated and will
eventually be removed.

### iOS Quirks

- <iOS7 can't detect the type of cellular network connection.
    - `navigator.connection.type` is set to `Connection.CELL` for all cellular data.

### Windows Phone Quirks

- When running in the emulator, always detects `navigator.connection.type` as `Connection.UNKNOWN`.

- Windows Phone can't detect the type of cellular network connection.
    - `navigator.connection.type` is set to `Connection.CELL` for all cellular data.

### Windows Quirks

- When running in the Phone 8.1 emulator, always detects `navigator.connection.type` as `Connection.ETHERNET`.

### Tizen Quirks

- Tizen can only detect a WiFi or cellular connection.
    - `navigator.connection.type` is set to `Connection.CELL_2G` for all cellular data.

### Firefox OS Quirks

- Firefox OS can't detect the type of cellular network connection.
    - `navigator.connection.type` is set to `Connection.CELL` for all cellular data.

### Browser Quirks

- Browser can't detect the type of network connection.
`navigator.connection.type` is always set to `Connection.UNKNOWN` when online.

# Network-related Events

## offline

The event fires when an application goes offline, and the device is
not connected to the Internet.

    document.addEventListener("offline", yourCallbackFunction, false);

### Details

The `offline` event fires when a previously connected device loses a
network connection so that an application can no longer access the
Internet.  It relies on the same information as the Connection API,
and fires when the value of `connection.type` becomes `NONE`.

Applications typically should use `document.addEventListener` to
attach an event listener once the `deviceready` event fires.

### Quick Example

    document.addEventListener("offline", onOffline, false);

    function onOffline() {
        // Handle the offline event
    }


### iOS Quirks

During initial startup, the first offline event (if applicable) takes at least a second to fire.

### Windows Phone 7 Quirks

When running in the Emulator, the `connection.status` is always unknown, so this event does _not_ fire.

### Windows Phone 8 Quirks

The Emulator reports the connection type as `Cellular`, which does not change, so the event does _not_ fire.

## online

This event fires when an application goes online, and the device
becomes connected to the Internet.

    document.addEventListener("online", yourCallbackFunction, false);

### Details

The `online` event fires when a previously unconnected device receives
a network connection to allow an application access to the Internet.
It relies on the same information as the Connection API,
and fires when the `connection.type` changes from `NONE` to any other
value.

Applications typically should use `document.addEventListener` to
attach an event listener once the `deviceready` event fires.

### Quick Example

    document.addEventListener("online", onOnline, false);

    function onOnline() {
        // Handle the online event
    }


### iOS Quirks

During initial startup, the first `online` event (if applicable) takes
at least a second to fire, prior to which `connection.type` is
`UNKNOWN`.

### Windows Phone 7 Quirks

When running in the Emulator, the `connection.status` is always unknown, so this event does _not_ fire.

### Windows Phone 8 Quirks

The Emulator reports the connection type as `Cellular`, which does not change, so events does _not_ fire.

[Apache Cordova issue tracker]: https://issues.apache.org/jira/issues/?jql=project%20%3D%20CB%20AND%20status%20in%20%28Open%2C%20%22In%20Progress%22%2C%20Reopened%29%20AND%20resolution%20%3D%20Unresolved%20AND%20component%20%3D%20%22Plugin%20Network%20Information%22%20ORDER%20BY%20priority%20DESC%2C%20summary%20ASC%2C%20updatedDate%20DESC
