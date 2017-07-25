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

# cordova-plugin-dialogs

這個外掛程式提供對一些本機對話方塊使用者介面元素，通過全球 `navigator.notification` 物件的訪問。

雖然該物件附加到全球範圍內 `導航器`，它不可用直到 `deviceready` 事件之後。

    document.addEventListener("deviceready", onDeviceReady, false);
    function onDeviceReady() {
        console.log(navigator.notification);
    }
    

## 安裝

    cordova plugin add cordova-plugin-dialogs
    

## 方法

*   `navigator.notification.alert`
*   `navigator.notification.confirm`
*   `navigator.notification.prompt`
*   `navigator.notification.beep`

## navigator.notification.alert

顯示一個自訂的警報或對話方塊框。 大多數的科爾多瓦實現使用本機的對話方塊為此功能，但某些平臺上使用瀏覽器的 `alert` 功能，這是通常不那麼可自訂。

    navigator.notification.alert(message, alertCallback, [title], [buttonName])
    

*   **message**： 消息對話方塊。*（String）*

*   **alertCallback**： 當警報對話方塊的被解雇時要調用的回檔。*（函數）*

*   **title**： 標題對話方塊。*（String）*（可選，預設值為`Alert`)

*   **buttonName**： 按鈕名稱。*（字串）*（可選，預設值為`OK`)

### 示例

    function alertDismissed() {
        // do something
    }
    
    navigator.notification.alert(
        'You are the winner!',  // message
        alertDismissed,         // callback
        'Game Over',            // title
        'Done'                  // buttonName
    );
    

### 支援的平臺

*   亞馬遜火 OS
*   Android 系統
*   黑莓 10
*   火狐瀏覽器作業系統
*   iOS
*   Tizen
*   Windows Phone 7 和 8
*   Windows 8
*   Windows

### Windows Phone 7 和 8 怪癖

*   有沒有內置瀏覽器警報，但你可以綁定一個，如下所示調用 `alert()` 在全球範圍內：
    
        window.alert = navigator.notification.alert;
        

*   兩個 `alert` 和 `confirm` 的非阻塞的調用，其中的結果才是可用的非同步。

### 火狐瀏覽器作業系統怪癖：

本機阻止 `window.alert()` 和非阻塞的 `navigator.notification.alert()` 都可。

### 黑莓 10 怪癖

`navigator.notification.alert ('message'、 confirmCallback、 'title'、 'buttonLabels')` 回檔參數被傳遞的數位 1。

## navigator.notification.confirm

顯示一個可自訂的確認對話方塊。

    navigator.notification.confirm(message, confirmCallback, [title], [buttonLabels])
    

*   **message**： 消息對話方塊。*（字串）*

*   **confirmCallback**: 要用索引 （1、 2 或 3） 按下的按鈕，或者在沒有按下按鈕 (0) 駁回了對話方塊中時調用的回檔。*（函數）*

*   **title**： 標題對話方塊。*（字串）*（可選，預設值為`Confirm`)

*   **buttonLabels**： 指定按鈕標籤的字串陣列。*（陣列）*（可選，預設值為 [ `OK,Cancel` ])

### confirmCallback

當使用者按下確認對話方塊中的按鈕之一時，將執行 `confirmCallback`。

回檔需要參數 `buttonIndex` *（編號）*，即按下的按鈕的索引。 請注意索引使用一個基於索引，因此值 `1`、 `2`、 `3` 等。

### 示例

    function onConfirm(buttonIndex) {
        alert('You selected button ' + buttonIndex);
    }
    
    navigator.notification.confirm(
        'You are the winner!', // message
         onConfirm,            // callback to invoke with index of button pressed
        'Game Over',           // title
        ['Restart','Exit']     // buttonLabels
    );
    

### 支援的平臺

*   亞馬遜火 OS
*   Android 系統
*   黑莓 10
*   火狐瀏覽器作業系統
*   iOS
*   Tizen
*   Windows Phone 7 和 8
*   Windows 8
*   Windows

### Windows Phone 7 和 8 怪癖

*   有沒有內置的瀏覽器功能的 `window.confirm` ，但你可以將它綁定通過分配：
    
        window.confirm = navigator.notification.confirm;
        

*   調用到 `alert` 和 `confirm` 的非阻塞，所以結果就是只可用以非同步方式。

### Windows 的怪癖

*   在 Windows8/8.1 它是不可能將超過三個按鈕添加到 MessageDialog 實例。

*   在 Windows Phone 8.1 它是不可能顯示有超過兩個按鈕的對話方塊。

### 火狐瀏覽器作業系統怪癖：

本機阻止 `window.confirm()` 和非阻塞的 `navigator.notification.confirm()` 都可。

## navigator.notification.prompt

顯示本機的對話方塊，是可定制的比瀏覽器的 `prompt` 功能。

    navigator.notification.prompt(message, promptCallback, [title], [buttonLabels], [defaultText])
    

*   **message**： 消息對話方塊。*（String）*

*   **promptCallback**： 要用指數 （1、 2 或 3） 按下的按鈕或對話方塊中解雇無 (0) 按下一個按鈕時調用的回檔。*（函數）*

*   **title**： 標題對話方塊。*（String）*（可選，預設值為`Alert`)

*   **buttonLabels**： 指定按鈕標籤 (可選，預設值為 `["OK"，"Cancel"]` *（陣列）* 的字串陣列)

*   **defaultText**: 預設文字方塊中輸入值 （`字串`） (可選，預設值： 空字串）

### promptCallback

當使用者按下其中一個提示對話方塊中的按鈕時，將執行 `promptCallback`。傳遞給回檔的 `results` 物件包含以下屬性：

*   **buttonIndex**： 按下的按鈕的索引。*（數）*請注意索引使用一個基於索引，因此值 `1`、 `2`、 `3` 等。

*   **input1**： 在提示對話方塊中輸入的文本。*（字串）*

### 示例

    function onPrompt(results) {
        alert("You selected button number " + results.buttonIndex + " and entered " + results.input1);
    }
    
    navigator.notification.prompt(
        'Please enter your name',  // message
        onPrompt,                  // callback to invoke
        'Registration',            // title
        ['Ok','Exit'],             // buttonLabels
        'Jane Doe'                 // defaultText
    );
    

### 支援的平臺

*   亞馬遜火 OS
*   Android 系統
*   火狐瀏覽器作業系統
*   iOS
*   Windows Phone 7 和 8
*   Windows 8
*   Windows

### Android 的怪癖

*   Android 支援最多的三個按鈕，並忽略任何更多。

*   在 Android 3.0 及更高版本，使用全息主題的設備以相反的順序顯示按鈕。

### Windows 的怪癖

*   在 Windows 上提示對話方塊是基於 html 的缺乏這種本機 api。

### 火狐瀏覽器作業系統怪癖：

本機阻止 `window.prompt()` 和非阻塞的 `navigator.notification.prompt()` 都可。

## navigator.notification.beep

該設備播放提示音的聲音。

    navigator.notification.beep(times);
    

*   **beep**： 次數重複在嗶嗶聲。*（數）*

### 示例

    // Beep twice!
    navigator.notification.beep(2);
    

### 支援的平臺

*   亞馬遜火 OS
*   Android 系統
*   黑莓 10
*   iOS
*   Tizen
*   Windows Phone 7 和 8
*   Windows 8

### 亞馬遜火 OS 怪癖

*   亞馬遜火 OS 播放預設 **設置/顯示和聲音** 板下指定的 **通知聲音**。

### Android 的怪癖

*   安卓系統播放預設 **通知鈴聲** **設置/聲音和顯示** 面板下指定。

### Windows Phone 7 和 8 怪癖

*   依賴于泛型蜂鳴音檔從科爾多瓦分佈。

### Tizen 怪癖

*   Tizen 通過播放音訊檔通過媒體 API 實現的蜂鳴聲。

*   蜂鳴音檔必須很短，必須位於應用程式的根目錄中，一個 `聲音` 子目錄和必須將命名為 `beep.wav`.
