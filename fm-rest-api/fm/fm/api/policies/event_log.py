#
# Copyright (c) 2022 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

from oslo_policy import policy

POLICY_ROOT = 'fm_api:event_log:%s'


event_log_rules = [
    policy.DocumentedRuleDefault(
        name=POLICY_ROOT % 'get',
        check_str='role:reader',
        description="Get event logs.",
        operations=[
            {
                'method': 'GET',
                'path': '/v1/event_log'
            },
            {
                'method': 'GET',
                'path': '/v1/event_log/{log_uuid}'
            },
            {
                'method': 'GET',
                'path': '/v1/event_log/detail'
            }
        ]
    )
]


def list_rules():
    return event_log_rules
