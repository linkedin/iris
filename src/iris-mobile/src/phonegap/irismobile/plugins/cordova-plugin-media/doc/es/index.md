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

# cordova-plugin-media

Este plugin proporciona la capacidad de grabar y reproducir archivos de audio en un dispositivo.

**Nota**: la implementación actual no se adhiere a una especificación del W3C para la captura de los medios de comunicación y se proporciona únicamente para su comodidad. Una futura implementación se adherirá a la más reciente especificación W3C y puede desaprueban las API actuales.

Este plugin define un global `Media` Constructor.

Aunque en el ámbito global, no estará disponible hasta después de la `deviceready` evento.

    document.addEventListener ("deviceready", onDeviceReady, false);
    function onDeviceReady() {console.log(Media)};
    

## Instalación

    Cordova plugin agregar cordova-plugin-media
    

## Plataformas soportadas

*   Android
*   BlackBerry 10
*   iOS
*   Windows Phone 7 y 8
*   Tizen
*   Windows

## Windows Phone rarezas

*   Archivo único multimedia puede reproducir en un momento.

*   Hay restricciones estrictas sobre cómo interactúa la aplicación con otros medios. Consulte la [documentación de Microsoft para obtener más detalles][1].

 [1]: http://msdn.microsoft.com/en-us/library/windowsphone/develop/hh184838(v=vs.92).aspx

## Los medios de comunicación

    los medios de comunicación var = new Media (src, mediaSuccess, [mediaError], [mediaStatus]);
    

### Parámetros

*   **src**: un URI que contiene el contenido de audio. *(DOMString)*

*   **mediaSuccess**: (opcional) la devolución de llamada que se ejecuta después de que un objeto `Media` ha completado el juego actual, registro o acción. *(Function)*

*   **mediaError**: (opcional) la devolución de llamada que se ejecuta si se produce un error. *(Función)*

*   **mediaStatus**: (opcional) la devolución de llamada que se ejecuta para indicar cambios en el estado. *(Función)*

### Constantes

Las siguientes constantes son reportadas como el único parámetro a la `mediaStatus` callback:

*   `Media.MEDIA_NONE` = 0;
*   `Media.MEDIA_STARTING` = 1;
*   `Media.MEDIA_RUNNING` = 2;
*   `Media.MEDIA_PAUSED` = 3;
*   `Media.MEDIA_STOPPED` = 4;

### Métodos

*   `media.getCurrentPosition`: devuelve la posición actual dentro de un archivo de audio.

*   `media.getDuration`: devuelve la duración de un archivo de audio.

*   `media.play`: iniciar o reanudar reproducción de un archivo de audio.

*   `media.pause`: pausar la reproducción de un archivo de audio.

*   `media.release`: libera recursos de audio del sistema operativo subyacente.

*   `media.seekTo`: mueve la posición dentro del archivo de audio.

*   `media.setVolume`: ajuste el volumen de reproducción de audio.

*   `media.startRecord`: iniciar la grabación de un archivo de audio.

*   `media.stopRecord`: dejar de grabar un archivo de audio.

*   `media.stop`: deja de jugar a un archivo de audio.

### Parámetros adicionales ReadOnly

*   **posición**: la posición dentro de la reproducción de audio, en segundos.
    
    *   No actualizada automáticamente durante la reproducción; Llame a `getCurrentPosition` para actualizar.

*   **duration**: la duración de los medios de comunicación, en segundos.

## media.getCurrentPosition

Devuelve la posición actual dentro de un archivo de audio. También actualiza el `Media` del objeto `position` parámetro.

    media.getCurrentPosition (mediaSuccess, [mediaError]);
    

### Parámetros

*   **mediaSuccess**: la devolución de llamada que se pasa a la posición actual en segundos.

*   **mediaError**: (opcional) la devolución de llamada para ejecutar si se produce un error.

### Ejemplo rápido

    Reproductor de audio / / var my_media = new Media (src, onSuccess, onError);
    
    Actualización medios posición cada segundo var mediaTimer = setInterval(function () {/ / obtener medios posición my_media.getCurrentPosition (/ / función de devolución de llamada de éxito (posición) {si (posición > -1) {console.log((position) + "sec");
                }}, / / función de callback de error (e) {console.log ("Error al obtener pos =" + e);
            }
        );
    }, 1000);
    

## media.getDuration

Devuelve la duración de un archivo de audio en segundos. Si se desconoce la duración, devuelve un valor de -1.

    media.getDuration();
    

### Ejemplo rápido

    Reproductor de audio / / var my_media = new Media (src, onSuccess, onError);
    
    Obtener contador duración var = 0;
    var timerDur = setInterval(function() {contador = contador + 100;
        Si (contador > 2000) {clearInterval(timerDur);
        } var dur = my_media.getDuration();
        Si (dur > 0) {clearInterval(timerDur);
            document.getElementById('audio_duration').innerHTML = (dur) + "sec";
        }}, 100);
    

## media.pause

Detiene temporalmente la reproducción de un archivo de audio.

    media.Pause();
    

### Ejemplo rápido

    Reproducir audio / / function playAudio(url) {/ / reproducción del archivo de audio en my_media var url = new Media (url, / / función de devolución de llamada de éxito () {console.log ("(playAudio): Audio éxito");}, / / función de callback de error (err) {console.log ("(playAudio): Audio Error:" + err);});
    
        Reproducir audio my_media.play();
    
        Hacer una pausa después de 10 segundos setTimeout (function () {media.pause();
        }, 10000);
    }
    

## media.play

Inicia o reanuda la reproducción de un archivo de audio.

    media.Play();
    

### Ejemplo rápido

    Reproducir audio / / function playAudio(url) {/ / reproducción del archivo de audio en el url var my_media = new Media (url, / / función de devolución de llamada de éxito () {console.log ("(playAudio): Audio éxito");
            }, / / función de callback de error (err) {console.log ("(playAudio): Audio Error:" + err);
            }
        );
        Reproducir audio my_media.play();
    }
    

### iOS rarezas

*   **numberOfLoops**: pasar esta opción al método `play` para especificar el número de veces que desea que los medios de archivo para jugar, por ejemplo:
    
        var myMedia = new Media("http://audio.ibeat.org/content/p1rj1s/p1rj1s_-_rockGuitar.mp3")
        myMedia.play({ numberOfLoops: 2 })
        

*   **playAudioWhenScreenIsLocked**: pasar en esta opción el método `play` para especificar si desea permitir la reproducción cuando la pantalla está bloqueada. Si se omite establecido en `true` (el valor predeterminado), el estado del botón mute hardware, por ejemplo:
    
        var myMedia = new Media("http://audio.ibeat.org/content/p1rj1s/p1rj1s_-_rockGuitar.mp3")
        myMedia.play({ playAudioWhenScreenIsLocked : false })
        

*   **orden de búsqueda de archivos**: cuando se proporciona sólo un nombre de archivo o ruta simple, iOS busca en el directorio `www` para el archivo, luego en el directorio de la aplicación `documents/tmp`:
    
        var myMedia = new Media("audio/beer.mp3")
        myMedia.play()  // first looks for file in www/audio/beer.mp3 then in <application>/documents/tmp/audio/beer.mp3
        

## media.release

Libera los recursos de audio del sistema operativo subyacente. Esto es particularmente importante para Android, ya que hay una cantidad finita de instancias de OpenCore para la reproducción multimedia. Las aplicaciones deben llamar el `release` función para cualquier `Media` recurso que ya no es necesario.

    media.Release();
    

### Ejemplo rápido

    Reproductor de audio / / var my_media = new Media (src, onSuccess, onError);
    
    my_media.Play();
    my_media.STOP();
    my_media.Release();
    

## media.seekTo

Establece la posición actual dentro de un archivo de audio.

    media.seekTo(milliseconds);
    

### Parámetros

*   **milliseconds**: la posición para ajustar la posición de reproducción en el audio, en milisegundos.

### Ejemplo rápido

    Reproductor de audio / / var my_media = new Media (src, onSuccess, onError);
        my_media.Play();
    Buscan a 10 segundos después de 5 segundos setTimeout(function() {my_media.seekTo(10000);}, 5000);
    

### BlackBerry 10 rarezas

*   No compatible con dispositivos BlackBerry OS 5.

## media.setVolume

Ajuste el volumen para un archivo de audio.

    media.setVolume(volume);
    

### Parámetros

*   **volume**: el volumen para la reproducción. El valor debe estar dentro del rango de 0.0 a 1.0.

### Plataformas soportadas

*   Android
*   iOS

### Ejemplo rápido

    Reproducir audio / / function playAudio(url) {/ / reproducción del archivo de audio en el url var my_media = new Media (url, / / éxito callback function() {console.log ("(playAudio): Audio éxito");
            }, / / error callback function(err) {console.log ("(playAudio): Audio Error:" + err);
        });
    
        Reproducir audio my_media.play();
    
        Silenciar el volumen después de 2 segundos setTimeout(function() {my_media.setVolume('0.0');
        }, 2000);
    
        Ajustar volumen 1.0 después de 5 segundos setTimeout(function() {my_media.setVolume('1.0');
        }, 5000);
    }
    

## media.startRecord

Empieza a grabar un archivo de audio.

    media.startRecord();
    

### Plataformas soportadas

*   Android
*   iOS
*   Windows Phone 7 y 8
*   Windows

### Ejemplo rápido

    Grabar audio / / function recordAudio() {var src = "myrecording.mp3";
        var mediaRec = new Media (src, / / éxito callback function() {console.log ("(recordAudio): Audio éxito");
            }, / / error callback function(err) {console.log ("(recordAudio): Audio Error:" + err.code);
            });
    
        Grabar audio mediaRec.startRecord();
    }
    

### Rarezas Android

*   Dispositivos Android grabación audio en formato Adaptive Multi-rate. El archivo especificado debe terminar con una extensión de *.amr*.
*   Los controles de volumen del hardware están conectados hasta el volumen de los medios de comunicación, mientras que los objetos a los medios de comunicación están vivos. Una vez creado el último objeto multimedia ha `release()` llamado en él, los controles de volumen volverá a su comportamiento por defecto. Los controles también se restablecen en la navegación de la página, como esto libera todos los objetos de los medios de comunicación.

### iOS rarezas

*   iOS únicos registros a archivos de tipo *.wav* y devuelve un error si el archivo de extensión el nombre es no es correcto.

*   Si no se proporciona una ruta completa, la grabación se coloca en el directorio de la aplicación `documents/tmp`. Esto se puede acceder mediante el `File` API utilizando `LocalFileSystem.TEMPORARY`. Ya debe existir cualquier subdirectorio especificado en un tiempo récord.

*   Archivos pueden ser grabados y jugó de nuevo usando los documentos URI:
    
        var myMedia = new Media("documents://beer.mp3")
        

### Windows rarezas

*   Si no se proporciona una ruta completa, la grabación se coloca en el directorio AppData/temp. Esto puede accederse a través de la `Archivo` Usando API `LocalFileSystem.TEMPORARY` o ' ms-appdata: temporal / / / /<filename>' URI.

*   Ya debe existir cualquier subdirectorio especificado en un tiempo récord.

### Rarezas Tizen

*   No compatible con dispositivos Tizen.

## media.stop

Deja de reproducir un archivo de audio.

    media.STOP();
    

### Ejemplo rápido

    Reproducir audio / / function playAudio(url) {/ / reproducción del archivo de audio en el url var my_media = new Media (url, / / éxito callback function() {console.log ("(playAudio): Audio éxito");
            }, / / error callback function(err) {console.log ("(playAudio): Audio Error:" + err);
            }
        );
    
        Reproducir audio my_media.play();
    
        Hacer una pausa después de 10 segundos setTimeout(function() {my_media.stop();
        }, 10000);
    }
    

## media.stopRecord

Detiene la grabación de un archivo de audio.

    media.stopRecord();
    

### Plataformas soportadas

*   Android
*   iOS
*   Windows Phone 7 y 8
*   Windows

### Ejemplo rápido

    Grabar audio / / function recordAudio() {var src = "myrecording.mp3";
        var mediaRec = new Media (src, / / éxito callback function() {console.log ("(recordAudio): Audio éxito");
            }, / / error callback function(err) {console.log ("(recordAudio): Audio Error:" + err.code);
            }
        );
    
        Grabar audio mediaRec.startRecord();
    
        Detener la grabación después de 10 segundos setTimeout(function() {mediaRec.stopRecord();
        }, 10000);
    }
    

### Rarezas Tizen

*   No compatible con dispositivos Tizen.

## MediaError

A `MediaError` objeto es devuelto a la `mediaError` función de devolución de llamada cuando se produce un error.

### Propiedades

*   **code**: uno de los códigos de error predefinido enumerados a continuación.

*   **mensaje**: un mensaje de error que describe los detalles del error.

### Constantes

*   `MediaError.MEDIA_ERR_ABORTED`= 1
*   `MediaError.MEDIA_ERR_NETWORK`= 2
*   `MediaError.MEDIA_ERR_DECODE`= 3
*   `MediaError.MEDIA_ERR_NONE_SUPPORTED`= 4
