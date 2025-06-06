#
# Copyright (c) 2013-2025 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

# -*- encoding: utf-8 -*-
#
#
# Author:
#

import copy
from . import constants
import six
import fm_core  # pylint: disable=import-error
import threading

fm_api_lock = threading.Lock()


class ClientException(Exception):
    pass


class APIException(Exception):
    pass


# Fields explanation:
#
# alarm_id: a text string of the alarm identifier
# alarm_state: see ALARM_STATE
# entity_type_id: type of the object raising alarm.
# entity_instance_id: instance information of the object raising alarm.
# severity: see ALARM_SEVERITY
# reason_text: free-format string providing description and additional details
#              on the alarm. Optional.
# alarm_type: see ALARM_TYPE
# probable_cause: see ALARM_PROBABLE_CAUSE
# proposed_repair_action:free-format string providing additional details on
#                        how to clear the alarm. Optional.
# service_affecting: true/false, default to false
# suppression: true/false (allowed/not-allowed), default to false
# uuid: unique identifier of an active alarm instance, filled by FM system
# Timestamp: when the alarm has been raised/updated, filled by FM system
# inhibit_alarms: hierarchical suppression of alarms if it is set to true
#                 true/false, default to false
# keep_existing_alarm: keep original alarm when creating an alarm that already exist
#                      true/false, default to false
# See CGCS FM Guide for the alarm model specification
class Fault(object):

    def __init__(self, alarm_id, alarm_state, entity_type_id,
                 entity_instance_id, severity, reason_text,
                 alarm_type, probable_cause, proposed_repair_action,
                 service_affecting=False, suppression=False,
                 uuid=None, timestamp=None, inhibit_alarms=False,
                 keep_existing_alarm=False):
        self.alarm_id = alarm_id
        self.alarm_state = alarm_state
        self.entity_type_id = self._unicode(entity_type_id)
        self.entity_instance_id = self._unicode(entity_instance_id)
        self.severity = severity
        self.reason_text = self._unicode(reason_text)
        self.alarm_type = alarm_type
        self.probable_cause = probable_cause
        self.proposed_repair_action = self._unicode(proposed_repair_action)
        self.service_affecting = service_affecting
        self.suppression = suppression
        self.uuid = uuid
        self.timestamp = timestamp
        self.inhibit_alarms = inhibit_alarms
        self.keep_existing_alarm = keep_existing_alarm

    def as_dict(self):
        return copy.copy(self.__dict__)

    @staticmethod
    def _unicode(value):
        if six.PY2 and isinstance(value, str):
            return six.text_type(value.decode('utf-8'))
        else:
            return value


class FaultAPIsBase(object):
    @staticmethod
    def _check_val(data):
        if data is None:
            return " "
        else:
            return data

    def _alarm_to_str(self, data):
        sep = constants.FM_CLIENT_STR_SEP
        return (sep + self._check_val(data.uuid) + sep + data.alarm_id + sep +
                data.alarm_state + sep + data.entity_type_id + sep +
                data.entity_instance_id + sep +
                self._check_val(data.timestamp) +
                sep + data.severity + sep + self._check_val(data.reason_text) +
                sep + data.alarm_type + sep + data.probable_cause + sep +
                self._check_val(data.proposed_repair_action) + sep +
                str(data.service_affecting) + sep +
                str(data.suppression) + sep +
                str(data.inhibit_alarms) + sep +
                str(data.keep_existing_alarm) + sep
                )

    @staticmethod
    def _str_to_alarm(alarm_str):
        line = alarm_str.split(constants.FM_CLIENT_STR_SEP)
        if len(line) < constants.MAX_ALARM_ATTRIBUTES:
            return None
        else:
            data = Fault(line[constants.FM_ALARM_ID_INDEX],
                         line[constants.FM_ALARM_STATE_INDEX],
                         line[constants.FM_ENT_TYPE_ID_INDEX],
                         line[constants.FM_ENT_INST_ID_INDEX],
                         line[constants.FM_SEVERITY_INDEX],
                         line[constants.FM_REASON_TEXT_INDEX],
                         line[constants.FM_ALARM_TYPE_INDEX],
                         line[constants.FM_CAUSE_INDEX],
                         line[constants.FM_REPAIR_ACTION_INDEX],
                         line[constants.FM_SERVICE_AFFECTING_INDEX],
                         line[constants.FM_SUPPRESSION_INDEX],
                         line[constants.FM_UUID_INDEX],
                         line[constants.FM_TIMESTAMP_INDEX])
            return data

    @staticmethod
    def _check_required_attributes(data):
        if data.alarm_id is None:
            raise ClientException("Alarm  id is is required.")
        if data.alarm_state is None:
            raise ClientException("Alarm state is required.")
        if data.severity is None:
            raise ClientException("Severity is required.")
        if data.alarm_type is None:
            raise ClientException("Alarm type is required.")
        if data.probable_cause is None:
            raise ClientException("Probable Cause is required.")
        if data.entity_type_id is None:
            raise ClientException("Entity type id is required.")
        if data.entity_instance_id is None:
            raise ClientException("Entity instance id is required.")

    @staticmethod
    def _validate_attributes(data):
        """ Validate the attributes
            only applies to Telco specific attributes"""
        if data.alarm_state not in constants.ALARM_STATE:
            raise ClientException("Invalid Fault State: %s" %
                                  data.alarm_state)
        if data.severity not in constants.ALARM_SEVERITY:
            raise ClientException("Invalid Fault Severity: %s" %
                                  data.severity)
        if data.alarm_type not in constants.ALARM_TYPE:
            raise ClientException("Invalid Fault Type: %s" %
                                  data.alarm_type)
        if data.probable_cause not in constants.ALARM_PROBABLE_CAUSE:
            raise ClientException("Invalid Fault Probable Cause: %s" %
                                  data.probable_cause)

    @staticmethod
    def alarm_allowed(alarm_severity, threshold):
        def severity_to_int(severity):
            if severity == 'none':
                return 5
            elif severity == constants.FM_ALARM_SEVERITY_CRITICAL:
                return 4
            elif severity == constants.FM_ALARM_SEVERITY_MAJOR:
                return 3
            elif severity == constants.FM_ALARM_SEVERITY_MINOR:
                return 2
            elif severity == constants.FM_ALARM_SEVERITY_WARNING:
                return 1

        given = severity_to_int(alarm_severity)
        threshold = severity_to_int(threshold)
        if given < threshold:
            return True
        return False


class FaultAPIs(FaultAPIsBase):

    def set_fault(self, data):
        with fm_api_lock:
            self._check_required_attributes(data)
            self._validate_attributes(data)
            buff = self._alarm_to_str(data)
            try:
                return fm_core.set(buff)
            except (RuntimeError, SystemError, TypeError):
                return None

    def set_faults(self, data):
        buff_list = []
        with fm_api_lock:
            for alarm_data in data:
                self._check_required_attributes(alarm_data)
                self._validate_attributes(alarm_data)
                buff = self._alarm_to_str(alarm_data)
                buff_list.append(buff)
            try:
                return fm_core.set_fault_list(buff_list)
            except (RuntimeError, SystemError, TypeError):
                return None

    def clear_fault(self, alarm_id, entity_instance_id):
        with fm_api_lock:
            sep = constants.FM_CLIENT_STR_SEP
            buff = (sep + self._check_val(alarm_id) + sep +
                    self._check_val(entity_instance_id) + sep)
            try:
                resp = fm_core.clear(buff)
                # resp may be True/False/None after FaultAPIsV2
                #  implementation.
                # To keep FaultAPIs the same as before,
                #  return False for None case.
                if resp is True:
                    return True
                else:
                    return False
            except (RuntimeError, SystemError, TypeError):
                return False

    def get_fault(self, alarm_id, entity_instance_id):
        with fm_api_lock:
            sep = constants.FM_CLIENT_STR_SEP
            buff = (sep + self._check_val(alarm_id) + sep +
                    self._check_val(entity_instance_id) + sep)
            try:
                resp = fm_core.get(buff)
                if resp:
                    return self._str_to_alarm(resp)
            except (RuntimeError, SystemError, TypeError):
                pass
            return None

    def clear_all(self, entity_instance_id):
        with fm_api_lock:
            try:
                resp = fm_core.clear_all(entity_instance_id)
                # resp may be True/False/None after FaultAPIsV2
                #  implementation.
                # To keep FaultAPIs the same as before,
                #  return False for None case.
                if resp is True:
                    return True
                else:
                    return False
            except (RuntimeError, SystemError, TypeError):
                return False

    def get_faults(self, entity_instance_id):
        with fm_api_lock:
            try:
                resp = fm_core.get_by_eid(entity_instance_id)
                if resp:
                    data = []
                    for i in resp:
                        data.append(self._str_to_alarm(i))
                    return data
            except (RuntimeError, SystemError, TypeError):
                pass
            return None

    def get_faults_by_id_n_eid(self, alarm_id, entity_instance_id):
        with fm_api_lock:
            sep = constants.FM_CLIENT_STR_SEP
            buff = (sep + self._check_val(alarm_id) + sep +
                    self._check_val(entity_instance_id) + sep)
            try:
                resp = fm_core.get_by_id_n_eid(buff)
                if resp:
                    data = []
                    for i in resp:
                        data.append(self._str_to_alarm(i))
                    return data
            except (RuntimeError, SystemError, TypeError):
                pass
            return None

    def get_faults_by_id(self, alarm_id):
        with fm_api_lock:
            try:
                resp = fm_core.get_by_aid(alarm_id)
                if resp:
                    data = []
                    for i in resp:
                        data.append(self._str_to_alarm(i))
                    return data
            except (RuntimeError, SystemError, TypeError):
                pass
            return None


class FaultAPIsV2(FaultAPIsBase):

    # Input: alarm data
    # Return: Success: uuid for the alarm
    # Exception: 1. Input Alarm format is not valid
    #            2. When there is operation failure
    def set_fault(self, data):
        with fm_api_lock:
            self._check_required_attributes(data)
            self._validate_attributes(data)
            buff = self._alarm_to_str(data)
            uuid = fm_core.set(buff)
        if uuid is None:
            raise APIException("Failed to execute set_fault.")
        return uuid

    # Input: alarm_id, entity_instance_id
    # Return: Success: True
    #         Alarm doesn't exist: False
    # Exception: When there is operation failure
    def clear_fault(self, alarm_id, entity_instance_id):
        with fm_api_lock:
            sep = constants.FM_CLIENT_STR_SEP
            buff = (sep + self._check_val(alarm_id) + sep +
                    self._check_val(entity_instance_id) + sep)
            resp = fm_core.clear(buff)
            if resp is False:
                # There is operation failure
                raise APIException("Failed to execute clear_fault.")
            elif resp is None:
                # alarm is not found
                return False
            else:
                return True

    # Input: alarm_id, entity_instance_id
    # Return: Success: Alarm
    #         Alarm doesn't exist: None
    # Exception: When there is operation failure
    def get_fault(self, alarm_id, entity_instance_id):
        with fm_api_lock:
            sep = constants.FM_CLIENT_STR_SEP
            buff = (sep + self._check_val(alarm_id) + sep +
                    self._check_val(entity_instance_id) + sep)
            resp = fm_core.get(buff)
            if resp is False:
                raise APIException("Failed to execute get_fault.")
            else:
                return self._str_to_alarm(resp) if resp else None

    # Input: entity_instance_id
    # Return: Success: True
    #         Alarm doesn't exist: False
    # Exception: When there is operation failure
    def clear_all(self, entity_instance_id):
        with fm_api_lock:
            resp = fm_core.clear_all(entity_instance_id)
            if resp is False:
                # There is operation failure
                raise APIException("Failed to execute clear_all.")
            elif resp is None:
                # alarm is not found
                return False
            else:
                return True

    # Input: entity_instance_id
    # Return: Success: Alarm list
    #         Alarm doesn't exist: None
    # Exception: When there is operation failure
    def get_faults(self, entity_instance_id):
        with fm_api_lock:
            resp = fm_core.get_by_eid(entity_instance_id)
            if resp is False:
                raise APIException("Failed to execute get_faults.")
            elif resp:
                data = []
                for i in resp:
                    data.append(self._str_to_alarm(i))
                return data
            else:
                return None

    # Input: alarm_id
    # Return: Success: Alarm list
    #         Alarm doesn't exist: None
    # Exception: When there is operation failure
    def get_faults_by_id(self, alarm_id):
        with fm_api_lock:
            resp = fm_core.get_by_aid(alarm_id)
            if resp is False:
                raise APIException("Failed to execute get_faults_by_id.")
            elif resp:
                data = []
                for i in resp:
                    data.append(self._str_to_alarm(i))
                return data
            else:
                return None

    def set_faults(self, data: list[Fault]) -> bool:
        """Set a list of provided faults

        :param data: list of Fault objects
        """
        buff_list = []
        for alarm_data in data:
            self._check_required_attributes(alarm_data)
            self._validate_attributes(alarm_data)
            buff = self._alarm_to_str(alarm_data)
            buff_list.append(buff)

        with fm_api_lock:
            resp = fm_core.set_fault_list(buff_list)
        if resp is False:
            raise APIException("Failed to execute set_faults.")
        return resp

    def clear_faults_list(self, faults_list: list[tuple[str, str]]) -> bool:
        """Clear a list of provided faults

        :param faults_list: list of tuples (alarm_id, entity_instance_id)
        """
        buff_list = []
        sep = constants.FM_CLIENT_STR_SEP
        for alarm_id, entity_instance_id in faults_list:
            buff_list.append(sep + self._check_val(alarm_id) + sep +
                             self._check_val(entity_instance_id) + sep)
        with fm_api_lock:
            resp = fm_core.clear_list(buff_list)
        if resp is False:
            raise APIException("Failed to execute clear_faults_list.")
        return resp
