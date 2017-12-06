# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

from falcon import HTTPBadRequest


def test_parse_valid_body():
    from iris.webhooks.alertmanager import alertmanager
    am_webhook = alertmanager()

    fake_post = {
        "receiver": "iris-test",
        "status": "firing",
        "alerts": [{
            "status": "firing",
            "labels": {
                "alertname": "InstanceDown",
                "group": "testgroup",
                "instance": "testinstance:8080",
                "job": "testjob",
                "monitor": "testmonitor",
                "severity": "page"
            },
            "annotations": {
                "description": "testannotation",
                "summary": "testsummary"
            },
            "startsAt": "2017-12-04T09:17:22.804Z",
            "endsAt": "0001-01-01T00:00:00Z",
            "generatorURL": "http://1a80c99c0865:9090/graph?g0.expr=up+%3D%3D+0\\u0026g0.tab=0"
        }],
        "groupLabels": {
            "alertname": "testalert",
            "iris_plan": "testplan"
        },
        "commonLabels": {
            "alertname": "testalert",
            "group": "testgroup",
            "instance": "testinstance:8080",
            "job": "testjob",
            "monitor": "testmonitor",
            "severity": "page"
        },
        "commonAnnotations": {
            "description": "testcommonannotation",
            "summary": "testcommonsummary"
        },
        "externalURL": "http://a9fabe732a60:9093",
        "version": "4",
        "groupKey": "{}:{alertname=\"testalert\"}"
    }
    am_webhook.validate_post(fake_post)


def test_parse_invalid_body():
    from iris.webhooks.alertmanager import alertmanager
    am_webhook = alertmanager()

    fake_post = {
        "receiver": "iris-test",
        "status": "firing",
        "alerts": [{
            "status": "firing",
            "labels": {
                "alertname": "InstanceDown",
                "group": "testgroup",
                "instance": "testinstance:8080",
                "job": "testjob",
                "monitor": "testmonitor",
                "severity": "page"
            },
            "annotations": {
                "description": "testannotation",
                "summary": "testsummary"
            },
            "startsAt": "2017-12-04T09:17:22.804Z",
            "endsAt": "0001-01-01T00:00:00Z"
        }],
        "groupLabels": {
            "alertname": "testalert"
        },
        "commonLabels": {
            "alertname": "testalert"
        },
        "commonAnnotations": {
            "description": "testcommonannotation"
        },
        "groupKey": "{}:{alertname=\"testalert\"}"
    }
    try:
        am_webhook.validate_post(fake_post)
    except HTTPBadRequest:
        pass
