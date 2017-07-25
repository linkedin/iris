var platform;
function onDeviceReady() {
    platform = device.platform.toLowerCase();
    if(platform.match(/win/)){
        platform = "windows";
    }

    $('body').addClass(platform);

    // Bind events
    $(document).on("resume", onResume);


    // create/open SQLite db for storing secret and username
    var myDB = window.sqlitePlugin.openDatabase({name: "irisMobile.db", location: 'default'});

    //create new table in db
    myDB.transaction(function(transaction) {
    transaction.executeSql('CREATE TABLE IF NOT EXISTS data (username text primary key, secret text)', [],
    function(tx, result) {
    console.log("Table created successfully");
    },
    function(error) {
    alert("SQLite: Error occurred while creating the table.");
    });
    });




    // Register change listeners for Android
    if(platform === "android"){
        cordova.plugins.diagnostic.registerPermissionRequestCompleteHandler(function(statuses){
            console.info("Permission request complete");
            for (var permission in statuses){
                switch(statuses[permission]){
                    case cordova.plugins.diagnostic.permissionStatus.GRANTED:
                        console.log("Permission granted to use "+permission);
                        break;
                    case cordova.plugins.diagnostic.permissionStatus.NOT_REQUESTED:
                        console.log("Permission to use "+permission+" has not been requested yet");
                        break;
                    case cordova.plugins.diagnostic.permissionStatus.DENIED:
                        console.log("Permission denied to use "+permission);
                        break;
                    case cordova.plugins.diagnostic.permissionStatus.DENIED_ALWAYS:
                        console.log("Permission permanently denied to use "+permission);
                        break;
                }
            }
        });

    }

    //scan qr code and insert into db
    $('#use-camera').on("click", function(){
      cordova.plugins.barcodeScanner.scan(
        function (result) {
          if(!result.cancelled)
          {
            //check that scanned code is QR code
            if(result.format == "QR_CODE")
            {


              var username =  window.localStorage.getItem("username");
              var secret = result.text;

              //delete to make sure there is only ever one user
              myDB.transaction(function(transaction) {
              var executeQuery = "DELETE FROM data ";
              transaction.executeSql(executeQuery, [],
               //On Success
               function(tx, result) {console.log('Delete successfully');},
               //On Error
               function(error){alert('SQLite: Something went Wrong deleting');});
               });

              myDB.transaction(function(transaction) {
              var executeQuery = "INSERT OR IGNORE INTO data (username, secret) VALUES (?,?)";
              transaction.executeSql(executeQuery, [username,secret]
              , function(tx, result) {
                console.log('Inserted');
                getCode(username,secret);
              },
              function(error){
              alert('SQLite: Error occurred inserting into table');
              });
              });




            }
            else{
              alert('Not recognized as QR code, try again');
            }


          }
          else
          {
            alert("You have cancelled scan");
          }
        },
        function (error) {
            alert("Scanning failed: " + error);
        }
        );
    });

    // iOS+Android settings
    $('#request-camera').on("click", function(){
        cordova.plugins.diagnostic.requestCameraAuthorization({
            successCallback: function(status){
                console.log("Successfully requested camera authorization: authorization was " + status);
                checkState();
            },
            errorCallback: function(error){
                console.error(error);
            },
            externalStorage: true
        });
    });





    $('#request-camera-roll').on("click", function(){
        cordova.plugins.diagnostic.requestCameraRollAuthorization(function(status){
            console.log("Successfully requested camera roll authorization: authorization was " + status);
            checkState();
        }, function(error){
            console.error(error);
        });
    });







    if(platform === "ios") {
        // Setup background refresh request
        var Fetcher = window.BackgroundFetch;
        var fetchCallback = function() {
            console.log('BackgroundFetch initiated');
            $.get({
                url: 'index.html',
                callback: function(response) {
                    console.log("BackgroundFetch successful");
                    Fetcher.finish();
                }
            });
        };
        var failureCallback = function() {
            console.error('- BackgroundFetch failed');
        };
        Fetcher.configure(fetchCallback, failureCallback, {
            stopOnTerminate: true
        });

        // Setup push notifications
        var push = PushNotification.init({
            "android": {
                "senderID": "123456789"
            },
            "ios": {
                "sound": true,
                "alert": true,
                "badge": true
            },
            "windows": {}
        });

        push.on('registration', function(data) {
            console.log("registration event: " + data.registrationId);
        });

        push.on('error', function(e) {
            console.log("push error = " + e.message);
        });
    }

    setTimeout(checkState, 500);
}


function checkState(){
    console.log("Checking state...");

    $('#state li').removeClass('on off');


    // Camera
    var onGetCameraAuthorizationStatus;
    cordova.plugins.diagnostic.isCameraAvailable({
        successCallback: function(available){
            $('#state .camera').addClass(available ? 'on' : 'off');
        },
        errorCallback: onError,
        externalStorage: true
    });

    if(platform === "android" || platform === "ios") {
        cordova.plugins.diagnostic.isCameraPresent(function (present) {
            $('#state .camera-present').addClass(present ? 'on' : 'off');
        }, onError);

        //check for camera, ask for authorization and then scan barcode
        cordova.plugins.diagnostic.isCameraAuthorized({
            successCallback: function (authorized) {
                $('#state .camera-authorized').addClass(authorized ? 'on' : 'off');
                if(authorized){

                }
                else{
                  cordova.plugins.diagnostic.requestCameraAuthorization({
                      successCallback: function(status){
                          console.log("Successfully requested camera authorization: authorization was " + status);
                          checkState();
                      },
                      errorCallback: function(error){
                          console.error(error);
                      },
                      externalStorage: true
                  });
                }


            },
            errorCallback: onError,
            externalStorage: true
        });

        cordova.plugins.diagnostic.getCameraAuthorizationStatus({
            successCallback: function (status) {
                $('#state .camera-authorization-status').find('.value').text(status.toUpperCase());
                onGetCameraAuthorizationStatus(status);
            },
            errorCallback: onError,
            externalStorage: true
        });

    }

    if(platform === "ios"){
        cordova.plugins.diagnostic.isCameraRollAuthorized(function(authorized){
            $('#state .camera-roll-authorized').addClass(authorized ? 'on' : 'off');
        }, onError);

        cordova.plugins.diagnostic.getCameraRollAuthorizationStatus(function(status){
            $('#state .camera-roll-authorization-status').find('.value').text(status.toUpperCase());
            $('#request-camera-roll').toggle(status === cordova.plugins.diagnostic.permissionStatus.NOT_REQUESTED);
        }, onError);

        onGetCameraAuthorizationStatus = function(status){
            $('#request-camera').toggle(status === cordova.plugins.diagnostic.permissionStatus.NOT_REQUESTED);
        }
    }

    if(platform === "android"){
        onGetCameraAuthorizationStatus = function(status){
            $('#request-camera').toggle(status != cordova.plugins.diagnostic.permissionStatus.GRANTED && status != cordova.plugins.diagnostic.permissionStatus.DENIED_ALWAYS);
        }
    }


    if(platform === "ios") {

        // Background refresh
        cordova.plugins.diagnostic.isBackgroundRefreshAuthorized(function (enabled) {
            $('#state .background-refresh-authorized').addClass(enabled ? 'on' : 'off');
        }, onError);

        cordova.plugins.diagnostic.getBackgroundRefreshStatus(function (status) {
            $('#state .background-refresh-authorization-status').find('.value').text(status.toUpperCase());
        }, onError);

        // Remote notifications
        cordova.plugins.diagnostic.isRemoteNotificationsEnabled(function (enabled) {
            $('#state .remote-notifications-enabled').addClass(enabled ? 'on' : 'off');
        }, onError);

        cordova.plugins.diagnostic.isRegisteredForRemoteNotifications(function (enabled) {
            $('#state .remote-notifications-registered').addClass(enabled ? 'on' : 'off');
        }, onError);

        cordova.plugins.diagnostic.getRemoteNotificationTypes(function (types) {
            var value = "";
            for (var type in types){
                value += type + "=" + (types[type] ? "Y" : "N") +"; ";
            }
            $('#state .remote-notifications-types').find('.value').text(value);
        }, onError);

    }


}

function onError(error){
    console.error("An error occurred: "+error);
}

function onResume(){
    checkState();
}


$(document).on("deviceready", onDeviceReady);
