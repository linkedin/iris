/*
 *
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 *
*/

/* global PluginResult */

var _clientListeners = {},
    _webkitBattery = navigator.webkitBattery || navigator.battery;

module.exports = {
    start: function (success, fail, args, env) {
        var result = new PluginResult(args, env),
            listener = function (info) {
                var resultInfo = {};
                if (info) {
                    if (info.srcElement) {
                        //webkitBattery listeners store webkitBattery in srcElement object
                        info = info.srcElement;
                    }

                    //put data from webkitBattery into a format cordova expects
                    //webkitBattery seems to return level as a decimal pre 10.2
                    resultInfo.level = info.level <= 1 ? info.level * 100 : info.level;
                    resultInfo.isPlugged = info.charging;
                }

                result.callbackOk(resultInfo, true);
            };

        if (_clientListeners[env.webview.id]) {
            //TODO: Change back to erroring out after reset is implemented
            //result.error("Battery listener already running");
            _webkitBattery.onchargingchange = null;
            _webkitBattery.onlevelchange = null;
        }

        _clientListeners[env.webview.id] = listener;

        _webkitBattery.onchargingchange = listener;
        _webkitBattery.onlevelchange = listener;

        setTimeout(function(){
            //Call callback with webkitBattery data right away
            listener(_webkitBattery);
        });

        result.noResult(true);
    },
    stop: function (success, fail, args, env) {
        var result = new PluginResult(args, env),
            listener = _clientListeners[env.webview.id];

        if (!listener) {
            result.error("Battery listener has not started");
        } else {
            _webkitBattery.onchargingchange = null;
            _webkitBattery.onlevelchange = null;
            delete _clientListeners[env.webview.id];
            result.noResult(false);
        }
    }
};
