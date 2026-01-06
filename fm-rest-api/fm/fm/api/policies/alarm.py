#
# Copyright (c) 2022,2025 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

from oslo_policy import policy
from fm.api.policies import base

POLICY_ROOT = 'fm_api:alarm:%s'


alarm_rules = [
    policy.DocumentedRuleDefault(
        name=POLICY_ROOT % 'create',
        check_str='rule:' + base.ADMIN_OR_CONFIGURATOR,
        description="Create an alarm.",
        operations=[
            {
                'method': 'POST',
                'path': '/v1/alarms'
            }
        ]
    ),
    policy.DocumentedRuleDefault(
        name=POLICY_ROOT % 'delete',
        check_str='rule:' + base.ADMIN_OR_CONFIGURATOR,
        description="Delete an alarm.",
        operations=[
            {
                'method': 'DELETE',
                'path': '/v1/alarms/{alarm_uuid}'
            }
        ]
    ),
    policy.DocumentedRuleDefault(
        name=POLICY_ROOT % 'get',
        check_str='rule:' + base.READER_OR_OPERATOR_OR_CONFIGURATOR,
        description="Get alarms.",
        operations=[
            {
                'method': 'GET',
                'path': '/v1/alarms'
            },
            {
                'method': 'GET',
                'path': '/v1/alarms/{alarm_uuid}'
            },
            {
                'method': 'GET',
                'path': '/v1/alarms/detail'
            },
            {
                'method': 'GET',
                'path': '/v1/alarms/summary'
            }
        ]
    ),
    policy.DocumentedRuleDefault(
        name=POLICY_ROOT % 'modify',
        check_str='rule:' + base.ADMIN_OR_CONFIGURATOR,
        description="Modify an alarm.",
        operations=[
            {
                'method': 'PUT',
                'path': '/v1/alarms'
            }
        ]
    )
]


def list_rules():
    return alarm_rules
