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

/* global exports, cordova, FileTransfer, FileTransferError, FileUploadOptions, LocalFileSystem */

/* jshint jasmine: true */

exports.defineAutoTests = function () {

    "use strict";

    // constants
    var ONE_SECOND = 1000; // in milliseconds
    var GRACE_TIME_DELTA = 600; // in milliseconds
    var DEFAULT_FILESYSTEM_SIZE = 1024 * 50; // filesystem size in bytes
    var UNKNOWN_HOST = "http://foobar.apache.org";
    var HEADERS_ECHO = "http://whatheaders.com"; // NOTE: this site is very useful!
    var DOWNLOAD_TIMEOUT = 7 * ONE_SECOND;
    var WINDOWS_UNKNOWN_HOST_TIMEOUT = 35 * ONE_SECOND;
    var UPLOAD_TIMEOUT = 7 * ONE_SECOND;
    var ABORT_DELAY = 100; // for abort() tests
    var LATIN1_SYMBOLS = '¥§©ÆÖÑøøø¼';
    var DATA_URI_PREFIX = "data:image/png;base64,";
    var DATA_URI_CONTENT = "iVBORw0KGgoAAAANSUhEUgAAAAUAAAAFCAYAAACNbyblAAAAHElEQVQI12P4//8/w38GIAXDIBKE0DHxgljNBAAO9TXL0Y4OHwAAAABJRU5ErkJggg==";
    var DATA_URI_CONTENT_LENGTH = 85; // bytes. (This is the raw file size: used https://en.wikipedia.org/wiki/File:Red-dot-5px.png from https://en.wikipedia.org/wiki/Data_URI_scheme)

    // config for upload test server
    // NOTE:
    //      more info at https://github.com/apache/cordova-labs/tree/cordova-filetransfer
    var SERVER                  = "http://cordova-vm.apache.org:5000";
    var SERVER_WITH_CREDENTIALS = "http://cordova_user:cordova_password@cordova-vm.apache.org:5000";

    // flags
    var isWindows = cordova.platformId === "windows8" || cordova.platformId === "windows";
    var isWP8 = cordova.platformId === "windowsphone";
    var isBrowser = cordova.platformId === "browser";
    var isIE = isBrowser && navigator.userAgent.indexOf("Trident") >= 0;
    var isIos = cordova.platformId === "ios";

    // tests
    describe("FileTransferError", function () {

        it("should exist", function () {
            expect(FileTransferError).toBeDefined();
        });

        it("should be constructable", function () {
            var transferError = new FileTransferError();
            expect(transferError).toBeDefined();
        });

        it("filetransfer.spec.3 should expose proper constants", function () {

            expect(FileTransferError.FILE_NOT_FOUND_ERR).toBeDefined();
            expect(FileTransferError.INVALID_URL_ERR).toBeDefined();
            expect(FileTransferError.CONNECTION_ERR).toBeDefined();
            expect(FileTransferError.ABORT_ERR).toBeDefined();
            expect(FileTransferError.NOT_MODIFIED_ERR).toBeDefined();

            expect(FileTransferError.FILE_NOT_FOUND_ERR).toBe(1);
            expect(FileTransferError.INVALID_URL_ERR).toBe(2);
            expect(FileTransferError.CONNECTION_ERR).toBe(3);
            expect(FileTransferError.ABORT_ERR).toBe(4);
            expect(FileTransferError.NOT_MODIFIED_ERR).toBe(5);
        });
    });

    describe("FileUploadOptions", function () {

        it("should exist", function () {
            expect(FileUploadOptions).toBeDefined();
        });

        it("should be constructable", function () {
            var transferOptions = new FileUploadOptions();
            expect(transferOptions).toBeDefined();
        });
    });

    describe("FileTransfer", function () {
        this.persistentRoot = null;
        this.tempRoot       = null;

        // named callbacks
        var unexpectedCallbacks = {
            httpFail:          function () {},
            httpWin:           function () {},
            fileSystemFail:    function () {},
            fileSystemWin:     function () {},
            fileOperationFail: function () {},
            fileOperationWin:  function () {},
        };

        var expectedCallbacks = {
            unsupportedOperation: function (response) {
                console.log("spec called unsupported functionality; response:", response);
            },
        };

        // helpers
        var deleteFile = function (fileSystem, name, done) {
            fileSystem.getFile(name, null,
                function (fileEntry) {
                    fileEntry.remove(
                        function () {
                            done();
                        },
                        function () {
                            throw new Error("failed to delete: '" + name + "'");
                        }
                    );
                },
                function () {
                    done();
                }
            );
        };

        var writeFile = function (fileSystem, name, content, success, done) {
            var fileOperationFail = function() {
                unexpectedCallbacks.fileOperationFail();
                done();
            };

            fileSystem.getFile(name, { create: true },
                function (fileEntry) {
                    fileEntry.createWriter(function (writer) {

                        writer.onwrite = function () {
                            success(fileEntry);
                        };

                        writer.onabort = function (evt) {
                            throw new Error("aborted creating test file '" + name + "': " + evt);
                        };

                        writer.error = function (evt) {
                            throw new Error("aborted creating test file '" + name + "': " + evt);
                        };

                        if (cordova.platformId === "browser") {
                            var blob = new Blob([content + "\n"], { type: "text/plain" });
                            writer.write(blob);
                        } else {
                            writer.write(content + "\n");
                        }

                    }, fileOperationFail);
                },
                function () {
                    throw new Error("could not create test file '" + name + "'");
                }
            );
        };

        // according to documentation, wp8 does not support onProgress:
        // https://github.com/apache/cordova-plugin-file-transfer/blob/master/doc/index.md#supported-platforms
        var wp8OnProgressHandler = function () {};

        var defaultOnProgressHandler = function (event) {
            if (event.lengthComputable) {
                expect(event.loaded).toBeGreaterThan(1);
                expect(event.total).toBeGreaterThan(0);
                expect(event.total).not.toBeLessThan(event.loaded);
                expect(event.lengthComputable).toBe(true, "lengthComputable");
            } else {
                // In IE, when lengthComputable === false, event.total somehow is equal to 2^64
                if (isIE) {
                    expect(event.total).toBe(Math.pow(2, 64));
                } else {
                    // iOS returns -1, and other platforms return 0
                    expect(event.total).toBeLessThan(1);
                }
            }
        };

        var getMalformedUrl = function () {
            if (cordova.platformId === "android" || cordova.platformId === "amazon-fireos") {
                // bad protocol causes a MalformedUrlException on Android
                return "httpssss://example.com";
            } else {
                // iOS doesn't care about protocol, space in hostname causes error
                return "httpssss://exa mple.com";
            }
        };

        // NOTE:
        //      there are several beforeEach calls, one per async call; since calling done()
        //      signifies a completed async call, each async call needs its own done(), and
        //      therefore its own beforeEach
        beforeEach(function (done) {
            var specContext = this;

            window.requestFileSystem(LocalFileSystem.PERSISTENT, DEFAULT_FILESYSTEM_SIZE,
                function (fileSystem) {
                    specContext.persistentRoot = fileSystem.root;
                    done();
                },
                function () {
                    throw new Error("Failed to initialize persistent file system.");
                }
            );
        });

        beforeEach(function (done) {
            var specContext = this;

            window.requestFileSystem(LocalFileSystem.TEMPORARY, DEFAULT_FILESYSTEM_SIZE,
                function (fileSystem) {
                    specContext.tempRoot = fileSystem.root;
                    done();
                },
                function () {
                    throw new Error("Failed to initialize temporary file system.");
                }
            );
        });

        // spy on all named callbacks
        beforeEach(function() {

            // ignore the actual implementations of the unexpected callbacks
            for (var callback in unexpectedCallbacks) {
                if (unexpectedCallbacks.hasOwnProperty(callback)) {
                    spyOn(unexpectedCallbacks, callback);
                }
            }

            // but run the implementations of the expected callbacks
            for (callback in expectedCallbacks) { // jshint ignore: line
                if (expectedCallbacks.hasOwnProperty(callback)) {
                    spyOn(expectedCallbacks, callback).and.callThrough();
                }
            }
        });

        // at the end, check that none of the unexpected callbacks got called,
        // and act on the expected callbacks
        afterEach(function() {
            for (var callback in unexpectedCallbacks) {
                if (unexpectedCallbacks.hasOwnProperty(callback)) {
                    expect(unexpectedCallbacks[callback]).not.toHaveBeenCalled();
                }
            }

            if (expectedCallbacks.unsupportedOperation.calls.any()) {
                pending();
            }
        });

        it("should initialise correctly", function() {
            expect(this.persistentRoot).toBeDefined();
            expect(this.tempRoot).toBeDefined();
        });

        it("should exist", function () {
            expect(FileTransfer).toBeDefined();
        });

        it("filetransfer.spec.1 should be constructable", function () {
            var transfer = new FileTransfer();
            expect(transfer).toBeDefined();
        });

        it("filetransfer.spec.2 should expose proper functions", function () {

            var transfer = new FileTransfer();

            expect(transfer.upload).toBeDefined();
            expect(transfer.download).toBeDefined();

            expect(transfer.upload).toEqual(jasmine.any(Function));
            expect(transfer.download).toEqual(jasmine.any(Function));
        });

        describe("methods", function() {
            this.transfer       = null;
            this.root           = null;
            this.fileName       = null;
            this.localFilePath  = null;

            beforeEach(function() {

                this.transfer = new FileTransfer();

                // assign onprogress handler
                this.transfer.onprogress = isWP8 ? wp8OnProgressHandler : defaultOnProgressHandler;

                // spy on the onprogress handler, but still call through to it
                spyOn(this.transfer, "onprogress").and.callThrough();

                this.root          = this.persistentRoot;
                this.fileName      = "testFile.txt";
                this.localFilePath = this.root.toURL() + this.fileName;
            });

            // NOTE:
            //      if download tests are failing, check the
            //      URL white list for the following URLs:
            //         - 'httpssss://example.com'
            //         - 'apache.org', with subdomains="true"
            //         - 'cordova-filetransfer.jitsu.com'
            describe("download", function () {

                // helpers
                var verifyDownload = function (fileEntry, specContext) {
                    expect(fileEntry.name).toBe(specContext.fileName);
                };

                // delete the downloaded file
                afterEach(function (done) {
                    deleteFile(this.root, this.fileName, done);
                });

                it("ensures that test file does not exist", function (done) {
                    deleteFile(this.root, this.fileName, done);
                });

                it("filetransfer.spec.4 should download a file", function (done) {

                    var fileURL = SERVER + "/robots.txt";
                    var specContext = this;

                    var fileWin = function (blob) {

                        if (specContext.transfer.onprogress.calls.any()) {
                            var lastProgressEvent = specContext.transfer.onprogress.calls.mostRecent().args[0];
                            expect(lastProgressEvent.loaded).not.toBeGreaterThan(blob.size);
                        } else {
                            console.log("no progress events were emitted");
                        }

                        done();
                    };

                    var fileSystemFail = function() {
                        unexpectedCallbacks.fileSystemFail();
                        done();
                    };

                    var downloadFail = function() {
                        unexpectedCallbacks.httpFail();
                        done();
                    };

                    var downloadWin = function (entry) {

                        verifyDownload(entry, specContext);

                        // verify the FileEntry representing this file
                        entry.file(fileWin, fileSystemFail);
                    };

                    specContext.transfer.download(fileURL, specContext.localFilePath, downloadWin, downloadFail);
                }, DOWNLOAD_TIMEOUT);

                it("filetransfer.spec.5 should download a file using http basic auth", function (done) {

                    var fileURL = SERVER_WITH_CREDENTIALS + "/download_basic_auth";
                    var specContext = this;

                    var downloadWin = function (entry) {
                        verifyDownload(entry, specContext);
                        done();
                    };

                    var downloadFail = function() {
                        unexpectedCallbacks.httpFail();
                        done();
                    };

                    specContext.transfer.download(fileURL, specContext.localFilePath, downloadWin, downloadFail);
                }, DOWNLOAD_TIMEOUT);

                it("filetransfer.spec.6 should get 401 status on http basic auth failure", function (done) {

                    // NOTE:
                    //      using server without credentials
                    var fileURL = SERVER + "/download_basic_auth";

                    var downloadFail = function (error) {
                        expect(error.http_status).toBe(401);
                        expect(error.http_status).not.toBe(404, "Ensure " + fileURL + " is in the white list");
                        done();
                    };

                    var downloadWin = function() {
                        unexpectedCallbacks.httpWin();
                        done();
                    };

                    this.transfer.download(fileURL, this.localFilePath, downloadWin, downloadFail, null,
                        {
                            headers: {
                                "If-Modified-Since": "Thu, 19 Mar 2015 00:00:00 GMT"
                            }
                        });
                }, DOWNLOAD_TIMEOUT);

                it("filetransfer.spec.7 should download a file using file:// (when hosted from file://)", function (done) {

                    // for Windows platform it's ms-appdata:/// by default, not file://
                    if (isWindows) {
                        pending();
                        return;
                    }

                    var fileURL = window.location.protocol + "//" + window.location.pathname.replace(/ /g, "%20");
                    var specContext = this;

                    if (!/^file:/.exec(fileURL) && cordova.platformId !== "blackberry10") {
                        if (cordova.platformId === "windowsphone") {
                            expect(fileURL).toMatch(/^x-wmapp0:/);
                        }
                        done();
                        return;
                    }

                    var downloadWin = function (entry) {
                        verifyDownload(entry, specContext);
                        done();
                    };

                    var downloadFail = function() {
                        unexpectedCallbacks.httpFail();
                        done();
                    };

                    specContext.transfer.download(fileURL, specContext.localFilePath, downloadWin, downloadFail);
                }, DOWNLOAD_TIMEOUT);

                it("filetransfer.spec.8 should download a file using https://", function (done) {

                    var fileURL = "https://www.apache.org/licenses/";
                    var specContext = this;

                    var downloadFail = function() {
                        unexpectedCallbacks.httpFail();
                        done();
                    };

                    var fileOperationFail = function() {
                        unexpectedCallbacks.fileOperationFail();
                        done();
                    };

                    var fileSystemFail = function() {
                        unexpectedCallbacks.fileSystemFail();
                        done();
                    };

                    var fileWin = function (file) {

                        var reader = new FileReader();

                        reader.onerror = fileOperationFail;
                        reader.onload  = function () {
                            expect(reader.result).toMatch(/The Apache Software Foundation/);
                            done();
                        };

                        reader.readAsText(file);
                    };

                    var downloadWin = function (entry) {
                        verifyDownload(entry, specContext);
                        entry.file(fileWin, fileSystemFail);
                    };

                    specContext.transfer.download(fileURL, specContext.localFilePath, downloadWin, downloadFail);
                }, DOWNLOAD_TIMEOUT);

                it("filetransfer.spec.11 should call the error callback on abort()", function (done) {

                    var fileURL = "http://cordova.apache.org/downloads/BlueZedEx.mp3";
                    fileURL = fileURL + "?q=" + (new Date()).getTime();
                    var specContext = this;

                    var downloadWin = function () {
                        unexpectedCallbacks.httpWin();
                        done();
                    };

                    specContext.transfer.download(fileURL, specContext.localFilePath, downloadWin, done);
                    setTimeout(function() {
                        specContext.transfer.abort();
                    }, ABORT_DELAY);
                }, DOWNLOAD_TIMEOUT);

                it("filetransfer.spec.9 should not leave partial file due to abort", function (done) {

                    var fileURL = "http://cordova.apache.org/downloads/logos_2.zip";
                    var specContext = this;

                    var fileSystemWin = function() {
                        unexpectedCallbacks.fileSystemWin();
                        done();
                    };

                    var downloadWin = function() {
                        unexpectedCallbacks.httpWin();
                        done();
                    };

                    var downloadFail = function (error) {

                        var result = (error.code === FileTransferError.ABORT_ERR || error.code === FileTransferError.CONNECTION_ERR)? true: false;
                        if (!result) {
                            fail("Expected " + error.code + " to be " + FileTransferError.ABORT_ERR + " or " + FileTransferError.CONNECTION_ERR);
                        }
                        expect(specContext.transfer.onprogress).toHaveBeenCalled();

                        // check that there is no file
                        specContext.root.getFile(specContext.fileName, null, fileSystemWin, done);
                    };

                    // abort at the first onprogress event
                    specContext.transfer.onprogress = function (event) {
                        if (event.loaded > 0) {
                            specContext.transfer.abort();
                        }
                    };

                    spyOn(specContext.transfer, "onprogress").and.callThrough();

                    specContext.transfer.download(fileURL, specContext.localFilePath, downloadWin, downloadFail);
                }, DOWNLOAD_TIMEOUT);

                it("filetransfer.spec.10 should be stopped by abort()", function (done) {

                    var fileURL = "http://cordova.apache.org/downloads/BlueZedEx.mp3";
                    fileURL = fileURL + "?q=" + (new Date()).getTime();
                    var specContext = this;

                    expect(specContext.transfer.abort).not.toThrow(); // should be a no-op.

                    var downloadWin = function() {
                        unexpectedCallbacks.httpWin();
                        done();
                    };

                    var downloadFail = function (error) {

                        expect(error.code).toBe(FileTransferError.ABORT_ERR);

                        // delay calling done() to wait for the bogus abort()
                        setTimeout(done, GRACE_TIME_DELTA * 2);
                    };

                    specContext.transfer.download(fileURL, specContext.localFilePath, downloadWin, downloadFail);
                    setTimeout(function() {
                        specContext.transfer.abort();
                    }, ABORT_DELAY);

                    // call abort() again, after a time greater than the grace period
                    setTimeout(function () {
                        expect(specContext.transfer.abort).not.toThrow();
                    }, GRACE_TIME_DELTA);
                }, DOWNLOAD_TIMEOUT);

                it("filetransfer.spec.12 should get http status on failure", function (done) {

                    var fileURL = SERVER + "/404";

                    var downloadFail = function (error) {

                        expect(error.http_status).not.toBe(401, "Ensure " + fileURL + " is in the white list");
                        expect(error.http_status).toBe(404);

                        // wp8 does not make difference between 404 and unknown host
                        if (isWP8) {
                            expect(error.code).toBe(FileTransferError.CONNECTION_ERR);
                        } else {
                            expect(error.code).toBe(FileTransferError.FILE_NOT_FOUND_ERR);
                        }

                        done();
                    };

                    var downloadWin = function() {
                        unexpectedCallbacks.httpWin();
                        done();
                    };

                    this.transfer.download(fileURL, this.localFilePath, downloadWin, downloadFail);
                }, DOWNLOAD_TIMEOUT);

                it("filetransfer.spec.13 should get http body on failure", function (done) {

                    var fileURL = SERVER + "/404";

                    var downloadFail = function (error) {

                        expect(error.http_status).not.toBe(401, "Ensure " + fileURL + " is in the white list");
                        expect(error.http_status).toBe(404);

                        expect(error.body).toBeDefined();
                        expect(error.body).toMatch("You requested a 404");

                        done();
                    };

                    var downloadWin = function() {
                        unexpectedCallbacks.httpWin();
                        done();
                    };

                    this.transfer.download(fileURL, this.localFilePath, downloadWin, downloadFail);
                }, DOWNLOAD_TIMEOUT);

                it("filetransfer.spec.14 should handle malformed urls", function (done) {

                    var fileURL = getMalformedUrl();

                    var downloadFail = function (error) {

                        // Note: Android needs the bad protocol to be added to the access list
                        // <access origin=".*"/> won't match because ^https?:// is prepended to the regex
                        // The bad protocol must begin with http to avoid automatic prefix
                        expect(error.http_status).not.toBe(401, "Ensure " + fileURL + " is in the white list");
                        expect(error.code).toBe(FileTransferError.INVALID_URL_ERR);

                        done();
                    };

                    var downloadWin = function() {
                        unexpectedCallbacks.httpWin();
                        done();
                    };

                    this.transfer.download(fileURL, this.localFilePath, downloadWin, downloadFail);
                });

                it("filetransfer.spec.15 should handle unknown host", function (done) {
                    var fileURL = UNKNOWN_HOST;

                    var downloadFail = function (error) {
                        expect(error.code).toBe(FileTransferError.CONNECTION_ERR);
                        done();
                    };

                    var downloadWin = function() {
                        unexpectedCallbacks.httpWin();
                        done();
                    };

                    // turn off the onprogress handler
                    this.transfer.onprogress = function () {};

                    this.transfer.download(fileURL, this.localFilePath, downloadWin, downloadFail);
                }, isWindows ? WINDOWS_UNKNOWN_HOST_TIMEOUT : DOWNLOAD_TIMEOUT);

                it("filetransfer.spec.16 should handle bad file path", function (done) {
                    var fileURL = SERVER;

                    var downloadWin = function() {
                        unexpectedCallbacks.httpWin();
                        done();
                    };

                    this.transfer.download(fileURL, "c:\\54321", downloadWin, done);
                });

                it("filetransfer.spec.17 progress should work with gzip encoding", function (done) {

                    // lengthComputable false on bb10 when downloading gzip
                    if (cordova.platformId === "blackberry10") {
                        pending();
                        return;
                    }

                    var fileURL = "http://www.apache.org/";
                    var specContext = this;

                    var downloadWin = function (entry) {
                        verifyDownload(entry, specContext);
                        done();
                    };

                    var downloadFail = function () {
                        unexpectedCallbacks.httpFail();
                        done();
                    };

                    specContext.transfer.download(fileURL, specContext.localFilePath, downloadWin,downloadFail);
                }, DOWNLOAD_TIMEOUT);

                it("filetransfer.spec.30 downloaded file entries should have a toNativeURL method", function (done) {

                    if (cordova.platformId === "browser") {
                        pending();
                        return;
                    }

                    var fileURL = SERVER + "/robots.txt";

                    var downloadWin = function (entry) {

                        expect(entry.toNativeURL).toBeDefined();
                        expect(entry.toNativeURL).toEqual(jasmine.any(Function));

                        var nativeURL = entry.toNativeURL();

                        expect(nativeURL).toBeTruthy();
                        expect(nativeURL).toEqual(jasmine.any(String));

                        if (isWindows) {
                            expect(nativeURL.substring(0, 14)).toBe("ms-appdata:///");
                        } else if (isWP8) {
                            expect(nativeURL.substring(0, 1)).toBe("/");
                        } else {
                            expect(nativeURL.substring(0, 7)).toBe("file://");
                        }

                        done();
                    };

                    var downloadFail = function() {
                        unexpectedCallbacks.httpFail();
                        done();
                    };

                    this.transfer.download(fileURL, this.localFilePath, downloadWin, downloadFail);
                }, DOWNLOAD_TIMEOUT);

                it("filetransfer.spec.28 (compatibility) should be able to download a file using local paths", function (done) {

                    var fileURL = SERVER + "/robots.txt";
                    var specContext = this;

                    var unsupported = function (response) {
                        expectedCallbacks.unsupportedOperation(response);
                        done();
                    };

                    var downloadWin = function (entry) {
                        verifyDownload(entry, specContext);
                        done();
                    };

                    var internalFilePath;
                    if (specContext.root.toInternalURL) {
                        internalFilePath = specContext.root.toInternalURL() + specContext.fileName;
                    } else {
                        internalFilePath = specContext.localFilePath;
                    }

                    var downloadFail = function() {
                        unexpectedCallbacks.httpFail();
                        done();
                    };

                    // This is an undocumented interface to File which exists only for testing
                    // backwards compatibilty. By obtaining the raw filesystem path of the download
                    // location, we can pass that to transfer.download() to make sure that previously-stored
                    // paths are still valid.
                    cordova.exec(function (localPath) {
                        specContext.transfer.download(fileURL, localPath, downloadWin, downloadFail);
                    }, unsupported, "File", "_getLocalFilesystemPath", [internalFilePath]);
                });

                it("filetransfer.spec.33 should properly handle 304", function (done) {

                    if (isWP8) {
                        pending();
                        return;
                    }

                    var imageURL = "http://apache.org/images/feather-small.gif";
                    var lastModified = new Date();

                    var downloadFail = function (error) {
                        expect(error.http_status).toBe(304);
                        expect(error.code).toBe(FileTransferError.NOT_MODIFIED_ERR);
                        done();
                    };

                    var downloadWin = function() {
                        unexpectedCallbacks.httpWin();
                        done();
                    };

                    this.transfer.download(imageURL + "?q=" + lastModified.getTime(), this.localFilePath, downloadWin, downloadFail, null,
                        {
                            headers: {
                                "If-Modified-Since": lastModified.toUTCString()
                            }
                        });
                }, DOWNLOAD_TIMEOUT);

                it("filetransfer.spec.35 304 should not result in the deletion of a cached file", function (done) {

                    if (isWP8) {
                        pending();
                        return;
                    }

                    var imageURL = "http://apache.org/images/feather-small.gif";
                    var lastModified = new Date();
                    var specContext = this;

                    var fileOperationFail = function() {
                        unexpectedCallbacks.fileOperationFail();
                        done();
                    };

                    var fileSystemFail = function() {
                        unexpectedCallbacks.fileSystemFail();
                        done();
                    };

                    var httpWin =  function() {
                        unexpectedCallbacks.httpWin();
                        done();
                    };

                    var httpFail =  function() {
                        unexpectedCallbacks.httpFail();
                        done();
                    };

                    var downloadFail = function (error) {
                        expect(error.http_status).toBe(304);
                        expect(error.code).toBe(FileTransferError.NOT_MODIFIED_ERR);

                        specContext.persistentRoot.getFile(specContext.fileName, { create: false },
                            function (entry) {
                                var fileWin = function (file) {
                                    var reader = new FileReader();

                                    reader.onerror = fileOperationFail;
                                    reader.onloadend  = function () {

                                        expect(reader.result).toBeTruthy();
                                        if (reader.result !== null) {
                                            expect(reader.result.length).toBeGreaterThan(0);
                                        }

                                        done();
                                    };

                                    reader.readAsBinaryString(file);
                                };

                                entry.file(fileWin, fileSystemFail);
                            },
                            function (err) {
                                expect("Could not open test file '" + specContext.fileName + "': " + JSON.stringify(err)).not.toBeDefined();
                                done();
                            }
                        );
                    };

                    // Adding parameters to the requests to avoid caching on iOS, which leads to 200
                    // instead of 304 in result of the second request. (a similar issue is described in CB-8606, CB-10088)
                    specContext.transfer.download(imageURL + "?q=" + lastModified.getTime(), specContext.localFilePath, function () {
                        specContext.transfer.download(imageURL + "?q=" + (lastModified.getTime() + 1), specContext.localFilePath, httpWin, downloadFail, null,
                        {
                            headers: {
                                "If-Modified-Since": lastModified.toUTCString()
                            }
                        });
                    }, httpFail);
                }, DOWNLOAD_TIMEOUT * 2);

                it("filetransfer.spec.36 should handle non-UTF8 encoded download response", function (done) {

                    // Only iOS is supported: https://issues.apache.org/jira/browse/CB-9840
                    if (!isIos) {
                        pending();
                    }

                    var fileURL = SERVER + '/download_non_utf';
                    var specContext = this;

                    var fileOperationFail = function() {
                        unexpectedCallbacks.fileOperationFail();
                        done();
                    };

                    var fileSystemFail = function() {
                        unexpectedCallbacks.fileSystemFail();
                        done();
                    };

                    var httpFail = function() {
                        unexpectedCallbacks.httpFail();
                        done();
                    };

                    var fileWin = function (blob) {

                        if (specContext.transfer.onprogress.calls.any()) {
                            var lastProgressEvent = specContext.transfer.onprogress.calls.mostRecent().args[0];
                            expect(lastProgressEvent.loaded).not.toBeGreaterThan(blob.size);
                        } else {
                            console.log("no progress events were emitted");
                        }

                        expect(blob.size).toBeGreaterThan(0);

                        var reader = new FileReader();

                        reader.onerror = fileOperationFail;
                        reader.onloadend  = function () {
                            expect(reader.result.indexOf(LATIN1_SYMBOLS)).not.toBe(-1);
                            done();
                        };

                        reader.readAsBinaryString(blob);
                    };

                    var downloadWin = function (entry) {

                        verifyDownload(entry, specContext);

                        // verify the FileEntry representing this file
                        entry.file(fileWin, fileSystemFail);
                    };

                    specContext.transfer.download(fileURL, specContext.localFilePath, downloadWin, httpFail);
                }, UPLOAD_TIMEOUT);
            });

            describe("upload", function() {
                this.uploadParams   = null;
                this.uploadOptions  = null;
                this.fileName       = null;
                this.fileContents   = null;
                this.localFilePath  = null;

                // helpers
                var verifyUpload = function (uploadResult, specContext) {

                    expect(uploadResult.bytesSent).toBeGreaterThan(0);
                    expect(uploadResult.responseCode).toBe(200);

                    var obj = null;
                    try {
                        obj = JSON.parse(uploadResult.response);
                        expect(obj.fields).toBeDefined();
                        expect(obj.fields.value1).toBe("test");
                        expect(obj.fields.value2).toBe("param");
                    } catch (e) {
                        expect(obj).not.toBeNull("returned data from server should be valid json");
                    }

                    expect(specContext.transfer.onprogress).toHaveBeenCalled();
                };

                beforeEach(function(done) {
                    var specContext = this;

                    specContext.fileName               = "fileToUpload.txt";
                    specContext.fileContents           = "upload test file";

                    specContext.uploadParams           = {};
                    specContext.uploadParams.value1    = "test";
                    specContext.uploadParams.value2    = "param";

                    specContext.uploadOptions          = new FileUploadOptions();
                    specContext.uploadOptions.fileKey  = "file";
                    specContext.uploadOptions.fileName = specContext.fileName;
                    specContext.uploadOptions.mimeType = "text/plain";
                    specContext.uploadOptions.params   = specContext.uploadParams;

                    var fileWin = function (entry) {
                        specContext.localFilePath = entry.toURL();
                        done();
                    };

                    // create a file to upload
                    writeFile(specContext.root, specContext.fileName, specContext.fileContents, fileWin, done);
                });

                // delete the uploaded file
                afterEach(function (done) {
                    deleteFile(this.root, this.fileName, done);
                });

                it("filetransfer.spec.18 should be able to upload a file", function (done) {

                    var fileURL = SERVER + "/upload";
                    var specContext = this;

                    var uploadWin = function (uploadResult) {

                        verifyUpload(uploadResult, specContext);

                        if (cordova.platformId === "ios") {
                            expect(uploadResult.headers).toBeDefined("Expected headers to be defined.");
                            expect(uploadResult.headers["Content-Type"]).toBeDefined("Expected content-type header to be defined.");
                        }

                        done();
                    };

                    var uploadFail = function() {
                        unexpectedCallbacks.httpFail();
                        done();
                    };

                    // NOTE: removing uploadOptions cause Android to timeout
                    specContext.transfer.upload(specContext.localFilePath, fileURL, uploadWin, uploadFail, specContext.uploadOptions);
                }, UPLOAD_TIMEOUT);

                it("filetransfer.spec.19 should be able to upload a file with http basic auth", function (done) {

                    var fileURL = SERVER_WITH_CREDENTIALS + "/upload_basic_auth";
                    var specContext = this;

                    var uploadWin = function (uploadResult) {
                        verifyUpload(uploadResult, specContext);
                        done();
                    };

                    var uploadFail = function() {
                        unexpectedCallbacks.httpFail();
                        done();
                    };

                    // NOTE: removing uploadOptions cause Android to timeout
                    specContext.transfer.upload(specContext.localFilePath, fileURL, uploadWin, uploadFail, specContext.uploadOptions);
                }, UPLOAD_TIMEOUT);

                it("filetransfer.spec.21 should be stopped by abort()", function (done) {

                    var fileURL = SERVER + "/upload";
                    var specContext = this;

                    var uploadFail = function (e) {
                        expect(e.code).toBe(FileTransferError.ABORT_ERR);

                        // delay calling done() to wait for the bogus abort()
                        setTimeout(done, GRACE_TIME_DELTA * 2);
                    };

                    var uploadWin = function() {
                        unexpectedCallbacks.httpWin();
                        done();
                    };

                    var fileWin = function () {

                        expect(specContext.transfer.abort).not.toThrow();

                        // NOTE: removing uploadOptions cause Android to timeout
                        specContext.transfer.upload(specContext.localFilePath, fileURL, uploadWin, uploadFail, specContext.uploadOptions);
                        setTimeout(function() {
                            specContext.transfer.abort();
                        }, ABORT_DELAY);

                        setTimeout(function () {
                            expect(specContext.transfer.abort).not.toThrow();
                        }, GRACE_TIME_DELTA);
                    };

                    writeFile(specContext.root, specContext.fileName, new Array(200000).join("aborttest!"), fileWin, done);
                }, UPLOAD_TIMEOUT);

                it("filetransfer.spec.22 should get http status and body on failure", function (done) {

                    var fileURL = SERVER + "/403";

                    var uploadFail = function (error) {
                        expect(error.http_status).toBe(403);
                        expect(error.http_status).not.toBe(401, "Ensure " + fileURL + " is in the white list");
                        done();
                    };

                    var uploadWin = function() {
                        unexpectedCallbacks.httpWin();
                        done();
                    };

                    this.transfer.upload(this.localFilePath, fileURL, uploadWin, uploadFail, this.uploadOptions);
                }, UPLOAD_TIMEOUT);

                it("filetransfer.spec.24 should handle malformed urls", function (done) {

                    var fileURL = getMalformedUrl();

                    var uploadFail = function (error) {
                        expect(error.code).toBe(FileTransferError.INVALID_URL_ERR);
                        expect(error.http_status).not.toBe(401, "Ensure " + fileURL + " is in the white list");
                        done();
                    };

                    var uploadWin = function() {
                        unexpectedCallbacks.httpWin();
                        done();
                    };

                    this.transfer.upload(this.localFilePath, fileURL, uploadWin, uploadFail, {});
                });

                it("filetransfer.spec.25 should handle unknown host", function (done) {

                    var fileURL = UNKNOWN_HOST;

                    var uploadFail = function (error) {
                        expect(error.code).toBe(FileTransferError.CONNECTION_ERR);
                        expect(error.http_status).not.toBe(401, "Ensure " + fileURL + " is in the white list");
                        done();
                    };

                    var uploadWin = function() {
                        unexpectedCallbacks.httpWin();
                        done();
                    };

                    this.transfer.upload(this.localFilePath, fileURL, uploadWin, uploadFail, {});
                }, UPLOAD_TIMEOUT);

                it("filetransfer.spec.25 should handle missing file", function (done) {

                    var fileURL = SERVER + "/upload";

                    var uploadFail = function (error) {
                        expect(error.code).toBe(FileTransferError.FILE_NOT_FOUND_ERR);
                        expect(error.http_status).not.toBe(401, "Ensure " + fileURL + " is in the white list");
                        done();
                    };

                    var uploadWin = function() {
                        unexpectedCallbacks.httpWin();
                        done();
                    };

                    this.transfer.upload("does_not_exist.txt", fileURL, uploadWin, uploadFail);
                }, UPLOAD_TIMEOUT);

                it("filetransfer.spec.26 should handle bad file path", function (done) {

                    var fileURL = SERVER + "/upload";

                    var uploadFail = function (error) {
                        expect(error.http_status).not.toBe(401, "Ensure " + fileURL + " is in the white list");
                        done();
                    };

                    var uploadWin = function() {
                        unexpectedCallbacks.httpWin();
                        done();
                    };

                    this.transfer.upload("c:\\54321", fileURL, uploadWin, uploadFail);
                });

                it("filetransfer.spec.27 should be able to set custom headers", function (done) {

                    var fileURL = HEADERS_ECHO;

                    var uploadWin = function (uploadResult) {

                        expect(uploadResult.bytesSent).toBeGreaterThan(0);
                        expect(uploadResult.responseCode).toBe(200);
                        expect(uploadResult.response).toBeDefined();

                        var responseHtml = decodeURIComponent(uploadResult.response);

                        expect(responseHtml).toMatch(/CustomHeader1[\s\S]*CustomValue1/i);
                        expect(responseHtml).toMatch(/CustomHeader2[\s\S]*CustomValue2[\s\S]*CustomValue3/i, "Should allow array values");

                        done();
                    };

                    var uploadFail = function() {
                        unexpectedCallbacks.httpFail();
                        done();
                    };

                    this.uploadOptions.headers = {
                        "CustomHeader1": "CustomValue1",
                        "CustomHeader2": ["CustomValue2", "CustomValue3"],
                    };

                    // NOTE: removing uploadOptions cause Android to timeout
                    this.transfer.upload(this.localFilePath, fileURL, uploadWin, uploadFail, this.uploadOptions);
                }, UPLOAD_TIMEOUT);

                it("filetransfer.spec.29 (compatibility) should be able to upload a file using local paths", function (done) {

                    var fileURL = SERVER + "/upload";
                    var specContext = this;

                    var unsupported = function (response) {
                        expectedCallbacks.unsupportedOperation(response);
                        done();
                    };

                    var uploadWin = function (uploadResult) {
                        verifyUpload(uploadResult, specContext);
                        done();
                    };

                    var uploadFail = function() {
                        unexpectedCallbacks.httpFail();
                        done();
                    };

                    var internalFilePath;
                    if (specContext.root.toInternalURL) {
                        internalFilePath = specContext.root.toInternalURL() + specContext.fileName;
                    } else {
                        internalFilePath = specContext.localFilePath;
                    }

                    // This is an undocumented interface to File which exists only for testing
                    // backwards compatibilty. By obtaining the raw filesystem path of the download
                    // location, we can pass that to transfer.download() to make sure that previously-stored
                    // paths are still valid.
                    cordova.exec(function (localPath) {
                        specContext.transfer.upload(localPath, fileURL, uploadWin, uploadFail, specContext.uploadOptions);
                    }, unsupported, "File", "_getLocalFilesystemPath", [internalFilePath]);
                }, UPLOAD_TIMEOUT);

                it("filetransfer.spec.31 should be able to upload a file using PUT method", function (done) {

                    var fileURL = SERVER + "/upload";
                    var specContext = this;

                    var uploadWin = function (uploadResult) {

                        verifyUpload(uploadResult, specContext);

                        if (cordova.platformId === "ios") {
                            expect(uploadResult.headers).toBeDefined("Expected headers to be defined.");
                            expect(uploadResult.headers["Content-Type"]).toBeDefined("Expected content-type header to be defined.");
                        }

                        done();
                    };

                    var uploadFail = function() {
                        unexpectedCallbacks.httpFail();
                        done();
                    };

                    specContext.uploadOptions.httpMethod = "PUT";

                    // NOTE: removing uploadOptions cause Android to timeout
                    specContext.transfer.upload(specContext.localFilePath, fileURL, uploadWin, uploadFail, specContext.uploadOptions);
                }, UPLOAD_TIMEOUT);

                it("filetransfer.spec.32 should be able to upload a file (non-multipart)", function (done) {

                    var fileURL = SERVER + "/upload";
                    var specContext = this;

                    var uploadWin = function (uploadResult) {

                        expect(uploadResult.bytesSent).toBeGreaterThan(0);
                        expect(uploadResult.responseCode).toBe(200);
                        expect(uploadResult.response).toBeDefined();
                        if (uploadResult.response) {
                            expect(uploadResult.response).toEqual(specContext.fileContents + "\n");
                        }
                        expect(specContext.transfer.onprogress).toHaveBeenCalled();

                        if (cordova.platformId === "ios") {
                            expect(uploadResult.headers).toBeDefined("Expected headers to be defined.");
                            expect(uploadResult.headers["Content-Type"]).toBeDefined("Expected content-type header to be defined.");
                        }

                        done();
                    };

                    var uploadFail = function() {
                        unexpectedCallbacks.httpFail();
                        done();
                    };

                    // Content-Type header disables multipart
                    specContext.uploadOptions.headers = {
                        "Content-Type": "text/plain"
                    };

                    // NOTE: removing uploadOptions cause Android to timeout
                    specContext.transfer.upload(specContext.localFilePath, fileURL, uploadWin, uploadFail, specContext.uploadOptions);
                }, UPLOAD_TIMEOUT);

                it("filetransfer.spec.34 should not delete a file on upload error", function (done) {

                    var fileURL = SERVER + "/upload";
                    var specContext = this;

                    var uploadFail = function (e) {
                        expect(e.code).toBe(FileTransferError.ABORT_ERR);

                        // check that the file is there
                        specContext.root.getFile(specContext.fileName, null, function(entry) {
                            expect(entry).toBeDefined();
                            // delay calling done() to wait for the bogus abort()
                            setTimeout(done, GRACE_TIME_DELTA * 2);
                        }, function(err) {
                            expect(err).not.toBeDefined(err && err.code);
                            done();
                        });
                    };

                    var uploadWin = function() {
                        unexpectedCallbacks.httpWin();
                        done();
                    };

                    var fileWin = function () {

                        expect(specContext.transfer.abort).not.toThrow();

                        // abort at the first onprogress event
                        specContext.transfer.onprogress = function (event) {
                            if (event.loaded > 0) {
                                specContext.transfer.abort();
                            }
                        };

                        // NOTE: removing uploadOptions cause Android to timeout
                        specContext.transfer.upload(specContext.localFilePath, fileURL, uploadWin, uploadFail, specContext.uploadOptions);
                    };

                    writeFile(specContext.root, specContext.fileName, new Array(100000).join("aborttest!"), fileWin, done);
                }, UPLOAD_TIMEOUT);

                it("filetransfer.spec.37 should handle non-UTF8 encoded upload response", function (done) {

                    // Only iOS is supported: https://issues.apache.org/jira/browse/CB-9840
                    if (!isIos) {
                        pending();
                    }

                    var fileURL = SERVER + '/upload_non_utf';
                    var specContext = this;

                    var uploadWin = function (uploadResult) {

                        verifyUpload(uploadResult, specContext);

                        var obj = null;
                        try {
                            obj = JSON.parse(uploadResult.response);
                            expect(obj.latin1Symbols).toBe(LATIN1_SYMBOLS);
                        } catch (e) {
                            expect(obj).not.toBeNull("returned data from server should be valid json");
                        }

                        if (cordova.platformId === 'ios') {
                            expect(uploadResult.headers).toBeDefined('Expected headers to be defined.');
                            expect(uploadResult.headers['Content-Type']).toBeDefined('Expected content-type header to be defined.');
                        }

                        done();
                    };

                    var uploadFail = function() {
                        unexpectedCallbacks.httpFail();
                        done();
                    };

                    // NOTE: removing uploadOptions cause Android to timeout
                    specContext.transfer.upload(specContext.localFilePath, fileURL, uploadWin, uploadFail, specContext.uploadOptions);
                }, UPLOAD_TIMEOUT);

                it("filetransfer.spec.38 should be able to upload a file using data: source uri", function (done) {

                    var fileURL = SERVER + "/upload";
                    var specContext = this;

                    var uploadWin = function (uploadResult) {

                        verifyUpload(uploadResult,specContext);

                        var obj = null;
                        try {
                            obj = JSON.parse(uploadResult.response);
                            expect(obj.files.file.size).toBe(DATA_URI_CONTENT_LENGTH);
                        } catch (e) {
                            expect(obj).not.toBeNull("returned data from server should be valid json");
                        }

                        if (cordova.platformId === "ios") {
                            expect(uploadResult.headers).toBeDefined("Expected headers to be defined.");
                            expect(uploadResult.headers["Content-Type"]).toBeDefined("Expected content-type header to be defined.");
                        }

                        done();
                    };

                    var dataUri = DATA_URI_PREFIX + DATA_URI_CONTENT;
                    // NOTE: removing uploadOptions cause Android to timeout
                    specContext.transfer.upload(dataUri, fileURL, uploadWin, function (err) {
                        console.error('err: ' + JSON.stringify(err));
                        expect(err).not.toBeDefined();
                        done();
                    }, specContext.uploadOptions);
                }, UPLOAD_TIMEOUT);

                it("filetransfer.spec.39 should be able to upload a file using data: source uri (non-multipart)", function (done) {

                    var fileURL = SERVER + "/upload";

                    var uploadWin = function (uploadResult) {

                        expect(uploadResult.responseCode).toBe(200);
                        expect(uploadResult.bytesSent).toBeGreaterThan(0);

                        if (cordova.platformId === "ios") {
                            expect(uploadResult.headers).toBeDefined("Expected headers to be defined.");
                            expect(uploadResult.headers["Content-Type"]).toBeDefined("Expected content-type header to be defined.");
                        }

                        done();
                    };

                    var uploadFail = function() {
                        unexpectedCallbacks.httpFail();
                        done();
                    };

                    // Content-Type header disables multipart
                    this.uploadOptions.headers = {
                        "Content-Type": "image/png"
                    };

                    var dataUri = DATA_URI_PREFIX + DATA_URI_CONTENT;
                    // NOTE: removing uploadOptions cause Android to timeout
                    this.transfer.upload(dataUri, fileURL, uploadWin, uploadFail, this.uploadOptions);
                }, UPLOAD_TIMEOUT);

                it("filetransfer.spec.40 should not fail to upload a file using data: source uri when the data is empty", function (done) {

                    var fileURL = SERVER + "/upload";

                    var dataUri = DATA_URI_PREFIX;

                    var uploadFail = function() {
                        unexpectedCallbacks.httpFail();
                        done();
                    };

                    // NOTE: removing uploadOptions cause Android to timeout
                    this.transfer.upload(dataUri, fileURL, done, uploadFail, this.uploadOptions);
                }, UPLOAD_TIMEOUT);

                it("filetransfer.spec.41 should not fail to upload a file using data: source uri when the data is empty (non-multipart)", function (done) {

                    var fileURL = SERVER + "/upload";

                    // Content-Type header disables multipart
                    this.uploadOptions.headers = {
                        "Content-Type": "image/png"
                    };

                    // turn off the onprogress handler
                    this.transfer.onprogress = function () { };

                    var dataUri = DATA_URI_PREFIX;

                    var uploadFail = function() {
                        unexpectedCallbacks.httpFail();
                        done();
                    };

                    // NOTE: removing uploadOptions cause Android to timeout
                    this.transfer.upload(dataUri, fileURL, done, uploadFail, this.uploadOptions);
                }, UPLOAD_TIMEOUT);
            });
        });
    });
};

/******************************************************************************/
/******************************************************************************/
/******************************************************************************/

exports.defineManualTests = function (contentEl, createActionButton) {

    "use strict";

    var imageURL = "http://apache.org/images/feather-small.gif";
    var videoURL = "http://techslides.com/demos/sample-videos/small.mp4";

    function clearResults() {
        var results = document.getElementById("info");
        results.innerHTML = "";
    }

    function downloadImg(source, urlFn, element, directory) {
        var filename = source.substring(source.lastIndexOf("/") + 1);
        filename = (directory || "") + filename;

        function download(fileSystem) {
            var ft = new FileTransfer();
            console.log("Starting download");

            var progress = document.getElementById("loadingStatus");
            progress.value = 0;

            ft.onprogress = function(progressEvent) {
                if (progressEvent.lengthComputable) {
                    var currPercents = parseInt(100 * (progressEvent.loaded / progressEvent.total), 10);
                    if (currPercents > progress.value) {
                        progress.value = currPercents;
                    }
                } else {
                    progress.value = null;
                }
            };

            ft.download(source, fileSystem.root.toURL() + filename, function (entry) {
                console.log("Download complete");
                element.src = urlFn(entry);
                console.log("Src URL is " + element.src);
                console.log("Inserting element");
                document.getElementById("info").appendChild(element);
            }, function (e) { console.log("ERROR: ft.download " + e.code); });
        }
        console.log("Requesting filesystem");
        clearResults();
        window.requestFileSystem(LocalFileSystem.TEMPORARY, 0, function (fileSystem) {
            console.log("Checking for existing file");
            if (typeof directory !== "undefined") {
                console.log("Checking for existing directory.");
                fileSystem.root.getDirectory(directory, {}, function (dirEntry) {
                    dirEntry.removeRecursively(function () {
                        download(fileSystem);
                    }, function () { console.log("ERROR: dirEntry.removeRecursively"); });
                }, function () {
                    download(fileSystem);
                });
            } else {
                fileSystem.root.getFile(filename, { create: false }, function (entry) {
                    console.log("Removing existing file");
                    entry.remove(function () {
                        download(fileSystem);
                    }, function () { console.log("ERROR: entry.remove"); });
                }, function () {
                    download(fileSystem);
                });
            }
        }, function () { console.log("ERROR: requestFileSystem"); });
    }

    /******************************************************************************/

    var progress_tag = "<progress id=\"loadingStatus\" value=\"0\" max=\"100\" style=\"width: 100%;\"></progress>";
    var file_transfer_tests = "<h2>Image File Transfer Tests</h2>" +
        "<h3>The following tests should display an image of the Apache feather in the status box</h3>" +
        "<div id=\"cdv_image\"></div>" +
        "<div id=\"native_image\"></div>" +
        "<div id=\"non-existent_dir\"></div>" +
        "<h2>Video File Transfer Tests</h2>" +
        "<h3>The following tests should display a video in the status box. The video should play when play is pressed</h3>" +
        "<div id=\"cdv_video\"></div>" +
        "<div id=\"native_video\"></div>";

    contentEl.innerHTML = "<div id=\"info\"></div>" + "<br>" + progress_tag +
        file_transfer_tests;

    createActionButton("Download and display img (cdvfile)", function () {
        downloadImg(imageURL, function (entry) { return entry.toInternalURL(); }, new Image());
    }, "cdv_image");

    createActionButton("Download and display img (native)", function () {
        downloadImg(imageURL, function (entry) { return entry.toURL(); }, new Image());
    }, "native_image");

    createActionButton("Download to a non-existent dir (should work)", function () {
        downloadImg(imageURL, function (entry) { return entry.toURL(); }, new Image(), "/nonExistentDirTest/");
    }, "non-existent_dir");

    createActionButton("Download and play video (cdvfile)", function () {
        var videoElement = document.createElement("video");
        videoElement.controls = "controls";
        downloadImg(videoURL, function (entry) { return entry.toInternalURL(); }, videoElement);
    }, "cdv_video");

    createActionButton("Download and play video (native)", function () {
        var videoElement = document.createElement("video");
        videoElement.controls = "controls";
        downloadImg(videoURL, function (entry) { return entry.toURL(); }, videoElement);
    }, "native_video");
};
