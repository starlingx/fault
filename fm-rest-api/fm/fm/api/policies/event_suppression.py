#
# Copyright (c) 2024 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

from oslo_policy import policy
from fm.api.policies import base

POLICY_ROOT = 'fm_api:event_suppression:%s'


event_suppression_rules = [
    policy.DocumentedRuleDefault(
        name=POLICY_ROOT % 'get',
        check_str='rule:' + base.READER_OR_OPERATOR,
        description="Get event suppressions.",
        operations=[
            {
                'method': 'GET',
                'path': '/v1/event_suppression'
            },
            {
                'method': 'GET',
                'path': '/v1/event_suppression/{event_suppression_uuid}'
            }
        ]
    ),
    policy.DocumentedRuleDefault(
        name=POLICY_ROOT % 'modify',
        check_str='rule:' + base.ADMIN_IN_SYSTEM_PROJECTS,
        description="Modify the value of an event suppression.",
        operations=[
            {
                'method': 'PATCH',
                'path': '/v1/event_suppression/{event_suppression_uuid}'
            }
        ]
    )
]


def list_rules():
    return event_suppression_rules
