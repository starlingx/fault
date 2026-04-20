#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Tests for fm_api.fm_api FaultAPIs and FaultAPIsV2 classes."""
# pylint: disable=protected-access,unused-argument

import sys
import unittest
from unittest import mock
from tests import constants as TC

sys.modules['fm_core'] = mock.MagicMock()


class TestFaultAPIs(unittest.TestCase):
    """Test FaultAPIs class."""

    def setUp(self):
        """Set up test fixtures."""
        from fm_api.fm_api import FaultAPIs, Fault
        self.api = FaultAPIs()
        self.Fault = Fault

    def _make_fault(self, **kwargs):
        """Create a valid Fault."""
        defaults = {
            'alarm_id': TC.TEST_ALARM_ID,
            'alarm_state': 'set',
            'entity_type_id': 'system',
            'entity_instance_id': 'host=controller-0',
            'severity': 'major',
            'reason_text': 'Test alarm',
            'alarm_type': 'equipment',
            'probable_cause': 'software-error',
            'proposed_repair_action': 'Fix it',
        }
        defaults.update(kwargs)
        return self.Fault(**defaults)

    @mock.patch('fm_core.set', return_value='uuid-123')
    def test_set_fault_success(self, mock_set):
        """Test set_fault returns uuid on success."""
        fault = self._make_fault()
        result = self.api.set_fault(fault)
        self.assertEqual(result, 'uuid-123')
        mock_set.assert_called_once()

    @mock.patch('fm_core.set', side_effect=RuntimeError)
    def test_set_fault_runtime_error(self, mock_set):
        """Test set_fault returns None on RuntimeError."""
        fault = self._make_fault()
        result = self.api.set_fault(fault)
        self.assertIsNone(result)

    @mock.patch('fm_core.set', side_effect=SystemError)
    def test_set_fault_system_error(self, mock_set):
        """Test set_fault returns None on SystemError."""
        fault = self._make_fault()
        result = self.api.set_fault(fault)
        self.assertIsNone(result)

    @mock.patch('fm_core.set', side_effect=TypeError)
    def test_set_fault_type_error(self, mock_set):
        """Test set_fault returns None on TypeError."""
        fault = self._make_fault()
        result = self.api.set_fault(fault)
        self.assertIsNone(result)

    @mock.patch('fm_core.set_fault_list', return_value=True)
    def test_set_faults_success(self, mock_set_list):
        """Test set_faults with list of faults."""
        fault2 = self._make_fault(
            alarm_id='200.001')
        faults = [self._make_fault(), fault2]
        result = self.api.set_faults(faults)
        self.assertTrue(result)

    @mock.patch('fm_core.set_fault_list', side_effect=RuntimeError)
    def test_set_faults_error(self, mock_set_list):
        """Test set_faults returns None on error."""
        faults = [self._make_fault()]
        result = self.api.set_faults(faults)
        self.assertIsNone(result)

    @mock.patch('fm_core.clear', return_value=True)
    def test_clear_fault_success(self, mock_clear):
        """Test clear_fault returns True on success."""
        result = self.api.clear_fault('100.104', 'host=controller-0')
        self.assertTrue(result)

    @mock.patch('fm_core.clear', return_value=None)
    def test_clear_fault_not_found(self, mock_clear):
        """Test clear_fault returns False when not found."""
        result = self.api.clear_fault('100.104', 'host=controller-0')
        self.assertFalse(result)

    @mock.patch('fm_core.clear', return_value=False)
    def test_clear_fault_false(self, mock_clear):
        """Test clear_fault returns False on False response."""
        result = self.api.clear_fault('100.104', 'host=controller-0')
        self.assertFalse(result)

    @mock.patch('fm_core.clear', side_effect=RuntimeError)
    def test_clear_fault_error(self, mock_clear):
        """Test clear_fault returns False on error."""
        result = self.api.clear_fault('100.104', 'host=controller-0')
        self.assertFalse(result)

    @mock.patch('fm_core.get')
    def test_get_fault_success(self, mock_get):
        """Test get_fault returns Fault on success."""
        from fm_api import constants
        sep = constants.FM_CLIENT_STR_SEP
        parts = ['uuid-1', TC.TEST_ALARM_ID, 'set', 'system',
                 'host=ctrl-0', '2024-01-01', 'major',
                 'Test', 'equipment', 'software-error',
                 'Fix', 'False', 'False', 'False']
        mock_get.return_value = sep.join(parts)
        result = self.api.get_fault(TC.TEST_ALARM_ID, 'host=ctrl-0')
        self.assertIsNotNone(result)
        self.assertEqual(result.alarm_id, TC.TEST_ALARM_ID)

    @mock.patch('fm_core.get', return_value=None)
    def test_get_fault_not_found(self, mock_get):
        """Test get_fault returns None when not found."""
        result = self.api.get_fault(TC.TEST_ALARM_ID, 'host=ctrl-0')
        self.assertIsNone(result)

    @mock.patch('fm_core.get', side_effect=RuntimeError)
    def test_get_fault_error(self, mock_get):
        """Test get_fault returns None on error."""
        result = self.api.get_fault(TC.TEST_ALARM_ID, 'host=ctrl-0')
        self.assertIsNone(result)

    @mock.patch('fm_core.clear_all', return_value=True)
    def test_clear_all_success(self, mock_clear_all):
        """Test clear_all returns True on success."""
        result = self.api.clear_all('host=controller-0')
        self.assertTrue(result)

    @mock.patch('fm_core.clear_all', return_value=None)
    def test_clear_all_not_found(self, mock_clear_all):
        """Test clear_all returns False when None."""
        result = self.api.clear_all('host=controller-0')
        self.assertFalse(result)

    @mock.patch('fm_core.clear_all', side_effect=RuntimeError)
    def test_clear_all_error(self, mock_clear_all):
        """Test clear_all returns False on error."""
        result = self.api.clear_all('host=controller-0')
        self.assertFalse(result)

    @mock.patch('fm_core.get_by_eid')
    def test_get_faults_success(self, mock_get_by_eid):
        """Test get_faults returns list of Faults."""
        from fm_api import constants
        sep = constants.FM_CLIENT_STR_SEP
        parts = ['uuid-1', TC.TEST_ALARM_ID, 'set', 'system',
                 'host=ctrl-0', '2024-01-01', 'major',
                 'Test', 'equipment', 'software-error',
                 'Fix', 'False', 'False', 'False']
        mock_get_by_eid.return_value = [sep.join(parts)]
        result = self.api.get_faults('host=ctrl-0')
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)

    @mock.patch('fm_core.get_by_eid', return_value=None)
    def test_get_faults_none(self, mock_get_by_eid):
        """Test get_faults returns None when no faults."""
        result = self.api.get_faults('host=ctrl-0')
        self.assertIsNone(result)

    @mock.patch('fm_core.get_by_eid', side_effect=RuntimeError)
    def test_get_faults_error(self, mock_get_by_eid):
        """Test get_faults returns None on error."""
        result = self.api.get_faults('host=ctrl-0')
        self.assertIsNone(result)

    @mock.patch('fm_core.get_by_aid')
    def test_get_faults_by_id_success(self, mock_get_by_aid):
        """Test get_faults_by_id returns list."""
        from fm_api import constants
        sep = constants.FM_CLIENT_STR_SEP
        parts = ['uuid-1', TC.TEST_ALARM_ID, 'set', 'system',
                 'host=ctrl-0', '2024-01-01', 'major',
                 'Test', 'equipment', 'software-error',
                 'Fix', 'False', 'False', 'False']
        mock_get_by_aid.return_value = [sep.join(parts)]
        result = self.api.get_faults_by_id(TC.TEST_ALARM_ID)
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)

    @mock.patch('fm_core.get_by_aid', return_value=None)
    def test_get_faults_by_id_none(self, mock_get_by_aid):
        """Test get_faults_by_id returns None."""
        result = self.api.get_faults_by_id(TC.TEST_ALARM_ID)
        self.assertIsNone(result)

    @mock.patch('fm_core.get_by_id_n_eid')
    def test_get_faults_by_id_n_eid_success(self, mock_fn):
        """Test get_faults_by_id_n_eid returns list."""
        from fm_api import constants
        sep = constants.FM_CLIENT_STR_SEP
        parts = ['uuid-1', TC.TEST_ALARM_ID, 'set', 'system',
                 'host=ctrl-0', '2024-01-01', 'major',
                 'Test', 'equipment', 'software-error',
                 'Fix', 'False', 'False', 'False']
        mock_fn.return_value = [sep.join(parts)]
        result = self.api.get_faults_by_id_n_eid(
            TC.TEST_ALARM_ID, 'host=ctrl-0')
        self.assertIsNotNone(result)

    @mock.patch('fm_core.get_by_id_n_eid', return_value=None)
    def test_get_faults_by_id_n_eid_none(self, mock_fn):
        """Test get_faults_by_id_n_eid returns None."""
        result = self.api.get_faults_by_id_n_eid(
            TC.TEST_ALARM_ID, 'host=ctrl-0')
        self.assertIsNone(result)

    @mock.patch('fm_core.get_by_id_n_eid', side_effect=TypeError)
    def test_get_faults_by_id_n_eid_error(self, mock_fn):
        """Test get_faults_by_id_n_eid returns None on error."""
        result = self.api.get_faults_by_id_n_eid(
            TC.TEST_ALARM_ID, 'host=ctrl-0')
        self.assertIsNone(result)


class TestFaultAPIsV2(unittest.TestCase):
    """Test FaultAPIsV2 class."""

    def setUp(self):
        """Set up test fixtures."""
        from fm_api.fm_api import FaultAPIsV2, Fault, APIException
        self.api = FaultAPIsV2()
        self.Fault = Fault
        self.APIException = APIException

    def _make_fault(self, **kwargs):
        """Create a valid Fault."""
        defaults = {
            'alarm_id': TC.TEST_ALARM_ID,
            'alarm_state': 'set',
            'entity_type_id': 'system',
            'entity_instance_id': 'host=controller-0',
            'severity': 'major',
            'reason_text': 'Test alarm',
            'alarm_type': 'equipment',
            'probable_cause': 'software-error',
            'proposed_repair_action': 'Fix it',
        }
        defaults.update(kwargs)
        return self.Fault(**defaults)

    @mock.patch('fm_core.set', return_value='uuid-v2')
    def test_set_fault_success(self, mock_set):
        """Test V2 set_fault returns uuid."""
        fault = self._make_fault()
        result = self.api.set_fault(fault)
        self.assertEqual(result, 'uuid-v2')

    @mock.patch('fm_core.set', return_value=None)
    def test_set_fault_failure(self, mock_set):
        """Test V2 set_fault raises APIException on None."""
        fault = self._make_fault()
        with self.assertRaises(self.APIException):
            self.api.set_fault(fault)

    @mock.patch('fm_core.clear', return_value=True)
    def test_clear_fault_success(self, mock_clear):
        """Test V2 clear_fault returns True."""
        result = self.api.clear_fault(TC.TEST_ALARM_ID, 'host=ctrl-0')
        self.assertTrue(result)

    @mock.patch('fm_core.clear', return_value=None)
    def test_clear_fault_not_found(self, mock_clear):
        """Test V2 clear_fault returns False when not found."""
        result = self.api.clear_fault(TC.TEST_ALARM_ID, 'host=ctrl-0')
        self.assertFalse(result)

    @mock.patch('fm_core.clear', return_value=False)
    def test_clear_fault_failure(self, mock_clear):
        """Test V2 clear_fault raises APIException on failure."""
        with self.assertRaises(self.APIException):
            self.api.clear_fault(TC.TEST_ALARM_ID, 'host=ctrl-0')

    @mock.patch('fm_core.get')
    def test_get_fault_success(self, mock_get):
        """Test V2 get_fault returns Fault."""
        from fm_api import constants
        sep = constants.FM_CLIENT_STR_SEP
        parts = ['uuid-1', TC.TEST_ALARM_ID, 'set', 'system',
                 'host=ctrl-0', '2024-01-01', 'major',
                 'Test', 'equipment', 'software-error',
                 'Fix', 'False', 'False', 'False']
        mock_get.return_value = sep.join(parts)
        result = self.api.get_fault(TC.TEST_ALARM_ID, 'host=ctrl-0')
        self.assertIsNotNone(result)

    @mock.patch('fm_core.get', return_value=None)
    def test_get_fault_not_found(self, mock_get):
        """Test V2 get_fault returns None."""
        result = self.api.get_fault(TC.TEST_ALARM_ID, 'host=ctrl-0')
        self.assertIsNone(result)

    @mock.patch('fm_core.get', return_value=False)
    def test_get_fault_failure(self, mock_get):
        """Test V2 get_fault raises APIException."""
        with self.assertRaises(self.APIException):
            self.api.get_fault(TC.TEST_ALARM_ID, 'host=ctrl-0')

    @mock.patch('fm_core.clear_all', return_value=True)
    def test_clear_all_success(self, mock_clear_all):
        """Test V2 clear_all returns True."""
        result = self.api.clear_all('host=ctrl-0')
        self.assertTrue(result)

    @mock.patch('fm_core.clear_all', return_value=None)
    def test_clear_all_not_found(self, mock_clear_all):
        """Test V2 clear_all returns False."""
        result = self.api.clear_all('host=ctrl-0')
        self.assertFalse(result)

    @mock.patch('fm_core.clear_all', return_value=False)
    def test_clear_all_failure(self, mock_clear_all):
        """Test V2 clear_all raises APIException."""
        with self.assertRaises(self.APIException):
            self.api.clear_all('host=ctrl-0')

    @mock.patch('fm_core.get_by_eid')
    def test_get_faults_success(self, mock_fn):
        """Test V2 get_faults returns list."""
        from fm_api import constants
        sep = constants.FM_CLIENT_STR_SEP
        parts = ['uuid-1', TC.TEST_ALARM_ID, 'set', 'system',
                 'host=ctrl-0', '2024-01-01', 'major',
                 'Test', 'equipment', 'software-error',
                 'Fix', 'False', 'False', 'False']
        mock_fn.return_value = [sep.join(parts)]
        result = self.api.get_faults('host=ctrl-0')
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)

    @mock.patch('fm_core.get_by_eid', return_value=False)
    def test_get_faults_failure(self, mock_fn):
        """Test V2 get_faults raises APIException."""
        with self.assertRaises(self.APIException):
            self.api.get_faults('host=ctrl-0')

    @mock.patch('fm_core.get_by_eid', return_value=None)
    def test_get_faults_none(self, mock_fn):
        """Test V2 get_faults returns None."""
        result = self.api.get_faults('host=ctrl-0')
        self.assertIsNone(result)

    @mock.patch('fm_core.get_by_aid')
    def test_get_faults_by_id_success(self, mock_fn):
        """Test V2 get_faults_by_id returns list."""
        from fm_api import constants
        sep = constants.FM_CLIENT_STR_SEP
        parts = ['uuid-1', TC.TEST_ALARM_ID, 'set', 'system',
                 'host=ctrl-0', '2024-01-01', 'major',
                 'Test', 'equipment', 'software-error',
                 'Fix', 'False', 'False', 'False']
        mock_fn.return_value = [sep.join(parts)]
        result = self.api.get_faults_by_id(TC.TEST_ALARM_ID)
        self.assertIsNotNone(result)

    @mock.patch('fm_core.get_by_aid', return_value=False)
    def test_get_faults_by_id_failure(self, mock_fn):
        """Test V2 get_faults_by_id raises APIException."""
        with self.assertRaises(self.APIException):
            self.api.get_faults_by_id(TC.TEST_ALARM_ID)

    @mock.patch('fm_core.get_by_aid', return_value=None)
    def test_get_faults_by_id_none(self, mock_fn):
        """Test V2 get_faults_by_id returns None."""
        result = self.api.get_faults_by_id(TC.TEST_ALARM_ID)
        self.assertIsNone(result)

    @mock.patch('fm_core.set_fault_list', return_value=True)
    def test_set_faults_success(self, mock_fn):
        """Test V2 set_faults returns True."""
        faults = [self._make_fault()]
        result = self.api.set_faults(faults)
        self.assertTrue(result)

    @mock.patch('fm_core.set_fault_list', return_value=False)
    def test_set_faults_failure(self, mock_fn):
        """Test V2 set_faults raises APIException."""
        faults = [self._make_fault()]
        with self.assertRaises(self.APIException):
            self.api.set_faults(faults)

    @mock.patch('fm_core.clear_list', return_value=True)
    def test_clear_faults_list_success(self, mock_fn):
        """Test V2 clear_faults_list returns True."""
        faults_list = [(TC.TEST_ALARM_ID, 'host=ctrl-0')]
        result = self.api.clear_faults_list(faults_list)
        self.assertTrue(result)

    @mock.patch('fm_core.clear_list', return_value=False)
    def test_clear_faults_list_failure(self, mock_fn):
        """Test V2 clear_faults_list raises APIException."""
        faults_list = [(TC.TEST_ALARM_ID, 'host=ctrl-0')]
        with self.assertRaises(self.APIException):
            self.api.clear_faults_list(faults_list)


if __name__ == '__main__':
    unittest.main()
