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

# cordova-plugin-battery-status

Este plugin proporciona una implementación de una versión antigua de la [Batería estado eventos API][1].

 [1]: http://www.w3.org/TR/2011/WD-battery-status-20110915/

Agrega los siguientes tres `window` eventos:

*   batterystatus
*   batterycritical
*   batterylow

## Instalación

    cordova plugin add cordova-plugin-battery-status
    

## batterystatus

Este evento se desencadena cuando cambia el porcentaje de carga de la batería en menos de 1 por ciento, o si el aparato está enchufado o desenchufado.

El controlador del estado de batería se pasa un objeto que contiene dos propiedades:

*   **level**: el porcentaje de carga de la batería (0-100). *(Número)*

*   **isPlugged**: un valor booleano que indica si el dispositivo está conectado pulg *(Boolean)*

Las aplicaciones normalmente deben utilizar `window.addEventListener` para conectar un detector de eventos después de la `deviceready` evento incendios.

### Plataformas soportadas

*   Amazon fire OS
*   iOS
*   Android
*   BlackBerry 10
*   Windows Phone 7 y 8
*   Tizen
*   Firefox OS

### Windows Phone 7 y 8 rarezas

Windows Phone 7 no proporciona una API nativa para determinar el nivel de batería, lo que `level` no está disponible. El `isPlugged` parámetro *es* apoyado.

### Ejemplo

    window.addEventListener("batterystatus", onBatteryStatus, false);
    
    function onBatteryStatus(info) {
        // Handle the online event
        console.log("Level: " + info.level + " isPlugged: " + info.isPlugged);
    }
    

## batterycritical

El evento se desencadena cuando el porcentaje de carga de la batería ha alcanzado el umbral crítico de batería. El valor es específica del dispositivo.

El controlador `batterycritical` se pasa un objeto que contiene dos propiedades:

*   **level**: el porcentaje de carga de la batería (0-100). *(Número)*

*   **isPlugged**: un valor booleano que indica si el dispositivo está conectado pulg *(Boolean)*

Las aplicaciones normalmente deben utilizar `window.addEventListener` para conectar un detector de eventos una vez que se desencadene el evento `deviceready`.

### Plataformas soportadas

*   Amazon fire OS
*   iOS
*   Android
*   BlackBerry 10
*   Tizen
*   Firefox OS

### Ejemplo

    window.addEventListener("batterycritical", onBatteryCritical, false);
    
    function onBatteryCritical(info) {
        // Handle the battery critical event
        alert("Battery Level Critical " + info.level + "%\nRecharge Soon!");
    }
    

## batterylow

El evento se desencadena cuando el porcentaje de carga de la batería ha alcanzado el umbral de batería baja, el valor específico del dispositivo.

El controlador de `batterylow` se pasa un objeto que contiene dos propiedades:

*   **level**: el porcentaje de carga de la batería (0-100). *(Número)*

*   **isPlugged**: un valor booleano que indica si el dispositivo está conectado pulg *(Boolean)*

Las aplicaciones normalmente deben utilizar `window.addEventListener` para conectar un detector de eventos una vez que se desencadene el evento `deviceready`.

### Plataformas soportadas

*   Amazon fire OS
*   iOS
*   Android
*   BlackBerry 10
*   Tizen
*   Firefox OS

### Ejemplo

    window.addEventListener("batterylow", onBatteryLow, false);
    
    function onBatteryLow(info) {
        // Handle the battery low event
        alert("Battery Level Low " + info.level + "%");
    }
