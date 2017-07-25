/*
 * Copyright 2013 Research In Motion Limited.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

/* global PluginResult */

module.exports = {
    show: function (success, fail, args, env) {
        var result = new PluginResult(args, env);
        result.error("Not supported on platform", false);
    },

    hide: function (success, fail, args, env) {
        var result = new PluginResult(args, env);
        window.qnx.webplatform.getApplication().windowVisible = true;
        result.ok(undefined, false);
    }
};
