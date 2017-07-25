---
title: Vibration
description: Vibrate the device.
---
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

|Android 4.4|Android 5.1|Android 6.0|iOS 9.3|iOS 10.0|Windows 10 Store|Travis CI|
|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
|[![Build Status](http://cordova-ci.cloudapp.net:8080/buildStatus/icon?job=cordova-periodic-build/PLATFORM=android-4.4,PLUGIN=cordova-plugin-vibration)](http://cordova-ci.cloudapp.net:8080/job/cordova-periodic-build/PLATFORM=android-4.4,PLUGIN=cordova-plugin-vibration/)|[![Build Status](http://cordova-ci.cloudapp.net:8080/buildStatus/icon?job=cordova-periodic-build/PLATFORM=android-5.1,PLUGIN=cordova-plugin-vibration)](http://cordova-ci.cloudapp.net:8080/job/cordova-periodic-build/PLATFORM=android-5.1,PLUGIN=cordova-plugin-vibration/)|[![Build Status](http://cordova-ci.cloudapp.net:8080/buildStatus/icon?job=cordova-periodic-build/PLATFORM=android-6.0,PLUGIN=cordova-plugin-vibration)](http://cordova-ci.cloudapp.net:8080/job/cordova-periodic-build/PLATFORM=android-6.0,PLUGIN=cordova-plugin-vibration/)|[![Build Status](http://cordova-ci.cloudapp.net:8080/buildStatus/icon?job=cordova-periodic-build/PLATFORM=ios-9.3,PLUGIN=cordova-plugin-vibration)](http://cordova-ci.cloudapp.net:8080/job/cordova-periodic-build/PLATFORM=ios-9.3,PLUGIN=cordova-plugin-vibration/)|[![Build Status](http://cordova-ci.cloudapp.net:8080/buildStatus/icon?job=cordova-periodic-build/PLATFORM=ios-10.0,PLUGIN=cordova-plugin-vibration)](http://cordova-ci.cloudapp.net:8080/job/cordova-periodic-build/PLATFORM=ios-10.0,PLUGIN=cordova-plugin-vibration/)|[![Build Status](http://cordova-ci.cloudapp.net:8080/buildStatus/icon?job=cordova-periodic-build/PLATFORM=windows-10-store,PLUGIN=cordova-plugin-vibration)](http://cordova-ci.cloudapp.net:8080/job/cordova-periodic-build/PLATFORM=windows-10-store,PLUGIN=cordova-plugin-vibration/)|[![Build Status](https://travis-ci.org/apache/cordova-plugin-vibration.svg?branch=master)](https://travis-ci.org/apache/cordova-plugin-vibration)|

# cordova-plugin-vibration

This plugin aligns with the W3C vibration specification http://www.w3.org/TR/vibration/

This plugin provides a way to vibrate the device.

This plugin defines global objects including `navigator.vibrate`.

Although in the global scope, they are not available until after the `deviceready` event.

    document.addEventListener("deviceready", onDeviceReady, false);
    function onDeviceReady() {
        console.log(navigator.vibrate);
    }

:warning: Report issues on the [Apache Cordova issue tracker](https://issues.apache.org/jira/issues/?jql=project%20%3D%20CB%20AND%20status%20in%20%28Open%2C%20%22In%20Progress%22%2C%20Reopened%29%20AND%20resolution%20%3D%20Unresolved%20AND%20component%20%3D%20%22Plugin%20Vibration%22%20ORDER%20BY%20priority%20DESC%2C%20summary%20ASC%2C%20updatedDate%20DESC)


## Installation

    cordova plugin add cordova-plugin-vibration

## Supported Platforms

navigator.vibrate,<br />
navigator.notification.vibrate
- Amazon Fire OS
- Android
- BlackBerry 10
- Firefox OS
- iOS
- Windows Phone 7 and 8
- Windows (Windows Phone 8.1 devices only)

navigator.notification.vibrateWithPattern<br />
navigator.notification.cancelVibration
- Android
- Windows Phone 8
- Windows (Windows Phone 8.1 devices only)

## vibrate (recommended)

This function has three different functionalities based on parameters passed to it.

### Standard vibrate

Vibrates the device for a given amount of time.

    navigator.vibrate(time)

or

    navigator.vibrate([time])


-__time__: Milliseconds to vibrate the device. _(Number)_

#### Example

    // Vibrate for 3 seconds
    navigator.vibrate(3000);

    // Vibrate for 3 seconds
    navigator.vibrate([3000]);

#### iOS Quirks

- __time__: Ignores the specified time and vibrates for a pre-set amount of time.

    navigator.vibrate(3000); // 3000 is ignored

#### Windows and Blackberry Quirks

- __time__: Max time is 5000ms (5s) and min time is 1ms

    navigator.vibrate(8000); // will be truncated to 5000

### Vibrate with a pattern (Android and Windows only)
Vibrates the device with a given pattern

    navigator.vibrate(pattern);

- __pattern__: Sequence of durations (in milliseconds) for which to turn on or off the vibrator. _(Array of Numbers)_

#### Example

    // Vibrate for 1 second
    // Wait for 1 second
    // Vibrate for 3 seconds
    // Wait for 1 second
    // Vibrate for 5 seconds
    navigator.vibrate([1000, 1000, 3000, 1000, 5000]);

#### Windows Phone 8 Quirks

- vibrate(pattern) falls back on vibrate with default duration

### Cancel vibration (not supported in iOS)

Immediately cancels any currently running vibration.

    navigator.vibrate(0)

or

    navigator.vibrate([])

or

    navigator.vibrate([0])

Passing in a parameter of 0, an empty array, or an array with one element of value 0 will cancel any vibrations.

## *notification.vibrate (deprecated)

Vibrates the device for a given amount of time.

    navigator.notification.vibrate(time)

- __time__: Milliseconds to vibrate the device. _(Number)_

### Example

    // Vibrate for 2.5 seconds
    navigator.notification.vibrate(2500);

### iOS Quirks

- __time__: Ignores the specified time and vibrates for a pre-set amount of time.

        navigator.notification.vibrate();
        navigator.notification.vibrate(2500);   // 2500 is ignored

## *notification.vibrateWithPattern (deprecated)

Vibrates the device with a given pattern.

    navigator.notification.vibrateWithPattern(pattern, repeat)

- __pattern__: Sequence of durations (in milliseconds) for which to turn on or off the vibrator. _(Array of Numbers)_
- __repeat__: Optional index into the pattern array at which to start repeating (will repeat until canceled), or -1 for no repetition (default). _(Number)_

### Example

    // Immediately start vibrating
    // vibrate for 100ms,
    // wait for 100ms,
    // vibrate for 200ms,
    // wait for 100ms,
    // vibrate for 400ms,
    // wait for 100ms,
    // vibrate for 800ms,
    // (do not repeat)
    navigator.notification.vibrateWithPattern([0, 100, 100, 200, 100, 400, 100, 800]);

## *notification.cancelVibration (deprecated)

Immediately cancels any currently running vibration.

    navigator.notification.cancelVibration()

*Note - due to alignment with w3c spec, the starred methods will be phased out
