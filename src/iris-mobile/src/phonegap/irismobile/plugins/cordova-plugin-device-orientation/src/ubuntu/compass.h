/*
 *  Licensed under the Apache License, Version 2.0 (the "License");
 *  you may not use this file except in compliance with the License.
 *  You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 *  Unless required by applicable law or agreed to in writing, software
 *  distributed under the License is distributed on an "AS IS" BASIS,
 *  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *  See the License for the specific language governing permissions and
 *  limitations under the License.
 */

#ifndef COMPASS_H_HKFSAHKDFAS
#define COMPASS_H_HKFSAHKDFAS

#include <cplugin.h>
#include <QCompass>
#include <QtCore>

class DeviceOrientation: public CPlugin {
    Q_OBJECT
public:
    explicit DeviceOrientation(Cordova *cordova);

    virtual const QString fullName() override {
        return DeviceOrientation::fullID();
    }

    virtual const QString shortName() override {
        return "Compass";
    }

    static const QString fullID() {
        return "Compass";
    }

public slots:
    void getHeading(int scId, int ecId, QVariantMap options);

protected slots:
    void updateSensor();
    void sensorError(int error);

private:
    void reportResult();
    QCompass _compass;
    QList<int> _successCallbacks;
    QList<int> _errorCallbacks;

    double _azymuth;
    double _accuracy;
    qtimestamp _timestamp;
    bool _validData;
};

#endif
