#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Tests for fm_api.fm_api module - Fault and FaultAPIsBase classes."""
# pylint: disable=protected-access,unused-argument

import sys
import unittest
from unittest import mock
from tests import constants as TC

# Mock fm_core before importing fm_api
sys.modules['fm_core'] = mock.MagicMock()


class TestFault(unittest.TestCase):
    """Test Fault data class."""

    def setUp(self):
        """Set up test fixtures."""
        from fm_api.fm_api import Fault
        self.Fault = Fault

    def _make_fault(self, **kwargs):
        """Create a Fault with defaults."""
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

    def test_fault_creation(self):
        """Test basic Fault object creation."""
        fault = self._make_fault()
        self.assertEqual(fault.alarm_id, TC.TEST_ALARM_ID)
        self.assertEqual(fault.alarm_state, 'set')
        self.assertEqual(fault.severity, 'major')

    def test_fault_defaults(self):
        """Test Fault default values."""
        fault = self._make_fault()
        self.assertFalse(fault.service_affecting)
        self.assertFalse(fault.suppression)
        self.assertIsNone(fault.uuid)
        self.assertIsNone(fault.timestamp)
        self.assertFalse(fault.inhibit_alarms)
        self.assertFalse(fault.keep_existing_alarm)

    def test_fault_optional_params(self):
        """Test Fault with optional parameters."""
        fault = self._make_fault(
            service_affecting=True,
            suppression=True,
            uuid='test-uuid',
            timestamp='2024-01-01',
            inhibit_alarms=True,
            keep_existing_alarm=True,
        )
        self.assertTrue(fault.service_affecting)
        self.assertTrue(fault.suppression)
        self.assertEqual(fault.uuid, 'test-uuid')
        self.assertTrue(fault.inhibit_alarms)
        self.assertTrue(fault.keep_existing_alarm)

    def test_fault_as_dict(self):
        """Test Fault.as_dict returns correct dictionary."""
        fault = self._make_fault()
        d = fault.as_dict()
        self.assertIsInstance(d, dict)
        self.assertEqual(d['alarm_id'], TC.TEST_ALARM_ID)
        self.assertEqual(d['alarm_state'], 'set')
        self.assertEqual(d['severity'], 'major')
        self.assertIn('entity_type_id', d)
        self.assertIn('entity_instance_id', d)

    def test_fault_as_dict_is_copy(self):
        """Test as_dict returns a copy, not the original."""
        fault = self._make_fault()
        d = fault.as_dict()
        d['alarm_id'] = 'modified'
        self.assertEqual(fault.alarm_id, TC.TEST_ALARM_ID)

    def test_fault_unicode_str(self):
        """Test _unicode with string input."""
        result = self.Fault._unicode('test')
        self.assertEqual(result, 'test')

    def test_fault_unicode_none(self):
        """Test _unicode with None input."""
        result = self.Fault._unicode(None)
        self.assertIsNone(result)


class TestFaultAPIsBase(unittest.TestCase):
    """Test FaultAPIsBase class methods."""

    def setUp(self):
        """Set up test fixtures."""
        from fm_api.fm_api import FaultAPIsBase, Fault
        from fm_api import constants
        self.base = FaultAPIsBase()
        self.Fault = Fault
        self.constants = constants

    def _make_fault(self, **kwargs):
        """Create a Fault with defaults."""
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

    def test_check_val_none(self):
        """Test _check_val with None returns space."""
        self.assertEqual(self.base._check_val(None), " ")

    def test_check_val_value(self):
        """Test _check_val with value returns value."""
        self.assertEqual(self.base._check_val("test"), "test")

    def test_alarm_to_str(self):
        """Test _alarm_to_str produces separator-delimited string."""
        fault = self._make_fault()
        result = self.base._alarm_to_str(fault)
        sep = self.constants.FM_CLIENT_STR_SEP
        self.assertIn(sep, result)
        self.assertIn(TC.TEST_ALARM_ID, result)
        self.assertIn('set', result)
        self.assertIn('major', result)

    def test_str_to_alarm_valid(self):
        """Test _str_to_alarm with valid string."""
        sep = self.constants.FM_CLIENT_STR_SEP
        parts = ['uuid-123', TC.TEST_ALARM_ID, 'set', 'system',
                 'host=ctrl-0', '2024-01-01', 'major',
                 'Test alarm', 'equipment', 'software-error',
                 'Fix it', 'False', 'False', 'False']
        alarm_str = sep.join(parts)
        result = self.base._str_to_alarm(alarm_str)
        self.assertIsNotNone(result)
        self.assertEqual(result.alarm_id, TC.TEST_ALARM_ID)
        self.assertEqual(result.alarm_state, 'set')

    def test_str_to_alarm_short_string(self):
        """Test _str_to_alarm with too few fields returns None."""
        result = self.base._str_to_alarm("a###b###c")
        self.assertIsNone(result)

    def test_check_required_attributes_valid(self):
        """Test _check_required_attributes with valid fault."""
        fault = self._make_fault()
        # Should not raise
        self.base._check_required_attributes(fault)

    def test_check_required_missing_alarm_id(self):
        """Test missing alarm_id raises ClientException."""
        from fm_api.fm_api import ClientException
        fault = self._make_fault()
        fault.alarm_id = None
        with self.assertRaises(ClientException):
            self.base._check_required_attributes(fault)

    def test_check_required_missing_alarm_state(self):
        """Test missing alarm_state raises ClientException."""
        from fm_api.fm_api import ClientException
        fault = self._make_fault()
        fault.alarm_state = None
        with self.assertRaises(ClientException):
            self.base._check_required_attributes(fault)

    def test_check_required_missing_severity(self):
        """Test missing severity raises ClientException."""
        from fm_api.fm_api import ClientException
        fault = self._make_fault()
        fault.severity = None
        with self.assertRaises(ClientException):
            self.base._check_required_attributes(fault)

    def test_check_required_missing_alarm_type(self):
        """Test missing alarm_type raises ClientException."""
        from fm_api.fm_api import ClientException
        fault = self._make_fault()
        fault.alarm_type = None
        with self.assertRaises(ClientException):
            self.base._check_required_attributes(fault)

    def test_check_required_missing_probable_cause(self):
        """Test missing probable_cause raises ClientException."""
        from fm_api.fm_api import ClientException
        fault = self._make_fault()
        fault.probable_cause = None
        with self.assertRaises(ClientException):
            self.base._check_required_attributes(fault)

    def test_check_required_missing_entity_type_id(self):
        """Test missing entity_type_id raises ClientException."""
        from fm_api.fm_api import ClientException
        fault = self._make_fault()
        fault.entity_type_id = None
        with self.assertRaises(ClientException):
            self.base._check_required_attributes(fault)

    def test_check_required_missing_entity_instance_id(self):
        """Test missing entity_instance_id raises ClientException."""
        from fm_api.fm_api import ClientException
        fault = self._make_fault()
        fault.entity_instance_id = None
        with self.assertRaises(ClientException):
            self.base._check_required_attributes(fault)

    def test_validate_attributes_valid(self):
        """Test _validate_attributes with valid fault."""
        fault = self._make_fault()
        self.base._validate_attributes(fault)

    def test_validate_invalid_state(self):
        """Test invalid alarm_state raises ClientException."""
        from fm_api.fm_api import ClientException
        fault = self._make_fault(alarm_state='invalid')
        with self.assertRaises(ClientException):
            self.base._validate_attributes(fault)

    def test_validate_invalid_severity(self):
        """Test invalid severity raises ClientException."""
        from fm_api.fm_api import ClientException
        fault = self._make_fault(severity='invalid')
        with self.assertRaises(ClientException):
            self.base._validate_attributes(fault)

    def test_validate_invalid_alarm_type(self):
        """Test invalid alarm_type raises ClientException."""
        from fm_api.fm_api import ClientException
        fault = self._make_fault(alarm_type='invalid')
        with self.assertRaises(ClientException):
            self.base._validate_attributes(fault)

    def test_validate_invalid_probable_cause(self):
        """Test invalid probable_cause raises ClientException."""
        from fm_api.fm_api import ClientException
        fault = self._make_fault(probable_cause='invalid')
        with self.assertRaises(ClientException):
            self.base._validate_attributes(fault)

    def test_alarm_allowed_below_threshold(self):
        """Test alarm_allowed returns True when below threshold."""
        result = self.base.alarm_allowed('warning', 'major')
        self.assertTrue(result)

    def test_alarm_allowed_above_threshold(self):
        """Test alarm_allowed returns False when at/above threshold."""
        result = self.base.alarm_allowed('critical', 'warning')
        self.assertFalse(result)

    def test_alarm_allowed_equal_threshold(self):
        """Test alarm_allowed returns False when equal to threshold."""
        result = self.base.alarm_allowed('major', 'major')
        self.assertFalse(result)

    def test_alarm_allowed_none_threshold(self):
        """Test alarm_allowed with none threshold."""
        result = self.base.alarm_allowed('warning', 'none')
        self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()
