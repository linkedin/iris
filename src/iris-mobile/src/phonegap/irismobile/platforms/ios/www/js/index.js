// var app = {
//     // Application Constructor
//     initialize: function() {
//         this.bindEvents();
//     },
//     // Bind Event Listeners
//     //
//     // Bind any events that are required on startup. Common events are:
//     // 'load', 'deviceready', 'offline', and 'online'.
//     bindEvents: function() {
//         document.addEventListener('deviceready', this.onDeviceReady, false);
//     },
//     // deviceready Event Handler
//     //
//     // The scope of 'this' is the event. In order to call the 'receivedEvent'
//     // function, we must explicitly call 'app.receivedEvent(...);'
//     onDeviceReady: function() {
//         console.log('registration event');
//
//         //Initialize the PushNotification plugin and register an event handler for a registration event.
//         app.push = PushNotification.init({
//             "android": {
//                 "senderID": "83269765492"
//             },
//             "ios": {
//               "sound": true,
//               "vibration": true,
//               "badge": true
//             },
//             "windows": {}
//         });
//
//         app.push.on('registration', function(data) {
//             console.log("registration event: " + data.registrationId);
//             document.getElementById("regId").innerHTML = data.registrationId;
//             alert(data.registrationId);
//
//             //send regid to server
//             $.ajax({
//               url: "http://172.22.226.77:8000/push?regId="+data.registrationId,
//               type: 'GET',
//               dataType: 'json', // added data type
//               success: function(res) {
//                   console.log(res);
//                   //alert(res);
//               },
//               error: function (xhr, ajaxOptions, thrownError) {
//               //  alert(xhr.status);
//               //  alert(thrownError);
//              }
//           });
//
//             var oldRegId = localStorage.getItem('registrationId');
//             if (oldRegId !== data.registrationId) {
//                 // Save new registration ID
//                 localStorage.setItem('registrationId', data.registrationId);
//                 // Post registrationId to your app server as the value has changed
//             }
//         });
//
//         app.push.on('error', function(e) {
//             alert("push error = " + e.message);
//         });
//
//         app.push.on('notification', function(data) {
//            alert('notification event'+ JSON.stringify(data) );
//
//        });
//
//     }
// };
//
// app.initialize();
