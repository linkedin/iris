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
package org.apache.cordova.networkinformation;

import org.apache.cordova.CallbackContext;
import org.apache.cordova.CordovaInterface;
import org.apache.cordova.CordovaPlugin;
import org.apache.cordova.PluginResult;
import org.apache.cordova.CordovaWebView;
import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.net.ConnectivityManager;
import android.net.NetworkInfo;
import android.util.Log;

import java.util.Locale;

public class NetworkManager extends CordovaPlugin {

    public static int NOT_REACHABLE = 0;
    public static int REACHABLE_VIA_CARRIER_DATA_NETWORK = 1;
    public static int REACHABLE_VIA_WIFI_NETWORK = 2;

    public static final String WIFI = "wifi";
    public static final String WIMAX = "wimax";
    // mobile
    public static final String MOBILE = "mobile";
    
    // Android L calls this Cellular, because I have no idea! 
    public static final String CELLULAR = "cellular";
    // 2G network types
    public static final String GSM = "gsm";
    public static final String GPRS = "gprs";
    public static final String EDGE = "edge";
    // 3G network types
    public static final String CDMA = "cdma";
    public static final String UMTS = "umts";
    public static final String HSPA = "hspa";
    public static final String HSUPA = "hsupa";
    public static final String HSDPA = "hsdpa";
    public static final String ONEXRTT = "1xrtt";
    public static final String EHRPD = "ehrpd";
    // 4G network types
    public static final String LTE = "lte";
    public static final String UMB = "umb";
    public static final String HSPA_PLUS = "hspa+";
    // return type
    public static final String TYPE_UNKNOWN = "unknown";
    public static final String TYPE_ETHERNET = "ethernet";
    public static final String TYPE_WIFI = "wifi";
    public static final String TYPE_2G = "2g";
    public static final String TYPE_3G = "3g";
    public static final String TYPE_4G = "4g";
    public static final String TYPE_NONE = "none";

    private static final String LOG_TAG = "NetworkManager";

    private CallbackContext connectionCallbackContext;

    ConnectivityManager sockMan;
    BroadcastReceiver receiver;
    private JSONObject lastInfo = null;

    /**
     * Sets the context of the Command. This can then be used to do things like
     * get file paths associated with the Activity.
     *
     * @param cordova The context of the main Activity.
     * @param webView The CordovaWebView Cordova is running in.
     */
    public void initialize(CordovaInterface cordova, CordovaWebView webView) {
        super.initialize(cordova, webView);
        this.sockMan = (ConnectivityManager) cordova.getActivity().getSystemService(Context.CONNECTIVITY_SERVICE);
        this.connectionCallbackContext = null;

        // We need to listen to connectivity events to update navigator.connection
        IntentFilter intentFilter = new IntentFilter();
        intentFilter.addAction(ConnectivityManager.CONNECTIVITY_ACTION);
        if (this.receiver == null) {
            this.receiver = new BroadcastReceiver() {
                @Override
                public void onReceive(Context context, Intent intent) {
                    // (The null check is for the ARM Emulator, please use Intel Emulator for better results)
                    if(NetworkManager.this.webView != null)
                        updateConnectionInfo(sockMan.getActiveNetworkInfo());
                }
            };
            webView.getContext().registerReceiver(this.receiver, intentFilter);
        }

    }

    /**
     * Executes the request and returns PluginResult.
     *
     * @param action            The action to execute.
     * @param args              JSONArry of arguments for the plugin.
     * @param callbackContext   The callback id used when calling back into JavaScript.
     * @return                  True if the action was valid, false otherwise.
     */
    public boolean execute(String action, JSONArray args, CallbackContext callbackContext) {
        if (action.equals("getConnectionInfo")) {
            this.connectionCallbackContext = callbackContext;
            NetworkInfo info = sockMan.getActiveNetworkInfo();
            String connectionType = "";
            try {
                connectionType = this.getConnectionInfo(info).get("type").toString();
            } catch (JSONException e) { }

            PluginResult pluginResult = new PluginResult(PluginResult.Status.OK, connectionType);
            pluginResult.setKeepCallback(true);
            callbackContext.sendPluginResult(pluginResult);
            return true;
        }
        return false;
    }

    /**
     * Stop network receiver.
     */
    public void onDestroy() {
        if (this.receiver != null) {
            try {
                webView.getContext().unregisterReceiver(this.receiver);
            } catch (Exception e) {
                Log.e(LOG_TAG, "Error unregistering network receiver: " + e.getMessage(), e);
            } finally {
                receiver = null;
            }
        }
    }

    //--------------------------------------------------------------------------
    // LOCAL METHODS
    //--------------------------------------------------------------------------

    /**
     * Updates the JavaScript side whenever the connection changes
     *
     * @param info the current active network info
     * @return
     */
    private void updateConnectionInfo(NetworkInfo info) {
        // send update to javascript "navigator.network.connection"
        // Jellybean sends its own info
        JSONObject thisInfo = this.getConnectionInfo(info);
        if(!thisInfo.equals(lastInfo))
        {
            String connectionType = "";
            try {
                connectionType = thisInfo.get("type").toString();
            } catch (JSONException e) { }

            sendUpdate(connectionType);
            lastInfo = thisInfo;
        }
    }

    /**
     * Get the latest network connection information
     *
     * @param info the current active network info
     * @return a JSONObject that represents the network info
     */
    private JSONObject getConnectionInfo(NetworkInfo info) {
        String type = TYPE_NONE;
        String extraInfo = "";
        if (info != null) {
            // If we are not connected to any network set type to none
            if (!info.isConnected()) {
                type = TYPE_NONE;
            }
            else {
                type = getType(info);
            }
            extraInfo = info.getExtraInfo();
        }

        Log.d("CordovaNetworkManager", "Connection Type: " + type);
        Log.d("CordovaNetworkManager", "Connection Extra Info: " + extraInfo);

        JSONObject connectionInfo = new JSONObject();

        try {
            connectionInfo.put("type", type);
            connectionInfo.put("extraInfo", extraInfo);
        } catch (JSONException e) { }

        return connectionInfo;
    }

    /**
     * Create a new plugin result and send it back to JavaScript
     *
     * @param connection the network info to set as navigator.connection
     */
    private void sendUpdate(String type) {
        if (connectionCallbackContext != null) {
            PluginResult result = new PluginResult(PluginResult.Status.OK, type);
            result.setKeepCallback(true);
            connectionCallbackContext.sendPluginResult(result);
        }
        webView.postMessage("networkconnection", type);
    }

    /**
     * Determine the type of connection
     *
     * @param info the network info so we can determine connection type.
     * @return the type of mobile network we are on
     */
    private String getType(NetworkInfo info) {
        if (info != null) {
            String type = info.getTypeName().toLowerCase(Locale.US);

            Log.d("CordovaNetworkManager", "toLower : " + type.toLowerCase());
            Log.d("CordovaNetworkManager", "wifi : " + WIFI);
            if (type.equals(WIFI)) {
                return TYPE_WIFI;
            }
            else if (type.toLowerCase().equals(TYPE_ETHERNET)) { 
                return TYPE_ETHERNET;
            }
            else if (type.equals(MOBILE) || type.equals(CELLULAR)) {
                type = info.getSubtypeName().toLowerCase(Locale.US);
                if (type.equals(GSM) ||
                        type.equals(GPRS) ||
                        type.equals(EDGE)) {
                    return TYPE_2G;
                }
                else if (type.startsWith(CDMA) ||
                        type.equals(UMTS) ||
                        type.equals(ONEXRTT) ||
                        type.equals(EHRPD) ||
                        type.equals(HSUPA) ||
                        type.equals(HSDPA) ||
                        type.equals(HSPA)) {
                    return TYPE_3G;
                }
                else if (type.equals(LTE) ||
                        type.equals(UMB) ||
                        type.equals(HSPA_PLUS)) {
                    return TYPE_4G;
                }
            }
        }
        else {
            return TYPE_NONE;
        }
        return TYPE_UNKNOWN;
    }
}
