cordova.define('cordova/plugin_list', function(require, exports, module) {
module.exports = [
    {
        "file": "plugins/cordova-plugin-battery-status/www/battery.js",
        "id": "cordova-plugin-battery-status.battery",
        "pluginId": "cordova-plugin-battery-status",
        "clobbers": [
            "navigator.battery"
        ]
    },
    {
        "file": "plugins/cordova-plugin-battery-status/src/browser/BatteryProxy.js",
        "id": "cordova-plugin-battery-status.Battery",
        "pluginId": "cordova-plugin-battery-status",
        "runs": true
    },
    {
        "file": "plugins/cordova-plugin-camera/www/CameraConstants.js",
        "id": "cordova-plugin-camera.Camera",
        "pluginId": "cordova-plugin-camera",
        "clobbers": [
            "Camera"
        ]
    },
    {
        "file": "plugins/cordova-plugin-camera/www/CameraPopoverOptions.js",
        "id": "cordova-plugin-camera.CameraPopoverOptions",
        "pluginId": "cordova-plugin-camera",
        "clobbers": [
            "CameraPopoverOptions"
        ]
    },
    {
        "file": "plugins/cordova-plugin-camera/www/Camera.js",
        "id": "cordova-plugin-camera.camera",
        "pluginId": "cordova-plugin-camera",
        "clobbers": [
            "navigator.camera"
        ]
    },
    {
        "file": "plugins/cordova-plugin-camera/src/browser/CameraProxy.js",
        "id": "cordova-plugin-camera.CameraProxy",
        "pluginId": "cordova-plugin-camera",
        "runs": true
    },
    {
        "file": "plugins/cordova-plugin-contacts/www/contacts.js",
        "id": "cordova-plugin-contacts.contacts",
        "pluginId": "cordova-plugin-contacts",
        "clobbers": [
            "navigator.contacts"
        ]
    },
    {
        "file": "plugins/cordova-plugin-contacts/www/Contact.js",
        "id": "cordova-plugin-contacts.Contact",
        "pluginId": "cordova-plugin-contacts",
        "clobbers": [
            "Contact"
        ]
    },
    {
        "file": "plugins/cordova-plugin-contacts/www/ContactAddress.js",
        "id": "cordova-plugin-contacts.ContactAddress",
        "pluginId": "cordova-plugin-contacts",
        "clobbers": [
            "ContactAddress"
        ]
    },
    {
        "file": "plugins/cordova-plugin-contacts/www/ContactError.js",
        "id": "cordova-plugin-contacts.ContactError",
        "pluginId": "cordova-plugin-contacts",
        "clobbers": [
            "ContactError"
        ]
    },
    {
        "file": "plugins/cordova-plugin-contacts/www/ContactField.js",
        "id": "cordova-plugin-contacts.ContactField",
        "pluginId": "cordova-plugin-contacts",
        "clobbers": [
            "ContactField"
        ]
    },
    {
        "file": "plugins/cordova-plugin-contacts/www/ContactFindOptions.js",
        "id": "cordova-plugin-contacts.ContactFindOptions",
        "pluginId": "cordova-plugin-contacts",
        "clobbers": [
            "ContactFindOptions"
        ]
    },
    {
        "file": "plugins/cordova-plugin-contacts/www/ContactName.js",
        "id": "cordova-plugin-contacts.ContactName",
        "pluginId": "cordova-plugin-contacts",
        "clobbers": [
            "ContactName"
        ]
    },
    {
        "file": "plugins/cordova-plugin-contacts/www/ContactOrganization.js",
        "id": "cordova-plugin-contacts.ContactOrganization",
        "pluginId": "cordova-plugin-contacts",
        "clobbers": [
            "ContactOrganization"
        ]
    },
    {
        "file": "plugins/cordova-plugin-contacts/www/ContactFieldType.js",
        "id": "cordova-plugin-contacts.ContactFieldType",
        "pluginId": "cordova-plugin-contacts",
        "merges": [
            ""
        ]
    },
    {
        "file": "plugins/cordova-plugin-device/www/device.js",
        "id": "cordova-plugin-device.device",
        "pluginId": "cordova-plugin-device",
        "clobbers": [
            "device"
        ]
    },
    {
        "file": "plugins/cordova-plugin-device/src/browser/DeviceProxy.js",
        "id": "cordova-plugin-device.DeviceProxy",
        "pluginId": "cordova-plugin-device",
        "runs": true
    },
    {
        "file": "plugins/cordova-plugin-device-motion/www/Acceleration.js",
        "id": "cordova-plugin-device-motion.Acceleration",
        "pluginId": "cordova-plugin-device-motion",
        "clobbers": [
            "Acceleration"
        ]
    },
    {
        "file": "plugins/cordova-plugin-device-motion/www/accelerometer.js",
        "id": "cordova-plugin-device-motion.accelerometer",
        "pluginId": "cordova-plugin-device-motion",
        "clobbers": [
            "navigator.accelerometer"
        ]
    },
    {
        "file": "plugins/cordova-plugin-device-motion/src/browser/AccelerometerProxy.js",
        "id": "cordova-plugin-device-motion.AccelerometerProxy",
        "pluginId": "cordova-plugin-device-motion",
        "runs": true
    },
    {
        "file": "plugins/cordova-plugin-device-orientation/www/CompassError.js",
        "id": "cordova-plugin-device-orientation.CompassError",
        "pluginId": "cordova-plugin-device-orientation",
        "clobbers": [
            "CompassError"
        ]
    },
    {
        "file": "plugins/cordova-plugin-device-orientation/www/CompassHeading.js",
        "id": "cordova-plugin-device-orientation.CompassHeading",
        "pluginId": "cordova-plugin-device-orientation",
        "clobbers": [
            "CompassHeading"
        ]
    },
    {
        "file": "plugins/cordova-plugin-device-orientation/www/compass.js",
        "id": "cordova-plugin-device-orientation.compass",
        "pluginId": "cordova-plugin-device-orientation",
        "clobbers": [
            "navigator.compass"
        ]
    },
    {
        "file": "plugins/cordova-plugin-device-orientation/src/browser/CompassProxy.js",
        "id": "cordova-plugin-device-orientation.CompassProxy",
        "pluginId": "cordova-plugin-device-orientation",
        "runs": true
    },
    {
        "file": "plugins/cordova-plugin-dialogs/www/notification.js",
        "id": "cordova-plugin-dialogs.notification",
        "pluginId": "cordova-plugin-dialogs",
        "merges": [
            "navigator.notification"
        ]
    },
    {
        "file": "plugins/cordova-plugin-dialogs/www/browser/notification.js",
        "id": "cordova-plugin-dialogs.notification_browser",
        "pluginId": "cordova-plugin-dialogs",
        "merges": [
            "navigator.notification"
        ]
    },
    {
        "file": "plugins/cordova-plugin-file/www/DirectoryEntry.js",
        "id": "cordova-plugin-file.DirectoryEntry",
        "pluginId": "cordova-plugin-file",
        "clobbers": [
            "window.DirectoryEntry"
        ]
    },
    {
        "file": "plugins/cordova-plugin-file/www/DirectoryReader.js",
        "id": "cordova-plugin-file.DirectoryReader",
        "pluginId": "cordova-plugin-file",
        "clobbers": [
            "window.DirectoryReader"
        ]
    },
    {
        "file": "plugins/cordova-plugin-file/www/Entry.js",
        "id": "cordova-plugin-file.Entry",
        "pluginId": "cordova-plugin-file",
        "clobbers": [
            "window.Entry"
        ]
    },
    {
        "file": "plugins/cordova-plugin-file/www/File.js",
        "id": "cordova-plugin-file.File",
        "pluginId": "cordova-plugin-file",
        "clobbers": [
            "window.File"
        ]
    },
    {
        "file": "plugins/cordova-plugin-file/www/FileEntry.js",
        "id": "cordova-plugin-file.FileEntry",
        "pluginId": "cordova-plugin-file",
        "clobbers": [
            "window.FileEntry"
        ]
    },
    {
        "file": "plugins/cordova-plugin-file/www/FileError.js",
        "id": "cordova-plugin-file.FileError",
        "pluginId": "cordova-plugin-file",
        "clobbers": [
            "window.FileError"
        ]
    },
    {
        "file": "plugins/cordova-plugin-file/www/FileReader.js",
        "id": "cordova-plugin-file.FileReader",
        "pluginId": "cordova-plugin-file",
        "clobbers": [
            "window.FileReader"
        ]
    },
    {
        "file": "plugins/cordova-plugin-file/www/FileSystem.js",
        "id": "cordova-plugin-file.FileSystem",
        "pluginId": "cordova-plugin-file",
        "clobbers": [
            "window.FileSystem"
        ]
    },
    {
        "file": "plugins/cordova-plugin-file/www/FileUploadOptions.js",
        "id": "cordova-plugin-file.FileUploadOptions",
        "pluginId": "cordova-plugin-file",
        "clobbers": [
            "window.FileUploadOptions"
        ]
    },
    {
        "file": "plugins/cordova-plugin-file/www/FileUploadResult.js",
        "id": "cordova-plugin-file.FileUploadResult",
        "pluginId": "cordova-plugin-file",
        "clobbers": [
            "window.FileUploadResult"
        ]
    },
    {
        "file": "plugins/cordova-plugin-file/www/FileWriter.js",
        "id": "cordova-plugin-file.FileWriter",
        "pluginId": "cordova-plugin-file",
        "clobbers": [
            "window.FileWriter"
        ]
    },
    {
        "file": "plugins/cordova-plugin-file/www/Flags.js",
        "id": "cordova-plugin-file.Flags",
        "pluginId": "cordova-plugin-file",
        "clobbers": [
            "window.Flags"
        ]
    },
    {
        "file": "plugins/cordova-plugin-file/www/LocalFileSystem.js",
        "id": "cordova-plugin-file.LocalFileSystem",
        "pluginId": "cordova-plugin-file",
        "clobbers": [
            "window.LocalFileSystem"
        ],
        "merges": [
            "window"
        ]
    },
    {
        "file": "plugins/cordova-plugin-file/www/Metadata.js",
        "id": "cordova-plugin-file.Metadata",
        "pluginId": "cordova-plugin-file",
        "clobbers": [
            "window.Metadata"
        ]
    },
    {
        "file": "plugins/cordova-plugin-file/www/ProgressEvent.js",
        "id": "cordova-plugin-file.ProgressEvent",
        "pluginId": "cordova-plugin-file",
        "clobbers": [
            "window.ProgressEvent"
        ]
    },
    {
        "file": "plugins/cordova-plugin-file/www/fileSystems.js",
        "id": "cordova-plugin-file.fileSystems",
        "pluginId": "cordova-plugin-file"
    },
    {
        "file": "plugins/cordova-plugin-file/www/requestFileSystem.js",
        "id": "cordova-plugin-file.requestFileSystem",
        "pluginId": "cordova-plugin-file",
        "clobbers": [
            "window.requestFileSystem"
        ]
    },
    {
        "file": "plugins/cordova-plugin-file/www/resolveLocalFileSystemURI.js",
        "id": "cordova-plugin-file.resolveLocalFileSystemURI",
        "pluginId": "cordova-plugin-file",
        "merges": [
            "window"
        ]
    },
    {
        "file": "plugins/cordova-plugin-file/www/browser/isChrome.js",
        "id": "cordova-plugin-file.isChrome",
        "pluginId": "cordova-plugin-file",
        "runs": true
    },
    {
        "file": "plugins/cordova-plugin-file/www/browser/Preparing.js",
        "id": "cordova-plugin-file.Preparing",
        "pluginId": "cordova-plugin-file",
        "runs": true
    },
    {
        "file": "plugins/cordova-plugin-file/src/browser/FileProxy.js",
        "id": "cordova-plugin-file.browserFileProxy",
        "pluginId": "cordova-plugin-file",
        "runs": true
    },
    {
        "file": "plugins/cordova-plugin-file/www/fileSystemPaths.js",
        "id": "cordova-plugin-file.fileSystemPaths",
        "pluginId": "cordova-plugin-file",
        "merges": [
            "cordova"
        ],
        "runs": true
    },
    {
        "file": "plugins/cordova-plugin-file/www/browser/FileSystem.js",
        "id": "cordova-plugin-file.firefoxFileSystem",
        "pluginId": "cordova-plugin-file",
        "merges": [
            "window.FileSystem"
        ]
    },
    {
        "file": "plugins/cordova-plugin-file-transfer/www/FileTransferError.js",
        "id": "cordova-plugin-file-transfer.FileTransferError",
        "pluginId": "cordova-plugin-file-transfer",
        "clobbers": [
            "window.FileTransferError"
        ]
    },
    {
        "file": "plugins/cordova-plugin-file-transfer/www/FileTransfer.js",
        "id": "cordova-plugin-file-transfer.FileTransfer",
        "pluginId": "cordova-plugin-file-transfer",
        "clobbers": [
            "window.FileTransfer"
        ]
    },
    {
        "file": "plugins/cordova-plugin-file-transfer/www/browser/FileTransfer.js",
        "id": "cordova-plugin-file-transfer.BrowserFileTransfer",
        "pluginId": "cordova-plugin-file-transfer",
        "clobbers": [
            "window.FileTransfer"
        ]
    },
    {
        "file": "plugins/cordova-plugin-globalization/www/GlobalizationError.js",
        "id": "cordova-plugin-globalization.GlobalizationError",
        "pluginId": "cordova-plugin-globalization",
        "clobbers": [
            "window.GlobalizationError"
        ]
    },
    {
        "file": "plugins/cordova-plugin-globalization/www/globalization.js",
        "id": "cordova-plugin-globalization.globalization",
        "pluginId": "cordova-plugin-globalization",
        "clobbers": [
            "navigator.globalization"
        ]
    },
    {
        "file": "plugins/cordova-plugin-globalization/www/browser/moment.js",
        "id": "cordova-plugin-globalization.moment",
        "pluginId": "cordova-plugin-globalization",
        "runs": true
    },
    {
        "file": "plugins/cordova-plugin-globalization/src/browser/GlobalizationProxy.js",
        "id": "cordova-plugin-globalization.GlobalizationProxy",
        "pluginId": "cordova-plugin-globalization",
        "runs": true
    },
    {
        "file": "plugins/cordova-plugin-inappbrowser/www/inappbrowser.js",
        "id": "cordova-plugin-inappbrowser.inappbrowser",
        "pluginId": "cordova-plugin-inappbrowser",
        "clobbers": [
            "cordova.InAppBrowser.open",
            "window.open"
        ]
    },
    {
        "file": "plugins/cordova-plugin-inappbrowser/src/browser/InAppBrowserProxy.js",
        "id": "cordova-plugin-inappbrowser.InAppBrowserProxy",
        "pluginId": "cordova-plugin-inappbrowser",
        "merges": [
            ""
        ]
    },
    {
        "file": "plugins/cordova-plugin-media/www/MediaError.js",
        "id": "cordova-plugin-media.MediaError",
        "pluginId": "cordova-plugin-media",
        "clobbers": [
            "window.MediaError"
        ]
    },
    {
        "file": "plugins/cordova-plugin-media/www/Media.js",
        "id": "cordova-plugin-media.Media",
        "pluginId": "cordova-plugin-media",
        "clobbers": [
            "window.Media"
        ]
    },
    {
        "file": "plugins/cordova-plugin-media/www/browser/Media.js",
        "id": "cordova-plugin-media.BrowserMedia",
        "pluginId": "cordova-plugin-media",
        "clobbers": [
            "window.Media"
        ]
    },
    {
        "file": "plugins/cordova-plugin-media-capture/www/CaptureAudioOptions.js",
        "id": "cordova-plugin-media-capture.CaptureAudioOptions",
        "pluginId": "cordova-plugin-media-capture",
        "clobbers": [
            "CaptureAudioOptions"
        ]
    },
    {
        "file": "plugins/cordova-plugin-media-capture/www/CaptureImageOptions.js",
        "id": "cordova-plugin-media-capture.CaptureImageOptions",
        "pluginId": "cordova-plugin-media-capture",
        "clobbers": [
            "CaptureImageOptions"
        ]
    },
    {
        "file": "plugins/cordova-plugin-media-capture/www/CaptureVideoOptions.js",
        "id": "cordova-plugin-media-capture.CaptureVideoOptions",
        "pluginId": "cordova-plugin-media-capture",
        "clobbers": [
            "CaptureVideoOptions"
        ]
    },
    {
        "file": "plugins/cordova-plugin-media-capture/www/CaptureError.js",
        "id": "cordova-plugin-media-capture.CaptureError",
        "pluginId": "cordova-plugin-media-capture",
        "clobbers": [
            "CaptureError"
        ]
    },
    {
        "file": "plugins/cordova-plugin-media-capture/www/MediaFileData.js",
        "id": "cordova-plugin-media-capture.MediaFileData",
        "pluginId": "cordova-plugin-media-capture",
        "clobbers": [
            "MediaFileData"
        ]
    },
    {
        "file": "plugins/cordova-plugin-media-capture/www/MediaFile.js",
        "id": "cordova-plugin-media-capture.MediaFile",
        "pluginId": "cordova-plugin-media-capture",
        "clobbers": [
            "MediaFile"
        ]
    },
    {
        "file": "plugins/cordova-plugin-media-capture/www/capture.js",
        "id": "cordova-plugin-media-capture.capture",
        "pluginId": "cordova-plugin-media-capture",
        "clobbers": [
            "navigator.device.capture"
        ]
    },
    {
        "file": "plugins/cordova-plugin-media-capture/src/browser/CaptureProxy.js",
        "id": "cordova-plugin-media-capture.CaptureProxy",
        "pluginId": "cordova-plugin-media-capture",
        "runs": true
    },
    {
        "file": "plugins/cordova-plugin-network-information/www/network.js",
        "id": "cordova-plugin-network-information.network",
        "pluginId": "cordova-plugin-network-information",
        "clobbers": [
            "navigator.connection",
            "navigator.network.connection"
        ]
    },
    {
        "file": "plugins/cordova-plugin-network-information/www/Connection.js",
        "id": "cordova-plugin-network-information.Connection",
        "pluginId": "cordova-plugin-network-information",
        "clobbers": [
            "Connection"
        ]
    },
    {
        "file": "plugins/cordova-plugin-network-information/src/browser/network.js",
        "id": "cordova-plugin-network-information.NetworkInfoProxy",
        "pluginId": "cordova-plugin-network-information",
        "runs": true
    },
    {
        "file": "plugins/cordova-plugin-splashscreen/www/splashscreen.js",
        "id": "cordova-plugin-splashscreen.SplashScreen",
        "pluginId": "cordova-plugin-splashscreen",
        "clobbers": [
            "navigator.splashscreen"
        ]
    },
    {
        "file": "plugins/cordova-plugin-splashscreen/src/browser/SplashScreenProxy.js",
        "id": "cordova-plugin-splashscreen.SplashScreenProxy",
        "pluginId": "cordova-plugin-splashscreen",
        "runs": true
    },
    {
        "file": "plugins/phonegap-plugin-barcodescanner/www/barcodescanner.js",
        "id": "phonegap-plugin-barcodescanner.BarcodeScanner",
        "pluginId": "phonegap-plugin-barcodescanner",
        "clobbers": [
            "cordova.plugins.barcodeScanner"
        ]
    },
    {
        "file": "plugins/phonegap-plugin-barcodescanner/src/browser/BarcodeScannerProxy.js",
        "id": "phonegap-plugin-barcodescanner.BarcodeScannerProxy",
        "pluginId": "phonegap-plugin-barcodescanner",
        "runs": true
    },
    {
        "file": "plugins/cordova-sqlite-storage/www/SQLitePlugin.js",
        "id": "cordova-sqlite-storage.SQLitePlugin",
        "pluginId": "cordova-sqlite-storage",
        "clobbers": [
            "SQLitePlugin"
        ]
    },
    {
        "file": "plugins/phonegap-plugin-push/www/push.js",
        "id": "phonegap-plugin-push.PushNotification",
        "pluginId": "phonegap-plugin-push",
        "clobbers": [
            "PushNotification"
        ]
    },
    {
        "file": "plugins/phonegap-plugin-push/www/browser/push.js",
        "id": "phonegap-plugin-push.BrowserPush",
        "pluginId": "phonegap-plugin-push",
        "clobbers": [
            "PushNotification"
        ]
    }
];
module.exports.metadata = 
// TOP OF METADATA
{
    "cordova-plugin-battery-status": "1.1.2",
    "cordova-plugin-camera": "2.1.1",
    "cordova-plugin-compat": "1.1.0",
    "cordova-plugin-console": "1.0.7",
    "cordova-plugin-contacts": "2.0.1",
    "cordova-plugin-device": "1.1.6",
    "cordova-plugin-device-motion": "1.2.5",
    "cordova-plugin-device-orientation": "1.0.7",
    "cordova-plugin-dialogs": "1.2.1",
    "cordova-plugin-file": "4.3.3",
    "cordova-plugin-file-transfer": "1.5.1",
    "cordova-plugin-geolocation": "2.1.0",
    "cordova-plugin-globalization": "1.0.7",
    "cordova-plugin-inappbrowser": "1.3.0",
    "cordova-plugin-media": "2.2.0",
    "cordova-plugin-media-capture": "1.2.0",
    "cordova-plugin-network-information": "1.2.1",
    "cordova-plugin-splashscreen": "3.2.2",
    "phonegap-plugin-barcodescanner": "4.1.0",
    "cordova.plugins.diagnostic": "3.6.5",
    "cordova-sqlite-storage": "2.0.4",
    "phonegap-plugin-push": "1.10.5"
}
// BOTTOM OF METADATA
});