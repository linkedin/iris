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

이 플러그인 위도 및 경도 등의 소자의 위치에 대 한 정보를 제공합니다. 일반적인 위치 정보 등 글로벌 포지셔닝 시스템 (GPS) 및 위치와 같은 IP 주소, RFID, WiFi 및 블루투스 MAC 주소 및 GSM/CDMA 셀 Id 네트워크 신호에서 유추 합니다. 보장은 없다는 API 소자의 실제 위치를 반환 합니다.

이 API [W3C Geolocation API 사양](http://dev.w3.org/geo/api/spec-source.html)에 기반 하 고 이미 구현을 제공 하지 않는 장치에만 실행 됩니다.

**경고**: 중요 한 개인 정보 보호 문제를 제기 하는 위치 정보 데이터의 수집 및 사용 합니다. 응용 프로그램의 개인 정보 보호 정책 다른 당사자와의 데이터 (예를 들어, 굵고, 괜 찮 아 요, 우편 번호, 등)의 정밀도 수준을 공유 여부를 app 지리적 데이터를 사용 하는 방법 토론 해야 한다. 그것은 사용자의 행방을 밝힐 수 있기 때문에 및 저장, 그들의 여행 역사 지리적 위치 데이터는 일반적으로 민감한 간주. 따라서, 애플 리 케이 션의 개인 정보 보호 정책 뿐만 아니라 강력 하 게 좋습니다 (해당 되는 경우 장치 운영 체제 이렇게 이미 하지 않는) 응용 프로그램 위치 정보 데이터에 액세스 하기 전에 그냥--시간 통지. 그 통지는 (예를 들어, **확인** 및 **아니오**선택 제시) 하 여 사용자의 허가 취득 뿐만 아니라, 위에서 언급 된 동일한 정보를 제공 해야 합니다. 자세한 내용은 개인 정보 보호 가이드를 참조 하십시오.

이 플러그인 (플랫폼은 그렇지 않으면 누락 된)에 대 한 전역 `navigator.geolocation` 개체를 정의 합니다.

개체가 전역 범위에 있지만,이 플러그인에 의해 제공 되는 기능 하지 사용할 수 있습니다까지 `deviceready` 이벤트 후.

    document.addEventListener("deviceready", onDeviceReady, false);
    function onDeviceReady() {
        console.log("navigator.geolocation works well");
    }
    

## 설치

코르도바 5.0 + (현재 안정적인 1.0.0) 필요

    cordova plugin add cordova-plugin-geolocation
    

코르도바의 이전 버전 사용 되지 않는 id (부실 0.3.12)를 통해 설치할 수 있습니다.

    cordova plugin add org.apache.cordova.geolocation
    

그것은 또한 배상 계약 url을 통해 직접 설치할 수 (불안정)

    cordova plugin add https://github.com/apache/cordova-plugin-geolocation.git
    

## 지원 되는 플랫폼

  * 아마존 화재 운영 체제
  * 안 드 로이드
  * 블랙베리 10
  * Firefox 운영 체제
  * iOS
  * Tizen
  * Windows Phone 7과 8
  * 윈도우 8
  * 윈도우

## 메서드

  * navigator.geolocation.getCurrentPosition
  * navigator.geolocation.watchPosition
  * navigator.geolocation.clearWatch

## (읽기 전용) 개체

  * Position
  * PositionError
  * Coordinates

## navigator.geolocation.getCurrentPosition

매개 변수 `Position` 개체와 `geolocationSuccess`를 디바이스의 현재 위치를 반환합니다. 오류가 있는 경우에, `geolocationError` 콜백 `PositionError` 개체에 전달 됩니다.

    navigator.geolocation.getCurrentPosition(geolocationSuccess,
                                             [geolocationError],
                                             [geolocationOptions]);
    

### 매개 변수

  * **geolocationSuccess**: 현재의 위치를 전달 되는 콜백.

  * **geolocationError**: *(선택 사항)* 오류가 발생 하면 실행 되는 콜백.

  * **geolocationOptions**: *(선택 사항)* 위치 옵션.

### 예를 들어

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

위치에 변화를 탐지할 때 소자의 현재 위치를 반환 합니다. 장치 새 위치를 검색 하는 경우 `geolocationSuccess` 콜백 매개 변수로 개체를 `Position`으로 실행 합니다. 오류가 있는 경우에, `geolocationError` 콜백 매개 변수로 `PositionError` 개체를 실행 합니다.

    var watchId = navigator.geolocation.watchPosition(geolocationSuccess,
                                                      [geolocationError],
                                                      [geolocationOptions]);
    

### 매개 변수

  * **geolocationSuccess**: 현재의 위치를 전달 되는 콜백.

  * **geolocationError**: (선택 사항) 오류가 발생 하면 실행 되는 콜백.

  * **geolocationOptions**: (선택 사항)는 지리적 위치 옵션.

### 반환

  * **문자열**: 시계 위치 간격을 참조 하는 시계 id를 반환 합니다. 시계 id와 함께 사용 해야 합니다 `navigator.geolocation.clearWatch` 위치 변화에 대 한 보고 중지.

### 예를 들어

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

지리적 `Position` 검색을 사용자 지정 하는 선택적 매개 변수.

    { maximumAge: 3000, timeout: 5000, enableHighAccuracy: true };
    

### 옵션

  * **enableHighAccuracy**: 힌트는 응용 프로그램에 필요한 최상의 결과 제공 합니다. 기본적으로 장치를 검색 하려고 한 `Position` 네트워크 기반 방법을 사용 하 여. 이 속성을 설정 `true` 위성 위치 등 보다 정확한 방법을 사용 하 여 프레임 워크. *(부울)*

  * **시간 제한**: 최대 시간의 길이 (밀리초) 호출에서 전달할 수 있는 `navigator.geolocation.getCurrentPosition` 또는 `geolocation.watchPosition` 해당까지 `geolocationSuccess` 콜백 실행. 경우는 `geolocationSuccess` 콜백이이 시간 내에서 호출 되지 않습니다는 `geolocationError` 콜백 전달 되는 `PositionError.TIMEOUT` 오류 코드. (함께 사용 하는 경우 `geolocation.watchPosition` , `geolocationError` 콜백 간격에서 호출 될 수 있는 모든 `timeout` 밀리초!) *(수)*

  * **maximumAge**: 밀리초 단위로 지정 된 시간 보다 더 큰 되는 캐시 위치를 수락 합니다. *(수)*

### 안 드 로이드 단점

`EnableHighAccuracy` 옵션을 `true`로 설정 되어 있지 않으면 안 드 로이드 2.x 에뮬레이터 위치 결과 반환 하지 않는.

## navigator.geolocation.clearWatch

`watchID` 매개 변수에서 참조 하는 소자의 위치 변경에 대 한 보고 중지 합니다.

    navigator.geolocation.clearWatch(watchID);
    

### 매개 변수

  * **watchID**: id는 `watchPosition` 간격을 취소 합니다. (문자열)

### 예를 들어

    // Options: watch for changes in position, and use the most
    // accurate position acquisition method available.
    //
    var watchID = navigator.geolocation.watchPosition(onSuccess, onError, { enableHighAccuracy: true });
    
    // ...later on...
    
    navigator.geolocation.clearWatch(watchID);
    

## Position

`Position` 좌표 및 지리적 위치 API에 의해 생성 하는 타임 스탬프를 포함 합니다.

### 속성

  * **coords**: 지리적 좌표 집합. *(좌표)*

  * **timestamp**: 생성 타임 스탬프에 대 한 `coords` . *(DOMTimeStamp)*

## Coordinates

`Coordinates` 개체를 현재 위치에 대 한 요청에 콜백 함수를 사용할 수 있는 `Position` 개체에 첨부 됩니다. 그것은 위치의 지리적 좌표를 설명 하는 속성 집합이 포함 되어 있습니다.

### 속성

  * **latitude**: 소수점도 위도. *(수)*

  * **longitude**: 경도 10 진수 각도. *(수)*

  * **altitude**: 높이의 타원 면 미터에 위치. *(수)*

  * **정확도**: 정확도 레벨 미터에 위도 및 경도 좌표. *(수)*

  * **altitudeAccuracy**: 미터에 고도 좌표의 정확도 수준. *(수)*

  * **heading**: 여행, 진 북을 기준으로 시계 방향으로 세도에 지정 된 방향으로. *(수)*

  * **speed**: 초당 미터에 지정 된 디바이스의 현재 땅 속도. *(수)*

### 아마존 화재 OS 단점

**altitudeAccuracy**: `null` 반환 안 드 로이드 장치에 의해 지원 되지 않습니다.

### 안 드 로이드 단점

**altitudeAccuracy**: `null` 반환 안 드 로이드 장치에 의해 지원 되지 않습니다.

## PositionError

`PositionError` 개체는 navigator.geolocation와 함께 오류가 발생 하면 `geolocationError` 콜백 함수에 전달 됩니다.

### 속성

  * **코드**: 미리 정의 된 오류 코드 중 하나가 아래에 나열 된.

  * **message**: 발생 한 오류 세부 정보를 설명 하는 오류 메시지.

### 상수

  * `PositionError.PERMISSION_DENIED` 
      * 사용자가 위치 정보를 검색 애플 리 케이 션을 허용 하지 않는 경우 반환 됩니다. 이 플랫폼에 따라 달라 집니다.
  * `PositionError.POSITION_UNAVAILABLE` 
      * 장치 위치를 검색할 수 없을 때 반환 합니다. 일반적으로,이 장치는 네트워크에 연결 되어 있지 않은 또는 위성 수정 프로그램을 얻을 수 없습니다 의미 합니다.
  * `PositionError.TIMEOUT` 
      * 장치에 지정 된 시간 내에서 위치를 검색할 수 없는 경우 반환 되는 `timeout` 에 포함 된 `geolocationOptions` . 함께 사용 될 때 `navigator.geolocation.watchPosition` ,이 오류를 반복적으로 전달 될 수는 `geolocationError` 콜백 매 `timeout` 밀리초.