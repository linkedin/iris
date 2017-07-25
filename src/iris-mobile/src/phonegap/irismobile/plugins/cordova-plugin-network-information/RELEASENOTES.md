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

### 1.2.1 (Apr 15, 2016)
* CB-10763: Remove emoji in `cordova-plugin-network-information`
* CB-10636 Add `JSHint` for plugins

### 1.2.0 (Jan 15, 2016)
* Adding `CoreTelephony` to `plugin.xml`
* Adding notification for `CT radio` information
* Adding `CT radio` information
* CB-10160: Fixed the case mismatch issue

### 1.1.0 (Nov 18, 2015)
* [CB-10035](https://issues.apache.org/jira/browse/CB-10035) Updated `RELEASENOTES` to be newest to oldest
* Fixing contribute link.
* These notifications are objects so their address always evaluates to true.
* Update `NetworkManager.java`
* [CB-9542](https://issues.apache.org/jira/browse/CB-9542) `Browser Proxy` not defined correctly
* Solved `toLowerCase` issue with `Locale.US`

### 1.0.1 (Jun 17, 2015)
* Adding .ratignore file.
* [CB-9128](https://issues.apache.org/jira/browse/CB-9128) cordova-plugin-network-information documentation translation: cordova-plugin-network-information
* fix npm md issue

### 1.0.0 (Apr 15, 2015)
* [CB-8746](https://issues.apache.org/jira/browse/CB-8746) gave plugin major version bump
* [CB-8683](https://issues.apache.org/jira/browse/CB-8683) changed plugin-id to pacakge-name
* [CB-8653](https://issues.apache.org/jira/browse/CB-8653) properly updated translated docs to use new id
* [CB-8653](https://issues.apache.org/jira/browse/CB-8653) updated translated docs to use new id
* [CB-8185](https://issues.apache.org/jira/browse/CB-8185) Fixes typo in `cordova.platformId`
* Use TRAVIS_BUILD_DIR, install paramedic by npm
* [CB-8185](https://issues.apache.org/jira/browse/CB-8185) Use `navigator.onLine` as connection information source on browser platform
* [CB-8653](https://issues.apache.org/jira/browse/CB-8653) Updated Readme
* [CB-8659](https://issues.apache.org/jira/browse/CB-8659): ios: 4.0.x Compatibility: Remove use of initWebView method
* [CB-8573](https://issues.apache.org/jira/browse/CB-8573) Integrate TravisCI
* [CB-8438](https://issues.apache.org/jira/browse/CB-8438) cordova-plugin-network-information documentation translation: cordova-plugin-network-information
* [CB-8538](https://issues.apache.org/jira/browse/CB-8538) Added package.json file

### 0.2.15 (Feb 04, 2015)
* [CB-8384](https://issues.apache.org/jira/browse/CB-8384) Network status change support on Windows
* [CB-8384](https://issues.apache.org/jira/browse/CB-8384) Fixes the way we detect online status on Windows
* [CB-8384](https://issues.apache.org/jira/browse/CB-8384) Add Windows platform quirks
* [CB-8384](https://issues.apache.org/jira/browse/CB-8384) Add Windows section to Network Information plugin

### 0.2.14 (Dec 02, 2014)
* [CB-7976](https://issues.apache.org/jira/browse/CB-7976) **Android**: Use webView's context rather than Activity's context for intent receiver
* [CB-7700](https://issues.apache.org/jira/browse/CB-7700) cordova-plugin-network-information documentation translation: cordova-plugin-network-information

### 0.2.13 (Oct 03, 2014)
* [CB-7595](https://issues.apache.org/jira/browse/CB-7595): Android L changes the type from Mobile to Cellular, I'm pretty sure this isn't documented

### 0.2.12 (Sep 17, 2014)
* [CB-7471](https://issues.apache.org/jira/browse/CB-7471) cordova-plugin-network-information documentation translation
* Fix network information type exception on fxos 2
* Added support for the browser
* [CB-6724](https://issues.apache.org/jira/browse/CB-6724) added documentation for manual tests
* remove reference to test assets, they are optional
* Renamed test dir and added nested plugin.xml
* [CB-6964](https://issues.apache.org/jira/browse/CB-6964) ported manual tests
* Port network tests to plugin-test-framework
* Fix naviagtor typo

### 0.2.11 (Aug 06, 2014)
* **FFOS** update NetworkProxy.js
* [CB-6127](https://issues.apache.org/jira/browse/CB-6127) Updated translations for docs
* [CB-7019](https://issues.apache.org/jira/browse/CB-7019) Updated version and RELEASENOTES.md for release 0.2.10
* Fixed docs for online/offline event being backwards

### 0.2.10 (Jun 24, 2014)
* [CB-6907](https://issues.apache.org/jira/browse/CB-6907): [android] Don't crash on startup if no networks available

### 0.2.9 (Jun 05, 2014)
* updated notice file to include missing license
* Cached extra info to better detect changes.
* [CB-6809](https://issues.apache.org/jira/browse/CB-6809) Add license to CONTRIBUTING.md
* [CB-6491](https://issues.apache.org/jira/browse/CB-6491) add CONTRIBUTING.md
* [CB-6350](https://issues.apache.org/jira/browse/CB-6350) - Fix networkStatusForFlags return value type to work with 64-bit iOS (closes #8)
* Initial version of firefox os network information plugin
* there was an error in the object definition

### 0.2.8 (Apr 17, 2014)
* [CB-6342](https://issues.apache.org/jira/browse/CB-6342): [iOS] iOS reports a cellular connection even when in Airplane mode
* [CB-6422](https://issues.apache.org/jira/browse/CB-6422): [windows8] use cordova/exec/proxy
* [CB-6460](https://issues.apache.org/jira/browse/CB-6460): Update license headers
* [CB-6465](https://issues.apache.org/jira/browse/CB-6465): Add license headers to Tizen code
* Add NOTICE file

### 0.2.7 (Feb 05, 2014)
* Initial implementation of Tizen plugin.

### 0.2.6 (Jan 02, 2014)
* [CB-5658](https://issues.apache.org/jira/browse/CB-5658) Add doc/index.md for netinfo plugin

### 0.2.5 (Dec 4, 2013)
* [ubuntu] specify policy_group
* add ubuntu platform
* Added amazon-fireos platform. Change to use amazon-fireos as the platform if user agent string contains 'cordova-amazon-fireos'

### 0.2.4 (Oct 28, 2013)
* [CB-5128](https://issues.apache.org/jira/browse/CB-5128): add repo + issue tag to plugin.xml for network information plugin
* [CB-4915](https://issues.apache.org/jira/browse/CB-4915) Incremented plugin version on dev branch.

### 0.2.3 (Sept 25, 2013)
* [CB-4889](https://issues.apache.org/jira/browse/CB-4889) bumping&resetting version
* [windows8] commandProxy was moved
* [CB-4889](https://issues.apache.org/jira/browse/CB-4889) renaming org.apache.cordova.core.network-information to org.apache.cordova.network-information
* removed duplicate comment line from plugin.xml
* added Network APIs for FirefoxOS
* Rename CHANGELOG.md -> RELEASENOTES.md
* [CB-4752](https://issues.apache.org/jira/browse/CB-4752) Incremented plugin version on dev branch.

### 0.2.1 (Sept 5, 2013)
* [CB-4432](https://issues.apache.org/jira/browse/CB-4432) copyright notice change
