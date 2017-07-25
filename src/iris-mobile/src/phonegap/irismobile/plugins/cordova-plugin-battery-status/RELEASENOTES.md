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

### 1.1.2 (Apr 15, 2016)
* CB-10720 Reorganizing and rewording docs.
* CB-10636 Add JSHint for plugins

### 1.1.1 (Nov 18, 2015)
* [CB-10035](https://issues.apache.org/jira/browse/CB-10035) Updated `RELEASENOTES` to be newest to oldest
* Fixing contribute link.

### 1.1.0 (Jun 17, 2015)
* added missing license headers
* [CB-7953](https://issues.apache.org/jira/browse/CB-7953) Add cordova-plugin-battery-status support for browser platform
* [CB-9128](https://issues.apache.org/jira/browse/CB-9128) cordova-plugin-battery-status documentation translation: cordova-plugin-battery-status
* attempt to fix npm issue

### 1.0.0 (Apr 15, 2015)
* [CB-8746](https://issues.apache.org/jira/browse/CB-8746) gave plugin major version bump
* [CB-8808](https://issues.apache.org/jira/browse/CB-8808) Fixed tests to pass on Windows Phone 8.1
* [CB-8831](https://issues.apache.org/jira/browse/CB-8831) Adds extra check for available API on Windows
* [CB-8653](https://issues.apache.org/jira/browse/CB-8653) properly updated translated docs to use new id
* [CB-8683](https://issues.apache.org/jira/browse/CB-8683) changed plugin-id to pacakge-name
* [CB-8653](https://issues.apache.org/jira/browse/CB-8653) updated translated docs to use new id
* Use TRAVIS_BUILD_DIR, install paramedic by npm
* Doc correction, Use the apostrophe to show possession
* Fix travis+paramedic pathing issue
* add Android+FireOS warning to tell devs that prolonged use will drain the battery.
* [CB-7971](https://issues.apache.org/jira/browse/CB-7971) Add cordova-plugin-battery-status support for Windows Phone 8.1
* [CB-8659](https://issues.apache.org/jira/browse/CB-8659): ios: 4.0.x Compatibility: Remove use of initWithWebView method
* added apache/travis badge - will not show until INFRA updates the github integration
* add travis.yml for CI with paramedic
* [CB-8538](https://issues.apache.org/jira/browse/CB-8538) Added package.json file

### 0.2.12 (Dec 02, 2014)
* [CB-7976](https://issues.apache.org/jira/browse/CB-7976) Android: Use webView's context rather than Activity's context for intent receiver
* [CB-7700](https://issues.apache.org/jira/browse/CB-7700) cordova-plugin-battery-status documentation translation: cordova-plugin-battery-status
* [CB-7571](https://issues.apache.org/jira/browse/CB-7571) Bump version of nested plugin to match parent plugin

### 0.2.11 (Sep 17, 2014)
* [CB-7249](https://issues.apache.org/jira/browse/CB-7249) cordova-plugin-battery-status documentation translation: cordova-plugin-battery-status
* [CB-6724](https://issues.apache.org/jira/browse/CB-6724) re-add accidental removed of var keyword
* [CB-6957](https://issues.apache.org/jira/browse/CB-6957) renamed folder to tests + added nested plugin.xml
* added documentation for manual tests
* [CB-6957](https://issues.apache.org/jira/browse/CB-6957) Style improvements on Manual tests

### 0.2.10 (Aug 06, 2014)
* [CB-6957](https://issues.apache.org/jira/browse/CB-6957) Ported Battery-status manual & automated
* [CB-6127](https://issues.apache.org/jira/browse/CB-6127) Updated translations for docs

### 0.2.9 (Jun 05, 2014)
* [CB-6721](https://issues.apache.org/jira/browse/CB-6721) Test for batterycritical change before batterylow change
* [CB-5611](https://issues.apache.org/jira/browse/CB-5611) firefoxos: battery-status plugin support added
* [CB-4519](https://issues.apache.org/jira/browse/CB-4519), [CB-4520](https://issues.apache.org/jira/browse/CB-4520) low+critical weren't firing when level went from 21->19, and were when level went 19->20
* [CB-6491](https://issues.apache.org/jira/browse/CB-6491) add CONTRIBUTING.md

### 0.2.8 (Apr 17, 2014)
* [CB-6465](https://issues.apache.org/jira/browse/CB-6465): Add license headers to Tizen code
* [CB-6460](https://issues.apache.org/jira/browse/CB-6460): Update license headers
* Add NOTICE file

### 0.2.7 (Feb 05, 2014)
* Add Tizen plugin.

### 0.2.6 (Jan 02, 2014)
* [CB-5658](https://issues.apache.org/jira/browse/CB-5658) Add doc/index.md for Battery Status.

### 0.2.5 (Dec 4, 2013)
* Merged WP8 support for level, but #def'd it out so the same code runs on wp7.  Updated docs to reflect WP8 support for battery level, and low+critical events
* wp8 add support in level
* add ubuntu platform
* 1. Updated platform name amazon->amazon-fireos. Deleted src files. 2. Change to use amazon-fireos as the platform if user agent string contains 'cordova-amazon-fireos'

### 0.2.4 (Oct 25, 2013)
* [CB-5128](https://issues.apache.org/jira/browse/CB-5128): added repo + issue tag to plugin.xml for battery status plugin
* [CB-4915](https://issues.apache.org/jira/browse/CB-4915) Incremented plugin version on dev branch.

### 0.2.3 (Sept 25, 2013)
* [CB-4889](https://issues.apache.org/jira/browse/CB-4889) bumping&resetting version
* [CB-4752](https://issues.apache.org/jira/browse/CB-4752) Incremented plugin version on dev branch.
* [CB-4889](https://issues.apache.org/jira/browse/CB-4889) renaming org.apache.cordova.core.battery-status to org.apache.cordova.battery-status
