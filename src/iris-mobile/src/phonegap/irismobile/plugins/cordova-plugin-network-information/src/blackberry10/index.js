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

//map from BB10 to cordova connection types:
//https://github.com/apache/cordova-js/blob/master/lib/common/plugin/Connection.js
function mapConnectionType(con) {
    switch (con.type) {
    case 'wired':
        return 'ethernet';
    case 'wifi':
        return 'wifi';
    case 'none':
        return 'none';
    case 'cellular':
        switch (con.technology) {
        case 'edge':
        case 'gsm':
            return '2g';
        case 'evdo':
            return '3g';
        case 'umts':
            return '3g';
        case 'lte':
            return '4g';
        }
        return "cellular";
    }
    return 'unknown';
}

function currentConnectionType() {
    try {
        //possible for webplatform to throw pps exception
        return mapConnectionType(window.qnx.webplatform.device.activeConnection || { type : 'none' });
    }
    catch (e) {
        return 'unknown';
    }
}

module.exports = {
    getConnectionInfo: function (success, fail, args, env) {
        var result = new PluginResult(args, env);
        result.ok(currentConnectionType());
    }
};
