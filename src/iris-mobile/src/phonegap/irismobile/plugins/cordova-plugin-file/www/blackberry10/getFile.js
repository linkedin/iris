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

/* 
 * getFile
 *
 * IN:
 *  args
 *   0 - local filesytem URI for the base directory to search
 *   1 - file to be created/returned; may be absolute path or relative path
 *   2 - options object
 * OUT:
 *  success - FileEntry
 *  fail - FileError code
 */

var resolve = cordova.require('cordova-plugin-file.resolveLocalFileSystemURIProxy');

module.exports = function (success, fail, args) {
    var uri = args[0] === "/" ? "" : args[0] + "/" + args[1],
        options = args[2],
        onSuccess = function (entry) {
            if (typeof(success) === 'function') {
                success(entry);
            }
        },
        onFail = function (code) {
            if (typeof(fail) === 'function') {
                fail(code);
            }
        };
    resolve(function (entry) {
        if (!entry.isFile) {
            onFail(FileError.TYPE_MISMATCH_ERR);
        } else {
            onSuccess(entry);
        }
    }, onFail, [uri, options]);
};
