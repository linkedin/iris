<!---
    Licensed to the Apache Software Foundation (ASF) under one
    or more contributor license agreements.  See the NOTICE file
    distributed with this work for additional information
    regarding copyright ownership.  The ASF licenses this file
    to you under the Apache License, Version 2.0 (the
    "License"); you may not use this file except in compliance
    with the License.  You may obtain a copy of the License at

      http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing,
    software distributed under the License is distributed on an
    "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
    KIND, either express or implied.  See the License for the
    specific language governing permissions and limitations
    under the License.
-->

# cordova-plugin-media-capture

このプラグインは、デバイスのオーディオ、イメージ、およびビデオ キャプチャ機能へのアクセスを提供します。

**警告**: イメージ、ビデオ、またはデバイスのカメラやマイクからの音声の収集と利用を重要なプライバシーの問題を発生させます。 アプリのプライバシー ポリシーは、アプリがそのようなセンサーを使用する方法と、記録されたデータは他の当事者と共有かどうかを議論すべきです。 さらに、カメラまたはマイクのアプリの使用がない場合明らかに、ユーザー インターフェイスで、前に、アプリケーションにアクセスするカメラまたはマイクを (デバイスのオペレーティング システムしない場合そう既に) - 時間のお知らせを提供する必要があります。 その通知は、上記の (例えば、 **[ok]**を**おかげで**選択肢を提示する) によってユーザーのアクセス許可を取得するだけでなく、同じ情報を提供する必要があります。 いくつかのアプリのマーケットプ レース - 時間の通知を提供して、カメラまたはマイクにアクセスする前にユーザーからアクセス許可を取得するアプリをする必要がありますに注意してください。 詳細については、プライバシーに関するガイドを参照してください。

このプラグインでは、グローバル `navigator.device.capture` オブジェクトを定義します。

グローバル スコープではあるがそれがないまで `deviceready` イベントの後です。

    document.addEventListener("deviceready", onDeviceReady, false);
    function onDeviceReady() {
        console.log(navigator.device.capture);
    }
    

## インストール

    cordova plugin add cordova-plugin-media-capture
    

## サポートされているプラットフォーム

*   アマゾン火 OS
*   アンドロイド
*   ブラックベリー 10
*   iOS
*   Windows Phone 7 と 8
*   Windows 8

## オブジェクト

*   キャプチャ
*   CaptureAudioOptions
*   CaptureImageOptions
*   CaptureVideoOptions
*   CaptureCallback
*   CaptureErrorCB
*   ConfigurationData
*   MediaFile
*   MediaFileData

## メソッド

*   capture.captureAudio
*   capture.captureImage
*   capture.captureVideo
*   MediaFile.getFormatData

## プロパティ

*   **supportedAudioModes**: デバイスでサポートされている形式の録音。（ConfigurationData[])

*   **supportedImageModes**: 記録画像サイズとデバイスでサポートされている形式です。（ConfigurationData[])

*   **supportedVideoModes**: 記録のビデオ解像度とデバイスでサポートされている形式です。（ConfigurationData[])

## capture.captureAudio

> オーディオ レコーダー アプリケーションを起動し、キャプチャしたオーディオ クリップ ファイルに関する情報を返します。

    navigator.device.capture.captureAudio(
        CaptureCB captureSuccess, CaptureErrorCB captureError,  [CaptureAudioOptions options]
    );
    

### 説明

オーディオ録音デバイスの既定のオーディオ録音アプリケーションを使用してキャプチャする非同期操作を開始します。 操作を単一のセッションで複数の録音をキャプチャするデバイスのユーザーことができます。

キャプチャ操作は、アプリケーションでは、録音を終了するか、または録音 `CaptureAudioOptions.limit` で指定された最大数に達したときに終了します。 `limit` パラメーター値が指定されていない場合既定の 1 つ （1） とキャプチャ操作をユーザーが 1 つのオーディオ クリップを録音した後終了します。

キャプチャ操作が完了したら、キャプチャしたオーディオ クリップの各ファイルを記述する `MediaFile` オブジェクトの配列を `CaptureCallback` を実行します。 場合は、ユーザー操作を終了します、オーディオ クリップをキャプチャする前に、`CaptureErrorCallback` を実行します `CaptureError` オブジェクトと `CaptureError.CAPTURE_NO_MEDIA_FILES` エラーコードをフィーチャーします。

### サポートされているプラットフォーム

*   アマゾン火 OS
*   アンドロイド
*   ブラックベリー 10
*   iOS
*   Windows Phone 7 と 8
*   Windows 8

### 例

    // capture callback
    var captureSuccess = function(mediaFiles) {
        var i, path, len;
        for (i = 0, len = mediaFiles.length; i < len; i += 1) {
            path = mediaFiles[i].fullPath;
            // do something interesting with the file
        }
    };
    
    // capture error callback
    var captureError = function(error) {
        navigator.notification.alert('Error code: ' + error.code, null, 'Capture Error');
    };
    
    // start audio capture
    navigator.device.capture.captureAudio(captureSuccess, captureError, {limit:2});
    

### iOS の癖

*   iOS に既定のオーディオ録音アプリケーションがない単純なユーザー インターフェイスが提供されます。

### Windows Phone 7 と 8 癖

*   Windows Phone 7 シンプルなユーザー インターフェイスが提供されるので、既定のオーディオ録音アプリケーションはありません。

## CaptureAudioOptions

> オーディオ キャプチャの構成オプションをカプセル化します。

### プロパティ

*   **制限**: デバイス ユーザーは、単一のキャプチャ操作で記録することができますオーディオ クリップの最大数。値 1 (デフォルトは 1) 以上にする必要があります。

*   **期間**: オーディオのサウンド クリップの最大継続時間を秒単位で。

### 例

    // limit capture operation to 3 media files, no longer than 10 seconds each
    var options = { limit: 3, duration: 10 };
    
    navigator.device.capture.captureAudio(captureSuccess, captureError, options);
    

### アマゾン火 OS 癖

*   `duration`パラメーターはサポートされていません。長さの記録プログラムで限定することはできません。

### Android の癖

*   `duration`パラメーターはサポートされていません。長さの記録プログラムで限定することはできません。

### ブラックベリー 10 癖

*   `duration`パラメーターはサポートされていません。長さの記録プログラムで限定することはできません。
*   `limit`パラメーターはサポートされていません、各呼び出しに対して、1 つだけ記録を作成できます。

### iOS の癖

*   `limit`パラメーターはサポートされていません、各呼び出しに対して、1 つだけ記録を作成できます。

## capture.captureImage

> カメラ アプリケーションを起動し、キャプチャしたイメージ ファイルに関する情報を返します。

    navigator.device.capture.captureImage(
        CaptureCB captureSuccess, CaptureErrorCB captureError, [CaptureImageOptions options]
    );
    

### 説明

デバイスのカメラ アプリケーションを使用して画像をキャプチャする非同期操作を開始します。操作では、単一のセッションで 1 つ以上のイメージをキャプチャすることができます。

キャプチャ終了操作時ユーザー カメラ アプリケーションを閉じるまたはのいずれかの `CaptureAudioOptions.limit` によって指定された録音の最大数に達した。 `limit` 値が指定されていない場合、デフォルトは 1 つ （1） キャプチャ操作が終了した後、ユーザーは単一のイメージをキャプチャします。

キャプチャ操作が完了したら、キャプチャしたイメージの各ファイルを記述する `MediaFile` オブジェクトの配列を `CaptureCB` コールバックを呼び出します。 ユーザーがイメージをキャプチャする前に操作を終了する場合 `CaptureError.CAPTURE_NO_MEDIA_FILES` のエラー コードを備え `CaptureError` オブジェクトと `CaptureErrorCB` コールバックを実行します。

### サポートされているプラットフォーム

*   アマゾン火 OS
*   アンドロイド
*   ブラックベリー 10
*   iOS
*   Windows Phone 7 と 8
*   Windows 8

### Windows Phone 7 の癖

Zune を介してお使いのデバイスが接続されているネイティブ カメラ アプリケーションを呼び出すと、動作しませんし、エラー コールバックを実行します。

### 例

    // capture callback
    var captureSuccess = function(mediaFiles) {
        var i, path, len;
        for (i = 0, len = mediaFiles.length; i < len; i += 1) {
            path = mediaFiles[i].fullPath;
            // do something interesting with the file
        }
    };
    
    // capture error callback
    var captureError = function(error) {
        navigator.notification.alert('Error code: ' + error.code, null, 'Capture Error');
    };
    
    // start image capture
    navigator.device.capture.captureImage(captureSuccess, captureError, {limit:2});
    

## CaptureImageOptions

> イメージ キャプチャの構成オプションをカプセル化します。

### プロパティ

*   **制限**: ユーザーは、単一のキャプチャ操作でキャプチャすることができますイメージの最大数。値 1 (デフォルトは 1) 以上にする必要があります。

### 例

    // limit capture operation to 3 images
    var options = { limit: 3 };
    
    navigator.device.capture.captureImage(captureSuccess, captureError, options);
    

### iOS の癖

*   **Limit**パラメーターはサポートされていませんとだけ 1 枚の画像の呼び出しごと。

## capture.captureVideo

> ビデオ レコーダー アプリケーションを起動し、キャプチャしたビデオ クリップ ファイルに関する情報を返します。

    navigator.device.capture.captureVideo(
        CaptureCB captureSuccess, CaptureErrorCB captureError, [CaptureVideoOptions options]
    );
    

### 説明

デバイスのビデオ録画アプリケーションを使用してビデオ記録をキャプチャする非同期操作を開始します。操作は、単一のセッションで 1 つ以上の録音をキャプチャすることができます。

キャプチャ操作はユーザーがビデオ録画アプリケーションを終了または `CaptureVideoOptions.limit` で指定された録音の最大数に達したときに終了します。 `limit` パラメーター値が指定されていない場合それデフォルト値は 1 (1) と、ユーザーは 1 つのビデオ クリップを記録した後にキャプチャ操作が終了しました。

キャプチャ操作が完了したら、`CaptureCB` コールバック実行に使用する各ビデオ クリップのキャプチャ ファイルを記述する `MediaFile` オブジェクトの配列。 ユーザーがビデオ クリップをキャプチャする前に操作を終了する場合 `CaptureError.CAPTURE_NO_MEDIA_FILES` のエラー コードを備え `CaptureError` オブジェクトと `CaptureErrorCB` コールバックを実行します。

### サポートされているプラットフォーム

*   アマゾン火 OS
*   アンドロイド
*   ブラックベリー 10
*   iOS
*   Windows Phone 7 と 8
*   Windows 8

### 例

    // capture callback
    var captureSuccess = function(mediaFiles) {
        var i, path, len;
        for (i = 0, len = mediaFiles.length; i < len; i += 1) {
            path = mediaFiles[i].fullPath;
            // do something interesting with the file
        }
    };
    
    // capture error callback
    var captureError = function(error) {
        navigator.notification.alert('Error code: ' + error.code, null, 'Capture Error');
    };
    
    // start video capture
    navigator.device.capture.captureVideo(captureSuccess, captureError, {limit:2});
    

### ブラックベリー 10 癖

*   ブラックベリー 10 コルドバ**ビデオ レコーダー**アプリケーションを起動し、リム、によって提供されるビデオ録画をキャプチャしようとします。 アプリは受け取ります、 `CaptureError.CAPTURE_NOT_SUPPORTED` 、アプリケーションがデバイスにインストールされていない場合はエラー コード。

## CaptureVideoOptions

> ビデオ キャプチャの構成オプションをカプセル化します。

### プロパティ

*   **制限**: デバイスのユーザーを単一のキャプチャ操作でキャプチャすることができますビデオ クリップの最大数。値 1 (デフォルトは 1) 以上にする必要があります。

*   **期間**: ビデオ クリップの最大継続時間を秒単位で。

### 例

    // limit capture operation to 3 video clips
    var options = { limit: 3 };
    
    navigator.device.capture.captureVideo(captureSuccess, captureError, options);
    

### ブラックベリー 10 癖

*   **期間**パラメーターはサポートされていませんので、録音の長さは限られたプログラムを使用することはできません。

### iOS の癖

*   **Limit**パラメーターはサポートされていません。のみ 1 つのビデオは、呼び出しごとに記録されます。

## CaptureCB

> 成功したメディア キャプチャ操作時に呼び出されます。

    function captureSuccess( MediaFile[] mediaFiles ) { ... };
    

### 説明

この関数は成功したキャプチャ操作の完了後に実行します。 いずれかのメディア ファイルをキャプチャすると、この時点で、ユーザーが終了しているメディア ・ キャプチャ ・ アプリケーションまたはキャプチャ制限に達しています。

`MediaFile` の各オブジェクトにはキャプチャしたメディア ファイルについて説明します。

### 例

    // capture callback
    function captureSuccess(mediaFiles) {
        var i, path, len;
        for (i = 0, len = mediaFiles.length; i < len; i += 1) {
            path = mediaFiles[i].fullPath;
            // do something interesting with the file
        }
    };
    

## CaptureError

> 失敗したメディア キャプチャ操作からの結果のエラー コードをカプセル化します。

### プロパティ

*   **コード**: 事前定義されたエラー コードのいずれか次のとおりです。

### 定数

*   `CaptureError.CAPTURE_INTERNAL_ERR`: カメラまたはマイクの画像やサウンドをキャプチャに失敗しました。

*   `CaptureError.CAPTURE_APPLICATION_BUSY`： 現在カメラやオーディオのキャプチャのアプリケーション別のキャプチャ要求を提供します。

*   `CaptureError.CAPTURE_INVALID_ARGUMENT`： 無効な API の使用 (例えば、の値 `limit` が 1 未満です)。

*   `CaptureError.CAPTURE_NO_MEDIA_FILES`: ユーザーが何かをキャプチャする前にカメラやオーディオのキャプチャ アプリケーションを終了します。

*   `CaptureError.CAPTURE_NOT_SUPPORTED`： 要求されたキャプチャ操作はサポートされていません。

## CaptureErrorCB

> メディア キャプチャ操作中にエラーが発生した場合に呼び出されます。

    function captureError( CaptureError error ) { ... };
    

### 説明

この関数は、エラーが発生した場合を起動しようとすると、メディア操作のキャプチャを実行します。 障害シナリオを含めますキャプチャ アプリケーションがビジー状態、キャプチャ操作は既に起こって、または、操作をキャンセルする前にメディア ファイルが自動的にキャプチャされます。

この関数は適切なエラー `code` を含む `CaptureError` オブジェクトで実行します。.

### 例

    // capture error callback
    var captureError = function(error) {
        navigator.notification.alert('Error code: ' + error.code, null, 'Capture Error');
    };
    

## ConfigurationData

> デバイスがサポートするメディア キャプチャ パラメーターのセットをカプセル化します。

### 説明

デバイスでサポートされているメディアのキャプチャのモードについて説明します。構成データには、MIME の種類、およびビデオやイメージ キャプチャのキャプチャ寸法が含まれます。

MIME の種類は [RFC2046][1] に従う必要があります。例:

 [1]: http://www.ietf.org/rfc/rfc2046.txt

*   `video/3gpp`
*   `video/quicktime`
*   `image/jpeg`
*   `audio/amr`
*   `audio/wav`

### プロパティ

*   **タイプ**: 小文字の文字列を ASCII でエンコードされたメディアの種類を表します。（，）

*   **高さ**: イメージまたはビデオのピクセルでの高さ。値は、サウンド クリップの場合は 0 です。(数)

*   **幅**: イメージまたはピクセルのビデオの幅。値は、サウンド クリップの場合は 0 です。(数)

### 例

    // retrieve supported image modes
    var imageModes = navigator.device.capture.supportedImageModes;
    
    // Select mode that has the highest horizontal resolution
    var width = 0;
    var selectedmode;
    for each (var mode in imageModes) {
        if (mode.width > width) {
            width = mode.width;
            selectedmode = mode;
        }
    }
    

任意のプラットフォームでサポートされていません。すべての構成データの配列は空です。

## MediaFile.getFormatData

> 取得についての書式情報メディア キャプチャ ファイル。

    mediaFile.getFormatData(
        MediaFileDataSuccessCB successCallback,
        [MediaFileDataErrorCB errorCallback]
    );
    

### 説明

この関数は、非同期的にメディア ファイルの形式情報を取得しようとします。 成功した場合、`MediaFileData` オブジェクトと `MediaFileDataSuccessCB` コールバックを呼び出します。 失敗した場合、この関数は `MediaFileDataErrorCB` コールバックを呼び出します。

### サポートされているプラットフォーム

*   アマゾン火 OS
*   アンドロイド
*   ブラックベリー 10
*   iOS
*   Windows Phone 7 と 8
*   Windows 8

### アマゾン火 OS 癖

API 情報にアクセスするメディア ファイル形式は限られて、それで、必ずしもすべて `MediaFileData` プロパティがサポートされます。

### ブラックベリー 10 癖

既定値を持つすべての `MediaFileData` オブジェクトを返すので、メディア ファイルについて API を提供しません。

### Android の癖

API 情報にアクセスするメディア ファイル形式は限られて、それで、必ずしもすべて `MediaFileData` プロパティがサポートされます。

### iOS の癖

API 情報にアクセスするメディア ファイル形式は限られて、それで、必ずしもすべて `MediaFileData` プロパティがサポートされます。

## MediaFile

> メディア キャプチャ ファイルのプロパティをカプセル化します。

### プロパティ

*   **名前**: パス情報なしのファイルの名前。（，）

*   **fullPath**: 名を含むファイルの完全パス。（，）

*   **タイプ**: ファイルの mime の種類 (，)

*   **ファイルサイズ**: 日付と時刻、ファイルが最後に変更されました。（日）

*   **サイズ**: バイトで、ファイルのサイズ。(数)

### メソッド

*   **MediaFile.getFormatData**: メディア ファイルの形式情報を取得します。

## MediaFileData

> メディア ファイルの形式情報をカプセル化します。

### プロパティ

*   **コーデック**： オーディオおよびビデオ コンテンツの実際のフォーマット。（，）

*   **ビットレート**： コンテンツの平均ビットレート。値が画像の場合は 0 です。(数)

*   **高さ**: イメージまたはビデオのピクセルでの高さ。値は、オーディオ クリップの場合は 0 です。(数)

*   **幅**: イメージまたはピクセルのビデオの幅。値は、オーディオ クリップの場合は 0 です。(数)

*   **期間**: 秒のビデオまたはサウンドのクリップの長さ。値が画像の場合は 0 です。(数)

### ブラックベリー 10 癖

API には、メディア ファイルの形式情報提供しません `MediaFile.getFormatData` 機能によって返される `MediaFileData` オブジェクト次の既定値。

*   **コーデック**： ないサポートされておりを返します`null`.

*   **ビットレート**： ないサポートされており、ゼロを返します。

*   **高さ**: ないサポートされており、ゼロを返します。

*   **幅**: ないサポートされており、ゼロを返します。

*   **期間**: ないサポートされており、ゼロを返します。

### アマゾン火 OS 癖

以下がサポート `MediaFileData` プロパティ。

*   **コーデック**： いないサポートしを返します`null`.

*   **ビットレート**： いないサポートし、ゼロを返します。

*   **高さ**: サポート: イメージ ファイルやビデオ ファイルのみです。

*   **幅**: サポート: イメージ ファイルやビデオ ファイルのみです。

*   **期間**: サポート: オーディオおよびビデオ ファイルのみ

### Android の癖

以下がサポート `MediaFileData` プロパティ。

*   **コーデック**： ないサポートされておりを返します`null`.

*   **ビットレート**： ないサポートされており、ゼロを返します。

*   **高さ**: サポート: イメージ ファイルやビデオ ファイルのみです。

*   **幅**: サポート: イメージ ファイルやビデオ ファイルのみです。

*   **期間**: サポート: オーディオおよびビデオ ファイルのみです。

### iOS の癖

以下がサポート `MediaFileData` プロパティ。

*   **コーデック**： ないサポートされておりを返します`null`.

*   **ビットレート**： iOS4 オーディオのみのデバイスでサポートされています。画像や動画はゼロを返します。

*   **高さ**: サポート: イメージ ファイルやビデオ ファイルのみです。

*   **幅**: サポート: イメージ ファイルやビデオ ファイルのみです。

*   **期間**: サポート: オーディオおよびビデオ ファイルのみです。
