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
* CB-10097 dialog doesn't show on **iOS** when called from a select list `onChange` event
* Remove `warning` emoji, as it doesn't correctly display in the docs website: http://cordova.apache.org/docs/en/dev/cordova-plugin-dialogs/index.html
* CB-10727 Dialogs plugin has warnings on **iOS**
* CB-10636 Add `JSHint` for plugins

### 1.2.0 (Nov 18, 2015)
* [CB-10035](https://issues.apache.org/jira/browse/CB-10035) Updated `RELEASENOTES` to be newest to oldest
* [CB-8549](https://issues.apache.org/jira/browse/CB-8549) Updated source to pass `Fortify` scan.
* Fixing contribute link.
* add `CSS class` to prompt `div` for **Windows** platform
* [CB-9347](https://issues.apache.org/jira/browse/CB-9347) - fix to allow to stack multiple `UIAlertControllers`

### 1.1.1 (Jun 17, 2015)
* [CB-9128](https://issues.apache.org/jira/browse/CB-9128) cordova-plugin-dialogs documentation translation: cordova-plugin-dialogs
* fix npm md

### 1.1.0 (May 06, 2015)
* [CB-8928](https://issues.apache.org/jira/browse/CB-8928): Removed direct call to `toStaticHTML`, only call it if we are sure it's present. This closes #52
* [CB-7734](https://issues.apache.org/jira/browse/CB-7734) - `navigator.notification.alert` or `navigator.notification.confirm` seem have a "many words" issue. (closes #39)
 
### 1.0.0 (Apr 15, 2015)
* [CB-8746](https://issues.apache.org/jira/browse/CB-8746) gave plugin major version bump
* [CB-8683](https://issues.apache.org/jira/browse/CB-8683) updated wp and bb specific references of old id to new id
* [CB-8683](https://issues.apache.org/jira/browse/CB-8683) changed plugin-id to pacakge-name
* [CB-8653](https://issues.apache.org/jira/browse/CB-8653) properly updated translated docs to use new id
* [CB-8653](https://issues.apache.org/jira/browse/CB-8653) updated translated docs to use new id
* Use TRAVIS_BUILD_DIR, install paramedic by npm
* [CB-8653](https://issues.apache.org/jira/browse/CB-8653) Updated Readme
* [CB-8659](https://issues.apache.org/jira/browse/CB-8659): ios: 4.0.x Compatibility: Remove use of deprecated headers
* [CB-8565](https://issues.apache.org/jira/browse/CB-8565) Integrate TravisCI
* [CB-8438](https://issues.apache.org/jira/browse/CB-8438) cordova-plugin-dialogs documentation translation: cordova-plugin-dialogs
* [CB-8538](https://issues.apache.org/jira/browse/CB-8538) Added package.json file
* [CB-8367](https://issues.apache.org/jira/browse/CB-8367) [org.apache.cordova.dialogs] Add Prompt support on Windows

### 0.3.0 (Feb 04, 2015)
* Correct way to specify Windows platform in config.xml
* [CB-8351](https://issues.apache.org/jira/browse/CB-8351) ios: Use argumentForIndex rather than NSArray extension
* [CB-7955](https://issues.apache.org/jira/browse/CB-7955) Add support "browser" platform

### 0.2.11 (Dec 02, 2014)
* [CB-7737](https://issues.apache.org/jira/browse/CB-7737) lower min height for alert
* [CB-8038](https://issues.apache.org/jira/browse/CB-8038) backslash getting escaped twice in **BB10**
* [CB-8029](https://issues.apache.org/jira/browse/CB-8029) test 1-based indexing for confirm
* [CB-7639](https://issues.apache.org/jira/browse/CB-7639) Update docs + manual tests
* [CB-7639](https://issues.apache.org/jira/browse/CB-7639) Revert back `isAlertShowing` flag in case of exception to prevent queuing of future dialogs.
* [CB-7639](https://issues.apache.org/jira/browse/CB-7639) Handle button labels as array on windows
* [CB-7977](https://issues.apache.org/jira/browse/CB-7977) Mention `deviceready` in plugin docs
* Check for `setTextDirection` API level
* **Android** Make spinner dialog to use `THEME_DEVICE_DEFAULT_LIGHT` (same as the other dialogs)
* **Android** Unbreak `API` level < `14`
* [CB-7414](https://issues.apache.org/jira/browse/CB-7414) **BB10** Document callback parameter for `navigator.notification.alert`
* [CB-7700](https://issues.apache.org/jira/browse/CB-7700) cordova-plugin-dialogs documentation translation: cordova-plugin-dialogs
* [CB-7571](https://issues.apache.org/jira/browse/CB-7571) Bump version of nested plugin to match parent plugin

### 0.2.10 (Sep 17, 2014)
* [CB-7538](https://issues.apache.org/jira/browse/CB-7538) Android beep thread fix Beep now executes in it's own thread. It was previously executing in the main UI thread which was causing the application to lock up will the beep was occurring.  Closing pull request
* Set dialog text dir to locale
* Renamed test dir, added nested plugin.xml
* added documentation for manual tests
* [CB-6965](https://issues.apache.org/jira/browse/CB-6965) Added manual tests
* [CB-6965](https://issues.apache.org/jira/browse/CB-6965) Port notification tests to test-framework

### 0.2.9 (Aug 06, 2014)
* ubuntu: pass proper arguments to prompt callback
* ubuntu: use TextField instead of TextInput
* ubuntu: proper message escaping before passing to qml
* **FFOS** update notification.js
* [CB-6127](https://issues.apache.org/jira/browse/CB-6127) Updated translations for docs
* android: Explicitly apply default theme to dialogs
* Fix Beep exception on Android when no argument passed

### 0.2.8 (Jun 05, 2014)
* [CB-6801](https://issues.apache.org/jira/browse/CB-6801) Add license
* running original windows.open, inAppBrowser is overriding it no need to place CSS in every page anymore
* [CB-5945](https://issues.apache.org/jira/browse/CB-5945) [Windows8] do not call success callbacks until dialog is dismissed
* [CB-4616](https://issues.apache.org/jira/browse/CB-4616) Returned index 0 was not documented for notification.prompt
* update docs to state that prompt is supported on windowsphone
* [CB-6528](https://issues.apache.org/jira/browse/CB-6528) allow scroll on alert message content
* [CB-6628][amazon-fireos]dialogs plugin's confirm and prompt methods dont work confirm() method was missing amazon-fireos platform check. added that. prompt() method had bug. It is executed in a worker thread that does not have a message queue(or Looper object) associated with it and hence "can't create a handler" exception is thrown. To fix this issue, we need to create the EditText widget from within the UI thread. This was fixed sometime ago when we added fireos platform but commit got lost somewhere. So fixing it again now.
* [CB-6491](https://issues.apache.org/jira/browse/CB-6491) add CONTRIBUTING.md
* Added check for isFinishing() on the parent activity to prevent crashes when trying to display dialogs when activity is in this phase of it's lifecycle
* [CB-4966](https://issues.apache.org/jira/browse/CB-4966) Dialogs are in window now No need to add anything to manifest or index.html
* Removing FirefoxOS Quirks * no need to add special permission (it's different API with the same name) * notification.css is added automatically

### 0.2.7 (Apr 17, 2014)
* [CB-6212](https://issues.apache.org/jira/browse/CB-6212): [iOS] fix warnings compiled under arm64 64-bit
* [CB-6411](https://issues.apache.org/jira/browse/CB-6411): [BlackBerry10] Work around Audio playback issue
* [CB-6411](https://issues.apache.org/jira/browse/CB-6411): [BlackBerry10] Updates to beep
* [CB-6422](https://issues.apache.org/jira/browse/CB-6422): [windows8] use cordova/exec/proxy
* [CB-6460](https://issues.apache.org/jira/browse/CB-6460): Update license headers
* Add NOTICE file

### 0.2.6 (Feb 05, 2014)
* no need to recreate the manifest.webapp file after each `cordova prepare` for FFOS
* FFOS description added

### 0.2.5 (Jan 02, 2014)
* [CB-4696](https://issues.apache.org/jira/browse/CB-4696) Fix compile error for Xcode 4.5.
* [CB-5658](https://issues.apache.org/jira/browse/CB-5658) Add doc/index.md for Dialogs plugin
* [CB-3762](https://issues.apache.org/jira/browse/CB-3762) Change prompt default to empty string
* Move images from css to img

### 0.2.4 (Dec 4, 2013)
* add ubuntu platform
* 1. Added amazon-fireos platform. 2. Change to use amazon-fireos as a platform if user agent string contains 'cordova-amazon-fireos'.
* added beep funtionality using ms-winsoundevent:Notfication.Default

### 0.2.3 (Oct 28, 2013)
* [CB-5128](https://issues.apache.org/jira/browse/CB-5128): added repo + issue tag to plugin.xml for dialogs plugin
* new plugin execute arguments supported
* new plugin style
* smaller fonts styling input
* img files copied inside plugin
* style added
* prompt added
* styling from James
* fixed "exec" calls addedd css, but not working yet
* first (blind) try
* [CB-4915](https://issues.apache.org/jira/browse/CB-4915) Incremented plugin version on dev branch.

### 0.2.2 (Sept 25, 2013)
* [CB-4889](https://issues.apache.org/jira/browse/CB-4889) bumping&resetting version
* [windows8] commandProxy was moved
* [CB-4889](https://issues.apache.org/jira/browse/CB-4889) renaming reference in Notification.cs
* [CB-4889](https://issues.apache.org/jira/browse/CB-4889) renaming org.apache.cordova.core.dialogs to org.apache.cordova.dialogs
* Rename CHANGELOG.md -> RELEASENOTES.md
* [CB-4592](https://issues.apache.org/jira/browse/CB-4592) [Blackberry10] Added beep support
* [CB-4752](https://issues.apache.org/jira/browse/CB-4752) Incremented plugin version on dev branch.
