---
title: Device Motion
description: Access accelerometer data.
---
<!---
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

|Android 4.4|Android 5.1|Android 6.0|iOS 9.3|iOS 10.0|Windows 10 Store|Travis CI|
|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
|[![Build Status](http://cordova-ci.cloudapp.net:8080/buildStatus/icon?job=cordova-periodic-build/PLATFORM=android-4.4,PLUGIN=cordova-plugin-device-motion)](http://cordova-ci.cloudapp.net:8080/job/cordova-periodic-build/PLATFORM=android-4.4,PLUGIN=cordova-plugin-device-motion/)|[![Build Status](http://cordova-ci.cloudapp.net:8080/buildStatus/icon?job=cordova-periodic-build/PLATFORM=android-5.1,PLUGIN=cordova-plugin-device-motion)](http://cordova-ci.cloudapp.net:8080/job/cordova-periodic-build/PLATFORM=android-5.1,PLUGIN=cordova-plugin-device-motion/)|[![Build Status](http://cordova-ci.cloudapp.net:8080/buildStatus/icon?job=cordova-periodic-build/PLATFORM=android-6.0,PLUGIN=cordova-plugin-device-motion)](http://cordova-ci.cloudapp.net:8080/job/cordova-periodic-build/PLATFORM=android-6.0,PLUGIN=cordova-plugin-device-motion/)|[![Build Status](http://cordova-ci.cloudapp.net:8080/buildStatus/icon?job=cordova-periodic-build/PLATFORM=ios-9.3,PLUGIN=cordova-plugin-device-motion)](http://cordova-ci.cloudapp.net:8080/job/cordova-periodic-build/PLATFORM=ios-9.3,PLUGIN=cordova-plugin-device-motion/)|[![Build Status](http://cordova-ci.cloudapp.net:8080/buildStatus/icon?job=cordova-periodic-build/PLATFORM=ios-10.0,PLUGIN=cordova-plugin-device-motion)](http://cordova-ci.cloudapp.net:8080/job/cordova-periodic-build/PLATFORM=ios-10.0,PLUGIN=cordova-plugin-device-motion/)|[![Build Status](http://cordova-ci.cloudapp.net:8080/buildStatus/icon?job=cordova-periodic-build/PLATFORM=windows-10-store,PLUGIN=cordova-plugin-device-motion)](http://cordova-ci.cloudapp.net:8080/job/cordova-periodic-build/PLATFORM=windows-10-store,PLUGIN=cordova-plugin-device-motion/)|[![Build Status](https://travis-ci.org/apache/cordova-plugin-device-motion.svg?branch=master)](https://travis-ci.org/apache/cordova-plugin-device-motion)|

# cordova-plugin-device-motion

This plugin provides access to the device's accelerometer. The accelerometer is
a motion sensor that detects the change (_delta_) in movement relative to the
current device orientation, in three dimensions along the _x_, _y_, and _z_
axis.

Access is via a global `navigator.accelerometer` object.

Although the object is attached to the global scoped `navigator`, it is not available until after the `deviceready` event.

    document.addEventListener("deviceready", onDeviceReady, false);
    function onDeviceReady() {
        console.log(navigator.accelerometer);
    }

Report issues with this plugin on the [Apache Cordova issue tracker](https://issues.apache.org/jira/issues/?jql=project%20%3D%20CB%20AND%20status%20in%20%28Open%2C%20%22In%20Progress%22%2C%20Reopened%29%20AND%20resolution%20%3D%20Unresolved%20AND%20component%20%3D%20%22Plugin%20Device%20Motion%22%20ORDER%20BY%20priority%20DESC%2C%20summary%20ASC%2C%20updatedDate%20DESC)

## Installation

    cordova plugin add cordova-plugin-device-motion

## Supported Platforms

- Amazon Fire OS
- Android
- BlackBerry 10
- Browser
- Firefox OS
- iOS
- Tizen
- Windows Phone 8
- Windows

## Methods

- navigator.accelerometer.getCurrentAcceleration
- navigator.accelerometer.watchAcceleration
- navigator.accelerometer.clearWatch

## Objects

- Acceleration

## navigator.accelerometer.getCurrentAcceleration

Get the current acceleration along the _x_, _y_, and _z_ axes.

These acceleration values are returned to the `accelerometerSuccess`
callback function.

    navigator.accelerometer.getCurrentAcceleration(accelerometerSuccess, accelerometerError);


### Example

    function onSuccess(acceleration) {
        alert('Acceleration X: ' + acceleration.x + '\n' +
              'Acceleration Y: ' + acceleration.y + '\n' +
              'Acceleration Z: ' + acceleration.z + '\n' +
              'Timestamp: '      + acceleration.timestamp + '\n');
    }

    function onError() {
        alert('onError!');
    }

    navigator.accelerometer.getCurrentAcceleration(onSuccess, onError);

### Browser Quirks

Values for X, Y, Z motion are all randomly generated in order to simulate the accelerometer.

### Android Quirks

The accelerometer is called with the `SENSOR_DELAY_UI` flag, which limits the maximum readout frequency to something between 20 and 60 Hz, depending on the device. Values for __period__ corresponding to higher frequencies will result in duplicate samples. More details can be found in the [Android API Guide](http://developer.android.com/guide/topics/sensors/sensors_overview.html#sensors-monitor).


### iOS Quirks

- iOS doesn't recognize the concept of getting the current acceleration at any given point.

- You must watch the acceleration and capture the data at given time intervals.

- Thus, the `getCurrentAcceleration` function yields the last value reported from a `watchAccelerometer` call.

## navigator.accelerometer.watchAcceleration

Retrieves the device's current `Acceleration` at a regular interval, executing
the `accelerometerSuccess` callback function each time. Specify the interval in
milliseconds via the `acceleratorOptions` object's `frequency` parameter.

The returned watch ID references the accelerometer's watch interval,
and can be used with `navigator.accelerometer.clearWatch` to stop watching the
accelerometer.

    var watchID = navigator.accelerometer.watchAcceleration(accelerometerSuccess,
                                                           accelerometerError,
                                                           accelerometerOptions);

- __accelerometerOptions__: An object with the following optional keys:
  - __frequency__: requested frequency of calls to accelerometerSuccess with acceleration data in Milliseconds. _(Number)_ (Default: 10000)


###  Example

    function onSuccess(acceleration) {
        alert('Acceleration X: ' + acceleration.x + '\n' +
              'Acceleration Y: ' + acceleration.y + '\n' +
              'Acceleration Z: ' + acceleration.z + '\n' +
              'Timestamp: '      + acceleration.timestamp + '\n');
    }

    function onError() {
        alert('onError!');
    }

    var options = { frequency: 3000 };  // Update every 3 seconds

    var watchID = navigator.accelerometer.watchAcceleration(onSuccess, onError, options);

### iOS Quirks

The API calls the success callback function at the interval requested,
but restricts the range of requests to the device between 40ms and
1000ms. For example, if you request an interval of 3 seconds,
(3000ms), the API requests data from the device every 1 second, but
only executes the success callback every 3 seconds.

## navigator.accelerometer.clearWatch

Stop watching the `Acceleration` referenced by the `watchID` parameter.

    navigator.accelerometer.clearWatch(watchID);

- __watchID__: The ID returned by `navigator.accelerometer.watchAcceleration`.

###  Example

    var watchID = navigator.accelerometer.watchAcceleration(onSuccess, onError, options);

    // ... later on ...

    navigator.accelerometer.clearWatch(watchID);

## Acceleration

Contains `Accelerometer` data captured at a specific point in time.
Acceleration values include the effect of gravity (9.81 m/s^2), so that when a
device lies flat and facing up, _x_, _y_, and _z_ values returned should be
`0`, `0`, and `9.81`.

### Properties

- __x__:  Amount of acceleration on the x-axis. (in m/s^2) _(Number)_
- __y__:  Amount of acceleration on the y-axis. (in m/s^2) _(Number)_
- __z__:  Amount of acceleration on the z-axis. (in m/s^2) _(Number)_
- __timestamp__: Creation timestamp in milliseconds. _(DOMTimeStamp)_
