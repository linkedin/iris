# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.


def test_parse_valid_body():
    from iris.webhooks.rackspace import rackspace
    rs_webhook = rackspace()

    fake_post = {
        "event_id": "test_check",
        "log_entry_id": "ntOgGC8c9G",
        "details": {
            "target": "www.example.com",
            "timestamp": 1527062018051,
            "metrics": {
                "tt_firstbyte": {
                    "type": "I",
                    "data": 2,
                    "unit": "unknown"
                },
                "duration": {
                    "type": "I",
                    "data": 2,
                    "unit": "unknown"
                },
                "bytes": {
                    "type": "i",
                    "data": 17,
                    "unit": "unknown"
                },
                "tt_connect": {
                    "type": "I",
                    "data": 0,
                    "unit": "unknown"
                },
                "code": {
                    "type": "s",
                    "data": "200",
                    "unit": "unknown"
                }
            },
            "state": "CRITICAL",
            "status": "Critical Error :-(",
            "txn_id": ".rh-S949.h-api0.ord1.prod.cm.k1k.me.r-SJg49cHk.c-100000001.ts-1000000000001.v-cdb2afa",
            "observations": [
                {
                    "monitoring_zone_id": "mzTEST1",
                    "state": "CRITICAL",
                    "status": "Critical Error :-(",
                    "timestamp": 1527062018051,
                    "collectorState": "UP"
                },
                {
                    "monitoring_zone_id": "mzTEST2",
                    "state": "WARNING",
                    "status": "Warning :-/",
                    "timestamp": 1527062008051
                },
                {
                    "monitoring_zone_id": "mzTEST3",
                    "state": "OK",
                    "status": "Rocking (all good)!",
                    "timestamp": 1527061988051
                }
            ]
        },
        "entity": {
            "id": "enTEST",
            "label": "Test Entity",
            "ip_addresses": {
                "default": "8.8.8.8"
            },
            "metadata": "null",
            "managed": "false",
            "uri": "null",
            "agent_id": "agentA"
        },
        "check": {
            "id": "chTEST",
            "label": "Check Testing Notifications",
            "type": "remote.http",
            "details": {
                "url": "http://www.example.com",
                "method": "GET",
                "follow_redirects": "true",
                "include_body": "false"
            },
            "monitoring_zones_poll": [
                "mzTEST1",
                "mzTEST2",
                "mzTEST3"
            ],
            "timeout": 30,
            "period": 60,
            "target_alias": "default",
            "target_hostname": "null",
            "target_resolver": "",
            "disabled": "false",
            "metadata": "null",
            "confd_name": "null",
            "confd_hash": "null",
            "check_version": 0
        },
        "alarm": {
            "id": "alTEST",
            "label": "Alarm Testing Notifications",
            "check_type": "null",
            "check_id": "chTEST",
            "entity_id": "enTEST",
            "criteria": "if (metric[\"t\"] >= 2.1) { return CRITICAL } return OK",
            "disabled": "false",
            "notification_plan_id": "null",
            "metadata": "null",
            "confd_name": "null",
            "confd_hash": "null"
        },
        "tenant_id": "845119",
        "dashboard_link": "https://intelligence.rackspace.com/cloud/entities/enTEST/checks/chTEST/alarm/alTEST"
    }
    rs_webhook.validate_post(fake_post)
