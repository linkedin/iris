/**
 *  Diagnostic plugin for iOS
 *
 *  Copyright (c) 2015 Working Edge Ltd.
 *  Copyright (c) 2012 AVANTIC ESTUDIO DE INGENIEROS
 **/
var Diagnostic = (function(){

    /********************
     * Internal functions
     ********************/

    function ensureBoolean(callback){
        return function(result){
            callback(!!result);
        }
    }

    function mapFromLegacyCameraApi() {
        var params;
        if (typeof arguments[0]  === "function") {
            params = (arguments.length > 2 && typeof arguments[2]  === "object") ? arguments[2] : {};
            params.successCallback = arguments[0];
            if(arguments.length > 1 && typeof arguments[1]  === "function") {
                params.errorCallback = arguments[1];
            }
        }else { // if (typeof arguments[0]  === "object")
            params = arguments[0];
        }
        return params;
    }


    /********************
     * Public properties
     ********************/
    var Diagnostic = {};

    /**
     * Permission states
     * @type {object}
     */
    Diagnostic.permissionStatus = {
        "NOT_REQUESTED": "not_determined", // App has not yet requested this permission
        "DENIED": "denied", // User denied access to this permission
        "RESTRICTED": "restricted", // Permission is unavailable and user cannot enable it.  For example, when parental controls are in effect for the current user.
        "GRANTED": "authorized", //  User granted access to this permission
        "GRANTED_WHEN_IN_USE": "authorized_when_in_use" //  User granted access use location permission only when app is in use
    };

    Diagnostic.locationAuthorizationMode = {
        "ALWAYS": "always",
        "WHEN_IN_USE": "when_in_use"
    };

    Diagnostic.bluetoothState = {
        "UNKNOWN": "unknown",
        "RESETTING": "resetting",
        "UNSUPPORTED": "unsupported",
        "UNAUTHORIZED": "unauthorized",
        "POWERED_OFF": "powered_off",
        "POWERED_ON": "powered_on"
    };

    // Placeholder listeners
    Diagnostic._onBluetoothStateChange =
        Diagnostic._onLocationStateChange = function(){};

    /**********************
     *
     * Public API functions
     *
     **********************/

    /***********
     * General
     ***********/

    /**
     * Switch to settings app. Opens settings page for this app.
     *
     * @param {Function} successCallback - The callback which will be called when switch to settings is successful.
     * @param {Function} errorCallback - The callback which will be called when switch to settings encounters an error.
     * This callback function is passed a single string parameter containing the error message.
     * This works only on iOS 8+. iOS 7 and below will invoke the errorCallback.
     */
    Diagnostic.switchToSettings = function(successCallback, errorCallback) {
        return cordova.exec(successCallback,
            errorCallback,
            'Diagnostic',
            'switchToSettings',
            []);
    };

    /************
     * Location *
     ************/


    /**
     * Checks if location is available for use by the app.
     * On iOS this returns true if both the device setting for Location Services is ON AND the application is authorized to use location.
     * When location is enabled, the locations returned are by a mixture GPS hardware, network triangulation and Wifi network IDs.
     *
     * @param {Function} successCallback - The callback which will be called when operation is successful.
     * This callback function is passed a single boolean parameter which is TRUE if location is available for use.
     * @param {Function} errorCallback -  The callback which will be called when operation encounters an error.
     * This callback function is passed a single string parameter containing the error message.
     */
    Diagnostic.isLocationAvailable = function(successCallback, errorCallback) {
        return cordova.exec(ensureBoolean(successCallback),
            errorCallback,
            'Diagnostic',
            'isLocationAvailable',
            []);
    };

    /**
     * Checks if the device location setting is enabled.
     * Returns true if Location Services is enabled.
     *
     * @param {Function} successCallback - The callback which will be called when operation is successful.
     * This callback function is passed a single boolean parameter which is TRUE if Location Services is enabled.
     * @param {Function} errorCallback -  The callback which will be called when operation encounters an error.
     * This callback function is passed a single string parameter containing the error message.
     */
    Diagnostic.isLocationEnabled = function(successCallback, errorCallback) {
        return cordova.exec(ensureBoolean(successCallback),
            errorCallback,
            'Diagnostic',
            'isLocationEnabled',
            []);
    };


    /**
     * Checks if the application is authorized to use location.
     *
     * @param {Function} successCallback - The callback which will be called when operation is successful.
     * This callback function is passed a single boolean parameter which is TRUE if application is authorized to use location either "when in use" (only in foreground) OR "always" (foreground and background).
     * @param {Function} errorCallback -  The callback which will be called when operation encounters an error.
     * This callback function is passed a single string parameter containing the error message.
     */
    Diagnostic.isLocationAuthorized = function(successCallback, errorCallback) {
        return cordova.exec(ensureBoolean(successCallback),
            errorCallback,
            'Diagnostic',
            'isLocationAuthorized',
            []);
    };

    /**
     * Returns the location authorization status for the application.
     *
     * @param {Function} successCallback - The callback which will be called when operation is successful.
     * This callback function is passed a single string parameter which indicates the location authorization status as a constant in `cordova.plugins.diagnostic.permissionStatus`.
     * Possible values are:
     * `cordova.plugins.diagnostic.permissionStatus.NOT_REQUESTED`
     * `cordova.plugins.diagnostic.permissionStatus.DENIED`
     * `cordova.plugins.diagnostic.permissionStatus.GRANTED`
     * `cordova.plugins.diagnostic.permissionStatus.GRANTED_WHEN_IN_USE`
     * Note that `GRANTED` indicates the app is always granted permission (even when in background).
     * @param {Function} errorCallback -  The callback which will be called when operation encounters an error.
     * This callback function is passed a single string parameter containing the error message.
     */
    Diagnostic.getLocationAuthorizationStatus = function(successCallback, errorCallback) {
        return cordova.exec(successCallback,
            errorCallback,
            'Diagnostic',
            'getLocationAuthorizationStatus',
            []);
    };

    /**
     * Requests location authorization for the application.
     * Authorization can be requested to use location either "when in use" (only in foreground) or "always" (foreground and background).
     * Should only be called if authorization status is NOT_REQUESTED. Calling it when in any other state will have no effect.
     *
     * @param {Function} successCallback - Invoked in response to the user's choice in the permission dialog.
     * It is passed a single string parameter which defines the resulting authorisation status as a constant in `cordova.plugins.diagnostic.permissionStatus`.
     * Possible values are:
     * `cordova.plugins.diagnostic.permissionStatus.DENIED`
     * `cordova.plugins.diagnostic.permissionStatus.GRANTED`
     * `cordova.plugins.diagnostic.permissionStatus.GRANTED_WHEN_IN_USE`
     * @param {Function} errorCallback -  The callback which will be called when operation encounters an error.
     * This callback function is passed a single string parameter containing the error message.
     * @param {String} mode - (optional) location authorization mode as a constant in `cordova.plugins.diagnostic.locationAuthorizationMode`.
     * If not specified, defaults to `cordova.plugins.diagnostic.locationAuthorizationMode.WHEN_IN_USE`.
     */
    Diagnostic.requestLocationAuthorization = function(successCallback, errorCallback, mode) {
        return cordova.exec(successCallback,
            errorCallback,
            'Diagnostic',
            'requestLocationAuthorization',
            [mode && mode === Diagnostic.locationAuthorizationMode.ALWAYS]);
    };

    /**
     * Registers a function to be called when a change in Location state occurs.
     * On iOS, this occurs when location authorization status is changed.
     * This can be triggered either by the user's response to a location permission authorization dialog,
     * by the user turning on/off Location Services,
     * or by the user changing the Location authorization state specifically for your app.
     * Pass in a falsey value to de-register the currently registered function.
     *
     * @param {Function} successCallback -  The callback which will be called when the Location state changes.
     * This callback function is passed a single string parameter indicating the new location authorisation status as a constant in `cordova.plugins.diagnostic.permissionStatus`.
     */
    Diagnostic.registerLocationStateChangeHandler = function(successCallback) {
        Diagnostic._onLocationStateChange = successCallback || function(){};
    };

    /************
     * Camera   *
     ************/

    /**
     * Checks if camera is enabled for use.
     * On iOS this returns true if both the device has a camera AND the application is authorized to use it.
     *
     * @param {Object} params - (optional) parameters:
     *  - {Function} successCallback - The callback which will be called when operation is successful.
     * This callback function is passed a single boolean parameter which is TRUE if camera is present and authorized for use.
     *  - {Function} errorCallback -  The callback which will be called when operation encounters an error.
     * This callback function is passed a single string parameter containing the error message.
     */
    Diagnostic.isCameraAvailable = function(params) {
        params = mapFromLegacyCameraApi.apply(this, arguments);

        params.successCallback = params.successCallback || function(){};
        return cordova.exec(ensureBoolean(params.successCallback),
            params.errorCallback,
            'Diagnostic',
            'isCameraAvailable',
            []);
    };

    /**
     * Checks if camera hardware is present on device.
     *
     * @param {Function} successCallback - The callback which will be called when operation is successful.
     * This callback function is passed a single boolean parameter which is TRUE if camera is present
     * @param {Function} errorCallback -  The callback which will be called when operation encounters an error.
     * This callback function is passed a single string parameter containing the error message.
     */
    Diagnostic.isCameraPresent = function(successCallback, errorCallback) {
        return cordova.exec(ensureBoolean(successCallback),
            errorCallback,
            'Diagnostic',
            'isCameraPresent',
            []);
    };


    /**
     * Checks if the application is authorized to use the camera.
     *
     * @param {Object} params - (optional) parameters:
     *  - {Function} successCallback - The callback which will be called when operation is successful.
     * This callback function is passed a single boolean parameter which is TRUE if camera is authorized for use.
     *   - {Function} errorCallback -  The callback which will be called when operation encounters an error.
     * This callback function is passed a single string parameter containing the error message.
     */
    Diagnostic.isCameraAuthorized = function(params) {
        params = mapFromLegacyCameraApi.apply(this, arguments);

        return cordova.exec(ensureBoolean(params.successCallback),
            params.errorCallback,
            'Diagnostic',
            'isCameraAuthorized',
            []);
    };

    /**
     * Returns the camera authorization status for the application.
     *
     * @param {Object} params - (optional) parameters:
     *  - {Function} successCallback - The callback which will be called when operation is successful.
     * This callback function is passed a single string parameter which indicates the authorization status as a constant in `cordova.plugins.diagnostic.permissionStatus`.
     *  - {Function} errorCallback -  The callback which will be called when operation encounters an error.
     * This callback function is passed a single string parameter containing the error message.
     */
    Diagnostic.getCameraAuthorizationStatus = function(params) {
        params = mapFromLegacyCameraApi.apply(this, arguments);

        return cordova.exec(params.successCallback,
            params.errorCallback,
            'Diagnostic',
            'getCameraAuthorizationStatus',
            []);
    };

    /**
     * Requests camera authorization for the application.
     * Should only be called if authorization status is NOT_REQUESTED. Calling it when in any other state will have no effect.
     *
     * @param {Object} params - (optional) parameters:
     * - {Function} successCallback - The callback which will be called when operation is successful.
     * This callback function is passed a single string parameter indicating whether access to the camera was granted or denied:
     * `cordova.plugins.diagnostic.permissionStatus.GRANTED` or `cordova.plugins.diagnostic.permissionStatus.DENIED`
     * - {Function} errorCallback -  The callback which will be called when operation encounters an error.
     * This callback function is passed a single string parameter containing the error message.
     */
    Diagnostic.requestCameraAuthorization = function(params){
        params = mapFromLegacyCameraApi.apply(this, arguments);

        params.successCallback = params.successCallback || function(){};
        return cordova.exec(function(isGranted){
                params.successCallback(isGranted ? Diagnostic.permissionStatus.GRANTED : Diagnostic.permissionStatus.DENIED);
            },
            params.errorCallback,
            'Diagnostic',
            'requestCameraAuthorization',
            []);
    };

    /**
     * Checks if the application is authorized to use the Camera Roll in Photos app.
     *
     * @param {Function} successCallback - The callback which will be called when operation is successful.
     * This callback function is passed a single boolean parameter which is TRUE if access to Camera Roll is authorized.
     * @param {Function} errorCallback -  The callback which will be called when operation encounters an error.
     * This callback function is passed a single string parameter containing the error message.
     */
    Diagnostic.isCameraRollAuthorized = function(successCallback, errorCallback) {
        return cordova.exec(ensureBoolean(successCallback),
            errorCallback,
            'Diagnostic',
            'isCameraRollAuthorized',
            []);
    };

    /**
     * Returns the authorization status for the application to use the Camera Roll in Photos app.
     *
     * @param {Function} successCallback - The callback which will be called when operation is successful.
     * This callback function is passed a single string parameter which indicates the authorization status as a constant in `cordova.plugins.diagnostic.permissionStatus`.
     * @param {Function} errorCallback -  The callback which will be called when operation encounters an error.
     * This callback function is passed a single string parameter containing the error message.
     */
    Diagnostic.getCameraRollAuthorizationStatus = function(successCallback, errorCallback) {
        return cordova.exec(successCallback,
            errorCallback,
            'Diagnostic',
            'getCameraRollAuthorizationStatus',
            []);
    };

    /**
     * Requests camera roll authorization for the application.
     * Should only be called if authorization status is NOT_REQUESTED. Calling it when in any other state will have no effect.
     *
     * @param {Function} successCallback - The callback which will be called when operation is successful.
     * This callback function is passed a single string parameter indicating the new authorization status:
     * `cordova.plugins.diagnostic.permissionStatus.GRANTED` or `cordova.plugins.diagnostic.permissionStatus.DENIED`
     * @param {Function} errorCallback -  The callback which will be called when operation encounters an error.
     * This callback function is passed a single string parameter containing the error message.
     */
    Diagnostic.requestCameraRollAuthorization = function(successCallback, errorCallback) {
        return cordova.exec(function(status){
                successCallback(status == "authorized" ? Diagnostic.permissionStatus.GRANTED : Diagnostic.permissionStatus.DENIED);
            },
            errorCallback,
            'Diagnostic',
            'requestCameraRollAuthorization',
            []);
    };

    /************
     * WiFi     *
     ************/

    /**
     * Checks if Wi-Fi is connected.
     * On iOS this returns true if the WiFi setting is set to enabled AND the device is connected to a network by WiFi.
     *
     * @param {Function} successCallback - The callback which will be called when operation is successful.
     * This callback function is passed a single boolean parameter which is TRUE if device is connected by WiFi.
     * @param {Function} errorCallback -  The callback which will be called when operation encounters an error.
     * This callback function is passed a single string parameter containing the error message.
     */
    Diagnostic.isWifiAvailable = function(successCallback, errorCallback) {
        return cordova.exec(ensureBoolean(successCallback),
            errorCallback,
            'Diagnostic',
            'isWifiAvailable',
            []);
    };

    /**
     * Checks if Wifi is enabled.
     * On iOS this returns true if the WiFi setting is set to enabled (regardless of whether it's connected to a network).
     *
     * @param {Function} successCallback -  The callback which will be called when the operation is successful.
     * This callback function is passed a single boolean parameter which is TRUE if WiFi is enabled.
     * @param {Function} errorCallback -  The callback which will be called when the operation encounters an error.
     *  This callback function is passed a single string parameter containing the error message.
     */
    Diagnostic.isWifiEnabled = function(successCallback, errorCallback) {
        return cordova.exec(successCallback,
            errorCallback,
            'Diagnostic',
            'isWifiEnabled',
            []);
    };

    /***************
     * Bluetooth   *
     ***************/

    /**
     * Checks if the device has Bluetooth LE capabilities and if so that Bluetooth is switched on
     *
     * @param {Function} successCallback - The callback which will be called when operation is successful.
     * This callback function is passed a single boolean parameter which is TRUE if device has Bluetooth LE and Bluetooth is switched on.
     * @param {Function} errorCallback -  The callback which will be called when operation encounters an error.
     * This callback function is passed a single string parameter containing the error message.
     */
    Diagnostic.isBluetoothAvailable = function(successCallback, errorCallback) {
        return cordova.exec(ensureBoolean(successCallback),
            errorCallback,
            'Diagnostic',
            'isBluetoothAvailable',
            []);
    };

    /**
     * Returns the state of Bluetooth LE on the device.
     *
     * @param {Function} successCallback - The callback which will be called when operation is successful.
     * This callback function is passed a single string parameter which indicates the Bluetooth state as a constant in `cordova.plugins.diagnostic.bluetoothState`.
     * @param {Function} errorCallback -  The callback which will be called when operation encounters an error.
     * This callback function is passed a single string parameter containing the error message.
     */
    Diagnostic.getBluetoothState = function(successCallback, errorCallback) {
        return cordova.exec(successCallback,
            errorCallback,
            'Diagnostic',
            'getBluetoothState',
            []);
    };


    /**
     * Registers a function to be called when a change in Bluetooth state occurs.
     * Pass in a falsey value to de-register the currently registered function.
     *
     * @param {Function} successCallback - function call when a change in Bluetooth state occurs.
     * This callback function is passed a single string parameter which indicates the Bluetooth state as a constant in `cordova.plugins.diagnostic.bluetoothState`.
     * @param {Function} errorCallback -  The callback which will be called when the operation encounters an error.
     *  This callback function is passed a single string parameter containing the error message.
     */
    Diagnostic.registerBluetoothStateChangeHandler = function(successCallback, errorCallback){
        Diagnostic._onBluetoothStateChange = successCallback || function(){};
    };

    /**
     * Requests Bluetooth authorization for the application.
     * The outcome of the authorization request can be determined by registering a handler using `registerBluetoothStateChangeHandler()`.
     *
     * @param {Function} successCallback - The callback which will be called when operation is successful.
     * This callback function is not passed any parameters.
     * @param {Function} errorCallback -  The callback which will be called when operation encounters an error.
     * This callback function is passed a single string parameter containing the error message.
     */
    Diagnostic.requestBluetoothAuthorization = function(successCallback, errorCallback) {
        return cordova.exec(
            successCallback,
            errorCallback,
            'Diagnostic',
            'requestBluetoothAuthorization',
            []);
    };

    /***************************
     * Microphone / Record Audio
     ***************************/

    /**
     * Checks if the application is authorized to use the microphone for recording audio.
     *
     * @param {Function} successCallback - The callback which will be called when operation is successful.
     * This callback function is passed a single boolean parameter which is TRUE if access to microphone is authorized.
     * @param {Function} errorCallback -  The callback which will be called when operation encounters an error.
     * This callback function is passed a single string parameter containing the error message.
     */
    Diagnostic.isMicrophoneAuthorized = function(successCallback, errorCallback) {
        return cordova.exec(ensureBoolean(successCallback),
            errorCallback,
            'Diagnostic',
            'isMicrophoneAuthorized',
            []);
    };

    /**
     * Returns the authorization status for the application to use the microphone for recording audio.
     *
     * @param {Function} successCallback - The callback which will be called when operation is successful.
     * This callback function is passed a single string parameter which indicates the authorization status as a constant in `cordova.plugins.diagnostic.permissionStatus`.
     * @param {Function} errorCallback -  The callback which will be called when operation encounters an error.
     * This callback function is passed a single string parameter containing the error message.
     */
    Diagnostic.getMicrophoneAuthorizationStatus = function(successCallback, errorCallback) {
        return cordova.exec(successCallback,
            errorCallback,
            'Diagnostic',
            'getMicrophoneAuthorizationStatus',
            []);
    };

    /**
     * Requests access to microphone if authorization was never granted nor denied, will only return access status otherwise.
     *
     * @param {Function} successCallback - The callback which will be called when operation is successful.
     * This callback function is passed a single string parameter indicating whether access to the microphone was granted or denied:
     * `cordova.plugins.diagnostic.permissionStatus.GRANTED` or `cordova.plugins.diagnostic.permissionStatus.DENIED`
     * @param {Function} errorCallback - The callback which will be called when an error occurs.
     * This callback function is passed a single string parameter containing the error message.
     * This works only on iOS 7+.
     */
    Diagnostic.requestMicrophoneAuthorization = function(successCallback, errorCallback) {
        return cordova.exec(function(isGranted){
                successCallback(isGranted ? Diagnostic.permissionStatus.GRANTED : Diagnostic.permissionStatus.DENIED);
            },
            errorCallback,
            'Diagnostic',
            'requestMicrophoneAuthorization',
            []);
    };

    /***********************
     * Remote Notifications
     ***********************/

    /**
     * Checks if remote (push) notifications are enabled.
     * On iOS 8+, returns true if app is registered for remote notifications AND "Allow Notifications" switch is ON AND alert style is not set to "None" (i.e. "Banners" or "Alerts").
     * On iOS <=7, returns true if app is registered for remote notifications AND alert style is not set to "None" (i.e. "Banners" or "Alerts") - same as isRegisteredForRemoteNotifications().
     *
     * @param {Function} successCallback - The callback which will be called when operation is successful.
     * This callback function is passed a single boolean parameter which is TRUE if remote (push) notifications are enabled.
     * @param {Function} errorCallback -  The callback which will be called when operation encounters an error.
     * This callback function is passed a single string parameter containing the error message.
     */
    Diagnostic.isRemoteNotificationsEnabled = function(successCallback, errorCallback) {
        return cordova.exec(ensureBoolean(successCallback),
            errorCallback,
            'Diagnostic',
            'isRemoteNotificationsEnabled',
            []);
    };

    /**
     * Indicates the current setting of notification types for the app in the Settings app.
     * Note: on iOS 8+, if "Allow Notifications" switch is OFF, all types will be returned as disabled.
     *
     * @param {Function} successCallback - The callback which will be called when operation is successful.
     * This callback function is passed a single object parameter where the key is the notification type and the value is a boolean indicating whether it's enabled:
     * "alert" => alert style is not set to "None" (i.e. "Banners" or "Alerts");
     * "badge" => "Badge App Icon" switch is ON;
     * "sound" => "Sounds"/"Alert Sound" switch is ON.
     * @param {Function} errorCallback -  The callback which will be called when operation encounters an error.
     * This callback function is passed a single string parameter containing the error message.
     */
    Diagnostic.getRemoteNotificationTypes = function(successCallback, errorCallback) {
        return cordova.exec(function(sTypes){
                var oTypes = JSON.parse(sTypes);
                for(var type in oTypes){
                    oTypes[type] = parseInt(oTypes[type]) === 1 ;
                }
                successCallback(oTypes);
            },
            errorCallback,
            'Diagnostic',
            'getRemoteNotificationTypes',
            []);
    };

    /**
     * Indicates if the app is registered for remote notifications on the device.
     * On iOS 8+, returns true if the app is registered for remote notifications and received its device token,
     * or false if registration has not occurred, has failed, or has been denied by the user.
     * Note that user preferences for notifications in the Settings app will not affect this.
     * On iOS <=7, returns true if app is registered for remote notifications AND alert style is not set to "None" (i.e. "Banners" or "Alerts") - same as isRemoteNotificationsEnabled().
     *
     * @param {Function} successCallback - The callback which will be called when operation is successful.
     * This callback function is passed a single boolean parameter which is TRUE if the device is registered for remote (push) notifications.
     * @param {Function} errorCallback -  The callback which will be called when operation encounters an error.
     * This callback function is passed a single string parameter containing the error message.
     */
    Diagnostic.isRegisteredForRemoteNotifications = function(successCallback, errorCallback) {
        return cordova.exec(ensureBoolean(successCallback),
            errorCallback,
            'Diagnostic',
            'isRegisteredForRemoteNotifications',
            []);
    };

    /*************
     * Contacts
     *************/

    /**
     * Checks if the application is authorized to use contacts (address book).
     *
     * @param {Function} successCallback - The callback which will be called when operation is successful.
     * This callback function is passed a single boolean parameter which is TRUE if contacts is authorized for use.
     * @param {Function} errorCallback -  The callback which will be called when operation encounters an error.
     * This callback function is passed a single string parameter containing the error message.
     */
    Diagnostic.isContactsAuthorized = function(successCallback, errorCallback) {
        return cordova.exec(ensureBoolean(successCallback),
            errorCallback,
            'Diagnostic',
            'isAddressBookAuthorized',
            []);
    };

    /**
     * Returns the contacts (address book) authorization status for the application.
     *
     * @param {Function} successCallback - The callback which will be called when operation is successful.
     * This callback function is passed a single string parameter which indicates the authorization status as a constant in `cordova.plugins.diagnostic.permissionStatus`.
     * @param {Function} errorCallback -  The callback which will be called when operation encounters an error.
     * This callback function is passed a single string parameter containing the error message.
     */
    Diagnostic.getContactsAuthorizationStatus = function(successCallback, errorCallback) {
        return cordova.exec(successCallback,
            errorCallback,
            'Diagnostic',
            'getAddressBookAuthorizationStatus',
            []);
    };

    /**
     * Requests contacts (address book) authorization for the application.
     * Should only be called if authorization status is NOT_REQUESTED. Calling it when in any other state will have no effect.
     *
     * @param {Function} successCallback - The callback which will be called when operation is successful.
     * This callback function is passed a single string parameter indicating whether access to contacts was granted or denied:
     * `cordova.plugins.diagnostic.permissionStatus.GRANTED` or `cordova.plugins.diagnostic.permissionStatus.DENIED`
     * @param {Function} errorCallback -  The callback which will be called when operation encounters an error.
     * This callback function is passed a single string parameter containing the error message.
     */
    Diagnostic.requestContactsAuthorization = function(successCallback, errorCallback) {
        return cordova.exec(function(isGranted){
                successCallback(isGranted ? Diagnostic.permissionStatus.GRANTED : Diagnostic.permissionStatus.DENIED);
            },
            errorCallback,
            'Diagnostic',
            'requestAddressBookAuthorization',
            []);
    };

    /*****************
     * Calendar events
     *****************/

    /**
     * Checks if the application is authorized to use calendar.
     *
     * @param {Function} successCallback - The callback which will be called when operation is successful.
     * This callback function is passed a single boolean parameter which is TRUE if calendar is authorized for use.
     * @param {Function} errorCallback -  The callback which will be called when operation encounters an error.
     * This callback function is passed a single string parameter containing the error message.
     */
    Diagnostic.isCalendarAuthorized = function(successCallback, errorCallback) {
        return cordova.exec(ensureBoolean(successCallback),
            errorCallback,
            'Diagnostic',
            'isCalendarAuthorized',
            []);
    };

    /**
     * Returns the calendar event authorization status for the application.
     *
     * @param {Function} successCallback - The callback which will be called when operation is successful.
     * This callback function is passed a single string parameter which indicates the authorization status as a constant in `cordova.plugins.diagnostic.permissionStatus`.
     * @param {Function} errorCallback -  The callback which will be called when operation encounters an error.
     * This callback function is passed a single string parameter containing the error message.
     */
    Diagnostic.getCalendarAuthorizationStatus = function(successCallback, errorCallback) {
        return cordova.exec(successCallback,
            errorCallback,
            'Diagnostic',
            'getCalendarAuthorizationStatus',
            []);
    };

    /**
     * Requests calendar event authorization for the application.
     * Should only be called if authorization status is NOT_REQUESTED. Calling it when in any other state will have no effect.
     *
     * @param {Function} successCallback - The callback which will be called when operation is successful.
     * This callback function is passed a single string parameter indicating whether access to calendar was granted or denied:
     * `cordova.plugins.diagnostic.permissionStatus.GRANTED` or `cordova.plugins.diagnostic.permissionStatus.DENIED`
     * @param {Function} errorCallback -  The callback which will be called when operation encounters an error.
     * This callback function is passed a single string parameter containing the error message.
     */
    Diagnostic.requestCalendarAuthorization = function(successCallback, errorCallback) {
        return cordova.exec(function(isGranted){
                successCallback(isGranted ? Diagnostic.permissionStatus.GRANTED : Diagnostic.permissionStatus.DENIED);
            },
            errorCallback,
            'Diagnostic',
            'requestCalendarAuthorization',
            []);
    };

    /*********************
     * Calendar reminders
     *********************/

    /**
     * Checks if the application is authorized to use calendar reminders.
     *
     * @param {Function} successCallback - The callback which will be called when operation is successful.
     * This callback function is passed a single boolean parameter which is TRUE if reminders is authorized for use.
     * @param {Function} errorCallback -  The callback which will be called when operation encounters an error.
     * This callback function is passed a single string parameter containing the error message.
     */
    Diagnostic.isRemindersAuthorized = function(successCallback, errorCallback) {
        return cordova.exec(ensureBoolean(successCallback),
            errorCallback,
            'Diagnostic',
            'isRemindersAuthorized',
            []);
    };

    /**
     * Returns the calendar event authorization status for the application.
     *
     * @param {Function} successCallback - The callback which will be called when operation is successful.
     * This callback function is passed a single string parameter which indicates the authorization status as a constant in `cordova.plugins.diagnostic.permissionStatus`.
     * @param {Function} errorCallback -  The callback which will be called when operation encounters an error.
     * This callback function is passed a single string parameter containing the error message.
     */
    Diagnostic.getRemindersAuthorizationStatus = function(successCallback, errorCallback) {
        return cordova.exec(successCallback,
            errorCallback,
            'Diagnostic',
            'getRemindersAuthorizationStatus',
            []);
    };

    /**
     * Requests calendar reminders authorization for the application.
     * Should only be called if authorization status is NOT_REQUESTED. Calling it when in any other state will have no effect.
     *
     * @param {Function} successCallback - The callback which will be called when operation is successful.
     * This callback function is passed a single string parameter indicating whether access to reminders was granted or denied:
     * `cordova.plugins.diagnostic.permissionStatus.GRANTED` or `cordova.plugins.diagnostic.permissionStatus.DENIED`
     * @param {Function} errorCallback -  The callback which will be called when operation encounters an error.
     * This callback function is passed a single string parameter containing the error message.
     */
    Diagnostic.requestRemindersAuthorization = function(successCallback, errorCallback) {
        return cordova.exec(function(isGranted){
                successCallback(isGranted ? Diagnostic.permissionStatus.GRANTED : Diagnostic.permissionStatus.DENIED);
            },
            errorCallback,
            'Diagnostic',
            'requestRemindersAuthorization',
            []);
    };

    /*********************
     * Background refresh
     *********************/

    /**
     * Returns the background refresh authorization status for the application.
     *
     * @param {Function} successCallback - The callback which will be called when operation is successful.
     * This callback function is passed a single string parameter which indicates the authorization status as a constant in `cordova.plugins.diagnostic.permissionStatus`.
     * @param {Function} errorCallback -  The callback which will be called when operation encounters an error.
     * This callback function is passed a single string parameter containing the error message.
     */
    Diagnostic.getBackgroundRefreshStatus = function(successCallback, errorCallback) {
        return cordova.exec(successCallback,
            errorCallback,
            'Diagnostic',
            'getBackgroundRefreshStatus',
            []);
    };

    /**
     * Checks if the application is authorized for background refresh.
     *
     * @param {Function} successCallback - The callback which will be called when operation is successful.
     * This callback function is passed a single boolean parameter which is TRUE if background refresh is authorized for use.
     * @param {Function} errorCallback -  The callback which will be called when operation encounters an error.
     * This callback function is passed a single string parameter containing the error message.
     */
    Diagnostic.isBackgroundRefreshAuthorized = function(successCallback, errorCallback) {
        Diagnostic.getBackgroundRefreshStatus(function(status){
            successCallback(status === Diagnostic.permissionStatus.GRANTED);
        }, errorCallback);
    };

    /*************
     * Motion
     *************/

    /**
     * Checks if motion tracking is available on the current device.
     *
     * @param {Function} successCallback - The callback which will be called when operation is successful.
     * This callback function is passed a single boolean parameter which is TRUE if motion tracking is available on the current device.
     * @param {Function} errorCallback -  The callback which will be called when operation encounters an error.
     * This callback function is passed a single string parameter containing the error message.
     */
    Diagnostic.isMotionAvailable = function(successCallback, errorCallback) {
        return cordova.exec(ensureBoolean(successCallback),
            errorCallback,
            'Diagnostic',
            'isMotionAvailable',
            []);
    };

    /**
     * Checks if it's possible to determine the outcome of a motion authorization request on the current device.
     * There's no direct way to determine if authorization was granted or denied, so the Pedometer API must be used to indirectly determine this:
     * therefore, if the device supports motion tracking but not Pedometer Event Tracking, the outcome of requesting motion detection cannot be determined.
     *
     * @param {Function} successCallback - The callback which will be called when operation is successful.
     * This callback function is passed a single boolean parameter which is TRUE if it's possible to determine the outcome of a motion authorization request on the current device.
     * @param {Function} errorCallback -  The callback which will be called when operation encounters an error.
     * This callback function is passed a single string parameter containing the error message.
     */
    Diagnostic.isMotionRequestOutcomeAvailable = function(successCallback, errorCallback) {
        return cordova.exec(ensureBoolean(successCallback),
            errorCallback,
            'Diagnostic',
            'isMotionRequestOutcomeAvailable',
            []);
    };

    /**
     * Requests and checks motion authorization for the application:
     * there is no way to independently request only or check only, so both must be done in one operation.
     * The native dialog asking user's consent can only be invoked once after the app is installed by calling this function:
     * once the user has either allowed or denied access, this function will only return the current authorization status
     * - it is not possible to re-invoke the dialog if the user denied permission in the native dialog;
     * in this case, you will have to instruct the user how to change motion authorization manually via the Settings app.
     * When calling this function, the message contained in the `NSMotionUsageDescription` .plist key is displayed to the user;
     * this plugin provides a default message, but you should override this with your specific reason for requesting access.
     * If the device doesn't support motion detection, the error callback will be invoked.
     * There's no direct way to determine if authorization was granted or denied, so the Pedometer API must be used to indirectly determine this:
     * therefore, if the device supports motion tracking but not Pedometer Event Tracking, the outcome of requesting motion detection cannot be determined.
     *
     * @param {Function} successCallback - The callback which will be called when operation is successful.
     * This callback function is passed a single string parameter indicating the result:
     * - `cordova.plugins.diagnostic.permissionStatus.GRANTED` - user granted motion authorization
     * - `cordova.plugins.diagnostic.permissionStatus.DENIED` - user denied authorization
     * - `cordova.plugins.diagnostic.permissionStatus.RESTRICTED` - user cannot grant motion authorization
     * - `cordova.plugins.diagnostic.permissionStatus.NOT_DETERMINED` - device does not support Pedometer Event Tracking, so authorization outcome cannot be determined.
     * - {Function} errorCallback - The callback which will be called when an error occurs. This callback function is passed a single string parameter containing the error message.
     * @param {Function} errorCallback -  The callback which will be called when operation encounters an error.
     * This callback function is passed a single string parameter containing the error message.
     */
    Diagnostic.requestAndCheckMotionAuthorization = function(successCallback, errorCallback) {
        return cordova.exec(
            successCallback,
            errorCallback,
            'Diagnostic',
            'requestAndCheckMotionAuthorization',
            []);
    };

    return Diagnostic;
})();
module.exports = Diagnostic;
