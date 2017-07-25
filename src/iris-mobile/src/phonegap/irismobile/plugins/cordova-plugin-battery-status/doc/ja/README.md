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

# cordova-plugin-battery-status

[![Build Status](https://travis-ci.org/apache/cordova-plugin-battery-status.svg)](https://travis-ci.org/apache/cordova-plugin-battery-status)

このプラグインは、[バッテリ ステータス イベント API](http://www.w3.org/TR/2011/WD-battery-status-20110915/)の旧バージョンの実装を提供します.

次の 3 つを追加します `window` イベント。

  * batterystatus
  * batterycritical
  * batterylow

## インストール

    cordova plugin add cordova-plugin-battery-status
    

## batterystatus

バッテリーの充電の割合 1% 以上によって変更されたとき、またはデバイス接続している場合に発生します。

バッテリ状態ハンドラーは 2 つのプロパティを格納しているオブジェクトに渡されます。

  * **レベル**： バッテリーの充電量 （0-100) の割合。*(数)*

  * **起こしたり**： デバイスが接続されてインチ*(ブール値)*かどうかを示すブール値

通常アプリケーションに使用する必要があります `window.addEventListener` 後のイベント リスナーをアタッチする、 `deviceready` イベントが発生します。

### サポートされているプラットフォーム

  * アマゾン火 OS
  * iOS
  * アンドロイド
  * ブラックベリー 10
  * Windows Phone 7 と 8
  * Windows (Windows Phone 8.1 のみ)
  * Tizen
  * Firefox の OS

### アンドロイドとアマゾン火 OS 癖

  * 警告: Android + 火 OS 実装は欲張りな長期使用ユーザーのバッテリーを排出するでしょう。 

### Windows Phone 7 と 8 癖

Windows Phone 7 は、バッテリーのレベルを決定するネイティブ Api を提供しませんので、 `level` プロパティは使用できません。`isPlugged`パラメーター*が*サポートされています。

### Windows の癖

Windows Phone 8.1`isPlugged`パラメーターをサポートしていません。 `level`のパラメーター*is*サポートされています。

### 例

    window.addEventListener("batterystatus", onBatteryStatus, false);
    
    function onBatteryStatus(info) {
        // Handle the online event
        console.log("Level: " + info.level + " isPlugged: " + info.isPlugged);
    }
    

## batterycritical

バッテリーの充電の割合がバッテリ切れのしきい値に達したときに発生します。値は、デバイス固有です。

`batterycritical`ハンドラーは 2 つのプロパティを格納しているオブジェクトに渡されます。

  * **レベル**： バッテリーの充電量 （0-100) の割合。*(数)*

  * **起こしたり**： デバイスが接続されてインチ*(ブール値)*かどうかを示すブール値

通常アプリケーションに使用する必要があります `window.addEventListener` 一度のイベント リスナーをアタッチし、 `deviceready` イベントが発生します。

### サポートされているプラットフォーム

  * アマゾン火 OS
  * iOS
  * アンドロイド
  * ブラックベリー 10
  * Tizen
  * Firefox の OS
  * Windows (Windows Phone 8.1 のみ)

### Windows の癖

それはサポートされていないために、Windows Phone 8.1 は接続状態に関係なく`batterycritical`イベントを発生します。

### 例

    window.addEventListener("batterycritical", onBatteryCritical, false);
    
    function onBatteryCritical(info) {
        // Handle the battery critical event
        alert("Battery Level Critical " + info.level + "%\nRecharge Soon!");
    }
    

## batterylow

バッテリーの充電の割合がバッテリ低下しきい値、デバイス固有の値に達したときに発生します。

`batterylow`ハンドラーは 2 つのプロパティを格納しているオブジェクトに渡されます。

  * **レベル**： バッテリーの充電量 （0-100) の割合。*(数)*

  * **起こしたり**： デバイスが接続されてインチ*(ブール値)*かどうかを示すブール値

通常アプリケーションに使用する必要があります `window.addEventListener` 一度のイベント リスナーをアタッチし、 `deviceready` イベントが発生します。

### サポートされているプラットフォーム

  * アマゾン火 OS
  * iOS
  * アンドロイド
  * ブラックベリー 10
  * Tizen
  * Firefox の OS
  * Windows (Windows Phone 8.1 のみ)

### Windows の癖

それはサポートされていないために、Windows Phone 8.1 は接続状態に関係なく`batterylow`イベントを発生します。

### 例

    window.addEventListener("batterylow", onBatteryLow, false);
    
    function onBatteryLow(info) {
        // Handle the battery low event
        alert("Battery Level Low " + info.level + "%");
    }