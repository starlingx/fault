#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Tests for fm_api module: Fault, FaultAPIsBase, FaultAPIs, FaultAPIsV2."""
# pylint: disable=protected-access,unused-argument

import unittest
from unittest import mock
from tests.base import (
    BaseFmApiTestCase, make_alarm_str,
    TEST_ALARM_ID,
)


class TestFault(BaseFmApiTestCase):
    """Test Fault data class."""

    def test_creation(self):
        fault = self._make_fault()
        self.assertEqual(fault.alarm_id, TEST_ALARM_ID)
        self.assertEqual(fault.alarm_state, 'set')
        self.assertEqual(fault.severity, 'major')

    def test_defaults(self):
        fault = self._make_fault()
        self.assertFalse(fault.service_affecting)
        self.assertFalse(fault.suppression)
        self.assertIsNone(fault.uuid)
        self.assertIsNone(fault.timestamp)
        self.assertFalse(fault.inhibit_alarms)
        self.assertFalse(fault.keep_existing_alarm)

    def test_optional_params(self):
        fault = self._make_fault(
            service_affecting=True, suppression=True,
            uuid='test-uuid', timestamp='2024-01-01',
            inhibit_alarms=True, keep_existing_alarm=True)
        self.assertTrue(fault.service_affecting)
        self.assertTrue(fault.suppression)
        self.assertEqual(fault.uuid, 'test-uuid')
        self.assertTrue(fault.inhibit_alarms)
        self.assertTrue(fault.keep_existing_alarm)

    def test_as_dict(self):
        fault = self._make_fault()
        d = fault.as_dict()
        self.assertIsInstance(d, dict)
        self.assertEqual(d['alarm_id'], TEST_ALARM_ID)
        self.assertIn('entity_type_id', d)

    def test_as_dict_is_copy(self):
        fault = self._make_fault()
        d = fault.as_dict()
        d['alarm_id'] = 'modified'
        self.assertEqual(fault.alarm_id, TEST_ALARM_ID)

    def test_unicode_str(self):
        self.assertEqual(self.Fault._unicode('test'), 'test')

    def test_unicode_none(self):
        self.assertIsNone(self.Fault._unicode(None))


class TestFaultAPIsBase(BaseFmApiTestCase):
    """Test FaultAPIsBase class methods."""

    def test_check_val_none(self):
        self.assertEqual(self.base._check_val(None), " ")

    def test_check_val_value(self):
        self.assertEqual(self.base._check_val("test"), "test")

    def test_alarm_to_str(self):
        fault = self._make_fault()
        result = self.base._alarm_to_str(fault)
        sep = self.constants.FM_CLIENT_STR_SEP
        self.assertIn(sep, result)
        self.assertIn(TEST_ALARM_ID, result)

    def test_str_to_alarm_valid(self):
        result = self.base._str_to_alarm(make_alarm_str())
        self.assertIsNotNone(result)
        self.assertEqual(result.alarm_id, TEST_ALARM_ID)

    def test_str_to_alarm_short_string(self):
        self.assertIsNone(self.base._str_to_alarm("a###b###c"))

    def test_check_required_attributes_valid(self):
        self.base._check_required_attributes(self._make_fault())

    def test_check_required_missing_fields(self):
        from fm_api.fm_api import ClientException
        for field in ['alarm_id', 'alarm_state', 'severity',
                      'alarm_type', 'probable_cause',
                      'entity_type_id', 'entity_instance_id']:
            fault = self._make_fault()
            setattr(fault, field, None)
            with self.assertRaises(ClientException, msg=field):
                self.base._check_required_attributes(fault)

    def test_validate_attributes_valid(self):
        self.base._validate_attributes(self._make_fault())

    def test_validate_invalid_fields(self):
        from fm_api.fm_api import ClientException
        invalid_cases = [
            ('alarm_state', 'invalid'),
            ('severity', 'invalid'),
            ('alarm_type', 'invalid'),
            ('probable_cause', 'invalid'),
        ]
        for field, value in invalid_cases:
            with self.assertRaises(ClientException, msg=field):
                self.base._validate_attributes(
                    self._make_fault(**{field: value}))

    def test_alarm_allowed(self):
        self.assertTrue(self.base.alarm_allowed('warning', 'major'))
        self.assertFalse(self.base.alarm_allowed('critical', 'warning'))
        self.assertFalse(self.base.alarm_allowed('major', 'major'))
        self.assertTrue(self.base.alarm_allowed('warning', 'none'))


class TestFaultAPIs(BaseFmApiTestCase):
    """Test FaultAPIs class."""

    def setUp(self):
        super().setUp()
        from fm_api.fm_api import FaultAPIs
        self.api = FaultAPIs()

    @mock.patch('fm_core.set', return_value='uuid-123')
    def test_set_fault_success(self, _):
        self.assertEqual(
            self.api.set_fault(self._make_fault()), 'uuid-123')

    @mock.patch('fm_core.set', side_effect=RuntimeError)
    def test_set_fault_error(self, _):
        self.assertIsNone(self.api.set_fault(self._make_fault()))

    @mock.patch('fm_core.set', side_effect=SystemError)
    def test_set_fault_system_error(self, _):
        self.assertIsNone(self.api.set_fault(self._make_fault()))

    @mock.patch('fm_core.set', side_effect=TypeError)
    def test_set_fault_type_error(self, _):
        self.assertIsNone(self.api.set_fault(self._make_fault()))

    @mock.patch('fm_core.set_fault_list', return_value=True)
    def test_set_faults_success(self, _):
        self.assertTrue(self.api.set_faults([self._make_fault()]))

    @mock.patch('fm_core.set_fault_list', side_effect=RuntimeError)
    def test_set_faults_error(self, _):
        self.assertIsNone(self.api.set_faults([self._make_fault()]))

    @mock.patch('fm_core.clear', return_value=True)
    def test_clear_fault_success(self, _):
        self.assertTrue(self.api.clear_fault('100.104', 'host=c'))

    @mock.patch('fm_core.clear', return_value=None)
    def test_clear_fault_not_found(self, _):
        self.assertFalse(self.api.clear_fault('100.104', 'host=c'))

    @mock.patch('fm_core.clear', side_effect=RuntimeError)
    def test_clear_fault_error(self, _):
        self.assertFalse(self.api.clear_fault('100.104', 'host=c'))

    @mock.patch('fm_core.get')
    def test_get_fault_success(self, m):
        m.return_value = make_alarm_str()
        result = self.api.get_fault(TEST_ALARM_ID, 'host=ctrl-0')
        self.assertEqual(result.alarm_id, TEST_ALARM_ID)

    @mock.patch('fm_core.get', return_value=None)
    def test_get_fault_not_found(self, _):
        self.assertIsNone(
            self.api.get_fault(TEST_ALARM_ID, 'host=ctrl-0'))

    @mock.patch('fm_core.get', side_effect=RuntimeError)
    def test_get_fault_error(self, _):
        self.assertIsNone(
            self.api.get_fault(TEST_ALARM_ID, 'host=ctrl-0'))

    @mock.patch('fm_core.clear_all', return_value=True)
    def test_clear_all_success(self, _):
        self.assertTrue(self.api.clear_all('host=c'))

    @mock.patch('fm_core.clear_all', return_value=None)
    def test_clear_all_not_found(self, _):
        self.assertFalse(self.api.clear_all('host=c'))

    @mock.patch('fm_core.clear_all', side_effect=RuntimeError)
    def test_clear_all_error(self, _):
        self.assertFalse(self.api.clear_all('host=c'))

    @mock.patch('fm_core.get_by_eid')
    def test_get_faults_success(self, m):
        m.return_value = [make_alarm_str()]
        result = self.api.get_faults('host=ctrl-0')
        self.assertEqual(len(result), 1)

    @mock.patch('fm_core.get_by_eid', return_value=None)
    def test_get_faults_none(self, _):
        self.assertIsNone(self.api.get_faults('host=ctrl-0'))

    @mock.patch('fm_core.get_by_eid', side_effect=RuntimeError)
    def test_get_faults_error(self, _):
        self.assertIsNone(self.api.get_faults('host=ctrl-0'))

    @mock.patch('fm_core.get_by_aid')
    def test_get_faults_by_id_success(self, m):
        m.return_value = [make_alarm_str()]
        self.assertEqual(
            len(self.api.get_faults_by_id(TEST_ALARM_ID)), 1)

    @mock.patch('fm_core.get_by_aid', return_value=None)
    def test_get_faults_by_id_none(self, _):
        self.assertIsNone(self.api.get_faults_by_id(TEST_ALARM_ID))

    @mock.patch('fm_core.get_by_id_n_eid')
    def test_get_faults_by_id_n_eid_success(self, m):
        m.return_value = [make_alarm_str()]
        self.assertIsNotNone(
            self.api.get_faults_by_id_n_eid(TEST_ALARM_ID, 'host=c'))

    @mock.patch('fm_core.get_by_id_n_eid', return_value=None)
    def test_get_faults_by_id_n_eid_none(self, _):
        self.assertIsNone(
            self.api.get_faults_by_id_n_eid(TEST_ALARM_ID, 'host=c'))

    @mock.patch('fm_core.get_by_id_n_eid', side_effect=TypeError)
    def test_get_faults_by_id_n_eid_error(self, _):
        self.assertIsNone(
            self.api.get_faults_by_id_n_eid(TEST_ALARM_ID, 'host=c'))


class TestFaultAPIsV2(BaseFmApiTestCase):
    """Test FaultAPIsV2 class."""

    def setUp(self):
        super().setUp()
        from fm_api.fm_api import FaultAPIsV2, APIException
        self.api = FaultAPIsV2()
        self.APIException = APIException

    @mock.patch('fm_core.set', return_value='uuid-v2')
    def test_set_fault_success(self, _):
        self.assertEqual(
            self.api.set_fault(self._make_fault()), 'uuid-v2')

    @mock.patch('fm_core.set', return_value=None)
    def test_set_fault_failure(self, _):
        with self.assertRaises(self.APIException):
            self.api.set_fault(self._make_fault())

    @mock.patch('fm_core.clear', return_value=True)
    def test_clear_fault_success(self, _):
        self.assertTrue(
            self.api.clear_fault(TEST_ALARM_ID, 'host=c'))

    @mock.patch('fm_core.clear', return_value=None)
    def test_clear_fault_not_found(self, _):
        self.assertFalse(
            self.api.clear_fault(TEST_ALARM_ID, 'host=c'))

    @mock.patch('fm_core.clear', return_value=False)
    def test_clear_fault_failure(self, _):
        with self.assertRaises(self.APIException):
            self.api.clear_fault(TEST_ALARM_ID, 'host=c')

    @mock.patch('fm_core.get')
    def test_get_fault_success(self, m):
        m.return_value = make_alarm_str()
        self.assertIsNotNone(
            self.api.get_fault(TEST_ALARM_ID, 'host=c'))

    @mock.patch('fm_core.get', return_value=None)
    def test_get_fault_not_found(self, _):
        self.assertIsNone(
            self.api.get_fault(TEST_ALARM_ID, 'host=c'))

    @mock.patch('fm_core.get', return_value=False)
    def test_get_fault_failure(self, _):
        with self.assertRaises(self.APIException):
            self.api.get_fault(TEST_ALARM_ID, 'host=c')

    @mock.patch('fm_core.clear_all', return_value=True)
    def test_clear_all_success(self, _):
        self.assertTrue(self.api.clear_all('host=c'))

    @mock.patch('fm_core.clear_all', return_value=None)
    def test_clear_all_not_found(self, _):
        self.assertFalse(self.api.clear_all('host=c'))

    @mock.patch('fm_core.clear_all', return_value=False)
    def test_clear_all_failure(self, _):
        with self.assertRaises(self.APIException):
            self.api.clear_all('host=c')

    @mock.patch('fm_core.get_by_eid')
    def test_get_faults_success(self, m):
        m.return_value = [make_alarm_str()]
        self.assertEqual(len(self.api.get_faults('host=c')), 1)

    @mock.patch('fm_core.get_by_eid', return_value=False)
    def test_get_faults_failure(self, _):
        with self.assertRaises(self.APIException):
            self.api.get_faults('host=c')

    @mock.patch('fm_core.get_by_eid', return_value=None)
    def test_get_faults_none(self, _):
        self.assertIsNone(self.api.get_faults('host=c'))

    @mock.patch('fm_core.get_by_aid')
    def test_get_faults_by_id_success(self, m):
        m.return_value = [make_alarm_str()]
        self.assertIsNotNone(
            self.api.get_faults_by_id(TEST_ALARM_ID))

    @mock.patch('fm_core.get_by_aid', return_value=False)
    def test_get_faults_by_id_failure(self, _):
        with self.assertRaises(self.APIException):
            self.api.get_faults_by_id(TEST_ALARM_ID)

    @mock.patch('fm_core.get_by_aid', return_value=None)
    def test_get_faults_by_id_none(self, _):
        self.assertIsNone(self.api.get_faults_by_id(TEST_ALARM_ID))

    @mock.patch('fm_core.set_fault_list', return_value=True)
    def test_set_faults_success(self, _):
        self.assertTrue(self.api.set_faults([self._make_fault()]))

    @mock.patch('fm_core.set_fault_list', return_value=False)
    def test_set_faults_failure(self, _):
        with self.assertRaises(self.APIException):
            self.api.set_faults([self._make_fault()])

    @mock.patch('fm_core.clear_list', return_value=True)
    def test_clear_faults_list_success(self, _):
        self.assertTrue(
            self.api.clear_faults_list([(TEST_ALARM_ID, 'host=c')]))

    @mock.patch('fm_core.clear_list', return_value=False)
    def test_clear_faults_list_failure(self, _):
        with self.assertRaises(self.APIException):
            self.api.clear_faults_list([(TEST_ALARM_ID, 'host=c')])


class TestFmApiConstants(unittest.TestCase):
    """Test fm_api constants definitions."""

    def setUp(self):
        from fm_api import constants as c
        self.c = c

    def test_entity_types(self):
        self.assertEqual(self.c.FM_ENTITY_TYPE_SYSTEM, 'system')
        self.assertEqual(self.c.FM_ENTITY_TYPE_HOST, 'host')
        self.assertEqual(self.c.FM_ENTITY_TYPE_PORT, 'port')
        self.assertEqual(self.c.FM_ENTITY_TYPE_INTERFACE, 'interface')
        self.assertEqual(self.c.FM_ENTITY_TYPE_SERVICE, 'service')
        self.assertEqual(self.c.FM_ENTITY_TYPE_K8S, 'kubernetes')

    def test_alarm_states(self):
        self.assertEqual(self.c.FM_ALARM_STATE_SET, 'set')
        self.assertEqual(self.c.FM_ALARM_STATE_CLEAR, 'clear')
        self.assertEqual(len(self.c.ALARM_STATE), 4)

    def test_alarm_severity(self):
        expected = ['clear', 'warning', 'minor', 'major', 'critical']
        self.assertEqual(self.c.ALARM_SEVERITY, expected)

    def test_alarm_types(self):
        self.assertEqual(len(self.c.ALARM_TYPE), 12)
        self.assertIn('equipment', self.c.ALARM_TYPE)

    def test_probable_cause_list(self):
        self.assertGreater(len(self.c.ALARM_PROBABLE_CAUSE), 70)
        self.assertIn('software-error', self.c.ALARM_PROBABLE_CAUSE)

    def test_client_str_sep(self):
        self.assertEqual(self.c.FM_CLIENT_STR_SEP, "###")

    def test_alarm_attribute_indices(self):
        self.assertEqual(self.c.FM_UUID_INDEX, 0)
        self.assertEqual(self.c.FM_ALARM_ID_INDEX, 1)
        self.assertEqual(self.c.MAX_ALARM_ATTRIBUTES, 14)

    def test_alarm_id_formats(self):
        self.assertTrue(self.c.FM_ALARM_ID_FS_USAGE.startswith("100."))
        self.assertTrue(
            self.c.FM_ALARM_ID_NETWORK_PORT.startswith("300."))
        self.assertTrue(
            self.c.FM_ALARM_ID_VM_FAILED.startswith("700."))
        self.assertTrue(
            self.c.FM_ALARM_ID_STORAGE_CEPH.startswith("800."))
        self.assertTrue(
            self.c.FM_ALARM_ID_PATCH_IN_PROGRESS.startswith("900."))
        self.assertTrue(
            self.c.FM_ALARM_ID_TPM_INIT.startswith("500."))
        self.assertTrue(
            self.c.FM_ALARM_ID_DC_SUBCLOUD_OFFLINE.startswith("280."))
        self.assertTrue(
            self.c.FM_ALARM_ID_K8S_RESOURCE_PV.startswith("850."))
        self.assertTrue(
            self.c.FM_ALARM_ID_BACKUP_IN_PROGRESS.startswith("210."))


if __name__ == '__main__':
    unittest.main()
