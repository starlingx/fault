#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Shared test constants for fault project.

Centralizes test data values used across
multiple test files.

:returns: None (module-level constants)
"""

# Standard test UUID
TEST_UUID = (
    'a1b2c3d4-e5f6-7890-abcd-ef1234567890')

# Common alarm test data
TEST_ALARM_ID = '100.104'
TEST_ALARM_STATE = 'set'
TEST_ENTITY_TYPE = 'system'
TEST_ENTITY_INSTANCE = 'host=ctrl-0'
TEST_SEVERITY = 'major'
TEST_REASON = 'Test alarm'
TEST_ALARM_TYPE = 'equipment'
TEST_PROBABLE_CAUSE = 'software-error'
TEST_REPAIR_ACTION = 'Fix it'
TEST_SUPPRESS_STATUS = 'unsuppressed'
TEST_MGMT_AFFECTING = 'warning'
TEST_DEGRADE_AFFECTING = 'none'

# Short entity instance for tight lines
TEST_ENTITY_SHORT = 'host=c'


def alarm_data(**overrides):
    """Return a complete alarm data dictionary.

    :param overrides: key-value pairs to override
    :returns: dict -- alarm data
    """
    data = dict(
        uuid=TEST_UUID,
        alarm_id=TEST_ALARM_ID,
        alarm_state=TEST_ALARM_STATE,
        entity_type_id=TEST_ENTITY_TYPE,
        entity_instance_id=TEST_ENTITY_SHORT,
        timestamp=None,
        severity=TEST_SEVERITY,
        reason_text=TEST_REASON,
        alarm_type=TEST_ALARM_TYPE,
        probable_cause=TEST_PROBABLE_CAUSE,
        proposed_repair_action=TEST_REPAIR_ACTION,
        service_affecting=False,
        suppression=False,
        inhibit_alarms=False,
        masked=False,
        suppression_status=TEST_SUPPRESS_STATUS,
        mgmt_affecting=TEST_MGMT_AFFECTING,
        degrade_affecting=TEST_DEGRADE_AFFECTING,
    )
    data.update(overrides)
    return data


def event_log_data(**overrides):
    """Return a complete event log data dictionary.

    :param overrides: key-value pairs to override
    :returns: dict -- event log data
    """
    data = dict(
        uuid=TEST_UUID,
        event_log_id=TEST_ALARM_ID,
        state=TEST_ALARM_STATE,
        entity_type_id=TEST_ENTITY_TYPE,
        entity_instance_id=TEST_ENTITY_SHORT,
        timestamp=None,
        severity=TEST_SEVERITY,
        reason_text=TEST_REASON,
        event_log_type=TEST_ALARM_TYPE,
        probable_cause=TEST_PROBABLE_CAUSE,
        proposed_repair_action=TEST_REPAIR_ACTION,
        service_affecting=False,
        suppression=False,
        suppression_status=TEST_SUPPRESS_STATUS,
    )
    data.update(overrides)
    return data


def event_suppression_data(**overrides):
    """Return event suppression data dictionary.

    :param overrides: key-value pairs to override
    :returns: dict -- event suppression data
    """
    data = dict(
        uuid=TEST_UUID,
        alarm_id=TEST_ALARM_ID,
        description=TEST_REASON,
        suppression_status=TEST_SUPPRESS_STATUS,
    )
    data.update(overrides)
    return data
