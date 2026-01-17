#
# Copyright (c) 2022 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

import itertools

from fm.api.policies import base
from fm.api.policies import alarm
from fm.api.policies import event_log
from fm.api.policies import event_suppression


def list_rules():
    return itertools.chain(
        base.list_rules(),
        alarm.list_rules(),
        event_log.list_rules(),
        event_suppression.list_rules()
    )
