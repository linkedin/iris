<!--
# license: Licensed to the Apache Software Foundation (ASF) under one
#         or more contributor license agreements.  See the NOTICE file
#         distributed with this work for additional information
#         regarding copyright ownership.  The ASF licenses this file
#         to you under the Apache License, Version 2.0 (the
#         "License"); you may not use this file except in compliance
#         with the License.  You may obtain a copy of the License at
#
#           http://www.apache.org/licenses/LICENSE-2.0
#
#         Unless required by applicable law or agreed to in writing,
#         software distributed under the License is distributed on an
#         "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
#         KIND, either express or implied.  See the License for the
#         specific language governing permissions and limitations
#         under the License.
-->

# cordova-plugin-geolocation

[![Build Status](https://travis-ci.org/apache/cordova-plugin-geolocation.svg)](https://travis-ci.org/apache/cordova-plugin-geolocation)

這個外掛程式提供了有關該設備的位置，例如緯度和經度資訊。 常見的位置資訊來源包括全球定位系統 (GPS) 和網路信號，如 IP 位址、 RFID、 WiFi 和藍牙 MAC 位址和 GSM/CDMA 儲存格 Id 從推斷出的位置。 沒有任何保證，API 返回設備的實際位置。

此 API 基於[W3C 地理定位 API 規範](http://dev.w3.org/geo/api/spec-source.html)，並只執行已經不提供實現的設備上。

**警告**： 地理定位資料的收集和使用提出了重要的隱私問題。 您的應用程式的隱私權原則應該討論這款應用程式如何使用地理定位資料，資料是否共用它的任何其他締約方和的資料 （例如，粗、 細，ZIP 代碼級別，等等） 的精度水準。 地理定位資料一般認為是敏感，因為它能揭示使用者的下落以及如果存儲，他們的旅行的歷史。 因此，除了應用程式的隱私權原則，您應強烈考慮之前應用程式訪問地理定位資料 （如果設備作業系統不會這樣做已經) 提供在時間的通知。 該通知應提供相同的資訊上文指出的並獲取該使用者的許可權 （例如，通過為**確定**並**不感謝**提出的選擇）。 有關詳細資訊，請參閱隱私指南。

這個外掛程式定義了一個全球 `navigator.geolocation` 物件 （為平臺哪裡否則丟失）。

儘管物件是在全球範圍內，提供這個外掛程式的功能不可用直到 `deviceready` 事件之後。

    document.addEventListener("deviceready", onDeviceReady, false);
    function onDeviceReady() {
        console.log("navigator.geolocation works well");
    }
    

## 安裝

這就要求科爾多瓦 5.0 + (當前穩定 v1.0.0)

    cordova plugin add cordova-plugin-geolocation
    

舊版本的科爾多瓦仍可以通過已棄用 id (陳舊 0.3.12) 安裝

    cordova plugin add org.apache.cordova.geolocation
    

它也是可以直接通過回購 url 安裝 (不穩定)

    cordova plugin add https://github.com/apache/cordova-plugin-geolocation.git
    

## 支援的平臺

  * 亞馬遜火 OS
  * Android 系統
  * 黑莓 10
  * 火狐瀏覽器作業系統
  * iOS
  * Tizen
  * Windows Phone 7 和 8
  * Windows 8
  * Windows

## 方法

  * navigator.geolocation.getCurrentPosition
  * navigator.geolocation.watchPosition
  * navigator.geolocation.clearWatch

## 物件 （唯讀）

  * Position
  * PositionError
  * Coordinates

## navigator.geolocation.getCurrentPosition

返回設備的當前位置到 `geolocationSuccess` 回檔與 `Position` 物件作為參數。 如果有錯誤，`geolocationError` 回檔傳遞一個 `PositionError` 物件。

    navigator.geolocation.getCurrentPosition(geolocationSuccess,
                                             [geolocationError],
                                             [geolocationOptions]);
    

### 參數

  * **geolocationSuccess**： 傳遞當前位置的回檔。

  * **geolocationError**： *（可選）*如果錯誤發生時執行的回檔。

  * **geolocationOptions**： *（可選）*地理定位選項。

### 示例

    // onSuccess Callback
    // This method accepts a Position object, which contains the
    // current GPS coordinates
    //
    var onSuccess = function(position) {
        alert('Latitude: '          + position.coords.latitude          + '\n' +
              'Longitude: '         + position.coords.longitude         + '\n' +
              'Altitude: '          + position.coords.altitude          + '\n' +
              'Accuracy: '          + position.coords.accuracy          + '\n' +
              'Altitude Accuracy: ' + position.coords.altitudeAccuracy  + '\n' +
              'Heading: '           + position.coords.heading           + '\n' +
              'Speed: '             + position.coords.speed             + '\n' +
              'Timestamp: '         + position.timestamp                + '\n');
    };
    
    // onError Callback receives a PositionError object
    //
    function onError(error) {
        alert('code: '    + error.code    + '\n' +
              'message: ' + error.message + '\n');
    }
    
    navigator.geolocation.getCurrentPosition(onSuccess, onError);
    

## navigator.geolocation.watchPosition

返回設備的當前的位置，當檢測到更改位置。 當設備檢索一個新位置時，則 `geolocationSuccess` 回檔執行與 `Position` 物件作為參數。 如果有錯誤，則 `geolocationError` 回檔執行同一個 `PositionError` 物件作為參數。

    var watchId = navigator.geolocation.watchPosition(geolocationSuccess,
                                                      [geolocationError],
                                                      [geolocationOptions]);
    

### 參數

  * **geolocationSuccess**： 傳遞當前位置的回檔。

  * **geolocationError**： （可選） 如果錯誤發生時執行的回檔。

  * **geolocationOptions**： （可選） 地理定位選項。

### 返回

  * **String**： 返回引用的觀看位置間隔的表 id。 應與一起使用的表 id `navigator.geolocation.clearWatch` 停止了觀看中位置的更改。

### 示例

    // onSuccess Callback
    //   This method accepts a `Position` object, which contains
    //   the current GPS coordinates
    //
    function onSuccess(position) {
        var element = document.getElementById('geolocation');
        element.innerHTML = 'Latitude: '  + position.coords.latitude      + '<br />' +
                            'Longitude: ' + position.coords.longitude     + '<br />' +
                            '<hr />'      + element.innerHTML;
    }
    
    // onError Callback receives a PositionError object
    //
    function onError(error) {
        alert('code: '    + error.code    + '\n' +
              'message: ' + error.message + '\n');
    }
    
    // Options: throw an error if no update is received every 30 seconds.
    //
    var watchID = navigator.geolocation.watchPosition(onSuccess, onError, { timeout: 30000 });
    

## geolocationOptions

若要自訂的地理 `Position` 檢索的可選參數.

    { maximumAge: 3000, timeout: 5000, enableHighAccuracy: true };
    

### 選項

  * **enableHighAccuracy**： 提供應用程式需要最佳的可能結果的提示。 預設情況下，該設備將嘗試檢索 `Position` 使用基於網路的方法。 將此屬性設置為 `true` 告訴要使用更精確的方法，如衛星定位的框架。 *(布林值)*

  * **timeout**： 時間 (毫秒) 從調用傳遞，允許的最大長度 `navigator.geolocation.getCurrentPosition` 或 `geolocation.watchPosition` 直到相應的 `geolocationSuccess` 回檔執行。 如果 `geolocationSuccess` 不會在此時間內調用回檔 `geolocationError` 傳遞回檔 `PositionError.TIMEOUT` 錯誤代碼。 (請注意，與一起使用時 `geolocation.watchPosition` 、 `geolocationError` 的時間間隔可以調用回檔每 `timeout` 毫秒!)*（人數）*

  * **maximumAge**： 接受其年齡大於指定以毫秒為單位的時間沒有緩存的位置。*（人數）*

### Android 的怪癖

Android 2.x 模擬器不除非 `enableHighAccuracy` 選項設置為 `true`，否則返回地理定位結果.

## navigator.geolocation.clearWatch

停止觀察到 `watchID` 參數所引用的設備的位置。

    navigator.geolocation.clearWatch(watchID);
    

### 參數

  * **watchID**： 的 id `watchPosition` 清除的時間間隔。（字串）

### 示例

    // Options: watch for changes in position, and use the most
    // accurate position acquisition method available.
    //
    var watchID = navigator.geolocation.watchPosition(onSuccess, onError, { enableHighAccuracy: true });
    
    // ...later on...
    
    navigator.geolocation.clearWatch(watchID);
    

## Position

包含 `Position` 座標和時間戳記，由地理位置 API 創建。

### 屬性

  * **coords**： 一組的地理座標。*（座標）*

  * **timestamp**： 創建時間戳記為 `coords` 。*（DOMTimeStamp）*

## Coordinates

`Coordinates` 的物件附加到一個 `Position` 物件，可用於在當前職位的請求中的回呼函數。 它包含一組屬性描述位置的地理座標。

### 屬性

  * **latitude**： 緯度以十進位度為單位。*（人數）*

  * **longitude**: 經度以十進位度為單位。*（人數）*

  * **altitude**： 高度在米以上橢球體中的位置。*（人數）*

  * **accuracy**： 中米的緯度和經度座標的精度級別。*（人數）*

  * **altitudeAccuracy**： 在米的海拔高度座標的精度級別。*（人數）*

  * **heading**： 旅行，指定以度為單位元數目相對於真北順時針方向。*（人數）*

  * **speed**： 當前地面速度的設備，指定在米每秒。*（人數）*

### 亞馬遜火 OS 怪癖

**altitudeAccuracy**: 不支援的 Android 設備，返回 `null`.

### Android 的怪癖

**altitudeAccuracy**: 不支援的 Android 設備，返回 `null`.

## PositionError

`PositionError` 物件將傳遞給 `geolocationError` 回呼函數中，當出現 navigator.geolocation 錯誤時發生。

### 屬性

  * **code**： 下面列出的預定義的錯誤代碼之一。

  * **message**： 描述所遇到的錯誤的詳細資訊的錯誤訊息。

### 常量

  * `PositionError.PERMISSION_DENIED` 
      * 返回當使用者不允許應用程式檢索的位置資訊。這是取決於平臺。
  * `PositionError.POSITION_UNAVAILABLE` 
      * 返回設備時，不能檢索的位置。一般情況下，這意味著該設備未連接到網路或無法獲取衛星的修復。
  * `PositionError.TIMEOUT` 
      * 返回設備時，無法在指定的時間內檢索位置 `timeout` 中包含 `geolocationOptions` 。 與一起使用時 `navigator.geolocation.watchPosition` ，此錯誤可能反復傳遞給 `geolocationError` 回檔每 `timeout` 毫秒為單位）。