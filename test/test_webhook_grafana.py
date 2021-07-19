# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

import pytest
from falcon import HTTPBadRequest


def test_parse_valid_body():
    from iris.webhooks.grafana import grafana
    grafana_webhook = grafana()

    fake_post = {
        "evalMatches": [{
            "value": 100,
            "metric": "High value",
            "tags": "",
        }, {
            "value": 200,
            "metric": "Higher Value",
            "tags": "",
        }],
        "imageUrl": "http://grafana.org/assets/img/blog/mixed_styles.png",
        "message": "Someone is testing the alert notification within grafana.",
        "ruleId": 0,
        "ruleName": "Test notification",
        "ruleUrl": "https://grafana.org/",
        "state": "alerting",
        "title": "[Alerting] Test notification"
    }
    grafana_webhook.validate_post(fake_post)


def test_parse_invalid_body():
    from iris.webhooks.grafana import grafana
    grafana_webhook = grafana()

    fake_post = {
        "evalMatches": [{
            "value": 100,
            "metric": "High value",
            "tags": "",
        }, {
            "value": 200,
            "metric": "Higher Value",
            "tags": "",
        }],
        "imageUrl": "http://grafana.org/assets/img/blog/mixed_styles.png",
        "message": "Someone is testing the alert notification within grafana.",
        "ruleId": 0,
        "ruleName": "Test notification",
        "ruleUrl": "https://grafana.org/",
        "title": "[Alerting] Test notification"
    }

    with pytest.raises(HTTPBadRequest):
        grafana_webhook.validate_post(fake_post)
