<!--
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
# 
# http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
#  KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#
-->
# Release Notes

### 2.1.0 (Jan 15, 2016)
* CB-10319 **Android** Adding reflective helper methods for permission requests
* CB-8523 Fixed accuracy when `enableHighAccuracy: false` on **iOS**.
* CB-10286 Don't skip automatic tests on **Android** devices
* CB-10277 Error callback should be called w/ `PositionError` when location access is denied
* CB-10285 Added tests for `PositionError` constants
* CB-10278 geolocation `watchPosition` doesn't return `watchID` string
* CB-8443 **Android** nothing happens if `GPS` is turned off
* CB-10204 Fix `getCurrentPosition` options on **Android**
* CB-7146 Remove built-in `WebView navigator.geolocation` manual tests
* CB-2845 `PositionError` constants not attached to prototype as specified in W3C document

### 2.0.0 (Nov 18, 2015)
* [CB-10035](https://issues.apache.org/jira/browse/CB-10035) Updated `RELEASENOTES` to be newest to oldest
* [CB-9907](https://issues.apache.org/jira/browse/CB-9907) Handle **iOS** tests that fail when ios simulator does not have a location
* [CB-8826](https://issues.apache.org/jira/browse/CB-8826) Check for `NSLocationWhenInUseUsageDescription` first
* [CB-9105](https://issues.apache.org/jira/browse/CB-9105): Fixing `JS` errors in the shim
* Added support for new permissions model for **Android 6.0** aka **Marshmallow**
* Expect `lastPosition` to have a `timestamp` that is already in `msecs`
* [CB-4596](https://issues.apache.org/jira/browse/CB-4596) Date objects are supposed to be `DOMTimeStamp`
* Fixing contribute link.
* [CB-9355](https://issues.apache.org/jira/browse/CB-9355) Fix Geolocation plugin start watch fail related to unset `MovementThreshold` on **Windows 10**

### 1.0.1 (Jun 17, 2015)
* [CB-9128](https://issues.apache.org/jira/browse/CB-9128) cordova-plugin-geolocation documentation translation: cordova-plugin-geolocation
* fix npm md issue
* [CB-8845](https://issues.apache.org/jira/browse/CB-8845) Updated comment why Android tests are currently pended
* [CB-8845](https://issues.apache.org/jira/browse/CB-8845) Pended tests for Android
* Add more install text for legacy versions of cordova tools. This closes #36

### 1.0.0 (Apr 15, 2015)
* [CB-8746](https://issues.apache.org/jira/browse/CB-8746) gave plugin major version bump
* [CB-8683](https://issues.apache.org/jira/browse/CB-8683) changed plugin-id to pacakge-name
* [CB-8653](https://issues.apache.org/jira/browse/CB-8653) properly updated translated docs to use new id
* [CB-8653](https://issues.apache.org/jira/browse/CB-8653) updated translated docs to use new id
* Use TRAVIS_BUILD_DIR, install paramedic by npm
* [CB-8681](https://issues.apache.org/jira/browse/CB-8681) Fixed occasional test failures
* docs: added Windows to supported platforms
* [CB-8653](https://issues.apache.org/jira/browse/CB-8653) Updated Readme
* [CB-8659](https://issues.apache.org/jira/browse/CB-8659): ios: 4.0.x Compatibility: Remove use of initWebView method
* [CB-8659](https://issues.apache.org/jira/browse/CB-8659): ios: 4.0.x Compatibility: Remove use of deprecated headers
* Wrong parameter in Firefox OS plugin
* [CB-8568](https://issues.apache.org/jira/browse/CB-8568) Integrate TravisCI
* [CB-8438](https://issues.apache.org/jira/browse/CB-8438) cordova-plugin-geolocation documentation translation: cordova-plugin-geolocation
* [CB-8538](https://issues.apache.org/jira/browse/CB-8538) Added package.json file
* [CB-8443](https://issues.apache.org/jira/browse/CB-8443) Geolocation tests fail on Windows due to done is called multiple times

### 0.3.12 (Feb 04, 2015)
* [CB-8351](https://issues.apache.org/jira/browse/CB-8351) ios: Use argumentForIndex rather than NSArray extension

### 0.3.11 (Dec 02, 2014)
* Do not stop updating location when the error is `kCLErrorLocationUnknown`
* [CB-8094](https://issues.apache.org/jira/browse/CB-8094) Pended auto tests for **Windows** Store since they require user interaction
* [CB-8085](https://issues.apache.org/jira/browse/CB-8085) Fix geolocation plugin on **Windows**
* [CB-7977](https://issues.apache.org/jira/browse/CB-7977) Mention `deviceready` in plugin docs
* [CB-7700](https://issues.apache.org/jira/browse/CB-7700) cordova-plugin-geolocation documentation translation: cordova-plugin-geolocation

### 0.3.10 (Sep 17, 2014)
* [CB-7556](https://issues.apache.org/jira/browse/CB-7556) iOS: Clearing all Watches does not stop Location Services
* [CB-7158](https://issues.apache.org/jira/browse/CB-7158) Fix geolocation for ios 8
* Revert [CB-6911](https://issues.apache.org/jira/browse/CB-6911) partially (keeping Info.plist key installation for iOS 8)
* [CB-6911](https://issues.apache.org/jira/browse/CB-6911) Geolocation fails in iOS 8
* [CB-5114](https://issues.apache.org/jira/browse/CB-5114) Windows 8.1 - Use a new proxy as old geolocation methods is deprecated
* [CB-5114](https://issues.apache.org/jira/browse/CB-5114) Append Windows 8.1 into plugin.xml + Optimize Windows 8 Geolocation proxy
* Renamed test dir, added nested plugin.xml
* added documentation for manual tests
* [CB-7146](https://issues.apache.org/jira/browse/CB-7146) Added manual tests
* Removed js-module for tests from plugin.xml
* Changing cdvtest format to use module exports
* register tests using new style
* Convert tests to new style
* Removed amazon-fireos code for geolocation.
* [CB-7571](https://issues.apache.org/jira/browse/CB-7571) Bump version of nested plugin to match parent plugin

### 0.3.9 (Aug 06, 2014)
* **FFOS** update GeolocationProxy.js
* [CB-7187](https://issues.apache.org/jira/browse/CB-7187) ios: Add explicit dependency on CoreLocation.framework
* [CB-7187](https://issues.apache.org/jira/browse/CB-7187) Delete unused #import of CDVShared.h
* [CB-6127](https://issues.apache.org/jira/browse/CB-6127) Updated translations for docs
* ios: Changed distanceFilter from none to 5 meters, prevents it from spamming the callback even though nothing changed.

### 0.3.8 (Jun 05, 2014)
* [CB-6127](https://issues.apache.org/jira/browse/CB-6127) Spanish and French Translations added. Github close #14
* [CB-6804](https://issues.apache.org/jira/browse/CB-6804) Add license
* [CB-5416](https://issues.apache.org/jira/browse/CB-5416) - Adding support for auto-managing permissions
* [CB-6491](https://issues.apache.org/jira/browse/CB-6491) add CONTRIBUTING.md
* pass by only coords
* proper implementation for firefoxos
* call FxOS's getCurrentProxy added

### 0.3.7 (Apr 17, 2014)
* [CB-6422](https://issues.apache.org/jira/browse/CB-6422): [windows8] use cordova/exec/proxy
* [CB-6212](https://issues.apache.org/jira/browse/CB-6212): [iOS] fix warnings compiled under arm64 64-bit
* [CB-5977](https://issues.apache.org/jira/browse/CB-5977): [android] Removing the Android Geolocation Code.  Mission Accomplished.
* [CB-6460](https://issues.apache.org/jira/browse/CB-6460): Update license headers
* Add NOTICE file

### 0.3.6 (Feb 05, 2014)
* add ubuntu platform support
* [CB-5326](https://issues.apache.org/jira/browse/CB-5326) adding FFOS permission and updating supported platforms
* [CB-5729](https://issues.apache.org/jira/browse/CB-5729) [BlackBerry10] Update GeolocationProxy to return collapsed object

### 0.3.5 (Jan 02, 2014)
* [CB-5658](https://issues.apache.org/jira/browse/CB-5658) Add doc/index.md for Geolocation plugin
* windows8: adds missing reference to PositionError (w/o it the app crashes)
* Removing incorrectly added closing comments for wp7 platform in plugin.xml

### 0.3.4 (Dec 4, 2013)
* Append proxy to platform definition in plugin.xml
* Append windows 8 Geolocation proxy
* Code clean-up for android src.
* Updated amazon-fireos platform + reverting some of the fixes in android code.
* Added amazon-fireos platform + some of the fixes in android code.
* [CB-5334](https://issues.apache.org/jira/browse/CB-5334) [BlackBerry10] Use command proxy
* call FxOS's getCurrentProxy added
* pass by only coords
* proper implementation for firefoxos

### 0.3.3 (Oct 28, 2013)
* [CB-5128](https://issues.apache.org/jira/browse/CB-5128): add repo + issue tag to plugin.xml for geolocation plugin
* [CB-4915](https://issues.apache.org/jira/browse/CB-4915) Incremented plugin version on dev branch.

### 0.3.2 (Sept 25, 2013)
* [CB-4889](https://issues.apache.org/jira/browse/CB-4889) bumping&resetting version
* [BlackBerry10] removed uneeded permission tags in plugin.xml
* [CB-4889](https://issues.apache.org/jira/browse/CB-4889) renaming org.apache.cordova.core.geolocation to org.apache.cordova.geolocation

### 0.3.0 (Sept 5, 2013)
* Added support for windows 8 (Adds required permission)
