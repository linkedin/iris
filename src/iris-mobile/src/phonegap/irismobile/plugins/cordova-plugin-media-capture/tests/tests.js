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
    describe('Capture (navigator.device.capture)', function () {
        it("capture.spec.1 should exist", function () {
            expect(navigator.device).toBeDefined();
            expect(navigator.device.capture).toBeDefined();
        });

        it("capture.spec.2 should have the correct properties ", function () {
            expect(navigator.device.capture.supportedAudioModes).toBeDefined();
            expect(navigator.device.capture.supportedImageModes).toBeDefined();
            expect(navigator.device.capture.supportedVideoModes).toBeDefined();
        });

        it("capture.spec.3 should contain a captureAudio function", function () {
            expect(navigator.device.capture.captureAudio).toBeDefined();
            expect(typeof navigator.device.capture.captureAudio == 'function').toBe(true);
        });

        it("capture.spec.4 should contain a captureImage function", function () {
            expect(navigator.device.capture.captureImage).toBeDefined();
            expect(typeof navigator.device.capture.captureImage == 'function').toBe(true);
        });

        it("capture.spec.5 should contain a captureVideo function", function () {
            expect(navigator.device.capture.captureVideo).toBeDefined();
            expect(typeof navigator.device.capture.captureVideo == 'function').toBe(true);
        });

        describe('CaptureAudioOptions', function () {
            it("capture.spec.6 CaptureAudioOptions constructor should exist", function () {
                var options = new CaptureAudioOptions();
                expect(options).toBeDefined();
                expect(options.limit).toBeDefined();
                expect(options.duration).toBeDefined();
            });
        });

        describe('CaptureImageOptions', function () {
            it("capture.spec.7 CaptureImageOptions constructor should exist", function () {
                var options = new CaptureImageOptions();
                expect(options).toBeDefined();
                expect(options.limit).toBeDefined();
            });
        });

        describe('CaptureVideoOptions', function () {
            it("capture.spec.8 CaptureVideoOptions constructor should exist", function () {
                var options = new CaptureVideoOptions();
                expect(options).toBeDefined();
                expect(options.limit).toBeDefined();
                expect(options.duration).toBeDefined();
            });
        });

        describe('CaptureError interface', function () {
            it("capture.spec.9 CaptureError constants should be defined", function () {
                expect(CaptureError.CAPTURE_INTERNAL_ERR).toBe(0);
                expect(CaptureError.CAPTURE_APPLICATION_BUSY).toBe(1);
                expect(CaptureError.CAPTURE_INVALID_ARGUMENT).toBe(2);
                expect(CaptureError.CAPTURE_NO_MEDIA_FILES).toBe(3);
            });

            it("capture.spec.10 CaptureError properties should exist", function () {
                var error = new CaptureError();
                expect(error).toBeDefined();
                expect(error.code).toBeDefined();
            });
        });

        describe('MediaFileData', function () {
            it("capture.spec.11 MediaFileData constructor should exist", function () {
                var fileData = new MediaFileData();
                expect(fileData).toBeDefined();
                expect(fileData.bitrate).toBeDefined();
                expect(fileData.codecs).toBeDefined();
                expect(fileData.duration).toBeDefined();
                expect(fileData.height).toBeDefined();
                expect(fileData.width).toBeDefined();
            });
        });

        describe('MediaFile', function () {
            it("capture.spec.12 MediaFile constructor should exist", function () {
                var fileData = new MediaFile();
                expect(fileData).toBeDefined();
                expect(fileData.name).toBeDefined();
                expect(fileData.type).toBeDefined();
                expect(fileData.lastModifiedDate).toBeDefined();
                expect(fileData.size).toBeDefined();
            });
        });
    });
};

/******************************************************************************/
/******************************************************************************/
/******************************************************************************/

exports.defineManualTests = function (contentEl, createActionButton) {
    var platformId = cordova.require('cordova/platform').id;
    var pageStartTime = +new Date();

    function log(value) {
        document.getElementById('camera_status').textContent += (new Date() - pageStartTime) / 1000 + ': ' + value + '\n';
        console.log(value);
    }

    function captureAudioWin(mediaFiles) {
        var path = mediaFiles[0].fullPath;
        log('Audio captured: ' + path);
        var m = new Media(path);
        m.play();
    }

    function captureAudioFail(e) {
        log('Error getting audio: ' + e.code);
    }

    function getAudio() {
        clearStatus();
        var options = { limit: 1, duration: 10 };
        navigator.device.capture.captureAudio(captureAudioWin, captureAudioFail, options);
    }

    function captureImageWin(mediaFiles) {
        var path = mediaFiles[0].fullPath;
        // Necessary since windows doesn't allow file URLs for <img> elements
        if (cordova.platformId == 'windows' || cordova.platformId == 'windows8' || cordova.platformId === 'browser') {
            path = mediaFiles[0].localURL;
        }
        log('Image captured: ' + path);
        document.getElementById('camera_image').src = path;
    }

    function captureImageFail(e) {
        log('Error getting image: ' + e.code);
    }

    function getImage() {
        clearStatus();
        var options = { limit: 1 };
        navigator.device.capture.captureImage(captureImageWin, captureImageFail, options);
    }

    function captureVideoWin(mediaFiles) {
        var path = mediaFiles[0].fullPath;
        log('Video captured: ' + path);

        // need to inject the video element into the html
        // doesn't seem to work if you have a pre-existing video element and
        // add in a source tag
        var vid = document.createElement('video');
        vid.id = "theVideo";
        vid.width = "320";
        vid.height = "240";
        vid.controls = "true";
        var source_vid = document.createElement('source');
        source_vid.id = "theSource";
        source_vid.src = path;
        vid.appendChild(source_vid);
        document.getElementById('video_container').appendChild(vid);
    }

    function captureVideoFail(e) {
        log('Error getting video: ' + e.code);
    }

    function getVideo() {
        clearStatus();
        var options = { limit: 1, duration: 10 };
        navigator.device.capture.captureVideo(captureVideoWin, captureVideoFail, options);
    }

    function resolveMediaFileURL(mediaFile, callback) {
        resolveLocalFileSystemURL(mediaFile.localURL, function (entry) {
            log("Resolved by URL: " + mediaFile.localURL);
            if (callback) callback();
        }, function (err) {
            log("Failed to resolve by URL: " + mediaFile.localURL);
            log("Error: " + JSON.stringify(err));
            if (callback) callback();
        });
    }

    function resolveMediaFile(mediaFile, callback) {
        resolveLocalFileSystemURL(mediaFile.fullPath, function (entry) {
            log("Resolved by path: " + mediaFile.fullPath);
            if (callback) callback();
        }, function (err) {
            log("Failed to resolve by path: " + mediaFile.fullPath);
            log("Error: " + JSON.stringify(err));
            if (callback) callback();
        });
    }

    function resolveVideo() {
        clearStatus();
        var options = { limit: 1, duration: 5 };
        navigator.device.capture.captureVideo(function (mediaFiles) {
            captureVideoWin(mediaFiles);
            resolveMediaFile(mediaFiles[0], function () {
                resolveMediaFileURL(mediaFiles[0]);
            });
        }, captureVideoFail, options);
    }

    function clearStatus() {
        document.getElementById('camera_status').innerHTML = '';
        document.getElementById('camera_image').src = 'about:blank';
    }

    /******************************************************************************/

    contentEl.innerHTML = '<div id="info" style="white-space: pre-wrap">' +
        '<b>Status:</b> <div id="camera_status"></div>' +
        'img: <img width="100" id="camera_image">' +
        'video: <div id="video_container"></div>' +
        '</div><div id="audio"></div>' +
        'Expected result: Audio recorder will come up. Press record button to record for 10 seconds. Press Done. Status box will update with audio file and automatically play recording.' +
        '<p/> <div id="image"></div>' +
        'Expected result: Status box will update with image just taken.' +
        '<p/> <div id="video"></div>' +
        'Expected result: Record 10 second video. Status box will update with video file that you can play.' +
        '<p/> <div id="video_and_resolve"></div>' +
        'Expected result: Record 5 second video. Status box will show that URL was resolved and video will get added at the bottom of the status box for playback.';

    createActionButton('Capture 10 sec of audio and play', function () {
        getAudio();
    }, 'audio');

    createActionButton('Capture 1 image', function () {
        getImage();
    }, 'image');

    createActionButton('Capture 10 sec of video', function () {
        getVideo();
    }, 'video');

    createActionButton('Capture 5 sec of video and resolve', function () {
        resolveVideo();
    }, 'video_and_resolve');
};
