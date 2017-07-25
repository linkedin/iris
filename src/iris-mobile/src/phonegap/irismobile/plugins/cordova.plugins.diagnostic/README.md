Cordova diagnostic plugin [![Latest Stable Version](https://img.shields.io/npm/v/cordova.plugins.diagnostic.svg)](https://www.npmjs.com/package/cordova.plugins.diagnostic) [![Total Downloads](https://img.shields.io/npm/dt/cordova.plugins.diagnostic.svg)](https://npm-stat.com/charts.html?package=cordova.plugins.diagnostic)
=========================

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->


- [Overview](#overview)
  - [Important notes](#important-notes)
    - [Native environment required](#native-environment-required)
    - [Version 3.2 for iOS 10](#version-32-for-ios-10)
    - [Version 3.1 backward-incompatibility](#version-31-backward-incompatibility)
    - [Version 3 backward-incompatibility](#version-3-backward-incompatibility)
    - [Building for Android](#building-for-android)
- [Installation](#installation)
  - [Using the Cordova/Phonegap CLI](#using-the-cordovaphonegap-cli)
  - [Using Cordova Plugman](#using-cordova-plugman)
  - [PhoneGap Build](#phonegap-build)
- [Usage](#usage)
  - [Android, iOS and Windows 10 Mobile](#android-ios-and-windows-10-mobile)
    - [isLocationAvailable()](#islocationavailable)
    - [isWifiAvailable()](#iswifiavailable)
    - [isWifiEnabled()](#iswifienabled)
    - [isCameraAvailable()](#iscameraavailable)
    - [isBluetoothAvailable()](#isbluetoothavailable)
  - [Android and Windows 10 Mobile only](#android-and-windows-10-mobile-only)
    - [switchToLocationSettings()](#switchtolocationsettings)
    - [switchToMobileDataSettings()](#switchtomobiledatasettings)
    - [switchToBluetoothSettings()](#switchtobluetoothsettings)
    - [switchToWifiSettings()](#switchtowifisettings)
    - [setWifiState()](#setwifistate)
    - [setBluetoothState()](#setbluetoothstate)
  - [Android and iOS](#android-and-ios)
    - [permissionStatus constants](#permissionstatus-constants)
    - [bluetoothState constants](#bluetoothstate-constants)
    - [isLocationEnabled()](#islocationenabled)
    - [isLocationAuthorized()](#islocationauthorized)
    - [getLocationAuthorizationStatus()](#getlocationauthorizationstatus)
    - [requestLocationAuthorization()](#requestlocationauthorization)
    - [isCameraPresent()](#iscamerapresent)
    - [isCameraAuthorized()](#iscameraauthorized)
    - [getCameraAuthorizationStatus()](#getcameraauthorizationstatus)
    - [requestCameraAuthorization()](#requestcameraauthorization)
    - [isMicrophoneAuthorized()](#ismicrophoneauthorized)
    - [getMicrophoneAuthorizationStatus()](#getmicrophoneauthorizationstatus)
    - [requestMicrophoneAuthorization()](#requestmicrophoneauthorization)
    - [isContactsAuthorized()](#iscontactsauthorized)
    - [getContactsAuthorizationStatus()](#getcontactsauthorizationstatus)
    - [requestContactsAuthorization()](#requestcontactsauthorization)
    - [isCalendarAuthorized()](#iscalendarauthorized)
    - [getCalendarAuthorizationStatus()](#getcalendarauthorizationstatus)
    - [requestCalendarAuthorization()](#requestcalendarauthorization)
    - [switchToSettings()](#switchtosettings)
    - [getBluetoothState()](#getbluetoothstate)
    - [registerBluetoothStateChangeHandler()](#registerbluetoothstatechangehandler)
    - [registerLocationStateChangeHandler()](#registerlocationstatechangehandler)
  - [Android only](#android-only)
    - [locationMode constants](#locationmode-constants)
    - [isGpsLocationAvailable()](#isgpslocationavailable)
    - [isGpsLocationEnabled()](#isgpslocationenabled)
    - [isNetworkLocationAvailable()](#isnetworklocationavailable)
    - [isNetworkLocationEnabled()](#isnetworklocationenabled)
    - [getLocationMode()](#getlocationmode)
    - [getPermissionAuthorizationStatus()](#getpermissionauthorizationstatus)
    - [getPermissionsAuthorizationStatus()](#getpermissionsauthorizationstatus)
    - [requestRuntimePermission()](#requestruntimepermission)
    - [requestRuntimePermissions()](#requestruntimepermissions)
    - [isRequestingPermission()](#isrequestingpermission)
    - [registerPermissionRequestCompleteHandler()](#registerpermissionrequestcompletehandler)
    - [isBluetoothEnabled()](#isbluetoothenabled)
    - [hasBluetoothSupport()](#hasbluetoothsupport)
    - [hasBluetoothLESupport()](#hasbluetoothlesupport)
    - [hasBluetoothLEPeripheralSupport()](#hasbluetoothleperipheralsupport)
    - [isExternalStorageAuthorized()](#isexternalstorageauthorized)
    - [getExternalStorageAuthorizationStatus()](#getexternalstorageauthorizationstatus)
    - [requestExternalStorageAuthorization()](#requestexternalstorageauthorization)
    - [getExternalSdCardDetails()](#getexternalsdcarddetails)
    - [switchToWirelessSettings()](#switchtowirelesssettings)
    - [switchToNFCSettings()](#switchtonfcsettings)
    - [isNFCPresent()](#isnfcpresent)
    - [isNFCEnabled()](#isnfcenabled)
    - [isNFCAvailable()](#isnfcavailable)
    - [registerNFCStateChangeHandler()](#registernfcstatechangehandler)
    - [NFCState constants](#nfcstate-constants)
  - [iOS only](#ios-only)
    - [isCameraRollAuthorized()](#iscamerarollauthorized)
    - [getCameraRollAuthorizationStatus()](#getcamerarollauthorizationstatus)
    - [requestCameraRollAuthorization()](#requestcamerarollauthorization)
    - [isRemoteNotificationsEnabled()](#isremotenotificationsenabled)
    - [isRegisteredForRemoteNotifications()](#isregisteredforremotenotifications)
    - [getRemoteNotificationTypes()](#getremotenotificationtypes)
    - [isRemindersAuthorized()](#isremindersauthorized)
    - [getRemindersAuthorizationStatus()](#getremindersauthorizationstatus)
    - [requestRemindersAuthorization()](#requestremindersauthorization)
    - [isBackgroundRefreshAuthorized()](#isbackgroundrefreshauthorized)
    - [getBackgroundRefreshStatus()](#getbackgroundrefreshstatus)
    - [requestBluetoothAuthorization()](#requestbluetoothauthorization)
    - [isMotionAvailable()](#ismotionavailable)
    - [isMotionRequestOutcomeAvailable()](#ismotionrequestoutcomeavailable)
    - [requestAndCheckMotionAuthorization()](#requestandcheckmotionauthorization)
- [Platform Notes](#platform-notes)
  - [Android](#android)
    - [Android permissions](#android-permissions)
  - [Windows](#windows)
    - [Supported Windows versions](#supported-windows-versions)
    - [Windows 10 Mobile permissions](#windows-10-mobile-permissions)
  - [iOS](#ios)
    - [iOS usage description messages](#ios-usage-description-messages)
- [Example project](#example-project)
  - [Screenshots](#screenshots)
    - [Android](#android-1)
    - [iOS](#ios-1)
- [Release notes](#release-notes)
- [Credits](#credits)
- [License](#license)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->


# Overview

This Cordova/Phonegap plugin for iOS, Android and Windows 10 Mobile is used to manage device settings such as Location,  Bluetooth and WiFi. It enables management of run-time permissions, device hardware and core OS features.

The plugin is registered in on [npm](https://www.npmjs.com/package/cordova.plugins.diagnostic) as `cordova.plugins.diagnostic`

<!-- DONATE -->
[![donate](https://www.paypalobjects.com/en_US/i/btn/btn_donateCC_LG_global.gif)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=ZRD3W47HQ3EMJ)

I dedicate a considerable amount of my free time to developing and maintaining this Cordova plugin, along with my other Open Source software.
To help ensure this plugin is kept updated, new features are added and bugfixes are implemented quickly, please donate a couple of dollars (or a little more if you can stretch) as this will help me to afford to dedicate time to its maintenance. Please consider donating if you're using this plugin in an app that makes you money, if you're being paid to make the app, if you're asking for new features or priority bug fixes.
<!-- END DONATE -->


## Important notes

### Native environment required

Note that this plugin is intended for use in a **native** mobile environment.
It will **NOT** work in a browser-emulated Cordova environment, for example by running `cordova serve` or using the [Ripple emulator](https://github.com/ripple-emulator/ripple).

### Version 3.2 for iOS 10

`cordova.plugins.diagnostic@3.2.0` adds support for the new UserNotifications framework added in iOS 10. To build using v3.2.0, you will need to use XCode 8+ because there's no way to conditionally include a framework using the `<framework>` tag in the plugin.xml.

Currently (25 Sep 2016) cloud-based build platforms such as Phonegap Build, Ionic Cloud and Intel XDK are still using an XCode 7 build environment, so building with `cordova.plugins.diagnostic@3.2` results in a fatal build error `framework not found UserNotifications`.

Therefore, users of these cloud platforms should specify `cordova.plugins.diagnostic@3.1` in their config.xml until such time as their cloud platform is updated to use XCode 8+.

### Version 3.1 backward-incompatibility

This version contains backwardly-incompatible renaming of some functions in order to logically separate those which check if a device OS setting is enabled (`isSomethingEnabled()`) vs those which check if hardware/sensor is available for use by the app (device OS setting is enabled AND app has authorisation AND hardware is present - `isSomethingAvailable()`).

To avoid breaking existing code which uses the prior function names, either fix the version of the plugin in your config.xml to `cordova.plugins.diagnostic@3.0` or update your code to use [the revised names detailed in the release notes](https://github.com/dpa99c/cordova-diagnostic-plugin/wiki/Release-notes).

### Version 3 backward-incompatibility

In order to make cross-platform use of the shared plugin functions easier, some **backwardly-incompatible changes** have been made to existing API functions in v3 of the plugin.

To avoid breaking existing code which uses the old API syntax, you can continue to use the v2 API by specifying the plugin version when adding it: `cordova.plugins.diagnostic@2`

See the [release notes page ](https://github.com/dpa99c/cordova-diagnostic-plugin/wiki/Release-notes) for details of the backward-incompatible changes.

### Building for Android

In order to avoid build problems with Android, please make sure you have the latest versions of the following Android SDK components installed:

- Android SDK Tools
- Android SDK Platform-tools
- Android SDK Build-tools
- Target SDK Platform - e.g. Android 6.0 (API 23)
- Android Support Repository
- Android Support Library
- Google Repository

Also make sure you have the latest release of the `cordova-android` platform installed. You can check if the Android platform in your Cordova project is up-to-date using `cordova platform check android` and if it's not, update it using `cordova platform rm android && cordova platform add android@latest`.

Phonegap Build uses should use the latest available CLI version ([listed here](https://build.phonegap.com/current-support)) by specifying using the `phonegap-version` tag in your `config.xml`, for example:

    <preference name="phonegap-version" value="cli-6.4.0" />

#### Building for Android runtime permissions

In order to support Android 6 (API 23) [runtime permissions](http://developer.android.com/training/permissions/requesting.html), this plugin must depend on libraries only present in API 23+, so you __must build using Android SDK Platform v23 or above__. To do this you must have [Cordova Android platform](https://github.com/apache/cordova-android)@5.0.0 or above installed in your project. You can check the currently installed platform versions with the following command:

    cordova platform ls

__Note:__ Attempting to build with API 22 or below will result in a build error.


You __must__ also make sure your build environment has the following Android libraries installed. In a local build environment, you'd install these via the Android SDK Manager:

-  Android Support Library - Rev. 23 or above
-  Android Support Repository - Rev. 23 or above


#### Building for API 22 or lower

For users who wish to build against API 22 or below, there is a branch of the plugin repo which contains most of the plugin functionality __except Android 6 runtime permissions__. This removes the dependency on API 23 and will allow you to build against legacy API versions (22 and below).

The legacy branch is published to npm as [`cordova.plugins.diagnostic.api-22`](https://www.npmjs.com/package/cordova.plugins.diagnostic.api-22), so you'll need to use this plugin ID when adding it:

    cordova plugin add cordova.plugins.diagnostic.api-22

**NOTE**: Phonegap Build now supports API 23, so its users may use the main plugin branch (`cordova.plugins.diagnostic`).

# Installation

## Using the Cordova/Phonegap CLI

    $ cordova plugin add cordova.plugins.diagnostic
    $ phonegap plugin add cordova.plugins.diagnostic

**NOTE**: Make sure your Cordova CLI version is 5.0.0+ (check with `cordova -v`). Cordova 4.x and below uses the now deprecated [Cordova Plugin Registry](http://plugins.cordova.io) as its plugin repository, so using a version of Cordova 4.x or below will result in installing an [old version](http://plugins.cordova.io/#/package/cordova.plugins.diagnostic) of this plugin.

## Using Cordova Plugman

    $ plugman install --plugin=cordova.plugins.diagnostic --platform=<platform> --project=<project_path> --plugins_dir=plugins

For example, to install for the Android platform

    $ plugman install --plugin=cordova.plugins.diagnostic --platform=android --project=platforms/android --plugins_dir=plugins

## PhoneGap Build
Add the following xml to your config.xml to use the latest version of this plugin from [npm](https://www.npmjs.com/package/cordova.plugins.diagnostic):

    <plugin name="cordova.plugins.diagnostic" source="npm" />

# Usage

The plugin is exposed via the `cordova.plugins.diagnostic` object and provides the following functions:

## Android, iOS and Windows 10 Mobile

### isLocationAvailable()

Checks if app is able to access device location.

    cordova.plugins.diagnostic.isLocationAvailable(successCallback, errorCallback);

On iOS and Windows 10 Mobile this returns true if both the device setting is enabled AND the application is authorized to use location.
When location is enabled, the locations returned are by a mixture GPS hardware, network triangulation and Wifi network IDs.

On Android, this returns true if Location mode is enabled and any mode is selected (e.g. Battery saving, Device only, High accuracy)
AND if the app is authorised to use location.
When location is enabled, the locations returned are dependent on the location mode:

* Battery saving = network triangulation and Wifi network IDs (low accuracy)
* Device only = GPS hardware only (high accuracy)
* High accuracy = GPS hardware, network triangulation and Wifi network IDs (high and low accuracy)

#### Parameters

- {Function} successCallback -  The callback which will be called when operation is successful.
This callback function is passed a single boolean parameter which is TRUE if location is available for use.
- {Function} errorCallback -  The callback which will be called when operation encounters an error.
This callback function is passed a single string parameter containing the error message.


#### Example usage

    cordova.plugins.diagnostic.isLocationAvailable(function(available){
        console.log("Location is " + (available ? "available" : "not available"));
    }, function(error){
        console.error("The following error occurred: "+error);
    });

### isWifiAvailable()

Checks if Wifi is available.
On iOS this returns true if the device is connected to a network by WiFi.
On Android and Windows 10 Mobile this returns true if the WiFi setting is set to enabled, and is the same as [`isWifiEnabled()`](#iswifienabled)

On Android this requires permission `<uses-permission android:name="android.permission.ACCESS_WIFI_STATE" />`

    cordova.plugins.diagnostic.isWifiAvailable(successCallback, errorCallback);

#### Parameters

- {Function} successCallback -  The callback which will be called when operation is successful.
This callback function is passed a single boolean parameter which is TRUE if WiFi is available.
- {Function} errorCallback -  The callback which will be called when operation encounters an error.
This callback function is passed a single string parameter containing the error message.


#### Example usage

    cordova.plugins.diagnostic.isWifiAvailable(function(available){
        console.log("WiFi is " + (available ? "available" : "not available"));
    }, function(error){
        console.error("The following error occurred: "+error);
    });

### isWifiEnabled()

On iOS this returns true if the WiFi setting is set to enabled (regardless of whether it's connected to a network).
On Android and Windows 10 Mobile this returns true if the WiFi setting is set to enabled, and is the same as [`isWifiAvailable()`](#iswifiavailable)
On Android this requires permission `<uses-permission android:name="android.permission.ACCESS_WIFI_STATE" />`

    cordova.plugins.diagnostic.isWifiEnabled(successCallback, errorCallback);

#### Parameters

- {Function} successCallback -  The callback which will be called when operation is successful.
This callback function is passed a single boolean parameter which is true if the device setting is enabled.
- {Function} errorCallback -  The callback which will be called when operation encounters an error.
This callback function is passed a single string parameter containing the error message.


#### Example usage

    cordova.plugins.diagnostic.isWifiEnabled(function(enabled){
        console.log("WiFi is " + (enabled ? "enabled" : "disabled"));
    }, function(error){
        console.error("The following error occurred: "+error);
    });

### isCameraAvailable()

Checks if camera is available.

Notes:
- On Android & iOS this returns true if the device has a camera AND the application is authorized to use it.
- On Windows 10 Mobile this returns true if the device has a **rear-facing** camera.

Notes for Android:
- On Android by default this checks run-time permission for both `READ_EXTERNAL_STORAGE` and `CAMERA` because [cordova-plugin-camera@2.2+](https://github.com/apache/cordova-plugin-camera) requires both of these permissions.
- The call signature `cordova.plugins.diagnostic.isCameraAvailable(successCallback, errorCallback, externalStorage)` is also supported for benefit of the [ionic-native Promise API wrapper](https://github.com/driftyco/ionic-native/blob/master/src/%40ionic-native/plugins/diagnostic/index.ts).


    cordova.plugins.diagnostic.isCameraAvailable(params);
    cordova.plugins.diagnostic.isCameraAvailable(successCallback, errorCallback, params)
    cordova.plugins.diagnostic.isCameraAvailable(successCallback, errorCallback, externalStorage)

#### Parameters
- {Object} params - (optional) parameters:
    - {Function} successCallback -  The callback which will be called when operation is successful.
This callback function is passed a single boolean parameter which is TRUE if camera is present and authorized for use.
    - {Function} errorCallback -  The callback which will be called when operation encounters an error.
This callback function is passed a single string parameter containing the error message.
    - {Boolean} externalStorage - (Android only) If true, checks permission for `READ_EXTERNAL_STORAGE` in addition to `CAMERA` run-time permission.
Defaults to true.


#### Example usage

    cordova.plugins.diagnostic.isCameraAvailable({
        successCallback: function(available){
            console.log("Camera is " + (available ? "available" : "not available"));
        },
        errorCallback: function(error){
            console.error("The following error occurred: "+error);
        },
        externalStorage: false
    });
    
    cordova.plugins.diagnostic.isCameraAvailable(
        function(available){
            console.log("Camera is " + (available ? "available" : "not available"));
        }, function(error){
            console.error("The following error occurred: "+error);
        }, {
            externalStorage: false
        }
    );
    
    cordova.plugins.diagnostic.isCameraAvailable(
        function(available){
            console.log("Camera is " + (available ? "available" : "not available"));
        }, function(error){
            console.error("The following error occurred: "+error);
        }, false
    );

### isBluetoothAvailable()

Checks if Bluetooth is available to the app.
Returns true if the device has Bluetooth capabilities AND if Bluetooth setting is switched on (same on Android, iOS and Windows 10 Mobile)

On Android this requires permission `<uses-permission android:name="android.permission.BLUETOOTH" />`

    cordova.plugins.diagnostic.isBluetoothAvailable(successCallback, errorCallback);

#### Parameters

- {Function} successCallback -  The callback which will be called when operation is successful.
This callback function is passed a single boolean parameter which is TRUE if Bluetooth is available.
- {Function} errorCallback -  The callback which will be called when operation encounters an error.
This callback function is passed a single string parameter containing the error message.


#### Example usage

    cordova.plugins.diagnostic.isBluetoothAvailable(function(available){
        console.log("Bluetooth is " + (available ? "available" : "not available"));
    }, function(error){
        console.error("The following error occurred: "+error);
    });

## Android and Windows 10 Mobile only

### switchToLocationSettings()

Displays the device location settings to allow user to enable location services/change location mode.

    cordova.plugins.diagnostic.switchToLocationSettings();

Note: On Android, you may want to consider using the [Request Location Accuracy Plugin for Android](https://github.com/dpa99c/cordova-plugin-request-location-accuracy) to request the desired location accuracy without needing the user to manually do this on the Location Settings page.

### switchToMobileDataSettings()

Displays mobile settings to allow user to enable mobile data.

    cordova.plugins.diagnostic.switchToMobileDataSettings();

### switchToBluetoothSettings()

Displays Bluetooth settings to allow user to enable Bluetooth.

    cordova.plugins.diagnostic.switchToBluetoothSettings();

### switchToWifiSettings()

Displays WiFi settings to allow user to enable WiFi.

    cordova.plugins.diagnostic.switchToWifiSettings();


### setWifiState()

Enables/disables WiFi on the device.

    cordova.plugins.diagnostic.setWifiState(successCallback, errorCallback, state);

Requires the following permissions for Android:

    <uses-permission android:name="android.permission.ACCESS_WIFI_STATE"/>
    <uses-permission android:name="android.permission.CHANGE_WIFI_STATE"/>

Requires the following capabilities for Windows 10 Mobile:

    <DeviceCapability Name="radios" />

#### Parameters

- {Function} successCallback - function to call on successful setting of WiFi state
- {Function} errorCallback - function to call on failure to set WiFi state.
- {Boolean} state - WiFi state to set: TRUE for enabled, FALSE for disabled.


#### Example usage

    cordova.plugins.diagnostic.setWifiState(function(){
        console.log("Wifi was enabled");
    }, function(error){
        console.error("The following error occurred: "+error);
    },
    true);

### setBluetoothState()

Enables/disables Bluetooth on the device.

    cordova.plugins.diagnostic.setBluetoothState(successCallback, errorCallback, state);

Requires the following permissions on Android:

    <uses-permission android:name="android.permission.BLUETOOTH"/>
    <uses-permission android:name="android.permission.BLUETOOTH_ADMIN"/>

Requires the following capabilities for Windows 10 Mobile:

    <DeviceCapability Name="radios" />

#### Parameters

- {Function} successCallback - function to call on successful setting of Bluetooth state
- {Function} errorCallback - function to call on failure to set Bluetooth state.
- {Boolean} state - Bluetooth state to set: TRUE for enabled, FALSE for disabled.


#### Example usage

    cordova.plugins.diagnostic.setBluetoothState(function(){
        console.log("Bluetooth was enabled");
    }, function(error){
        console.error("The following error occurred: "+error);
    },
    true);

## Android and iOS

### permissionStatus constants

Both Android and iOS define constants for requesting and reporting the various permission states.

    cordova.plugins.diagnostic.permissionStatus

#### Android

The following permission states are defined for Android:

- `NOT_REQUESTED` - App has not yet requested access to this permission.
App can request permission and user will be prompted to allow/deny.
- `GRANTED` - User granted access to this permission, the device is running Android 5.x or below, or the app is built with API 22 or below.
- `DENIED` - User denied access to this permission (without checking "Never Ask Again" box).
App can request permission again and user will be prompted again to allow/deny again.
- `DENIED_ALWAYS` - User denied access to this permission and checked "Never Ask Again" box.
App can never ask for permission again.
The only way around this is to instruct the user to manually change the permission on the app permissions settings page.

#### iOS

The following permission states are defined for iOS:

- `NOT_REQUESTED` - App has not yet requested access to this permission.
App can request permission and user will be prompted to allow/deny.
- `DENIED` - User denied access to this permission.
App can never ask for permission again.
The only way around this is to instruct the user to manually change the permission in the Settings app.
- `RESTRICTED` - Permission is unavailable and user cannot enable it.
For example, when parental controls are in effect for the current user.
- `GRANTED` - User granted access to this permission.
For location permission, this indicates the user has granted access to the permission "always" (when app is both in foreground and background).
- `GRANTED_WHEN_IN_USE` - Used only for location permission.
Indicates the user has granted access to the permission "when in use" (only when the app is in the foreground).

#### Example

    if(somePermissionStatus === cordova.plugins.diagnostic.permissionStatus.GRANTED){
        // Do something
    }

### bluetoothState constants

Defines constants for the various Bluetooth hardware states

        cordova.plugins.diagnostic.bluetoothState

#### Android

- `UNKNOWN` - Bluetooth hardware state is unknown or unavailable
- `POWERED_OFF` - Bluetooth hardware is switched off
- `POWERED_ON` - Bluetooth hardware is switched on and available for use
- `POWERING_OFF`- Bluetooth hardware is currently switching off
- `POWERING_ON`- Bluetooth hardware is currently switching on

#### iOS

- `UNKNOWN` - Bluetooth hardware state is unknown
- `RESETTING` - Bluetooth hardware state is currently resetting
- `POWERED_OFF` - Bluetooth hardware is switched off
- `POWERED_ON` - Bluetooth hardware is switched on and available for use
- `UNAUTHORIZED`- Bluetooth hardware use is not authorized for the current application

#### Example

    cordova.plugins.diagnostic.getBluetoothState(function(state){
        if(state === cordova.plugins.diagnostic.bluetoothState.POWERED_ON){
            // Do something with Bluetooth
        }
    }, function(error){
        console.error(error);
    });

### isLocationEnabled()

Returns true if the device setting for location is on.
On Android this returns true if Location Mode is switched on.
On iOS this returns true if Location Services is switched on.

    cordova.plugins.diagnostic.isLocationEnabled(successCallback, errorCallback);

#### Parameters

- {Function} successCallback -  The callback which will be called when operation is successful.
This callback function is passed a single boolean parameter which is TRUE if location setting is enabled.
- {Function} errorCallback -  The callback which will be called when operation encounters an error.
This callback function is passed a single string parameter containing the error message.


#### Example usage

    cordova.plugins.diagnostic.isLocationEnabled(function(enabled){
        console.log("Location setting is " + (enabled ? "enabled" : "disabled"));
    }, function(error){
        console.error("The following error occurred: "+error);
    });

### isLocationAuthorized()

Checks if the application is authorized to use location.

Notes for Android:

- This is intended for Android 6 / API 23 and above.
Calling on Android 5 / API 22 and below will always return GRANTED status as permissions are already granted at installation time.

    `cordova.plugins.diagnostic.isLocationAuthorized(successCallback, errorCallback);`

#### Parameters

- {Function} successCallback -  The callback which will be called when operation is successful.
This callback function is passed a single boolean parameter.
On iOS this will return TRUE if application is authorized to use location either "when in use" (only in foreground) OR "always" (foreground and background).
On Android this will return TRUE if the app currently has runtime authorisation to use location.
- {Function} errorCallback -  The callback which will be called when operation encounters an error.
This callback function is passed a single string parameter containing the error message.


#### Example usage

    cordova.plugins.diagnostic.isLocationAuthorized(function(authorized){
        console.log("Location is " + (authorized ? "authorized" : "unauthorized"));
    }, function(error){
        console.error("The following error occurred: "+error);
    });

### getLocationAuthorizationStatus()

 Returns the location authorization status for the application.

 Note for Android: this is intended for Android 6 / API 23 and above. Calling on Android 5 / API 22 and below will always return GRANTED status as permissions are already granted at installation time.

    cordova.plugins.diagnostic.getLocationAuthorizationStatus(successCallback, errorCallback);

#### Parameters

- {Function} successCallback -  The callback which will be called when operation is successful.
This callback function is passed a single string parameter which indicates the location authorization status as a [permissionStatus constant](#permissionstatus-constants).
- {Function} errorCallback -  The callback which will be called when operation encounters an error.
This callback function is passed a single string parameter containing the error message.

#### Example iOS usage

    cordova.plugins.diagnostic.getLocationAuthorizationStatus(function(status){
       switch(status){
           case cordova.plugins.diagnostic.permissionStatus.NOT_REQUESTED:
               console.log("Permission not requested");
               break;
           case cordova.plugins.diagnostic.permissionStatus.DENIED:
               console.log("Permission denied");
               break;
           case cordova.plugins.diagnostic.permissionStatus.GRANTED:
               console.log("Permission granted always");
               break;
           case cordova.plugins.diagnostic.permissionStatus.GRANTED_WHEN_IN_USE:
               console.log("Permission granted only when in use");
               break;
       }
    }, function(error){
        console.error("The following error occurred: "+error);
    });

#### Example Android usage

    cordova.plugins.diagnostic.getLocationAuthorizationStatus(function(status){
        switch(status){
            case cordova.plugins.diagnostic.permissionStatus.NOT_REQUESTED:
                console.log("Permission not requested");
                break;
            case cordova.plugins.diagnostic.permissionStatus.GRANTED:
                console.log("Permission granted");
                break;
            case cordova.plugins.diagnostic.permissionStatus.DENIED:
                console.log("Permission denied");
                break;
            case cordova.plugins.diagnostic.permissionStatus.DENIED_ALWAYS:
                console.log("Permission permanently denied");
                break;
        }
    }, function(error){
        console.error(error);
    });

### requestLocationAuthorization()

 Requests location authorization for the application.

 Notes for iOS:

- Calling this on iOS 7 or below will have no effect, as location permissions are are implicitly granted.
- On iOS 8+, authorization can be requested to use location either "when in use" (only in foreground) or "always" (foreground and background).
- This should only be called if authorization status is NOT_DETERMINED - calling it when in any other state will have no effect.
- When calling this function, the messages contained in the  `NSLocationAlwaysUsageDescription` and `NSLocationWhenInUseUsageDescription` .plist keys are displayed to the user when requesting to use location **always** or **when in use**, respectively;
this plugin provides default messages, but you should override them with your specific reason for requesting access - see the [iOS usage description messages](#ios-usage-description-messages) section for how to customise them.

 Notes for Android:

- This is intended for Android 6 / API 23 and above. Calling on Android 5 / API 22 and below will have no effect as the permissions are already granted at installation time.
- The successCallback is invoked in response to the user's choice in the permission dialog and is passed the resulting authorization status.

    `cordova.plugins.diagnostic.requestLocationAuthorization(successCallback, errorCallback, mode);`

#### Parameters

- {Function} successCallback - Invoked in response to the user's choice in the permission dialog.
It is passed a single string parameter which defines the [resulting authorisation status](#runtime-permission-statuses).
- {Function} errorCallback -  The callback which will be called when operation encounters an error.
This callback function is passed a single string parameter containing the error message.
- {String} mode - (iOS-only / optional) location authorization mode specified as a [locationAuthorizationMode constant](#locationauthorizationmode-constants).
If not specified, defaults to `WHEN_IN_USE`.

#### Example iOS usage

    cordova.plugins.diagnostic.requestLocationAuthorization(function(status){
        switch(status){
            case cordova.plugins.diagnostic.permissionStatus.NOT_REQUESTED:
                console.log("Permission not requested");
                break;
            case cordova.plugins.diagnostic.permissionStatus.DENIED:
                console.log("Permission denied");
                break;
            case cordova.plugins.diagnostic.permissionStatus.GRANTED:
                console.log("Permission granted always");
                break;
            case cordova.plugins.diagnostic.permissionStatus.GRANTED_WHEN_IN_USE:
                console.log("Permission granted only when in use");
                break;
        }
    }, function(error){
        console.error(error);
    }, cordova.plugins.diagnostic.locationAuthorizationMode.ALWAYS);

#### Example Android usage

    cordova.plugins.diagnostic.requestLocationAuthorization(function(status){
        switch(status){
            case cordova.plugins.diagnostic.permissionStatus.NOT_REQUESTED:
                console.log("Permission not requested");
                break;
            case cordova.plugins.diagnostic.permissionStatus.GRANTED:
                console.log("Permission granted");
                break;
            case cordova.plugins.diagnostic.permissionStatus.DENIED:
                console.log("Permission denied");
                break;
            case cordova.plugins.diagnostic.permissionStatus.DENIED_ALWAYS:
                console.log("Permission permanently denied");
                break;
        }
    }, function(error){
        console.error(error);
    });

### isCameraPresent()

Checks if camera hardware is present on device.

    cordova.plugins.diagnostic.isCameraPresent(successCallback, errorCallback);

#### Parameters

- {Function} successCallback -  The callback which will be called when operation is successful.
This callback function is passed a single boolean parameter which is TRUE if camera is present
- {Function} errorCallback -  The callback which will be called when operation encounters an error.
This callback function is passed a single string parameter containing the error message.


#### Example usage

    cordova.plugins.diagnostic.isCameraPresent(function(present){
        console.log("Camera is " + (present ? "present" : "absent"));
    }, function(error){
        console.error("The following error occurred: "+error);
    });

### isCameraAuthorized()

Checks if the application is authorized to use the camera.

Notes for Android:
- This is intended for Android 6 / API 23 and above. Calling on Android 5 / API 22 and below will always return TRUE as permissions are already granted at installation time.
- By default this checks run-time permission for both `READ_EXTERNAL_STORAGE` and `CAMERA` because [cordova-plugin-camera@2.2+](https://github.com/apache/cordova-plugin-camera) requires both of these permissions.
- The call signature `cordova.plugins.diagnostic.isCameraAuthorized(successCallback, errorCallback, externalStorage)` is also supported for benefit of the [ionic-native Promise API wrapper](https://github.com/driftyco/ionic-native/blob/master/src/%40ionic-native/plugins/diagnostic/index.ts).


    cordova.plugins.diagnostic.isCameraAuthorized(params);
    cordova.plugins.diagnostic.isCameraAuthorized(successCallback, errorCallback, params)
    cordova.plugins.diagnostic.isCameraAuthorized(successCallback, errorCallback, externalStorage)

#### Parameters
- {Object} params - (optional) parameters:
    - {Function} successCallback -  The callback which will be called when operation is successful.
This callback function is passed a single boolean parameter which is TRUE if camera is authorized for use.
    - {Function} errorCallback -  The callback which will be called when operation encounters an error.
This callback function is passed a single string parameter containing the error message.
    - {Boolean} externalStorage - (Android only) If true, checks permission for `READ_EXTERNAL_STORAGE` in addition to `CAMERA` run-time permission.
Defaults to true.

#### Example usage

    cordova.plugins.diagnostic.isCameraAuthorized({
        successCallback: function(authorized){
            console.log("App is " + (authorized ? "authorized" : "denied") + " access to the camera");
        },
        errorCallback: function(error){
            console.error("The following error occurred: "+error);
        }, 
        externalStorage: false
    });
    
    cordova.plugins.diagnostic.isCameraAuthorized(
        function(authorized){
            console.log("App is " + (authorized ? "authorized" : "denied") + " access to the camera");
        }, function(error){
            console.error("The following error occurred: "+error);
        }, {
            externalStorage: false
        }
    );
    
    cordova.plugins.diagnostic.isCameraAuthorized(
        function(authorized){
            console.log("App is " + (authorized ? "authorized" : "denied") + " access to the camera");
        }, function(error){
            console.error("The following error occurred: "+error);
        }, false
    );    

### getCameraAuthorizationStatus()

Returns the camera authorization status for the application.

Notes for Android:
- This is intended for Android 6 / API 23 and above. Calling on Android 5 / API 22 and below will always return GRANTED status as permissions are already granted at installation time.
- By default this checks run-time permission for both `READ_EXTERNAL_STORAGE` and `CAMERA` because [cordova-plugin-camera@2.2+](https://github.com/apache/cordova-plugin-camera) requires both of these permissions.
- The call signature `cordova.plugins.diagnostic.getCameraAuthorizationStatus(successCallback, errorCallback, externalStorage)` is also supported for benefit of the [ionic-native Promise API wrapper](https://github.com/driftyco/ionic-native/blob/master/src/%40ionic-native/plugins/diagnostic/index.ts).


    cordova.plugins.diagnostic.getCameraAuthorizationStatus(params);
    cordova.plugins.diagnostic.getCameraAuthorizationStatus(successCallback, errorCallback, params)
    cordova.plugins.diagnostic.getCameraAuthorizationStatus(successCallback, errorCallback, externalStorage)

#### Parameters
- {Object} params - (optional) parameters:
    - {Function} successCallback -  The callback which will be called when operation is successful.
This callback function is passed a single string parameter which indicates the authorization status as a [permissionStatus constant](#permissionstatus-constants).
    - {Function} errorCallback -  The callback which will be called when operation encounters an error.
This callback function is passed a single string parameter containing the error message.
    - {Boolean} externalStorage - (Android only) If true, checks permission for `READ_EXTERNAL_STORAGE` in addition to `CAMERA` run-time permission.
Defaults to true.


#### Example usage

    cordova.plugins.diagnostic.getCameraAuthorizationStatus({
        successCallback: function(status){
            if(status === cordova.plugins.diagnostic.permissionStatus.GRANTED){
                console.log("Camera use is authorized");
            }
        },
        errorCallback: function(error){
            console.error("The following error occurred: "+error);
        },
        externalStorage: false
    });
    
    cordova.plugins.diagnostic.getCameraAuthorizationStatus(
        function(status){
            if(status === cordova.plugins.diagnostic.permissionStatus.GRANTED){
                console.log("Camera use is authorized");
            }
        }, function(error){
            console.error("The following error occurred: "+error);
        }, {
            externalStorage: false
        }
    );
    
    cordova.plugins.diagnostic.getCameraAuthorizationStatus(
        function(status){
            if(status === cordova.plugins.diagnostic.permissionStatus.GRANTED){
                console.log("Camera use is authorized");
            }
        }, function(error){
            console.error("The following error occurred: "+error);
        }, false
    );   

### requestCameraAuthorization()

Requests camera authorization for the application.


Notes for iOS:
- Should only be called if authorization status is NOT_DETERMINED. Calling it when in any other state will have no effect.
- When calling this function, the message contained in the `NSCameraUsageDescription` .plist key is displayed to the user;
this plugin provides a default message, but you should override this with your specific reason for requesting access - see the [iOS usage description messages](#ios-usage-description-messages) section for how to customise it.

Notes for Android:
- This is intended for Android 6 / API 23 and above. Calling on Android 5 / API 22 and below will have no effect as the permissions are already granted at installation time.
- By default this requests run-time permission for both `READ_EXTERNAL_STORAGE` and `CAMERA` because [cordova-plugin-camera@2.2+](https://github.com/apache/cordova-plugin-camera) requires both of these permissions.
- Requested run-time permissions which must be added to `AndroidManifest.xml` - see [Android camera permissions](#android-camera-permissions).
- The call signature `cordova.plugins.diagnostic.requestCameraAuthorization(successCallback, errorCallback, externalStorage)` is also supported for benefit of the [ionic-native Promise API wrapper](https://github.com/driftyco/ionic-native/blob/master/src/%40ionic-native/plugins/diagnostic/index.ts).

    
    cordova.plugins.diagnostic.requestCameraAuthorization(params);
    cordova.plugins.diagnostic.requestCameraAuthorization(successCallback, errorCallback, params)
    cordova.plugins.diagnostic.requestCameraAuthorization(successCallback, errorCallback, externalStorage)

#### Parameters

- {Object} params - (optional) parameters:
    - {Function} successCallback -  The callback which will be called when operation is successful.
This callback function is passed a single string parameter indicating whether access to the camera was granted or denied:
`cordova.plugins.diagnostic.permissionStatus.GRANTED` or `cordova.plugins.diagnostic.permissionStatus.DENIED`
    - {Function} errorCallback -  The callback which will be called when operation encounters an error.
This callback function is passed a single string parameter containing the error message.
    - {Boolean} externalStorage - (Android only) If true, requests permission for `READ_EXTERNAL_STORAGE` in addition to `CAMERA` run-time permission.
    Defaults to true.

#### Example usage

    cordova.plugins.diagnostic.requestCameraAuthorization({
        successCallback: function(status){
            console.log("Authorization request for camera use was " + (status == cordova.plugins.diagnostic.permissionStatus.GRANTED ? "granted" : "denied"));
        },
        errorCallback: function(error){
            console.error(error);
        },
        externalStorage: false
    });
    
    cordova.plugins.diagnostic.requestCameraAuthorization(
        function(status){
            console.log("Authorization request for camera use was " + (status == cordova.plugins.diagnostic.permissionStatus.GRANTED ? "granted" : "denied"));
        }, function(error){
            console.error("The following error occurred: "+error);
        }, {
            externalStorage: false
        }
    );
    
    cordova.plugins.diagnostic.requestCameraAuthorization(
        function(status){
            console.log("Authorization request for camera use was " + (status == cordova.plugins.diagnostic.permissionStatus.GRANTED ? "granted" : "denied"));
        }, function(error){
            console.error("The following error occurred: "+error);
        }, false
    );   

### isMicrophoneAuthorized()

Checks if the application is authorized to use the microphone.

Notes for Android:
- This is intended for Android 6 / API 23 and above. Calling on Android 5 / API 22 and below will always return TRUE as permissions are already granted at installation time.

Notes for iOS:
- Requires iOS 8+

    `cordova.plugins.diagnostic.isMicrophoneAuthorized(successCallback, errorCallback);`

#### Parameters

- {Function} successCallback -  The callback which will be called when operation is successful.
This callback function is passed a single boolean parameter which is TRUE if microphone is authorized for use.
- {Function} errorCallback -  The callback which will be called when operation encounters an error.
This callback function is passed a single string parameter containing the error message.


#### Example usage

    cordova.plugins.diagnostic.isMicrophoneAuthorized(function(authorized){
        console.log("App is " + (authorized ? "authorized" : "denied") + " access to the microphone");
    }, function(error){
        console.error("The following error occurred: "+error);
    });

### getMicrophoneAuthorizationStatus()

Returns the microphone authorization status for the application.

Notes for Android:
- This is intended for Android 6 / API 23 and above. Calling on Android 5 / API 22 and below will always return GRANTED status as permissions are already granted at installation time.

Notes for iOS:
- Requires iOS 8+

    `cordova.plugins.diagnostic.getMicrophoneAuthorizationStatus(successCallback, errorCallback);`

#### Parameters

- {Function} successCallback -  The callback which will be called when operation is successful.
This callback function is passed a single string parameter which indicates the authorization status as a [permissionStatus constant](#permissionstatus-constants).
- {Function} errorCallback -  The callback which will be called when operation encounters an error.
This callback function is passed a single string parameter containing the error message.

#### Example usage

    cordova.plugins.diagnostic.getMicrophoneAuthorizationStatus(function(status){
       if(status === cordova.plugins.diagnostic.permissionStatus.GRANTED){
           console.log("Microphone use is authorized");
       }
    }, function(error){
        console.error("The following error occurred: "+error);
    });


### requestMicrophoneAuthorization()

Requests microphone authorization for the application.

Notes for iOS:
- Should only be called if authorization status is NOT_DETERMINED. Calling it when in any other state will have no effect and just return the current authorization status.
- When calling this function, the message contained in the `NSMicrophoneUsageDescription` .plist key is displayed to the user;
this plugin provides a default message, but you should override this with your specific reason for requesting access - see the [iOS usage description messages](#ios-usage-description-messages) section for how to customise it.
- Requires iOS 7+

Notes for Android:
- This is intended for Android 6 / API 23 and above. Calling on Android 5 / API 22 and below will have no effect as the permissions are already granted at installation time.
- This requests permission for `RECORD_AUDIO` which must be added to `AndroidManifest.xml` - see [Android permissions](#android-permissions).

    cordova.plugins.diagnostic.requestMicrophoneAuthorization(successCallback, errorCallback);

#### Parameters
- {Function} successCallback - The callback which will be called when operation is successful.
This callback function is passed a single string parameter indicating whether access to the microphone was granted or denied:
`cordova.plugins.diagnostic.permissionStatus.GRANTED` or `cordova.plugins.diagnostic.permissionStatus.DENIED`
- {Function} errorCallback - The callback which will be called when an error occurs. This callback function is passed a single string parameter containing the error message.

#### Example usage

    cordova.plugins.diagnostic.requestMicrophoneAuthorization(function(status){
       if(status === cordova.plugins.diagnostic.permissionStatus.GRANTED){
           console.log("Microphone use is authorized");
       }
    }, function(error){
        console.error(error);
    });

### isContactsAuthorized()

Checks if the application is authorized to use contacts (address book).

Notes for Android:
- This is intended for Android 6 / API 23 and above. Calling on Android 5 / API 22 and below will always return TRUE as permissions are already granted at installation time.

    `cordova.plugins.diagnostic.isContactsAuthorized(successCallback, errorCallback);`

#### Parameters

- {Function} successCallback -  The callback which will be called when operation is successful.
This callback function is passed a single boolean parameter which is TRUE if contacts is authorized for use.
- {Function} errorCallback -  The callback which will be called when operation encounters an error.
This callback function is passed a single string parameter containing the error message.


#### Example usage

    cordova.plugins.diagnostic.isContactsAuthorized(function(authorized){
        console.log("App is " + (authorized ? "authorized" : "denied") + " access to contacts");
    }, function(error){
        console.error("The following error occurred: "+error);
    });

### getContactsAuthorizationStatus()

Returns the contacts authorization status for the application.

Notes for Android:
- This is intended for Android 6 / API 23 and above. Calling on Android 5 / API 22 and below will always return GRANTED status as permissions are already granted at installation time.

    `cordova.plugins.diagnostic.getContactsAuthorizationStatus(successCallback, errorCallback);`

#### Parameters

- {Function} successCallback -  The callback which will be called when operation is successful.
This callback function is passed a single string parameter which indicates the authorization status as a [permissionStatus constant](#permissionstatus-constants).
- {Function} errorCallback -  The callback which will be called when operation encounters an error.
This callback function is passed a single string parameter containing the error message.

#### Example usage

    cordova.plugins.diagnostic.getContactsAuthorizationStatus(function(status){
        if(status === cordova.plugins.diagnostic.permissionStatus.GRANTED){
            console.log("Contacts use is authorized");
        }
    }, function(error){
        console.error("The following error occurred: "+error);
    });


### requestContactsAuthorization()

Requests contacts authorization for the application.

Notes for iOS:
- Should only be called if authorization status is NOT_DETERMINED. Calling it when in any other state will have no effect and just return the current authorization status.
- When calling this function, the message contained in the `NSContactsUsageDescription` .plist key is displayed to the user;
this plugin provides a default message, but you should override this with your specific reason for requesting access - see the [iOS usage description messages](#ios-usage-description-messages) section for how to customise it.

Notes for Android:
- This is intended for Android 6 / API 23 and above. Calling on Android 5 / API 22 and below will have no effect as the permissions are already granted at installation time.
- This requests permission for `READ_CONTACTS` run-time permission
- Required permissions must be added to `AndroidManifest.xml` as appropriate - see [Android permissions](#android-permissions): `READ_CONTACTS, WRITE_CONTACTS, GET_ACCOUNTS`

    cordova.plugins.diagnostic.requestContactsAuthorization(successCallback, errorCallback);

#### Parameters
- {Function} successCallback - The callback which will be called when operation is successful.
This callback function is passed a single string parameter indicating whether access to contacts was granted or denied:
`cordova.plugins.diagnostic.permissionStatus.GRANTED` or `cordova.plugins.diagnostic.permissionStatus.DENIED`
- {Function} errorCallback - The callback which will be called when an error occurs. This callback function is passed a single string parameter containing the error message.

#### Example usage

    cordova.plugins.diagnostic.requestContactsAuthorization(function(status){
        if(status === cordova.plugins.diagnostic.permissionStatus.GRANTED){
            console.log("Contacts use is authorized");
        }
    }, function(error){
        console.error(error);
    });
    
### isCalendarAuthorized()

Checks if the application is authorized to use the calendar.

Notes for Android:
- This is intended for Android 6 / API 23 and above. Calling on Android 5 / API 22 and below will always return TRUE as permissions are already granted at installation time.

Notes for iOS:
- This relates to Calendar Events (not Calendar Reminders)

    `cordova.plugins.diagnostic.isCalendarAuthorized(successCallback, errorCallback);`

#### Parameters

- {Function} successCallback -  The callback which will be called when operation is successful.
This callback function is passed a single boolean parameter which is TRUE if calendar is authorized for use.
- {Function} errorCallback -  The callback which will be called when operation encounters an error.
This callback function is passed a single string parameter containing the error message.


#### Example usage

    cordova.plugins.diagnostic.isCalendarAuthorized(function(authorized){
        console.log("App is " + (authorized ? "authorized" : "denied") + " access to calendar");
    }, function(error){
        console.error("The following error occurred: "+error);
    });

### getCalendarAuthorizationStatus()

Returns the calendar authorization status for the application.

Notes for Android:
- This is intended for Android 6 / API 23 and above. Calling on Android 5 / API 22 and below will always return GRANTED status as permissions are already granted at installation time.

Notes for iOS:
- This relates to Calendar Events (not Calendar Reminders)

    `cordova.plugins.diagnostic.getCalendarAuthorizationStatus(successCallback, errorCallback);`

#### Parameters

- {Function} successCallback -  The callback which will be called when operation is successful.
This callback function is passed a single string parameter which indicates the authorization status as a [permissionStatus constant](#permissionstatus-constants).
- {Function} errorCallback -  The callback which will be called when operation encounters an error.
This callback function is passed a single string parameter containing the error message.

#### Example usage

    cordova.plugins.diagnostic.getCalendarAuthorizationStatus(function(status){
       if(status === cordova.plugins.diagnostic.permissionStatus.GRANTED){
           console.log("Calendar use is authorized");
       }
    }, function(error){
        console.error("The following error occurred: "+error);
    });


### requestCalendarAuthorization()

Requests calendar authorization for the application.

Notes for iOS:
- Should only be called if authorization status is NOT_DETERMINED. Calling it when in any other state will have no effect and just return the current authorization status.
- When calling this function, the message contained in the `NSCalendarsUsageDescription` .plist key is displayed to the user;
this plugin provides a default message, but you should override this with your specific reason for requesting access - see the [iOS usage description messages](#ios-usage-description-messages) section for how to customise it.
- This relates to Calendar Events (not Calendar Reminders)

Notes for Android:
- This is intended for Android 6 / API 23 and above. Calling on Android 5 / API 22 and below will have no effect as the permissions are already granted at installation time.
- This requests permission for `READ_CALENDAR` run-time permission
- Required permissions must be added to `AndroidManifest.xml` as appropriate - see [Android permissions](#android-permissions): `READ_CALENDAR, WRITE_CALENDAR`

    cordova.plugins.diagnostic.requestCalendarAuthorization(successCallback, errorCallback);

#### Parameters
- {Function} successCallback - The callback which will be called when operation is successful.
This callback function is passed a single string parameter indicating whether access to calendar was granted or denied:
`cordova.plugins.diagnostic.permissionStatus.GRANTED` or `cordova.plugins.diagnostic.permissionStatus.DENIED`
- {Function} errorCallback - The callback which will be called when an error occurs. This callback function is passed a single string parameter containing the error message.

#### Example usage

    cordova.plugins.diagnostic.requestCalendarAuthorization(function(status){
       if(status === cordova.plugins.diagnostic.permissionStatus.GRANTED){
           console.log("Calendar use is authorized");
       }
    }, function(error){
        console.error(error);
    });
    
### switchToSettings()

Opens settings page for this app.

On Android, this opens the "App Info" page in the Settings app.

On iOS, this opens the app settings page in the Settings app. This works only on iOS 8+ - iOS 7 and below will invoke the errorCallback.

    cordova.plugins.diagnostic.switchToSettings(successCallback, errorCallback);

#### Parameters

- {Function} successCallback - The callback which will be called when switch to settings is successful.
- {Function} errorCallback - The callback which will be called when switch to settings encounters an error. This callback function is passed a single string parameter containing the error message.


#### Example usage

    cordova.plugins.diagnostic.switchToSettings(function(){
        console.log("Successfully switched to Settings app");
    }, function(error){
        console.error("The following error occurred: "+error);
    });

### getBluetoothState()

Returns the state of Bluetooth on the device.

    cordova.plugins.diagnostic.getBluetoothState(successCallback, errorCallback);

#### Parameters

- {Function} successCallback -  The callback which will be called when operation is successful.
This callback function is passed a single string parameter which indicates the Bluetooth state as a constant in [`cordova.plugins.diagnostic.bluetoothState`](#bluetoothstate-constants).
- {Function} errorCallback -  The callback which will be called when operation encounters an error.
This callback function is passed a single string parameter containing the error message.

#### Example usage

    cordova.plugins.diagnostic.getBluetoothState(function(state){
       if(state === cordova.plugins.diagnostic.bluetoothState.POWERED_ON){
           console.log("Bluetooth is able to connect");
       }
    }, function(error){
        console.error(error);
    });

### registerBluetoothStateChangeHandler()

Registers a function to be called when a change in Bluetooth state occurs.
Pass in a falsey value to de-register the currently registered function.

This is triggered when Bluetooth state changes so is useful for detecting changes made in quick settings which would not result in pause/resume events being fired.

    cordova.plugins.diagnostic.registerBluetoothStateChangeHandler(successCallback);

#### Parameters

- {Function} successCallback - function call when a change in Bluetooth state occurs.
This callback function is passed a single string parameter which indicates the Bluetooth state as a constant in [`cordova.plugins.diagnostic.bluetoothState`](#bluetoothstate-constants).

#### Example usage

    cordova.plugins.diagnostic.registerBluetoothStateChangeHandler(function(state){
       if(state === cordova.plugins.diagnostic.bluetoothState.POWERED_ON){
           console.log("Bluetooth is able to connect");
       }
    });

### registerLocationStateChangeHandler()

Registers a function to be called when a change in Location state occurs.
Pass in a falsey value to de-register the currently registered function.

This is triggered when Location state changes so is useful for detecting changes made in quick settings which would not result in pause/resume events being fired.

On Android, this occurs when the Location Mode is changed.

On iOS, this occurs when location authorization status is changed.
This can be triggered either by the user's response to a location permission authorization dialog,
by the user turning on/off Location Services,
or by the user changing the Location authorization state specifically for your app.

    cordova.plugins.diagnostic.registerLocationStateChangeHandler(successCallback);

#### Parameters

- {Function} successCallback - function call when a change in location state occurs.
On Android, the function is passed a single string parameter defined as a constant in `cordova.plugins.diagnostic.locationMode`.
On iOS, the function is passed a single string parameter indicating the new location authorisation status as a constant in `cordova.plugins.diagnostic.permissionStatus`.

#### Example usage

    cordova.plugins.diagnostic.registerLocationStateChangeHandler(function(state){
        if((device.platform === "Android" && state !== cordova.plugins.diagnostic.locationMode.LOCATION_OFF)
            || (device.platform === "iOS") && ( state === cordova.plugins.diagnostic.permissionStatus.GRANTED
                || state === cordova.plugins.diagnostic.permissionStatus.GRANTED_WHEN_IN_USE
        )){
            console.log("Location is available");
        }
    });

## Android only

### locationMode constants

Defines constants for the various location modes on Android.

    cordova.plugins.diagnostic.locationMode

#### Values

- `HIGH_ACCURACY` - GPS hardware, network triangulation and Wifi network IDs (high and low accuracy)
- `BATTERY_SAVING` - Network triangulation and Wifi network IDs (low accuracy)
- `DEVICE_ONLY` -  GPS hardware (high accuracy)
- `LOCATION_OFF` - Location services disabled (no accuracy)

#### Example

    cordova.plugins.diagnostic.getLocationMode(function(locationMode){
        switch(locationMode){
            case cordova.plugins.diagnostic.locationMode.HIGH_ACCURACY:
                console.log("High accuracy");
                break;
            case cordova.plugins.diagnostic.locationMode.BATTERY_SAVING:
                console.log("Battery saving");
                break;
            case cordova.plugins.diagnostic.locationMode.DEVICE_ONLY:
                console.log("Device only");
                break;
            case cordova.plugins.diagnostic.locationMode.LOCATION_OFF:
                console.log("Location off");
                break;
        }
    },function(error){
        console.error("The following error occurred: "+error);
    });

### isGpsLocationAvailable()

Checks if high-accuracy locations are available to the app from GPS hardware.
Returns true if Location mode is enabled and is set to "Device only" or "High accuracy" AND if the app is authorised to use location.

    cordova.plugins.diagnostic.isGpsLocationAvailable(successCallback, errorCallback);

#### Parameters

- {Function} successCallback -  The callback which will be called when operation is successful.
This callback function is passed a single boolean parameter which is TRUE if high-accuracy GPS-based location is available.
- {Function} errorCallback -  The callback which will be called when operation encounters an error.
This callback function is passed a single string parameter containing the error message.


#### Example usage

    cordova.plugins.diagnostic.isGpsLocationAvailable(function(available){
        console.log("GPS location is " + (available ? "available" : "not available"));
    }, function(error){
        console.error("The following error occurred: "+error);
    });

### isGpsLocationEnabled()

Checks if the device location setting is set to return high-accuracy locations from GPS hardware.
Returns true if Location mode is enabled and is set to either:

- Device only = GPS hardware only (high accuracy)
- High accuracy = GPS hardware, network triangulation and Wifi network IDs (high and low accuracy)


    cordova.plugins.diagnostic.isGpsLocationEnabled(successCallback, errorCallback);

#### Parameters

- {Function} successCallback -  The callback which will be called when operation is successful.
This callback function is passed a single boolean parameter which is TRUE if device setting is set to return high-accuracy GPS-based location.
- {Function} errorCallback -  The callback which will be called when operation encounters an error.
This callback function is passed a single string parameter containing the error message.


#### Example usage

    cordova.plugins.diagnostic.isGpsLocationEnabled(function(enabled){
        console.log("GPS location is " + (enabled ? "enabled" : "disabled"));
    }, function(error){
        console.error("The following error occurred: "+error);
    });

### isNetworkLocationAvailable()

Checks if low-accuracy locations are available to the app from network triangulation/WiFi access points.
Returns true if Location mode is enabled and is set to "Battery saving" or "High accuracy"
AND if the app is authorised to use location.

    cordova.plugins.diagnostic.isNetworkLocationAvailable(successCallback, errorCallback);

#### Parameters

- {Function} successCallback -  The callback which will be called when operation is successful.
This callback function is passed a single boolean parameter which is TRUE if low-accuracy network-based location is available.
- {Function} errorCallback -  The callback which will be called when operation encounters an error.
This callback function is passed a single string parameter containing the error message.


#### Example usage

    cordova.plugins.diagnostic.isNetworkLocationAvailable(function(available){
        console.log("Network location is " + (available ? "available" : "not available"));
    }, function(error){
        console.error("The following error occurred: "+error);
    });

### isNetworkLocationEnabled()

Checks if location mode is set to return low-accuracy locations from network triangulation/WiFi access points
Returns true if Location mode is enabled and is set to either:

- Battery saving = network triangulation and Wifi network IDs (low accuracy)
- High accuracy = GPS hardware, network triangulation and Wifi network IDs (high and low accuracy)


    cordova.plugins.diagnostic.isNetworkLocationEnabled(successCallback, errorCallback);

#### Parameters

- {Function} successCallback -  The callback which will be called when operation is successful.
This callback function is passed a single boolean parameter which is TRUE if device setting is set to return low-accuracy network-based location.
- {Function} errorCallback -  The callback which will be called when operation encounters an error.
This callback function is passed a single string parameter containing the error message.


#### Example usage

    cordova.plugins.diagnostic.isNetworkLocationEnabled(function(enabled){
        console.log("Network location is " + (enabled ? "enabled" : "disabled"));
    }, function(error){
        console.error("The following error occurred: "+error);
    });

### getLocationMode()

Returns the current location mode setting for the device.

    cordova.plugins.diagnostic.getLocationMode(successCallback, errorCallback);

#### Parameters

- {Function} successCallback -  The callback which will be called when operation is successful.
This callback function is passed a single string parameter indicating the current location mode
as a constant in `cordova.plugins.diagnostic.locationMode`.
- {Function} errorCallback -  The callback which will be called when operation encounters an error.
This callback function is passed a single string parameter containing the error message.


#### Example usage

    cordova.plugins.diagnostic.getLocationMode(function(locationMode){
        switch(locationMode){
            case cordova.plugins.diagnostic.locationMode.HIGH_ACCURACY:
                console.log("High accuracy");
                break;
            case cordova.plugins.diagnostic.locationMode.BATTERY_SAVING:
                console.log("Battery saving");
                break;
            case cordova.plugins.diagnostic.locationMode.DEVICE_ONLY:
                console.log("Device only");
                break;
            case cordova.plugins.diagnostic.locationMode.LOCATION_OFF:
                console.log("Location off");
                break;
        }
    },function(error){
        console.error("The following error occurred: "+error);
    });

### getPermissionAuthorizationStatus()

Returns the current authorisation status for a given permission.

Note: this is intended for Android 6 / API 23 and above. Calling on Android 5 / API 22 and below will always return GRANTED status as permissions are already granted at installation time.

#### Parameters

- {Function} successCallback - function to call on successful retrieval of status.
This callback function is passed a single string parameter which defines the current [permission status](#permissionstatus-constants)
- {Function} errorCallback - function to call on failure to retrieve authorisation status.
This callback function is passed a single string parameter containing the error message.
- {String} permission - permission to request authorisation status for, defined as a [runtime permission constant](#dangerous-runtime-permissions).

#### Example usage

    cordova.plugins.diagnostic.getPermissionAuthorizationStatus(function(status){
        switch(status){
            case cordova.plugins.diagnostic.permissionStatus.GRANTED:
                console.log("Permission granted to use the camera");
                break;
            case cordova.plugins.diagnostic.permissionStatus.NOT_REQUESTED:
                console.log("Permission to use the camera has not been requested yet");
                break;
            case cordova.plugins.diagnostic.permissionStatus.DENIED:
                console.log("Permission denied to use the camera - ask again?");
                break;
            case cordova.plugins.diagnostic.permissionStatus.DENIED_ALWAYS:
                console.log("Permission permanently denied to use the camera - guess we won't be using it then!");
                break;
        }
    }, function(error){
        console.error("The following error occurred: "+error);
    }, cordova.plugins.diagnostic.permission.CAMERA);

### getPermissionsAuthorizationStatus()

Returns the current authorisation status for multiple permissions.

Note: this is intended for Android 6 / API 23 and above. Calling on Android 5 / API 22 and below will always return GRANTED status as permissions are already granted at installation time.

#### Parameters

- {Function} successCallback - function to call on successful retrieval of status.
This callback function is passed a single object parameter which defines a key/value map, where the key is the requested [runtime permission](#dangerous-runtime-permissions), and the value is the current [permission status](#permissionstatus-constants).
- {Function} errorCallback - function to call on failure to retrieve authorisation status.
This callback function is passed a single string parameter containing the error message.
- {Array} permissions - list of permissions to request authorisation statuses for, defined as [runtime permission constants](#dangerous-runtime-permissions).

#### Example usage

    cordova.plugins.diagnostic.getPermissionsAuthorizationStatus(function(statuses){
        for (var permission in statuses){
            switch(statuses[permission]){
                case cordova.plugins.diagnostic.permissionStatus.GRANTED:
                    console.log("Permission granted to use "+permission);
                    break;
                case cordova.plugins.diagnostic.permissionStatus.NOT_REQUESTED:
                    console.log("Permission to use "+permission+" has not been requested yet");
                    break;
                case cordova.plugins.diagnostic.permissionStatus.DENIED:
                    console.log("Permission denied to use "+permission+" - ask again?");
                    break;
                case cordova.plugins.diagnostic.permissionStatus.DENIED_ALWAYS:
                    console.log("Permission permanently denied to use "+permission+" - guess we won't be using it then!");
                    break;
            }
        }
    }, function(error){
        console.error("The following error occurred: "+error);
    },[
        cordova.plugins.diagnostic.permission.ACCESS_FINE_LOCATION,
        cordova.plugins.diagnostic.permission.ACCESS_COARSE_LOCATION
    ]);

### requestRuntimePermission()

Requests app to be granted authorisation for a runtime permission.

Note: this is intended for Android 6 / API 23 and above. Calling on Android 5 / API 22 and below will have no effect as the permissions are already granted at installation time.

#### Parameters

- {Function} successCallback - function to call on successful request for runtime permission.
This callback function is passed a single string parameter which defines the resulting [permission status](#permissionstatus-constants)
- {Function} errorCallback - function to call on failure to request authorisation.
This callback function is passed a single string parameter containing the error message.
- {String} permission - permission to request authorisation for, defined as a [runtime permission constant](#dangerous-runtime-permissions).

#### Example usage

    cordova.plugins.diagnostic.requestRuntimePermission(function(status){
        switch(status){
            case cordova.plugins.diagnostic.permissionStatus.GRANTED:
                console.log("Permission granted to use the camera");
                break;
            case cordova.plugins.diagnostic.permissionStatus.NOT_REQUESTED:
                console.log("Permission to use the camera has not been requested yet");
                break;
            case cordova.plugins.diagnostic.permissionStatus.DENIED:
                console.log("Permission denied to use the camera - ask again?");
                break;
            case cordova.plugins.diagnostic.permissionStatus.DENIED_ALWAYS:
                console.log("Permission permanently denied to use the camera - guess we won't be using it then!");
                break;
        }
    }, function(error){
        console.error("The following error occurred: "+error);
    }, cordova.plugins.diagnostic.permission.CAMERA);


### requestRuntimePermissions()

Requests app to be granted authorisation for multiple runtime permissions.

Note: this is intended for Android 6 / API 23 and above. Calling on Android 5 / API 22 and below will always return GRANTED status as permissions are already granted at installation time.

#### Parameters

- {Function} successCallback - function to call on successful request for runtime permissions.
This callback function is passed a single object parameter which defines a key/value map, where the key is the [runtime permission](#dangerous-runtime-permissions) to request, and the value is the current [permission status](#permissionstatus-constants).
- {Function} errorCallback - function to call on failure to request authorisation.
This callback function is passed a single string parameter containing the error message.
- {Array} permissions - list of permissions to request authorisation for, defined as [runtime permission constants](#dangerous-runtime-permissions).

#### Example usage

    cordova.plugins.diagnostic.requestRuntimePermissions(function(statuses){
        for (var permission in statuses){
            switch(statuses[permission]){
                case cordova.plugins.diagnostic.permissionStatus.GRANTED:
                    console.log("Permission granted to use "+permission);
                    break;
                case cordova.plugins.diagnostic.permissionStatus.NOT_REQUESTED:
                    console.log("Permission to use "+permission+" has not been requested yet");
                    break;
                case cordova.plugins.diagnostic.permissionStatus.DENIED:
                    console.log("Permission denied to use "+permission+" - ask again?");
                    break;
                case cordova.plugins.diagnostic.permissionStatus.DENIED_ALWAYS:
                    console.log("Permission permanently denied to use "+permission+" - guess we won't be using it then!");
                    break;
            }
        }
    }, function(error){
        console.error("The following error occurred: "+error);
    },[
        cordova.plugins.diagnostic.permission.ACCESS_FINE_LOCATION,
        cordova.plugins.diagnostic.permission.ACCESS_COARSE_LOCATION
    ]);

### isRequestingPermission()

Indicates if the plugin is currently requesting a runtime permission via the native API.
Note that only one request can be made concurrently because the native API cannot handle concurrent requests,
so the plugin will invoke the error callback if attempting to make more than one simultaneous request.
Multiple permission requests should be grouped into a single call since the native API is setup to handle batch requests of multiple permission groups.

    var isRequesting = cordova.plugins.diagnostic.isRequestingPermission();

#### Example usage

    var isRequesting = cordova.plugins.diagnostic.isRequestingPermission();
    if(!isRequesting){
        requestSomePermissions();
    }else{
        cordova.plugins.diagnostic.registerPermissionRequestCompleteHandler(function(statuses){
            cordova.plugins.diagnostic.registerPermissionRequestCompleteHandler(null); // de-register handler after single call
            requestSomePermissions();
        });
    }

### registerPermissionRequestCompleteHandler()

Registers a function to be called when a runtime permission request has completed.
Pass in a falsey value to de-register the currently registered function.

    cordova.plugins.diagnostic.registerPermissionRequestCompleteHandler(successCallback);

#### Parameters

- {Function} successCallback -  The callback which will be called when a runtime permission request has completed.
This callback function is passed a single object parameter which defines a key/value map, where the key is the permission requested (defined as a value in cordova.plugins.diagnostic.permission) and the value is the resulting authorisation status of that permission as a value in cordova.plugins.diagnostic.permissionStatus.

#### Example usage

    function onPermissionRequestComplete(statuses){
        console.info("Permission request complete");
        for (var permission in statuses){
            switch(statuses[permission]){
                case cordova.plugins.diagnostic.permissionStatus.GRANTED:
                    console.log("Permission granted to use "+permission);
                    break;
                case cordova.plugins.diagnostic.permissionStatus.NOT_REQUESTED:
                    console.log("Permission to use "+permission+" has not been requested yet");
                    break;
                case cordova.plugins.diagnostic.permissionStatus.DENIED:
                    console.log("Permission denied to use "+permission);
                    break;
                case cordova.plugins.diagnostic.permissionStatus.DENIED_ALWAYS:
                    console.log("Permission permanently denied to use "+permission);
                    break;
            }
        }
        cordova.plugins.diagnostic.registerPermissionRequestCompleteHandler(null); // de-register handler
    }
    cordova.plugins.diagnostic.registerPermissionRequestCompleteHandler(onPermissionRequestComplete);

### isBluetoothEnabled()

Checks if the device setting for Bluetooth is switched on.

On Android this requires permission `<uses-permission android:name="android.permission.BLUETOOTH" />`

    cordova.plugins.diagnostic.isBluetoothAvailable(successCallback, errorCallback);

#### Parameters

- {Function} successCallback -  The callback which will be called when operation is successful.
This callback function is passed a single boolean parameter which is TRUE if Bluetooth is switched on.
- {Function} errorCallback -  The callback which will be called when operation encounters an error.
This callback function is passed a single string parameter containing the error message.


#### Example usage

    cordova.plugins.diagnostic.isBluetoothEnabled(function(enabled){
        console.log("Bluetooth is " + (enabled ? "enabled" : "disabled"));
    }, function(error){
        console.error("The following error occurred: "+error);
    });

### hasBluetoothSupport()

Checks if the device has Bluetooth capabilities.
See http://developer.android.com/guide/topics/connectivity/bluetooth.html.

    cordova.plugins.diagnostic.hasBluetoothLESupport(successCallback, errorCallback);

#### Parameters

- {Function} successCallback -  The callback which will be called when the operation is successful.
This callback function is passed a single boolean parameter which is TRUE if device has Bluetooth capabilities.
- {Function} errorCallback -  The callback which will be called when the operation encounters an error.
This callback function is passed a single string parameter containing the error message.

#### Example usage

    cordova.plugins.diagnostic.hasBluetoothSupport(function(supported){
        console.log("Bluetooth is " + (supported ? "supported" : "unsupported"));
    }, function(error){
        console.error("The following error occurred: "+error);
    });

### hasBluetoothLESupport()

Checks if the device has Bluetooth Low Energy (LE) capabilities.
See http://developer.android.com/guide/topics/connectivity/bluetooth-le.html.

    cordova.plugins.diagnostic.hasBluetoothLESupport(successCallback, errorCallback);

#### Parameters

- {Function} successCallback -  The callback which will be called when the operation is successful.
This callback function is passed a single boolean parameter which is TRUE if device has Bluetooth LE capabilities.
- {Function} errorCallback -  The callback which will be called when the operation encounters an error.
This callback function is passed a single string parameter containing the error message.

#### Example usage

    cordova.plugins.diagnostic.hasBluetoothLESupport(function(supported){
        console.log("Bluetooth LE is " + (supported ? "supported" : "unsupported"));
    }, function(error){
        console.error("The following error occurred: "+error);
    });

### hasBluetoothLEPeripheralSupport()
Checks if the device supports Bluetooth Low Energy (LE) Peripheral mode.
See http://developer.android.com/guide/topics/connectivity/bluetooth-le.html#roles.

#### Parameters

- {Function} successCallback -  The callback which will be called when the operation is successful.
This callback function is passed a single boolean parameter which is TRUE if device supports Bluetooth LE Peripheral mode.
- {Function} errorCallback -  The callback which will be called when the operation encounters an error.
This callback function is passed a single string parameter containing the error message.

#### Example usage

    cordova.plugins.diagnostic.hasBluetoothLEPeripheralSupport(function(supported){
        console.log("Bluetooth LE Peripheral Mode is " + (supported ? "supported" : "unsupported"));
    }, function(error){
        console.error("The following error occurred: "+error);
    });

### isExternalStorageAuthorized()

Checks if the application is authorized to use external storage.

Notes for Android:
- This is intended for Android 6 / API 23 and above. Calling on Android 5 / API 22 and below will always return TRUE as permissions are already granted at installation time.
- This checks for `READ_EXTERNAL_STORAGE` `CAMERA` run-time permission.

    `cordova.plugins.diagnostic.isExternalStorageAuthorized(successCallback, errorCallback);`

#### Parameters

- {Function} successCallback -  The callback which will be called when operation is successful.
This callback function is passed a single boolean parameter which is TRUE if external storage is authorized for use.
- {Function} errorCallback -  The callback which will be called when operation encounters an error.
This callback function is passed a single string parameter containing the error message.


#### Example usage

    cordova.plugins.diagnostic.isExternalStorageAuthorized(function(authorized){
        console.log("App is " + (authorized ? "authorized" : "denied") + " access to the external storage");
    }, function(error){
        console.error("The following error occurred: "+error);
    });

### getExternalStorageAuthorizationStatus()

Returns the external storage authorization status for the application.

Notes for Android:
- This is intended for Android 6 / API 23 and above. Calling on Android 5 / API 22 and below will always return GRANTED status as permissions are already granted at installation time.
- This checks for `READ_EXTERNAL_STORAGE` run-time permission.

    `cordova.plugins.diagnostic.getExternalStorageAuthorizationStatus(successCallback, errorCallback);`

#### Parameters

- {Function} successCallback -  The callback which will be called when operation is successful.
This callback function is passed a single string parameter which indicates the authorization status as a [permissionStatus constant](#permissionstatus-constants).
- {Function} errorCallback -  The callback which will be called when operation encounters an error.
This callback function is passed a single string parameter containing the error message.

#### Example usage

    cordova.plugins.diagnostic.getExternalStorageAuthorizationStatus(function(status){
        if(status === cordova.plugins.diagnostic.permissionStatus.GRANTED){
            console.log("External storage use is authorized");
        }
    }, function(error){
        console.error("The following error occurred: "+error);
    });

### requestExternalStorageAuthorization()

Requests external storage authorization for the application.

- This is intended for Android 6 / API 23 and above. Calling on Android 5 / API 22 and below will have no effect as the permissions are already granted at installation time.
- This requests permission for `READ_EXTERNAL_STORAGE` run-time permission which must be added to `AndroidManifest.xml`.

    `cordova.plugins.diagnostic.requestExternalStorageAuthorization(successCallback, errorCallback);`

#### Parameters

- {Function} successCallback -  The callback which will be called when operation is successful.
This callback function is passed a single string parameter indicating whether access to the external storage was granted or denied:
`cordova.plugins.diagnostic.permissionStatus.GRANTED` or `cordova.plugins.diagnostic.permissionStatus.DENIED`
- {Function} errorCallback -  The callback which will be called when operation encounters an error.
This callback function is passed a single string parameter containing the error message.

#### Example usage

    cordova.plugins.diagnostic.requestExternalStorageAuthorization(function(status){
        console.log("Authorization request for external storage use was " + (status == cordova.plugins.diagnostic.permissionStatus.GRANTED ? "granted" : "denied"));
    }, function(error){
        console.error(error);
    });

### getExternalSdCardDetails()

Returns details of external SD card(s): absolute path, is writable, free space.

The intention of this method is to return the location and details of *removable* _external_ SD cards.
This differs from the "external directories" returned by [cordova-plugin-file](https://github.com/apache/cordova-plugin-file) which return mount points relating to non-removable (internal) storage.

For example, on a Samsung Galaxy S4 running Android 7.1.1:

 - `cordova.file.externalRootDirectory` returns `file:///storage/emulated/0/`
 - `cordova.file.externalApplicationStorageDirectory` returns `file:///storage/emulated/0/Android/data/cordova.plugins.diagnostic.example/`

 which are on non-removable internal storage.

 Whereas this method returns:

    ```
    [{
        "path": "/storage/4975-1401/Android/data/cordova.plugins.diagnostic.example/files",
        "filePath": "file:///storage/4975-1401/Android/data/cordova.plugins.diagnostic.example/files",
        "canWrite": true,
        "freeSpace": 16254009344,
        "type": "application"
    }, {
        "path": "/storage/4975-1401",
        "filePath": "file:///storage/4975-1401",
        "canWrite": false,
        "freeSpace": 16254009344,
        "type": "root"
    }]
    ```

 which are on external removable storage.

- Requires permission for `READ_EXTERNAL_STORAGE` run-time permission which must be added to `AndroidManifest.xml`.

    `cordova.plugins.diagnostic.getExternalSdCardDetails(successCallback, errorCallback);`

#### Parameters

- {Function} successCallback -  function to call on successful request for external SD card details.
This callback function is passed a single argument which is an array consisting of an entry for each external storage location found.
Each array entry is an object with the following keys:
    - {String} path - absolute path to the storage location
    - {String} filePath - absolute path prefixed with file protocol for use with cordova-plugin-file
    - {Boolean} canWrite - true if the location is writable
    - {Integer} freeSpace - number of bytes of free space on the device on which the storage locaiton is mounted.
    - {String} type - indicates the type of storage location: either "application" if the path is an Android application sandbox path or "root" if the path is the device root.
- {Function} errorCallback -  The callback which will be called when operation encounters an error.
This callback function is passed a single string parameter containing the error message.

#### Example usage

    cordova.plugins.diagnostic.getExternalSdCardDetails(function(details){
        details.forEach(function(detail){
            if(detail.canWrite && details.freeSpace > 100000){
                cordova.file.externalSdCardDirectory = detail.filePath;
                // Then: write file to external SD card
            }
        });
    }, function(error){
        console.error(error);
    });

### switchToWirelessSettings()

Switches to the wireless settings page in the Settings app.
Allows configuration of wireless controls such as Wi-Fi, Bluetooth and Mobile networks.

    cordova.plugins.diagnostic.switchToWirelessSettings();

### switchToNFCSettings()

Displays NFC settings to allow user to enable NFC.

On some versions of Android, this may open the same page as `switchToWirelessSettings()` if the NFC switch is on the Wireless settings page.

    cordova.plugins.diagnostic.switchToNFCSettings();

### isNFCPresent()

Checks if NFC hardware is present on device.

    cordova.plugins.diagnostic.isNFCPresent(successCallback, errorCallback);

#### Parameters

- {Function} successCallback -  The callback which will be called when operation is successful.
This callback function is passed a single boolean parameter which is TRUE if NFC is present
- {Function} errorCallback -  The callback which will be called when operation encounters an error.
This callback function is passed a single string parameter containing the error message.


#### Example usage

    cordova.plugins.diagnostic.isNFCPresent(function(present){
        console.log("NFC hardware is " + (present ? "present" : "absent"));
    }, function(error){
        console.error("The following error occurred: "+error);
    });
    
### isNFCEnabled()

Checks if the device setting for NFC is switched on.

Note: this operation **does not** require NFC permission in the manifest.

    cordova.plugins.diagnostic.isNFCAvailable(successCallback, errorCallback);

#### Parameters

- {Function} successCallback -  The callback which will be called when operation is successful.
This callback function is passed a single boolean parameter which is TRUE if NFC is switched on.
- {Function} errorCallback -  The callback which will be called when operation encounters an error.
This callback function is passed a single string parameter containing the error message.


#### Example usage

    cordova.plugins.diagnostic.isNFCEnabled(function(enabled){
        console.log("NFC is " + (enabled ? "enabled" : "disabled"));
    }, function(error){
        console.error("The following error occurred: "+error);
    });

### isNFCAvailable()

Checks if NFC is available to the app.
Returns true if the device has NFC capabilities AND if NFC setting is switched on.

Note: this operation **does not** require NFC permission in the manifest.

    cordova.plugins.diagnostic.isNFCAvailable(successCallback, errorCallback);

#### Parameters

- {Function} successCallback -  The callback which will be called when operation is successful.
This callback function is passed a single boolean parameter which is TRUE if NFC is available.
- {Function} errorCallback -  The callback which will be called when operation encounters an error.
This callback function is passed a single string parameter containing the error message.


#### Example usage

    cordova.plugins.diagnostic.isNFCAvailable(function(available){
        console.log("NFC is " + (available ? "available" : "not available"));
    }, function(error){
        console.error("The following error occurred: "+error);
    });

### registerNFCStateChangeHandler()

Registers a function to be called when a change in NFC state occurs.
Pass in a falsey value to de-register the currently registered function.

This is triggered when NFC state changes so is useful for detecting changes made in quick settings which would not result in pause/resume events being fired.

    cordova.plugins.diagnostic.registerNFCStateChangeHandler(successCallback);

#### Parameters

- {Function} successCallback - function call when a change in NFC state occurs.
The function is passed a single string parameter defined as a constant in `cordova.plugins.diagnostic.NFCState`.

#### Example usage

    cordova.plugins.diagnostic.registerNFCStateChangeHandler(function(state){
        console.log("NFC state changed to: " + state);
    });

### NFCState constants

Defines constants for the various NFC power states.

    cordova.plugins.diagnostic.NFCState

#### Values

- `UNKNOWN` - Bluetooth hardware state is unknown or unavailable
- `POWERED_OFF` - Bluetooth hardware is switched off
- `POWERED_ON` - Bluetooth hardware is switched on and available for use
- `POWERING_OFF`- Bluetooth hardware is currently switching off
- `POWERING_ON`- Bluetooth hardware is currently switching on

#### Example

    cordova.plugins.diagnostic.registerNFCStateChangeHandler(function(state){
        switch(state){
            case cordova.plugins.diagnostic.NFCState.UNKNOWN:
                console.log("NFC state is unknown");
                break;
            case cordova.plugins.diagnostic.NFCState.POWERED_OFF:
                console.log("NFC is powered off");
                break;
            case cordova.plugins.diagnostic.NFCState.POWERED_ON:
                console.log("NFC is powered on");
                break;
            case cordova.plugins.diagnostic.NFCState.POWERING_OFF:
                console.log("NFC is powering off");
                break;
            case cordova.plugins.diagnostic.NFCState.POWERING_ON:
                console.log("NFC is powering on);
                break;
        }
    },function(error){
        console.error("The following error occurred: "+error);
    });

## iOS only


### isCameraRollAuthorized()

Checks if the application is authorized to use the Camera Roll in Photos app.

    cordova.plugins.diagnostic.isCameraRollAuthorized(successCallback, errorCallback);

#### Parameters

- {Function} successCallback -  The callback which will be called when operation is successful.
This callback function is passed a single boolean parameter which is TRUE if access to Camera Roll is authorized.
- {Function} errorCallback -  The callback which will be called when operation encounters an error.
This callback function is passed a single string parameter containing the error message.


#### Example usage

    cordova.plugins.diagnostic.isCameraRollAuthorized(function(authorized){
        console.log("App is " + (authorized ? "authorized" : "denied") + " access to the camera roll");
    }, function(error){
        console.error("The following error occurred: "+error);
    });

### getCameraRollAuthorizationStatus()

Returns the authorization status for the application to use the Camera Roll in Photos app.

    cordova.plugins.diagnostic.getCameraRollAuthorizationStatus(successCallback, errorCallback);

#### Parameters

- {Function} successCallback -  The callback which will be called when operation is successful.
This callback function is passed a single string parameter which indicates the authorization status as a constant in `cordova.plugins.diagnostic.permissionStatus`.
- {Function} errorCallback -  The callback which will be called when operation encounters an error.
This callback function is passed a single string parameter containing the error message.

#### Example usage

    cordova.plugins.diagnostic.getCameraRollAuthorizationStatus(function(status){
        switch(status){
            case cordova.plugins.diagnostic.permissionStatus.NOT_REQUESTED:
                console.log("Permission not requested");
                break;
            case cordova.plugins.diagnostic.permissionStatus.DENIED:
                console.log("Permission denied");
                break;
            case cordova.plugins.diagnostic.permissionStatus.GRANTED:
                console.log("Permission granted");
                break;
        }
    }, function(error){
        console.error("The following error occurred: "+error);
    });

### requestCameraRollAuthorization()

Requests camera roll authorization for the application.
Should only be called if authorization status is NOT_REQUESTED. Calling it when in any other state will have no effect.
When calling this function, the message contained in the `NSPhotoLibraryUsageDescription` .plist key is displayed to the user;
this plugin provides a default message, but you should override this with your specific reason for requesting access - see the [iOS usage description messages](#ios-usage-description-messages) section for how to customise it.

    cordova.plugins.diagnostic.requestCameraRollAuthorization(successCallback, errorCallback);

#### Parameters

- {Function} successCallback -  The callback which will be called when operation is successful.
This callback function is passed a single string parameter indicating the new authorization status:
`cordova.plugins.diagnostic.permissionStatus.GRANTED` or `cordova.plugins.diagnostic.permissionStatus.DENIED`
- {Function} errorCallback -  The callback which will be called when operation encounters an error.
This callback function is passed a single string parameter containing the error message.

#### Example usage

    cordova.plugins.diagnostic.requestCameraRollAuthorization(function(status){
        console.log("Authorization request for camera roll was " + (status == cordova.plugins.diagnostic.permissionStatus.GRANTED ? "granted" : "denied"));
    }, function(error){
        console.error(error);
    });


### isRemoteNotificationsEnabled()

Checks if remote (push) notifications are enabled.

On iOS 8+, returns true if app is registered for remote notifications **AND** "Allow Notifications" switch is ON **AND** alert style is not set to "None" (i.e. "Banners" or "Alerts").

On iOS <=7, returns true if app is registered for remote notifications **AND** alert style is not set to "None" (i.e. "Banners" or "Alerts") - same as [isRegisteredForRemoteNotifications()](#isregisteredforremotenotifications).

    cordova.plugins.diagnostic.isRemoteNotificationsEnabled(successCallback, errorCallback);

#### Parameters
- {Function} successCallback - The callback which will be called when operation is successful.
This callback function is passed a single boolean parameter which is TRUE if remote (push) notifications are enabled.
- {Function} errorCallback - The callback which will be called when an error occurs. This callback function is passed a single string parameter containing the error message.

#### Example usage

    cordova.plugins.diagnostic.isRemoteNotificationsEnabled(function(enabled){
        console.log("Remote notifications are " + (enabled ? "enabled" : "disabled"));
    }, function(error){
        console.error("The following error occurred: "+error);
    });

### isRegisteredForRemoteNotifications()

Indicates if the app is registered for remote (push) notifications on the device.

On iOS 8+, returns true if the app is registered for remote notifications and received its device token, or false if registration has not occurred, has failed, or has been denied by the user.
Note that user preferences for notifications in the Settings app will not affect this.

On iOS <=7, returns true if app is registered for remote notifications AND alert style is not set to "None" (i.e. "Banners" or "Alerts") - same as [isRemoteNotificationsEnabled()](#isremotenotificationsenabled).

    cordova.plugins.diagnostic.isRegisteredForRemoteNotifications(successCallback, errorCallback);

#### Parameters
- {Function} successCallback - The callback which will be called when operation is successful.
This callback function is passed a single boolean parameter which is TRUE if the device is registered for remote (push) notifications.
- {Function} errorCallback - The callback which will be called when an error occurs. This callback function is passed a single string parameter containing the error message.

#### Example usage

    cordova.plugins.diagnostic.isRegisteredForRemoteNotifications(function(registered){
        console.log("Device " + (registered ? "is" : "isn't") + " registered for remote notifications");
    }, function(error){
        console.error("The following error occurred: "+error);
    });

### getRemoteNotificationTypes()

Indicates the current setting of notification types for the app in the Settings app.

Note: on iOS 8+, if "Allow Notifications" switch is OFF, all types will be returned as disabled.

    cordova.plugins.diagnostic.getRemoteNotificationTypes(successCallback, errorCallback);

#### Parameters
- {Function} successCallback - The callback which will be called when operation is successful.
This callback function is passed a single object parameter where the key is the notification type and the value is a boolean indicating whether it's enabled:
     * "alert" => alert style is not set to "None" (i.e. "Banners" or "Alerts");
     * "badge" => "Badge App Icon" switch is ON;
     * "sound" => "Sounds"/"Alert Sound" switch is ON.
- {Function} errorCallback - The callback which will be called when an error occurs. This callback function is passed a single string parameter containing the error message.

#### Example usage

    cordova.plugins.diagnostic.getRemoteNotificationTypes(function(types){
        for(var type in types){
            console.log(type + " is " + (types[type] ? "enabled" : "disabled"));
        }
    }, function(error){
        console.error("The following error occurred: "+error);
    });

### isRemindersAuthorized()

Checks if the application is authorized to use reminders.

    cordova.plugins.diagnostic.isRemindersAuthorized(successCallback, errorCallback);

#### Parameters

- {Function} successCallback -  The callback which will be called when operation is successful.
This callback function is passed a single boolean parameter which is TRUE if reminders access is authorized for use.
- {Function} errorCallback -  The callback which will be called when operation encounters an error.
This callback function is passed a single string parameter containing the error message.


#### Example usage

    cordova.plugins.diagnostic.isRemindersAuthorized(function(authorized){
        console.log("App is " + (authorized ? "authorized" : "denied") + " access to reminders");
    }, function(error){
        console.error("The following error occurred: "+error);
    });

### getRemindersAuthorizationStatus()

Returns the reminders authorization status for the application.

    cordova.plugins.diagnostic.getRemindersAuthorizationStatus(successCallback, errorCallback);

#### Parameters

- {Function} successCallback -  The callback which will be called when operation is successful.
This callback function is passed a single string parameter which indicates the authorization status as a [permissionStatus constant](#permissionstatus-constants).
- {Function} errorCallback -  The callback which will be called when operation encounters an error.
This callback function is passed a single string parameter containing the error message.

#### Example usage

    cordova.plugins.diagnostic.getRemindersAuthorizationStatus(function(status){
        if(status === cordova.plugins.diagnostic.permissionStatus.GRANTED){
            console.log("Reminders authorization allowed");
        }
    }, function(error){
        console.error("The following error occurred: "+error);
    });


### requestRemindersAuthorization()

Requests reminders authorization for the application.
Should only be called if authorization status is NOT_DETERMINED. Calling it when in any other state will have no effect and just return the current authorization status.
When calling this function, the message contained in the `NSRemindersUsageDescription` .plist key is displayed to the user;
this plugin provides a default message, but you should override this with your specific reason for requesting access - see the [iOS usage description messages](#ios-usage-description-messages) section for how to customise it.

    cordova.plugins.diagnostic.requestRemindersAuthorization(successCallback, errorCallback);

#### Parameters
- {Function} successCallback - The callback which will be called when operation is successful.
This callback function is passed a single string parameter indicating whether access to calendar was granted or denied:
`cordova.plugins.diagnostic.permissionStatus.GRANTED` or `cordova.plugins.diagnostic.permissionStatus.DENIED`
- {Function} errorCallback - The callback which will be called when an error occurs. This callback function is passed a single string parameter containing the error message.

#### Example usage

    cordova.plugins.diagnostic.requestRemindersAuthorization(function(status){
        if(status === cordova.plugins.diagnostic.permissionStatus.GRANTED){
            console.log("Reminders authorization allowed");
        }
    }, function(error){
        console.error(error);
    });

### isBackgroundRefreshAuthorized()

Checks if the application is authorized for background refresh.

    cordova.plugins.diagnostic.isBackgroundRefreshAuthorized(successCallback, errorCallback);

#### Parameters

- {Function} successCallback -  The callback which will be called when operation is successful.
This callback function is passed a single boolean parameter which is TRUE if background refresh access is authorized for use.
- {Function} errorCallback -  The callback which will be called when operation encounters an error.
This callback function is passed a single string parameter containing the error message.


#### Example usage

    cordova.plugins.diagnostic.isBackgroundRefreshAuthorized(function(authorized){
        console.log("App is " + (authorized ? "authorized" : "not authorized") + " to perform background refresh");
    }, function(error){
        console.error("The following error occurred: "+error);
    });

### getBackgroundRefreshStatus()

Returns the background refresh authorization status for the application.

    cordova.plugins.diagnostic.getBackgroundRefreshStatus(successCallback, errorCallback);

#### Parameters

- {Function} successCallback -  The callback which will be called when operation is successful.
This callback function is passed a single string parameter which indicates the authorization status as a [permissionStatus constant](#permissionstatus-constants).
- {Function} errorCallback -  The callback which will be called when operation encounters an error.
This callback function is passed a single string parameter containing the error message.

#### Example usage

    cordova.plugins.diagnostic.getBackgroundRefreshStatus(function(status){
        if(status === cordova.plugins.diagnostic.permissionStatus.GRANTED){
            console.log("Background refresh is allowed");
        }
    }, function(error){
        console.error("The following error occurred: "+error);
    });

### requestBluetoothAuthorization()

Requests Bluetooth authorization for the application.
- The outcome of the authorization request can be determined by registering a handler using [`registerBluetoothStateChangeHandler()`](#registerbluetoothstatechangehandler).
- When calling this function, the message contained in the `NSBluetoothPeripheralUsageDescription` .plist key is displayed to the user;
this plugin provides a default message, but you should override this with your specific reason for requesting access - see the [iOS usage description messages](#ios-usage-description-messages) section for how to customise it.

    cordova.plugins.diagnostic.requestBluetoothAuthorization(successCallback, errorCallback);

#### Parameters

- {Function} successCallback -  The callback which will be called when operation is successful.
This callback function is not passed any parameters.
- {Function} errorCallback -  The callback which will be called when operation encounters an error.
This callback function is passed a single string parameter containing the error message.

#### Example usage

    cordova.plugins.diagnostic.requestBluetoothAuthorization(function(){
        console.log("Bluetooth authorization was requested."));
    }, function(error){
        console.error(error);
    });

### isMotionAvailable()

Checks if motion tracking is available on the current device.

    cordova.plugins.diagnostic.isMotionAvailable(successCallback, errorCallback);

#### Parameters

- {Function} successCallback -  The callback which will be called when operation is successful.
This callback function is passed a single boolean parameter which is TRUE if motion tracking is available on the current device.
- {Function} errorCallback -  The callback which will be called when operation encounters an error.
This callback function is passed a single string parameter containing the error message.


#### Example usage

    cordova.plugins.diagnostic.isMotionAvailable(function(available){
        console.log("Motion tracking is " + (available ? "available" : "not available") + " on this device");
    }, function(error){
        console.error("The following error occurred: "+error);
    });

### isMotionRequestOutcomeAvailable()

Checks if it's possible to determine the outcome of a motion authorization request on the current device.
There's no direct way to determine if authorization was granted or denied, so the Pedometer API must be used to indirectly determine this:
therefore, if the device supports motion tracking but not Pedometer Event Tracking, the outcome of requesting motion detection cannot be determined.

    cordova.plugins.diagnostic.isMotionRequestOutcomeAvailable(successCallback, errorCallback);

#### Parameters

- {Function} successCallback -  The callback which will be called when operation is successful.
This callback function is passed a single boolean parameter which is TRUE if it's possible to determine the outcome of a motion authorization request on the current device.
- {Function} errorCallback -  The callback which will be called when operation encounters an error.
This callback function is passed a single string parameter containing the error message.


#### Example usage

    cordova.plugins.diagnostic.isMotionRequestOutcomeAvailable(function(available){
        console.log("Motion tracking authorization request outcome is " + (available ? "available" : "not available") + " on this device");
    }, function(error){
        console.error("The following error occurred: "+error);
    });

### requestAndCheckMotionAuthorization()

Requests and checks motion authorization for the application:
there is no way to independently request only or check only, so both must be done in one operation.

The native dialog asking user's consent can only be invoked once after the app is installed by calling this function.
Once the user has either allowed or denied access, this function will only return the current authorization status:
it is not possible to re-invoke the dialog if the user denied permission in the native dialog -
in this case, you will have to instruct the user how to change motion authorization manually via the Settings app.

When calling this function, the message contained in the `NSMotionUsageDescription` .plist key is displayed to the user;
this plugin provides a default message, but you should override this with your specific reason for requesting access - see the [iOS usage description messages](#ios-usage-description-messages) section for how to customise it.

If the device doesn't support motion detection, the error callback will be invoked.

There's no direct way to determine if authorization was granted or denied, so the Pedometer API must be used to indirectly determine this:
therefore, if the device supports motion tracking but not Pedometer Event Tracking, the outcome of requesting motion detection cannot be determined.

    cordova.plugins.diagnostic.requestAndCheckMotionAuthorization(successCallback, errorCallback);

#### Parameters
- {Function} successCallback - The callback which will be called when operation is successful.
This callback function is passed a single string parameter indicating the result:
    - `cordova.plugins.diagnostic.permissionStatus.GRANTED` - user granted motion authorization.
    - `cordova.plugins.diagnostic.permissionStatus.DENIED` - user denied motion authorization.
    - `cordova.plugins.diagnostic.permissionStatus.RESTRICTED` - user cannot grant motion authorization.
    - `cordova.plugins.diagnostic.permissionStatus.NOT_DETERMINED` - device does not support Pedometer Event Tracking, so authorization outcome cannot be determined.
- {Function} errorCallback - The callback which will be called when an error occurs. This callback function is passed a single string parameter containing the error message.

#### Example usage

    cordova.plugins.diagnostic.requestAndCheckMotionAuthorization(function(status){
        if(status === cordova.plugins.diagnostic.permissionStatus.GRANTED){
            console.log("Motion authorization allowed");
        }
    }, function(error){
        console.error(error);
    });


# Platform Notes

## Android

### Android permissions

Some of functions offered by this plugin require specific permissions to be set in the AndroidManifest.xml. Where additional permissions are needed, they are listed alongside the function that requires them.

These permissions will not be set by this plugin, to avoid asking for unnecessary permissions in your app, in the case that you do not use a particular part of the plugin.
Instead, you can add these permissions as necessary, depending what functions in the plugin you decide to use.

You can add these permissions either by manually editing the AndroidManifest.xml in `/platforms/android/`, or define them in the config.xml and apply them using the [cordova-custom-config](https://github.com/dpa99c/cordova-custom-config) plugin, for example:

    <platform name="android">
        <plugin name="cordova-custom-config" version="*"/>
        <config-file target="AndroidManifest.xml" parent="/*">
            <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
            <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />
        </config-file>
    </platform>

#### Android runtime permissions

Android 6 / API 23 introduces the concept of [runtime permissions](http://developer.android.com/training/permissions/requesting.html). Similar to iOS, certain "dangerous" permissions must be requested at runtime __in addition__ to being listed in the Android manifest.

Runtime permissions only apply if the device/emulator the app is running on has Android 6.0 or above. If the app is running on Android 5.x or below, runtime permissions do not apply - all permissions are granted at installation time.

This plugin supports [checking](#getpermissionauthorizationstatus) and [requesting](#requestruntimepermission) of Android runtime permissions.

##### "Dangerous" runtime permissions

The plugin defines the [full list of dangersous permissions available in API 23](http://developer.android.com/guide/topics/security/permissions.html#perm-groups) as a list of constants available via the `cordova.plugins.diagnostic.runtimePermission` object. The following permissions are available:

- `cordova.plugins.diagnostic.permission.READ_CALENDAR`
- `cordova.plugins.diagnostic.permission.WRITE_CALENDAR`
- `cordova.plugins.diagnostic.permission.CAMERA`
- `cordova.plugins.diagnostic.permission.READ_CONTACTS`
- `cordova.plugins.diagnostic.permission.WRITE_CONTACTS`
- `cordova.plugins.diagnostic.permission.GET_ACCOUNTS`
- `cordova.plugins.diagnostic.permission.ACCESS_FINE_LOCATION`
- `cordova.plugins.diagnostic.permission.ACCESS_COARSE_LOCATION`
- `cordova.plugins.diagnostic.permission.RECORD_AUDIO`
- `cordova.plugins.diagnostic.permission.READ_PHONE_STATE`
- `cordova.plugins.diagnostic.permission.CALL_PHONE`
- `cordova.plugins.diagnostic.permission.ADD_VOICEMAIL`
- `cordova.plugins.diagnostic.permission.USE_SIP`
- `cordova.plugins.diagnostic.permission.PROCESS_OUTGOING_CALLS`
- `cordova.plugins.diagnostic.permission.READ_CALL_LOG`
- `cordova.plugins.diagnostic.permission.WRITE_CALL_LOG`
- `cordova.plugins.diagnostic.permission.SEND_SMS`
- `cordova.plugins.diagnostic.permission.RECEIVE_SMS`
- `cordova.plugins.diagnostic.permission.READ_SMS`
- `cordova.plugins.diagnostic.permission.RECEIVE_WAP_PUSH`
- `cordova.plugins.diagnostic.permission.RECEIVE_MMS`
- `cordova.plugins.diagnostic.permission.WRITE_EXTERNAL_STORAGE`
- `cordova.plugins.diagnostic.permission.READ_EXTERNAL_STORAGE`
- `cordova.plugins.diagnostic.permission.BODY_SENSORS`


##### Runtime permission groups

Each runtime permission belongs to a permission group. Requesting a permission also requests authorisation for all other permissions in that group. If other permissions in the group are not defined in the manifest, they will default to DENIED_ALWAYS status. Otherwise, if user grants permission, all other permissions in the group will be granted; if user denies permission, all other permissions in the group will be denied.

Permissions are grouped as follows:

    CALENDAR: [READ_CALENDAR, WRITE_CALENDAR],
    CAMERA: [CAMERA],
    CONTACTS: [READ_CONTACTS, WRITE_CONTACTS, GET_ACCOUNTS],
    LOCATION: [ACCESS_FINE_LOCATION, ACCESS_COARSE_LOCATION],
    MICROPHONE: [RECORD_AUDIO],
    PHONE: [READ_PHONE_STATE, CALL_PHONE, ADD_VOICEMAIL, USE_SIP, PROCESS_OUTGOING_CALLS, READ_CALL_LOG, WRITE_CALL_LOG],
    SENSORS: [BODY_SENSORS],
    SMS: [SEND_SMS, RECEIVE_SMS, READ_SMS, RECEIVE_WAP_PUSH, RECEIVE_MMS],
    STORAGE: [READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE]

##### Runtime permissions example project

While the [cordova-diagnostic-plugin-example](https://github.com/dpa99c/cordova-diagnostic-plugin-example) illustrates use of runtime permissions in the context of requesting location and camera access, the [cordova-diagnostic-plugin-android-runtime-example](https://github.com/dpa99c/cordova-diagnostic-plugin-android-runtime-example) project explicitly illustrates use of Android runtime permissions with this plugin:

[https://github.com/dpa99c/cordova-diagnostic-plugin-android-runtime-example](https://github.com/dpa99c/cordova-diagnostic-plugin-android-runtime-example)

##### Android Camera permissions

Note that the Android variant of [`requestCameraAuthorization()`](#requestcameraauthorization) requests the `READ_EXTERNAL_STORAGE` permission, in addition to the `CAMERA` permission.
This is because the [cordova-plugin-camera@2.2+](https://github.com/apache/cordova-plugin-camera) requires both of these permissions.

So to use this method in conjunction with the Cordova camera plugin, make sure you are using the most recent `cordova-plugin-camera` release: v2.2.0 or above.

## Windows

### Supported Windows versions

Currently the plugin only supports Windows 10 and Windows 10 Mobile, not Windows Phone 8.0 or 8.1.

The reason being that the native functionality required by the plugin's current Windows implementation is only available since Windows 10.

For example, `isLocationAvailable()` [invokes](https://github.com/dpa99c/cordova-diagnostic-plugin/blob/master/src/windows/diagnosticProxy.js#L19) `Windows.Devices.Geolocation.Geolocator.requestAccessAsync()`. And this was only [introduced in Windows 10](https://msdn.microsoft.com/library/windows/apps/windows.devices.geolocation.geolocator.requestaccessasync.aspx).

Windows Phone 8.x would require a different implementation (even if possible), and I don't plan to add that since the Windows 8.x global marketshare is below 5% and falling, and is also rendered obsolete by Windows 10 Mobile.

### Windows 10 Mobile permissions

Some of functions offered by this plugin require specific permissions to be set in the package.windows10.appxmanifest. Where additional permissions are needed, they are listed alongside the function that requires them.

These permissions will not be set by this plugin, to avoid asking for unnecessary permissions in your app, in the case that you do not use a particular part of the plugin.
Instead, you can add these permissions as necessary, depending what functions in the plugin you decide to use.

You can add these permissions by manually editing the package.windows10.appxmanifest in `/platforms/windows/`.

## iOS

### iOS usage description messages

When requesting permission to use device functionality on iOS 8+, a message is displayed to the user indicating the reason for the request.
These messages are stored in the `{project}-Info.plist` file under `NS*UsageDescription` keys.

Upon installing this plugin into your project, it will add the following default messages to your plist.
To override these defaults, you can either edit the messages directly in the plist file, or to persist the changes between platform updates, use the [cordova-custom-config](https://github.com/dpa99c/cordova-custom-config) plugin to add overrides directly from the config.xml.
For example:

`config.xml`

    <platform name="ios">
        <plugin name="cordova-custom-config" version="*"/>
        <config-file platform="ios" target="*-Info.plist" parent="NSLocationAlwaysUsageDescription">
            <string>My custom message for always using location.</string>
        </config-file>
        <config-file platform="ios" target="*-Info.plist" parent="NSLocationWhenInUseUsageDescription">
            <string>My custom message for using location when in use.</string>
        </config-file>
    </platform>

# Example project

An example project illustrating use of this plugin can be found here: [https://github.com/dpa99c/cordova-diagnostic-plugin-example](https://github.com/dpa99c/cordova-diagnostic-plugin-example)

Phonegap Build users who want to validate the plugin in that environment can try building: [https://github.com/dpa99c/cordova-diagnostic-plugin-phonegap-build-example](https://github.com/dpa99c/cordova-diagnostic-plugin-phonegap-build-example)

## Screenshots

### Android

![Android screenshot](https://raw.githubusercontent.com/dpa99c/cordova-diagnostic-plugin-example/master/screenshots/android_1.png)
![Android screenshot](https://raw.githubusercontent.com/dpa99c/cordova-diagnostic-plugin-example/master/screenshots/android_2.png)
![Android screenshot](https://raw.githubusercontent.com/dpa99c/cordova-diagnostic-plugin-example/master/screenshots/android_3.png)

### iOS

![iOS screenshot](https://raw.githubusercontent.com/dpa99c/cordova-diagnostic-plugin-example/master/screenshots/ios_1.png)
![iOS screenshot](https://raw.githubusercontent.com/dpa99c/cordova-diagnostic-plugin-example/master/screenshots/ios_2.png)

# Release notes

See the [release notes wiki page](https://github.com/dpa99c/cordova-diagnostic-plugin/wiki/Release-notes)

# Credits

Forked from: [https://github.com/mablack/cordova-diagnostic-plugin](https://github.com/mablack/cordova-diagnostic-plugin)

Original Cordova 2 implementation by: AVANTIC ESTUDIO DE INGENIEROS ([www.avantic.net](http://www.avantic.net/))

Windows 10 implementation by [Mike Dailor](https://github.com/mdailor) / [Next Wave Software, Inc.](http://nextwavesoftware.com/)

# License
================

The MIT License

Copyright (c) 2016 Dave Alden / Working Edge Ltd.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
