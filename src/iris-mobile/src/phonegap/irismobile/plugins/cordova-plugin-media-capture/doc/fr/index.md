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

Ce plugin permet d'accéder à de l'appareil audio, image et capacités de capture vidéo.

**Avertissement**: collecte et utilisation des images, vidéo ou audio de la caméra ou un microphone de l'appareil soulève des questions importantes de la vie privée. La politique de confidentialité de votre application devrait traiter de la manière dont l'application utilise ces capteurs et du partage des données enregistrées avec d'autres parties ou non. En outre, si l'utilisation de l'application de la caméra ou un microphone n'est pas apparente dans l'interface utilisateur, vous devez fournir un avis juste-à-temps, avant que l'application accède à la caméra ou un microphone (si le système d'exploitation de périphérique n'est pas faire déjà). Cette notice devrait contenir les informations susmentionnées, ainsi que permettre de recueillir l'autorisation de l'utilisateur (par exemple, en offrant les possibilités **OK** et **Non merci**). Notez que certains magasins d'applications peuvent exiger la présence de ce genre de notice avant d'autoriser la distribution de votre application. Pour plus d'informations, consultez le Guide de la vie privée.

Ce plugin définit global `navigator.device.capture` objet.

Bien que dans la portée globale, il n'est pas disponible jusqu'après la `deviceready` événement.

    document.addEventListener (« deviceready », onDeviceReady, false) ;
    function onDeviceReady() {console.log(navigator.device.capture);}
    

## Installation

    Cordova plugin ajouter capture d'cordova-plugin-media
    

## Plates-formes prises en charge

*   Amazon Fire OS
*   Android
*   BlackBerry 10
*   iOS
*   Windows Phone 7 et 8
*   Windows 8

## Objets

*   Capture
*   CaptureAudioOptions
*   CaptureImageOptions
*   CaptureVideoOptions
*   CaptureCallback
*   CaptureErrorCB
*   ConfigurationData
*   MediaFile
*   MediaFileData

## Méthodes

*   capture.captureAudio
*   capture.captureImage
*   capture.captureVideo
*   MediaFile.getFormatData

## Propriétés

*   **supportedAudioModes** : les formats d'enregistrement audio supportés par l'appareil. (ConfigurationData[])

*   **supportedImageModes** : les formats et tailles de capture d'image supportés par l'appareil. (ConfigurationData[])

*   **supportedVideoModes**: les formats et résolutions d'enregistrement vidéo supportés par l'appareil. (ConfigurationData[])

## capture.captureAudio

> Ouvre l'application enregistreur audio et fournit des informations sur les fichiers audio capturés.

    navigator.device.capture.captureAudio (CaptureCB captureSuccess, CaptureErrorCB captureError, [CaptureAudioOptions options]) ;
    

### Description

Commence une opération asynchrone pour capturer les enregistrements audio à l'aide d'application d'enregistrement audio de l'appareil par défaut. L'opération permet à l'utilisateur de l'appareil capturer des enregistrements multiples en une seule séance.

L'opération de capture se termine lorsque l'utilisateur quitte l'enregistrement demande, ou le nombre maximal d'enregistrements spécifié par audio `CaptureAudioOptions.limit` est atteinte. Si aucun `limit` valeur du paramètre est spécifiée, par défaut à un (1), et l'opération de capture se termine après que l'utilisateur enregistre un clip audio unique.

Fin de l'opération de capture, le `CaptureCallback` s'exécute avec un tableau de `MediaFile` objets décrivant chacune capturé fichiers clip audio. Si l'utilisateur annule l'opération avant un clip audio est capturé, le `CaptureErrorCallback` s'exécute avec un objet `CaptureError`, mettant en vedette le code d'erreur `CaptureError.CAPTURE_NO_MEDIA_FILES`.

### Plates-formes prises en charge

*   Amazon Fire OS
*   Android
*   BlackBerry 10
*   iOS
*   Windows Phone 7 et 8
*   Windows 8

### Exemple

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
    

### iOS Quirks

*   iOS n'a pas une application d'enregistrement audio par défaut, donc une interface utilisateur simple est fournie.

### Windows Phone 7 et 8 Quirks

*   Windows Phone 7 n'a pas une application d'enregistrement audio par défaut, donc une interface utilisateur simple est fournie.

## CaptureAudioOptions

> Encapsule les options de configuration de capture audio.

### Propriétés

*   **limite**: le nombre maximal de clips audio, l'utilisateur de l'appareil permet d'enregistrer dans une opération de capture unique. La valeur doit être supérieure ou égale à 1 (1 par défaut).

*   **durée**: la durée maximale d'un clip sonore audio, en quelques secondes.

### Exemple

    // limit capture operation to 3 media files, no longer than 10 seconds each
    var options = { limit: 3, duration: 10 };
    
    navigator.device.capture.captureAudio(captureSuccess, captureError, options);
    

### Amazon Fire OS Quirks

*   Le `duration` paramètre n'est pas pris en charge. Longueurs d'enregistrement ne peut être limitée par programme.

### Quirks Android

*   Le `duration` paramètre n'est pas pris en charge. Longueurs d'enregistrement ne peut être limitée par programme.

### BlackBerry 10 Quirks

*   Le `duration` paramètre n'est pas pris en charge. Longueurs d'enregistrement ne peut être limitée par programme.
*   Le `limit` paramètre n'est pas pris en charge, ainsi qu'un enregistrement peut être créée pour chaque appel.

### iOS Quirks

*   Le `limit` paramètre n'est pas pris en charge, ainsi qu'un enregistrement peut être créée pour chaque appel.

## capture.captureImage

> Ouvre l'application appareil photo et fournit des informations sur les fichiers image capturés.

    navigator.device.capture.captureImage(
        CaptureCB captureSuccess, CaptureErrorCB captureError, [CaptureImageOptions options]
    );
    

### Description

Commence une opération asynchrone pour capturer des images à l'aide d'application caméra de l'appareil. L'opération permet aux utilisateurs de capturer plusieurs images en une seule séance.

Les extrémités d'opération de capture lorsque l'utilisateur ferme l'application appareil photo, ou le nombre maximal d'enregistrements spécifié par `CaptureAudioOptions.limit` est atteint. Si aucune valeur `limit` n'est spécifiée, par défaut à un (1), et l'opération de capture s'arrête après l'utilisateur restitue une image unique.

Lorsque l'opération de capture terminée, elle appelle le `CaptureCB` rappel avec un tableau de `MediaFile` objets décrivant chaque fichier de l'image capturée. Si l'utilisateur annule l'opération avant la capture d'une image, la `CaptureErrorCB` rappel s'exécute avec un `CaptureError` objet mettant en vedette un `CaptureError.CAPTURE_NO_MEDIA_FILES` code d'erreur.

### Plates-formes prises en charge

*   Amazon Fire OS
*   Android
*   BlackBerry 10
*   iOS
*   Windows Phone 7 et 8
*   Windows 8

### Windows Phone 7 Quirks

Invoquant l'application native caméra alors que votre appareil est connecté via Zune ne fonctionne pas, et exécute le rappel de l'erreur.

### Exemple

    capture de rappel var captureSuccess = function(mediaFiles) {var i, chemin, len ;
        pour (i = 0, len = mediaFiles.length; i < len ; j'ai += 1) {chemin d'accès = mediaFiles[i].fullPath ;
            faire quelque chose d'intéressant avec le fichier}} ;
    
    capturer l'erreur rappel var captureError = function(error) {navigator.notification.alert (' code d'erreur: ' + error.code, null, « Capture Error »);} ;
    
    démarrer l'image capture navigator.device.capture.captureImage (captureSuccess, captureError, {limit:2}) ;
    

## CaptureImageOptions

> Encapsule les options de configuration de capture d'image.

### Propriétés

*   **limite**: le nombre maximum d'images, l'utilisateur peut saisir dans une opération de capture unique. La valeur doit être supérieure ou égale à 1 (1 par défaut).

### Exemple

    limiter l'opération de capture aux options de 3 images var = { limit: 3 } ;
    
    navigator.device.capture.captureImage (captureSuccess, captureError, options) ;
    

### iOS Quirks

*   Le paramètre **limit** n'est pas pris en charge, et qu'une image est prise par l'invocation.

## capture.captureVideo

> Ouvre l'application enregistreur vidéo et fournit des informations sur les clips vidéo capturés.

    navigator.device.capture.captureVideo (CaptureCB captureSuccess, CaptureErrorCB captureError, [CaptureVideoOptions options]) ;
    

### Description

Commence une opération asynchrone pour capturer des enregistrements vidéo à l'aide de la demande d'enregistrement vidéo de l'appareil. L'opération permet à l'utilisateur de capturer plusieurs enregistrements en une seule séance.

L'opération de capture se termine lorsque l'utilisateur quitte l'application de l'enregistrement vidéo, ou le nombre maximal d'enregistrements spécifié par `CaptureVideoOptions.limit` est atteinte. Si aucun `limit` valeur du paramètre est spécifiée, par défaut à un (1), et l'opération de capture se termine après que l'utilisateur enregistre un clip vidéo unique.

Fin de l'opération de capture, il le `CaptureCB` rappel s'exécute avec un tableau de `MediaFile` objets décrivant chacune capturé clip vidéo. Si l'utilisateur annule l'opération avant la capture d'un clip vidéo, le `CaptureErrorCB` rappel s'exécute avec un `CaptureError` objet mettant en vedette un `CaptureError.CAPTURE_NO_MEDIA_FILES` code d'erreur.

### Plates-formes prises en charge

*   Amazon Fire OS
*   Android
*   BlackBerry 10
*   iOS
*   Windows Phone 7 et 8
*   Windows 8

### Exemple

    capture de rappel var captureSuccess = function(mediaFiles) {var i, chemin, len ;
        pour (i = 0, len = mediaFiles.length; i < len ; j'ai += 1) {chemin d'accès = mediaFiles[i].fullPath ;
            faire quelque chose d'intéressant avec le fichier}} ;
    
    capturer l'erreur rappel var captureError = function(error) {navigator.notification.alert (' code d'erreur: ' + error.code, null, « Capture Error »);} ;
    
    démarrer la capture vidéo navigator.device.capture.captureVideo (captureSuccess, captureError, {limit:2}) ;
    

### BlackBerry 10 Quirks

*   Cordova pour BlackBerry 10 essaie de lancer l'application **Enregistreur vidéo** , fournie par RIM, pour capturer les enregistrements vidéo. L'application reçoit un `CaptureError.CAPTURE_NOT_SUPPORTED` code d'erreur si l'application n'est pas installée sur l'appareil.

## CaptureVideoOptions

> Encapsule les options de configuration de capture vidéo.

### Propriétés

*   **limite**: le nombre maximal de clips vidéo, utilisateur de l'appareil peut capturer dans une opération de capture unique. La valeur doit être supérieure ou égale à 1 (1 par défaut).

*   **durée**: la durée maximale d'un clip vidéo, en quelques secondes.

### Exemple

    limiter l'opération de capture de 3 options de clips vidéo var = { limit: 3 } ;
    
    navigator.device.capture.captureVideo (captureSuccess, captureError, options) ;
    

### BlackBerry 10 Quirks

*   Le paramètre de **durée** n'est pas supporté, donc la longueur des enregistrements ne peut pas être limitée par programme.

### iOS Quirks

*   Le paramètre **limit** n'est pas pris en charge. Qu'une vidéo est enregistrée par l'invocation.

## CaptureCB

> Fonction appelée lors d'une opération de capture de médias réussie.

    fonction captureSuccess (MediaFile [] mediaFiles) { ... } ;
    

### Description

Cette fonction s'exécute après qu'une opération de capture réussie est terminée. À ce point qu'un fichier multimédia a été capturé et soit l'utilisateur a quitté l'application capture de média, ou la limite de capture a été atteinte.

Chaque `MediaFile` objet décrit un fichier multimédia capturés.

### Exemple

    capturer callback function captureSuccess(mediaFiles) {var i, chemin, len ;
        pour (i = 0, len = mediaFiles.length; i < len ; j'ai += 1) {chemin d'accès = mediaFiles[i].fullPath ;
            faire quelque chose d'intéressant avec le fichier}} ;
    

## CaptureError

> Encapsule le code d'erreur résultant d'une opération de capture de médias ayant échoué.

### Propriétés

*   **code**: un des codes d'erreur prédéfinis énumérés ci-dessous.

### Constantes

*   `CaptureError.CAPTURE_INTERNAL_ERR`: La caméra ou un microphone a échoué à capturer l'image ou le son.

*   `CaptureError.CAPTURE_APPLICATION_BUSY`: L'application de capture caméra / audio est actuellement une autre demande de capture.

*   `CaptureError.CAPTURE_INVALID_ARGUMENT`: Utilisation incorrecte de l'API (par exemple, la valeur de `limit` est inférieur à 1).

*   `CaptureError.CAPTURE_NO_MEDIA_FILES`: L'utilisateur quitte l'application capture audio ou de la caméra avant de capturer n'importe quoi.

*   `CaptureError.CAPTURE_NOT_SUPPORTED`: L'opération de capture demandée n'est pas pris en charge.

## CaptureErrorCB

> Fonction callback appelée si une erreur se produit pendant une opération de capture de médias.

    function captureError (erreur CaptureError) { ... } ;
    

### Description

Cette fonction s'exécute si une erreur se produit lorsque vous essayez de lancer un média opération de capture. Scénarios de défaillance incluent lors de l'application capture est occupée, une opération de capture est déjà en cours, ou l'utilisateur annule l'opération avant que tous les fichiers multimédias sont capturés.

Cette fonction s'exécute avec un `CaptureError` objet contenant une erreur appropriée`code`.

### Exemple

    capturer l'erreur rappel var captureError = function(error) {navigator.notification.alert (' code d'erreur: ' + error.code, null, « Capture Error »);} ;
    

## ConfigurationData

> Encapsule un ensemble de paramètres de capture de médias pris en charge par un appareil.

### Description

Décrit les modes de capture de média pris en charge par le périphérique. Les données de configuration incluent le type MIME et dimensions de capture pour la capture vidéo ou image.

[RFC2046][1]devraient respecter les types MIME. Exemples :

 [1]: http://www.ietf.org/rfc/rfc2046.txt

*   `video/3gpp`
*   `video/quicktime`
*   `image/jpeg`
*   `audio/amr`
*   `audio/wav`

### Propriétés

*   **type**: The ASCII encodée en chaîne minuscule qui représente le type de média. (DOMString)

*   **hauteur**: la hauteur de l'image ou la vidéo en pixels. La valeur est zéro pour les extraits sonores. (Nombre)

*   **largeur**: la largeur de l'image ou la vidéo en pixels. La valeur est zéro pour les extraits sonores. (Nombre)

### Exemple

    prise en charge de récupérer image modes var imageModes = navigator.device.capture.supportedImageModes ;
    
    Sélectionnez le mode qui a la plus haute résolution horizontale var largeur = 0 ;
    var selectedmode ;
    pour chaque (mode var imageModes) {si (mode.width > largeur) {largeur = mode.width ;
            selectedmode = mode ;
        }
    }
    

Pas pris en charge par n'importe quelle plateforme. Tous les tableaux de données de configuration sont vides.

## MediaFile.getFormatData

> Récupère des informations sur le format du fichier média capturé.

    mediaFile.getFormatData(
        MediaFileDataSuccessCB successCallback,
        [MediaFileDataErrorCB errorCallback]
    );
    

### Description

Cette fonction de façon asynchrone tente de récupérer les informations de format pour le fichier multimédia. S'il réussit, il appelle le rappel de `MediaFileDataSuccessCB` avec un objet `MediaFileData`. Si la tentative échoue, cette fonction appelle le rappel de `MediaFileDataErrorCB`.

### Plates-formes prises en charge

*   Amazon Fire OS
*   Android
*   BlackBerry 10
*   iOS
*   Windows Phone 7 et 8
*   Windows 8

### Amazon Fire OS Quirks

L'API pour accéder aux médias file format informations est limité, donc pas tous les `MediaFileData` propriétés sont prises en charge.

### BlackBerry 10 Quirks

Ne fournit pas une API pour plus d'informations sur les fichiers de médias, tous les objets de `MediaFileData` de retour avec les valeurs par défaut.

### Quirks Android

L'API pour accéder aux médias file format informations est limité, donc pas tous les `MediaFileData` propriétés sont prises en charge.

### iOS Quirks

L'API pour accéder aux médias file format informations est limité, donc pas tous les `MediaFileData` propriétés sont prises en charge.

## MediaFile

> Encapsule les propriétés d'un fichier média capturé.

### Propriétés

*   **nom**: le nom du fichier, sans le chemin d'accès. (DOMString)

*   **fullPath**: le chemin d'accès complet du fichier, y compris le nom. (DOMString)

*   **type**: type de mime du fichier (DOMString)

*   **lastModifiedDate**: la date et l'heure lorsque le fichier a été modifié. (Date)

*   **taille**: la taille du fichier, en octets. (Nombre)

### Méthodes

*   **MediaFile.getFormatData**: récupère les informations sur le format du fichier multimédia.

## MediaFileData

> Encapsule des informations de format d'un fichier média.

### Propriétés

*   **codecs**: le format réel du contenu audio et vidéo. (DOMString)

*   **débit**: le débit moyen du contenu. La valeur est égale à zéro pour les images. (Nombre)

*   **hauteur**: la hauteur de l'image ou la vidéo en pixels. La valeur est égale à zéro pour des clips audio. (Nombre)

*   **largeur**: la largeur de l'image ou la vidéo en pixels. La valeur est égale à zéro pour des clips audio. (Nombre)

*   **durée**: la durée du clip vidéo ou audio en quelques secondes. La valeur est égale à zéro pour les images. (Nombre)

### BlackBerry 10 Quirks

Aucune API ne fournit des informations sur le format des fichiers multimédias, donc l'objet de `MediaFileData` retourné par `MediaFile.getFormatData` caractéristiques les valeurs par défaut suivantes :

*   **codecs**: pas pris en charge et retourne`null`.

*   **Bitrate**: pas pris en charge et retourne la valeur zéro.

*   **hauteur**: pas pris en charge et retourne la valeur zéro.

*   **largeur**: non pris en charge et retourne la valeur zéro.

*   **durée**: non pris en charge et retourne la valeur zéro.

### Amazon Fire OS Quirks

Prend en charge ce qui suit `MediaFileData` Propriétés :

*   **codecs** : propriété non prise en charge, sa valeur est `null`.

*   **bitrate** : propriété non prise en charge, sa valeur est zéro.

*   **hauteur**: prise en charge : seuls les fichiers image et vidéo.

*   **largeur**: prise en charge : seuls les fichiers image et vidéo.

*   **durée**: prise en charge : seuls les fichiers audio et vidéo

### Quirks Android

Prend en charge ce qui suit `MediaFileData` Propriétés :

*   **codecs**: pas pris en charge et retourne`null`.

*   **Bitrate**: pas pris en charge et retourne la valeur zéro.

*   **height** : propriété prise en charge seulement pour les fichiers image et vidéo.

*   **width** : propriété prise en charge seulement pour les fichiers image et vidéo.

*   **durée**: prise en charge : seuls les fichiers audio et vidéo.

### iOS Quirks

Prend en charge ce qui suit `MediaFileData` Propriétés :

*   **codecs**: pas pris en charge et retourne`null`.

*   **Bitrate**: pris en charge sur les périphériques d'iOS4 pour l'audio uniquement. Renvoie zéro pour les images et vidéos.

*   **hauteur**: prise en charge : seuls les fichiers image et vidéo.

*   **largeur**: prise en charge : seuls les fichiers image et vidéo.

*   **duration** : propriété prise en charge seulement pour les fichiers audio et vidéo.
