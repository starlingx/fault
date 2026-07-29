#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Integration tests for fault project cross-component validation."""
# pylint: disable=protected-access,unused-argument

import os
import sys
import unittest
from unittest import mock
from tests import constants as TC

sys.modules['fm_core'] = mock.MagicMock()


class TestCrossComponentIntegration(unittest.TestCase):
    """Test cross-component interactions."""

    def setUp(self):
        """Set project root."""
        self.root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    def test_fm_api_constants_importable(self):
        """Test fm_api constants can be imported."""
        from fm_api import constants
        self.assertTrue(hasattr(constants, 'ALARM_STATE'))

    def test_fm_api_fm_api_importable(self):
        """Test fm_api.fm_api can be imported."""
        from fm_api import fm_api
        self.assertTrue(hasattr(fm_api, 'Fault'))
        self.assertTrue(hasattr(fm_api, 'FaultAPIs'))
        self.assertTrue(hasattr(fm_api, 'FaultAPIsV2'))

    def test_fault_uses_constants(self):
        """Test Fault class uses constants module correctly."""
        from fm_api.fm_api import FaultAPIsBase
        from fm_api import constants
        base = FaultAPIsBase()
        self.assertEqual(constants.FM_CLIENT_STR_SEP, "###")
        # Verify _check_val is consistent
        self.assertEqual(base._check_val(None), " ")
        self.assertEqual(base._check_val("test"), "test")

    def test_alarm_roundtrip(self):
        """Test alarm serialization produces valid string."""
        from fm_api.fm_api import Fault, FaultAPIsBase
        base = FaultAPIsBase()
        fault = Fault(
            alarm_id=TC.TEST_ALARM_ID,
            alarm_state='set',
            entity_type_id='system',
            entity_instance_id='host=controller-0',
            severity='major',
            reason_text='Test alarm',
            alarm_type='equipment',
            probable_cause='software-error',
            proposed_repair_action='Fix it',
        )
        alarm_str = base._alarm_to_str(fault)
        self.assertIn(TC.TEST_ALARM_ID, alarm_str)
        self.assertIn('set', alarm_str)
        self.assertIn('major', alarm_str)
        self.assertIn('###', alarm_str)

    def test_fmclient_exc_hierarchy(self):
        """Test fmclient exception hierarchy."""
        from fmclient.exc import (
            HTTPException, Unauthorized, HTTPUnauthorized,
            NotFound, HTTPNotFound
        )
        self.assertTrue(issubclass(HTTPUnauthorized, Unauthorized))
        self.assertTrue(issubclass(HTTPNotFound, NotFound))
        self.assertTrue(issubclass(Unauthorized, HTTPException))
        self.assertTrue(issubclass(NotFound, HTTPException))

    def test_events_yaml_parseable(self):
        """Test events.yaml can be parsed."""
        import yaml
        events_path = os.path.join(
            self.root, 'fm-doc', 'fm_doc', 'events.yaml')
        with open(events_path, 'r') as f:
            events = yaml.safe_load(f)
        self.assertIsInstance(events, dict)
        self.assertGreater(len(events), 0)

    def test_events_yaml_has_alarms(self):
        """Test events.yaml contains alarm entries."""
        import yaml
        events_path = os.path.join(
            self.root, 'fm-doc', 'fm_doc', 'events.yaml')
        with open(events_path, 'r') as f:
            events = yaml.safe_load(f)
        alarm_count = sum(
            1 for v in events.values()
            if isinstance(v, dict) and v.get('Type') == 'Alarm'
        )
        self.assertGreater(alarm_count, 0)

    def test_events_yaml_has_logs(self):
        """Test events.yaml contains log entries."""
        import yaml
        events_path = os.path.join(
            self.root, 'fm-doc', 'fm_doc', 'events.yaml')
        with open(events_path, 'r') as f:
            events = yaml.safe_load(f)
        log_count = sum(
            1 for v in events.values()
            if isinstance(v, dict) and v.get('Type') == 'Log'
        )
        self.assertGreater(log_count, 0)

    def test_constants_alarm_ids_in_events_yaml(self):
        """Test that constants alarm IDs exist in events.yaml."""
        import yaml
        from fm_api import constants
        events_path = os.path.join(
            self.root, 'fm-doc', 'fm_doc', 'events.yaml')
        with open(events_path, 'r') as f:
            events = yaml.safe_load(f)
        # Format event keys to strings
        event_keys = set()
        for k in events.keys():
            if isinstance(k, float):
                event_keys.add("{:.3f}".format(k))
            else:
                event_keys.add(str(k))
        # Check a few known alarm IDs
        self.assertIn(constants.FM_ALARM_ID_FS_USAGE, event_keys)

    def test_fm_log_module(self):
        """Test fm_log module integration."""
        import fm_log
        logger = fm_log.get_logger('integration_test')
        self.assertIsNotNone(logger)
        # Should be able to log without error
        logger.info("Integration test log message")

    def test_all_python_files_parseable(self):
        """Test all Python source files are syntactically valid."""
        import py_compile
        src_dirs = [
            os.path.join(self.root, 'fm-api', 'source', 'fm_api'),
            os.path.join(self.root, 'fm-common', 'sources'),
        ]
        for src_dir in src_dirs:
            if not os.path.isdir(src_dir):
                continue
            for fname in os.listdir(src_dir):
                if fname.endswith('.py'):
                    fpath = os.path.join(src_dir, fname)
                    try:
                        py_compile.compile(fpath, doraise=True)
                    except py_compile.PyCompileError:
                        self.fail(
                            "Failed to compile: {}".format(fpath))

    def test_setup_cfg_files_exist(self):
        """Test setup.cfg files exist for packages."""
        packages = [
            os.path.join(self.root, 'fm-common', 'sources',
                         'setup.cfg'),
            os.path.join(self.root, 'fm-rest-api', 'fm', 'setup.cfg'),
            os.path.join(self.root, 'fm-api', 'source', 'setup.cfg'),
        ]
        for pkg in packages:
            self.assertTrue(os.path.isfile(pkg),
                            "Missing: {}".format(pkg))

    def test_tox_ini_has_required_envs(self):
        """Test tox.ini has required environments."""
        tox_path = os.path.join(self.root, 'tox.ini')
        with open(tox_path, 'r') as f:
            content = f.read()
        self.assertIn('[testenv:linters]', content)
        self.assertIn('[testenv:pep8]', content)
        self.assertIn('[testenv:pylint]', content)

    def test_zuul_yaml_has_jobs(self):
        """Test .zuul.yaml has job definitions."""
        import yaml

        class SafeLoaderIgnoreUnknown(yaml.SafeLoader):
            """SafeLoader that ignores unknown tags."""

        SafeLoaderIgnoreUnknown.add_multi_constructor(
            '', lambda loader, suffix, node: None)

        zuul_path = os.path.join(self.root, '.zuul.yaml')
        with open(zuul_path, 'r') as f:
            data = yaml.load(f, Loader=SafeLoaderIgnoreUnknown)
        self.assertIsInstance(data, list)
        job_names = []
        for item in data:
            if isinstance(item, dict) and 'job' in item:
                if item['job'] and 'name' in item['job']:
                    job_names.append(item['job']['name'])
        self.assertGreater(len(job_names), 0)


if __name__ == '__main__':
    unittest.main()
