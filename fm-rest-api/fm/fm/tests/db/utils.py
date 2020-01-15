# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#
# Copyright 2020 Intel Corporation

"""Fault test utilities."""

from fm.db import api as db_api
from fm_api import constants


def get_test_alarm(**kw):
    alarm = {
        'uuid': kw.get('uuid'),
        'alarm_id': kw.get('alarm_id', constants.FM_ALARM_ID_VM_FAILED),
        'alarm_state': kw.get('alarm_state', constants.FM_ALARM_STATE_SET),
        'entity_type_id': kw.get('entity_type_id', constants.FM_ENTITY_TYPE_INSTANCE),
        'entity_instance_id': kw.get('entity_instance_id',
                                     constants.FM_ENTITY_TYPE_INSTANCE + '=' +
                                     'a4e4cdb7-2ee6-4818-84c8-5310fcd67b5d'),
        'severity': kw.get('severity', constants.FM_ALARM_SEVERITY_CRITICAL),
        'reason_text': kw.get('reason_text', "Unknown"),
        'alarm_type': kw.get('alarm_type', constants.FM_ALARM_TYPE_5),
        'probable_cause': kw.get('probable_cause', constants.ALARM_PROBABLE_CAUSE_8),
        'proposed_repair_action': None,
        'service_affecting': False,
        'suppression': False
    }
    return alarm


def create_test_alarm(**kw):
    """Create test alarm entry in DB and return alarm DB object.
    Function to be used to create test alarm objects in the database.
    :param kw: kwargs with overriding values for alarm's attributes.
    :returns: Test alarm DB object.
    """
    alarm = get_test_alarm(**kw)
    # Let DB generate ID if it isn't specified explicitly
    dbapi = db_api.get_instance()
    return dbapi.alarm_create(alarm)
