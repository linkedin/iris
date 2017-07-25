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

Ce plugin permet d'enregistrer et de lire des fichiers audio sur un périphérique.

**Remarque**: l'implémentation actuelle n'est pas conforme à une spécification du W3C pour la capture de médias et est fournie pour plus de commodité seulement. Une prochaine implémentation adhèrera à la toute dernière spécification du W3C, ce qui aura probablement pour effet de déprécier l'API actuelle.

Ce plugin définit un global `Media` constructeur.

Bien que dans la portée globale, il n'est pas disponible jusqu'après la `deviceready` événement.

    document.addEventListener (« deviceready », onDeviceReady, false) ;
    function onDeviceReady() {console.log(Media);}
    

## Installation

    Cordova plugin ajouter cordova-plugin-media
    

## Plates-formes prises en charge

*   Android
*   BlackBerry 10
*   iOS
*   Windows Phone 7 et 8
*   Paciarelli
*   Windows

## Windows Phone Quirks

*   Un seul fichier média peut être lu à la fois.

*   Il y a des restrictions strictes concernant la façon dont votre application interagit avec d'autres médias. Consultez la [documentation de Microsoft pour plus d'informations][1].

 [1]: http://msdn.microsoft.com/en-us/library/windowsphone/develop/hh184838(v=vs.92).aspx

## Media

    médias var = new Media (src, mediaSuccess, [mediaError], [mediaStatus]) ;
    

### Paramètres

*   **src** : l'URI du contenu audio. *(DOMString)*

*   **mediaSuccess** : (facultative) la fonction callback exécutée après que la lecture en cours, l'action d'enregistrement ou l'arrêt de lecture de l'objet `Media` soit terminée. *(Function)*

*   **mediaError** : (facultative) la fonction callback exécutée si une erreur survient. *(Function)*

*   **mediaStatus** : (facultative) la fonction callback exécutée lors de chaque changement d'état. *(Function)*

### Constantes

Les constantes suivantes sont déclarées comme le seul paramètre à la `mediaStatus` Rappel :

*   `Media.MEDIA_NONE` = 0;
*   `Media.MEDIA_STARTING` = 1;
*   `Media.MEDIA_RUNNING` = 2;
*   `Media.MEDIA_PAUSED` = 3;
*   `Media.MEDIA_STOPPED` = 4;

### Méthodes

*   `media.getCurrentPosition` : retourne la position de lecture dans un fichier audio.

*   `media.getDuration`: retourne la durée d'un fichier audio.

*   `media.play` : permet de commencer ou reprendre la lecture d'un fichier audio.

*   `media.pause` : interrompt la lecture d'un fichier audio.

*   `media.release` : libère les ressources audio correspondantes du système d'exploitation.

*   `media.seekTo` : déplace la position de lecture au sein du fichier audio.

*   `media.setVolume` : permet de régler le volume du clip audio.

*   `media.startRecord` : commence l'enregistrement d'un fichier audio.

*   `media.stopRecord` : arrête l'enregistrement d'un fichier audio.

*   `media.stop` : arrête la lecture d'un fichier audio.

### Paramètres supplémentaires en lecture seule

*   **position** : la position de lecture sein du clip audio, en secondes.
    
    *   La valeur n'est pas automatiquement rafraichie pendant la lecture ; un appel à `getCurrentPosition` permet sa mise à jour.

*   **duration** : la durée du média, en secondes.

## media.getCurrentPosition

Retourne la position courante dans un fichier audio. Met également à jour la `Media` de l'objet `position` paramètre.

    media.getCurrentPosition (mediaSuccess, [mediaError]) ;
    

### Paramètres

*   **mediaSuccess** : la fonction callback à laquelle est transmise la position actuelle exprimée en secondes.

*   **mediaError** : (facultative) la fonction callback exécutée si une erreur se produit.

### Petit exemple

    Lecteur audio / / var my_media = new Media (src, onSuccess, onError) ;
    
    Mise à jour media positionner chaque deuxième mediaTimer de var = setInterval(function () {/ / get médias position my_media.getCurrentPosition (/ / fonction de rappel réussi (position) {si (position > -1) {console.log((position) + "secondes") ;
                }}, / / fonction de rappel d'erreur (e) {console.log ("Error getting pos =" + e) ;
            }
        );
    }, 1000) ;
    

## media.getDuration

Retourne la durée d'un fichier audio en quelques secondes. Si on ne connaît pas la durée, elle retourne la valeur -1.

    media.getDuration() ;
    

### Petit exemple

    Lecteur audio / / var my_media = new Media (src, onSuccess, onError) ;
    
    Obtenez durée var compteur = 0 ;
    var timerDur = setInterval(function() {Compteur = compteur + 100 ;
        Si (contrer > 2000) {clearInterval(timerDur) ;
        } var dur = my_media.getDuration() ;
        Si (dur > 0) {clearInterval(timerDur) ;
            document.getElementById('audio_duration').innerHTML = (dur) + "secondes" ;
        }}, 100) ;
    

## media.pause

Suspendre la lecture d'un fichier audio.

    Media.pause() ;
    

### Petit exemple

    Lire les données audio / / function playAudio(url) {/ / lire le fichier audio à my_media var url = nouveaux médias (url, / / fonction de rappel réussi () {console.log ("playAudio (): Audio succès");}, / / fonction de rappel d'erreur (err) {console.log ("playAudio (): erreur Audio:" + err);}) ;
    
        Lecture audio my_media.play() ;
    
        Pause après 10 secondes setTimeout (function () {media.pause() ;
        }, 10000) ;
    }
    

## media.play

Commence ou reprend la lecture d'un fichier audio.

    Media.Play() ;
    

### Petit exemple

    Lire les données audio / / function playAudio(url) {/ / lire le fichier audio à url var my_media = new Media (url, / / fonction de rappel réussi () {console.log ("playAudio (): Audio succès") ;
            }, / / fonction de rappel d'erreur (err) {console.log ("playAudio (): Audio Error:" + err) ;
            }
        );
        Lecture audio my_media.play() ;
    }
    

### iOS Quirks

*   **numberOfLoops** : transmettre cette option à la méthode `play` permet de spécifier le nombre de lectures à la suite d'un fichier donné, par exemple :
    
        var myMedia = new Media("http://audio.ibeat.org/content/p1rj1s/p1rj1s_-_rockGuitar.mp3")
        myMedia.play({ numberOfLoops: 2 })
        

*   **playAudioWhenScreenIsLocked** : transmettre cette option à la méthode `play` permet de spécifier si la lecture doit continuer même lorsque l'écran de l'appareil est verrouillé. Si la valeur est `true` (par défaut), le bouton matériel mute est ignoré, par exemple :
    
        var myMedia = new Media("http://audio.ibeat.org/content/p1rj1s/p1rj1s_-_rockGuitar.mp3")
        myMedia.play({ playAudioWhenScreenIsLocked : false })
        

*   **ordre de recherche de fichier** : si un nom de fichier ou chemin d'accès simple est fourni, iOS recherche d'abord le fichier correspondant dans le répertoire `www`, puis dans le répertoire `documents/tmp` appartenant à l'application :
    
        var myMedia = new Media("audio/beer.mp3")
        myMedia.play()  // recherche d'abord le fichier www/audio/beer.mp3 puis <application>/documents/tmp/audio/beer.mp3
        

## media.release

Libère les ressources audio du système d'exploitation sous-jacent. Cela est particulièrement important pour Android, puisqu'il y a une quantité finie d'instances OpenCore pour la lecture du média. Les applications doivent appeler le `release` fonction pour tout `Media` ressource qui n'est plus nécessaire.

    Media.Release() ;
    

### Petit exemple

    Lecteur audio / / var my_media = new Media (src, onSuccess, onError) ;
    
    my_media.Play() ;
    my_media.Stop() ;
    my_media.Release() ;
    

## media.seekTo

Définit la position actuelle dans un fichier audio.

    media.seekTo(milliseconds) ;
    

### Paramètres

*   **milliseconds** : la nouvelle position de lecture au sein du fichier audio, en millisecondes.

### Petit exemple

    Lecteur audio / / var my_media = new Media (src, onSuccess, onError) ;
        my_media.Play() ;
    SeekTo à 10 secondes après 5 secondes setTimeout(function() {my_media.seekTo(10000);}, 5000) ;
    

### BlackBerry 10 Quirks

*   Cette méthode n'est pas prise en charge sur les périphériques BlackBerry OS 5.

## media.setVolume

Régler le volume du fichier audio.

    media.setVolume(volume) ;
    

### Paramètres

*   **volume** : le volume à utiliser pour la lecture. La valeur doit être comprise entre 0.0 et 1.0 inclus.

### Plates-formes prises en charge

*   Android
*   iOS

### Petit exemple

    Lire les données audio / / function playAudio(url) {/ / lire le fichier audio à my_media var url = nouveaux médias (url, / / réussite rappel function() {console.log ("playAudio (): Audio succès") ;
            }, / / erreur rappel function(err) {console.log ("playAudio (): Audio Error:" + err) ;
        });
    
        Lecture audio my_media.play() ;
    
        Couper le volume après 2 secondes setTimeout(function() {my_media.setVolume('0.0') ;
        }, 2000) ;
    
        Réglez le volume à 1.0 après 5 secondes setTimeout(function() {my_media.setVolume('1.0') ;
        }, 5000) ;
    }
    

## media.startRecord

Pour démarrer l'enregistrement d'un fichier audio.

    media.startRecord() ;
    

### Plates-formes prises en charge

*   Android
*   iOS
*   Windows Phone 7 et 8
*   Windows

### Petit exemple

    Enregistrer de l'audio / / function recordAudio() {var src = « myrecording.mp3 » ;
        var mediaRec = new Media (src, / / réussite rappel function() {console.log ("recordAudio (): Audio succès") ;
            }, / / erreur rappel function(err) {console.log ("recordAudio (): Audio Error:" + err.code) ;
            });
    
        MediaRec.startRecord() audio record ;
    }
    

### Quirks Android

*   Les appareils Android enregistrent de l'audio au format Adaptive Multi-Rate. Le nom de fichier spécifié doit donc comporter une extension *.amr*.
*   Les contrôles de volume du matériel sont câblés jusqu'au volume de médias tandis que tous les objets multimédia sont vivants. Une fois créé le dernier objet multimédia a `release()` appelé à ce sujet, les contrôles de volume revenir à leur comportement par défaut. Les contrôles sont également réinitialisés sur la navigation de la page, car cela libère tous les objets multimédias.

### iOS Quirks

*   iOS produit uniquement des enregistrements sous la forme de fichier de type *.wav* et renvoie une erreur si l'extension du nom de fichier est incorrecte.

*   Si un chemin d'accès complet n'est pas précisé, l'enregistrement est placé dans le répertoire `documents/tmp` correspondant à l'application. Il sera ensuite accessible via l'API `File` en utilisant la constante `LocalFileSystem.TEMPORARY`. Tout sous-répertoire présent dans le chemin d'accès au moment de l'enregistrement doit déjà exister.

*   Les fichiers peuvent être enregistrés et lus à l'aide de l'URI des documents :
    
        var myMedia = new Media("documents://beer.mp3")
        

### Bizarreries de Windows

*   Si un chemin d'accès complet n'est pas fourni, l'enregistrement est placé dans le répertoire AppData/temp. Ce qui peut être consulté le `Fichier` À l'aide de l'API `LocalFileSystem.TEMPORARY` ou ' ms-appdata : temp / / / /<filename>' URI.

*   N'importe quel sous-répertoire spécifié au moment de l'enregistrement doit déjà exister.

### Bizarreries de paciarelli

*   Pas pris en charge sur les appareils paciarelli.

## media.stop

Arrête la lecture d'un fichier audio.

    Media.Stop() ;
    

### Petit exemple

    Lire les données audio / / function playAudio(url) {/ / lire le fichier audio à my_media var url = nouveaux médias (url, / / réussite rappel function() {console.log ("playAudio (): Audio succès") ;
            }, / / erreur rappel function(err) {console.log ("playAudio (): Audio Error:" + err) ;
            }
        );
    
        Lecture audio my_media.play() ;
    
        Pause après 10 secondes setTimeout(function() {my_media.stop() ;
        }, 10000) ;
    }
    

## media.stopRecord

Arrête d'enregistrer un fichier audio.

    media.stopRecord() ;
    

### Plates-formes prises en charge

*   Android
*   iOS
*   Windows Phone 7 et 8
*   Windows

### Petit exemple

    Enregistrer de l'audio / / function recordAudio() {var src = « myrecording.mp3 » ;
        var mediaRec = new Media (src, / / réussite rappel function() {console.log ("recordAudio (): Audio succès") ;
            }, / / erreur rappel function(err) {console.log ("recordAudio (): Audio Error:" + err.code) ;
            }
        );
    
        MediaRec.startRecord() audio record ;
    
        Arrêter l'enregistrement après 10 secondes setTimeout(function() {mediaRec.stopRecord() ;
        }, 10000) ;
    }
    

### Bizarreries de paciarelli

*   Pas pris en charge sur les appareils paciarelli.

## MediaError

A `MediaError` objet est retourné à la `mediaError` fonction de rappel lorsqu'une erreur survient.

### Propriétés

*   **code**: l'un des codes d'erreur prédéfinis énumérés ci-dessous.

*   **message**: un message d'erreur décrivant les détails de l'erreur.

### Constantes

*   `MediaError.MEDIA_ERR_ABORTED`= 1
*   `MediaError.MEDIA_ERR_NETWORK`= 2
*   `MediaError.MEDIA_ERR_DECODE`= 3
*   `MediaError.MEDIA_ERR_NONE_SUPPORTED`= 4
