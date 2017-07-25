$(document).ready(function() {
    document.addEventListener("deviceready", onDeviceReady, false);
});

function onDeviceReady() {
     $('#scan').click( function()
        {
          cordova.plugins.barcodeScanner.scan(
          function (result) {
              alert("We got a barcode\n" +
                    "Result: " + result.text + "\n" +
                    "Format: " + result.format + "\n" +
                    "Cancelled: " + result.cancelled);
          },
          function (error) {
              alert("Scanning failed: " + error);
          });
        }
     );
}
