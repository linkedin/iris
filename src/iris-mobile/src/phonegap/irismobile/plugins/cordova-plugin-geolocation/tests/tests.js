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
exports.defineAutoTests = function () {
    var fail = function (done, context, message) {
        // prevents done() to be called several times
        if (context) {
            if (context.done) return;
            context.done = true;
        }

        if (message) {
            expect(false).toBe(true, message);
        } else {
            expect(false).toBe(true);
        }

        // watchPosition could call its callback sync (before returning the value)
        // so we invoke done async to make sure we know watcher id to .clear in afterEach
        setTimeout(function () {
            done();
        });
    };
    
    var succeed = function (done, context) {
        // prevents done() to be called several times
        if (context) {
            if (context.done) return;
            context.done = true;
        }

        expect(true).toBe(true);

        // watchPosition could call its callback sync (before returning the value)
        // so we invoke done async to make sure we know watcher id to .clear in afterEach
        setTimeout(function () {
            done();
        });
    };

    // On Windows, some tests prompt user for permission to use geolocation and interrupt autotests run
    var isWindowsStore = (cordova.platformId == "windows8") || (cordova.platformId == "windows" && !WinJS.Utilities.isPhone);
    var majorDeviceVersion = null;
    var versionRegex = /(\d)\..+/.exec(device.version);
    if (versionRegex !== null) {
        majorDeviceVersion = Number(versionRegex[1]);
    }
    // Starting from Android 6.0 there are confirmation dialog which prevents us from running auto tests in silent mode (user interaction needed)
    // Also, Android emulator doesn't provide geo fix without manual interactions or mocks
    var skipAndroid = cordova.platformId == "android" && (device.isVirtual || majorDeviceVersion >= 6);
    var isIOSSim = false; // if iOS simulator does not have a location set, it will fail.


    describe('Geolocation (navigator.geolocation)', function () {

        it("geolocation.spec.1 should exist", function () {
            expect(navigator.geolocation).toBeDefined();
        });

        it("geolocation.spec.2 should contain a getCurrentPosition function", function () {
            expect(typeof navigator.geolocation.getCurrentPosition).toBeDefined();
            expect(typeof navigator.geolocation.getCurrentPosition == 'function').toBe(true);
        });

        it("geolocation.spec.3 should contain a watchPosition function", function () {
            expect(typeof navigator.geolocation.watchPosition).toBeDefined();
            expect(typeof navigator.geolocation.watchPosition == 'function').toBe(true);
        });

        it("geolocation.spec.4 should contain a clearWatch function", function () {
            expect(typeof navigator.geolocation.clearWatch).toBeDefined();
            expect(typeof navigator.geolocation.clearWatch == 'function').toBe(true);
        });

    });

    describe('getCurrentPosition method', function () {

        describe('error callback', function () {

            it("geolocation.spec.5 should be called if we set timeout to 0 and maximumAge to a very small number", function (done) {
                if (isWindowsStore || skipAndroid) {
                    pending();
                }

                navigator.geolocation.getCurrentPosition(
                    fail.bind(null, done),
                    succeed.bind(null, done),
                    {
                        maximumAge: 0,
                        timeout: 0
                    });
            });

            it("geolocation.spec.9 on failure should return PositionError object with error code constants", function (done) {
                if (isWindowsStore || skipAndroid) {
                    pending();
                }

                navigator.geolocation.getCurrentPosition(
                    fail.bind(this, done),
                    function(gpsError) {
                        // W3C specs: http://dev.w3.org/geo/api/spec-source.html#position_error_interface
                        expect(gpsError.PERMISSION_DENIED).toBe(1);
                        expect(gpsError.POSITION_UNAVAILABLE).toBe(2);
                        expect(gpsError.TIMEOUT).toBe(3);
                        done();
                    },
                    {
                        maximumAge: 0,
                        timeout: 0
                    });
            });

        });

        describe('success callback', function () {

            it("geolocation.spec.6 should be called with a Position object", function (done) {
                if (isWindowsStore || skipAndroid) {
                    pending();
                }

                navigator.geolocation.getCurrentPosition(function (p) {
                    expect(p.coords).toBeDefined();
                    expect(p.timestamp).toBeDefined();
                    done();
                }, function(err){
                    if(err.message && err.message.indexOf('kCLErrorDomain') > -1){
                        console.log("Error: Location not set in simulator, tests will fail.");
                        expect(true).toBe(true);
                        isIOSSim = true;
                        done();
                    }
                    else {
                        fail(done);
                    }
                },
                {
                    maximumAge: (5 * 60 * 1000) // 5 minutes maximum age of cached position
                });
            }, 25000); // first geolocation call can take several seconds on some devices
        });

    });

    describe('watchPosition method', function () {

        beforeEach(function(done) {
            // This timeout is set to lessen the load on platform's geolocation services
            // which were causing occasional test failures
            setTimeout(function() {
                done();
            }, 100);
        });

        describe('error callback', function () {

            var errorWatch = null;
            afterEach(function () {
                navigator.geolocation.clearWatch(errorWatch);
            });

            it("geolocation.spec.7 should be called if we set timeout to 0 and maximumAge to a very small number", function (done) {
                if (isWindowsStore || skipAndroid) {
                    pending();
                }

                var context = this;
                errorWatch = navigator.geolocation.watchPosition(
                    fail.bind(null, done, context, 'Unexpected win'),
                    succeed.bind(null, done, context),
                    {
                        maximumAge: 0,
                        timeout: 0
                    });
            });

            it("geolocation.spec.10 on failure should return PositionError object with error code constants", function (done) {
                if (isWindowsStore || skipAndroid) {
                    pending();
                }

                var context = this;
                errorWatch = navigator.geolocation.watchPosition(
                    fail.bind(this, done, context, 'Unexpected win'),
                    function(gpsError) {
                        if (context.done) return;
                        context.done = true;

                        // W3C specs: http://dev.w3.org/geo/api/spec-source.html#position_error_interface
                        expect(gpsError.PERMISSION_DENIED).toBe(1);
                        expect(gpsError.POSITION_UNAVAILABLE).toBe(2);
                        expect(gpsError.TIMEOUT).toBe(3);

                        done();
                    },
                    {
                        maximumAge: 0,
                        timeout: 0
                    });
            });

        });

        describe('success callback', function () {

            var successWatch = null;
            afterEach(function () {
                navigator.geolocation.clearWatch(successWatch);
            });

            it("geolocation.spec.8 should be called with a Position object", function (done) {
                if (isWindowsStore || skipAndroid || isIOSSim) {
                    pending();
                }

                var context = this;
                successWatch = navigator.geolocation.watchPosition(
                    function (p) {
                        // prevents done() to be called several times
                        if (context.done) return;
                        context.done = true;

                        expect(p.coords).toBeDefined();
                        expect(p.timestamp).toBeDefined();
                        // callback could be called sync so we invoke done async to make sure we know watcher id to .clear in afterEach 
                        setTimeout(function () {
                            done();
                        });
                    },
                    fail.bind(null, done, context, 'Unexpected fail callback'),
                    {
                        maximumAge: (5 * 60 * 1000) // 5 minutes maximum age of cached position
                    });
                expect(successWatch).toBeDefined();
            });

        });

    });

};

/******************************************************************************/
/******************************************************************************/
/******************************************************************************/

exports.defineManualTests = function (contentEl, createActionButton) {
    var watchLocationId = null;

    /**
     * Start watching location
     */
    var watchLocation = function () {
        var geo = navigator.geolocation;
        if (!geo) {
            alert('navigator.geolocation object is missing.');
            return;
        }

        // Success callback
        var success = function (p) {
            setLocationDetails(p);
        };

        // Fail callback
        var fail = function (e) {
            console.log("watchLocation fail callback with error code " + e);
            stopLocation(geo);
        };

        // Get location
        watchLocationId = geo.watchPosition(success, fail, { enableHighAccuracy: true });
        setLocationStatus("Running");
    };

    /**
     * Stop watching the location
     */
    var stopLocation = function () {
        var geo = navigator.geolocation;
        if (!geo) {
            alert('navigator.geolocation object is missing.');
            return;
        }
        setLocationStatus("Stopped");
        if (watchLocationId) {
            geo.clearWatch(watchLocationId);
            watchLocationId = null;
        }
    };

    /**
     * Get current location
     */
    var getLocation = function (opts) {
        var geo = navigator.geolocation;
        if (!geo) {
            alert('navigator.geolocation object is missing.');
            return;
        }

        // Stop location if running
        stopLocation(geo);

        // Success callback
        var success = function (p) {
            setLocationDetails(p);
            setLocationStatus("Done");
        };

        // Fail callback
        var fail = function (e) {
            console.log("getLocation fail callback with error code " + e.code);
            setLocationStatus("Error: " + e.code);
        };

        setLocationStatus("Retrieving location...");

        // Get location
        geo.getCurrentPosition(success, fail, opts || { enableHighAccuracy: true }); //, {timeout: 10000});

    };

    /**
     * Set location status
     */
    var setLocationStatus = function (status) {
        document.getElementById('location_status').innerHTML = status;
    };
    var setLocationDetails = function (p) {
        var date = (new Date(p.timestamp));
        document.getElementById('latitude').innerHTML = p.coords.latitude;
        document.getElementById('longitude').innerHTML = p.coords.longitude;
        document.getElementById('altitude').innerHTML = p.coords.altitude;
        document.getElementById('accuracy').innerHTML = p.coords.accuracy;
        document.getElementById('heading').innerHTML = p.coords.heading;
        document.getElementById('speed').innerHTML = p.coords.speed;
        document.getElementById('altitude_accuracy').innerHTML = p.coords.altitudeAccuracy;
        document.getElementById('timestamp').innerHTML = date.toDateString() + " " + date.toTimeString();
    };

    /******************************************************************************/

    var location_div = '<div id="info">' +
            '<b>Status:</b> <span id="location_status">Stopped</span>' +
            '<table width="100%">',
        latitude = '<tr>' +
            '<td><b>Latitude:</b></td>' +
            '<td id="latitude">&nbsp;</td>' +
            '<td>(decimal degrees) geographic coordinate [<a href="http://dev.w3.org/geo/api/spec-source.html#lat">#ref]</a></td>' +
            '</tr>',
        longitude = '<tr>' +
            '<td><b>Longitude:</b></td>' +
            '<td id="longitude">&nbsp;</td>' +
            '<td>(decimal degrees) geographic coordinate [<a href="http://dev.w3.org/geo/api/spec-source.html#lat">#ref]</a></td>' +
            '</tr>',
        altitude = '<tr>' +
            '<td><b>Altitude:</b></td>' +
            '<td id="altitude">&nbsp;</td>' +
            '<td>null if not supported;<br>' +
            '(meters) height above the [<a href="http://dev.w3.org/geo/api/spec-source.html#ref-wgs">WGS84</a>] ellipsoid. [<a href="http://dev.w3.org/geo/api/spec-source.html#altitude">#ref]</a></td>' +
            '</tr>',
        accuracy = '<tr>' +
            '<td><b>Accuracy:</b></td>' +
            '<td id="accuracy">&nbsp;</td>' +
            '<td>(meters; non-negative; 95% confidence level) the accuracy level of the latitude and longitude coordinates. [<a href="http://dev.w3.org/geo/api/spec-source.html#accuracy">#ref]</a></td>' +
            '</tr>',
        heading = '<tr>' +
            '<td><b>Heading:</b></td>' +
            '<td id="heading">&nbsp;</td>' +
            '<td>null if not supported;<br>' +
            'NaN if speed == 0;<br>' +
            '(degrees; 0° ≤ heading < 360°) direction of travel of the hosting device- counting clockwise relative to the true north. [<a href="http://dev.w3.org/geo/api/spec-source.html#heading">#ref]</a></td>' +
            '</tr>',
        speed = '<tr>' +
            '<td><b>Speed:</b></td>' +
            '<td id="speed">&nbsp;</td>' +
            '<td>null if not supported;<br>' +
            '(meters per second; non-negative) magnitude of the horizontal component of the hosting device current velocity. [<a href="http://dev.w3.org/geo/api/spec-source.html#speed">#ref]</a></td>' +
            '</tr>',
        altitude_accuracy = '<tr>' +
            '<td><b>Altitude Accuracy:</b></td>' +
            '<td id="altitude_accuracy">&nbsp;</td>' +
            '<td>null if not supported;<br>(meters; non-negative; 95% confidence level) the accuracy level of the altitude. [<a href="http://dev.w3.org/geo/api/spec-source.html#altitude-accuracy">#ref]</a></td>' +
            '</tr>',
        time = '<tr>' +
            '<td><b>Time:</b></td>' +
            '<td id="timestamp">&nbsp;</td>' +
            '<td>(DOMTimeStamp) when the position was acquired [<a href="http://dev.w3.org/geo/api/spec-source.html#timestamp">#ref]</a></td>' +
            '</tr>' +
            '</table>' +
            '</div>',
        actions =
            '<div id="cordova-getLocation"></div>' +
            'Expected result: Will update all applicable values in status box for current location. Status will read Retrieving Location (may not see this if location is retrieved immediately) then Done.' +
            '<p/> <div id="cordova-watchLocation"></div>' +
            'Expected result: Will update all applicable values in status box for current location and update as location changes. Status will read Running.' +
            '<p/> <div id="cordova-stopLocation"></div>' +
            'Expected result: Will stop watching the location so values will not be updated. Status will read Stopped.' +
            '<p/> <div id="cordova-getOld"></div>' +
            'Expected result: Will update location values with a cached position that is up to 30 seconds old. Verify with time value. Status will read Done.',
        values_info =
            '<h3>Details about each value are listed below in the status box</h3>',
        note = 
            '<h3>Allow use of current location, if prompted</h3>';

    contentEl.innerHTML = values_info + location_div + latitude + longitude + altitude + accuracy + heading + speed
        + altitude_accuracy + time + note + actions;

    createActionButton('Get Location', function () {
        getLocation();
    }, 'cordova-getLocation');

    createActionButton('Start Watching Location', function () {
        watchLocation();
    }, 'cordova-watchLocation');

    createActionButton('Stop Watching Location', function () {
        stopLocation();
    }, 'cordova-stopLocation');

    createActionButton('Get Location Up to 30 Sec Old', function () {
        getLocation({ maximumAge: 30000 });
    }, 'cordova-getOld');
};
