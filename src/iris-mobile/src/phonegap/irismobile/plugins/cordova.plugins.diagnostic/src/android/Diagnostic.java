/*
       Licensed to the Apache Software Foundation (ASF) under one
       or more contributor license agreements.  See the NOTICE file
       distributed with this work for additional information
       regarding copyright ownership.  The ASF licenses this file
       to you under the Apache License, Version 2.0 (the
       "License"); you may not use this file except in compliance
       with the License.  You may obtain a copy of the License at

         http://www.apache.org/licenses/LICENSE-2.0

       Unless required by applicable law or agreed to in writing,
       software distributed under the License is distributed on an
       "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
       KIND, either express or implied.  See the License for the
       specific language governing permissions and limitations
       under the License.
*/
package cordova.plugins;

/*
 * Imports
 */
import java.io.File;
import java.io.InputStream;
import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Random;


import org.apache.cordova.CordovaWebView;
import org.apache.cordova.CallbackContext;
import org.apache.cordova.CordovaPlugin;
import org.apache.cordova.CordovaInterface;
import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import android.Manifest;
import android.app.Activity;
import android.bluetooth.BluetoothAdapter;
import android.content.BroadcastReceiver;
import android.content.IntentFilter;
import android.location.Location;
import android.location.LocationListener;
import android.location.LocationManager;
import android.location.LocationProvider;
import android.net.Uri;
import android.nfc.NfcAdapter;
import android.nfc.NfcManager;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.os.StatFs;
import android.support.v4.os.EnvironmentCompat;
import android.text.TextUtils;
import android.util.Log;

import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.provider.Settings;
import android.net.wifi.WifiManager;

import android.support.v4.app.ActivityCompat;
import java.lang.SecurityException;
import java.util.Set;

import static android.nfc.NfcAdapter.EXTRA_ADAPTER_STATE;
import static android.nfc.NfcAdapter.STATE_OFF;
import static android.nfc.NfcAdapter.STATE_ON;

/**
 * Diagnostic plugin implementation for Android
 */
public class Diagnostic extends CordovaPlugin{


    /*************
     * Constants *
     *************/

    /**
     * Tag for debug log messages
     */
    public static final String TAG = "Diagnostic";

    /**
     * Map of "dangerous" permissions that need to be requested at run-time (Android 6.0/API 23 and above)
     * See http://developer.android.com/guide/topics/security/permissions.html#perm-groups
     */
    private static final Map<String, String> permissionsMap;
    static {
        Map<String, String> _permissionsMap = new HashMap <String, String>();
        Diagnostic.addBiDirMapEntry(_permissionsMap, "READ_CALENDAR", Manifest.permission.READ_CALENDAR);
        Diagnostic.addBiDirMapEntry(_permissionsMap, "WRITE_CALENDAR", Manifest.permission.WRITE_CALENDAR);
        Diagnostic.addBiDirMapEntry(_permissionsMap, "CAMERA", Manifest.permission.CAMERA);
        Diagnostic.addBiDirMapEntry(_permissionsMap, "READ_CONTACTS", Manifest.permission.READ_CONTACTS);
        Diagnostic.addBiDirMapEntry(_permissionsMap, "WRITE_CONTACTS", Manifest.permission.WRITE_CONTACTS);
        Diagnostic.addBiDirMapEntry(_permissionsMap, "GET_ACCOUNTS", Manifest.permission.GET_ACCOUNTS);
        Diagnostic.addBiDirMapEntry(_permissionsMap, "ACCESS_FINE_LOCATION", Manifest.permission.ACCESS_FINE_LOCATION);
        Diagnostic.addBiDirMapEntry(_permissionsMap, "ACCESS_COARSE_LOCATION", Manifest.permission.ACCESS_COARSE_LOCATION);
        Diagnostic.addBiDirMapEntry(_permissionsMap, "RECORD_AUDIO", Manifest.permission.RECORD_AUDIO);
        Diagnostic.addBiDirMapEntry(_permissionsMap, "READ_PHONE_STATE", Manifest.permission.READ_PHONE_STATE);
        Diagnostic.addBiDirMapEntry(_permissionsMap, "CALL_PHONE", Manifest.permission.CALL_PHONE);
        Diagnostic.addBiDirMapEntry(_permissionsMap, "ADD_VOICEMAIL", Manifest.permission.ADD_VOICEMAIL);
        Diagnostic.addBiDirMapEntry(_permissionsMap, "USE_SIP", Manifest.permission.USE_SIP);
        Diagnostic.addBiDirMapEntry(_permissionsMap, "PROCESS_OUTGOING_CALLS", Manifest.permission.PROCESS_OUTGOING_CALLS);
        Diagnostic.addBiDirMapEntry(_permissionsMap, "SEND_SMS", Manifest.permission.SEND_SMS);
        Diagnostic.addBiDirMapEntry(_permissionsMap, "RECEIVE_SMS", Manifest.permission.RECEIVE_SMS);
        Diagnostic.addBiDirMapEntry(_permissionsMap, "READ_SMS", Manifest.permission.READ_SMS);
        Diagnostic.addBiDirMapEntry(_permissionsMap, "RECEIVE_WAP_PUSH", Manifest.permission.RECEIVE_WAP_PUSH);
        Diagnostic.addBiDirMapEntry(_permissionsMap, "RECEIVE_MMS", Manifest.permission.RECEIVE_MMS);
        Diagnostic.addBiDirMapEntry(_permissionsMap, "WRITE_EXTERNAL_STORAGE", Manifest.permission.WRITE_EXTERNAL_STORAGE);
        Diagnostic.addBiDirMapEntry(_permissionsMap, "READ_CALL_LOG", Manifest.permission.READ_CALL_LOG);
        Diagnostic.addBiDirMapEntry(_permissionsMap, "WRITE_CALL_LOG", Manifest.permission.WRITE_CALL_LOG);
        Diagnostic.addBiDirMapEntry(_permissionsMap, "READ_EXTERNAL_STORAGE", Manifest.permission.READ_EXTERNAL_STORAGE);
        Diagnostic.addBiDirMapEntry(_permissionsMap, "BODY_SENSORS", Manifest.permission.BODY_SENSORS);
        permissionsMap = Collections.unmodifiableMap(_permissionsMap);
    }


    /*
     * Map of permission request code to callback context
     */
    private HashMap<String, CallbackContext> callbackContexts = new HashMap<String, CallbackContext>();

    /*
     * Map of permission request code to permission statuses
     */
    private HashMap<String, JSONObject> permissionStatuses = new HashMap<String, JSONObject>();


    /**
     * User authorised permission
     */
    private static final String STATUS_GRANTED = "GRANTED";

    /**
     * User denied permission (without checking "never ask again")
     */
    private static final String STATUS_DENIED = "DENIED";

    private static String gpsLocationPermission = "ACCESS_FINE_LOCATION";
    private static String networkLocationPermission = "ACCESS_COARSE_LOCATION";
    private static String externalStoragePermission = "READ_EXTERNAL_STORAGE";

    /**
     * Either user denied permission and checked "never ask again"
     * Or authorisation has not yet been requested for permission
     */
    private static final String STATUS_NOT_REQUESTED_OR_DENIED_ALWAYS = "STATUS_NOT_REQUESTED_OR_DENIED_ALWAYS";

    /**
     * Current state of Bluetooth hardware is unknown
     */
    private static final String BLUETOOTH_STATE_UNKNOWN = "unknown";

    /**
     * Current state of Bluetooth hardware is ON
     */
    private static final String BLUETOOTH_STATE_POWERED_ON = "powered_on";

    /**
     * Current state of Bluetooth hardware is OFF
     */
    private static final String BLUETOOTH_STATE_POWERED_OFF = "powered_off";

    /**
     * Current state of Bluetooth hardware is transitioning to ON
     */
    private static final String BLUETOOTH_STATE_POWERING_ON = "powering_on";

    /**
     * Current state of Bluetooth hardware is transitioning to OFF
     */
    private static final String BLUETOOTH_STATE_POWERING_OFF = "powering_off";

    private static final String LOCATION_MODE_HIGH_ACCURACY = "high_accuracy";
    private static final String LOCATION_MODE_DEVICE_ONLY = "device_only";
    private static final String LOCATION_MODE_BATTERY_SAVING = "battery_saving";
    private static final String LOCATION_MODE_OFF = "location_off";
    private static final String LOCATION_MODE_UNKNOWN = "unknown";

    private static final Integer GET_EXTERNAL_SD_CARD_DETAILS_PERMISSION_REQUEST = 1000;

    public static final int NFC_STATE_VALUE_UNKNOWN = 0;
    public static final int NFC_STATE_VALUE_OFF = 1;
    public static final int NFC_STATE_VALUE_TURNING_ON = 2;
    public static final int NFC_STATE_VALUE_ON = 3;
    public static final int NFC_STATE_VALUE_TURNING_OFF = 4;

    public static final String NFC_STATE_UNKNOWN = "unknown";
    public static final String NFC_STATE_OFF = "powered_off";
    public static final String NFC_STATE_TURNING_ON = "powering_on";
    public static final String NFC_STATE_ON = "powered_on";
    public static final String NFC_STATE_TURNING_OFF = "powering_off";

    /*************
     * Variables *
     *************/

    /**
     * Singleton class instance
     */
    public static Diagnostic instance = null;

    public static LocationManager locationManager;

    public static NfcManager nfcManager;

    /**
     * Current Cordova callback context (on this thread)
     */
    protected CallbackContext currentContext;

    private boolean bluetoothListenerInitialized = false;
    private String currentLocationMode = null;
    private String currentNFCState = NFC_STATE_UNKNOWN;

    /*************
     * Public API
     ************/

    /**
     * Constructor.
     */
    public Diagnostic() {}

    /**
     * Sets the context of the Command. This can then be used to do things like
     * get file paths associated with the Activity.
     *
     * @param cordova The context of the main Activity.
     * @param webView The CordovaWebView Cordova is running in.
     */
    public void initialize(CordovaInterface cordova, CordovaWebView webView) {
        Log.d(TAG, "initialize()");
        instance = this;

        locationManager = (LocationManager) this.cordova.getActivity().getSystemService(Context.LOCATION_SERVICE);
        nfcManager = (NfcManager) this.cordova.getActivity().getApplicationContext().getSystemService(Context.NFC_SERVICE);
        currentNFCState = isNFCAvailable() ? NFC_STATE_ON : NFC_STATE_OFF;
        super.initialize(cordova, webView);
    }

    /**
     * Called on destroying activity
     */
    public void onDestroy() {
        try {
            if (bluetoothListenerInitialized) {
                this.cordova.getActivity().unregisterReceiver(blueoothStateChangeReceiver);
            }
        }catch(Exception e){
            Log.w(TAG, "Unable to unregister Bluetooth receiver: " + e.getMessage());
        }
    }

    /**
     * Executes the request and returns PluginResult.
     *
     * @param action            The action to execute.
     * @param args              JSONArry of arguments for the plugin.
     * @param callbackContext   The callback id used when calling back into JavaScript.
     * @return                  True if the action was valid, false if not.
     */
    public boolean execute(String action, JSONArray args, CallbackContext callbackContext) throws JSONException {
        currentContext = callbackContext;

        try {
            if (action.equals("switchToSettings")){
                switchToAppSettings();
                callbackContext.success();
            } else if (action.equals("switchToLocationSettings")){
                switchToLocationSettings();
                callbackContext.success();
            } else if (action.equals("switchToMobileDataSettings")){
                switchToMobileDataSettings();
                callbackContext.success();
            } else if (action.equals("switchToBluetoothSettings")){
                switchToBluetoothSettings();
                callbackContext.success();
            } else if (action.equals("switchToWifiSettings")){
                switchToWifiSettings();
                callbackContext.success();
            } else if (action.equals("switchToWirelessSettings")){
                switchToWirelessSettings();
                callbackContext.success();
            } else if (action.equals("switchToNFCSettings")){
                switchToNFCSettings();
                callbackContext.success();
            } else if(action.equals("isLocationAvailable")) {
                callbackContext.success(isGpsLocationAvailable() || isNetworkLocationAvailable() ? 1 : 0);
            } else if(action.equals("isLocationEnabled")) {
                callbackContext.success(isGpsLocationEnabled() || isNetworkLocationEnabled() ? 1 : 0);
            } else if(action.equals("isGpsLocationAvailable")) {
                callbackContext.success(isGpsLocationAvailable() ? 1 : 0);
            } else if(action.equals("isNetworkLocationAvailable")) {
                callbackContext.success(isNetworkLocationAvailable() ? 1 : 0);
            } else if(action.equals("isGpsLocationEnabled")) {
                callbackContext.success(isGpsLocationEnabled() ? 1 : 0);
            } else if(action.equals("isNetworkLocationEnabled")) {
                callbackContext.success(isNetworkLocationEnabled() ? 1 : 0);
            } else if(action.equals("getLocationMode")) {
                callbackContext.success(getLocationModeName());
            } else if(action.equals("isWifiAvailable")) {
                callbackContext.success(isWifiAvailable() ? 1 : 0);
            } else if(action.equals("isCameraPresent")) {
                callbackContext.success(isCameraPresent() ? 1 : 0);
            } else if(action.equals("isBluetoothAvailable")) {
                callbackContext.success(isBluetoothAvailable() ? 1 : 0);
            }else if(action.equals("isBluetoothEnabled")) {
                callbackContext.success(isBluetoothEnabled() ? 1 : 0);
            } else if(action.equals("hasBluetoothSupport")) {
                callbackContext.success(hasBluetoothSupport() ? 1 : 0);
            } else if(action.equals("hasBluetoothLESupport")) {
                callbackContext.success(hasBluetoothLESupport() ? 1 : 0);
            } else if(action.equals("hasBluetoothLEPeripheralSupport")) {
                callbackContext.success(hasBluetoothLEPeripheralSupport() ? 1 : 0);
            } else if(action.equals("setWifiState")) {
                setWifiState(args.getBoolean(0));
                callbackContext.success();
            } else if(action.equals("setBluetoothState")) {
                setBluetoothState(args.getBoolean(0));
                callbackContext.success();
            } else if(action.equals("getBluetoothState")) {
                callbackContext.success(getBluetoothState());
            } else if(action.equals("initializeBluetoothListener")) {
                initializeBluetoothListener();
                callbackContext.success();
            } else if(action.equals("getPermissionAuthorizationStatus")) {
                this.getPermissionAuthorizationStatus(args);
            } else if(action.equals("getPermissionsAuthorizationStatus")) {
                this.getPermissionsAuthorizationStatus(args);
            } else if(action.equals("requestRuntimePermission")) {
                this.requestRuntimePermission(args);
            } else if(action.equals("requestRuntimePermissions")) {
                this.requestRuntimePermissions(args);
            } else if(action.equals("getExternalSdCardDetails")) {
                this.getExternalSdCardDetails();
            } else if(action.equals("isNFCPresent")) {
                callbackContext.success(isNFCPresent() ? 1 : 0);
            } else if(action.equals("isNFCEnabled")) {
                callbackContext.success(isNFCEnabled() ? 1 : 0);
            } else if(action.equals("isNFCAvailable")) {
                callbackContext.success(isNFCAvailable() ? 1 : 0);
            } else {
                handleError("Invalid action");
                return false;
            }
        }catch(Exception e ) {
            handleError("Exception occurred: ".concat(e.getMessage()));
            return false;
        }
        return true;
    }


    public boolean isGpsLocationAvailable() throws Exception {
        boolean result = isGpsLocationEnabled() && isLocationAuthorized();
        Log.d(TAG, "GPS location available: " + result);
        return result;
    }

    public boolean isGpsLocationEnabled() throws Exception {
        int mode = getLocationMode();
        boolean result = (mode == 3 || mode == 1);
        Log.d(TAG, "GPS location setting enabled: " + result);
        return result;
    }

    public boolean isNetworkLocationAvailable() throws Exception {
        boolean result =  isNetworkLocationEnabled() && isLocationAuthorized();
        Log.d(TAG, "Network location available: " + result);
        return result;
    }

    public boolean isNetworkLocationEnabled() throws Exception {
        int mode = getLocationMode();
        boolean result = (mode == 3 || mode == 2);
        Log.d(TAG, "Network location setting enabled: " + result);
        return result;
    }

    public String getLocationModeName() throws Exception {
        String modeName;
        int mode = getLocationMode();
        switch(mode){
            case Settings.Secure.LOCATION_MODE_HIGH_ACCURACY:
                modeName = LOCATION_MODE_HIGH_ACCURACY;
                break;
            case Settings.Secure.LOCATION_MODE_SENSORS_ONLY:
                modeName = LOCATION_MODE_DEVICE_ONLY;
                break;
            case Settings.Secure.LOCATION_MODE_BATTERY_SAVING:
                modeName = LOCATION_MODE_BATTERY_SAVING;
                break;
            case Settings.Secure.LOCATION_MODE_OFF:
                modeName = LOCATION_MODE_OFF;
                break;
            default:
                modeName = LOCATION_MODE_UNKNOWN;
        }
        currentLocationMode = modeName;
        return modeName;
    }

    public void notifyLocationStateChange(){
        try {
            String currentMode = currentLocationMode;
            String newMode = getLocationModeName();
            if(!newMode.equals(currentMode)){
                Log.d(TAG, "Location mode change to: " + getLocationModeName());
                executeGlobalJavascript("_onLocationStateChange(\"" + getLocationModeName() +"\");");
            }
        }catch(Exception e){
            Log.e(TAG, "Error retrieving current location mode on location state change: "+e.toString());
        }
    }

    public boolean isWifiAvailable() {
        WifiManager wifiManager = (WifiManager) this.cordova.getActivity().getSystemService(Context.WIFI_SERVICE);
        boolean result = wifiManager.isWifiEnabled();
        return result;
    }

    public boolean isCameraPresent() {
        PackageManager pm = this.cordova.getActivity().getPackageManager();
        boolean result = pm.hasSystemFeature(PackageManager.FEATURE_CAMERA);
        return result;
    }

    public boolean isBluetoothAvailable() {
        boolean result = hasBluetoothSupport() && isBluetoothEnabled();
        return result;
    }

    public boolean isBluetoothEnabled() {
        BluetoothAdapter mBluetoothAdapter = BluetoothAdapter.getDefaultAdapter();
        boolean result = mBluetoothAdapter != null && mBluetoothAdapter.isEnabled();
        return result;
    }

    public boolean hasBluetoothSupport() {
        PackageManager pm = this.cordova.getActivity().getPackageManager();
        boolean result = pm.hasSystemFeature(PackageManager.FEATURE_BLUETOOTH);
        return result;
    }

    public boolean hasBluetoothLESupport() {
        PackageManager pm = this.cordova.getActivity().getPackageManager();
        boolean result = pm.hasSystemFeature(PackageManager.FEATURE_BLUETOOTH_LE);
        return result;
    }

    public boolean hasBluetoothLEPeripheralSupport() {
        if (Build.VERSION.SDK_INT >=21){
            BluetoothAdapter mBluetoothAdapter = BluetoothAdapter.getDefaultAdapter();
            boolean result = mBluetoothAdapter != null && mBluetoothAdapter.isMultipleAdvertisementSupported();
            return result;
        }
        return false;
    }
       
    public void switchToAppSettings() {
        Log.d(TAG, "Switch to App Settings");
        Intent appIntent = new Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS);
        Uri uri = Uri.fromParts("package", cordova.getActivity().getPackageName(), null);
        appIntent.setData(uri);
        cordova.getActivity().startActivity(appIntent);
    }

    public void switchToLocationSettings() {
        Log.d(TAG, "Switch to Location Settings");
        Intent settingsIntent = new Intent(Settings.ACTION_LOCATION_SOURCE_SETTINGS);
        cordova.getActivity().startActivity(settingsIntent);
    }

    public void switchToMobileDataSettings() {
        Log.d(TAG, "Switch to Mobile Data Settings");
        Intent settingsIntent = new Intent(Settings.ACTION_DATA_ROAMING_SETTINGS);
        cordova.getActivity().startActivity(settingsIntent);
    }

    public void switchToBluetoothSettings() {
        Log.d(TAG, "Switch to Bluetooth Settings");
        Intent settingsIntent = new Intent(Settings.ACTION_BLUETOOTH_SETTINGS);
        cordova.getActivity().startActivity(settingsIntent);
    }

    public void switchToWifiSettings() {
        Log.d(TAG, "Switch to Wifi Settings");
        Intent settingsIntent = new Intent(Settings.ACTION_WIFI_SETTINGS);
        cordova.getActivity().startActivity(settingsIntent);
    }

    public void switchToWirelessSettings() {
        Log.d(TAG, "Switch to wireless Settings");
        Intent settingsIntent = new Intent(Settings.ACTION_WIRELESS_SETTINGS);
        cordova.getActivity().startActivity(settingsIntent);
    }
    public void switchToNFCSettings() {
        Log.d(TAG, "Switch to NFC Settings");
        Intent settingsIntent = new Intent(Settings.ACTION_WIRELESS_SETTINGS);
        if (android.os.Build.VERSION.SDK_INT >= 16) {
            settingsIntent = new Intent(android.provider.Settings.ACTION_NFC_SETTINGS);
        }
        cordova.getActivity().startActivity(settingsIntent);
    }

    public void setWifiState(boolean enable) {
        WifiManager wifiManager = (WifiManager) this.cordova.getActivity().getSystemService(Context.WIFI_SERVICE);
        if (enable && !wifiManager.isWifiEnabled()) {
            wifiManager.setWifiEnabled(true);
        } else if (!enable && wifiManager.isWifiEnabled()) {
            wifiManager.setWifiEnabled(false);
        }
    }

    public static boolean setBluetoothState(boolean enable) {
        BluetoothAdapter bluetoothAdapter = BluetoothAdapter.getDefaultAdapter();
        boolean isEnabled = bluetoothAdapter.isEnabled();
        if (enable && !isEnabled) {
            return bluetoothAdapter.enable();
        }
        else if(!enable && isEnabled) {
            return bluetoothAdapter.disable();
        }
        return true;
    }

    public String getBluetoothState(){

        String bluetoothState = BLUETOOTH_STATE_UNKNOWN;
        if(hasBluetoothSupport()){
            BluetoothAdapter mBluetoothAdapter = BluetoothAdapter.getDefaultAdapter();
            int state = mBluetoothAdapter.getState();
            switch(state){
                case BluetoothAdapter.STATE_OFF:
                    bluetoothState = BLUETOOTH_STATE_POWERED_OFF;
                    break;
                case BluetoothAdapter.STATE_ON:
                    bluetoothState = BLUETOOTH_STATE_POWERED_ON;
                    break;
                case BluetoothAdapter.STATE_TURNING_OFF:
                    bluetoothState = BLUETOOTH_STATE_POWERING_OFF;
                    break;
                case BluetoothAdapter.STATE_TURNING_ON:
                    bluetoothState = BLUETOOTH_STATE_POWERING_ON;
                    break;
            }
        }
        return bluetoothState;
    }

    public void getPermissionsAuthorizationStatus(JSONArray args) throws Exception{
        JSONArray permissions = args.getJSONArray(0);
        JSONObject statuses = _getPermissionsAuthorizationStatus(jsonArrayToStringArray(permissions));
        currentContext.success(statuses);
    }

    public void getPermissionAuthorizationStatus(JSONArray args) throws Exception{
        String permission = args.getString(0);
        JSONArray permissions = new JSONArray();
        permissions.put(permission);
        JSONObject statuses = _getPermissionsAuthorizationStatus(jsonArrayToStringArray(permissions));
        currentContext.success(statuses.getString(permission));
    }

    public void requestRuntimePermissions(JSONArray args) throws Exception{
        JSONArray permissions = args.getJSONArray(0);
        int requestId = storeContextByRequestId();
        _requestRuntimePermissions(permissions, requestId);
    }

    public void requestRuntimePermission(JSONArray args) throws Exception{
        requestRuntimePermission(args.getString(0));
    }

    public void requestRuntimePermission(String permission) throws Exception{
        requestRuntimePermission(permission, storeContextByRequestId());
    }

    public void requestRuntimePermission(String permission, int requestId) throws Exception{
        JSONArray permissions = new JSONArray();
        permissions.put(permission);
        _requestRuntimePermissions(permissions, requestId);
    }

    public void getExternalSdCardDetails() throws Exception{
        String permission = permissionsMap.get(externalStoragePermission);
        if (hasPermission(permission)) {
            _getExternalSdCardDetails();
        } else {
            requestRuntimePermission(permission, GET_EXTERNAL_SD_CARD_DETAILS_PERMISSION_REQUEST);
        }
    }

    public boolean isNFCPresent() {
        boolean result = false;
        try {
            NfcAdapter adapter = nfcManager.getDefaultAdapter();
            result = adapter != null;
        }catch(Exception e){
            Log.e(TAG, e.getMessage());
        }
        return result;
    }

    public boolean isNFCEnabled() {
        boolean result = false;
        try {
            NfcAdapter adapter = nfcManager.getDefaultAdapter();
            result = adapter != null && adapter.isEnabled();
        }catch(Exception e){
            Log.e(TAG, e.getMessage());
        }
        return result;
    }

    public boolean isNFCAvailable() {
        boolean result = isNFCPresent() && isNFCEnabled();
        return result;
    }

    public void notifyNFCStateChange(String state){
        try {
            if(state != currentNFCState){
                Log.d(TAG, "NFC state changed to: " + state);
                executeGlobalJavascript("_onNFCStateChange(\"" + state +"\");");
                currentNFCState = state;
            }
        }catch(Exception e){
            Log.e(TAG, "Error retrieving current NFC state on state change: "+e.toString());
        }
    }


    /************
     * Internals
     ***********/
    /**
     * Handles an error while executing a plugin API method  in the specified context.
     * Calls the registered Javascript plugin error handler callback.
     * @param errorMsg Error message to pass to the JS error handler
     */
    private void handleError(String errorMsg, CallbackContext context){
        try {
            Log.e(TAG, errorMsg);
            context.error(errorMsg);
        } catch (Exception e) {
            Log.e(TAG, e.toString());
        }
    }

    /**
     * Handles an error while executing a plugin API method in the current context.
     * Calls the registered Javascript plugin error handler callback.
     * @param errorMsg Error message to pass to the JS error handler
     */
    private void handleError(String errorMsg) {
        handleError(errorMsg, currentContext);
    }

    /**
     * Handles error during a runtime permissions request.
     * Calls the registered Javascript plugin error handler callback
     * then removes entries associated with the request ID.
     * @param errorMsg Error message to pass to the JS error handler
     * @param requestId The ID of the runtime request
     */
    private void handleError(String errorMsg, int requestId){
        CallbackContext context;
        String sRequestId = String.valueOf(requestId);
        if (callbackContexts.containsKey(sRequestId)) {
            context = callbackContexts.get(sRequestId);
        }else{
            context = currentContext;
        }
        handleError(errorMsg, context);
        clearRequest(requestId);
    }

    /**
     * Returns current location mode
     */
    private int getLocationMode() throws Exception {
        int mode;
        if (Build.VERSION.SDK_INT >= 19){ // Kitkat and above
            mode = Settings.Secure.getInt(this.cordova.getActivity().getContentResolver(), Settings.Secure.LOCATION_MODE);
        }else{ // Pre-Kitkat
            if(isLocationProviderEnabled(LocationManager.GPS_PROVIDER) && isLocationProviderEnabled(LocationManager.NETWORK_PROVIDER)){
                mode = 3;
            } else if(isLocationProviderEnabled(LocationManager.GPS_PROVIDER)){
                mode = 1;
            } else if(isLocationProviderEnabled(LocationManager.NETWORK_PROVIDER)){
                mode = 2;
            }else{
                mode = 0;
            }
        }
        return mode;
    }

    private boolean isLocationAuthorized() throws Exception {
        boolean authorized = hasPermission(permissionsMap.get(gpsLocationPermission)) || hasPermission(permissionsMap.get(networkLocationPermission));
        Log.v(TAG, "Location permission is "+(authorized ? "authorized" : "unauthorized"));
        return authorized;
    }

    private boolean isLocationProviderEnabled(String provider) {
        return locationManager.isProviderEnabled(provider);
    }

    private void initializeBluetoothListener(){
        if(!bluetoothListenerInitialized){
            this.cordova.getActivity().registerReceiver(blueoothStateChangeReceiver, new IntentFilter(BluetoothAdapter.ACTION_STATE_CHANGED));
            bluetoothListenerInitialized = true;
        }
    }


    private JSONObject _getPermissionsAuthorizationStatus(String[] permissions) throws Exception{
        JSONObject statuses = new JSONObject();
        for(int i=0; i<permissions.length; i++){
            String permission = permissions[i];
            if(!permissionsMap.containsKey(permission)){
                throw new Exception("Permission name '"+permission+"' is not a valid permission");
            }
            String androidPermission = permissionsMap.get(permission);
            Log.v(TAG, "Get authorisation status for "+androidPermission);
            boolean granted = hasPermission(androidPermission);
            if(granted){
                statuses.put(permission, Diagnostic.STATUS_GRANTED);
            }else{
                boolean showRationale = shouldShowRequestPermissionRationale(this.cordova.getActivity(), androidPermission);
                if(!showRationale){
                    statuses.put(permission, Diagnostic.STATUS_NOT_REQUESTED_OR_DENIED_ALWAYS);
                }else{
                    statuses.put(permission, Diagnostic.STATUS_DENIED);
                }
            }
        }
        return statuses;
    }

    private void _requestRuntimePermissions(JSONArray permissions, int requestId) throws Exception{
        JSONObject currentPermissionsStatuses = _getPermissionsAuthorizationStatus(jsonArrayToStringArray(permissions));
        JSONArray permissionsToRequest = new JSONArray();
        for(int i = 0; i<currentPermissionsStatuses.names().length(); i++){
            String permission = currentPermissionsStatuses.names().getString(i);
            boolean granted = currentPermissionsStatuses.getString(permission) == Diagnostic.STATUS_GRANTED;
            if(granted){
                Log.d(TAG, "Permission already granted for "+permission);
                JSONObject requestStatuses = permissionStatuses.get(String.valueOf(requestId));
                requestStatuses.put(permission, Diagnostic.STATUS_GRANTED);
                permissionStatuses.put(String.valueOf(requestId), requestStatuses);
            }else{
                String androidPermission = permissionsMap.get(permission);
                Log.d(TAG, "Requesting permission for "+androidPermission);
                permissionsToRequest.put(androidPermission);
            }
        }
        if(permissionsToRequest.length() > 0){
            Log.v(TAG, "Requesting permissions");
            requestPermissions(this, requestId, jsonArrayToStringArray(permissionsToRequest));

        }else{
            Log.d(TAG, "No permissions to request: returning result");
            sendRuntimeRequestResult(requestId);
        }
    }

    private void sendRuntimeRequestResult(int requestId){
        String sRequestId = String.valueOf(requestId);
        CallbackContext context = callbackContexts.get(sRequestId);
        JSONObject statuses = permissionStatuses.get(sRequestId);
        Log.v(TAG, "Sending runtime request result for id="+sRequestId);
        context.success(statuses);
    }

    private int storeContextByRequestId(){
        String requestId = generateRandomRequestId();
        callbackContexts.put(requestId, currentContext);
        permissionStatuses.put(requestId, new JSONObject());
        return Integer.valueOf(requestId);
    }

    private String generateRandomRequestId(){
        String requestId = null;

        while(requestId == null){
            requestId = generateRandom();
            if(callbackContexts.containsKey(requestId)){
                requestId = null;
            }
        }
        return requestId;
    }

    private String generateRandom(){
        Random rn = new Random();
        int random = rn.nextInt(1000000) + 1;
        return Integer.toString(random);
    }

    private String[] jsonArrayToStringArray(JSONArray array) throws JSONException{
        if(array==null)
            return null;

        String[] arr=new String[array.length()];
        for(int i=0; i<arr.length; i++) {
            arr[i]=array.optString(i);
        }
        return arr;
    }

    private CallbackContext getContextById(String requestId) throws Exception{
        if (!callbackContexts.containsKey(requestId)) {
            throw new Exception("No context found for request id=" + requestId);
        }
        return callbackContexts.get(requestId);
    }

    private void clearRequest(int requestId){
        String sRequestId = String.valueOf(requestId);
        if (!callbackContexts.containsKey(sRequestId)) {
            return;
        }
        callbackContexts.remove(sRequestId);
        permissionStatuses.remove(sRequestId);
    }

    /**
     * Adds a bi-directional entry to a map in the form on 2 entries: key>value and value>key
     * @param map
     * @param key
     * @param value
     */
    private static void addBiDirMapEntry(Map map, Object key, Object value){
        map.put(key, value);
        map.put(value, key);
    }

    private boolean hasPermission(String permission) throws Exception{
        boolean hasPermission = true;
        Method method = null;
        try {
            method = cordova.getClass().getMethod("hasPermission", permission.getClass());
            Boolean bool = (Boolean) method.invoke(cordova, permission);
            hasPermission = bool.booleanValue();
        } catch (NoSuchMethodException e) {
            Log.w(TAG, "Cordova v" + CordovaWebView.CORDOVA_VERSION + " does not support runtime permissions so defaulting to GRANTED for " + permission);
        }
        return hasPermission;
    }

    private void requestPermissions(CordovaPlugin plugin, int requestCode, String [] permissions) throws Exception{
        try {
            java.lang.reflect.Method method = cordova.getClass().getMethod("requestPermissions", org.apache.cordova.CordovaPlugin.class ,int.class, java.lang.String[].class);
            method.invoke(cordova, plugin, requestCode, permissions);
        } catch (NoSuchMethodException e) {
            throw new Exception("requestPermissions() method not found in CordovaInterface implementation of Cordova v" + CordovaWebView.CORDOVA_VERSION);
        }
    }

    private boolean shouldShowRequestPermissionRationale(Activity activity, String permission) throws Exception{
        boolean shouldShow;
        try {
            java.lang.reflect.Method method = ActivityCompat.class.getMethod("shouldShowRequestPermissionRationale", Activity.class, java.lang.String.class);
            Boolean bool = (Boolean) method.invoke(null, activity, permission);
            shouldShow = bool.booleanValue();
        } catch (NoSuchMethodException e) {
            throw new Exception("shouldShowRequestPermissionRationale() method not found in ActivityCompat class. Check you have Android Support Library v23+ installed");
        }
        return shouldShow;
    }

    public void executeGlobalJavascript(final String jsString){
        cordova.getActivity().runOnUiThread(new Runnable() {
            @Override
            public void run() {
                webView.loadUrl("javascript:cordova.plugins.diagnostic." + jsString);
            }
        });
    }

    protected void _getExternalSdCardDetails() throws JSONException {
        String[] storageDirectories = getStorageDirectories();

        JSONArray details = new JSONArray();
        for(int i=0; i<storageDirectories.length; i++) {
            String directory = storageDirectories[i];
            File f = new File(directory);
            JSONObject detail = new JSONObject();
            if(f.canRead()){
                detail.put("path", directory);
                detail.put("filePath", "file://"+directory);
                detail.put("canWrite", f.canWrite());
                detail.put("freeSpace", getFreeSpaceInBytes(directory));
                if(directory.contains("Android")){
                    detail.put("type", "application");
                }else{
                    detail.put("type", "root");
                }
                details.put(detail);
            }
        }
        currentContext.success(details);
    }

    /**
     * Given a path return the number of free bytes in the filesystem containing the path.
     *
     * @param path to the file system
     * @return free space in bytes
     */
    private long getFreeSpaceInBytes(String path) {
        try {
            StatFs stat = new StatFs(path);
            long blockSize = stat.getBlockSize();
            long availableBlocks = stat.getAvailableBlocks();
            return availableBlocks * blockSize;
        } catch (IllegalArgumentException e) {
            // The path was invalid. Just return 0 free bytes.
            return 0;
        }
    }


    /**
     * Returns all available external SD-Cards in the system.
     *
     * @return paths to all available external SD-Cards in the system.
     */
    public String[] getStorageDirectories() {

        List<String> results = new ArrayList<String>();

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.KITKAT) { //Method 1 for KitKat & above
            File[] externalDirs = this.cordova.getActivity().getApplicationContext().getExternalFilesDirs(null);

            for (File file : externalDirs) {
                if(file == null){
                    continue;
                }
                String applicationPath = file.getPath();
                String rootPath = applicationPath.split("/Android")[0];

                boolean addPath = false;

                if(Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
                    addPath = Environment.isExternalStorageRemovable(file);
                }
                else{
                    addPath = Environment.MEDIA_MOUNTED.equals(EnvironmentCompat.getStorageState(file));
                }

                if(addPath){
                    results.add(rootPath);
                    results.add(applicationPath);
                }
            }
        }

        if(results.isEmpty()) { //Method 2 for all versions
            // better variation of: http://stackoverflow.com/a/40123073/5002496
            String output = "";
            try {
                final Process process = new ProcessBuilder().command("mount | grep /dev/block/vold")
                        .redirectErrorStream(true).start();
                process.waitFor();
                final InputStream is = process.getInputStream();
                final byte[] buffer = new byte[1024];
                while (is.read(buffer) != -1) {
                    output = output + new String(buffer);
                }
                is.close();
            } catch (final Exception e) {
                e.printStackTrace();
            }
            if(!output.trim().isEmpty()) {
                String devicePoints[] = output.split("\n");
                for(String voldPoint: devicePoints) {
                    results.add(voldPoint.split(" ")[2]);
                }
            }
        }

        //Below few lines is to remove paths which may not be external memory card, like OTG (feel free to comment them out)
        if(Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            for (int i = 0; i < results.size(); i++) {
                if (!results.get(i).toLowerCase().matches(".*[0-9a-f]{4}[-][0-9a-f]{4}.*")) {
                    Log.d(TAG, results.get(i) + " might not be extSDcard");
                    results.remove(i--);
                }
            }
        } else {
            for (int i = 0; i < results.size(); i++) {
                if (!results.get(i).toLowerCase().contains("ext") && !results.get(i).toLowerCase().contains("sdcard")) {
                    Log.d(TAG, results.get(i)+" might not be extSDcard");
                    results.remove(i--);
                }
            }
        }

        String[] storageDirectories = new String[results.size()];
        for(int i=0; i<results.size(); ++i) storageDirectories[i] = results.get(i);

        return storageDirectories;
    }

    /************
     * Overrides
     ***********/

    /**
     * Callback received when a runtime permissions request has been completed.
     * Retrieves the stateful Cordova context and permission statuses associated with the requestId,
     * then updates the list of status based on the grantResults before passing the result back via the context.
     *
     * @param requestCode - ID that was used when requesting permissions
     * @param permissions - list of permissions that were requested
     * @param grantResults - list of flags indicating if above permissions were granted or denied
     */
    public void onRequestPermissionResult(int requestCode, String[] permissions, int[] grantResults) throws JSONException {
        String sRequestId = String.valueOf(requestCode);
        Log.v(TAG, "Received result for permissions request id=" + sRequestId);
        try {

            CallbackContext context = getContextById(sRequestId);
            JSONObject statuses = permissionStatuses.get(sRequestId);

            for (int i = 0, len = permissions.length; i < len; i++) {
                String androidPermission = permissions[i];
                String permission = permissionsMap.get(androidPermission);
                String status;
                if (grantResults[i] == PackageManager.PERMISSION_DENIED) {
                    boolean showRationale = shouldShowRequestPermissionRationale(this.cordova.getActivity(), androidPermission);
                    if (!showRationale) {
                        // EITHER: The app doesn't have a permission and the user has not been asked for the permission before
                        // OR: user denied WITH "never ask again"
                        status = Diagnostic.STATUS_NOT_REQUESTED_OR_DENIED_ALWAYS;
                    } else {
                        // user denied WITHOUT "never ask again"
                        status = Diagnostic.STATUS_DENIED;
                    }
                } else {
                    // Permission granted
                    status = Diagnostic.STATUS_GRANTED;
                }
                statuses.put(permission, status);
                Log.v(TAG, "Authorisation for " + permission + " is " + statuses.get(permission));
                clearRequest(requestCode);
            }

            if(requestCode == GET_EXTERNAL_SD_CARD_DETAILS_PERMISSION_REQUEST){
                _getExternalSdCardDetails();
            }else{
                context.success(statuses);
            }
        }catch(Exception e ) {
            handleError("Exception occurred onRequestPermissionsResult: ".concat(e.getMessage()), requestCode);
        }
    }

    private final BroadcastReceiver blueoothStateChangeReceiver = new BroadcastReceiver() {
        @Override
        public void onReceive(Context context, Intent intent) {
            final String action = intent.getAction();
            String bluetoothState;

            if (action.equals(BluetoothAdapter.ACTION_STATE_CHANGED)) {
                final int state = intent.getIntExtra(BluetoothAdapter.EXTRA_STATE,
                        BluetoothAdapter.ERROR);
                switch (state) {
                    case BluetoothAdapter.STATE_OFF:
                        bluetoothState = BLUETOOTH_STATE_POWERED_OFF;
                        break;
                    case BluetoothAdapter.STATE_TURNING_OFF:
                        bluetoothState = BLUETOOTH_STATE_POWERING_OFF;
                        break;
                    case BluetoothAdapter.STATE_ON:
                        bluetoothState = BLUETOOTH_STATE_POWERED_ON;
                        break;
                    case BluetoothAdapter.STATE_TURNING_ON:
                        bluetoothState = BLUETOOTH_STATE_POWERING_ON;
                        break;
                    default:
                        bluetoothState = BLUETOOTH_STATE_UNKNOWN;
                }
                instance.executeGlobalJavascript("_onBluetoothStateChange(\""+bluetoothState+"\");");
            }
        }
    };

    public static class LocationProviderChangedReceiver extends BroadcastReceiver{

        @Override
        public void onReceive(Context context, Intent intent) {
            if(instance != null){ // if app is running
                Log.v(TAG, "onReceiveLocationProviderChange");
                instance.notifyLocationStateChange();
            }
        }

    }

    public static class NFCStateChangedReceiver extends BroadcastReceiver{

        @Override
        public void onReceive(Context context, Intent intent) {
            final int stateValue = intent.getIntExtra(EXTRA_ADAPTER_STATE, -1);
            if(instance != null){ // if app is running
                String state;
                switch(stateValue){
                    case NFC_STATE_VALUE_OFF:
                        state = NFC_STATE_OFF;
                        break;
                    case NFC_STATE_VALUE_TURNING_ON:
                        state = NFC_STATE_TURNING_ON;
                        break;
                    case NFC_STATE_VALUE_ON:
                        state = NFC_STATE_ON;
                        break;
                    case NFC_STATE_VALUE_TURNING_OFF:
                        state = NFC_STATE_TURNING_OFF;
                        break;
                    default:
                        state = NFC_STATE_UNKNOWN;
                }
                Log.v(TAG, "onReceiveNFCStateChange: "+state);
                instance.notifyNFCStateChange(state);
            }
        }

    }
}
