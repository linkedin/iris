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

このプラグインは緯度や経度などのデバイスの場所に関する情報を提供します。 位置情報の共通のソースはグローバル ポジショニング システム （GPS） と IP アドレス、RFID、WiFi および Bluetooth の MAC アドレス、および GSM/cdma 方式携帯 Id などのネットワーク信号から推定される場所にもあります。 API は、デバイスの実際の場所を返すことの保証はありません。

この API は[W3C 地理位置情報 API 仕様](http://dev.w3.org/geo/api/spec-source.html)に基づいており、既に実装を提供しないデバイス上のみで実行します。

**警告**: 地理位置情報データの収集と利用を重要なプライバシーの問題を発生させます。 アプリのプライバシー ポリシーは他の当事者とデータ (たとえば、粗い、罰金、郵便番号レベル、等) の精度のレベルでは共有されているかどうか、アプリが地理位置情報データを使用する方法を議論すべきです。 地理位置情報データと一般に見なされる敏感なユーザーの居場所を開示することができますので、彼らの旅行の歴史保存されている場合。 したがって、アプリのプライバシー ポリシーに加えて、強くする必要があります (デバイス オペレーティング システムしない場合そう既に)、アプリケーションに地理位置情報データをアクセスする前に - 時間のお知らせを提供します。 その通知は、上記の (例えば、 **[ok]**を**おかげで**選択肢を提示する) によってユーザーのアクセス許可を取得するだけでなく、同じ情報を提供する必要があります。 詳細については、プライバシーに関するガイドを参照してください。

このプラグインは、グローバル `navigator.geolocation` オブジェクト (プラットフォーム行方不明ですそれ以外の場合) を定義します。

オブジェクトは、グローバル スコープでですが、このプラグインによって提供される機能は、`deviceready` イベントの後まで使用できません。

    document.addEventListener("deviceready", onDeviceReady, false);
    function onDeviceReady() {
        console.log("navigator.geolocation works well");
    }
    

## インストール

これはコルドバ 5.0 + (現在安定 1.0.0) を必要とします。

    cordova plugin add cordova-plugin-geolocation
    

コルドバの古いバージョンでも非推奨 id (古い 0.3.12 と) 経由でインストールできます。

    cordova plugin add org.apache.cordova.geolocation
    

また、レポの url 経由で直接インストールすることが可能だ (不安定)

    cordova plugin add https://github.com/apache/cordova-plugin-geolocation.git
    

## サポートされているプラットフォーム

  * アマゾン火 OS
  * アンドロイド
  * ブラックベリー 10
  * Firefox の OS
  * iOS
  * Tizen
  * Windows Phone 7 と 8
  * Windows 8
  * Windows

## メソッド

  * navigator.geolocation.getCurrentPosition
  * navigator.geolocation.watchPosition
  * navigator.geolocation.clearWatch

## オブジェクト (読み取り専用)

  * Position
  * PositionError
  * Coordinates

## navigator.geolocation.getCurrentPosition

`Position` オブジェクトを `geolocationSuccess` コールバックにパラメーターとしてデバイスの現在位置を返します。 エラーがある場合 `geolocationError` コールバックには、`PositionError` オブジェクトが渡されます。

    navigator.geolocation.getCurrentPosition(geolocationSuccess,
                                             [geolocationError],
                                             [geolocationOptions]);
    

### パラメーター

  * **geolocationSuccess**: 現在の位置を渡されるコールバック。

  * **geolocationError**: *(省略可能)*エラーが発生した場合に実行されるコールバック。

  * **geolocationOptions**: *(オプション)*地理位置情報のオプションです。

### 例

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

位置の変更が検出された場合は、デバイスの現在位置を返します。 取得されると、デバイスの新しい場所、`geolocationSuccess` コールバック パラメーターとして `位置` オブジェクトを実行します。 エラーがある場合、`geolocationError` コールバック パラメーターとして `PositionError` オブジェクトで実行します。

    var watchId = navigator.geolocation.watchPosition(geolocationSuccess,
                                                      [geolocationError],
                                                      [geolocationOptions]);
    

### パラメーター

  * **geolocationSuccess**: 現在の位置を渡されるコールバック。

  * **geolocationError**: (省略可能) エラーが発生した場合に実行されるコールバック。

  * **geolocationOptions**: (オプション) 地理位置情報のオプションです。

### 返します

  * **文字列**: 時計の位置の間隔を参照する時計 id を返します。 時計 id で使用する必要があります `navigator.geolocation.clearWatch` 停止位置の変化を監視します。

### 例

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

地理位置情報 `の位置` の検索をカスタマイズするための省略可能なパラメーター.

    { maximumAge: 3000, timeout: 5000, enableHighAccuracy: true };
    

### オプション

  * **enableHighAccuracy**： 最高の結果が、アプリケーションに必要があることのヒントを示します。 既定では、デバイスの取得を試みます、 `Position` ネットワーク ベースのメソッドを使用します。 このプロパティを設定する `true` 衛星測位などのより正確な方法を使用するためにフレームワークに指示します。 *(ブール値)*

  * **タイムアウト**: への呼び出しから通過が許可される時間 (ミリ秒単位) の最大長 `navigator.geolocation.getCurrentPosition` または `geolocation.watchPosition` まで対応する、 `geolocationSuccess` コールバックを実行します。 場合は、 `geolocationSuccess` この時間内に、コールバックは呼び出されません、 `geolocationError` コールバックに渡される、 `PositionError.TIMEOUT` のエラー コード。 (と組み合わせて使用するときに注意してください `geolocation.watchPosition` の `geolocationError` 間隔でコールバックを呼び出すことができますすべて `timeout` ミリ秒 ！)*(数)*

  * **maximumAge**： 年齢があるミリ秒単位で指定した時間よりも大きくないキャッシュされた位置を受け入れます。*(数)*

### Android の癖

`enableHighAccuracy` オプションが `true` に設定しない限り、アンドロイド 2.x エミュレーター地理位置情報の結果を返さない.

## navigator.geolocation.clearWatch

`watchID` パラメーターによって参照される、デバイスの場所への変更を見て停止します。

    navigator.geolocation.clearWatch(watchID);
    

### パラメーター

  * **watchID**: の id、 `watchPosition` をクリアする間隔。(文字列)

### 例

    // Options: watch for changes in position, and use the most
    // accurate position acquisition method available.
    //
    var watchID = navigator.geolocation.watchPosition(onSuccess, onError, { enableHighAccuracy: true });
    
    // ...later on...
    
    navigator.geolocation.clearWatch(watchID);
    

## Position

`Position` 座標と地理位置情報 API で作成されたタイムスタンプが含まれます。

### プロパティ

  * **coords**: 地理的座標のセット。*（座標）*

  * **timestamp**: 作成のタイムスタンプを `coords` 。*（DOMTimeStamp）*

## Coordinates

`Coordinates` のオブジェクトは現在の位置のための要求でコールバック関数に使用する `Position` オブジェクトにアタッチされます。 位置の地理座標を記述するプロパティのセットが含まれています。

### プロパティ

  * **latitude**: 10 度緯度。*(数)*

  * **longitude**: 10 進度の経度。*(数)*

  * **altitude**: 楕円体上のメートルの位置の高さ。*(数)*

  * **accuracy**: メートルの緯度と経度座標の精度レベル。*(数)*

  * **altitudeAccuracy**： メートルの高度座標の精度レベル。*(数)*

  * **headingし**: 進行方向、カウント、真北から時計回りの角度で指定します。*(数)*

  * **speed**： 毎秒メートルで指定されたデバイスの現在の対地速度。*(数)*

### アマゾン火 OS 癖

**altitudeAccuracy**: `null` を返すことの Android デバイスでサポートされていません.

### Android の癖

**altitudeAccuracy**: `null` を返すことの Android デバイスでサポートされていません.

## PositionError

`PositionError` オブジェクト navigator.geolocation でエラーが発生したときに `geolocationError` コールバック関数に渡されます。

### プロパティ

  * **コード**: 次のいずれかの定義済みのエラー コード。

  * **message**: 発生したエラーの詳細を説明するエラー メッセージ。

### 定数

  * `PositionError.PERMISSION_DENIED` 
      * ユーザーの位置情報を取得するアプリを許可しない場合に返されます。これはプラットフォームに依存します。
  * `PositionError.POSITION_UNAVAILABLE` 
      * デバイスが、位置を取得することができます返されます。一般に、つまり、デバイスがネットワークに接続されていないまたは衛星の修正を得ることができません。
  * `PositionError.TIMEOUT` 
      * デバイスがで指定された時間内の位置を取得することができるときに返される、 `timeout` に含まれている `geolocationOptions` 。 使用すると `navigator.geolocation.watchPosition` 、このエラーが繰り返しに渡すことが、 `geolocationError` コールバックごと `timeout` (ミリ秒単位)。